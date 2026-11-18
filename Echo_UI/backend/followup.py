"""T5.2 follow-up: code only, no model. Reads later source records through FollowUpScope.

"observed" means a matching record exists in the synthetic data; nothing is sent externally.
"""
import sys
from pathlib import Path

ECHO = Path(__file__).resolve().parents[2] / "Agent_Echo"
sys.path.insert(0, str(ECHO))
from agents.data_access import DISCOVERY_RANGE, DiscoveryData, DiscoveryScope, FollowUpData, FollowUpScope, _FOLLOWUP_END, _quarter  # noqa: E402

DATABASE = ECHO / "data" / "echo_discovery_v1.db"  # tests point this elsewhere if needed
SOURCE = {"A1": "HR_recognition_events", "A2": "HR_recognition_feedback", "A3": "HR_one_on_ones",
          "A4": "HR_recognition_feedback", "A5": "HR_review_notes", "A6": "OP_team_plans"}
NEEDS_WORK = {"A1", "A2", "A4", "A5"}


def result(status, action_type, reason, window=None, matched=(), coverage=None):
    return {"status": status, "action_type": action_type, "window": window, "matched": list(matched),
            "coverage": coverage, "reason": reason}


def follow_up(action, manager_id, database=None):
    """One result for a saved action, from its last version and the manager's decision date."""
    current, kind = action["current"], action["current"]["action_type"]
    if action["state"] == "proposed":
        return result("pending_decision", kind, "Pending decision: only accepted or edited actions are followed up.")
    if action["state"] == "dismissed":
        return result("dismissed", kind, current["reason"] or "Dismissed.")
    window = {"start": current["decided_on"], "end": _FOLLOWUP_END}
    refs, beneficiary = current["work_refs"], action.get("beneficiary_manager_id")
    if kind in NEEDS_WORK and not refs:
        return result("unknown", kind, "This finding has no anchored work, so the action cannot be matched to specific work.", window)
    if kind in ("A2", "A4", "A6") and not beneficiary:
        return result("unknown", kind, "The saved action has no beneficiary manager ID to match.", window)
    database = database or DATABASE
    try:
        if action["subject_kind"] == "person":
            people = (action["subject_id"],)
        else:  # a team action: any person on the frozen roster can be the match
            roster = DiscoveryData(database, DiscoveryScope(manager_id, *DISCOVERY_RANGE))
            people = tuple(p["Employee_ID"] for p in roster.roster())
            roster.close()
        data = FollowUpData(database, FollowUpScope(manager_id, window["start"], window["end"], people, tuple(refs),
                                                    (beneficiary,) if beneficiary else ()))
        try:
            rows = data.evidence()
        finally:
            data.close()
    except ValueError as error:  # outside the frozen roster, or dates outside the follow-up range
        return result("unknown", kind, f"The saved action cannot be followed up: {error}", window)

    def inside(value):
        return bool(value) and window["start"] <= str(value)[:10] <= window["end"]

    def on_work(r):
        return any(ref in refs for ref in r["work_refs"])

    def by_beneficiary(r):  # by manager ID: team names repeat across managers
        return r["beneficiary_manager_id"] == beneficiary

    mine = lambda r: r["Employee_ID"] in people  # noqa: E731
    table = rows[SOURCE[kind]]
    if kind == "A1":
        hits = [r for r in table if mine(r) and on_work(r) and inside(r["event_date"])]
    elif kind == "A2":
        hits = [r for r in table if mine(r) and on_work(r) and by_beneficiary(r) and inside(r["event_date"])]
    elif kind == "A3":
        hits = [r for r in table if mine(r) and r["Manager_ID"] == manager_id and r["Topic_Code"] == "workload" and inside(r["event_date"])]
    elif kind == "A4":  # the share date counts, not the feedback date
        hits = [r for r in table if mine(r) and on_work(r) and by_beneficiary(r) and r["shared_as_of"] and inside(r["shared_event_date"])]
    elif kind == "A5":
        hits = [r for r in table if mine(r) and on_work(r) and inside(r["event_date"])]
    else:  # A6: the evidence query already limits Planning_Manager_ID to the home manager
        hits = [r for r in table if r["beneficiary_manager_id"] == beneficiary and inside(r["event_date"])]
    quarters = sorted({_quarter(window["start"]), _quarter(window["end"])})  # the window lies within one quarter
    declared = {r["Quarter"]: r["Coverage_Status"] for r in rows["OP_source_coverage"] if r["Source_Table"] == SOURCE[kind]}
    coverage = {"source_table": SOURCE[kind], "quarters": {q: declared.get(q, "undeclared") for q in quarters}}
    if hits:
        return result("observed", kind, f"{len(hits)} matching record(s) exist in the synthetic source data.", window,
                      [r["record_id"] for r in hits], coverage)
    if all(v == "complete" for v in coverage["quarters"].values()):
        return result("not_yet", kind, "No matching record yet; the source is declared complete for the whole window.", window, (), coverage)
    return result("unknown", kind, "No matching record, and coverage of the source is partial or undeclared for part of the window.",
                  window, (), coverage)
