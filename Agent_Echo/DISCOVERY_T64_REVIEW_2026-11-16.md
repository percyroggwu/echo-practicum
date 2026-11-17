# Discovery T6.4: independent review

Date: 2026-11-16. Scope: T6.4 of [WORK_BREAKDOWN_DISCOVERY.md](WORK_BREAKDOWN_DISCOVERY.md), a review of the whole Discovery change. That covers phases 0-6: base commit 31a05ff, branch `discovery-phases-0-5` and the uncommitted phase 6 files. Phase 6 results: [DISCOVERY_PHASE6_OFFLINE_REPORT_2026-11-16.md](DISCOVERY_PHASE6_OFFLINE_REPORT_2026-11-16.md).

## How it ran

- **Reviewers.** The user asked for the review here, with Opus 5.5 at extra-high effort instead of Fable. Three read-only reviewers ran in parallel, one per slice:
  - data access, import and evidence boundaries;
  - agent, workflow and runtime;
  - UI backend and frontend, and the scorer.
- **Limits.** No file in the project, no database and no `Echo_UI/cache` or `runs` entry was changed. There were no model, API or network calls. The reviewers ran offline tests and wrote scratch scripts outside the repo.
- **Verification.** The coordinator re-read the code for the five most serious findings, marked "confirmed" below. The other findings are as the reviewers reported them, with how each was checked.
- **Fixes.** Nothing has been fixed yet. Each fix waits for the user's decision.

## Findings

| # | Severity | Where | Defect | Checked |
| --- | --- | --- | --- | --- |
| R1 | High | `agents/discovery_tools.py:126-133` | Every `focus_hint` is resolved as a team name. A topic focus such as "workload" gets no team, so the run returns `needs_clarification` with no candidates. Original never answers and Discovery never runs. Plan line 94 allows a topic focus, and §3.2 says a focus never stops the run. `test_discovery_subject.py:63` encodes the current behavior. | Confirmed; reviewer ran `resolve_subject` for M32 |
| R2 | Medium | `agents/discovery_tools.py:11-40, 116-120` | A `period_hint` the regexes do not parse stops the run with a period clarification, for example "Q2", "this year", "last 6 months", "in June" or "recently". The planner is told to copy the phrase as written. Neither the UI nor the CLI can answer a period clarification. A period outside the dates also asks for clarification, though the plan says it is declined. | Confirmed; reviewer ran `_period` |
| R3 | Medium-high | `Echo_UI/backend/app.py:417` | Demo mode never passes the clarification to `offline.build`. Choosing the right person repeats the same `needs_clarification` forever, for example M02 "Isabel". Tests cover live mode only. | Confirmed; reviewer reproduced it through `start_run` |
| R4 | Medium | `Echo_UI/frontend/src/manager/Brief.tsx:197` | When Original fails, the brief returns early, so the Discovery section (line 353) is never shown and its actions are never registered. The plan says the section is published in that case, and the API does carry it. | Confirmed |
| R5 | Medium | `agents/discovery_checks.py:142-145` | The A3 trigger passes on any cited `OP_activity_weekly` row (`weekly or load > 0`), and the prefilter adds the latest weekly row for every pool person. A3 can therefore pass for normal load. Plan §6.2 requires load above the normal range. | Confirmed; reviewer ran a synthetic pool |
| R6 | Medium | `agents/connections.py:14-16, 55-60` | The Discovery profile keeps the base profile's `request_interval_seconds` and `rate_limit_retries`. The plan (§12, §3.6) says no pacing interval and no 429 retry. If the private GW profile declares 3 rate-limit retries, as PROJECT_CONTEXT says, a 429 waits 20/40/80 s or more before the deadline check. The time is refunded, so Original does not fail. `test_request_pacing.py` asserts that Discovery shares pacing. | Code read; live values from PROJECT_CONTEXT only |
| R7 | Medium (contract) | `agents/discovery_checks.py:117-118, 140-141` | `no_feedback`, and so A2, is checked only against the cited items, so the model can leave out partner feedback that exists in the pool. This matches the prompt contract (`policies.py:64`) but not plan §6.2, "help with no partner feedback". | Reviewer ran a synthetic pool |
| R8 | Low | `agents/discovery.py:125-200` | Only time inside model calls is refunded. Discovery's own code (summary twice, prefilter, checks) takes about 3-3.5 s from Original's budget (M32 3.48 s, M14 2.76 s). Plan §3.6(6) says Original keeps the same seconds. | Reviewer measured with a zero-latency model |
| R9 | Low | `agents/original.py:497-509` | `attach_discovery` can raise after the workflow's error handling, so an internal section mismatch would lose Original's reviewed answer. Only a bug can trigger it. The test checks only the in-memory result. | Code read |
| R10 | Low | `agents/discovery_tools.py:84-86` | A team name shared by two managers, both outside the manager's team (for example Campaign Operations, M17 and M49), asks for clarification instead of declining. Team candidates have no `employee_id`, so the UI cannot answer it. | Code read |
| R11 | Low | `agents/data_access.py:383-388` | Text from after the as-of date can still reach the evidence. When `Completion_Date` is after the as-of date, `Dependency_Description` is kept. This affects 42 of 60 teams, 1-5 rows each. The week of 2026-06-29 (1,901 weekly rows) and capacity periods ending 2026-07-03 count toward Q2 workload. | Reviewer scanned all 60 managers |
| R12 | Low | `agents/data_access.py:455` | A contribution's beneficiary is looked up only when its work request falls inside the window. 758 contributions get no beneficiary (17 cross-team ones for M32, early October) and drop out of help counts. They are formal requests, not hidden work. | Read-only query |
| R13 | Low (latent) | `agents/data_access.py:478-487` | A thread added through its messages credits only the people in the first message. There are no cases in the current data. | Ran on M32, M14 and M31 |
| R14 | Low | `agents/original.py:1103-1106` | The declined and clarification returns leave `DiscoveryData` open until garbage collection. | Code read |
| R15 | Low | `Echo_UI/backend/offline.py` (`declined()`, `unsupported()`) | Two offline artifacts lack `discovery_section`, so the projection shows `null` instead of the `not_run` shape. Gate 6 expects the section for every status. | Code read |
| R16 | Low | `Echo_UI/frontend/src/manager/DiscoverySection.tsx:43` | `changed` compares only how many references are selected, so swapping one reference for another cannot be saved. | Code read |
| R17 | Low | `Echo_UI/backend/followup.py:33` | After an edit that removes every reference, the `unknown` reason still says "This finding has no anchored work". | Code read |
| R18 | Low (pre-existing) | `Echo_UI/frontend/src/manager/Brief.tsx:271` | The declined "Why" card is drawn as a ZeroSugar card, though `checked_by` is `"code"`. | Code read |

## Scorer and test quality

| # | Where | Issue |
| --- | --- | --- |
| S1 | `score_discovery.py:168-172` | The gate 1 `p5_other_managers` check counts a person as reached when any self-review item of theirs is in the pool, not P5's own records. The real result is fine, but the check would still pass with every P5 record dropped. |
| S2 | `score_discovery.py:348-353` | Gate 5 counts `OK (skipped=4)` as a pass, while gates 2-6 treat a skip as unverified. The log has no skip reasons at verbosity 1. |
| S3 | Gate 6 | Two "pass" items are only partly backed: the "ZeroSugar input matches review-v8" item rests on absence tests, and the "scorer finds P1-P6 via the section" item on a synthetic unit test. Gate 6 and overall acceptance still report `unverified`, so the overall result is not overstated. |
| T1 | `tests/test_ui_offline_discovery.py:61-62` | The assertion is always true: the helped-team question returns `None` offline, which makes `(None or ({},))[0].get(...)` empty. The `_subject_plan` rule itself is correct. |
| T2 | `tests/test_discovery_access.py:138-153` | The chosen work reference has no follow-up rows, so the anchor assertions loop over nothing. |
| T3 | `tests/test_import_discovery_profile.py:92-95` | It calls `build_database(..., replace=True)` against the real legacy database path and relies on the `echo.db` guard. If that guard regressed, it would replace `data/echo.db`. |

## Checked and found correct

- **Privacy and scope:** checked across all 60 managers.
  - Analysis evidence has no names or IDs of people outside the team. Another manager's ID appears only in `beneficiary_manager_id`.
  - Scopes enforce the fixed analysis range and the frozen follow-up roster.
  - Share and resolution dates hide what was not yet known at the as-of date.
  - Coverage rows and team plans are limited to the manager.
- **Answer key:** it is absent from the manifest, the runtime database and the index. It is used only by the scorer and the tests; runtime code mentions its folder only in guards.
- **Budget:**
  - at most 3 logical calls, with one shared schema retry;
  - network retries charged to their call and refunded with it;
  - refunds in `finally` with no double refund, and raw counters unchanged;
  - effective budget values used everywhere.
- **Isolation:**
  - nothing from Discovery reaches Original's compose input or ZeroSugar's input;
  - the section is attached after review on every exit and reset on each run;
  - the declined path reads no evidence;
  - the legacy path is unchanged.
- **Actions store:**
  - ownership is enforced (403 or 404 for another manager), and `run_id` cannot be used for path traversal;
  - actions come only from the server-side artifact, and reposting is idempotent;
  - edits accept only allowed references, and versions are append-only.
- **Follow-up:** the A1-A6 rules match plan §6.3, including the A2/A4 match by manager ID and the coverage rule.
- **Fixed range and clarification:** another range or missing dates give a 422. The chosen person is checked against the roster. `recording_key` includes the chosen ID.
- **Scorer:** pool slots come from the current pool rule, findings are read from `discovery_section.rendered`, every ratio needs a non-zero count, and a missing or skipped bound test counts as unverified.

Not reviewed: `Present.tsx`, `HomeDashboard.tsx` and `ActionCenter.tsx`, which may also use the non-fixed range on discovery_v1, and the depth of the t24/t25 tests.

## Fixes applied (2026-11-16, user-approved: R1-R7)

The user raised R4 to high: the Discovery section must be shown when Original fails.

- **R1, topic focus.** `resolve_subject` treats a `focus_hint` that names no team as a topic. The whole team is processed, with no beneficiary filter, and the topic still reaches the model through the question. A team name shared by two managers still asks for clarification. Tests: `test_topic_focus_runs_the_whole_team`.
- **R2, period.**
  - `_period` now also reads:
    - a quarter without a year ("Q2");
    - a month ("in June");
    - a year ("2026", "this year", "last year");
    - a half ("H1 2026", "the first half of 2026");
    - "last N months" or "last N quarters".
  - A phrase it still cannot read no longer stops the run. It reviews all authorized dates, sets `period.hint_not_applied`, and the section says so. The model still never chooses dates.
  - A period outside the authorized dates is now declined (`reason_code: period_out_of_scope`) with its own rule and two next steps, in both the CLI and offline paths. This follows plan §3.1.
  - Tests: `test_period_phrases`, `test_unrecognized_period_keeps_the_window_and_says_so`, `test_limits_and_dates`.
- **R3, demo clarification.** `app.offline_run` passes the chosen employee to `offline.build`, and on to `resolve_subject`. Test: `test_demo_mode_applies_the_clarification`.
- **R4, section when Original fails.** `Brief.tsx` renders `DiscoverySection` (cards and action registration) under the "couldn't finish" card whenever the section is present. Not checked in the browser: the offline demo cannot produce a failed Original run.
- **R5, A3 trigger.** A3 now requires workload above the team's normal range (`_load_above_range > 0`); a cited weekly row alone no longer passes. In focus mode no workload baseline exists, so A3 is withheld there. Test: `test_a3_needs_load_above_range_not_just_a_weekly_row`.
- **R6, Discovery profile.** `DISCOVERY_OVERRIDES` sets `request_interval_seconds: 0` and `rate_limit_retries: 0`. A 429 now ends as `failed_provider` and is refunded.
  - Trade-off: Discovery's request is not spaced by the shared pacer, so on a paced credential it can start right after Original's planning call. The plan accepts that.
  - Tests: the profile test now uses a paced base, and `test_request_pacing` expects Discovery to start unpaced.
- **R7, A2 / `no_feedback`.** A finding marked `no_feedback` is withheld (`visibility_not_supported`) when the person's pool items hold partner feedback from the beneficiary on the same work, cited or not. Feedback on other work does not count. The judgment rule in `policies.py` now says the same. Test: `test_no_feedback_is_withheld_when_uncited_partner_feedback_exists_on_the_work`.

Verification:
- **Offline suite:** 493 tests, 0 failures, 4 skipped. Log: `data/discovery_t64_fix_unit_results.txt`.
- **Frontend:** `npm run build` passes.
- **Databases:** both hashes are unchanged.
- **Not done:** no live call, and no browser check.

R8-R18 and S1-S3, T1-T3 remain open.

## Remaining before live runs

R1-R7 are fixed. The low findings (R8-R18) and S1, S2, T1 and T3 are still open and do not block the live runs.
