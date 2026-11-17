"""Code-built Discovery section: pointer line, findings, action drafts. Not reviewed by ZeroSugar."""

LABEL = "Checked by code; not reviewed by ZeroSugar"

ACTION_NAMES = {"A1": "Recognize a contribution", "A2": "Request feedback from the benefited team",
                "A3": "Workload conversation", "A4": "Ask for visibility",
                "A5": "Performance-review note", "A6": "Team process change"}

# Filled only from the checked finding's fields. Each avoids its "must not claim" (plan 6.2).
TEMPLATES = {
    "A1": "Recognition note (personalize before sending): {people} supported {team}. {work_summary} {why_it_matters} Thank you for this work.",
    "A2": "To: {recipient} ({team} manager)\nHi {recipient}, {people} on my team supported your team: {work_summary} Could you share feedback on how this work went for {team}?",
    "A3": "1:1 agenda with {people}: review the cross-team and after-hours load in this period, including the work for {team}; agree on what to keep, hand off or make visible.",
    "A4": "To: {recipient} ({team} manager)\nHi {recipient}, when your team gives feedback on work by {people}, such as: {work_summary} could you copy me so I can see it?",
    "A5": "Performance-review note (to verify): {people} contributed to {team}. {work_summary} {why_it_matters}",
    "A6": "Planning item: agree with {team} how requests to {people} are logged and made visible, given the repeated help across quarters.",
}
RECIPIENT_ACTIONS = ("A2", "A4")


def draft(action_type, finding, names, recipient):
    """Render one draft. The partner manager appears only in the A2/A4 recipient line."""
    people = ", ".join(names[e] for e in finding["employee_ids"])
    return TEMPLATES[action_type].format(people=people, team=finding["beneficiary_team"],
        work_summary=finding["work_summary"].strip(), why_it_matters=finding["why_it_matters"].strip(),
        recipient=recipient if action_type in RECIPIENT_ACTIONS else "")


def pointer(status, count):
    if status in ("findings", "partial"):
        return f"Discovery found {count} finding{'s' if count != 1 else ''} about contributions to other teams."
    if status in ("no_candidates", "no_findings"):
        return "No hidden-contribution findings in the selected evidence."
    if status == "all_withheld":
        return "Discovery could not produce verifiable findings."
    return "Discovery could not complete the analysis."


def finding_ids(result):
    return [f["finding_id"] for f in result["findings"]] + [f["finding_id"] for f in result["more_findings"]["listed"]]


def render(result, names, reason=None):
    """Plain text section from the checked result; deterministic for the same input."""
    ids = finding_ids(result)
    lines = [f"Discovery ({LABEL})", pointer(result["status"], len(ids))]
    if result["status"] in ("failed_provider", "failed_budget") and reason:
        lines.append(f"Reason: {reason}.")
    if result["status"] == "all_withheld":
        lines.append(f"Withheld findings: {len(result['internal']['withheld'])}.")
    period = result["period"]
    line = f"Period: {period['start']} to {period['end']}, as of {period['as_of']}."
    if period.get("narrowed_from_hint"):
        line += " Narrowed from the period in your question to the authorized dates."
    lines.append(line)
    coverage = result["coverage"]
    line = f"Coverage: {coverage['people_reviewed']} of {coverage['team_size']} people prioritized for review."
    if coverage["selection"] == "failed":
        line += " The selection step failed, so fewer people were reviewed."
    if coverage["caps_hit"]:
        line += " Evidence caps reached: " + ", ".join(coverage["caps_hit"]) + "."
    lines.append(line)
    for number, finding in enumerate(result["findings"], 1):
        people = ", ".join(names[e] for e in finding["employee_ids"])
        kind = "team pattern" if finding["kind"] == "team_pattern" else "person"
        lines += [f"{number}. {people}: help to {finding['beneficiary_team']} ({kind}, {finding['finding_id']})",
                  f"   What: {finding['work_summary']}",
                  f"   Why it matters: {finding['why_it_matters']}",
                  f"   Recognition: {finding['recognition_state'].replace('_', ' ')}; visibility: {finding['visibility_state'].replace('_', ' ')}",
                  f"   Sources: {', '.join(finding['evidence_ids'])}"]
        lines += [f"   Quote ({q['source_id']}): \"{q['text']}\"" for q in finding["quotes"]]
        for action in finding["actions"]:
            lines.append(f"   Action {action['action_type']} {ACTION_NAMES[action['action_type']]} ({action['action_id']}):")
            lines += ["      " + part for part in action["draft_text"].split("\n")]
    listed = result["more_findings"]["listed"]
    if listed:
        lines.append("More findings:")
        lines += [f"- {names[f['employee_id']]}: help to {f['beneficiary_team']} ({f['finding_id']})" for f in listed]
    if result["more_findings"]["not_listed"]:
        lines.append(f"{result['more_findings']['not_listed']} more findings are not listed.")
    return "\n".join(lines)


def provenance(result, rendered):
    return {"present": True, "status": result["status"], "finding_ids": finding_ids(result),
            "reviewed_by_zerosugar": False, "checked_by_code": True, "rendered": rendered}


NOT_RUN = {"present": False, "status": "not_run", "finding_ids": [], "reviewed_by_zerosugar": False,
           "checked_by_code": True, "rendered": ""}
