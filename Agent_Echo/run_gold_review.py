"""M1: run the frozen gold reviewer cases through ZeroSugar v7 and/or v8.

LIVE MODE MAKES MODEL API CALLS with the selected profile's credentials (from .env). Only
ZeroSugar runs; Original, Vanilla and the specialists are not called. Each review gets its own
budget. Results are written after every review, so an interrupted run keeps its progress.

    python gold_cases.py                                     # once: build reports/gold_v1/cases.json
    python run_gold_review.py --profile apinex_test --dry-run
    python run_gold_review.py --profile apinex_test --cases B1,B2,B7,B15 --repeats 1
    python score_gold.py sheet reports/gold_v1/<results>.json reports/gold_v1/<sheet>.md
"""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

from agents.connections import DEFAULT_CONFIG, ModelRegistry
from agents.execution_log import RunLog, record, error_summary
from agents.runtime import RunBudget
from agents.zero_sugar import ZeroSugarAgent, ReviewRepairNeeded
from agents.zero_sugar_v8 import ZeroSugarAgentV8
from gold_cases import CASEBOOK_SHA256, OUTPUT as CASES, prepared_reviewer

HERE = Path(__file__).resolve().parent
DATABASE = HERE / "data" / "echo.db"
LOGS = HERE / "reports" / "logs"
REVIEWERS = {"v7": ZeroSugarAgent, "v8": ZeroSugarAgentV8}
MODEL_CALLS, SECONDS = 8, 600   # per review: two phases, three attempts each, the shared extra attempt


def plan(cases, versions, repeats, start=1):
    """Interleave versions inside each case and repeat, so time-of-day affects both alike."""
    return [(case, version, repeat) for repeat in range(start, start + repeats) for case in cases for version in versions]


def objections(verdict):
    """Everything the reviewer asked to change, for the human adjudication sheet."""
    items = [c["issue"] + (" -> " + c["requested_change"] if c.get("requested_change") not in (None, c["issue"]) else "")
             for c in verdict.corrections]
    items += [f"{f['finding_id']} withheld: {f.get('reason', '')}" for f in verdict.findings if f["status"] != "supported"]
    return list(dict.fromkeys(items))


def run_one(case, version, model, database=DATABASE):
    budget = RunBudget(model_limit=MODEL_CALLS, tool_limit=2 * MODEL_CALLS, seconds=SECONDS)
    agent = prepared_reviewer(case, database, REVIEWERS[version], model, budget)
    started = time.monotonic()
    result = {"status": "completed"}
    try:
        verdict = agent.review(case["question"], case["answer"], case["evidence"], claims=case["claims"],
                               grounding=case["grounding"], require_sentiment=True, require_actionable=True)
        result.update(decision=verdict.decision, issues=objections(verdict),
                      label_disputes=[{**d, "finding_id": f["finding_id"]} for f in verdict.findings
                                      for d in f.get("label_disputes", [])],
                      deterministic_issues=verdict.deterministic_issues,
                      scores={k: v["score"] for k, v in verdict.ratings.items()},
                      withheld_findings=[f["finding_id"] for f in verdict.findings if f["status"] != "supported"],
                      review_version=verdict.version)
    except ReviewRepairNeeded as error:
        result.update(status="protocol_failure", stop="support_failed_completeness_repairs_returned",
                      issues=[c["issue"] for c in error.corrections])
    except (RuntimeError, ValueError) as error:
        protocol = isinstance(error, RuntimeError) and "protocol exhausted" in str(error)
        result.update(status="protocol_failure" if protocol else "error", error=error_summary(error))
    finally:
        agent.close()
    result.update(seconds=round(time.monotonic() - started, 1), model_calls=budget.models,
                  input_tokens=sum(u.get("input_tokens", 0) for c in budget.request_costs for u in c["provider_usage"]),
                  output_tokens=sum(u.get("output_tokens", 0) for c in budget.request_costs for u in c["provider_usage"]),
                  rejected_attempts=len(agent.diagnostics.get("rejected_attempts", [])),
                  phases=[{k: p.get(k) for k in ("phase", "status", "model_attempts")} for p in agent.diagnostics.get("review_phases", [])])
    return result


def save(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", required=True, help="Model profile for ZeroSugar, e.g. apinex_test or apinex_gemini_test.")
    parser.add_argument("--cases", default=",".join(f"B{i}" for i in range(1, 17)), help="Comma-separated, default B1-B16.")
    parser.add_argument("--versions", default="v7,v8", help="Comma-separated: v7, v8 or both (default).")
    parser.add_argument("--repeats", type=int, default=1, help="Runs per case and version (default 1).")
    parser.add_argument("--repeat-start", type=int, default=1,
                        help="First repeat number, to complete an interrupted series without reusing numbers.")
    parser.add_argument("--output", type=Path, help="New results file; default reports/gold_v1/results_<profile>_<UTC>.json.")
    parser.add_argument("--connections", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true", help="Check inputs and print the plan; no API call.")
    args = parser.parse_args(argv)

    if not CASES.exists():
        parser.error("Build the cases first: python gold_cases.py")
    data = json.loads(CASES.read_text(encoding="utf-8"))
    if data["casebook_sha256"] != CASEBOOK_SHA256:
        parser.error("cases.json was not built from the frozen GOLD_CASEBOOK_v1.md; rebuild it.")
    cases = [c.strip() for c in args.cases.split(",") if c.strip()]
    versions = [v.strip() for v in args.versions.split(",") if v.strip()]
    if unknown := [c for c in cases if c not in data["cases"]]:
        parser.error("Unknown cases: " + ", ".join(unknown))
    if unknown := [v for v in versions if v not in REVIEWERS]:
        parser.error("Unknown versions: " + ", ".join(unknown))
    if not 1 <= args.repeats <= 5 or not 1 <= args.repeat_start <= 10:
        parser.error("--repeats must be 1-5 and --repeat-start 1-10.")
    steps = plan(cases, versions, args.repeats, args.repeat_start)
    print(f"{len(steps)} reviews: {len(cases)} cases x {len(versions)} versions x {args.repeats} repeats, profile {args.profile}.")
    print(f"Expected model calls: at least {2 * len(steps)} (two phases each), at most {MODEL_CALLS * len(steps)}.")
    if args.dry_run:
        for step in steps:
            print("  ", *step)
        print("Dry run: no API call was made.")
        return 0

    output = args.output or HERE / "reports" / "gold_v1" / (
        f"results_{args.profile}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json")
    if output.exists():
        parser.error("Output already exists; choose a new filename so earlier results are preserved.")
    output.parent.mkdir(parents=True, exist_ok=True)
    registry = ModelRegistry(args.connections, args.profile)
    results = {"casebook_sha256": CASEBOOK_SHA256, "profile": args.profile, "cases": cases, "versions": versions,
               "repeats": args.repeats, "started_utc": datetime.now(timezone.utc).isoformat(), "runs": []}
    try:
        with RunLog(LOGS, agent="gold_review", mode="live") as log:
            print("Execution log: " + str(log.path), flush=True)
            results["run_id"] = log.run_id
            save(output, results)
            for index, (case, version, repeat) in enumerate(steps, 1):
                print(f"[{index}/{len(steps)}] {case} {version} repeat {repeat} ...", end=" ", flush=True)
                record("gold_review_started", case=case, agent_version=version, repeat=repeat)
                outcome = run_one({**data["cases"][case], "question": data["question"]}, version, registry.get("ZeroSugar"))
                results["runs"].append({"case": case, "agent_version": version, "profile": args.profile,
                                        "repeat": repeat, **outcome})
                save(output, results)
                print(outcome["status"], outcome.get("decision", ""), f"{outcome['seconds']}s", flush=True)
            results["finished_utc"] = datetime.now(timezone.utc).isoformat()
            save(output, results)
            log.finish(0)
    except KeyboardInterrupt:
        print("\nInterrupted; completed reviews are saved in " + str(output), file=sys.stderr)
        return 130
    finally:
        registry.close()
    print("Results: " + str(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
