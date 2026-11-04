"""M2: run the frozen gold repair cases (R1-R6) through Original v7 and/or v8.

LIVE MODE MAKES MODEL API CALLS. Only Original runs, for one repair round: the saved candidate
from cases.json is loaded as the saved draft, one correction is pending, no specialist is
offered and no review follows. This measures editing alone. Results use the format
score_gold.py reads (answer and correction_response per run).

    python run_gold_repair.py --profile apinex_test --dry-run
    python run_gold_repair.py --profile apinex_test --repeats 1
    python score_gold.py sheet reports_gold/<results>.json reports_gold/<sheet>.md
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

from agents import AccessScope
from agents.connections import DEFAULT_CONFIG, ModelRegistry
from agents.content import block_catalog
from agents.delivery_diagnostics import duplication, repair_context
from agents.execution_log import RunLog, record, error_summary
from agents.grounding import FactCatalog
from agents.original import OriginalAgent
from agents.original_v8 import OriginalAgentV8, REPAIR_NOTE
from agents.runtime import RunBudget, Specialist
from gold_cases import CASEBOOK_SHA256, OUTPUT as CASES
from run_gold_review import plan, save

HERE = Path(__file__).resolve().parent
DATABASE = HERE / "data" / "echo.db"
LOGS = HERE / "reports" / "logs"
ORIGINALS = {"v7": OriginalAgent, "v8": OriginalAgentV8}
MODEL_CALLS, SECONDS = 14, 600   # Original keeps its own seven-turn cap inside this budget

# The same message OriginalAgent.workflow sends at the start of a v7 repair round.
V7_REPAIR_MESSAGE = ("The saved answer is supplied once through available_blocks. "
    "Assess each correction against the question, saved blocks and evidence. "
    "Repair justified mandatory issues; explain any unjustified requirement or contradictory repair "
    "so ZeroSugar can independently withdraw or reassess it. Never change supported meaning merely to comply. "
    "Preserve supported facts, meaning and sources, "
    "Explain each removal in removal_reasons. If replacing requested content, supply its replacement "
    "in this same submission. A repaired citation is not a reason to delete examples, questions or limits. "
    "while allowing rephrasing, reordering, qualitative synthesis and removal of redundant presentation. "
    "Reuse existing evidence; the revised candidate will be reviewed again. Answer in English. "
    "The active pending corrections are supplied in the coordination context; the retrieved evidence "
    "is supplied once as source evidence. The complete review verdict is not needed for this repair.")


def prepared_original(version, candidate, correction, model, budget):
    """An Original whose saved draft is the candidate, as after a completed review."""
    scope = AccessScope(**candidate["scope"])
    agent = ORIGINALS[version](DATABASE, scope, lambda name: model, "live")
    agent.budget, agent.repair_round = budget, 1
    agent.numeric_requested = True   # the workflow sets this for a sentiment question
    catalog = FactCatalog(candidate["evidence"], candidate["scope"])
    blocks = block_catalog(candidate["grounding"]["payload"], candidate["evidence"], candidate["scope"], catalog.facts)
    agent.draft_blocks, agent.reusable_blocks, agent.draft_texts = dict(blocks), dict(blocks), {}
    challenges = []
    if version == "v7":
        # v7 disputes through challenge_corrections; record it instead of starting a review.
        agent.last_verdict = SimpleNamespace(corrections=[correction])
        agent.handlers["challenge_corrections"] = lambda correction_ids, finding_ids, reason: (
            challenges.append({"correction_ids": correction_ids, "reason": reason})
            or {"status": "recorded", "note": "This evaluation records the challenge without a new review. "
                "Submit the answer you consider correct."})
        agent.set_delegations([])
        context = [{"role": "user", "content": V7_REPAIR_MESSAGE},
                   {"role": "user", "content": json.dumps({"numeric_coverage": [],
                       "pending_corrections": repair_context([correction], agent.draft_blocks)})}]
    else:
        agent.set_delegations([])
        agent.open_corrections = agent.compact_corrections(repair_context([correction], agent.draft_blocks))
        context = [{"role": "user", "content": REPAIR_NOTE}]
    return agent, context, challenges


def run_one(question, candidate, repair, version, model):
    budget = RunBudget(model_limit=MODEL_CALLS, tool_limit=2 * MODEL_CALLS, seconds=SECONDS)
    correction = repair["correction"]
    agent, context, challenges = prepared_original(version, candidate, correction, model, budget)
    started, result = time.monotonic(), {"status": "completed"}
    try:
        answer = Specialist.run(agent, question, initial_evidence=candidate["evidence"], context=context).answer
        if version == "v8":
            response = (agent.correction_responses.get(correction["correction_id"]) or {}).get("response")
        else:
            response = "disputed" if challenges else "fixed"
        result.update(answer=answer, correction_response=response, changed=answer != candidate["answer"],
                      duplicate_paragraph_pairs=duplication(answer)["pair_count"])
    except (RuntimeError, ValueError) as error:
        summary = error_summary(error)
        result.update(status="protocol_failure" if isinstance(error, RuntimeError) else "error", error=summary,
                      correction_response="disputed" if challenges else None)
    finally:
        agent.close()
    diagnostics = getattr(agent, "last_result", None).diagnostics if getattr(agent, "last_result", None) else {}
    result.update(seconds=round(time.monotonic() - started, 1), model_calls=budget.models,
                  input_tokens=sum(u.get("input_tokens", 0) for c in budget.request_costs for u in c["provider_usage"]),
                  output_tokens=sum(u.get("output_tokens", 0) for c in budget.request_costs for u in c["provider_usage"]),
                  rejected_attempts=len(diagnostics.get("rejected_attempts", [])),
                  rejection_codes=sorted({r.get("validation_code") for r in diagnostics.get("rejected_attempts", [])
                                          if r.get("validation_code")}),
                  challenges=challenges)
    return result


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", required=True, help="Model profile for Original, e.g. apinex_test.")
    parser.add_argument("--cases", default=",".join(f"R{i}" for i in range(1, 7)), help="Comma-separated, default R1-R6.")
    parser.add_argument("--versions", default="v7,v8", help="Comma-separated: v7, v8 or both (default).")
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
