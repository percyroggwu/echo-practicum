"""Code checks for Discovery's model outputs. A failing finding is withheld, never repaired."""

import re

ACTION_TYPES = ("A1", "A2", "A3", "A4", "A5", "A6")
REJECTION_REASONS = ("already_recognized", "own_team_help", "no_hidden_work", "insufficient_evidence",
                     "effort_without_impact", "credited_to_someone_else", "workload_only")
VISIBILITY = ("praise_not_shared", "no_feedback", "shared")
RECOGNITION = ("recognized", "not_recognized", "unknown")
TEXT_LIMIT = 400
QUOTE_MIN = 10


class SchemaFailure(ValueError):
    """A model output that does not match its contract; `code` is a fixed enum, never source text."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def check_selection(summary, ids):
    """Raise SchemaFailure unless `ids` is exactly the requested set of distinct summary IDs."""
    if not isinstance(ids, list) or any(not isinstance(e, str) for e in ids):
        raise SchemaFailure("selection_not_a_list")
    if len(set(ids)) != len(ids):
        raise SchemaFailure("selection_duplicate")
    if set(ids) & set(summary["lowest"]):
        raise SchemaFailure("selection_satisfaction_slot")
    if not set(ids) <= {line["employee_id"] for line in summary["lines"]}:
        raise SchemaFailure("selection_unknown_id")
    if len(ids) != summary["selection_count"]:
        raise SchemaFailure("selection_wrong_count")
    return list(ids)


def _strings(value, limit=None):
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value) and (limit is None or len(value) <= limit)


def check_judgment_schema(output):
    """Validate the judgment output's shape; strict tool schemas are not trusted to be enforced."""
    if not isinstance(output, dict) or set(output) != {"findings", "rejected"}:
        raise SchemaFailure("judgment_keys")
    if not isinstance(output["findings"], list) or not isinstance(output["rejected"], list):
        raise SchemaFailure("judgment_lists")
    keys = {"kind", "employee_ids", "beneficiary_manager_id", "work_summary", "why_it_matters",
            "visibility_state", "recognition_state", "evidence_ids", "quotes", "action_types"}
    for finding in output["findings"]:
        if not isinstance(finding, dict) or set(finding) != keys:
            raise SchemaFailure("finding_keys")
        if finding["kind"] not in ("person", "team_pattern") or not _strings(finding["employee_ids"], 10) \
                or not finding["employee_ids"] or not _strings(finding["evidence_ids"], 12) or not finding["evidence_ids"]:
            raise SchemaFailure("finding_fields")
        if not all(isinstance(finding[k], str) and finding[k].strip() for k in ("beneficiary_manager_id", "work_summary", "why_it_matters")):
            raise SchemaFailure("finding_text")
        if finding["visibility_state"] not in VISIBILITY or finding["recognition_state"] not in RECOGNITION:
            raise SchemaFailure("finding_states")
        if not isinstance(finding["action_types"], list) or any(a not in ACTION_TYPES for a in finding["action_types"]):
            raise SchemaFailure("finding_actions")
        if not isinstance(finding["quotes"], list) or any(
                not isinstance(q, dict) or set(q) != {"source_id", "text"} or not all(isinstance(q[k], str) for k in q)
                for q in finding["quotes"]):
            raise SchemaFailure("finding_quotes")
    for item in output["rejected"]:
        if not isinstance(item, dict) or set(item) != {"employee_id", "reason"} \
                or not isinstance(item["employee_id"], str) or item["reason"] not in REJECTION_REASONS:
            raise SchemaFailure("rejected_fields")
    return output


def pool_index(pool):
    """record_id -> {'item': visible item, 'people': employees whose bounded items include it}."""
    index = {}
    for person in pool["people"]:
        for item in person["items"]:
            entry = index.setdefault(item["record_id"], {"item": item, "people": set()})
            entry["people"].add(person["employee_id"])
    return index


def disputed_rejections(output, pool, home_manager):
    """IDs rejected as already_recognized although a visible cross-team work item has no recorded recognition."""
    people = {p["employee_id"]: p for p in pool["people"]}
    return [r["employee_id"] for r in output["rejected"]
            if r["reason"] == "already_recognized" and r["employee_id"] in people
            and any(i.get("work_refs") and i.get("beneficiary_manager_id") not in (None, home_manager)
                    and i.get("closing_context", {}).get("recognition_state") == "no_recognition_event_recorded"
                    for i in people[r["employee_id"]]["items"])]


def _load_above_range(person):
    return sum(q["weeks_above_team_range"] for field in person.get("context", {}).get("workload", {}).values()
               for q in field.get("quarters", []))


def check_finding(finding, pool, index, home_manager):
    """Return None when the finding passes, else the first failing check (fixed enum)."""
    people = {p["employee_id"]: p for p in pool["people"]}
    ids = finding["employee_ids"]
    if len(set(ids)) != len(ids) or any(e not in people for e in ids):
        return "person_not_in_pool"
    if (finding["kind"] == "person") != (len(ids) == 1):
        return "kind_mismatch"
    if any(e not in index for e in finding["evidence_ids"]):
        return "unknown_evidence_id"
    cited = [index[e] for e in finding["evidence_ids"]]
    if any(not entry["people"] & set(ids) for entry in cited):
        return "evidence_not_for_subject"
    for quote in finding["quotes"]:
        text = quote["text"].strip()
        if quote["source_id"] not in finding["evidence_ids"] or len(text) < QUOTE_MIN \
                or text not in index[quote["source_id"]]["item"].get("text", ""):
            return "quote_not_in_source"
    beneficiary = finding["beneficiary_manager_id"]
    if beneficiary == home_manager:
        return "own_team_help"
    if beneficiary not in {entry["item"].get("beneficiary_manager_id") for entry in cited}:
        return "beneficiary_not_in_evidence"
    items = [entry["item"] for entry in cited]
    feedback = [i for i in items if i["source"] == "HR_recognition_feedback"]
    visibility = finding["visibility_state"]
    if visibility == "praise_not_shared" and not any(not i.get("details", {}).get("shared_as_of") for i in feedback):
        return "visibility_not_supported"
    if visibility == "shared" and not any(i.get("details", {}).get("shared_as_of") for i in feedback):
        return "visibility_not_supported"
    if visibility == "no_feedback" and feedback:
        return "visibility_not_supported"
    if visibility == "no_feedback":
        # Plan 6.2 "help with no partner feedback": uncited feedback from the beneficiary on the same work counts too.
        work_keys = {(r["type"], r["id"]) for i in items for r in i.get("work_refs") or []}
        if any(i["source"] == "HR_recognition_feedback" and i.get("beneficiary_manager_id") == beneficiary
               and work_keys & {(r["type"], r["id"]) for r in i.get("work_refs") or []}
               for e in ids for i in people[e]["items"]):
            return "visibility_not_supported"
    # Coverage applies to work records; self-review and weekly activity rows carry no work anchor.
    work = [i for i in items if i.get("work_refs")]
    states = [i.get("closing_context", {}) for i in work]
    recognition = finding["recognition_state"]
    if recognition == "recognized" and not any(s.get("recognition_state") == "recorded" for s in states):
        return "recognition_not_supported"
    if recognition == "not_recognized":
        if any(s.get("recognition_state") == "recorded" for s in states):
            return "contradicts_recognition_record"
        if not states or any(s.get("absence_coverage") != "complete" for s in states):
            return "not_recognized_under_unknown_coverage"
    if len(finding["work_summary"]) > TEXT_LIMIT or len(finding["why_it_matters"]) > TEXT_LIMIT:
        return "text_too_long"
    return None


def action_allowed(action_type, finding, pool, index):
    """Whether the action's trigger (plan 6.2) fits the checked finding."""
    person = finding["kind"] == "person"
    if action_type == "A1":
        return person and finding["recognition_state"] != "recognized"
    if action_type == "A2":
        return person and finding["visibility_state"] == "no_feedback"
    if action_type == "A3":
        # Plan 6.2: load above the normal range; a cited weekly row alone does not show that.
        subject = next(p for p in pool["people"] if p["employee_id"] == finding["employee_ids"][0])
        return person and _load_above_range(subject) > 0
    if action_type == "A4":
        return finding["visibility_state"] == "praise_not_shared"
    if action_type == "A5":
        return person
    if action_type == "A6":
        return finding["kind"] == "team_pattern"
    return False


def redact(text, sanitize, own_ids):
    """Replace outside names and IDs; returns (text, replacements). Own-team IDs stay."""
    cleaned = sanitize(text)
    count = int(cleaned != text)
    foreign = [m for m in set(re.findall(r"(?<!\w)E\d{4}(?!\w)", cleaned)) if m not in own_ids]
    for identifier in foreign:
        cleaned = re.sub(r"(?<!\w)" + identifier + r"(?!\w)", "[colleague outside the team]", cleaned)
        count += 1
    return cleaned, count


def rank_key(finding, index):
    """Plan 3.4: independent source types, then a linked goal or blocker, then recency."""
    items = [index[e]["item"] for e in finding["evidence_ids"]]
    linked = any(i["source"] in ("OP_dependency_blockers", "OP_team_goals", "OP_goal_outcomes")
                 or i.get("details", {}).get("Team_Goal_ID") or i.get("details", {}).get("Blocked_Team_Goal_ID")
                 for i in items)
    return (len({i["source"] for i in items}), linked, max((i.get("event_date") or "") for i in items))
