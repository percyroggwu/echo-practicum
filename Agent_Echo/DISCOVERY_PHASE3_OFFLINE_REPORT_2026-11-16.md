# Discovery Phase 3: offline implementation report

Date: 2026-11-16. Scope:
- the phase 3 start: the T2.3-T2.5 rework for the 5 + 5 pool;
- T3.1-T3.6 of [WORK_BREAKDOWN_DISCOVERY.md](WORK_BREAKDOWN_DISCOVERY.md), following [plan v10](DISCOVERY_SCOPE_AND_PLAN_v10_2026-11-15.md).

**Implemented and passing offline.** Every model call in the tests is scripted. Nothing was committed, and nothing ran live. Selection quality and judgment quality are **not** measured here; they need the live gates (plan gate 7 and later).

## Who did what

| Work | By | Notes |
| --- | --- | --- |
| T2.3 `lowest_satisfaction(n=5)` | ChatGPT session (GPT-6.1 Sol; it spawned an Astra coordinator) | Finished before its usage limit stopped it |
| T2.4 `team_summary`, T2.5 prefilter with recorded selections, rewritten phase 2 tests and audit | Same session | Code and tests were in place when it stopped. They were verified here, and three test defects were fixed (below) |
| T3.1-T3.6 | Claude Code (Opus 5.5), inline, no subagents | Resumed from the stopped session at the user's request |

## What was built

- **T3.6 budget** (`runtime.py`, `request_pacing.py`, `model.py`, `connections.py`, `resume.py`, `vanilla.py`):
  - `RunBudget` gains `refunded_models`, `paused_seconds`, `refund()` and `effective_deadline()`. `consume()`, `remaining()` and the retry path use the effective values; the raw `models` and `deadline` never change.
  - `respond(..., call_deadline=)`: the request deadline is the earlier of the per-call and the effective run deadline. Only then does `send_request` pass `timeout = min(time left, request_timeout)`; other agents pass no per-request timeout.
  - In the retry path, `consume("model")` now runs after the checks that can refuse a retry. Inside Discovery, a retry that would pass the deadline or the call budget raises `DiscoveryTimeout` without sleeping.
  - `DiscoveryTimeout` (a `RuntimeError` subclass) is raised by `check_request_deadline()` only when a call deadline is set.
  - `snapshot()` carries both refund fields. Resume restores `refunded_models` and checks effective calls. Vanilla's headroom check uses `remaining()`.
- **T3.1 `agents/discovery.py`** (`DiscoveryAgent`):
  - **Call flow:** selection call (team questions) → prefilter → judgment call → code checks → top-5 rule → actions → section.
  - **Limits:** at most 3 logical calls with one shared schema retry, a budget check before every call, and a refund in `finally`.
  - **Failed selection:** the pool is the 5 satisfaction people and the status is `partial`. In focus mode, where there is no satisfaction slot, a failed selection gives `failed_provider` or `failed_budget`.
  - **Output:** `discovery-result-v1` plus `section` (its provenance and rendered text).
- **T3.2 role text** (`policies.py`): `DISCOVERY_ROLE`, `DISCOVERY_SELECTION` and `DISCOVERY_JUDGMENT`. Original's planning rule is written as `DISCOVERY_PLANNING_RULE` but **not yet wired into `original.py`**. The plan fields it refers to arrive in T4.1, and adding the rule earlier would describe fields the current schema does not have.
- **T3.3 `agents/discovery_checks.py`.**
  - The selection check refuses an unknown ID, a duplicate, an ID from the satisfaction slot and a wrong count.
  - The judgment schema check runs on the output itself, without trusting the provider to enforce the strict schema.
  - Each finding is checked for:
    - IDs that exist in the pool, people in scope and evidence belonging to the finding's subjects;
    - exact quotes;
    - the beneficiary (with own-team help refused);
    - visibility and recognition states that match the cited items, including no `not_recognized` under unknown coverage.
  - Action triggers follow plan 6.2.
  - Outside names and IDs are redacted.
  - The top-5 ranking rule follows plan 3.4.
- **T3.5 `agents/discovery_section.py`.**
  - One template per action (A1-A6), the pointer line per status, and a deterministic renderer.
  - Provenance is `{present, status, finding_ids, reviewed_by_zerosugar: false, checked_by_code: true, rendered}`, and `NOT_RUN` is the shape for when Discovery did not run.
  - The partner manager's name appears only in the A2/A4 recipient line, from a new `DiscoveryData.team_manager()`.
- **T3.4 registration.**
  - `AGENTS` includes `Discovery`, `connections.json` has `"Discovery": null`, and `agents/__init__.py` exports `DiscoveryAgent`.
  - Discovery's profile is **derived from Original's profile** as `<base>_discovery`, with `timeout_seconds: 135` and `max_retries: 0`. A local private configuration therefore needs no extra entry.
  - It keeps the base profile's pacing, if any. GW declares none, so Discovery on GW has none, as the plan requires.

## Deviations to note

1. **The prompt serialization is compact.** The summary that `team_summary` returns has one nested block per beneficiary team. Sent as JSON, it was about 168k characters for M32 (about 42k tokens), ten times the plan's estimate.
   - Discovery now sends it as one `|`-separated row per person in ID order (`summary_table`), with the same facts: per-person totals plus `Team: count` for each beneficiary team.
   - The per-team detail for mentions, goals and blockers is summed into the person's totals. No fact is ranked or dropped.
   - The judgment payload drops empty detail fields and repeated provenance text (`judgment_people`).
2. **`partial` does not fire for the 10-person pool.** Every team question reviews 10 people by design, so reaching that size is not reported as a cap. `partial` means that some findings were withheld or that the selection failed. Item caps are listed in `coverage.caps_hit`.
3. **`team_summary` runs twice per team question**, once in `run()` and again inside `prefilter()`. It costs seconds offline and no model calls. Left as is to keep `prefilter`'s interface.
4. **Fixes to the stopped session's tests:**
   - The `test_discovery_t24` privacy regex matched "source" inside "Resource Planning". It now uses whole words.
   - `test_discovery_prefilter`'s pulse row lacked `Quarter`, so the team pool was empty under the 5 + 5 rule.
   - Four connection tests assumed that every role shares one profile (`test_provider_connections`, `test_request_pacing`, `test_workflow`, `test_private_connections`). They now treat Discovery's own profile as the intended exception and assert its 135 s and `max_retries: 0`.

## Verification

Run from `Agent_Echo` with `PYTHONPATH=.venv/Lib/site-packages`:

| Command | Result |
| --- | --- |
| `python -B tests/run_phase2_offline.py` | **422 tests in 470 s, OK (4 skipped)**; log `data/discovery_phase3_unit_results.txt` |
| `python -B tests/run_phase2_offline.py --pattern test_discovery_phase3.py` | 21 tests OK |
| `python -B tests/discovery_phase2_audit.py` | **60 teams, 11 of 11 gates pass, `acceptance_pass: true`**, 1,793 s; `data/discovery_phase2_metrics.json`, log `data/discovery_phase2_audit_results.txt` |
| `git diff --check` | exit 0 (line-ending warnings only) |
| `graphify update .` | exit 0; 4,125 nodes, AST only |

Plan gates 1-3, offline part:

| Check | Result |
| --- | --- |
| Satisfaction slot: M32 `E2198, E0010, E1748, E2156, E1401`; M14 `E1183, E1209, E0450, E0885, E1088` | Pass |
| Whole team for teams of 10 or fewer: M41, M42, M49, M58, M59 | Pass |
| Automatic plants: 47 in the code slot, 73 for the selection | Pass (matches plan 5.7) |
| Every positive outside the code slot is in the summary, with help toward its beneficiary team | 78/78 |
| With a recorded selection that includes them, the prefilter keeps a listed source for hand-built positives / automatic plants | 13/13 · 117/120 (97.5%, gate ≥ 95%) |
| P5's self-review in E0001's line; P6's mentions in E0970's line | 5 · 2 |
| Focus on Infrastructure in M32: every P4 member is listed with Infrastructure evidence | Pass. The list has more than 10 people, so the focused pool also depends on the selection call (live) |
| Privacy, inactive people, caps, dates, summary order, forbidden words | 0 violations |
| Synthetic bad findings withheld (fabricated ID or quote, out-of-scope person, own-team help, `not_recognized` under unknown coverage, unsupported visibility, kind mismatch); bad selections refused; invalid action triggers dropped | Pass |
| 3-call cap with a shared schema retry; failed selection gives `partial`; named people make no selection call; no budget means no call; a timeout gives `failed_budget` and the run continues; refunds restore `remaining()` | Pass |
| A hung request ends at the call deadline: `models` = 1, `request_costs` = 1, no `request_transport_retry` event | Pass |
| Per-request timeout only with a call deadline; a run-level timeout outside Discovery stays a plain `RuntimeError` | Pass |

Listed-source row recall is a diagnostic, not a gate: for example, positive feedback rows 143/308 and blockers 74/77. Each person keeps at most 8 items, so many listed rows cannot fit.

## Token sizes (characters/4; no cached provider tokenizer)

| Manager | Selection summary | Judgment pool (10 people) |
| --- | --- | --- |
| M32 | 50 lines, 14,274 chars, about 3.6k tokens | 54,677 chars, about 13.7k tokens |
| M14 | 30 lines, 9,619 chars, about 2.4k tokens | 52,426 chars, about 13.1k tokens |

These figures leave out the instructions and the output. They are within the plan's 3-4k and roughly 12-13k estimates.

## Known limits (not hidden)

- **M32** has six positives that can enter only through the selection: P3, E1586, E0561, P6 and two automatic plants. There are five slots, so its recall in a team question is reported, not guaranteed.
- **The selection call's choices** are measured only by the live selection-only run over 60 teams (plan gate 7), which needs authorization.
- **The judgment's quality, and D1-D8 rejection,** are live gates 7-9.
- **The 120/135 s values** are starting values, still to be set from a measured latency.

## Changed files

- **Runtime:** `agents/runtime.py`, `agents/request_pacing.py`, `agents/model.py`, `agents/connections.py`, `agents/resume.py`, `agents/vanilla.py`, `agents/data_access.py` (`team_manager`), `agents/policies.py`, `agents/__init__.py`, `connections.json`.
- **New runtime:** `agents/discovery.py`, `agents/discovery_checks.py`, `agents/discovery_section.py`.
- **Phase 2 rework (stopped session):** `agents/discovery_tools.py` plus its tests.
- **Tests:**
  - new: `tests/test_discovery_phase3.py`;
  - edited: `tests/test_discovery_prefilter.py`, `tests/test_discovery_t24.py`, `tests/discovery_phase2_audit.py` (which now measures the prompt forms), `tests/test_provider_connections.py`, `tests/test_request_pacing.py`, `tests/test_workflow.py`.
- **Docs:** this report, a header line on the phase 2 report, `PROJECT_CONTEXT.md`, `DOCUMENTATION_MAP.md`.

| Database | SHA-256 before = after |
| --- | --- |
| data/echo.db | 95db1450b9d4129db0e1efb29c2d31e07adf894a9d2568900246b409dbc766f4 |
| data/echo_discovery_v1.db | b26494d63e2e46c840355ce69630b31fc684ee138b647584a2f3dc7620e03df4 |

## What remains

> Phase 4 is now done offline: [DISCOVERY_PHASE4_OFFLINE_REPORT_2026-11-16.md](DISCOVERY_PHASE4_OFFLINE_REPORT_2026-11-16.md).

- **Phase 4:**
  - T4.1: Original's plan fields, `resolve_subject`, the Discovery step and wiring `DISCOVERY_PLANNING_RULE`;
  - T4.2: release section and provenance;
  - T4.6: capture, CLI and the `report-reader` agent definition.
- **Phase 5:** actions store, follow-up endpoint and UI.
- **Phase 6:** tests and scorer, then the authorized live runs (plan gates 7-11).
