"""Gate 7 (plan section 8, T6.5): Discovery's selection call alone, over every team in discovery_v1.

LIVE: makes real model calls. Run it only with explicit authorization.
  python run_discovery_selection.py --profile gw_azure --output reports/discovery_t65_selection.json

Each team that needs a selection gets one logical call (plus at most one schema retry), with the
same instructions, summary, tool and checks as a real team question. Teams of 10 or fewer need no
call and are recorded with []. There is no judgment call.

The output's "teams" list is the input for:
  python score_discovery.py --selection-report reports/discovery_t65_selection.json
It also records calls, tokens, latency and failures per team. Failed teams stay out of "teams";
rerun with --resume and the same --output to retry only those. The scorer needs all teams.

Calls are spaced by --interval seconds, because Discovery's profile has no pacing of its own
(plan: about 60 calls and 200-250k input tokens under GW's limit of about 50k tokens per minute).
"""

from pathlib import Path
import argparse
import json
import sqlite3
import statistics
import sys
import time

from agents.connections import DEFAULT_CONFIG, ModelRegistry
from agents.data_access import DiscoveryData, DiscoveryScope, DISCOVERY_RANGE
from agents.discovery import DiscoveryAgent, SELECTION_FAILURES, CALL_CAP, CALL_SECONDS
from agents.discovery_tools import resolve_subject, team_summary
from agents.execution_log import RunLog, record
from agents.runtime import RunBudget

HERE = Path(__file__).resolve().parent
DATABASE = HERE / "data" / "echo_discovery_v1.db"
LOG_DIRECTORY = HERE / "reports" / "logs"
QUESTION = "How is my team doing?"


def managers(database):
    with sqlite3.connect(Path(database).as_uri() + "?mode=ro", uri=True) as source:
        return [r[0] for r in source.execute("SELECT Manager_ID FROM HR_managers ORDER BY Manager_ID")]


def select_team(database, manager, model, question, call_seconds):
    """One team's selection; returns a report row. Never raises for a model failure."""
    data = DiscoveryData(database, DiscoveryScope(manager, *DISCOVERY_RANGE))
    try:
        resolution = resolve_subject(data, {"subject_kind": "team"})
        summary = team_summary(data, resolution.get("focus_hint"), resolution["period"])
        row = {"manager_id": manager, "team_size": len(data.roster()), "selection_count": summary["selection_count"],
               "summary_people": len(summary["lines"]), "selected_employee_ids": [], "status": "not_needed",
               "calls": 0, "schema_retries": 0, "input_tokens": 0, "output_tokens": 0, "seconds": 0.0}
        if not summary["selection_count"]:
            return row
        agent = DiscoveryAgent(data, model, RunBudget(model_limit=CALL_CAP, tool_limit=CALL_CAP,
                                                      seconds=call_seconds * CALL_CAP), call_seconds)
        agent.start()
        started = time.monotonic()
        try:
            row["selected_employee_ids"] = agent.select(question, summary)
            row["status"] = "done"
        except SELECTION_FAILURES as failure:
            row["status"], row["failure"] = "failed", getattr(failure, "code", None) or type(failure).__name__
        row.update(calls=agent.calls, schema_retries=int(agent.retry_used), seconds=round(time.monotonic() - started, 3),
                   **agent.usage)
        record("discovery_selection_team", manager_id=manager, status=row["status"], calls=row["calls"],
               seconds=row["seconds"], input_tokens=row["input_tokens"])
        return row
    finally:
        data.close()


def summarize(rows, profile, question):
    called = [r for r in rows.values() if r["calls"]]
    latency = sorted(r["seconds"] for r in called)
    return {
        "measurement": "Discovery gate 7, selection only", "profile": profile, "question": question,
        "range": list(DISCOVERY_RANGE),
        # Scorer input: every team that has a valid selection (done or not needed).
        "teams": [{"manager_id": m, "selected_employee_ids": r["selected_employee_ids"]}
                  for m, r in sorted(rows.items()) if r["status"] in {"done", "not_needed"}],
        "failed": sorted(m for m, r in rows.items() if r["status"] == "failed"),
        "totals": {"teams": len(rows), "calls": sum(r["calls"] for r in rows.values()),
                   "schema_retries": sum(r["schema_retries"] for r in rows.values()),
                   "input_tokens": sum(r["input_tokens"] for r in rows.values()),
                   "output_tokens": sum(r["output_tokens"] for r in rows.values()),
                   "latency_p50": round(statistics.median(latency), 3) if latency else None,
                   "latency_max": latency[-1] if latency else None},
        "rows": [rows[m] for m in sorted(rows)],
    }


def write(path, report):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", required=True, help="Model profile, e.g. gw_azure; Discovery's overrides apply.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true", help="Keep finished teams in --output and retry the rest.")
    parser.add_argument("--managers", help="Comma-separated manager IDs; default all.")
    parser.add_argument("--question", default=QUESTION, help="The team question shown to the selection call.")
    parser.add_argument("--interval", type=float, default=8.0, help="Seconds between calls (default 8).")
    parser.add_argument("--call-seconds", type=int, default=CALL_SECONDS)
    parser.add_argument("--connections", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true", help="List the teams that need a call; no API call.")
    args = parser.parse_args(argv)
    every = managers(DATABASE)
    chosen = [m.strip() for m in args.managers.split(",")] if args.managers else every
    if set(chosen) - set(every):
        parser.error("Unknown manager: " + ", ".join(sorted(set(chosen) - set(every))))
    if args.output.exists() and not args.resume and not args.dry_run:
        print("Output already exists. Use --resume to continue it, or choose a fresh filename.", file=sys.stderr)
        return 1
    rows = {}
    if args.resume and args.output.exists():
        previous = json.loads(args.output.read_text(encoding="utf-8"))
        if previous.get("profile") != args.profile or previous.get("question") != args.question:
            parser.error("--resume needs the same --profile and --question as the saved run.")
        rows = {r["manager_id"]: r for r in previous["rows"] if r["status"] in {"done", "not_needed"}}
    pending = [m for m in chosen if m not in rows]
    if args.dry_run:
        need = []
        for manager in pending:
            data = DiscoveryData(DATABASE, DiscoveryScope(manager, *DISCOVERY_RANGE))
            try:
                resolution = resolve_subject(data, {"subject_kind": "team"})
                if team_summary(data, None, resolution["period"])["selection_count"]:
                    need.append(manager)
            finally:
                data.close()
        print(f"{len(pending)} teams pending; {len(need)} need a selection call: {', '.join(need)}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with RunLog(LOG_DIRECTORY, agent="discovery_selection", mode="live") as log:
        print("Execution log: " + str(log.path), flush=True)
        registry = ModelRegistry(args.connections, args.profile)
        try:
            model = registry.get("Discovery")
            last_call = None
            for index, manager in enumerate(pending, 1):
                if last_call is not None:
                    time.sleep(max(0.0, args.interval - (time.monotonic() - last_call)))
                row = select_team(DATABASE, manager, model, args.question, args.call_seconds)
                if row["calls"]:
                    last_call = time.monotonic()
                rows[manager] = row
                write(args.output, summarize(rows, args.profile, args.question))
                print(f"{index}/{len(pending)} {manager}: {row['status']}"
                      + (f" ({row['seconds']} s, {row['input_tokens']} input tokens)" if row["calls"] else ""), flush=True)
        finally:
            registry.close()
        report = summarize(rows, args.profile, args.question)
        print(f"Teams: {len(report['teams'])} ready, {len(report['failed'])} failed. "
              f"Calls {report['totals']['calls']}, input tokens {report['totals']['input_tokens']}.")
        if report["failed"]:
            print("Rerun with --resume and the same --output to retry: " + ", ".join(report["failed"]))
        log.finish(0 if not report["failed"] else 1)
        return 0 if not report["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
