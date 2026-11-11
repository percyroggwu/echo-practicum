"""M4: the group C cases of P2_DECISION_CRITERIA_v3.md, built offline into reports_gold/M4_CASES_v1.json.

Three ZeroSugar cases, one per ZeroSugar group C line, each reviewed with the line ("with") and
with that exact text removed from the prompt at run time ("without"): v1 keeps a line only if
the case is otherwise mishandled. One Original case, M4-O1, repairs the B6 candidate through
the M2 harness (no without arm). Inputs come from reports_gold/cases.json (frozen gold v1)
and catalog SQL on data/echo.db. No model is called here.

    python gold_m4.py        # build reports_gold/M4_CASES_v1.json and print its SHA-256
"""

from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
from unittest import mock
import hashlib
import json
import sys

from agents import AccessScope, original, zero_sugar
from agents.data_access import ScopedData
from agents.grounding import FactCatalog, render_answer, GROUNDING_VERSION
from agents.lime import validate_visuals
from agents.metrics import MetricCatalog
from agents.tools import SQLReader
from gold_cases import OUTPUT as GOLD_CASES, QUESTION, build_payload, item

HERE = Path(__file__).resolve().parent
DATABASE = HERE / "data" / "echo.db"
OUTPUT = HERE / "reports_gold" / "M4_CASES_v1.json"
M4_SHA256 = "aa1f4d2a9368647b2028c6647db1ce42a52cf9db178d22e20a477736394944f6"   # approved and frozen 2026-11-07

# The line each case tests: (module, prompt constant, exact text). A "without" arm removes the text;
# patched() refuses a case whose text is not found exactly once (None: the whole constant, non-empty).
LINES = {
    "C1": (zero_sugar, "COMPLETENESS_INSTRUCTIONS",
           "\n- If the answer explains that requested evidence is unavailable, that satisfies the request."),
    "C2": (zero_sugar, "SUPPORT_INSTRUCTIONS",
           "task_outcomes lists each specialist task; a declined or failed task is not evidence that\ndata is absent.\n\n"),
    "C3": (zero_sugar, "CHART_NOTE", None),
    "O1": (original, "INSTRUCTIONS", "When evidence\n  is thin, a validation or information-gathering step is a valid action."),
}
REVIEW_CASES = ("C1", "C2", "C3")
O1_CORRECTION = {
    "correction_id": "C_" + hashlib.sha256(b"gold-m4:O1").hexdigest()[:16] + "_gold_O1", "kind": "policy_requirement",
    "owner": "Original", "issue": "No concrete manager action reasoned from the analysis is visible.",
    "requested_change": "Add a manager action that addresses the negative comments, citing the comments that motivate it.",
    "request_excerpt": None, "citation_ids": [], "detected_phases": ["gold"]}


def sha256(path=OUTPUT):
    # LF-normalized: core.autocrlf=true rewrites the checkout to CRLF on Windows.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def patched(case_id, arm):
    """Context for an arm: checks the case's line is in the prompt, and removes it for the without arm.

    The "reverted" arm (step 5, after the line was removed from the code) checks that it is gone."""
    module, name, text = LINES[case_id]
    current = getattr(module, name, "")
    if arm == "reverted":
        if current.strip() if text is None else text in current:
            raise ValueError(f"{case_id}: the reverted line is still in {module.__name__}.{name}.")
        return ExitStack()
    if not current.strip() if text is None else current.count(text) != 1:
        raise ValueError(f"{case_id}: the line under test is not in {module.__name__}.{name}.")
    stack = ExitStack()
    if arm == "without":
        stack.enter_context(mock.patch.object(module, name, "" if text is None else current.replace(text, "")))
    return stack


def prompt_sha256(case_id):
    """SHA-256 of the case's prompt constant as it is now (call inside patched())."""
    module, name, _ = LINES[case_id]
    return hashlib.sha256(getattr(module, name, "").encode("utf-8")).hexdigest()


def rendered(evidence, scope, payload):
    catalog = FactCatalog(evidence, scope)
    answer, claims = render_answer(payload, catalog, "Original")
    return answer, claims, {"version": GROUNDING_VERSION, "payload": payload, "role": "Original"}


def unavailable_case(base):
    """C1: the question asks for a neutral excerpt 'if available'; no comment is labelled neutral."""
    question = QUESTION.replace("illustrating a positive and a critical view if available",
                                "illustrating a positive, a critical and a neutral view if available")
    assert question != QUESTION
    payload = build_payload(FactCatalog(base["evidence"], base["scope"]), {})
    payload["interpretations"].append(item("No comment was classified neutral (0 of 13 eligible comments), so no "
                                           "neutral excerpt is available.", ["SENTIMENT1"]))
    answer, claims, grounding = rendered(base["evidence"], base["scope"], payload)
    return {**deepcopy(base), "question": question, "answer": answer, "claims": claims, "grounding": grounding,
            "task_outcomes": [], "visualization": None, "require_sentiment": True,
            "point": "The answer explains that the requested neutral excerpt is unavailable (no neutral comment)."}


def task_outcome_case(base):
    """C2: the base answer plus a declined numeric task; the question asks for comment text, not ratings."""
    outcome = {"agent": "Cherry", "status": "declined", "task_outcome": {
        "status": "declined", "reason_code": "out_of_role",
        "reason": "The question asks for comment text rather than numerical survey ratings."}}
    return {**deepcopy(base), "question": QUESTION, "task_outcomes": [outcome], "visualization": None,
            "require_sentiment": True,
            "point": "A declined Cherry task is listed; survey ratings exist but were not requested."}


def chart_case(database=DATABASE):
    """C3: a correct chart of the Recognition favorable percentage from catalog SQL, with a cited answer."""
    scope = AccessScope("M14", "2026-01-01", "2026-09-30")
    backend = ScopedData(database, scope)
    try:
        reader = SQLReader(backend.structured_tables(), scope)
    finally:
        backend.close()
    try:
        evidence = [MetricCatalog(reader).run("survey_trend", "Recognition")]
    finally:
        reader.close()
    catalog = FactCatalog(evidence, scope.__dict__)
    table = next(k for k, f in catalog.facts.items() if f["kind"] == "table")
    change = next(k for k, f in catalog.facts.items() if f["kind"] == "calculated"
                  and "Favorable_Percent increased by 25" in f["text"])
    payload = {"fact_ids": [table, change], "interpretations": [
        {"text": "Interpretation limits: one team and three survey dates; Responses vary from 32 to 36, and the "
                 "respondents may differ between dates. The rise shows change over time, not its cause.",
         "citation_ids": ["SQL1"], "quote": None}],
        "proposals": [
        {"text": "Proposed action: at the next check-in, ask the team which recognition practices changed this year "
                 "and keep the ones they name. Basis: the favorable percentage rose from 62.5% to 87.5%; the benefit is "
                 "an assumption.", "citation_ids": ["SQL1"], "quote": None}]}
    answer, claims, grounding = rendered(evidence, scope.__dict__, payload)
    visualization = {"charts": [{"source_id": "SQL1", "kind": "line", "x": "Survey_Date", "y": "Favorable_Percent",
                                 "series": None, "title": "Recognition favorable responses, 2026",
                                 "x_label": "Survey date", "y_label": "Favorable responses (%)",
                                 "unit": "Percent of responses", "denominator": "Responses"}],
                     "reason": "The question asks for a chart of the Recognition favorable percentage over time."}
    validate_visuals(visualization, evidence, scope)
    return {"question": "Show me a chart of the Recognition favorable percentage over the first three quarters of "
                        "2026, explain the change, and suggest one action.",
            "answer": answer, "claims": claims, "grounding": grounding, "evidence": evidence, "sentiment": {},
            "scope": scope.__dict__, "task_outcomes": [], "visualization": visualization, "require_sentiment": False,
            "point": "A correct chart: percent of responses, Responses as denominator, no causal claim."}


def build(database=DATABASE):
    gold = json.loads(GOLD_CASES.read_text(encoding="utf-8"))
    base = {k: gold["cases"]["B1"][k] for k in ("answer", "claims", "grounding", "evidence", "sentiment", "scope")}
    b6 = {k: gold["cases"]["B6"][k] for k in ("answer", "claims", "grounding", "evidence", "sentiment", "scope")}
    return {"version": "gold-m4-v1", "criteria": "P2_DECISION_CRITERIA_v3.md", "gold_casebook_sha256": gold["casebook_sha256"],
            "review_cases": {"C1": unavailable_case(base), "C2": task_outcome_case(base), "C3": chart_case(database)},
            "repair_case": {"O1": {"question": QUESTION, "candidate": b6, "correction": O1_CORRECTION,
                                   "point": "B6 has no action; 2 of 13 comments are negative (thin evidence)."}}}


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(OUTPUT, sha256())
    sys.exit(0)
