# Discovery Phase 4: offline integration report

Date: 2026-11-16. Scope: T4.1, T4.2, T4.4 (verify only) and T4.6 of
[WORK_BREAKDOWN_DISCOVERY.md](WORK_BREAKDOWN_DISCOVERY.md). Everything ran **offline**, with scripted
models and no provider calls. Scripted Discovery judgments only check plumbing; they are not accuracy
evidence. Phase 3 results: [DISCOVERY_PHASE3_OFFLINE_REPORT_2026-11-16.md](DISCOVERY_PHASE3_OFFLINE_REPORT_2026-11-16.md).

## What was built

- **Plan fields (T4.1).**
  - Original's plan gains `subject_kind` (`team`, `person`, `people`, `other_team`), `subject_names`, `period_hint` and `focus_hint`.
  - `"subject"` was added to both copies of the `missing_field` enum.
  - Saved and demo plans get the defaults through `setdefault`.
  - `DISCOVERY_PLANNING_RULE` is now in the planning instructions.
  - `workflow_plan` records the subject kind, the name count and whether there are period and focus hints, never the names themselves.
- **Workflow order (T4.1).** The order is `plan()` → `resolve_subject` → `set_delegations` → Discovery step → drafts loop.
  - A name outside the manager's team, or a comparison with another team, returns `declined`:
    - `task_outcome = {declined, subject_out_of_scope}`;
    - `verification = {decision: declined, drafts_checked: 0}`;
    - `guardrail = {rule, detail, checked_by: "code"}`;
    - two `next_steps`.

    No evidence is read and no role runs after planning.
  - An unresolved name, or a beneficiary team that is unknown or shared by two managers, returns `needs_clarification`. It has `missing_field = "subject"`, roster candidates in `clarification_candidates`, and a basis that passes `validate_clarification_basis`.
  - `run(question, clarification)` applies `clarification.employee_id` directly, with no name matching.
  - Discovery runs once per in-scope question before the drafts loop. It is in `planned_roles` only. It is not a delegation, a child result or a handoff entry.
  - Nothing from Discovery reaches Original's compose input or ZeroSugar's input (T4.4).
- **Section (T4.2).** `run()` has a single join point, `attach_discovery`, which:
  - re-renders the section from the checked result and requires it to match exactly;
  - stores it in `discovery_section`, outside `answer`, the fact and narrative limits and `release_counts`;
  - stores `discovery` without its `section` key;
  - records a `discovery_section_attached` event.

  Each `run()` starts again from `NOT_RUN`. The section is still published when Original's answer fails (ZeroSugar failure case).
- **Database gate.** The subject check and Discovery act only on `echo_discovery_v1.db`, detected by its `OP_collab_threads` table.
  - On that database, the scope must be the fixed range 2025-10-01 to 2026-06-30; any other range raises `ValueError`.
  - On `data/echo.db`, the new plan fields are parsed and recorded but not acted on, and the section is `not_run`.
- **Plumbing (T4.6).**
  - **CLI.** `run_agent.py` gains `--database {legacy,discovery_v1}` (default legacy). On discovery_v1 the range is fixed.
    - `--clarification-name` and `--clarification-employee` go together, and only with `original --question`.
    - `execution.discovery_applied` is in the report and in `response_finished`.
    - The CLI prints the section after the answer.
  - **Events.** `discovery_call` events record each call's seconds and refund, which is the latency T6.5 needs to set the 120/135 s pair.
  - **Report reader.** `report-reader` reads `discovery_section`, `discovery` and `discovery_applied`.
  - **Demo model.** `--demo` gains a scripted Discovery in `ScriptedDemoModel`. It selects the first summary rows and returns no findings, so a demo never shows invented findings.
  - **Release check.** `check_release.discovery_smoke()` fixes the `NOT_RUN` shape and the unreviewed label.

## Deviations to note

- **A Discovery code error is not caught.** It fails the whole workflow as an `execution_error`, with stage `discovery` and the section `not_run`. Provider errors and timeouts still give `failed_provider` or `failed_budget`, and Original still answers.
- **A failed selection still runs judgment** on the 5 satisfaction people, so a provider outage costs two refunded calls. This is plan §3.6 behavior, now covered by a test.
- **Team names repeat across managers.** For example, "Campaign Operations" is both M17 and M49, and "Budget Controls" is both M08 and M40. A beneficiary named only by team asks for clarification, and the manager ID resolves it.
- **Export and UI are not touched.** They belong to T5.3. The slide export does not show the section yet.

## Verification

- `tests/test_discovery_phase4.py`: 12 tests, all OK. They run full offline workflows on discovery_v1 for M32 and check:
  - Discovery calls (selection, then judgment);
  - that the section is present, outside `answer` and not reviewed;
  - no Discovery content in Original's or ZeroSugar's input;
  - two refunds;
  - the declined other_team and other-team-comparison cases;
  - clarification for an unknown name, an ambiguous team name and an unresolved person, then the chosen ID applied with no selection call;
  - section reset on a second question;
  - the section published on a ZeroSugar failure;
  - a Discovery provider failure;
  - the fixed-range `ValueError`;
  - legacy `not_run`;
  - CLI range and clarification validation;
  - a CLI demo report with `discovery_applied`.
- Full offline suite (`tests/run_phase2_offline.py`, network and credential files blocked): 434 tests, 0 failures, 4 skipped. Log: `data/discovery_phase4_unit_results.txt`.
- Fixtures updated for the new plan keys: `tests/test_gold_plans.py`, `tests/test_clarification_policy.py` and the shared `plan()` in `tests/test_flow_improvements.py`. A live-mode plan must carry the four fields; only saved and demo plans get defaults.
- `check_release` smoke parts (compile, `schema_smoke`, `discovery_smoke`): OK.
- CLI demo on discovery_v1, M32: status `complete`, `discovery_applied: true`, section `no_findings`, 2 Discovery calls, 10 of 55 people reviewed, selection `done`, 0 generation API calls.

## Changed files

- **Runtime:** `agents/original.py`, `agents/discovery_tools.py` (`declined(detail)`), `agents/model.py` (demo Discovery), `run_agent.py`, `check_release.py`.
- **Agent definition:** `Practicum/.claude/agents/report-reader.md`.
- **Tests:**
  - new: `tests/test_discovery_phase4.py`;
  - edited: `tests/test_gold_plans.py`, `tests/test_clarification_policy.py`, `tests/test_flow_improvements.py`.
- **Docs:** this report, `PROJECT_CONTEXT.md`, `DOCUMENTATION_MAP.md`.

| Database | SHA-256 before = after |
| --- | --- |
| data/echo.db | 95db1450b9d4129db0e1efb29c2d31e07adf894a9d2568900246b409dbc766f4 |
| data/echo_discovery_v1.db | b26494d63e2e46c840355ce69630b31fc684ee138b647584a2f3dc7620e03df4 |

## What remains

> Phase 5 is now done offline: [DISCOVERY_PHASE5_OFFLINE_REPORT_2026-11-16.md](DISCOVERY_PHASE5_OFFLINE_REPORT_2026-11-16.md).

- **Phase 5:** actions store, follow-up endpoint, UI and export of the section (T5.3).
- **Phase 6:** scorer and tests, then the authorized live runs (plan gates 7-11). Gate 11, the M3 rerun, also covers the global plan-schema change.
