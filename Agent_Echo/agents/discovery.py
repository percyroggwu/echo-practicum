"""Discovery: a small class of its own (not a Specialist). At most 3 logical model calls.

Team question: selection call -> prefilter -> judgment call -> code checks -> section.
One schema retry is shared by both calls. Every logical call is refunded to the run budget.
"""

import json
import time

from .discovery_checks import (SchemaFailure, check_selection, check_judgment_schema, check_finding,
                               action_allowed, pool_index, redact, rank_key, ACTION_TYPES, REJECTION_REASONS,
                               VISIBILITY, RECOGNITION)
from .discovery_section import draft, render, provenance
from .discovery_tools import team_summary, prefilter
from .execution_log import record
from .policies import with_policies, DISCOVERY_SELECTION, DISCOVERY_JUDGMENT
from .request_pacing import DiscoveryTimeout
from .runtime import function_tool
from .validation import OutputTokenLimit

DISCOVERY_VERSION = "discovery-v1"
CALL_CAP = 3
CALL_SECONDS = 120  # Starting value; set from measured latency (plan 3.6, gate 10).
DETAILED, ONE_LINE = 5, 5


class _BudgetFailure(Exception):
    pass


class _ProviderFailure(Exception):
    pass


def _strict(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def selection_tool(count):
    return function_tool("submit_selection", f"Return exactly {count} employee IDs from the summary.", {
        "selected_employee_ids": {"type": "array", "items": {"type": "string"}, "minItems": count, "maxItems": count}})


def judgment_tool():
    text = {"type": "string", "minLength": 1, "maxLength": 400}
    finding = _strict({
        "kind": {"type": "string", "enum": ["person", "team_pattern"]},
        "employee_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 10},
        "beneficiary_manager_id": {"type": "string"},
        "work_summary": text, "why_it_matters": text,
        "visibility_state": {"type": "string", "enum": list(VISIBILITY)},
        "recognition_state": {"type": "string", "enum": list(RECOGNITION)},
        "evidence_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 12},
        "quotes": {"type": "array", "maxItems": 4, "items": _strict({"source_id": {"type": "string"}, "text": {"type": "string"}})},
        "action_types": {"type": "array", "items": {"type": "string", "enum": list(ACTION_TYPES)}, "maxItems": 6}})
    rejected = _strict({"employee_id": {"type": "string"}, "reason": {"type": "string", "enum": list(REJECTION_REASONS)}})
    return function_tool("submit_findings", "Return checked-later findings and rejected people.", {
        "findings": {"type": "array", "items": finding, "maxItems": 15},
        "rejected": {"type": "array", "items": rejected}})


SUMMARY_COLUMNS = ("employee_id", "help_records", "contributions", "threads_answered", "blockers_resolved",
                   "incident_handoffs", "threads_without_request", "partner_feedback", "feedback_shared",
                   "recognition_events", "quarters_with_help", "mentions_in_others_text", "self_review_other_team",
                   "self_review_unmatched_initiative", "linked_goals", "linked_blockers", "weeks_above_team_range",
                   "help_by_team")


def summary_table(lines):
    """The team summary as one CSV-like row per person, in ID order. Same facts, no per-team nesting."""
    rows = ["|".join(SUMMARY_COLUMNS)]
    for line in lines:
        teams = line["beneficiaries"]
        total = lambda key: sum(b[key] for b in teams)
        values = [line["employee_id"], line["help_records"], total("contribution"), total("thread_answered"),
                  total("blocker_resolved"), total("incident_handoff"), total("informal_threads"),
                  total("partner_feedback"), total("shared_feedback"), line["recognition_events"],
                  line["quarters_with_help"], total("other_text_mentions"), line["self_review_cross_team"],
                  line["self_review_unmatched_initiative"], total("linked_goals"), total("linked_blockers"),
                  line["above_baseline_weeks"], "; ".join(f"{b['team']}: {b['help_records']}" for b in teams)]
        rows.append("|".join(str(v) for v in values))
    return "\n".join(rows)


def judgment_people(pool, team_names):
    """Pool people for the prompt: empty detail fields dropped, context reduced to per-quarter numbers."""
    people = []
    for person in pool["people"]:
        items = []
        for item in person["items"]:
            item = dict(item, details={k: v for k, v in item["details"].items() if v not in (None, "", [])})
            items.append({k: v for k, v in item.items() if k != "recorded_date"})
        context = person["context"]
        workload = {field: {"unit": value["unit"], "team_upper": round(value["team_upper"], 1),
                            "quarters": [[q["quarter"], round(q["mean"], 1), q["weeks_above_team_range"]] for q in value["quarters"]]}
                    for field, value in context["workload"].items()}
        help_by_team = {team_names.get(b["beneficiary_manager_id"], b["beneficiary_manager_id"]):
                        {q["quarter"]: q["help_records"] for q in b["quarters"]} for b in context["help_by_beneficiary"]}
        people.append({"employee_id": person["employee_id"], "name": person["name"], "items": items,
                       "workload": workload, "help_by_team_and_quarter": help_by_team})
    return people


WORKLOAD_NOTE = ("workload quarters are [quarter, weekly mean, weeks above the team range]; the team range is the "
                 "team's employee-quarter median plus 1.5 times the interquartile spread, in the analysis window.")


def _arguments(turn, name):
    calls = [c for c in turn.calls if c.name == name]
    if len(calls) != 1:
        raise SchemaFailure("missing_tool_call")
    try:
        return json.loads(calls[0].arguments)
    except (TypeError, ValueError):
        raise SchemaFailure("invalid_json") from None


class DiscoveryAgent:
    name = "Discovery"

    def __init__(self, data, model, budget, call_seconds=CALL_SECONDS):
        self.data, self.model, self.budget, self.call_seconds = data, model, budget, call_seconds

    # One logical call: budget check first, refund on every outcome.
    def _call(self, kind, instructions, history, tool):
        remaining = self.budget.remaining()
        if self.calls >= CALL_CAP or remaining["model_calls"] < 1 or remaining["seconds"] <= 0:
            raise _BudgetFailure("budget")
        self.calls += 1
        self.kinds.append(kind)
        record("agent_turn", agent=self.name, turn=self.calls, call=kind, closing=False, remaining=remaining)
        before, costs, started = self.budget.models, len(self.budget.request_costs), time.monotonic()
        try:
            self.budget.consume("model")
            return self.budget.respond(self.model, with_policies(instructions), history, [tool], True,
                                       call_deadline=started + self.call_seconds)
        except DiscoveryTimeout:
            raise _BudgetFailure("time") from None
        except OutputTokenLimit:
            raise SchemaFailure("output_truncated") from None
        except RuntimeError:
            raise _ProviderFailure("provider") from None
        finally:
            elapsed, used = time.monotonic() - started, self.budget.models - before
            self.budget.refund(used, elapsed)
            # Per-call latency sets the 120/135 s pair later (plan 3.6, gate 10).
            record("discovery_call", agent=self.name, call=kind, seconds=round(elapsed, 3), refunded_models=used)
            for cost in self.budget.request_costs[costs:]:
                for usage in cost.get("provider_usage", []):
                    self.usage["input_tokens"] += usage.get("input_tokens", 0)
                    self.usage["output_tokens"] += usage.get("output_tokens", 0)

    def _ask(self, kind, instructions, payload, tool, parse):
        history = [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]
        while True:
            try:
                return parse(_arguments(self._call(kind, instructions, history, tool), tool["name"]))
            except SchemaFailure as failure:
                if self.retry_used:
                    raise
                self.retry_used = True
                record("discovery_schema_retry", agent=self.name, call=kind, check=failure.code)
                history = history[:1] + [{"role": "user", "content":
                    f"Your previous output failed validation ({failure.code}). Call {tool['name']} again with a valid output."}]

    def run(self, question, resolution):
        record("agent_started", agent=self.name)
        self.calls, self.retry_used, self.kinds = 0, False, []
        self.usage = {"input_tokens": 0, "output_tokens": 0}
        subject = resolution["subject"]
        focus = resolution.get("focus_hint")
        selected, selection, reason = None, "not_needed", None
        summary = None
        if subject["kind"] == "team":
            summary = team_summary(self.data, focus, resolution["period"])
            if summary["selection_count"]:
                count = summary["selection_count"]
                try:
                    selected = self._ask("selection", DISCOVERY_SELECTION.format(count=count),
                        {"question": question, "count": count, "summary": summary_table(summary["lines"])},
                        selection_tool(count),
                        lambda output: check_selection(summary, output.get("selected_employee_ids")
                                                       if isinstance(output, dict) else None))
                    selection = "done"
                except (SchemaFailure, _ProviderFailure, _BudgetFailure) as failure:
                    selection, reason = "failed", type(failure).__name__
                    record("discovery_selection_failed", agent=self.name, failure=reason)
        pool = prefilter(self.data, resolution, selected)
        result = self._result(resolution, pool, selection, summary)
        if not pool["people"] and selection == "failed":
            # Focus mode has no satisfaction slot, so a failed selection leaves nobody to review.
            return self._finish(result, "failed_budget" if reason == "_BudgetFailure" else "failed_provider",
                                "the selection step failed")
        if not any(p["items"] for p in pool["people"]):
            return self._finish(result, "no_candidates")
        teams = self._team_names(pool)
        payload = {"question": question, "home_manager_id": self.data.scope.manager_id,
                   "period": pool["period"], "focus_hint": pool["focus_hint"], "beneficiary_teams": teams,
                   "workload_note": WORKLOAD_NOTE, "people": judgment_people(pool, teams),
                   "team_pattern_leads": pool["team_pattern_leads"]}
        try:
            output = self._ask("judgment", DISCOVERY_JUDGMENT, payload, judgment_tool(), check_judgment_schema)
        except _BudgetFailure:
            return self._finish(result, "failed_budget", "Discovery's call or time budget was reached")
        except (_ProviderFailure, SchemaFailure):
            return self._finish(result, "failed_provider", "the model call did not return a valid result")
        return self._checked(result, pool, output, selection)

    def _team_names(self, pool):
        managers = {i.get("beneficiary_manager_id") for p in pool["people"] for i in p["items"]}
        managers |= {b["beneficiary_manager_id"] for p in pool["people"] for b in p.get("context", {}).get("help_by_beneficiary", [])}
        managers |= {lead["beneficiary_manager_id"] for lead in pool["team_pattern_leads"]}
        names = {}
        for manager in sorted(m for m in managers if m):
            teams = self.data.resolve_team(manager)
            names[manager] = teams[0]["team"] if len(teams) == 1 else "Other team"
        return names

    def _result(self, resolution, pool, selection, summary):
        roster = self.data.roster()
        subject = resolution["subject"]
        entered = {"low_satisfaction": 0, "selection": 0, "whole_team": 0}
        if subject["kind"] == "team" and summary is not None:
            entered = {"low_satisfaction": len(summary["lowest"]) if not summary["whole_team"] else 0,
                       "selection": len(pool["people"]) - len(summary["lowest"]) if selection == "done" else 0,
                       "whole_team": len(summary["whole_team"])}
        # The 10-person team pool is the design, not a cut; coverage already states people reviewed.
        caps = ["items_per_person"] if pool["caps_hit"]["items"] else []
        return {"discovery_version": DISCOVERY_VERSION, "status": None,
                "subject": {"kind": subject["kind"], "employee_ids": list(subject["employee_ids"]) if subject["kind"] != "team" else [],
                            "team": self.data.manager["Primary_Team"]},
                "period": {k: pool["period"][k] for k in ("start", "end", "as_of")} | {"narrowed_from_hint": bool(pool["period"].get("narrowed_from_hint"))},
                "coverage": {"team_size": len(roster), "people_reviewed": len(pool["people"]), "selection": selection, "caps_hit": caps},
                "findings": [], "more_findings": {"listed": [], "not_listed": 0},
                "team_pattern_leads": [{"beneficiary_team": self._team_names({"people": [], "team_pattern_leads": [lead]})[lead["beneficiary_manager_id"]],
                                        "people": lead["people_count"], "hidden_items": lead["work_count"], "judged": "not_supported"}
                                       for lead in pool["team_pattern_leads"]],
                "internal": {"pool": {"size": len(pool["people"]), "entered_by": entered},
                             "rejected": [], "withheld": [], "redactions": 0},
                "usage": {}}

    def _checked(self, result, pool, output, selection):
        index = pool_index(pool)
        home = self.data.scope.manager_id
        names = {p["Employee_ID"]: p["Employee_Name"] for p in self.data.roster()}
        own = set(names)
        teams = self._team_names(pool)
        passed = []
        for number, finding in enumerate(output["findings"], 1):
            check = check_finding(finding, pool, index, home)
            if check:
                result["internal"]["withheld"].append({"finding_id": f"DISC-W{number}", "check": check})
                continue
            passed.append(finding)
        result["internal"]["rejected"] = [{"employee_id": r["employee_id"], "reason": r["reason"]}
                                          for r in output["rejected"] if r["employee_id"] in own]
        ranked = sorted(passed, key=lambda f: rank_key(f, index), reverse=True)
        supported = set()
        for position, finding in enumerate(ranked, 1):
            fid = f"DISC-{position}"
            summary_text, count_a = redact(finding["work_summary"], self.data.sanitize, own)
            why_text, count_b = redact(finding["why_it_matters"], self.data.sanitize, own)
            result["internal"]["redactions"] += count_a + count_b
            refs = []
            for evidence in finding["evidence_ids"]:
                for ref in index[evidence]["item"].get("work_refs", []):
                    if ref not in refs:
                        refs.append(ref)
            team = teams.get(finding["beneficiary_manager_id"], "Other team")
            if finding["kind"] == "team_pattern":
                supported.add(team)
            if position > DETAILED + ONE_LINE:
                result["more_findings"]["not_listed"] += 1
                continue
            if position > DETAILED:
                result["more_findings"]["listed"].append({"finding_id": fid, "employee_id": finding["employee_ids"][0],
                                                          "beneficiary_team": team})
                continue
            checked = {"finding_id": fid, "kind": finding["kind"], "employee_ids": list(finding["employee_ids"]),
                       "beneficiary_team": team, "work_summary": summary_text, "why_it_matters": why_text,
                       "visibility_state": finding["visibility_state"], "recognition_state": finding["recognition_state"],
                       "evidence_ids": list(finding["evidence_ids"]), "work_refs": refs,
                       "quotes": [{"source_id": q["source_id"], "text": q["text"].strip()} for q in finding["quotes"]],
                       "actions": []}
            recipient = self.data.team_manager(finding["beneficiary_manager_id"]) or {}
            for action_type in dict.fromkeys(finding["action_types"]):
                if not action_allowed(action_type, finding, pool, index):
                    result["internal"]["withheld"].append({"finding_id": fid, "check": "action_trigger_mismatch",
                                                           "action_type": action_type})
                    continue
                person = finding["kind"] == "person"
                checked["actions"].append({
                    "action_id": f"ACT-{fid[5:]}-{len(checked['actions']) + 1}", "action_type": action_type,
                    "subject_kind": "person" if person else "team",
                    "subject_id": finding["employee_ids"][0] if person else home,
                    "beneficiary_team": team, "beneficiary_manager_id": finding["beneficiary_manager_id"], "work_refs": refs,
                    # Allow-list: the partner manager is named only in their own A2/A4 recipient field.
                    "recipient": {"manager_id": recipient.get("manager_id"), "name": recipient.get("manager_name")}
                                 if action_type in ("A2", "A4") and recipient else None,
                    "draft_text": draft(action_type, checked, names, recipient.get("manager_name") or f"{team} manager")})
            result["findings"].append(checked)
        for lead in result["team_pattern_leads"]:
            lead["judged"] = "supported" if lead["beneficiary_team"] in supported else "not_supported"
        withheld = [w for w in result["internal"]["withheld"] if "action_type" not in w]
        if not output["findings"]:
            status = "no_findings"
        elif not passed:
            status = "all_withheld"
        elif withheld or selection == "failed":
            status = "partial"
        else:
            status = "findings"
        return self._finish(result, status)

    def _finish(self, result, status, reason=None):
        result["status"] = status
        result["internal"]["failure_reason"] = reason
        result["usage"] = {"calls": self.calls, "selection_calls": self.kinds.count("selection"),
                           "schema_retries": int(self.retry_used), **self.usage}
        names = {p["Employee_ID"]: p["Employee_Name"] for p in self.data.roster()}
        result["section"] = provenance(result, render(result, names, reason))
        record("agent_finished", agent=self.name, status=status, calls=self.calls,
               findings=len(result["section"]["finding_ids"]))
        return result
