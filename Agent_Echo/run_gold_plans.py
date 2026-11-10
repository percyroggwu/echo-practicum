"""M3: run the planning gold cases (reports_gold/GOLD_PLANS_v1.json) through OriginalAgent.plan().

LIVE MODE MAKES MODEL API CALLS. Only Original's planning step runs (at most two planning calls
per case-run); no specialist
model is called. The raw submit_plan arguments of every call are saved as a diagnostic; the
pass criterion is the final plan.

    python run_gold_plans.py --profile apinex_test --dry-run
    python run_gold_plans.py --profile apinex_test --repeats 2
"""

from datetime import datetime, timezone
from pathlib import Path
from agents import AccessScope
from agents.connections import DEFAULT_CONFIG, ModelRegistry
from agents.execution_log import RunLog, record, error_summary
from agents.original import OriginalAgent
from agents.runtime import RunBudget
from gold_plans import CASEBOOK, PLANS_SHA256, load, mismatches, observed, sha256, summary
from run_gold_review import save
import argparse
import sys
import time

HERE = Path(__file__).resolve().parent
DATABASE = HERE / "data" / "echo.db"
LOGS = HERE / "reports" / "logs"
MODEL_CALLS, TOOL_CALLS, SECONDS = 5, 2, 300   # two planning attempts plus transport retries; one describe()


class RecordingModel:
    """Passes calls through and keeps the raw tool-call arguments, before code normalizations."""
    def __init__(self, model):
        self.model, self.raw = model, []

    def respond(self, *args, **kwargs):
        turn = self.model.respond(*args, **kwargs)
        self.raw.append([{"name": c.name, "arguments": c.arguments} for c in turn.calls])
        return turn

    def __getattr__(self, name):
        return getattr(self.model, name)


def run_one(case, scope, model, database=DATABASE):
    budget = RunBudget(model_limit=MODEL_CALLS, tool_limit=TOOL_CALLS, seconds=SECONDS)
    recorder = RecordingModel(model)
    agent = OriginalAgent(database, AccessScope(**scope), lambda name: recorder, "live")
    agent.budget = budget
    started, result = time.monotonic(), {"status": "completed"}
    try:
        seen = observed(agent.plan(case["question"]))
        result.update(plan=seen, mismatches=mismatches(case["expected"], seen))
    except (RuntimeError, ValueError) as error:
        result.update(status="protocol_failure" if isinstance(error, RuntimeError) else "error",
                      error=error_summary(error), mismatches=None)
    finally:
        agent.close()
    result.update(seconds=round(time.monotonic() - started, 1), model_calls=budget.models, raw_calls=recorder.raw,
                  planning_diagnostics=getattr(agent, "planning_diagnostics", []),
                  input_tokens=sum(u.get("input_tokens", 0) for c in budget.request_costs for u in c["provider_usage"]),
                  output_tokens=sum(u.get("output_tokens", 0) for c in budget.request_costs for u in c["provider_usage"]))
    return result


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", required=True, help="Model profile for Original, e.g. apinex_test.")
    parser.add_argument("--cases", help="Comma-separated case ids; default all.")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--output", type=Path, help="New results file; default reports_gold/plans_<profile>_<UTC>.json.")
    parser.add_argument("--connections", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true", help="Check inputs and print the plan; no API call.")
    args = parser.parse_args(argv)

    data = load()
    by_id = {c["id"]: c for c in data["cases"]}
    cases = [c.strip() for c in args.cases.split(",")] if args.cases else list(by_id)
    if unknown := [c for c in cases if c not in by_id]:
        parser.error("Unknown cases: " + ", ".join(unknown))
    if not 1 <= args.repeats <= 5:
        parser.error("--repeats must be 1-5.")
    digest = sha256()
    frozen = digest == PLANS_SHA256
    steps = [(case, repeat) for repeat in range(1, args.repeats + 1) for case in cases]
    print(f"{len(steps)} plans: {len(cases)} cases x {args.repeats} repeats, profile {args.profile}.")
    print(f"Expected model calls: at least {len(steps)}, at most {2 * len(steps)} (plus transport retries).")
    print(f"Casebook {CASEBOOK.name} sha256 {digest[:12]}: " + ("frozen." if frozen else "NOT FROZEN (draft)."))
    if args.dry_run:
        for case, repeat in steps:
            c = by_id[case]
            print("  ", case, repeat, "hard" if c.get("hard") else "", c["expected"])
        print("Dry run: no API call was made.")
        return 0
    if not frozen:
        parser.error("The planning casebook is not frozen: the user approves the expected plans and PLANS_SHA256 is set first.")

    output = args.output or CASEBOOK.parent / (
        f"plans_{args.profile}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json")
    if output.exists():
        parser.error("Output already exists; choose a new filename so earlier results are preserved.")
    output.parent.mkdir(parents=True, exist_ok=True)
    registry = ModelRegistry(args.connections, args.profile)
    results = {"casebook_sha256": digest, "measurement": "M3 planning", "profile": args.profile, "cases": cases,
               "repeats": args.repeats, "started_utc": datetime.now(timezone.utc).isoformat(), "runs": []}
    try:
        with RunLog(LOGS, agent="gold_plans", mode="live") as log:
            print("Execution log: " + str(log.path), flush=True)
            results["run_id"] = log.run_id
            save(output, results)
            for index, (case, repeat) in enumerate(steps, 1):
                print(f"[{index}/{len(steps)}] {case} repeat {repeat} ...", end=" ", flush=True)
                record("gold_plan_started", case=case, repeat=repeat)
                c = by_id[case]
                outcome = run_one(c, c.get("scope", data["default_scope"]), registry.get("Original"))
                results["runs"].append({"case": case, "repeat": repeat, "profile": args.profile, **outcome})
                save(output, results)
                print(outcome["status"], "pass" if outcome["mismatches"] == [] else outcome["mismatches"] or "",
                      f"{outcome['seconds']}s", flush=True)
            results["finished_utc"] = datetime.now(timezone.utc).isoformat()
            results["summary"] = summary(results["runs"], data["cases"])
            save(output, results)
            log.finish(0)
    except KeyboardInterrupt:
        print("\nInterrupted; completed plans are saved in " + str(output), file=sys.stderr)
        return 130
    finally:
        registry.close()
    print("Summary: " + str(results["summary"]))
    print("Results: " + str(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
