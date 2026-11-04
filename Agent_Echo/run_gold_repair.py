"""M2: run the frozen gold repair cases (R1-R6) through Original (results label it "v8", as in the earlier v7/v8 comparison).

LIVE MODE MAKES MODEL API CALLS. Only Original runs, for one repair round: the saved candidate
from cases.json is loaded as the saved draft, one correction is pending, no specialist is
offered and no review follows. This measures editing alone. Results use the format
score_gold.py reads (answer and correction_response per run).

    python run_gold_repair.py --profile apinex_test --dry-run
    python run_gold_repair.py --profile apinex_test --repeats 1
    python score_gold.py sheet reports_gold/<results>.json reports_gold/<sheet>.md
"""

from datetime import datetime, timezone
from pathlib import Path
from agents import AccessScope
from agents.connections import DEFAULT_CONFIG, ModelRegistry
from agents.content import block_catalog
from agents.delivery_diagnostics import duplication, repair_context
from agents.execution_log import RunLog, record, error_summary
from agents.grounding import FactCatalog
from agents.original import OriginalAgent, REPAIR_NOTE
from agents.runtime import RunBudget, Specialist
from gold_cases import CASEBOOK_SHA256, OUTPUT as CASES
from run_gold_review import plan, save
import argparse
import json
import sys
import time

HERE = Path(__file__).resolve().parent
DATABASE = HERE / "data" / "echo.db"
LOGS = HERE / "reports" / "logs"
ORIGINALS = {"v8": OriginalAgent}
MODEL_CALLS, SECONDS = 14, 600   # Original keeps its own seven-turn cap inside this budget

def prepared_original(version, candidate, correction, model, budget):
    """An Original whose saved draft is the candidate, as after a completed review."""
    scope = AccessScope(**candidate["scope"])
    agent = ORIGINALS[version](DATABASE, scope, lambda name: model, "live")
    agent.budget, agent.repair_round = budget, 1
    agent.numeric_requested = True   # the workflow sets this for a sentiment question
    catalog = FactCatalog(candidate["evidence"], candidate["scope"])
    blocks = block_catalog(candidate["grounding"]["payload"], candidate["evidence"], candidate["scope"], catalog.facts)
    agent.draft_blocks, agent.reusable_blocks, agent.draft_texts = dict(blocks), dict(blocks), {}
    agent.set_delegations([])
    agent.open_corrections = agent.compact_corrections(repair_context([correction], agent.draft_blocks))
    return agent, [{"role": "user", "content": REPAIR_NOTE}]


def run_one(question, candidate, repair, version, model):
    budget = RunBudget(model_limit=MODEL_CALLS, tool_limit=2 * MODEL_CALLS, seconds=SECONDS)
    correction = repair["correction"]
    agent, context = prepared_original(version, candidate, correction, model, budget)
    started, result = time.monotonic(), {"status": "completed"}
    try:
        answer = Specialist.run(agent, question, initial_evidence=candidate["evidence"], context=context).answer
        response = (agent.correction_responses.get(correction["correction_id"]) or {}).get("response")
        result.update(answer=answer, correction_response=response, changed=answer != candidate["answer"],
                      duplicate_paragraph_pairs=duplication(answer)["pair_count"])
    except (RuntimeError, ValueError) as error:
        summary = error_summary(error)
        result.update(status="protocol_failure" if isinstance(error, RuntimeError) else "error", error=summary, correction_response=None)
    finally:
        agent.close()
    diagnostics = getattr(agent, "last_result", None).diagnostics if getattr(agent, "last_result", None) else {}
    result.update(seconds=round(time.monotonic() - started, 1), model_calls=budget.models,
                  input_tokens=sum(u.get("input_tokens", 0) for c in budget.request_costs for u in c["provider_usage"]),
                  output_tokens=sum(u.get("output_tokens", 0) for c in budget.request_costs for u in c["provider_usage"]),
                  rejected_attempts=len(diagnostics.get("rejected_attempts", [])),
                  rejection_codes=sorted({r.get("validation_code") for r in diagnostics.get("rejected_attempts", [])
                                          if r.get("validation_code")}))
    return result


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", required=True, help="Model profile for Original, e.g. apinex_test.")
    parser.add_argument("--cases", default=",".join(f"R{i}" for i in range(1, 7)), help="Comma-separated, default R1-R6.")
    parser.add_argument("--versions", default="v8", help="Result label; only v8 exists now.")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--repeat-start", type=int, default=1)
    parser.add_argument("--output", type=Path, help="New results file; default reports_gold/repairs_<profile>_<UTC>.json.")
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
    if unknown := [c for c in cases if c not in data["repairs"]]:
        parser.error("Unknown cases: " + ", ".join(unknown))
    if unknown := [v for v in versions if v not in ORIGINALS]:
        parser.error("Unknown versions: " + ", ".join(unknown))
    if not 1 <= args.repeats <= 5 or not 1 <= args.repeat_start <= 10:
        parser.error("--repeats must be 1-5 and --repeat-start 1-10.")
    steps = plan(cases, versions, args.repeats, args.repeat_start)
    print(f"{len(steps)} repairs: {len(cases)} cases x {len(versions)} versions x {args.repeats} repeats, profile {args.profile}.")
    print(f"Expected model calls: at least {len(steps)} (one answer each), at most {MODEL_CALLS * len(steps)}.")
    if args.dry_run:
        for case, version, repeat in steps:
            print("  ", case, version, repeat, "candidate", data["repairs"][case]["candidate"])
        print("Dry run: no API call was made.")
        return 0

    output = args.output or CASES.parent / (
        f"repairs_{args.profile}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json")
    if output.exists():
        parser.error("Output already exists; choose a new filename so earlier results are preserved.")
    output.parent.mkdir(parents=True, exist_ok=True)
    registry = ModelRegistry(args.connections, args.profile)
    results = {"casebook_sha256": CASEBOOK_SHA256, "measurement": "M2 repair", "profile": args.profile,
               "cases": cases, "versions": versions, "repeats": args.repeats,
               "started_utc": datetime.now(timezone.utc).isoformat(), "runs": []}
    try:
        with RunLog(LOGS, agent="gold_repair", mode="live") as log:
            print("Execution log: " + str(log.path), flush=True)
            results["run_id"] = log.run_id
            save(output, results)
            for index, (case, version, repeat) in enumerate(steps, 1):
                print(f"[{index}/{len(steps)}] {case} {version} repeat {repeat} ...", end=" ", flush=True)
                record("gold_repair_started", case=case, agent_version=version, repeat=repeat)
                repair = data["repairs"][case]
                outcome = run_one(data["question"], data["cases"][repair["candidate"]], repair, version,
                                  registry.get("Original"))
                results["runs"].append({"case": case, "agent_version": version, "profile": args.profile,
                                        "repeat": repeat, **outcome})
                save(output, results)
                print(outcome["status"], outcome.get("correction_response") or "", f"{outcome['seconds']}s", flush=True)
            results["finished_utc"] = datetime.now(timezone.utc).isoformat()
            save(output, results)
            log.finish(0)
    except KeyboardInterrupt:
        print("\nInterrupted; completed repairs are saved in " + str(output), file=sys.stderr)
        return 130
    finally:
        registry.close()
    print("Results: " + str(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
