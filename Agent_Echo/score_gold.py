"""Score M1/M2 runs against the frozen human gold. No API calls; no keyword matching of model text.

Automatic: decision versus gold, protocol failures, label disputes against the human labels
(Part A), whether Original disputed the false correction R6, and a text diff of each repair.
Human: whether a reviewer's objections include each "Must flag" item, which objections are
false, and whether a repair did "Must change" without losing "Must keep". Those go into an
adjudication sheet with the same '>' answer format as the casebook.

    python score_gold.py sheet  RESULTS.json SHEET.md      # write the adjudication sheet
    python score_gold.py report RESULTS.json SHEET.md      # totals against Part D thresholds

RESULTS.json: {"casebook_sha256": ..., "runs": [run, ...]}. A reviewer run (B cases) has case,
agent_version, profile, repeat, status ("completed" or "protocol_failure"), decision, issues
(list of strings) and label_disputes ([{source_id, proposed_label, problem}]). A repair run
(R cases) has case, agent_version, profile, repeat, status, answer and correction_response
("fixed", "disputed" or null).
"""

from difflib import unified_diff
import json
from pathlib import Path
import re
import sys

from gold_cases import CASEBOOK_HASHES, OUTPUT as CASES

NO_DEFECT = {"B1", "B4", "B13"}       # gold decision accept: nothing to flag
LABELS = ("positive", "negative", "neutral", "mixed", "indeterminate")


def run_key(run):
    return f"{run['case']} | {run['agent_version']} | {run['profile']} | {run['repeat']}"


def acceptable_labels(gold):
    """CMT id -> labels the annotator accepts (own label plus 'Also acceptable')."""
    result = {}
    for key, entry in gold.items():
        if key.startswith("A") and key[1:].isdigit():
            text = (entry.get("Your label", "") + " " + entry.get("Also acceptable", "")).lower()
            result["survey:" + entry["title"].strip()] = {label for label in LABELS if label in text}
    return result


def automatic(run, gold, cases):
    """Checks code can decide without reading model prose."""
    result = {"protocol_failure": run["status"] != "completed"}
    if run["case"].startswith("B"):
        expected = gold[run["case"]]["Decision"].strip().lower()
        result["decision_matches_gold"] = (not result["protocol_failure"]) and run.get("decision") == expected
        accepted = acceptable_labels(gold)
        result["false_label_disputes"] = [d["source_id"] for d in run.get("label_disputes", [])
                                          if d.get("source_id") in accepted and stored_label(cases[run["case"]], d["source_id"]) in accepted[d["source_id"]]]
    else:
        result["disputed"] = run.get("correction_response") == "disputed"
        result["false_correction_followed"] = run["case"] == "R6" and not result["protocol_failure"] and not result["disputed"]
    return result


def stored_label(case, source_id):
    return next((r["label"] for e in case["evidence"] for r in e.get("classification_records", []) or []
                 if r["citation_id"] == source_id), None)


def sheet(results, cases_data):
    gold, cases, repairs = cases_data["gold"], cases_data["cases"], cases_data["repairs"]
    lines = ["# Adjudication sheet", "",
             "For each run, read the gold and the model output, then answer after each '>'.",
             "Automatic checks are already filled in and need no answer.", ""]
    for run in results["runs"]:
        auto = automatic(run, gold, cases)
        g = gold[run["case"]]
        lines += ["---", "", f"### {run_key(run)}", "", f"Automatic: `{json.dumps(auto)}`", ""]
        if run["case"].startswith("B"):
            lines += [f"Gold decision: {g['Decision']}", f"Gold must flag: {g['Must flag']}",
                      f"Gold must not flag: {g['Must not flag']}", "",
                      f"Model decision: {run.get('decision')}", "Model objections:"]
            lines += [f"- {text}" for text in run.get("issues", [])] or ["- (none)"]
            lines += ["", "Must flag found? (yes / no / n.a.)", ">", "False objections (count):", ">", ""]
        else:
            before = cases[repairs[run["case"]]["candidate"]]["answer"]
            diff = list(unified_diff(before.splitlines(), (run.get("answer") or "").splitlines(), "candidate", "repair", lineterm="", n=0))
            lines += [f"Gold must change: {g['Must change']}", f"Gold must keep: {g['Must keep']}",
                      f"Gold dispute: {g['Correct to dispute?']}", f"Model response: {run.get('correction_response')}",
                      "", "Diff:", "```diff", *(diff or ["(no change)"]), "```", "",
                      "Must change done? (yes / no / n.a.)", ">", "Lost anything from must keep? (yes / no)", ">", ""]
    return "\n".join(lines)


def parse_sheet(text):
    answers, current, field = {}, None, None
    for line in text.splitlines():
        if line.startswith("### "):
            current, field = line[4:].strip(), None
            answers[current] = {}
        elif current and re.match(r"^[A-Z][^>]*[?:)]\s*$", line):
            field = line.strip()
        elif current and field and line.startswith(">"):
            answers[current][field] = line[1:].strip().lower()
            field = None
    return answers


def limit(text):
    match = re.match(r"\s*(\d+)", text or "")
    return int(match.group(1)) if match else None


def report(results, cases_data, sheet_text):
    gold, answers = cases_data["gold"], parse_sheet(sheet_text)
    totals = {}
    for run in results["runs"]:
        key, auto = run_key(run), automatic(run, gold, cases_data["cases"])
        human = answers.get(key, {})
        arm = totals.setdefault(f"{run['agent_version']} / {run['profile']}", {
            "runs": 0, "protocol_failures": 0, "wrong_decisions": 0, "false_objections_B1_R6": 0,
            "missed_defects_B2_B13": 0, "destructive_repairs": 0, "unadjudicated": 0})
        arm["runs"] += 1
        arm["protocol_failures"] += auto["protocol_failure"]
        if run["case"].startswith("B"):
            arm["wrong_decisions"] += not auto["decision_matches_gold"]
            found = human.get("Must flag found? (yes / no / n.a.)", "")
            false = limit(human.get("False objections (count):")) or 0
            false += len(auto["false_label_disputes"])
            if run["case"] == "B1":
                if not auto["protocol_failure"] and run.get("issues") and not human.get("False objections (count):"):
                    arm["unadjudicated"] += 1
                arm["false_objections_B1_R6"] += 1 if auto["protocol_failure"] or false else 0
            elif run["case"] not in NO_DEFECT and run["case"] in {f"B{i}" for i in range(2, 14)}:
                if auto["protocol_failure"] or found == "no":
                    arm["missed_defects_B2_B13"] += 1
                elif found != "yes":
                    arm["unadjudicated"] += 1
        else:
            lost = human.get("Lost anything from must keep? (yes / no)", "")
            if run["case"] == "R6":
                arm["false_objections_B1_R6"] += auto["false_correction_followed"] or auto["protocol_failure"]
            if lost == "yes" or auto["false_correction_followed"]:
                arm["destructive_repairs"] += 1
            elif lost != "no" and not auto["protocol_failure"]:
                arm["unadjudicated"] += 1
    thresholds = gold["thresholds"]
    caps = {"false_objections_B1_R6": limit(thresholds["Maximum false objections on B1 and R6"]),
            "missed_defects_B2_B13": limit(thresholds["Maximum missed defects on B2-B13"]),
            "destructive_repairs": limit(thresholds["Maximum destructive repairs on R1-R6"])}
    for arm in totals.values():
        arm["passes_thresholds"] = None if arm["unadjudicated"] else all(arm[k] <= v for k, v in caps.items() if v is not None)
    return {"casebook_sha256": cases_data["casebook_sha256"], "thresholds": caps, "arms": totals}


def main(argv):
    command, results_path, sheet_path = argv
    results = json.loads(Path(results_path).read_text(encoding="utf-8"))
    cases_data = json.loads(CASES.read_text(encoding="utf-8"))
    if results.get("casebook_sha256") not in CASEBOOK_HASHES or cases_data["casebook_sha256"] not in CASEBOOK_HASHES:
        raise ValueError("Results or cases were not produced against the frozen GOLD_CASEBOOK_v1.md.")
    if command == "sheet":
        Path(sheet_path).write_text(sheet(results, cases_data), encoding="utf-8")
        print(sheet_path)
    elif command == "report":
        print(json.dumps(report(results, cases_data, Path(sheet_path).read_text(encoding="utf-8")), indent=2))
    else:
        raise ValueError("Use 'sheet' or 'report'.")


if __name__ == "__main__":
    main(sys.argv[1:])
