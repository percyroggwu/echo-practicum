"""Build the frozen human-gold cases (GOLD_CASEBOOK_v1.md) as reviewer and repair inputs. No API calls.

B1-B13 are rendered by Echo's own source-facts-v7 renderer from the Gemini 51 evidence, so each
candidate is what Echo would produce. B9 and B11 cannot be produced by the renderer (code
prevents them), so they are tampered copies and Echo's objective audit flags them; they test
the code gate, not reviewer judgment. B14-B16 are copied from the saved 51/52 reports.

    python gold_cases.py            # writes reports_gold/cases.json
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

from agents import AccessScope
from agents.data_access import ScopedData
from agents.grounding import FactCatalog, render_answer, audit_claims, GROUNDING_VERSION
from agents.tools import SQLReader
from agents.zero_sugar import ZeroSugarAgent

HERE = Path(__file__).resolve().parent
CASEBOOK = HERE / "GOLD_CASEBOOK_v1.md"
# LF-normalized hash of the committed casebook, the same on any checkout.
CASEBOOK_SHA256 = "2ed93543df6892ece395d031f04b6834a49999fca5c26f9b324129984ac31c3d"
# Raw hash of the CRLF working copy, carried by cases.json and the M1/M2 results built before 2026-11-08.
LEGACY_CASEBOOK_SHA256 = "24d84029a130e2288878c31d880f6ca35a5792967daeffa3778d67484d5197d3"
CASEBOOK_HASHES = {CASEBOOK_SHA256, LEGACY_CASEBOOK_SHA256}
REPORTS = HERE / "reports_gold"   # gold inputs, cases.json, results and adjudication sheets
OUTPUT = REPORTS / "cases.json"
# Cases whose defect Echo's renderer cannot produce; the objective audit must flag them.
CODE_DETECTED = {"B9", "B11"}

QUESTION = ("I'm preparing for a team check-in. Using all eligible anonymous Recognition survey comments for the "
    "third quarter of 2026, classify each comment as positive, negative, neutral, mixed, or indeterminate. Show the "
    "count and percentage in each category, including the denominator. Include a short literal excerpt illustrating "
    "a positive and a critical view if available, with source citations. Explain the main patterns and interpretation "
    "limits, and suggest two follow-up questions for the team. Base this analysis on comment text rather than "
    "numerical survey ratings, and do not identify respondents.")


def item(text, refs, quote=None):
    return {"text": text, "citation_ids": [r if r == "SENTIMENT1" else "survey:" + r for r in refs], "quote": quote}


BASE = {
    "P1": item("Positive comments describe specific, timely recognition: partner-manager feedback after a handoff, direct "
               "thanks from another team, weekly recaps that name contributors, and clear processes.",
               ["CMT27500", "CMT27503", "CMT27504", "CMT27507"]),
    "P2": item("Negative comments describe support work left out of project summaries and thank-yous, and a raised concern "
               "that received no follow-up.", ["CMT27501", "CMT27502"]),
    "P3": item("Mixed comments combine useful support with remaining gaps: inconsistent access and gaps during busy periods.",
               ["CMT27508", "CMT27511", "CMT27512"]),
    "E1": item("Positive example.", ["CMT27500"], "A partner manager sent specific feedback after our handoff."),
    "E2": item("Critical example.", ["CMT27501"], "My extra work goes unnoticed."),
    "L1": item("Interpretation limits: percentages describe comments, not employees; labels are provisional model "
               "classifications; all comments come from one team and one survey date (2026-09-30), so there is no trend.",
               ["SENTIMENT1"]),
    "X1": item("Proposed action: for the next quarter, add a line to weekly recaps and project summaries that names "
               "supporting contributors, and check after one month whether the team notices a difference. Basis: negative "
               "and mixed comments report omitted support work; the benefit is an assumption.",
               ["CMT27501", "CMT27502", "CMT27508"]),
    # The casebook shows the questions without citations; the renderer requires one source per item.
    "Q1": item("Ask the team: Which kinds of support work are most often missed in summaries and thank-yous?",
               ["CMT27501", "CMT27502"]),
    "Q2": item("Ask the team: What would keep recognition consistent during busy periods?", ["CMT27508", "CMT27512"]),
}
INTERPRETATIONS, PROPOSALS = ["P1", "P2", "P3", "E1", "E2", "L1"], ["X1", "Q1", "Q2"]


def variants():
    """Exactly one change from the base per case, as written in Part B."""
    v = {"B1": {}}
    v["B2"] = {"drop": ["E2"]}
    v["B3"] = {"drop": ["E1"]}
    v["B4"] = {"add_proposals": [item("Ask the team: Who should be responsible for naming contributors in recaps?",
                                      ["CMT27501", "CMT27503"])]}
    v["B5"] = {"replace": {"Q1": item("Proposed action: review project summaries monthly.", ["CMT27501", "CMT27502"]),
                           "Q2": item("Proposed action: send a reminder before busy periods.", ["CMT27508", "CMT27512"])}}
    v["B6"] = {"drop": ["X1"]}
    v["B7"] = {"replace": {"P3": {**BASE["P3"], "citation_ids": BASE["P3"]["citation_ids"] + ["survey:CMT27510"]}}}
    v["B8"] = {"replace": {"P2": item(BASE["P2"]["text"] + " Most employees feel their work is not recognized.",
                                      ["CMT27501", "CMT27502", "SENTIMENT1"])}}
    v["B9"] = {"tamper": "E2_cited_to_CMT27500"}
    v["B10"] = {"replace": {"P2": item(BASE["P2"]["text"] + " The comment about missed follow-up likely came from the "
                                       "most senior engineer.", ["CMT27501", "CMT27502"])}}
    v["B11"] = {"no_classification_table": True}
    v["B12"] = {"drop": ["L1"]}
    v["B13"] = {"append_interpretation": "E2"}
    return v


def build_payload(catalog, change):
    parts = {key: deepcopy(value) for key, value in BASE.items()}
    for key, value in change.get("replace", {}).items():
        parts[key] = deepcopy(value)
    interpretations = [parts[k] for k in INTERPRETATIONS if k not in change.get("drop", [])]
    if "append_interpretation" in change:
        interpretations.append(deepcopy(parts[change["append_interpretation"]]))
    proposals = [parts[k] for k in PROPOSALS if k not in change.get("drop", [])] + change.get("add_proposals", [])
    aggregate = next(key for key, f in catalog.facts.items()
                     if f["kind"] == "table" and f["operation"].get("type") != "sentiment_classifications")
    payload = {"fact_ids": [aggregate], "interpretations": interpretations, "proposals": proposals}
    return payload if change.get("no_classification_table") else catalog.bind_classification_display(payload, "Original")


def render_case(evidence, scope, change):
    catalog = FactCatalog(evidence, scope)
    payload = build_payload(catalog, change)
    answer, claims = render_answer(payload, catalog, "Original")
    if change.get("tamper") == "E2_cited_to_CMT27500":
        # Not producible by the renderer (the quote is not in CMT27500); tamper text, claims and payload alike.
        for claim in claims:
            if claim.get("quote") == BASE["E2"]["quote"]:
                claim["text"] = claim["text"].replace("[survey:CMT27501]", "[survey:CMT27500]")
                claim["citation_ids"] = ["survey:CMT27500"]
        for entry in payload["interpretations"]:
            if entry["quote"] == BASE["E2"]["quote"]:
                entry["citation_ids"] = ["survey:CMT27500"]
        answer = "\n\n".join(c["text"] for c in claims)
    return answer, claims, {"version": GROUNDING_VERSION, "payload": payload, "role": "Original"}


def load_report(name):
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def real_cases():
    result = {}
    for case, name, key in (("B14", "apinex_prueba_gemini_51.json", "released_candidate"),
                            ("B15", "apinex_prueba_vanilla_52.json", "released_candidate"),
                            ("B16", "apinex_prueba_vanilla_52.json", "unreviewed_candidate")):
        report = load_report(name)
        candidate = report["verification"][key]
        result[case] = {"source": f"{name}:{key}:{candidate['candidate_id']}", "answer": candidate["answer"],
                        "claims": candidate["claims"], "grounding": candidate["grounding"],
                        "evidence": report["evidence"], "sentiment": report["sentiment"], "scope": report["scope"]}
    return result


REPAIRS = {
    "R1": ("B4", "missing_deliverable", "The answer has three team questions; the question asks for two.",
           "Keep exactly the two requested team questions."),
    "R2": ("B3", "missing_deliverable", "The requested literal positive example is missing.",
           "Add the requested literal positive example."),
    "R3": ("B9", "unsupported_claim", "The critical excerpt is attributed to the wrong comment.",
           "Cite the critical excerpt to the comment that contains it."),
    "R4": ("B8", "unsupported_claim", "The claim about most employees is not supported by the comments.",
           "Qualify or remove the unsupported claim about employees."),
    "R5": ("B13", "unusable_presentation", "The critical-example paragraph is repeated.",
           "Remove the repeated critical-example paragraph."),
    "R6": ("B1", "missing_deliverable", "The per-comment table omits CMT27506, CMT27507 and CMT27511.",
           "Add the missing comments to the per-comment table."),
}


def repair_inputs():
    result = {}
    for case, (candidate, kind, issue, change) in REPAIRS.items():
        identity = hashlib.sha256(("gold-v1:" + case).encode()).hexdigest()[:16]
        result[case] = {"candidate": candidate, "false_correction": case == "R6", "correction": {
            "correction_id": f"C_{identity}_gold_{case}", "kind": kind, "owner": "Original", "issue": issue,
            "requested_change": change, "request_excerpt": None, "citation_ids": [], "detected_phases": ["gold"]}}
    return result


def parse_casebook(path=CASEBOOK):
    """Read '### ID - title' sections and 'Field:' lines followed by '>' answers."""
    sections, current, field = {}, None, None
    for line in path.read_text(encoding="utf-8").splitlines():
        header = re.match(r"^### ([ABR]\d+) - (.*)$", line)
        if header:
            current, field = header.group(1), None
            sections[current] = {"title": header.group(2)}
        elif line.startswith("# "):
            current = "thresholds" if line.startswith("# Part D") else "record" if line.startswith("# Part E") else None
            if current:
                sections.setdefault(current, {})
            field = None
        elif current and re.match(r"^[A-Z][^>]*[:?]\s*$", line):
            field = line.strip().rstrip(":")
        elif current and field and line.startswith(">"):
            sections[current][field] = line[1:].strip()
            field = None
    return sections


def prepared_reviewer(case, database, cls=ZeroSugarAgent, model=None, budget=None):
    """The same trusted lookups ZeroSugarAgent.run() builds from the database."""
    scope = AccessScope(**case["scope"])
    agent = cls(scope, model, "live", budget=budget)
    backend = ScopedData(database, scope)
    try:
        agent.owned_reader = agent.sql_reader = SQLReader(backend.structured_tables(), scope)
        agent.document_lookup = {doc["citation_id"]: doc for doc in backend.text_documents()}
        agent.sentiment_documents = backend.sentiment_documents()
        agent.authorized_teams = list(backend.teams)
    finally:
        backend.close()
    agent.sentiment_reports = case["sentiment"]
    return agent


def objective_issues(case, database):
    agent = prepared_reviewer(case, database)
    try:
        issues = agent.audit(case["answer"], case["evidence"])
        issues += audit_claims(case["claims"], case["answer"], FactCatalog(case["evidence"], case["scope"]), case["grounding"])
        return list(dict.fromkeys(issues))
    finally:
        agent.close()


def sha256(path=CASEBOOK):
    # LF-normalized: core.autocrlf=true rewrites the checkout to CRLF on Windows.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def build(database=HERE / "data" / "echo.db"):
    digest = sha256()
    if digest != CASEBOOK_SHA256:
        raise ValueError("GOLD_CASEBOOK_v1.md differs from its frozen hash; a changed gold needs a new version.")
    source = load_report("apinex_prueba_gemini_51.json")
    scope = source["scope"]
    cases = {}
    for case, change in variants().items():
        answer, claims, grounding = render_case(source["evidence"], scope, change)
        cases[case] = {"source": "rendered from apinex_prueba_gemini_51.json evidence", "change": change,
                       "answer": answer, "claims": claims, "grounding": grounding, "evidence": source["evidence"],
                       "sentiment": source["sentiment"], "scope": scope}
    cases.update(real_cases())
    for case, value in cases.items():
        print(f"Checking {case} with the objective audit (offline)...", file=sys.stderr, flush=True)
        value["objective_issues"] = objective_issues(value, database)
        value["code_detected"] = case in CODE_DETECTED
        if bool(value["objective_issues"]) != (case in CODE_DETECTED):
            raise RuntimeError(f"{case}: objective audit result does not match its design: {value['objective_issues']}")
    return {"casebook": CASEBOOK.name, "casebook_sha256": digest, "question": QUESTION,
            "gold": parse_casebook(), "cases": cases, "repairs": repair_inputs()}


if __name__ == "__main__":
    data = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "cases": len(data["cases"]), "repairs": len(data["repairs"]),
                      "code_detected": sorted(CODE_DETECTED)}))
    sys.exit(0)
