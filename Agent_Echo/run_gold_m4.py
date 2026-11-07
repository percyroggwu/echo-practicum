"""M4: run the group C cases (reports_gold/M4_CASES_v1.json) and write an adjudication sheet.

LIVE MODE MAKES MODEL API CALLS. C1-C3: ZeroSugar reviews each case once with its line and once
without it (arms interleaved; --without-first reverses the order, for the second profile). O1:
Original repairs the B6 candidate through the M2 harness, repeats 2. Every run records the
SHA-256 of the prompt constant it used. Decisions follow P2_DECISION_CRITERIA_v3.md after the
sheet is adjudicated.

    python gold_m4.py                                  # once: build the cases
    python run_gold_m4.py --profile apinex_test --dry-run
    python run_gold_m4.py --profile apinex_test
    python run_gold_m4.py --profile apinex_gemini_test --without-first
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest import mock
import argparse
import json
import sys

from agents.connections import DEFAULT_CONFIG, ModelRegistry
from agents.execution_log import RunLog, record
from gold_m4 import M4_SHA256, OUTPUT as CASES, REVIEW_CASES, patched, prompt_sha256, sha256
import run_gold_repair
import run_gold_review

ARMS = ("with", "without")
MOTIVATING = {"survey:CMT27501", "survey:CMT27502", "SENTIMENT1"}


def steps(repeats, without_first=False):
    arms = ARMS[::-1] if without_first else ARMS
    review = [("review", case, arm, 1) for case in REVIEW_CASES for arm in arms]
    return review + [("repair", "O1", "with", r) for r in range(1, repeats + 1)]


def repair_checks(answer, payload, candidate):
    """Condition 2 from the submitted payload; condition 5 aid (diagnostic only)."""
    before = {p["text"] for p in candidate["grounding"]["payload"]["proposals"]}
    added = [p for p in (payload or {}).get("proposals", []) if p["text"] not in before]
    missing = [line for line in candidate["answer"].splitlines() if line.strip() and line not in (answer or "")]
    return {"added_proposals": added,
            "cites_motivating_findings": any(set(p.get("citation_ids") or []) & MOTIVATING for p in added),
            "candidate_lines_missing": missing}


def sheet(results, cases):
    lines = [f"# M4 adjudication sheet: {results['profile']}", "",
             f"Results: run {results.get('run_id')}, cases sha256 {results['cases_sha256'][:12]}, arm order "
             f"{results.get('arm_order')}. Criteria: P2_DECISION_CRITERIA_v3.md. Answer each question yes or no. "
             "A protocol failure is not adjudicated: its line reverts (v3).", ""]
    for run in results["runs"]:
        if run["kind"] == "review":
            case = cases["review_cases"][run["case"]]
            lines += [f"## {run['case']} {run['arm']} the line", "", f"Point: {case['point']}", "",
                      f"Status: {run['status']}; decision: {run.get('decision')}; prompt sha256 "
                      f"{(run.get('prompt_sha256') or '')[:12]}", "", "Issues:", ""]
            lines += [f"- {i}" for i in run.get("issues") or ["(none)"]]
            lines += ["", "Mishandled the point: a false objection, or a false 'data absent' claim, about it? (yes / no)",
                      "> ", ""]
        else:
            lines += [f"## O1 repeat {run['repeat']}", "", f"Status: {run['status']}; response: "
                      f"{run.get('correction_response')}; prompt sha256 {(run.get('prompt_sha256') or '')[:12]}", "",
                      "Added proposals (not in the B6 payload):", ""]
            lines += [f"> {p['text']} {p.get('citation_ids')}" for p in run.get("added_proposals") or []] or ["> (none)"]
            lines += ["", f"Condition 2 (automatic, from the payload): cites CMT27501, CMT27502 or SENTIMENT1 = "
                      f"{run.get('cites_motivating_findings')}", "",
                      "Diagnostic only, adjudicate condition 5: B6 lines not found verbatim in the answer:", ""]
            lines += [f"- {m}" for m in run.get("candidate_lines_missing") or ["(none)"]]
            lines += [""]
            for question in ("1. The added proposal is a validation or information-gathering step, and repeats neither "
                             "B6 team question?", "3. The benefit is stated as an assumption?", "4. No invented cause?",
                             "5. No content lost from the B6 candidate?"):
                lines += [question + " (yes / no)", "> ", ""]
    return "\n".join(lines)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", required=True, help="Model profile, e.g. apinex_test.")
    parser.add_argument("--repeats", type=int, default=2, help="O1 repeats (default 2, as in v2).")
    parser.add_argument("--without-first", action="store_true",
                        help="Run the without arm first in each case (the second profile, apinex_gemini_test).")
    parser.add_argument("--connections", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true", help="Check inputs and print the plan; no API call.")
    args = parser.parse_args(argv)

    if not CASES.exists():
        parser.error("Build the cases first: python gold_m4.py")
    digest = sha256()
    frozen = digest == M4_SHA256
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    plan = steps(args.repeats, args.without_first)
    order = "without first" if args.without_first else "with first"
    for case in (*REVIEW_CASES, "O1"):
        patched(case, "with").close()   # refuses now if a line under test is missing from its prompt
    print(f"{len(plan)} runs: C1-C3 x {len(ARMS)} arms ({order}), O1 x {args.repeats}, profile {args.profile}.")
    print(f"Expected model calls: at least {2 * 6 + args.repeats}, at most "
          f"{run_gold_review.MODEL_CALLS * 6 + run_gold_repair.MODEL_CALLS * args.repeats}.")
    print(f"Cases {CASES.name} sha256 {digest[:12]}: " + ("frozen." if frozen else "NOT FROZEN (draft)."))
    if args.dry_run:
        for step in plan:
            print("  ", *step)
        print("Dry run: no API call was made.")
        return 0
    if not frozen:
        parser.error("The M4 cases are not frozen: the user approves them and M4_SHA256 is set first.")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output = CASES.parent / f"m4_{args.profile}_{stamp}.json"
    registry = ModelRegistry(args.connections, args.profile)
    results = {"cases_sha256": digest, "measurement": "M4 group C", "profile": args.profile, "arm_order": order,
               "started_utc": datetime.now(timezone.utc).isoformat(), "runs": []}
    try:
        with RunLog(run_gold_review.LOGS, agent="gold_m4", mode="live") as log:
            print("Execution log: " + str(log.path), flush=True)
            results["run_id"] = log.run_id
            run_gold_review.save(output, results)
            for index, (kind, case, arm, repeat) in enumerate(plan, 1):
                print(f"[{index}/{len(plan)}] {case} {arm} repeat {repeat} ...", end=" ", flush=True)
                record("gold_m4_started", case=case, arm=arm, repeat=repeat)
                with patched(case, arm):
                    fingerprint = prompt_sha256(case)
                    if kind == "review":
                        outcome = review_one(cases["review_cases"][case], registry.get("ZeroSugar"))
                    else:
                        outcome = repair_one(cases["repair_case"][case], registry.get("Original"))
                results["runs"].append({"kind": kind, "case": case, "arm": arm, "repeat": repeat,
                                        "prompt_sha256": fingerprint, **outcome})
                run_gold_review.save(output, results)
                print(outcome["status"], outcome.get("decision") or outcome.get("correction_response") or "",
                      f"{outcome['seconds']}s", flush=True)
            results["finished_utc"] = datetime.now(timezone.utc).isoformat()
            run_gold_review.save(output, results)
            log.finish(0)
    except KeyboardInterrupt:
        print("\nInterrupted; completed runs are saved in " + str(output), file=sys.stderr)
        return 130
    finally:
        registry.close()
    target = output.with_name(output.stem + "_sheet.md")
    target.write_text(sheet(results, cases), encoding="utf-8")
    print("Results: " + str(output))
    print("Sheet: " + str(target))
    return 0


def review_one(case, model):
    """run_gold_review.run_one (frozen M1 harness) with the case's question, visualization and task_outcomes."""
    original = run_gold_review.ZeroSugarAgent.review
    def review(self, question, answer, evidence, **kwargs):
        kwargs.update(visualization=case["visualization"], task_outcomes=case["task_outcomes"],
                      require_sentiment=case["require_sentiment"])
        return original(self, case["question"], answer, evidence, **kwargs)
    with mock.patch.object(run_gold_review.ZeroSugarAgent, "review", review):
        return run_gold_review.run_one(case, "v8", model)


def repair_one(case, model):
    """run_gold_repair.run_one (frozen M2 harness), keeping Original's submitted payload for condition 2."""
    seen, original = {}, run_gold_repair.Specialist.run
    def run(agent, *args, **kwargs):
        seen["result"] = original(agent, *args, **kwargs)
        return seen["result"]
    with mock.patch.object(run_gold_repair.Specialist, "run", run):
        outcome = run_gold_repair.run_one(case["question"], case["candidate"], {"correction": case["correction"]},
                                          "v8", model)
    payload = (getattr(seen.get("result"), "grounding", None) or {}).get("payload")
    return {**outcome, **repair_checks(outcome.get("answer"), payload, case["candidate"])}


if __name__ == "__main__":
    sys.exit(main())
