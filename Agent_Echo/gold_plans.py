"""M3: the planning gold casebook (reports_gold/GOLD_PLANS_v1.json) and its scoring.

The casebook is a draft until the user approves the expected plans; then its SHA-256 is set in
PLANS_SHA256 and run_gold_plans.py refuses a live run on any other content.
Scoring follows P2_DECISION_CRITERIA_v1.md, M3, as clarified by P2_DECISION_CRITERIA_v2.md (hard cases).
"""

from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
CASEBOOK = HERE / "reports_gold" / "GOLD_PLANS_v1.json"
PLANS_SHA256 = "54461062a4d5ee8fc89186eb26dac993e2a3be907a7b3e34ccbca22ecfb54fea"   # frozen 2026-11-06 after the user approved the expected plans
FIELDS = ("needs_numbers", "needs_text", "needs_sentiment", "include_chart", "clarify", "metrics")
OVERALL_PASS = 0.85


def sha256(path=CASEBOOK):
    # LF-normalized: core.autocrlf=true rewrites the checkout to CRLF on Windows.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load(path=CASEBOOK):
    data = json.loads(path.read_text(encoding="utf-8"))
    for case in data["cases"]:
        expected = case["expected"]
        if expected.get("clarify") is not True and set(expected) != set(FIELDS):
            raise ValueError(f"{case['id']}: expected plan needs {', '.join(FIELDS)}.")
        if expected.get("needs_sentiment") and not expected.get("needs_text"):
            raise ValueError(f"{case['id']}: needs_sentiment requires needs_text.")
    return data


def observed(plan):
    """The compared view of a final plan from OriginalAgent.plan()."""
    return {**{k: plan[k] for k in FIELDS[:4]}, "clarify": plan["clarification_question"] is not None,
            "metrics": sorted([r["metric"], r["dimension"]] for r in plan["metrics"])}


def mismatches(expected, seen):
    """Fields where the observed plan differs; only clarify counts when a clarification is expected."""
    fields = ("clarify",) if expected.get("clarify") else FIELDS
    want = {**expected, "metrics": sorted(list(m) for m in expected.get("metrics", []))}
    return [f for f in fields if want[f] != seen[f]]


def summary(runs, cases):
    """Pass rule of P2_DECISION_CRITERIA_v1 M3 with the v2 hard cases; protocol failures stop the evaluation."""
    by_id = {c["id"]: c for c in cases}
    scored = [r for r in runs if r["status"] == "completed"]
    passed = [r for r in scored if not r["mismatches"]]
    hard_failed = sorted({r["case"] for r in runs if by_id[r["case"]].get("hard") and (r["status"] != "completed" or r["mismatches"])})
    rate = len(passed) / len(runs) if runs else 0.0
    protocol = [r["case"] for r in runs if r["status"] != "completed"]
    failures = {}
    for r in scored:
        for field in r["mismatches"]:
            failures.setdefault(field, []).append(f"{r['case']}#{r['repeat']}")
    return {"case_runs": len(runs), "passed": len(passed), "pass_rate": round(rate, 3),
            "hard_cases_failed": hard_failed, "protocol_failures": protocol, "mismatched_fields": failures,
            "result": "stopped (protocol failure)" if protocol else
                      "pass" if rate >= OVERALL_PASS and not hard_failed else "fail"}
