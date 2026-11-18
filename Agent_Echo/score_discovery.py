"""Offline Discovery gate scorer; never instantiates a provider or makes model calls.

Run from Agent_Echo with the system Python and PYTHONPATH=.venv/Lib/site-packages:
  python -B score_discovery.py --output data/discovery_phase6_gate_report.json
Add --regression-log data/discovery_phase6_unit_results.txt after the full
tests/run_phase2_offline.py run; that log is external evidence, not rerun here.

Optional gate-7 input (read only, never generated here):
  {"teams": [{"manager_id": "M01", "selected_employee_ids": ["E....", ...]}, ...]}
Exactly one row per current manager is required, including [] for small teams.
--artifact M32=path.json may be repeated. Findings are observed exclusively in
discovery_section.rendered; this measures visible coverage, not semantic truth.
Scripted judgments test plumbing and withholding, not analytical accuracy.
"""

import argparse
from collections import Counter
import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "echo_discovery_v1.db"
KEY = ROOT.parent / "files_discovery_v1_private" / "QA_discovery_v1_answer_key.csv"
PLAN = ROOT / "DISCOVERY_SCOPE_AND_PLAN_v10_2026-11-15.md"
FOCUSED = ("test_discovery_access.py", "test_discovery_subject.py",
           "test_discovery_signals.py", "test_discovery_prefilter.py",
           "test_discovery_phase2_boundaries.py", "test_discovery_phase3.py",
           "test_discovery_phase4.py", "test_discovery_phase6.py",
           "test_ui_followup.py", "test_ui_scope_clarification.py",
           "test_ui_offline_discovery.py", "test_ui_actions.py", "test_score_discovery.py")


def split(value):
    return [item.strip() for item in re.split(r"[;|]", value or "") if item.strip()]


def status(values):
    values = list(values)
    if "fail" in values:
        return "fail"
    return "pass" if values and all(v == "pass" for v in values) else "unverified"


def check(ok, **evidence):
    return {"status": "pass" if ok else "fail", **evidence}


def install_offline_guard():
    """Forbid real credentials and network even when optional evidence is supplied."""
    def guard(event, args):
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            synthetic = ROOT / "data" / "phase2_test_tmp"
            if path.name in {".env", "connections.private.json", "connections.local.json"} and synthetic not in path.parents:
                raise PermissionError("Credential access is forbidden in offline scoring.")
        if event in {"socket.connect", "socket.getaddrinfo"}:
            raise RuntimeError("Network access is forbidden in offline scoring.")
    sys.addaudithook(guard)


def load_cases(path=KEY):
    # Expectations remain in scorer/test code, never in a runtime prompt or database.
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def current_slots(summary, employees):
    """Derive slots solely from current team_summary output, ignoring Entry_Slot."""
    whole, lowest = set(summary["whole_team"]), set(summary["lowest"])
    return {e: "whole_team" if e in whole else "satisfaction" if e in lowest else "selection"
            for e in employees}


def gate1(cases, database=DB):
    from agents.data_access import DiscoveryData, DiscoveryScope
    from agents.discovery_checks import SchemaFailure, check_selection
    from agents.discovery_tools import prefilter, resolve_subject, team_summary

    with sqlite3.connect(Path(database).as_uri() + "?mode=ro", uri=True) as source:
        managers = [r[0] for r in source.execute("SELECT Manager_ID FROM HR_managers ORDER BY Manager_ID")]
        names = list(source.execute("SELECT Employee_ID,Employee_Name FROM HR_employees"))
        manager_names = list(source.execute("SELECT Manager_ID,Manager_Name FROM HR_managers"))
    totals = Counter()
    teams, plants, failures = {}, [], []
    for manager in managers:
        data = DiscoveryData(database, DiscoveryScope(manager, "2025-10-01", "2026-06-30"))
        try:
            resolved = resolve_subject(data, {"subject_kind": "team"})
            summary = team_summary(data)
            lines = {line["employee_id"]: line for line in summary["lines"]}
            roster = {r["Employee_ID"] for r in data.roster()}
            code = set(summary["whole_team"]) | set(summary["lowest"])
            encoded = json.dumps(summary["lines"], ensure_ascii=False)
            outsiders = [(e, n) for e, n in names if e not in roster] + [(m, n) for m, n in manager_names if m != manager]
            outside_names = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(n) for _, n in outsiders if n) + r")(?!\w)")
            leak = bool(outside_names.search(encoded))
            totals["summary_privacy_order_failures"] += bool(leak or list(lines) != sorted(lines) or any(
                word in encoded.lower() for word in ("pulse_score", "satisfaction", "weight", "strength", "source_text")))
            totals["small_teams"] += len(roster) <= 10
            totals["small_team_failures"] += len(roster) <= 10 and code != roster
            rows = {r["record_id"]: r for values in data.evidence().values() for r in values if r.get("record_id")}
            pools = {}

            def pool_for(required=()):
                selected = sorted(set(required) - code)
                selected += [e for e in lines if e not in selected][:max(0, summary["selection_count"] - len(selected))]
                if len(selected) > summary["selection_count"]:
                    raise ValueError("Conditional fixture exceeds the actual selection cap.")
                key = tuple(selected)
                if key not in pools:
                    pool = prefilter(data, resolved, selected_employee_ids=selected if summary["selection_count"] else None)
                    pools[key] = pool
                    items = [i for p in pool["people"] for i in p["items"]]
                    totals["cap_failures"] += len(pool["people"]) > 10 or any(len(p["items"]) > 8 for p in pool["people"])
                    totals["pool_date_failures"] += sum(not (
                        "2025-10-01" <= i["event_date"][:10] <= "2026-06-30" and
                        i["recorded_date"][:10] <= "2026-06-30") for i in items)
                    serialized = json.dumps(pool, ensure_ascii=False)
                    totals["pool_privacy_failures"] += bool(outside_names.search(serialized))
                    totals["pool_scope_failures"] += bool({p["employee_id"] for p in pool["people"]} - roster)
                return pools[key]

            for case in [c for c in cases if c["Manager_ID"] == manager and c["Kind"] == "case"]:
                employees = split(case["Employee_IDs"])
                if not employees:
                    failures.append({"case_id": case["Case_ID"], "reason": "empty_expected_subject"})
                slots = current_slots(summary, employees)
                expected = {e for e in split(case["Evidence_IDs"]) if e not in rows or (
                    "2025-10-01" <= rows[e].get("event_date", "")[:10] <= "2026-06-30" and
                    rows[e].get("recorded_date", "")[:10] <= "2026-06-30")}
                reached = []
                for employee in employees:
                    if employee not in roster:
                        failures.append({"case_id": case["Case_ID"], "employee_id": employee, "reason": "outside_frozen_roster"})
                        continue
                    if employee not in code:
                        totals["summary_expected"] += 1
                        facts = lines.get(employee, {})
                        beneficiary = case["Beneficiary_Team"]
                        good = any(b["manager_id"] == beneficiary and b["help_records"] > 0 for b in facts.get("beneficiaries", []))
                        totals["summary_reached"] += good
                    pool = pool_for([employee])
                    items = [i for p in pool["people"] if p["employee_id"] == employee for i in p["items"]]
                    hit = bool(expected & {i["record_id"] for i in items})
                    reached.append(hit)
                    if case["Origin"] == "hand_built":
                        totals["handbuilt_expected"] += 1
                        totals["handbuilt_reached"] += hit
                plants.append({"case_id": case["Case_ID"], "manager_id": manager, "origin": case["Origin"],
                               "employee_ids": employees, "slots": slots, "conditional_prefilter_reached": bool(reached) and all(reached)})
                if case["Origin"] == "automatic":
                    totals["automatic_expected"] += 1
                    totals["automatic_reached"] += bool(reached) and all(reached)
                    totals["automatic_code_slot"] += all(s != "selection" for s in slots.values())
                    totals["automatic_selection_slot"] += any(s == "selection" for s in slots.values())
            # P5's linked contributors have their own authorized home-team checks.
            for employee in {"M46": ["E0046"], "M31": ["E0051", "E0066"], "M01": ["E0074", "E0085"]}.get(manager, []):
                pool = pool_for([employee])
                items = [i for p in pool["people"] if p["employee_id"] == employee for i in p["items"]]
                totals["p5_other_expected"] += 1
                totals["p5_other_reached"] += any(i["source"] == "HR_self_review_items" for i in items)
            teams[manager] = {"team_size": len(roster), "code_slot": sorted(code), "lowest": summary["lowest"],
                              "selection_count": summary["selection_count"], "summary_ids": list(lines)}
            if manager == "M14":
                p5 = lines.get("E0001", {})
                totals["p5_distinctive"] = p5.get("self_review_cross_team", 0) + p5.get("self_review_unmatched_initiative", 0)
            if manager == "M32":
                totals["p6_distinctive"] = sum(b["other_text_mentions"] for b in lines.get("E0970", {}).get("beneficiaries", []))
                focus = resolve_subject(data, {"subject_kind": "team", "focus_hint": "M16"})
                fs = team_summary(data, focus_hint=focus["focus_hint"])
                required = {"E1401", "E1586", "E0561"}
                ids = {x["employee_id"] for x in fs["lines"]}
                focus_ok = required <= ids and all(any(b["manager_id"] == "M16" and b["help_records"] > 0 for b in x["beneficiaries"])
                    for x in fs["lines"] if x["employee_id"] in required)
                if not fs["selection_count"]:
                    fp = prefilter(data, focus)
                    focus_ok &= required <= {p["employee_id"] for p in fp["people"]}
                totals["focus_ok"] = focus_ok
            if summary["selection_count"]:
                valid = list(lines)[:summary["selection_count"]]
                bad = [valid + ["E-UNKNOWN"], valid[:-1], ["E-UNKNOWN"] + valid[1:], [valid[0]] * len(valid)]
                if summary["lowest"]:
                    bad.append([summary["lowest"][0]] + valid[1:])
                for choice in bad:
                    totals["bad_selection_expected"] += 1
                    try:
                        check_selection(summary, choice)
                    except SchemaFailure:
                        totals["bad_selection_refused"] += 1
            print(f"Gate 1: {manager} checked ({len(teams)}/{len(managers)} teams)", flush=True)
        finally:
            data.close()
    expected_slots = {"M32": ["E2198", "E0010", "E1748", "E2156", "E1401"],
                      "M14": ["E1183", "E1209", "E0450", "E0885", "E1088"]}
    checks = {
        "all_60_managers": check(len(teams) == 60, measured=len(teams)),
        "satisfaction_slots": check(all(teams[m]["lowest"] == ids for m, ids in expected_slots.items())),
        "whole_small_teams": check(totals["small_teams"] > 0 and not totals["small_team_failures"]),
        "summary_positive_beneficiary_recall": check(totals["summary_expected"] > 0 and totals["summary_expected"] == totals["summary_reached"]),
        "distinctive_p5_p6": check(totals["p5_distinctive"] > 0 and totals["p6_distinctive"] > 0),
        "summary_privacy_and_order": check(not totals["summary_privacy_order_failures"]),
        "conditional_prefilter_handbuilt": check(totals["handbuilt_expected"] > 0 and totals["handbuilt_expected"] == totals["handbuilt_reached"] and not failures),
        "conditional_prefilter_automatic": check(totals["automatic_expected"] > 0 and totals["automatic_reached"] / totals["automatic_expected"] >= .95),
        "p5_other_managers": check(totals["p5_other_expected"] == totals["p5_other_reached"] == 5),
        "selection_schema": check(totals["bad_selection_expected"] > 0 and totals["bad_selection_expected"] == totals["bad_selection_refused"]),
        "beneficiary_focus": check(bool(totals["focus_ok"])),
        "caps": check(not totals["cap_failures"]),
        "pool_dates_scope_privacy": check(not any(totals[k] for k in ("pool_date_failures", "pool_scope_failures", "pool_privacy_failures"))),
    }
    return {"status": status(c["status"] for c in checks.values()), "checks": checks, "totals": dict(totals),
            "teams": teams, "plants": plants, "failures": failures,
            "limitation": "Conditional recorded choices measure evidence retention, not model selection or finding accuracy."}


def score_selection(report, measured):
    """Score an existing selection-only capture against current slots, never run one."""
    teams = measured["teams"]
    rows = report.get("teams") if isinstance(report, dict) else None
    if not isinstance(rows, list):
        raise ValueError("Selection report must contain a teams list.")
    by_id = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("manager_id") not in teams or row["manager_id"] in by_id:
            raise ValueError("Selection report contains an unknown or duplicate manager.")
        manager = row["manager_id"]
        selected, team = row.get("selected_employee_ids"), teams[manager]
        if (not isinstance(selected, list) or any(not isinstance(e, str) for e in selected) or
                len(selected) != team["selection_count"] or len(set(selected)) != len(selected) or
                not set(selected) <= set(team["summary_ids"]) or set(selected) & set(team["code_slot"])):
            raise ValueError("Selection IDs must be exactly the current requested distinct summary IDs.")
        by_id[manager] = set(selected) | set(team["code_slot"])
    if set(by_id) != set(teams):
        raise ValueError("Selection report must contain every current manager exactly once.")
    output, expected, reached = {}, 0, 0
    for manager in teams:
        plants = [p for p in measured["plants"] if p["manager_id"] == manager]
        missed = [p["case_id"] for p in plants if not p["employee_ids"] or not set(p["employee_ids"]) <= by_id[manager]]
        automatic = [p for p in plants if p["origin"] == "automatic"]
        hits = sum(bool(p["employee_ids"]) and set(p["employee_ids"]) <= by_id[manager] for p in automatic)
        expected += len(automatic)
        reached += hits
        output[manager] = {"pool_ids": sorted(by_id[manager]), "automatic_expected": len(automatic),
                           "automatic_reached": hits, "missed_plants": missed}
    recall = reached / expected if expected else None
    return {"status": "pass" if recall is not None and recall >= .95 else "fail", "teams": output,
            "automatic_recall": recall, "automatic_expected": expected, "automatic_reached": reached,
            "unverified": ["Finding judgments, D1-D8 rejection and direct-person D8 require separate authorized captures."]}


def score_artifact(artifact, cases, manager_id):
    """Read ONLY the published section, including its code-authored rendered sources."""
    section = artifact.get("discovery_section")
    if not isinstance(section, dict):
        return {"status": "unverified", "reason": "discovery_section missing", "cases": []}
    text = section.get("rendered", "")
    if not isinstance(text, str):
        raise ValueError("Section rendered content must be text.")
    observed = []
    for case in cases:
        if case["Manager_ID"] == manager_id:
            evidence = split(case["Evidence_IDs"])
            hits = [e for e in evidence if re.search(r"(?<![\w-])" + re.escape(e) + r"(?![\w-])", text)]
            observed.append({"case_id": case["Case_ID"], "kind": case["Kind"], "visible_evidence_ids": hits,
                             "observed_in_section": bool(hits)})
    return {"status": "observed", "section_status": section.get("status"), "finding_ids": section.get("finding_ids", []),
            "cases": observed, "run_seconds": artifact.get("run_seconds", "not_recorded"),
            "limitation": "Visible listed source IDs establish section coverage only; one-line findings lack source IDs and semantic matching remains unverified."}


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = {}

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes.setdefault(test.id(), "pass")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes[test.id()] = "fail"

    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes[test.id()] = "fail"

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes[test.id()] = "unverified"

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.outcomes[test.id()] = "fail"

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.outcomes[test.id()] = "unverified"

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.outcomes[test.id()] = "fail"


def run_checks():
    sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
    import run_phase2_offline as runner
    import tempfile
    runner.TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    sys.addaudithook(runner.offline_audit)
    transcript = io.StringIO()
    with patch.object(tempfile, "tempdir", str(runner.TEMP_ROOT)), \
            patch.object(Path, "is_file", lambda p: False if runner.protected(p) else runner._is_file(p)), \
            patch.object(os, "mkdir", runner.test_mkdir), contextlib.redirect_stdout(transcript), contextlib.redirect_stderr(transcript):
        suite = unittest.TestSuite()
        for filename in FOCUSED:
            if (ROOT / "tests" / filename).exists():
                suite.addTests(unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern=filename))
        result = unittest.TextTestRunner(stream=transcript, verbosity=1, resultclass=RecordedResult).run(suite)
    return {"mode": "focused_offline_checks", "tests_run": result.testsRun,
            "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
            "successful": result.wasSuccessful(), "outcomes": result.outcomes,
            "skip_reasons": [{"test": t.id(), "reason": why} for t, why in result.skipped],
            "transcript": transcript.getvalue()}


def regression_evidence(path):
    if path is None:
        return {"status": "unverified", "reason": "No full offline runner log supplied."}
    raw = Path(path).read_bytes()
    content = raw.decode("utf-8-sig")
    summaries = list(re.finditer(r"(?m)^Ran (\d+) tests? in [\d.]+s\s*$", content))
    if len(summaries) != 1:
        return {"status": "unverified", "source": str(path), "reason": "Expected exactly one unittest summary."}
    summary = summaries[0]
    ending = content[summary.end():].strip()
    successful = int(summary.group(1)) > 0 and bool(re.match(r"^OK(?: \(skipped=\d+\))?(?:\s|$)", ending))
    failed = ending.startswith("FAILED")
    return {"status": "pass" if successful else "fail" if failed else "unverified", "source": str(path),
            "tests_run": int(summary.group(1)), "log_sha256": hashlib.sha256(raw).hexdigest(),
            "evidence_kind": "Externally supplied full-run log; scorer does not establish its command, freshness or source identity.",
            "unverified": ["Any skipped tests remain unverified; inspect the supplied log for reasons."] if "skipped=" in ending else []}


def plan_requirements():
    """Keep every offline gate requirement visible, even where evidence is incomplete."""
    text = PLAN.read_text(encoding="utf-8")
    section = text.split("## 8. Evaluation and gates", 1)[1].split("**Live**", 1)[0]
    groups = re.split(r"(?m)^([1-6])\. \*\*", section)[1:]
    return {number: body.strip() for number, body in zip(groups[::2], groups[1::2])}


def assertion_gate(evidence, requirements, bindings, unverified=()):
    """Missing or skipped assertions never become passes merely because a module ran."""
    checks = {}
    for requirement, tests in bindings.items():
        outcomes = {test: evidence["outcomes"].get(test, "unverified") for test in tests}
        checks[requirement] = {"status": status(outcomes.values()), "test_outcomes": outcomes}
    for requirement in unverified:
        checks[requirement] = {"status": "unverified", "reason": "No dedicated assertion in this scorer run."}
    return {"status": status(c["status"] for c in checks.values()), "checks": checks,
            "requirements": requirements, "unverified": list(unverified),
            "evidence_kind": "Executed assertions with scripted judgments; plumbing only, not accuracy evidence."}


def bound(class_name, *methods):
    return [f"{class_name}.test_{method}" for method in methods]


def mapped_gates(evidence, requirements):
    checks = "test_discovery_phase3.CheckTests"
    subject = "test_discovery_subject.ResolveTests"
    original = "test_discovery_phase4.OriginalDiscoveryTests"
    agent = "test_discovery_phase3.DiscoveryAgentTests"
    budget = "test_discovery_phase3.BudgetTests"
    phase6 = "test_discovery_phase6.DiscoveryPhase6Tests"
    integration = "test_discovery_phase6.DiscoveryPhase6IntegrationTests"
    follow = "test_ui_followup.FollowUpTests"
    return {
        "2": assertion_gate(evidence, requirements["2"], {
            "Fabricated IDs/quotes, foreign subjects and unknown-coverage non-recognition are withheld": bound(checks, "synthetic_bad_outputs_are_withheld"),
            "Invalid action triggers are refused": bound(checks, "action_triggers"),
        }),
        "3": assertion_gate(evidence, requirements["3"], {
            "Exact, ambiguous, unknown, outside and two-to-five subjects, accent/case matching and >5 limit": bound(subject,
                "people_and_accent", "ambiguous_and_unknown", "outside", "limits_and_dates", "every_supported_people_count_and_uppercase_accent_matching"),
            "Recorded team/person/focus questions run Discovery; other-team comparison is declined before evidence": bound(original,
                "team_question_runs_discovery_once_and_appends_the_section_after_review", "out_of_scope_subject_is_declined_before_any_evidence_is_read",
                "comparison_with_another_team_is_declined_and_beneficiary_focus_is_processed") + bound(agent, "named_people_make_no_selection_call"),
            "Temporal comparison stays a team question": bound(integration, "recorded_temporal_comparison_stays_team_scoped"),
            "Unresolved subject clarifies; original intent, period and chosen ID survive a changed replanned name": bound(original,
                "unresolved_name_gets_a_clarification_and_the_chosen_id_is_applied") + bound(integration, "changed_replanned_name_applies_chosen_id_and_retains_period") +
                bound("test_ui_scope_clarification.ScopeClarificationTests", "valid_clarification_is_passed_with_question_unchanged"),
        }),
        "4": assertion_gate(evidence, requirements["4"], {
            "P1 A1/A4 observed; P3 not yet": bound(follow, "p1_a1_and_a4_observed_and_p3_not_yet"),
            "Proposed means pending decision": bound(follow, "proposed_action_is_pending_decision"),
            "Empty complete source means not yet; accepted M41 plant A4 under named partial coverage means unknown": bound(follow,
                "empty_table_under_complete_coverage_is_not_yet", "partial_coverage_gives_unknown"),
            "A3 matches workload only": bound(follow, "a3_matches_only_workload"),
            "Follow-up cannot add people outside frozen roster": bound("test_discovery_access.DiscoveryAccessTests", "followup_freezes_roster_and_saved_anchors"),
        }),
        "6": assertion_gate(evidence, requirements["6"], {
            "No candidates differs from no findings; failures never mean no hidden work": bound(phase6,
                "no_candidates_costs_no_discovery_model_call", "pointer_and_provenance_for_every_status") + bound(agent, "all_withheld_and_no_findings"),
            "As-of recognition/share states exclude later events": bound("test_discovery_phase2_boundaries.Phase2BoundaryTests",
                "recognition_closing_state_uses_asof_and_the_same_employee") + bound("test_discovery_access.DiscoveryAccessTests", "sharing_and_external_privacy"),
            "CLI and backend require the fixed discovery_v1 range": bound("test_discovery_phase4.CommandLineTests",
                "discovery_v1_rejects_a_missing_or_different_range") + bound("test_ui_scope_clarification.ScopeClarificationTests", "other_or_missing_dates_rejected"),
            "Original released answer is byte-identical to reviewed candidate and section tampering is refused": bound(integration,
                "release_rejects_tampered_section_and_keeps_reviewed_answer"),
            "D1/D3 closing context survives eight-item cap": bound("test_discovery_prefilter.PrefilterTests", "pack_decoy_contradictions_in_eight_record_helper"),
            "Status pointers, checked provenance, five detailed plus five one-line cap and overflow": bound(phase6,
                "pointer_and_provenance_for_every_status", "top_five_plus_five_and_overflow_are_checked_and_rendered"),
            "Section resets between questions and is not_run after a decline": bound(integration, "findings_then_declined_resets_section_in_same_agent"),
            "Original failure artifact and manager API projection retain exact section outside answer": bound(integration,
                "original_failure_section_survives_artifact_and_manager_projection"),
            "Discovery events reach offline stage; manager projection retains section and clarification": bound("test_ui_offline_discovery.OfflineDiscoveryTests",
                "m32_has_discovery_events_section_and_actions") + bound("test_ui_scope_clarification.ScopeClarificationTests", "manager_view_projects_section_and_candidates_not_discovery"),
            "Original compose and ZeroSugar inputs exclude Discovery": bound(original, "team_question_runs_discovery_once_and_appends_the_section_after_review"),
            "Refunds restore remaining budget without changing raw counters, including timeout/failure": bound(budget,
                "refund_restores_remaining_without_changing_raw_counters", "paused_seconds_extend_the_effective_deadline") + bound(agent,
                "shared_schema_retry_and_three_call_cap", "selection_timeout_still_judges_and_refunds", "judgment_timeout_gives_failed_budget_and_full_refund"),
            "Three logical calls despite transport/schema retries, no selection for named people, and failed selection remains partial": bound(phase6,
                "three_logical_calls_with_transport_and_shared_schema_retry") + bound(agent, "named_people_make_no_selection_call", "failed_selection_reviews_the_satisfaction_slot_only"),
            "No call when retry budget is exhausted; hung request counted once": bound(phase6, "schema_retry_checks_available_budget_before_calling") +
                bound(budget, "hung_request_ends_at_the_call_deadline_and_is_counted_once"),
            "Scorer finds visible source IDs only through discovery_section": bound("test_score_discovery.DiscoveryScorerTests", "findings_are_read_only_from_the_published_section"),
        }, unverified=[
            "Every external name in the published section is excluded except an A2/A4 recipient",
            "Manager page renders six agents and declined Why card from projected code guardrail",
            "Correction rounds never rerun Discovery",
            "A different record ID for the same work closes A1; edits reject foreign references",
            "Export retains discovery_section with reviewed_by_zerosugar false",
            "Report-reader independently finds P1-P6 through the section",
            "Original closing turn and remaining seconds exactly match a no-Discovery control after all refunds",
            "Original completes closing turn after its post-Discovery budget is exhausted",
        ]),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "discovery_phase6_gate_report.json")
    parser.add_argument("--regression-log", type=Path)
    parser.add_argument("--selection-report", type=Path)
    parser.add_argument("--artifact", action="append", default=[], metavar="MANAGER=PATH")
    args = parser.parse_args(argv)
    install_offline_guard()
    began = time.monotonic()
    cases = load_cases()
    measured = gate1(cases)
    evidence = run_checks()
    requirements = plan_requirements()
    gates = {"1": measured}
    gates["1"]["requirements"] = requirements["1"]
    gates.update(mapped_gates(evidence, requirements))
    gates["5"] = {**regression_evidence(args.regression_log), "requirements": requirements["5"]}
    selection = {"status": "not_run", "reason": "No existing selection-only report supplied; no live call was made."}
    if args.selection_report:
        selection = score_selection(json.loads(args.selection_report.read_text(encoding="utf-8")), measured)
        selection["source"] = str(args.selection_report)
    artifacts = []
    for spec in args.artifact:
        manager, separator, filename = spec.partition("=")
        if not separator or manager not in measured["teams"]:
            parser.error("--artifact requires an existing manager ID followed by =PATH")
        artifacts.append({"source": filename, "manager_id": manager,
                          **score_artifact(json.loads(Path(filename).read_text(encoding="utf-8")), cases, manager)})
    transcript = evidence.pop("transcript")
    report = {"rules_version": "discovery-phase6-offline-v1", "gates": gates, "gate7_selection_only": selection,
              "artifact_section_coverage": artifacts, "test_execution": evidence,
              "elapsed_seconds": round(time.monotonic() - began, 2),
              "database_sha256": hashlib.sha256(DB.read_bytes()).hexdigest(),
              "limitations": ["Zero provider/model calls. Scripted judgments establish plumbing, not accuracy.",
                              "Conditional plant selections are independent fixtures and do not imply simultaneous M32 recall.",
                              "Gate7 findings and all gates8-11 remain outside this offline report."],
              "acceptance_status": status(g["status"] for g in gates.values())}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".tests.txt").write_text(transcript, encoding="utf-8")
    print(json.dumps({"output": str(args.output), "gates": {k: gates[k]["status"] for k in sorted(gates)},
                      "gate7": selection["status"], "tests_run": evidence["tests_run"],
                      "acceptance_status": report["acceptance_status"]}))
    return 1 if report["acceptance_status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
