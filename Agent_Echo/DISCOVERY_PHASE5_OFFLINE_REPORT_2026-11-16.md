# Discovery Phase 5: actions, follow-up and UI (offline report)

Date: 2026-11-16. Scope: T5.1-T5.5 of [WORK_BREAKDOWN_DISCOVERY.md](WORK_BREAKDOWN_DISCOVERY.md).
Everything ran **offline** with no model or API calls. The offline demo's Discovery findings come from a fixed rule, not a model, and say so in the section. Phase 4: [DISCOVERY_PHASE4_OFFLINE_REPORT_2026-11-16.md](DISCOVERY_PHASE4_OFFLINE_REPORT_2026-11-16.md).

## Who did what

Each task ran as a subagent with the model and effort the breakdown names. The order followed §10: T5.1 → T5.2 → T5.3 ║ T5.4 ║ T5.5. The coordinator reviewed each result, made the fixes listed under "Coordinator fixes", ran the full suite and checked the UI in a browser.

| Task | Agent | Result |
| --- | --- | --- |
| T5.1 actions store | Sonnet, medium | `Echo_UI/backend/actions.py`; 7 tests |
| T5.2 follow-up | Sonnet, high | `Echo_UI/backend/followup.py`; 11 tests |
| T5.3 frontend | Sonnet, medium | `DiscoverySection.tsx`, sixth agent on stage; build passes |
| T5.4 offline fixtures | Sonnet, medium | `offline.py` Discovery path; 6 tests (+1 from the coordinator) |
| T5.5 dates and clarification | Sonnet, medium | `app.py`, `ClarificationCard.tsx`; 8 tests |

## What was built

- **Actions store (T5.1).** A SQLite `manager_actions` store in `Echo_UI/cache/manager_actions.db`, separate from every source database.
  - `POST /api/managers/{id}/actions {run_id, action_ids?}`: the server reads the actions from the run's own artifact, so the client cannot inject them. Reposting is idempotent and never resets a decision.
  - `GET /api/managers/{id}/actions` returns each action's current state and version history.
  - `PATCH /api/managers/{id}/actions/{action_id}`: accept, edit or dismiss.
    - Dismissing needs a reason.
    - An edit may remove work references, or add only ones from the same finding.
    - Each version stores its own `work_refs` and the simulated decision date, 2026-07-01.
  - `Echo_UI/README.md` notes that there is no authentication and that the store is for synthetic data only.
- **Follow-up (T5.2).** `GET /api/managers/{id}/actions/follow-up` is pure code and reads only through `FollowUpScope`/`FollowUpData`.
  - Its statuses are `observed`, `not_yet`, `unknown`, `pending_decision` (proposed) and `dismissed` (never checked).
  - It applies the plan §6.3 rule for each action type, and the window runs from the decision to 2026-09-30.
  - When nothing matches, the declared 2026-Q3 coverage decides between `not_yet` and `unknown`.
  - A1, A2, A4 and A5 with no anchored work give `unknown`.
  - Results return record IDs only, never names or quotes.
- **Frontend (T5.3).**
  - Discovery is the sixth agent on stage and in the strip. It appears only when `agent="Discovery"` events arrive.
  - The `DiscoverySection` shows:
    - the exact label "Checked by code; not reviewed by ZeroSugar" and the rendered text;
    - typed A1-A6 action cards with Accept, Edit (type, draft and references) and Dismiss (reason required);
    - follow-up badges, with "Pending decision" for proposed actions, under the label "Simulation: observed means a record exists in the synthetic data".
  - Discovery actions are not kept in `localStorage`.
  - A declined question reuses the existing "Why" card (rule, detail, two next steps).
- **Offline fixtures (T5.4).** On discovery_v1 with the fixed range, the offline demo runs Discovery's real code path with a deterministic fixture model, and every output goes through `_checked`. It replays the Discovery events and returns `discovery` and `discovery_section`, both carrying a note that says the findings were chosen by a fixed rule.
  - Out-of-scope questions return the full declined shape, and an ambiguous first name returns `needs_clarification`.
  - The offline subject plan is rule-based, because offline mode has no planner.
  - Legacy is unchanged (`NOT_RUN`).
- **Dates and clarification (T5.5).**
  - **Database.** `ECHO_DATABASE=legacy|discovery_v1` selects the database, and `/api/meta` returns `database` and `fixed_range`.
  - **Range.** On discovery_v1, `POST /api/runs` rejects any range other than 2025-10-01..2026-06-30 with a 422, and the run command gets `--database discovery_v1`. The panels default to the fixed range, and the frontend shows the range read-only.
  - **Clarification.** `RunRequest.clarification` accepts only an `employee_id` from the manager's roster and passes it to `run_agent.py`. `recording_key` includes the chosen ID.
  - **Manager projection.** It gains `discovery_section`, `clarification_candidates` and three basis fields. `discovery` is not projected.

## Coordinator fixes

- **Beneficiary manager ID.** `agents/discovery.py`: each action record now carries `beneficiary_manager_id`, because team names repeat across managers and A6 needs the ID.
- **Offline subject plan.** `Echo_UI/backend/offline.py` sent every team name to `subject_names`, so "Who on my team helped Customer Renewals?" was declined, which breaks gate 3. A team only helped now becomes `focus_hint`. A comparison or a "how is …" question keeps the team as the subject and is declined. A test covers both.
- **Panel range.** `ManagerApp.tsx`: the panel requests fired before `/api/meta` loaded and never refetched, so the home page showed Q3 2026 and the September survey on discovery_v1. Their dependencies now include the range. Checked in the browser: Q2 2026 and the June survey.
- **A2/A4 match by manager ID (user-approved).** `FollowUpData.evidence()` now sets each feedback row's `beneficiary_manager_id` to the author's manager, with the same rule `DiscoveryData.evidence()` already used. The ID is kept apart from the masked fields. `followup.py` matches A2/A4 on that ID only and no longer falls back to the team name. A test points P1's A4 at a manager whose team has the same name and gets `not_yet`.

## Verification

- **Full offline suite** (`tests/run_phase2_offline.py`, network and credential files blocked): 468 tests, 0 failures, 4 skipped. Log: `data/discovery_phase5_unit_results.txt`.
  - It includes `test_ui_actions.py` (7), `test_ui_followup.py` (12), `test_ui_offline_discovery.py` (7) and `test_ui_scope_clarification.py` (8).
  - The UI tests call the handlers directly, because FastAPI's TestClient needs a socketpair, which the runner blocks.
- **Follow-up cases** (gate 4):
  - P1's A1 and A4 are `observed`, and P3's A2 is `not_yet`;
  - a proposed action is `pending_decision`;
  - a share before the decision does not close A4;
  - recognition for other work does not close A1;
  - the M41 A4 plant against the named `partial` row gives `unknown`;
  - A3 matches only `Topic_Code = workload`.

  P1 and P3 come from the answer key, read by test code only.
- **Clarification transport.** M02 has two Isabels (E2191, E2346). "What should I recognize Isabel for this quarter?" is resent unchanged with the chosen ID.
- **`npm run build`** passes. `npm run lint` finds no files to lint, so it checks nothing; its configuration was not changed.
- **Browser check** on a local server with `ECHO_DATABASE=discovery_v1`, M32, Demo mode (offline, no AI):
  - six agents on stage;
  - the Discovery section with both labels and 3 findings;
  - 10 action cards pending a decision;
  - accepting ACT-1-1 (A1) gave `not_yet` with complete coverage;
  - "How are we doing compared with Customer Renewals?" was declined, with `guardrail.checked_by = "code"`, two next steps and the section `not_run`;
  - a legacy range was rejected with a 422.

  These runs left synthetic entries in `Echo_UI/runs/` and `Echo_UI/cache/manager_actions.db`.

## Open points

- **Follow-up speed.** It builds one `DiscoveryData` per decided action, so it is slow for many actions; 11 tests took about 18 s.
- **Untested paths.** The A5 and A6 follow-up paths have no dedicated test.
- **Technical console.** `pages/Ask.tsx` keeps its own date inputs and does not read `fixed_range`. On discovery_v1 the backend rejects its dates.
- **Team size differs between views.** The home page counts 75 people for M32 and Discovery's coverage says 55. The two views count differently; this was not investigated.
- **Venv.** `Agent_Echo/.venv/Scripts/python.exe` points to a Python that no longer exists. The browser check used the system Python with `PYTHONPATH` set to the venv packages (`.claude/launch.json`).
- **Live runs.** The UI was not tested with a live model.

## Changed files

- **Backend:**
  - new: `Echo_UI/backend/actions.py`, `Echo_UI/backend/followup.py`;
  - edited: `Echo_UI/backend/app.py`, `Echo_UI/backend/offline.py`, `Echo_UI/README.md`.
- **Frontend:** `Echo_UI/frontend/src/lib/{agents,events,api}.ts`, `src/index.css`, and in `src/manager/`: `AgentStage.tsx`, `AgentStrip.tsx`, `Brief.tsx`, `ManagerApp.tsx`, plus the new `DiscoverySection.tsx` and `ClarificationCard.tsx`.
- **Agent:** `agents/discovery.py` (`beneficiary_manager_id`), `agents/data_access.py` (follow-up feedback beneficiary).
- **Tests:** `tests/test_ui_actions.py`, `tests/test_ui_followup.py`, `tests/test_ui_offline_discovery.py`, `tests/test_ui_scope_clarification.py`.
- **Other:** `Practicum/.claude/launch.json` (local preview), this report, `PROJECT_CONTEXT.md`, `DOCUMENTATION_MAP.md`.

| Database | SHA-256 before = after |
| --- | --- |
| data/echo.db | 95db1450b9d4129db0e1efb29c2d31e07adf894a9d2568900246b409dbc766f4 |
| data/echo_discovery_v1.db | b26494d63e2e46c840355ce69630b31fc684ee138b647584a2f3dc7620e03df4 |

## What remains

- **Phase 6:** T6.1-T6.4 (tests and scorer), then the authorized live runs (T6.5, plan gates 7-11).
- **Phase 7:** documentation.
