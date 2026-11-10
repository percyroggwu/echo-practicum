# Echo: current project context

## Spare review attempt and live runs 81-90, 2026-11-10

Branch `review-truncation-spare` (`92fa811`). Gate: 305 tests pass, 4 skipped.

- **Fix.** A review phase with a truncated attempt can now use the run's one shared protocol
  exception. Before, only a missing tool call made a phase eligible.
  - Every failed support phase since run 67 had lost at least one of its three attempts to
    a reasoning-only truncation, and none had used the exception: Gemini 68, Luna 70, 72, 74
    and 81.
  - The exception is still limited to one per run and to the remaining budget.
- **Live runs** used the question of runs 63-69:

| Runs | Code | Complete | Notes |
|---|---|---|---|
| Luna 81, 83; Gemini 82, 84 | `0e8c9e9` | 3 of 4 | 81 failed: its first support review truncated twice, then had `finding_missing`, with the exception unused. That led to the fix. 81 is also the first live firing of `label_issue_outside_disputes_dropped`. |
| Luna 85, 87, 89; Gemini 86, 88, 90 | `92fa811` | 2 of 6 (88, 89) | Each partial run failed for a different reason (see below). |

- **What fired in runs 85-90:**
  - `clarification_with_specialist` dropped two false clarifications. In 85 the model asked
    whether Vanilla or Cherry should do the work; in 86 it asked whether Q3 2026 meant the
    supplied window.
  - The spare attempt rescued run 90's support review after one truncated and one rejected
    attempt.
- **Partial runs:**
  - Luna 85 reached the draft limit: the reviewer raised a new objection on each of the
    4 drafts.
  - Gemini 86: on draft 3, the completeness review returned no tool call 4 times, including
    the spare attempt (`tool_call_count`).
  - Luna 87: the plan set `needs_numbers` with no metrics (the P1 pattern). Original then asked
    Cherry for the comment records, Cherry truncated, and because Cherry was in the plan,
    `accept()` blocked a review that had accepted.
  - Gemini 90 hit the 32-call limit on draft 3.
- **Since run 67:** 11 of 24 runs are complete. By batch: 2 of 10, 4 of 4, 3 of 4, 2 of 6.
- **Open items:**
  - review churn across drafts (85, 90);
  - Gemini returning no tool call in review (86);
  - planned-but-unneeded Cherry blocking an accepted answer (87);
  - clarifications whose plan selects no specialist (run 73);
  - the genuine label-dispute path.

## Clarification rule kept, 2026-11-09

Branch `planning-clarification-rule`. `plan()` drops a clarification when the same plan
already selects a specialist (`clarification_with_specialist`). Gate: 304 tests pass, 4 skipped.

- M3 under criteria v4 rule 3:
  - passes rose to 20 on test (baseline 18) and 21 on Gemini (baseline 17);
  - false clarifications went from 0 to 0 on test and from 3 to 0 on Gemini;
  - P12 and P13 still ask in all 8 case-runs.
- The details are in `reports_gold/DEVIATIONS.md`, "Clarification rule".
- The rule does not cover clarifications whose plan selects no specialist, such as live run 73
  ("May I classify…") and Gemini P11 r1. That open item stays.

## Review fixes and live runs 70-80, 2026-11-09

Branch `v8-followups`: code fixes only, no prompt line. Gate: 303 tests pass, 4 skipped.

- **Planning prompt trial: reverted, never committed.** Two existing `PLANNING_INSTRUCTIONS`
  lines were clarified: one for P1 `needs_numbers`, one for P7/P10 `needs_sentiment`. A full M3
  re-run measured them (`plans_apinex_test_20261108_195232.json`,
  `plans_apinex_gemini_test_20261108_202243.json`). Neither edit met criteria v4 rule 3:
  - Gemini failed P1 in both repeats.
  - P10 passed 1 of 4 and P7 3 of 4.
  - Gemini fell to 16, below its baseline of 17; test rose to 19.
  - See `reports_gold/DEVIATIONS.md`, "Planning prompt trial".
- **Review fixes.** Each one comes from a live run capture:
  - `16774e6`, from Luna 67. ZeroSugar now drops a Vanilla new issue that targets a
    classification table and cites one of its labeled comments
    (`label_issue_outside_disputes_dropped`).
    - What happened: the reviewer called the label defensible in `label_disputes`, then raised
      it again as a new issue. No role can relabel a code-rendered table, and Original's
      hand recount hit the output cap.
    - Absences (`missing_deliverable`) are never dropped, so Gemini 54's variant is not
      covered.
  - `edf08b7`, from Gemini 68. When a finding has more than 12 assertions and all are
    supported, it keeps the first 12 (`supported_assertions_truncated`). The last attempt had
    43 near-copies for F9. Gemini 60's case (mislabeled, partly unsupported assertions) is
    still rejected.
  - `2e6144a`, from Luna 72 and Gemini 71:
    - The label filter honors `safety_issue_index` only with a safety score of 1 or 2, as
      `safety_gate` does. Run 72 linked the label issue at score 3.
    - `accept()` blocks only on failures of specialists the plan required (`planned_roles`).
      In 71, Original asked Cherry, outside the plan, to recheck code-rendered counts. Cherry
      truncated twice, and a review that accepted 20 of 20 findings ended partial.
  - `2989051`, from Luna 74. Supported assertions for findings that are not pending (already
    reviewed, or a classification table) are now dropped (`assertion_outside_pending_dropped`)
    instead of failing the attempt. The slip appeared in 71 (twice), 72, 74 and 75.
- **Live runs** used the question of runs 63-69. The agent code hashes in each capture match
  the commit listed:

| Runs | Code | Complete | Notes |
|---|---|---|---|
| Luna 70, Gemini 71, Luna 72 | `edf08b7` | 0 of 3 | 70: support protocol failure on draft 4. 71: accepted, then partial (fixed in `2e6144a`). 72: call limit after the label issue passed through the safety link. |
| Luna 73, 74, 76; Gemini 75 | `2e6144a` | 1 of 4 (76) | 73: false clarification ("May I classify…"), kept after the recheck. 74: support protocol failure (fixed in `2989051`). 75: one provider call waited 2.5 h and hit the time limit. |
| Luna 77, 79; Gemini 78, 80 | `2989051` | 4 of 4 | 9-25 calls, 152-481 s. |

- **Reading the results.**
  - None of the new normalization events fired in runs 70-80, so the 4 of 4 is not
    attributable to these fixes.
  - Runs 77-80 also had far fewer reviewer rejections and reasoning-only truncations than
    runs 67-76.
  - Since run 67, 6 of 14 runs are complete.
  - Run 80's plan marked numbers and a chart the question did not ask for (the P1 pattern).
    `optional_chart_dropped` absorbed the chart, and Cherry was never called.
- **Open items:**
  - planning false clarifications (run 73);
  - a correction path for a genuine, non-defensible label dispute.
- **Decided, no change:**
  - Per-request time cap. Run 75's call returned at 18:33:38 and run 76 started at 18:34:10,
    so the machine most likely slept. No code runs during sleep, so a cap could not have cut
    the call. `timeout_seconds` already stops a server that sends nothing.
  - `reasoning_effort` stays unset for the APInex profiles.
    - In runs 67-80, 11 of 245 calls truncated with only reasoning output (9 in ZeroSugar,
      2 in Cherry). The median reasoning per call was 200-1,600 tokens, well under the cap of
      6,000.
    - Lowering the effort would change every call, including review judgments measured by
      M1 and M2 at the default effort, to address a tail of about 4.5%.
    - If it is revisited, use a separate profile, probe that APInex accepts the parameter,
      and compare M1 reviewer results against the baseline.

## Priority 2 closed and live runs 67-69, 2026-11-08

Decision: all seven restored v7 lines are reverted. Line A was reverted by M1 (criteria v1), the
two group B lines by M2 (v2), and the four group C lines by M4 (v3). M3 was stopped by the
`plan()` protocol defect. The evidence is in `reports_gold/DEVIATIONS.md` and in the
re-runs in `reports_gold/RERUN_COMPARISON_20261107.md`. Shipped code is `revert-p2-lines` merged into
`main`, tag `v8-shipped`.
Runs 67 (Luna), 68 and 69 (Gemini, 69 a repeat) used the runs 63-66 question. The plan never
asked the manager for data and never added a chart. Run 69 set `needs_numbers` true (M3 hard
case P1). All three found 9 positive, 2 negative and 2 mixed among 13 comments. Run 69 ended
complete/accept. Runs 67 and 68 ended partial after planning, with an earlier reviewed draft
released. In 67 the revised answer hit the 6,000 output-token cap. In 68 the draft 2 support
review failed 3 attempts.
Open items, outside priority 2: see the follow-ups below.

## Follow-ups after v8-shipped, 2026-11-08

Branch `v8-followups`, from `main` at `52b3003`. These are code fixes, not prompt lines. Gate:
299 tests pass, 4 skipped (303 after the 2026-11-09 review fixes above).

- **Casebook hash.** `gold_cases.sha256()` normalizes CRLF to LF before hashing, as
  `gold_plans` and `gold_m4` already do. `CASEBOOK_SHA256` is now the committed blob
  (`2ed93543…`). The old CRLF hash `24d84029…`, carried by `cases.json` and the M1/M2 results,
  is still accepted as `LEGACY_CASEBOOK_SHA256`.
- **`plan()` recheck.** The clarification recheck adds one planning turn instead of spending
  one of the two attempts. That spent attempt caused the 7 M3 protocol failures.
  `run_gold_plans.py` now allows 5 calls per case-run. Criteria v4 for the M3 re-run is frozen
  (`reports_gold/P2_DECISION_CRITERIA_v4.md`, `6189ffb`, `a0812a52…`).
  - M3 re-run (2026-11-08): 0 protocol failures, so the fix is kept. Passed: apinex_test 18 of
    28 (first run 17), apinex_gemini_test 17 of 28 (15).
  - Hard cases P1, P10 and P11 still fail. Gemini has 3 false clarifications.
  - `needs_sentiment` (P7, P10) and `needs_numbers` (P1) now meet the condition for opening a
    planning rule. See `reports_gold/DEVIATIONS.md`, "M3 re-run".
- **C3 chart review.** `visible_inventory` lists rendered charts, with kind, title, axes,
  unit, denominator and source. The instructions say the inventory is what the reader sees,
  but it listed only tables. In 3 of 6 C3 reviews the reviewer then called the chart
  missing. The completeness-only `visible_charts` key is gone. The Gemini "32 out of 36"
  invention, seen once, is not addressed.
  - Measured on `c23bf23` (2026-11-08, `m4_reverted_*_20261108_14*`/`15*`: test 3 runs,
    Gemini 2). C3 accept: test 1 of 3, Gemini 2 of 2.
  - The false "no chart" claim appears in 1 of 3 test runs (r1, "only metadata in
    visible_inventory") and in 0 of 2 Gemini runs. Before the fix it appeared in 1 of 1
    test reverted run.
  - Test r3 is a close call: no chart or denominator objection, but F4 is withheld over an
    assumption the answer already labels as one.
  - C1 test r1 was a completeness protocol failure (4 attempts). Its rejection codes are not
    in the result.
  - **Tried and reverted:** extending the completeness rule "Tables listed in
    visible_inventory are visible" to tables and charts, with each chart rendered. It was
    measured uncommitted (`m4_reverted_*_20261108_152*`/`153*`: test 3 runs, Gemini 2;
    C1 prompt `57e01569bf34`).
    - C3 accept: test 2 of 3, Gemini 2 of 2.
    - The false "no chart" claim is still in 1 of 3 test runs: r1 says the evidence holds
      "only an abstract line-chart specification", which is probably the support phase.
    - C1 looked worse, possibly noise: test r1 cited "no visible charts" where none was
      asked, and test r3 invented a neutral CMT27511 excerpt in the inventory.
    - With no gain on the target case, the line was reverted by the M4 standard: no prompt
      line without a measured benefit. The inventory fix (code) stays.
  - Open: the test reviewer sometimes does not accept that a listed chart is rendered
    (1 of 3 in both batches).
- **Output-token cap: not raised.** A19 keeps the cap and adds recovery. The run captures
  do not show answers too long for the cap:
  - Run 67: Luna wrote 21,201 and then 17,251 characters of visible deliberation and no tool
    call. It could not apply a reviewer correction to relabel CMT27512, because labels come
    from the code-rendered sentiment table, and Cherry returned nothing to recompute.
  - Run 68: 2 of its 3 failed support attempts were format errors (`finding_missing`,
    `assertion_coverage`). One was a reasoning truncation.
  - The open item is the label-correction path: a correction to a code-rendered label that
    Original cannot carry out. It is not the cap.

## Prompt audit and planning fixes after runs 63-66, 2026-11-04

[AUDIT_PROMPTS_V7_VS_CURRENT.md](AUDIT_PROMPTS_V7_VS_CURRENT.md) compares every v7 prompt rule
with the current prompts. Runs 63-66: 63 complete/accept; 64 partial at the call limit (plan
added numbers and a chart to a sentiment question, Lime failed, `label_group_sources` rejected
five times); 65/66 asked the manager for data the specialists retrieve. Applied:
- planning: sentiment-only means no numbers, numeric-only means no text, a chart only when the
  user asks, never ask the manager for comments, topics, ratings or records;
- `label_group` without cited comments is normalized (event `label_group_normalized`), not rejected;
- a failed or declined chart blocks completion only when the question asks for a chart (event
  `optional_chart_dropped`);
- one-line general rules restored from v7: validation step as action, categories through their
  aggregate, no invented reasons for counts (Original); unavailable evidence satisfies the
  request and the action policy is not a completeness item (completeness); task_outcomes
  line, CHART_NOTE sent only with a chart (support). All seven were measured (M1, M2, M4)
  and reverted on branch `revert-p2-lines` (2026-11-08; `reports_gold/DEVIATIONS.md`).
- adopted separately as a product boundary, not priority 2: pay/promotion/discipline/
  termination use is a safety concern (support). Relabelled 2026-11-05.
The post-revert re-runs (38 blocks, 2026-11-08) are in
`reports_gold/RERUN_COMPARISON_20261107.md`: M1, on its six re-run cases, at or below the
16-case v8 baselines on wrong decisions and missed defects (test 2/1 vs 3/1; Gemini 0/1 vs
3/4), with one test B1 false-objection run
against v8's 0; M2 test 2 destructive in R1-R5 (one above v8's 1), M2 Gemini 1 (below v8's 2);
M4 C3 mishandled on both profiles (Gemini regressed from the consolidated without-arm). No
decision changes.
Gate: 295 tests pass, 4 skipped (2026-11-08, `revert-p2-lines`; 299 on `v8-followups`).

## Original and ZeroSugar consolidated, 2026-11-04

Branch `consolidate-agents`. Each agent now has one version: `agents/original.py` holds the former
OriginalAgentV8 merged into its base (v8 prompt, planning prompt, answer-edit-v2 delivery,
duplicate normalization, repair responses; v7 delivery, planning prompt and
challenge_corrections removed), and `agents/zero_sugar.py` holds the former ZeroSugarAgentV8
(review-v8; the v7 prompt, submit_review schema and 21 v7-only methods removed;
`equivalent_calls` moved in from the deleted `review_v7.py`). Deleted: `original_v8.py`,
`zero_sugar_v8.py`, `review_v7.py`, `run_agent_v8.py`, `measure_repair_delivery.py`. Agent code
went from about 4,350 to 2,380 lines. Gold runners keep only the current arm (labelled "v8" for
continuity with earlier results); the demo model lost its v7 review branches. Tests: eight
review-v7 contract files deleted, shared helpers moved to `tests/fixtures.py`,
`test_v8_agents.py` renamed `test_agent_contracts.py`, 50 scenarios scripted in the v7 protocol
archived (not run) in `old_protocol_tests/`, and six end-to-end guarantees rewritten in
`tests/test_workflow_scenarios.py`. Gate: 277 tests pass; offline demo complete/accept. Live
check pending.

## Live runs 55-62 (Original v8 + ZeroSugar v8), 2026-11-04

Same question and scope as runs 53/54, run by the user. Complete/accept: Luna 55 (11 calls,
98k input tokens, 197 s), Luna 56 (16, 163k, 327 s), Gemini 58 (11, 116k, 222 s); no duplicated
paragraphs, 13 rows, both excerpts. Luna 56 shows four team questions (two requested, one a
near-copy) and was accepted. Failed at planning: Gemini 57, Gemini 59, Luna 61 (two-attempt
limit spent on "None - ..." text instead of null clarification, a chart without numbers, and in
59 an unneeded clarification about the topic label). Partial: Gemini 60 (call limit; ZeroSugar
repeatedly claimed the code-rendered table showed CMT27506 as negative when it showed positive,
sending Original and Vanilla into repeated rechecks) and Luna 62 (plan added numbers and a chart
not requested; Lime failed decline_task three times and the chart blocked completion).
Implemented 2026-11-04 (shared planning code, both Original versions): a clarification that is
not a question and starts with None/null/N/A/"no clarification"/"no missing" is null
(`agents/findings.py`), and include_chart without numbers is normalized to false instead of
rejected (`agents/original.py`). Offline replay of the logged plans: 57 and 61 now plan
normally; 59 now ends in its (unneeded) clarification instead of a planning failure. Still
proposed: stop reviewer objections that contradict a code-rendered table (60); keep an
unrequested chart from blocking completion (62).

## Original v8 adopted, 2026-11-04

After the adjudicated gold M2 (`GOLD_V1_RECORD.md`), the user adopted Original v8 for the CLI
workflow: `run_agent.py` imports `OriginalAgentV8` as `OriginalAgent`, with ZeroSugar v8 as its
reviewer. M2 with the normalizing duplicate guard: the requested change in 18 of 20 repairs,
1 duplicate pair in 24, must-keep content lost in 3 of 24 (all R2: the critical excerpt removed
while adding the positive one), the false correction R6 disputed in 1 of 4. Full-workflow
resume now refuses (Original v8 cannot resume); legacy phase resume keeps v7. The offline demo
(`--demo`) delivers through v8's submit_answer. Next: live end-to-end run 55.

## Live run Gemini 54, 2026-11-04

Partial at the 32-call limit (596 s, 548k input tokens). Original v7 spent 13 calls on seven
delivery rejections (five removal-reason mismatches) and a Cherry detour, and again duplicated
paragraphs. v8 enforced the action policy but re-raised a CMT27511 label concern as a new issue
after judging the label defensible. [Details](AGENTS_V8_DESIGN.md#live-run-gemini-54-original-v7--zerosugar-v8-2026-11-04).

## Live run 53 (Original v7 + ZeroSugar v8), 2026-11-04

Luna 53 completed and was accepted: first complete workflow since run 30; 17 calls, 306 s,
181k input tokens (Luna 52: 270k), three drafts, no protocol failure. v8 enforced the action
policy live. The accepted answer still repeats its whole analysis, keeps a cut-off action and an
unsupported "one comment per respondent" claim; draft 2's dropped questions were not reported.
[Details](AGENTS_V8_DESIGN.md#first-live-end-to-end-run-with-zerosugar-v8-luna-53-2026-11-04).

## ZeroSugar v8 adopted, Original v7 kept, 2026-11-04

After the adjudicated gold M1 (one repeat; v8 halved false objections on both models, no
protocol failures, about 40% fewer input tokens; only Luna v8 within the scaled missed-defect
threshold), the user adopted ZeroSugar v8 as the reviewer for all profiles. Original v7 is
unchanged and now reviews through v8; the CLI's standalone review and the offline demo use v8.
Legacy phase resumption and the scripted v7 workflow tests stay on review-v7. 437 offline tests
passed. A live end-to-end workflow is pending. [Details](AGENTS_V8_DESIGN.md#9-adoption-of-zerosugar-v8-2026-11-04).

## v8 corrections after the fourth smokes, 2026-11-03

`manager_actions` did not separate actions from team questions, so v8 now requires
`proposal_types` (action/team_question/other per proposal); `category_claims` accepts several
labels; completeness is told excerpts are code-copied; supported assertions without citations
get their finding's citations. 435 offline tests passed; no live call by the assistant.
[Details](AGENTS_V8_DESIGN.md#corrections-after-the-fourth-lunagemini-smokes-2026-11-03).

## v8 explicit action/category/dispute judgments, 2026-11-03

After the Luna and Gemini smokes (no reviewer caught B15's missing manager action; v8 disputed
defensible labels), v8 support adds `manager_actions` (empty list = code-derived policy
correction), `category_claims` (code checks cited comments against stored labels) and
`stored_label_defensible` on disputes (true = dropped). Model judgment unchanged; producer-side
action typing not implemented. 432 offline tests passed; no live call by the assistant.
[Details](AGENTS_V8_DESIGN.md#explicit-action-category-and-dispute-judgments-2026-11-03).

## Second smoke and v8 normalizations, 2026-11-03

Second smoke: no v8 truncation, but two v8 support protocol failures on mechanical slips. At
the user's instruction v8 now normalizes out-of-finding citations, policy_requirement fields
and same-label disputes, and no longer asks the reviewer to assess the renderer's application
boundary text (approved invariant change). 428 offline tests passed; no live call by the
assistant. [Details](AGENTS_V8_DESIGN.md#second-smoke-and-delivery-normalizations-2026-11-03).

## Reviewer smoke and v8 fixes, 2026-11-03

The user ran the M1 smoke (B1/B2/B7/B15, v7 and v8, `apinex_test`, one repeat): 8 of 8 reviews
completed. It exposed two v8 code defects, now fixed offline: the absence guard dropped real
omissions (now only annotated), and every truncated v8 support attempt had stringified the keyed
findings object (now flat arrays). The first smoke's v8 results predate the fix. Not adjudicated
yet; 427 offline tests passed. See [section 8](AGENTS_V8_DESIGN.md#8-smoke-run-and-revision-2026-11-03).

## Pacing and M1 runner, 2026-11-03

At the user's request the three APInex profiles now use `request_interval_seconds=10` (was
20); earlier runs used 20 s, and the pacing test reads the configured value. New
`run_gold_review.py` runs the gold reviewer cases through ZeroSugar v7/v8 for the user to
execute; the assistant made no live call. Usage: [GOLD_V1_RECORD.md](GOLD_V1_RECORD.md).

## Human gold v1 frozen, 2026-11-03

The user filled and froze the casebook as [GOLD_CASEBOOK_v1.md](GOLD_CASEBOOK_v1.md) (one
annotator). `gold_cases.py` builds 16 reviewer cases (B1-B13 rendered by Echo's renderer; B9/B11
code-detected tampered copies; B14-B16 real) and 6 repair inputs; `score_gold.py` scores runs
(code: decisions, label disputes, R6 dispute, diffs; annotator: must-flag/false objections,
repair damage). 425 offline tests passed. No model run yet; the reviewer-only runner needs
authorization. See [the record](GOLD_V1_RECORD.md).

## Human gold casebook draft, 2026-11-01

[GOLD_CASEBOOK_DRAFT.md](GOLD_CASEBOOK_DRAFT.md) prepares the independent reference: human
labels for the 13 comments, reviewer cases B1-B16 (base candidate plus one controlled change,
and three real 51/52 candidates) and repair cases R1-R6, with scoring rules. All gold cells
are empty until a person fills and freezes them; no case has been run.

## Original v8 / ZeroSugar v8 in new files, 2026-11-01

At the user's request, new `agents/original_v8.py` and `agents/zero_sugar_v8.py` (plus
`run_agent_v8.py` and `tests/test_v8_agents.py`) subclass the v7 agents. Examples derive their
citation from the excerpt, removals are one list, obligations take one status with no link,
all delivery errors return together, retries carry only the latest attempt, classification
tables are reviewed through label disputes, refuted absences are dropped, and prompts are
shorter and question-neutral. v7 remains the default and is unchanged. 9 new tests and the
full suite (421) passed offline; no live call. Seven listed changes need approval before live
use: [design and limits](AGENTS_V8_DESIGN.md).

## Proposed corrections after the updated audit, 2026-11-01

The user requested a detailed Markdown plan, not implementation.
[CORRECTION_UPDATE_PLAN_2026-11-01.md](CORRECTION_UPDATE_PLAN_2026-11-01.md) specifies
delivery fixes, separate ZeroSugar/Original measurements, explicit-removal simplification,
bounded absence disputes, contracts, budgets and acceptance gates. It retains model-owned
lifecycle judgments and corrects the companion token-saving counterfactual. No runtime
change, local test, API call or Git publication was performed for this planning task.

## Reasoning versus system audit of runs 51/52, 2026-11-01

[The audit](AUDIT_RUNS_51_52_REASONING_VS_SYSTEM.md) finds both terminal stops were
administrative bookkeeping (removal/reason mismatch; serial correction-link validation),
not reasoning. It proposes P1 system fixes, P2 contract simplifications (one conflicts with
the existing "offer both encodings" decision) and P3 canonical-table protection, and advises
measuring reviewer false objections instead of adding wording rules. None is approved or
implemented; no test, live call or publication. Its Addendum A answers an external review:
the three-part split (model arguments, Python recovery, content judgments) replaces the
"administrative only" framing, deriving linked-correction state is withdrawn, and the
companion analysis's Z3/O1/Z6/Z7 items are corrected there; the companion analysis was then
revised to match (revision 1, adding O6 for measuring Original repairs).
[A companion analysis](IMPROVEMENT_ANALYSIS_SCORES_AND_TOKENS.md), revision 2, covers 42
workflow logs (all profiles): input per call doubled from 8.5k to 17.0k at the 2026-10-28
boundary (instructions/schemas), review rounds and failing loops multiply it, and truncation hit
8 of 17 later runs. It ranks proposals by recurring rejection families, keeps the keyed review
schema, marks O3 as largely A8, and notes `challenge_corrections` was never called live.
Revision 3 corrects token figures (Luna 52 attempt-2 saving 64,961, not about 94k; failing
loop 121,357) and withdraws O2's tool-result saving claim. Analysis only; nothing approved
or implemented.

## Live results for v7: Gemini 51 / Luna 52, 2026-10-31

The final local gate passed 412 tests (63.725 s). Exactly two fresh full workflows used
identical frozen source/data/scope/limits. Gemini 51: partial, 19/18 calls, 420.766 s,
two completed reviews, 16 released findings; Original stopped on seven removal/reason
mismatches. Luna 52: partial, 16/15 calls, 351.593 s, one completed review, 7 released /
2 withheld; a fourth support attempt fixed its duplicate link but exposed a conflicting
mandatory/addressed refinement state. All four candidates replay their 13-row canonical
map correctly. Three completed support reviews delivered seven structured explanations.
Neither fully accepted; false absence/scope objections and editing regressions remain.
[Evidence, attribution and limits](RUNS_51_52_ANALYSIS.md). No extra live call, post-pair
runtime fix or Git publication. The nine-case instrument has no provider accuracy result.


## Authorized v7 update and live pair, 2026-10-31

The user authorized the corrected plan, local checks and exactly one fresh Gemini and
one fresh Luna workflow. [The v7 implementation](UPDATE_2026-10-31_V7.md) adds canonical
classification fidelity, consistent quote options, a single shared protocol exception,
structured rating explanations with bounded reviewer-only repair, phase/candidate-aware
reporting and measured request accounting. New contracts are review-v7/source-facts-v7;
v1-v6 replay and strict checkpoint identity remain. Nine controlled review cases and an
annotation scorer are available; their provider accuracy remains unmeasured. Verification
and live outcomes are recorded in that document after execution. No Git publication.


## Addendum E comparison, 2026-10-31

[The comparison](ADDENDUM_E_COMPARISON.md) preserves the audit and preceding analysis.
It confirms protocol/recovery stops but corrects E.6's identity attribution: candidate two
had F9 for the positive-pattern issue and F10 for the negative/busy-period issue; both IDs
were offered, so the duplicate mapping was not forced. Raw, diagnostic and final rating
counts also differ (recorded diagnostic 7/7/not reached; exported verdicts six one-character
fields). First-call selection and similarity-based release action remain proposed policy
changes, not proven harmless normalizations. E.11 excludes semantic grading and does not
disprove the separately observed reviewer contradictions or handoff/schema defects.
No runtime change, test, live request or publication was performed for this comparison.

## Analysis of runs 49/50, 2026-10-31

[Reasoning/system diagnosis](RUNS_49_50_ANALYSIS.md) contrasts the saved provider
responses with actual candidates and retained classifications. It identifies reviewer
contradictions, a two-comment label swap in Gemini's unverified third candidate, the
six-example versus thirteen-label handoff gap, a proposals quote schema/renderer mismatch,
nonlocalized duplicate-correction feedback, early loss of raw finding reviews for repair,
and misleading failure text. Multiple distinct Luna calls are observed upstream; model
versus gateway origin is unresolved. Safeguard rejection is separate from recovery defects.
Recommendations are not implemented or approved by this analysis. No new API call or test.

## Latest live pair: Gemini 49 and Luna 50, 2026-10-31

The user subsequently authorized exactly one fresh full workflow per profile. Both used
unchanged a14973b source, the same M14/Q3 Recognition question, data identity and budgets.
Gemini 49: 20/20 calls, 475.500 s, partial/revise with 10 findings released from the second
reviewed candidate; third-candidate completeness accepted but support failed three times
on correction_duplicate. Luna 50: 13/13 calls, 342.046 s, failed/invalid_review, no completed
review or released finding. Every completeness response contained two distinct tool calls
despite parallel_tool_calls=false. No connection failure, code change or acceptance-hunting
repeat occurred. Gemini's six non-completeness rating explanations remain one character;
its repair inputs reported 22,252-26,595 tokens, above 15,000. Neither run triggered A27
or a low-score global safety veto. [Evidence and limits](DELIVERY_RELIABILITY_UPDATE.md#live-pair-gemini-49-and-luna-50-2026-10-31).
[Addendum E](AUDIT_2026-10-31.md#addendum-e---runs-49-50-the-duplicate-refinement-rejection-and-the-completeness-call-guard)
verifies both runs and files observations 49-61 with proposed A32-A38; none is approved.

## Authorized review/delivery update, 2026-10-31

The user authorized the revised audit plan, local verification and Git publication,
with no live calls. New reviews use review-v6 with an explicit issue-linked safety veto;
one-character rating explanations remain diagnostic and cannot independently erase
supported findings. New answers use source-facts-v6, preserving v1-v5 replay. Delivery
now localizes quote/source errors, distinguishes changed from identical invalid submissions,
provides one mechanical quote-only fallback per role/workflow, and records explicit block
removal reasons. Both reviews, five roles, scope/privacy, provider settings and budgets remain.
Support/publication counts and explicit obligation identities are separated. The final local
gate passed 392 tests in 67.359 seconds, including 21 new cases. See
[implementation, verification and limits](UPDATE_2026-10-31.md). No fresh model behavior
is validated; old workflows still require matching implementation identity. A four-draft
offline saved-candidate measurement is available; the 15,000-token target remains unverified.

## Latest Gemini repeat: run 48, 2026-10-30

With unchanged code, question, scope and budgets, Gemini 48 made 11 successful calls
and completed one review round (both phases revise), then failed during repair after
three excerpt-source validation rejections. It finished in 217.859 s, released no findings,
and had no connection failure. The support review judged 11 of 13 findings supported on
every assertion; the safety score of 2, whose rationale is one character and which names no
issue, withheld all of them. [Evidence and limits](DELIVERY_RELIABILITY_UPDATE.md#gemini-48-repeat-2026-10-30).
No code change or new local test execution occurred for this repeat.
[AUDIT_2026-10-31.md](AUDIT_2026-10-31.md) reads runs 46-48 draft by draft and proposes
A23-A31; none is approved.


## Completed system update and live pair, 2026-10-30

The authorized system changes and evaluation are delivered; this supersedes the partial
implementation notes below. The 371-test gate passed. Network-enabled Gemini 46 failed
before independent review after three excerpt/source delivery rejections (9 calls, 8
successful). Luna 47 completed four review rounds and stopped partial/revise at the draft
cap (24 calls, 23 successful): 5 supported/released, 2 withheld, 18 pending entries / 15
unique issue texts. Connection failures and retries are preserved separately. Both live
manifests match the current source. No challenge call occurred; human semantic confirmation
is still pending. See [delivery evidence](DELIVERY_RELIABILITY_UPDATE.md#live-completion-gemini-46-and-luna-47-2026-10-30).


## Implemented system delivery update, 2026-10-30

This entry supersedes the partial implementation notes retained below.

The user authorized implementation, local tests and one fresh workflow per Gemini/Luna,
including connection retries. The system changes now retain rejected assertion assessments
and candidate/finding origin, bind a uniquely matched saved narrative block, and expose
whether that original block remains saved during repair. Matching compares source sets;
old finding numbers never select a new block. Ambiguous matches remain unbound.

Partial-result limitations derived from assertion corrections distinguish earlier-draft
obligations and explain their source-linked reasons instead of presenting an old F-number
as a current passage. Missing-verdict failures say that no conclusions were reviewed.
Artifacts include reviewed/released counts, per-draft duplication diagnostics and repair
request section sizes. Paragraph similarity is observational and never changes a verdict.

New source-facts-v5 rendering avoids appending an exact selected quotation already present
as a quoted span. v1-v4 rendering remains available unchanged. The public answer schema and
manager UI text fields are unchanged; no UI redesign, new prompts, judgment rules or budget
changes were introduced. Explicit challenge tests exercise accepted and still-revise
scripted dispositions and the one-challenge bound; real model use remains observational.

The final local release gate passed 371 tests in 58.610 seconds. An earlier run found one
fixture that expected new answers to keep the v4 version label; it was updated while a new
test checks exact v4 versus v5 quotation replay. Evidence: ignored
`reports/release_gate_20261030_final.txt`. `reports/delivery_pre_live_20261030.json` compares
three saved repair requests from each of 44/45 before and after restoring missing
assessments, with all other saved fields held fixed. This is a saved-request projection,
not an exact forecast of new live requests or a provider token measurement. New request
sizes are recorded separately. The 15k target is retained as historical observation.

Live results are recorded after completion in the dated delivery record. Semantic cases
are diagnostic references awaiting human confirmation, not evidence of model accuracy.


## Proposed follow-up plan, 2026-10-30

Implementation started: assertion-derived corrections now retain the originating candidate,
finding and rejected assertion assessments. The existing 365-test release gate passed in
35.368 seconds on this partial change. U2-U6 and the scripted packet-size comparison are
not complete; no new live evaluation has been performed. Do not treat the plan as delivered.
Additional work started U2: current assertion corrections receive a saved block ID only
when narrative text and citations identify exactly one block; earlier corrections are not
remapped by finding number. The full 365-test gate passed in 101.061 seconds after this
change, but targeted replacement/reordering verification and the remaining plan are pending.

[UPDATE_PLAN_2026-10-30.md](UPDATE_PLAN_2026-10-30.md) records the requested plan after
contrasting runs 44/45 with Addendum C. It proposes complete assertion-repair feedback,
correction/content identity, current versus historical limitation handling, bounded
presentation fixes, and separate reviewer/A8 evaluation. This is a proposal, not approval
or implementation; no tests, live calls or publication were performed for the plan.
It refines the audit's readings of Luna F4/F6 (false reviewer descriptions) and F5/F12
(old corrections name different content than the final supported blocks). The current
reassessment path and all existing scope, review and budget controls remain unchanged.
The G1-G6 plan revision limits implementation to system mechanisms and reporting: U3
owns per-draft >=0.9 duplication observations, U1 reports complete packet sizes without
a new size rejection, U6 retires 15k tokens as a pass/fail target within the proposed
plan, and U5 is diagnostic. No prompts or semantic judgment rules change. The existing
challenge path was not called in 44/45; Luna's falsely withheld F6 quote survived in
published F8. These are planning clarifications, not implemented or live-verified changes.

## A20-A22 and latest live pair, 2026-10-29

The follow-up changes passed the 365-test local release gate. Gemini 44 and Luna 45
completed four candidate reviews each but both ended `partial/revise`; neither accepted
the answer. Gemini recovered two support-review output-limit events using the compact
retry. Both runs logged the draft-limit stop at draft 4 without starting another draft.
A20's simultaneous-error case and A21's wrong correction-ID namespace were not triggered
live and remain supported by offline regression tests. Luna's final answer still had
misattribution, citation/content mismatches, duplication and no per-comment table; the
classification itself exists as prose over all 13 comments and the denominator is stated,
so that demand is a format suggestion beyond the question. This pair does not establish
sentiment accuracy or a deterministic calculation defect.
Gemini 43's restricted-environment attempt had zero successful calls and is distinct from
Gemini 44. Reports and limits are in
[delivery history](DELIVERY_RELIABILITY_UPDATE.md#fresh-live-runs-gemini-44-and-luna-45-2026-10-29)
and [live-test history](LIVE_TEST_HISTORY.md#corrections-delivery-follow-up-gemini-44-and-luna-45-2026-10-29).

[AUDIT_2026-10-30.md](AUDIT_2026-10-30.md) reads the same pair draft by draft and corrects
the 29 record: the run 41 support rejection was at 439.078 s, not 452.078; 20 of 32 calls
were used and 12 were unused; drafts 1 and 4 carried the literal excerpts and drafts 2-3 did
not. It adds observations 19-31, including the unguarded rendered excerpt, limitations that
name internal finding IDs, two findings published while the same review calls them
unsupported, the generic failure text of run 43 and the 15-pending/12-distinct count. A8's
15,000-token target remains unmeasured; the scripted four-draft run is where it must be
measured.

[AUDIT_2026-10-31.md](AUDIT_2026-10-31.md) continues it for runs 46-48 with observations
32-48. The main additions: the excerpt rejection names no item or allowed set, an item citing
only `SENTIMENT1` can never pass it, the stall rule counts three different submissions as
repetitions, and a safety score of 2 with a one-character rationale withheld 11 supported
findings in run 48. In run 47 the repair deleted content that earlier rounds had reviewed and
duplicate citation IDs cost three turns. It also records that run 47's limitations no longer
name internal finding IDs. A23-A31 are proposed and unapproved.

## Repair feedback and live results, 2026-10-29

A19, A8, A18 and A17 are implemented in the grounded Original repair loop and ZeroSugar
review delivery. Original gets one compact retry after output truncation only during a
repair, charged to the shared call budget; a second truncation still fails. Repair
context no longer repeats the full review verdict, pending corrections or evidence.
When a linked correction has an inconsistent lifecycle state, feedback names its exact
ID and current flags and offers both valid encodings without choosing the model's
meaning. Independently found structural errors are included together in sanitized
feedback. These changes preserve the five roles, review judgments, and existing limits.

The full local gate passed 362 tests in 34.707 seconds; `git diff --check` passed. Fresh
Luna 41 was partial after four candidate reviews: its final support review still asked
for changes (12 findings, 9 supported and 3 withheld). It exercised A18/A17 live: three
conflicting correction states were identified together and the next submission completed
the review, but did not accept the answer. Its first repair call reported 21,011 input
tokens versus 36,956 in Luna 40; candidates differed, so this is an observed reduction,
not an isolated causal estimate. Fresh Gemini 42 failed after three support attempts:
it repeated a duplicate citation in F4 on the first two. The correction citations were
already invalid in attempt 1 but were reported only on attempt 3, after the F4 issue was
corrected. No answer findings were released. Neither run truncated output;
A19 has offline regression coverage but remains unexercised live. Neither run establishes
semantic accuracy or full acceptance. Artifacts and limits are in
[DELIVERY_RELIABILITY_UPDATE.md](DELIVERY_RELIABILITY_UPDATE.md#repair-feedback-and-fresh-runs-41-42-2026-10-29).
The detailed Gemini42 trace records the callers, payloads, citations, validation feedback and
final stop: [GEMINI42_EVENT_TRACE.md](GEMINI42_EVENT_TRACE.md).

Addendum A of [AUDIT_2026-10-29.md](AUDIT_2026-10-29.md#addendum-a---runs-41-and-42-appended-2026-10-29)
audits the same two runs and adds findings P1-13 (the corrections block is validated after
the findings, so a defect present in attempt 1 was first reported in attempt 3), P1-14 (the
corrections citation field names no ID space and its rejection names no values) and P2-13
(the draft-limit stop logs a repair that cannot run), with actionables A20-A22. It also
corrects one reading of Gemini 42: the correction citations were finding IDs in all three
attempts, not introduced after the F4 fix. A fourth decision is open there: what a protocol
stop releases, since run 40 released 12 findings after failing and run 42 released none.

## Authorized delivery repair, 2026-10-28

The user approved executing A16/A11/A12/A14 and corrected A1/A2, including local
checks, GitHub publication and controlled live evaluation. The exact pre-change source,
private evidence and database are preserved under ignored
`reports/baselines/pre_delivery_20261028/`; old workflows require that exact version.
Checkpoint identity checks remain strict; no automatic migration or grouped review.

The initial 329-test suite reproduced 34 failures and 57 errors. Current-contract
fixtures and lazy checkpoint-only database hashing restore the baseline; the release
gate passed 333 checks before A1/A2. Delivery now reports resolved capacity and editable
block IDs; same-call removals/reuse are considered before enforcing the final limit.
Three consecutive identical structured-delivery rejections stop safely, releasing only
findings from the last completed review when available. The full release gate passed 343 offline checks (117.279 seconds), including nine
delivery regressions. Live results are recorded in
[the implementation record](DELIVERY_RELIABILITY_UPDATE.md).
A3-A5/A9-A10/A13 remain deferred; source rendering, review judgment and provider budgets are
unchanged.
The user completed the provider check-in after initial run 37 failed with HTTP 402.
The same-code continuation 37_resume_1 was partial (10/11 successful calls, 260.343 s,
1 completed review; 9 supported / 6 withheld findings). Luna 38 failed (11/12 calls,
265.609 s, no completed review). Both stopped at the unchanged 6000-token support
review output limit. Neither recorded narrative_count or answer_delivery_stalled;
A1/A2 are established by offline replay/tests, not directly exercised by these two live
runs. Complete acceptance and A15's repeated-run criterion remain unfulfilled.
No extra scope, profile/budget change or grouped review was applied.
A6/A7 were then implemented offline on the user's instruction: the review free-text
fields carry declared `maxLength`/`maxItems` bounds enforced for every newly generated
report, including legacy-shaped responses. Finding reasons are checked before retention
so an overlong entry stays editable on retry; historical report reads keep their old
limits. Rating rationales and uncertainty explicitly require non-whitespace text.
`finding_reviews` sent as text is rejected with `finding_reviews_type`, and a
truncated review retries a shorter delivery inside the same three attempts instead of
aborting the phase. Sentiment, citation and claim judgment are unchanged, no finding,
source or assertion was reduced. The declared maxima are a
ceiling, not a guarantee, so the compact truncation retry is the recovery path. The suite
passed 353 offline checks initially and 356 after the three review follow-up corrections.
Fresh Gemini 39 and Luna 40 were both partial. Four candidate reviews completed without
ZeroSugar truncation, but Gemini's repair generation exhausted its cap and Luna's fourth
support review failed on contradictory correction refinement. No full answer acceptance
or semantic accuracy is established; the compact truncation retry was not exercised.
See `DELIVERY_RELIABILITY_UPDATE.md` for artifacts and remaining limits.

## Engineering audit and suite state, 2026-10-28

An audit requested by the user is saved as [AUDIT_2026-10-28.md](AUDIT_2026-10-28.md).
It now includes a line-level read of `agents/zero_sugar.py` and `agents/original.py`.
Its revision 2 was written after an external review of revision 1 and changes four
actionables against code: obligations are not keyed on finding IDs (they are positional
per draft) or similar text, assertion counts are not fixed by decree, both delegation
widening sites are covered (`original.py:708,781`), and the two `capture.py` crashes are
test doubles plus one eager `database_identity` call, not two production defects. It adds
a checkpoint-compatibility pre-condition (A16): `source_versions()` hashes every agent
module, so any A1-A9 edit makes saved workflows non-resumable (`resume.py:198-199`), and
it records that cross-call review batching needs C2 re-approval.
Revision 3 applies a second pass: answer capacity is enforced on the resolved list because
a static `12 - retained` schema cap blocks a valid remove-one/add-one replacement;
obligation identity includes the objection family and a separate anchor for omissions;
budget work removes duplicated instructions instead of assessments; delegation follows the
capability a correction needs, not its owner. It also corrects the record: run 36 logged
seven `narrative_count` rejections (21, 25, 24, 23, 23, 23, 23; turns 1-7), the feedback
does carry expected/actual counts, and the `1->4->2->9->11` figure mixed completeness and
support counts (support 4->9->11; completeness 1->2->0->4). Run 36 support counts were
6->2->5, so obligation growth is observed once, not generally; and the model resubmitting
23 items after being told 12 is recorded as a contributing factor, not excused.
Measured, not inherited: the current working tree
runs 329 offline tests with 34 failures and 57 errors (91 red); committed HEAD `2475fcd`
already had 13 errors (`database_identity('unused')`), so the documented 2026-10-27
"322 checks passed" does not reproduce here. Run 30 on the previous code was complete;
runs 35 and 36 on current code failed and were partial. The audit separates backend
actionables from UI items; no UI change is planned. No runtime change was made and no
model call was performed for it.

Runs 37 (Gemini, resumed after the provider check-in) and 38 (Luna) exercised the
implemented A1/A2/A11/A12/A16 code: partial and failed respectively, both at
`output_token_limit` in the support review on attempt 1 of 3. Neither recorded a
`narrative_count` rejection nor an `answer_delivery_stalled` stop, so the delivery repair
is implemented and unexercised live; run 37 released 9 supported findings from its
completed draft-1 review and withheld 6. The binding blocker is now the review output
budget (A7 then A6). The reasoning counter is separate from output: run 37 completed a
review reporting 3,471 output and 3,451 reasoning, so the earlier "99% hidden reasoning"
claim is withdrawn, and four review-schema fields (`rationale`, finding `reason`,
`suggestions`, `uncertainty`) are unbounded. Measured state for runs 15-38 is 6/24
complete.

## Runs 33/34: shared schema alias failure, 2026-10-28

The user executed Luna run 33 and Gemini run 34. Both completed planning, then failed
with Python KeyError('quote') before Original's first coordination request and before
Vanilla ran. Luna first recovered a connection error using the new identical-request
transport retry; that was not its terminal failure. Neither run evaluates analytical
quality or completed review.

Cause: answer_schema shares one narrative template between interpretations/proposals;
deepcopy preserves that alias. live_answer_schema removed quote twice from the same
object. The fix detaches each branch before adaptation and leaves the canonical replay
schema unchanged. Original now records unexpected workflow exceptions privately and
marks its workflow checkpoint failed. The fix received static inspection only; no local
tests or additional API calls were run. Original 33/34 artifacts remain unchanged.

## Shared C1 reliability implementation, 2026-10-28

The user approved applying strengthened C1 and seven shared reliability changes to the
main application, without C2/C4, tests, builds or API calls. Implemented: bounded
identical-request transport retries; source-excerpt references extracted by Python;
reference-based specialist blocks and explicit draft edits; retained unverified draft
text references; code-managed correction references with explicit refinement history;
a bounded Original-to-ZeroSugar correction challenge; and new whole-workflow checkpoints
that continue the pending coordinator/specialist/review work through final release.
The five roles, both review responsibilities, privacy/scope/source integrity, sentiment
rubric, canonical source-facts-v4 replay and provider profiles remain. Legacy phase-only
points remain diagnostic; they do not contain the new coordinator state.

See [C1_RELIABILITY_UPDATE.md](C1_RELIABILITY_UPDATE.md) for exact delivery, continuation
and budget rules. Static inspection only: no functional validation, accepted-output
claim, publication or new model experiment. The frozen experiment copies and their
historical artifacts were not modified.

## Publication follow-up, 2026-10-27

The user subsequently authorized committing and publishing the current local code,
tests and documentation to GitHub. Earlier no-publication statements describe their
implementation stage. This follow-up changes no runtime behavior and runs no tests,
builds or model calls; review-v5 and capture/resumption remain unvalidated by execution.
Private credentials, reports, logs, checkpoints and local databases remain excluded.

## Corrected B, full capture and phase-only resumption after runs 27-29, 2026-10-27

Runs 27/28/29 all failed without completed support review: Luna 11 calls/226.735 s,
DeepSeek 25/558.000 s and Gemini 11/240.875 s. All classified 13 comments; hashes and
aggregation matched retained labels. Ten of twelve support submissions failed v4's
literal reconstruction requirement; two omitted findings. DeepSeek also failed exact
question-excerpt checks. Gemini completeness accepted actions in place of requested
questions; its candidate still overgeneralized mixed comments and proposed contacting
anonymous respondents. DeepSeek's last prose listed nine positive IDs while reporting
eight. These are format/semantic failures, not connection failures or validated accuracy.

User-approved correction now uses review-v5. Claim descriptions are concise assessments,
not literal reconstruction. Original is instructed to separate reviewable factual
assertions/premises; existing code assigns finding IDs, then IDs such as F2:A1 to review
assessments. Source subsets, explicit judgments, whole-finding withholding/repair, v3
correction judgments, both reviews, five roles and source-facts-v4 replay remain.

Full private exchanges and phase checkpoints are captured under reports/logs/details/,
with credentials omitted. Result artifacts link capture files. `--resume` accepts a new
failed artifact/checkpoint and runs that phase only; review retries never call Original
or Vanilla. Matching completed completeness can be reused; scope/source/profile/transport
changes are rejected or invalidate the affected subphase. New outputs preserve lineage
and bounded per-attempt budgets. Phase retries do not claim a complete Original answer.
Older files without checkpoints cannot automatically resume or recover missing arguments.

The user explicitly requested no local tests, builds or model calls during implementation.
Only static parsing/diff/reference review was performed; fixtures/new regressions are
unrun. Review-v4's earlier 322 checks do not validate this update. Next full runs are
30 Luna, 31 DeepSeek and 32 Gemini, to be executed by the user. See
[capture/resumption](RESUME_AND_CAPTURE.md), [commands](TESTING_AND_RAG.md#next-three-model-runs-30-32-2026-10-27)
and [history](LIVE_TEST_HISTORY.md). No GitHub publication.

## Assertion-level support review after runs twenty-five/twenty-six, 2026-10-27

Implemented user-selected option B: review-v4 assesses individual assertions inside
each finding, retaining a literal visible-text excerpt, factual/proposal kind, source
subset, explicit support judgment and reason. Ordered textual coverage and references
are checked in code; a failed assertion withholds its whole finding and creates an
Original repair despite any accepting verdict. Semantic decomposition and support remain
model judgments. V3 correction judgments, both phases, five roles, historical artifacts,
source-facts replay, provider settings and budgets remain. The technical UI shows these
assessments; manager projections are unchanged.

All 322 offline checks (including nine new regressions) and the frontend build passed.
No new provider call or GitHub publication. Live semantic improvement and suitability
for APInex's unchanged 6000-token output limit remain unverified. See the
[contract](WORKFLOW_RELIABILITY.md#assertion-level-support-review-review-v4-2026-10-27),
[validation](TESTING_AND_RAG.md#assertion-level-support-review-2026-10-27) and
[run 15-26 history](LIVE_TEST_HISTORY.md). All those saved runs predate review-v4.

Read-only inspection found run 24 partial (22 successful Luna calls, 499.937 seconds,
three drafts), run 25 failed (21 successful DeepSeek calls / 22 attempts, 460.954 seconds,
12/13 classification validated, no complete review), and run 26 complete (14 Gemini
calls, 306.156 seconds, two drafts, both final phases complete). Run 26's hashes, label
coverage, literal visible excerpts and aggregation match the database; accepted prose
nevertheless attributes inconsistent access/workload to both mixed comments when only
CMT27508 describes it. CMT27511 states frustration despite useful support. Run 24 also
calls CMT27512 positive in prose despite its stored mixed label. Acceptance is not
semantic validation. See the history for post-run changes and comparison limits.

## Additional APInex model options, 2026-10-27

Added user-requested `apinex_deepseek_test` / `free/deepseek-v4.1-flash` and
`apinex_gemini_test` / `free/gemini-3.8-flash` in connections.json. Both reuse the
APInex endpoint, APINEX_API_KEY and Luna's limits/pacing/retries. The existing Luna
profile, default and role assignments are preserved. Only configuration/offline
verification was performed; no new API call or live tool/quality validation.

## Reasoned actions and review simplification after run twenty-three, 2026-10-27

Run twenty-three was partial after four drafts, 26 successful calls and 562.578 seconds.
All drafts included the requested two questions; actions appeared in draft two but were
lost in subsequent revisions. Source/hash/coverage checks and aggregation reproduced:
13 comments, nine positive, two negative and two mixed; CMT27512 changed from mixed in
run twenty-two to positive on unchanged text. Reviews mixed false omissions/duplicate
repairs with a real unsupported attribution to CMT27511. Provider-reported usage was
323,368 tokens (294,516 input; 28,852 output), not a billing reconciliation.

The user approved at least one reasoned manager action in a complete Original analysis.
The proposal may introduce an idea outside the question and sources; its factual basis
and rationale must follow the analysis, while assumptions/possible benefits remain
proposals. Original preserves requested work and the action through repairs. Simplified
review instructions distinguish factual support, synthesis and action reasoning.
Completeness still checks the user's visible request only. Original activates a trusted
require_actionable flag for support; a missing action can be returned as policy_requirement
with Original ownership and request_excerpt=null. This avoids fabricating a user request.
The contextual kind is absent for other callers by default. Semantic presence/quality
remains model judgment; code does not infer it from punctuation or proposal-list length.
Both reviews, review-v3 lifecycle, objective gates, rubric and budgets remain. See the
[workflow](WORKFLOW_RELIABILITY.md#reasoned-actions-and-review-simplification-after-run-twenty-three-2026-10-27)
and [validation](TESTING_AND_RAG.md#reasoned-actions-and-review-simplification-after-run-twenty-three-2026-10-27).

## Requested content and additional actions after run twenty-two, 2026-10-27

Run twenty-two completed in 201.672 seconds with ten successful calls and one draft.
Read-only checks confirmed all 13 eligible source texts/hashes and label coverage,
recomputed aggregates and verified visible literal excerpts. Completeness raised three
unjustified objections; review-v3 support withdrew them without schema retries.
However, support treated the requested two team
questions as optional wording while accepting two action recommendations instead.
Classification remains provisional; CMT27512 changed from positive in runs seventeen
through nineteen to mixed in runs twenty through twenty-two on unchanged source text.

The user approved preserving useful actions as additions to the requested answer.
Original and both ZeroSugar instruction sets now distinguish requested content/item
counts from supplementary actions, using semantic judgment rather than punctuation or
fixed layouts. Actions should explain how cited findings motivate addressing a problem
or sustaining a strength; expected benefits remain proposals. No review stage, schema,
rubric, provider setting, budget or release gate changed. Run twenty-two is preserved
as pre-change evidence. See the [workflow](WORKFLOW_RELIABILITY.md#requested-content-and-additional-actions-after-run-twenty-two-2026-10-27)
and [validation record](TESTING_AND_RAG.md#requested-content-and-additional-actions-after-run-twenty-two-2026-10-27).

## Explicit correction judgments after run twenty-one, 2026-10-27

Run twenty-one was partial after 26 successful calls and four drafts. No duplicate review
calls occurred; all completeness phases completed on their first attempt. Two support
phases failed on correction coverage/replacement references; two completed. Obligations
grew 3/6/9/12, and the final review kept optional or contradicted objections pending.
The source table remained 13 comments: 8 positive, 2 negative and 3 mixed. This established
the need for the user-approved correction-contract update, not a new agent.

Implemented review-v3: code supplies every correction_judgments key; the model returns
mandatory/addressed booleans plus a reason. Code derives canonical states and routing;
models no longer manage replacement IDs or consolidation graphs on this path. Real
required/unaddressed omissions remain pending, while explicit not-required judgments
withdraw unjustified objections. Current objections judged already visibly addressed
are withdrawn; inherited ones are resolved. No prose/keyword rule infers these judgments.
Full repair text is sent once in review_obligations; previous_corrections contains IDs
only, and the completeness summary omits its repeated correction/issue lists. All
obligations and source evidence remain present. Legacy v2 submissions retain their
validators and conservative guard and are labeled v2; saved artifacts are not rewritten.

147 focused checks across review contracts, recovery, diagnostics, workflow and adapters
passed. After retained failed prototype checks, a support-only recheck reused run
twenty-one's completed completeness review for the identical candidate/source identity.
It assessed all 16 obligations using mandatory/addressed in one live call without
rejections: six withdrawals, ten retained inherited obligations and one new correction
(eleven active repairs), no deterministic issues, and a revise verdict. Output was 3515
tokens within the unchanged 6000 limit. The model still invented a denominator-sentence
requirement and retained redundant work; this confirms contract execution, not semantic
quality or full workflow improvement. Evidence:
reports/review_v3_check_21_20261027_support_only.json and
20261027_144043_c31c613c57d1.jsonl. Live checks and their limits are recorded in
[the testing guide](TESTING_AND_RAG.md#explicit-correction-judgments-after-run-twenty-one-2026-10-27).
Both reviews, all five roles, source-facts replay, source/privacy/arithmetic gates,
sentiment guidance/context, provider configuration and budgets remain. The UI still
consumes canonical review fields and exposes no new manager workflow. No full Original
rerun, broad suite, UI build, commit or GitHub push.

## Run twenty and single-call transport, 2026-10-27

Run twenty failed after 11 successful calls: completeness rejected its first rationale
and then received two submit_completeness_review calls on each of two retries. No
support review completed. The original diagnostic did not retain rationale type/length,
so its exact failed condition cannot be recovered. Runs seventeen through nineteen
had no duplicate completeness calls. The missing single-call transport setting already
existed; these observations do not establish that forwarding strict caused duplication.

ChatModel now sends parallel_tool_calls=false when exactly one tool is offered and
required. Other tool modes retain their previous behavior; multiple-call responses are
still rejected by the review gates. Invalid completeness rationales now report type,
character count (strings only) and the 1200-character bound without retaining content.
Thirty-six focused provider/field-diagnostic checks passed. A live recheck of only the
saved run-twenty completeness phase completed on the first call, with both strict=true
and parallel_tool_calls=false captured at the SDK boundary and one returned tool call.
Its valid verdict was revise, score 2; this is phase/transport evidence, not approval of
the complete answer or validation of the semantic objections. Local metadata:
reports/completeness_transport_check_20_20261027.json; log
20261027_063645_1ecd888e5f0a.jsonl. The original run remains unchanged.

No full workflow rerun, broader suite, commit or GitHub push. Correction-protocol
alternative B remains deferred; both reviews, source/privacy gates and budgets remain.

## Strict Chat transport follow-up, 2026-10-27

Run nineteen remained partial after four drafts; contextual numeric fields were omitted
correctly, but support submissions still failed and correction obligations grew from
five to eleven. Two independent review phases already existed. Do not describe missing
phase separation as the cause or treat schema conformity as semantic correctness.

Implemented alternative A: ChatModel now preserves an explicitly supplied strict value
when converting tools to Chat Completions, including false, without adding an absent
flag or mutating the original tools. Thirteen object-schema declarations were checked
for closed properties and complete required fields; no schema changes were needed.
Three focused adapter checks passed. APInex free/gpt-6-luna accepted two live strict
requests without employee data: the existing connection probe and a synthetic packet
using ZeroSugar's nested support schema. The latter matched its fixture and schema.
Local evidence: reports/strict_transport_probe_20261027.json and logs
20261027_061516_7cc233292e46.jsonl / 20261027_061641_f1a8f52f745b.jsonl.
An initial sandbox connection attempt failed before the successful network-enabled probe.

This verifies transport and observed schema conformity, not constrained-decoding
enforcement, semantic quality or improvement on the complete Recognition workflow.
Other Chat providers were not called. Alternative B (simplifying correction judgments
and state administration) remains deferred; both review phases, current correction
retention/withdrawal rules, source/privacy gates, prompts and budgets are unchanged.
No full-suite run, complete analytic rerun, commit or GitHub push. See
[strict transport checks](TESTING_AND_RAG.md#strict-chat-transport-follow-up-2026-10-27).

## Run eighteen and contextual review fields, 2026-10-26

Observed `apinex_prueba_vanilla_18.json` / `20261027_004732_89cb24d6210d.jsonl`
(UTC log name; local date October 26): complete, 27 successful calls, 530.453 seconds,
four drafts. ZeroSugar used 15 calls; nine support submissions failed across the first
three candidates. Final acceptance required both phases on draft four. V3 rubric/full
13-comment context were active; read-only source/label/aggregate checks matched run
seventeen. Final prose gave limited pattern synthesis. This is recovery evidence, not
a demonstrated quality improvement.

Implemented the user-approved follow-up locally: per-candidate support schema omits
numeric_reviews and correction_reviews when their trusted task lists are empty. Echo
fills only these inactive lists with []; any supplied inactive entries are ignored with
metadata-only diagnostics. Active obligations/numeric requests still require complete
valid assessments. Feedback uses the actual contextual schema, rebuilt per candidate;
all semantic judgments, gates, roles, v3 rubric, full source context and budgets remain.
Existing diagnostic fixtures and focused contextual-field checks were aligned without
execution. No tests, API calls, commit or GitHub push. See the
[contract](WORKFLOW_RELIABILITY.md#contextual-support-review-fields-after-run-eighteen-2026-10-26).

## General semantic guidance after run seventeen, 2026-10-26

Run seventeen (`apinex_prueba_vanilla_17.json`, log `20261026_231553_53fb1a92e8d9.jsonl`)
completed with nine successful calls, 171.109 seconds, one candidate and both reviews
accepted. Support received all 13 full response/label pairs using rubric v2. Read-only
source checks confirmed coverage, hashes, literal structured excerpts and arithmetic.
The user considers CMT27512's positive interpretation defensible and rejected further
case-specific label rules. Citation attribution and three questions instead of two remain
observed output limitations; this run is not a classifier-quality benchmark.

Implemented the approved simplification locally: new shared rubric v3 gives general
category definitions and leaves contextual interpretation to the model. Removed
case-specific live classification/review instructions. Stored v1/v2 definitions remain
for historical review; no artifacts were rewritten. Full comment context, correction
request grounding, both reviews, four drafts, diagnostics and all data/privacy/budget
controls remain. Existing review fixtures and sentiment-version/source assertions were
aligned without execution. No tests, model calls, commit or GitHub push. Current live
quality remains unverified. See the [current guidance](WORKFLOW_RELIABILITY.md#general-semantic-guidance-after-run-seventeen-2026-10-26).

## Run sixteen and local semantic-review update, 2026-10-26

Observed `apinex_prueba_vanilla_16.json` / `20261026_205443_d0fc0454b26f.jsonl`:
complete after 15 successful calls (Original/Vanilla/ZeroSugar: five each), 291.531 seconds
and two candidates, with both final review phases accepted. Read-only replay confirmed
all 13 authorized anonymous Recognition comments for M14's Data Platforms team, unchanged
hashes, literal excerpts and 9 positive / 2 negative / 2 mixed counts. No neutral or
indeterminate labels. CMT27512 changed mixed to positive versus run fifteen on unchanged
text. Review demanded unrequested neutral examples and formatting, then introduced and
accepted incorrect coverage-to-indeterminate reasoning and mixed/neutral boundary wording.
This is operational recovery evidence, not validated classification or review quality.

Implemented locally at the user's request, without tests, API calls, commit or GitHub push:
shared `survey-sentiment-v2` definitions for Vanilla and ZeroSugar, stored rubric identity
and v1 replay for older reports; request-grounded omission corrections with retained
literal question excerpts; stronger reassessment/challenge instructions using the existing
obligation lifecycle. All canonical comments from privacy-released groups now accompany
the summary; support receives full response/label/reason pairs and their versioned rubric.
Suppressed texts remain excluded; coverage diagnostics contain counts/versions only.
Oversize complete review input fails at the existing bound rather than substituting a
sample. Five roles, provider settings, budgets, source gates and source-facts-v4/v1-v3
remain. No automatic semantic relabeling or wording-pattern rejection was added.
Tests and live behavior for this update remain unverified; preserve run sixteen and use
a fresh artifact for any later authorized evaluation. See the
[workflow](WORKFLOW_RELIABILITY.md#sentiment-and-correction-grounding-after-run-sixteen-2026-10-26)
and [validation status](TESTING_AND_RAG.md#semantic-review-update-after-run-sixteen-2026-10-26).

## Run fifteen and local review recovery, 2026-10-26

The first run fifteen failed with HTTP 504 during planning (one attempted call, no
successful calls), log `20261026_185354_9256ff04815d.jsonl`. Its JSON was overwritten
by the user's repeat under the same filename; the original log remains. The repeat,
`20261026_185739_726c29abd0f2.jsonl`, failed after 13 successful calls / 248.766 seconds,
with 19 calls and about 754 seconds left. New diagnostics worked: completeness repaired
object-valued suggestions on turn three; support then omitted clarification_question,
omitted suggestions, and attempted resolved on a current completeness correction.
The last old rejection did not identify which correction. No complete support review
or Original revision occurred. Source replay confirmed 13 eligible anonymous comments
in M14's only authorized team, Data Platforms, unchanged source hashes, literal stored
excerpts and aggregate counts: 8 positive, 2 negative, 3 mixed, zero neutral/indeterminate.
CMT27512 changed positive to mixed versus run fourteen on unchanged text; semantic label
accuracy remains unvalidated. The draft omitted requested visible literal excerpts and
said 'Both mixed comments' despite three mixed labels. Completeness falsely claimed
three categories were absent even though all five appeared in the table.

Implemented locally at the user's request, without GitHub publication: optional review
annotations normalize neutrally with diagnostics; invalid closure of a current correction
keeps it pending without discarding the support review. False omissions may be withdrawn
against visible content. Exhausted invalid support can return validated repair instructions
to Original within the four-draft bound, without a completed review or any release;
both phases must succeed on the revised answer. Completeness now sees trusted scope/team
context, without source evidence. Original/Vanilla instructions distinguish examples from
category totals and requested visible quotes. The user subsequently approved four total
drafts (initial plus three revisions) and recovery after any of the first three drafts.
ZeroSugar retains three attempts per phase; success stops early and shared budgets still
take precedence. No provider/model/shared-budget/rubric changes.
See [workflow](WORKFLOW_RELIABILITY.md#review-recovery-after-run-fifteen-2026-10-26) and
[offline validation](TESTING_AND_RAG.md#review-recovery-checks-2026-10-26). Live behavior
after this update, classifier accuracy and provider strict support remain unverified.

## Run fourteen and field diagnostics, 2026-10-26

Observed `apinex_prueba_vanilla_14.json` / `20261026_101230_bbbaadd0c825.jsonl`:
failed after 12 successful calls / 233.438 seconds, with 20 model calls and about 770
seconds remaining. Planning correctly selected Vanilla only. All 13 source texts,
hashes, labels (9 positive, 2 negative, 2 mixed), literal excerpts and aggregates matched;
the first candidate included the requested examples and used v4 without automatic
synthetic-data wording. Completeness repaired an object-valued suggestion, then returned
five issues including unjustified scope/source/method/layout objections. All three
support submissions failed top-level field validation. Their exact missing/extra fields
were not captured and cannot be recovered from this log. No completed support review or
Original revision occurred; the original artifact is retained unchanged and ignored.

Implemented the authorized diagnostic-only follow-up: schema-derived field comparisons,
bounded/redacted missing/additional-field capture in artifacts/logs/model feedback, and
phase/candidate/schema/condition identity across retries. Repeated versus changed errors
are distinguished; valid submission repairs emit a linked event. No semantic review rule,
provider setting, source contract, role or execution budget changes in this follow-up.
Completion-scope/source-legitimacy behavior and provider strict-mode compatibility remain
separate pending work. See [workflow details](WORKFLOW_RELIABILITY.md#field-error-diagnostics-follow-up-2026-10-26)
and [validation](TESTING_AND_RAG.md). The 279-test offline suite passed, including
nine new diagnostic regressions, on Windows Python 3.12.10. No new live-provider
request was made.

## Review/data update after runs twelve and thirteen, 2026-10-26

Implemented the user-selected general update: data-origin-neutral analysis across all
five roles and new outputs; Original retains analysis coordination and manager action
proposals without a checklist or another agent. `review-v2` uses one correction list,
complete obligation assessments, explicit withdrawal/consolidation, and model review
of pending metric relevance. Existing objective gates and two review stages remain.
`source-facts-v4` removes automatic origin claims; v1/v2/v3 replay is preserved. Partial
release retains the reviewed version separately from a newer unreviewed draft. UI text,
status/count projection and new chart exports are aligned. Configuration, source data,
budgets, classification rubric and the five roles are unchanged.
See the [current workflow](WORKFLOW_RELIABILITY.md#review-and-data-contract-update-2026-10-26)
and [validation record](TESTING_AND_RAG.md). All 270 offline tests passed on Windows
Python 3.12.10, the frontend production build succeeded, and runs twelve/thirteen
replayed exactly. Run fourteen above exercises this version; a complete successful
live result remains unverified.

Observed run twelve: `apinex_prueba_vanilla_12.json`, log
`20261026_091358_6b0386f57c31.jsonl`: failed after 12 successful calls / 231.75s;
13 labels (9 positive, 2 negative, 2 mixed), sources/excerpts/aggregation reproduced.
Visible excerpts were absent. Completeness requested revision; support had three
invalid submissions. An unrequested pending survey trend could also force Cherry work.

Observed run thirteen: `apinex_prueba_vanilla_13.json`, log
`20261026_092301_3a80945b0f39.jsonl`: partial after 14 successful calls / 265.375s;
identical source hashes and labels. The first review supported seven blocks and requested
repairs. Original added literal positive/critical/mixed excerpts in its second draft;
that draft's completeness review failed three structural attempts. Published blocks
came from the first reviewed draft. Review feedback also contained duplicate repairs,
unjustified data-origin objections and inconsistent routing. Classification semantics
remain unvalidated. Both original artifacts are preserved and not committed.

Reviewed: 2026-10-26 (America/New_York). This is a short entry point for future chats. It describes the local files inspected on this date; verify relevant sources before changing behavior. It is not a benchmark report or a transcript of every project conversation.

## Audit follow-up, 2026-10-26

The user authorized the three core-only updates, quick offline tests and GitHub publication.
ZeroSugar now requires assessments of every prior correction even if the response omits
`correction_reviews`; legacy reviews without pending corrections remain readable.
Responses requests and usage logs honor the profile's `max_output_tokens`, retaining the
3500 fallback. Budgeted generation calls share their existing deadline with Chat's
explicit attempts, which recheck it after pacing and before sending. Waiting/in-flight
requests are not cancelled; SDK-internal retries retain their existing settings.
The five roles, source-facts-v3/v1/v2 contracts, provider configuration and Echo_UI are
unchanged. See the [workflow follow-up](WORKFLOW_RELIABILITY.md#audit-follow-up-review-coverage-output-limits-and-request-deadlines-2026-10-26)
and [focused validation](TESTING_AND_RAG.md). The 121 focused offline checks passed on
Windows Python 3.12.14, including eight new regressions. Two older revision fixtures were
updated to assess their pending corrections. No full-suite or live-provider run was made.

## Purpose and architecture

Echo is the Practicum HR/people-analytics prototype. It uses synthetic employee data to support manager review. The application runs in a terminal and exports local artifacts; a local web UI is also available in [Echo_UI](../Echo_UI/README.md).

Local UI setup, 2026-10-22: copied only `Echo_UI/` from `origin/main` at `fcc014a`, preserving the existing uncommitted agent changes. Built the frontend and started FastAPI at `http://127.0.0.1:8765` using the separate Windows Python 3.12 environment `Echo_UI/.venv-windows`. HTTP checks confirmed the page, M14 lookup and scoped overview; browser inspection confirmed M14's manager workspace in its default Demo mode. No analysis or live model call was run. This verifies local UI startup, not answer quality. The repository's `start.sh` is for macOS/Linux; this local Windows server was started directly with `.venv-windows/Scripts/python.exe -m uvicorn app:app --host 127.0.0.1 --port 8765` from `Echo_UI/backend/`. The existing local Git branch was not merged or committed.

| Role | Current responsibility | Main implementation |
| --- | --- | --- |
| Original | Plan the analysis, select specialists, integrate proposed actions, and coordinate corrections. | [original.py](agents/original.py) |
| Cherry | Obtain scoped numeric evidence through SQL and prepared metrics. | [cherry.py](agents/cherry.py), [metrics.py](agents/metrics.py) |
| Vanilla | Retrieve source-linked text and classify scoped survey sentiment when requested. | [vanilla.py](agents/vanilla.py), [tools.py](agents/tools.py), [semantic_search.py](agents/semantic_search.py) |
| Lime | Select supported charts from Cherry's evidence and export accepted SVG/CSV/provenance artifacts. | [lime.py](agents/lime.py), [chart_export.py](agents/chart_export.py) |
| ZeroSugar | Review evidence, findings, and chart plans; identify corrections. | [zero_sugar.py](agents/zero_sugar.py), [findings.py](agents/findings.py) |

Typical flow: question/scope -> Original's plan -> Cherry and/or Vanilla -> candidate answer -> Lime when needed -> ZeroSugar -> accepted output or localized correction. Specialists are selected by need, not always all invoked. Final states include `complete`, `partial`, `needs_clarification`, and `failed`.

Specialists can also return structured `declined` or `incomplete` task outcomes. Original
uses those to correct routing or explain unresolved work; a decline does not prove absent
data. Sentiment-label counts belong to Vanilla; SQL/rating metrics belong to Cherry.

Unsupported findings are withheld. Independently supported blocks may be released as partial output; charts are withheld for incomplete packages. A missing recognition record is not proof that recognition never occurred. Sentiment prevalence requires the complete eligible population, not selected search hits.

Sources: [AGENT_ROLES.md](AGENT_ROLES.md), [WORKFLOW_RELIABILITY.md](WORKFLOW_RELIABILITY.md).
The [documentation map](DOCUMENTATION_MAP.md) lists every current guide, coding-assistant
instruction file and local historical reference. `AGENTS.md` guides project maintenance;
`agents/policies.py` supplies the shared rules actually composed into model calls.

## Retrieval and configuration

- Default text retrieval is local SQLite FTS5/BM25. Semantic and hybrid retrieval are optional and use a separately configured embedding provider. A graph is not required by the existing RAG.
- [connections.json](connections.json) is the current source for non-secret models, endpoints, API versions, limits, default profile, and role assignments. Current [connections.py](agents/connections.py) rejects the old model/endpoint environment-reference fields. Prefer this code and [TESTING_AND_RAG.md](TESTING_AND_RAG.md) over older setup paragraphs when they conflict.
- Credentials alone are loaded from the ignored private `.env` or process environment. Do not inspect them for orientation.
- The configured shared default is `gw_azure`; role assignments are currently unset and inherit it. `google_test` currently names `gemini-3.5-flash-lite`. Other provider profiles are experiments, not automatic fallbacks or proof of availability. An explicit `--profile` selects the profile for that run.
- No OpenRouter profile exists in the inspected configuration. Paid comparisons and Graphify were discussed in chat; this task does not implement either integration or select a winning model.
- Added on 2026-10-20: optional `apinex_test` uses the existing Chat Completions adapter with `https://api.apinex.bond/v1`, `free/gpt-6-luna`, and the private `APINEX_API_KEY`. The user selected Luna for all roles via `--profile apinex_test` and 20-second request spacing (3 RPM target). [request_pacing.py](agents/request_pacing.py) shares spacing and HTTP 429 cooldowns by endpoint/credential within one process; two bounded retries honor `Retry-After` with fallback backoff. SDK retries stay disabled. Existing model-turn and elapsed-time budgets remain unchanged; waits consume elapsed time. Separate processes are not coordinated. The user approved raising the shared Luna output allowance from 3500 to 6000 tokens. The connection probe confirmed one real tool call on this date; this is not proof of analytic quality. See [APInex setup and probe](TESTING_AND_RAG.md#apinex-sdk-trial).

## Current implemented contracts

Selected autonomy/review update, 2026-10-23: implemented 1A/2A/3A/4A/5B/6A/7B/8A.
Original's role instructions are consolidated and favor integration of adequate specialist
analysis without losing meaning. The mandatory deliverable checklist is retired; only
actual review corrections persist. ZeroSugar now performs separate visible-answer
completeness and evidence-support calls. The first call sees question/answer and visible
chart labels when present, without source data; its
omissions cannot be overridden by later source acceptance. Code attaches citations to
reviewed finding IDs. New phase diagnostics contain counts/status metadata only. Existing
five roles, specialist formats, sentiment repair, routing flags, scope/privacy gates and
source-facts-v3/v1/v2 replay remain. No provider/model configuration is changed. The agent
suite passed 242 offline tests on Windows Python 3.12.14, including 19 new regressions;
initial baseline was 223 tests with 15 failures and 4 errors. Earlier tests were aligned
with explicit v2 replay/current v3 contracts, and partial-result compatibility was repaired.
No live provider call was performed. The user authorized GitHub publication after tests.
One additional normal review call per candidate consumes the existing budgets; live quality,
cost and latency are still unmeasured. See the [current workflow](WORKFLOW_RELIABILITY.md#autonomous-synthesis-and-two-stage-review-2026-10-23).


Historical first-stage coordination update, 2026-10-22, after run ten (checklist retired on 2026-10-23): Original's existing plan now
requests literal request-derived deliverables with analytical owners. The checklist
accompanies specialist assignment, final synthesis and review; the original question
remains authoritative. Existing Vanilla/Cherry answer/evidence formats and standalone
commands remain. ZeroSugar returns explicit corrections per mandatory issue, including
owner, requested change and available sources, and assesses each previous pending item
on the next candidate while reviewing the entire revised package. Optional wording is
a suggestion, not a reason to block. Partial output names current reviewed gaps rather
than inferring them from the agent targeted for repair. Older planning/review fields
remain readable; no source-facts-v3 answer or v1/v2 replay change is introduced. Code
checks structure/references, not semantic completion. No tests, replay, provider calls,
commit or GitHub publication were performed at that initial stage, as requested. The existing
revision/call/time/token limits remain. Evidence-only handoff is still deferred. See
[coordination contract](WORKFLOW_RELIABILITY.md#requested-deliverables-and-explicit-corrections-2026-10-22).

Publication follow-up, 2026-10-22: the user subsequently authorized committing and pushing
the pending coordination code and reference updates, incorporating the group's UI commits
from `origin/main`. This publication does not validate runtime behavior or answer quality;
no new runtime tests, artifact replay or provider calls are part of this follow-up.

First-stage v3 update, 2026-10-21, after run nine: narrative quantities/quantifiers now
produce nonblocking review warnings, not automatic answer rejection. Interpretations may
cite text or source rows with `quote=null`, regardless of source count; supplied illustrative
quotes remain literal. Whitespace and unambiguous known citations normalize without a
repair turn. ZeroSugar receives flagged claims and available computed comparisons, and
explains their support/uncertainty in per-finding reasons. Code still verifies scope,
sources, exact excerpts, coverage and controlled calculations; it does not assign sentiment
or prove prose meaning. Rejections/normalizations retain bounded redacted narrative context
and feedback; warning assessments are logged. Saved v1/v2 rendering remains implemented.
No tests, artifact replay or API calls were run, by user instruction; only static review.
At that point the proposed next filename was `apinex_prueba_vanilla_10.json`; its later
observed result and the current next filename are recorded below.
A successful answer remains the goal, not a demonstrated outcome of these code changes.
Specialist evidence-only handoff remains a separate second-stage proposal. See
[v3 workflow](WORKFLOW_RELIABILITY.md#narrative-review-signals-and-presentation-v3-2026-10-21)
and [source contract](SOURCE_GROUNDING.md).

Planning update, 2026-10-21, after run eight: Original normalizes an unused clarification
basis to null when no clarification question is proposed, preserving all other plan checks
and the two-attempt limit. Rejected/normalized attempts retain bounded, redacted received
clarification values, cause and feedback in JSONL and `diagnostics.planning_attempts`,
including on failure. Real clarification requests still require a valid basis and
reconsideration. Redaction covers recognizable patterns, not every possible personal
detail; artifacts remain local. No tests or API calls were run, as requested. Prior test
results predate this change; live confirmation is pending. See
[planning normalization](WORKFLOW_RELIABILITY.md#planning-normalization-and-diagnostics-2026-10-21).

Historical synthesis/presentation update, 2026-10-21: v2 allowed several cited
text sources to support a provisional synthesis with `quote=null`, while individual
examples still need literal excerpts. Exact source tables suppress repeated cell sentences,
and narrative labels are grouped. Original preserves facts/meaning/provenance during
repair without freezing the previous layout. ZeroSugar checks all cited sources and
separates mandatory `issues` from optional `suggestions`. Stored v1 answers retain their
original replay contract. Five roles, existing tools, scope/privacy gates and 6000 APInex
output tokens were unchanged. Only focused final offline checks were authorized; no initial,
general or live test was part of that update. See
[the contract](SOURCE_GROUNDING.md) and [workflow](WORKFLOW_RELIABILITY.md#cited-synthesis-and-presentation-2026-10-21).
Final evidence: 36 focused offline tests passed. The saved seventh-run v1 candidate still
passes source-claim replay; its same selection renders as 10 blocks in v2 instead of 21,
without the repeated cell sentences. No saved artifact was overwritten or live model run
performed. These checks do not certify future agent compliance or sentiment semantics.

The approved updates on 2026-10-20/21 preserve the five roles, source restrictions and
independent review. Detailed change history belongs in the linked operating guides;
the observed live runs are recorded separately below.

| Area | Current behavior | Detailed reference |
| --- | --- | --- |
| Numeric evidence | Original plans all needed dimensions; Cherry retains metric/schema/SQL tools and reuses completed work. Models select source facts; Python renders tables, differences and matched-date comparisons. | [Source contract](SOURCE_GROUNDING.md), [workflow](WORKFLOW_RELIABILITY.md) |
| Shared instructions and scope | Six rules in `agents/policies.py` reach every analysis call path. A proposed initial clarification must identify a missing detail and reconsider the full request within the existing two planning attempts. Normal planning adds no call. | [Shared rules](WORKFLOW_RELIABILITY.md#shared-rules-and-initial-planning-clarifications-2026-10-21) |
| Text classification | Original distinguishes full sentiment from SQL ratings. Vanilla uses batches of 20, three attempts per batch, retained valid records/counters within the same workflow, literal quotes up to 400 characters and separate explanations up to 160. No partial percentages. | [Role contract](AGENT_ROLES.md), [sentiment repairs](WORKFLOW_RELIABILITY.md#sentiment-routing-retained-progress-and-task-declines-2026-10-21) |
| Individual text sources | Publishable summary examples also become canonical `survey_response` evidence for Vanilla/Original citations; ZeroSugar checks the actual scoped response, labels, hashes, coverage and aggregation. Labels/interpretations remain provisional. | [Source grounding](SOURCE_GROUNDING.md) |
| Task outcomes | Cherry, Vanilla and Lime can decline incompatible work in an existing turn. Original can correct routing and reuses identical closed-task outcomes. Missing evidence, incomplete work and failure stay distinct. No new agent or mandatory preflight call. | [Workflow repairs](WORKFLOW_RELIABILITY.md#sentiment-routing-retained-progress-and-task-declines-2026-10-21) |
| Diagnostics and release | V3 answer rejections/normalizations retain bounded redacted narrative context and feedback; batch diagnostics stay minimized. Narrative warnings reach ZeroSugar without becoming integrity errors. Unsupported findings stay withheld; complete status requires completed review and requested coverage. | [V3 diagnostics](WORKFLOW_RELIABILITY.md#narrative-review-signals-and-presentation-v3-2026-10-21), [CLI guide](README.md) |

The earlier full implementation check passed **207 offline tests on 2026-10-21**, including
22 [sentiment workflow regressions](tests/test_sentiment_workflow_repairs.py), without
provider requests. Scripted labels test contracts, not model quality. The current
documentation review did not rerun that suite. Live confirmation of the fifth-run repairs
and independently measured sentiment quality remain pending.

Later repair, 2026-10-21: permit quarter/ISO-date references, provide precise structured
citation feedback and repeated-error guidance, reuse retained specialist evidence for
independent review, and distinguish failed/unexecuted reviews. Lime and ZeroSugar retain
minimized repair diagnostics; provider token counters and failure stages improve local
diagnosis. Roles, tools, APInex's 6000 tokens and all execution budgets are unchanged.
The 75 focused offline checks listed in TESTING_AND_RAG.md passed; the full suite was
not rerun and live confirmation remains pending. See
[repair and recovery](WORKFLOW_RELIABILITY.md#repair-feedback-and-retained-evidence-2026-10-21).

## What is implemented versus demonstrated

Engineering checks/demo use scripted or mocked model responses. A connection probe establishes API/tool access for that request. A live answer establishes an observed execution, not general analytical accuracy. Model acceptance is not independent human validation.

Live testing has already begun. The following existing local artifacts were inspected for mode, status, call counts, and verification metadata through 2026-10-21:

| Artifact under local `reports/` | Observed metadata |
| --- | --- |
| `prueba_gemini_encuestas.json` | `live`, 7 successful Gemini calls, `complete`, verifier `accept`. |
| `workflow_improvements_live_check_v4.json` | `live`, 8 successful NVIDIA calls, `partial`, verifier `revise`. |
| `apinex_prueba_media.json` | `live`, 17 successful Luna calls, `failed`; Vanilla quote validation failed and all three ZeroSugar review attempts were invalid. The earlier log does not identify the exact invalid review field. |
| `apinex_prueba_media_corregida.json` | Follow-up attempt could not connect, zero successful API calls, `failed` with `provider_connection`. It does not test the corrected model behavior or 6000-token support. |
| `apinex_prueba_media_actualizada.json` | User's live follow-up: 19 successful Luna calls, `partial`, 5 released findings; both dimensions retrieved. Original delegated sentiment to Cherry, the table lacked in-block citations, and ZeroSugar approved contradictory comparison prose. Vanilla was not invoked. This demonstrated a grounding/semantic-review gap, not successful analytic validation. |
| `apinex_prueba_media_3.json` | User's third live run: 1 successful Luna planning call, `needs_clarification`. Original incorrectly asked to complete an already complete question. No data tools, specialists or source-bound final answers were exercised. The shared-policy/clarification update followed this observation. |
| `apinex_prueba_media_4.json` | User's fourth live run: `complete`, 9 successful Luna calls, verifier `accept`, 14 reviewed units, 168.718 seconds. Original 4 calls, Cherry 4, ZeroSugar 1; Vanilla/Lime skipped. Source aggregates and numerical changes independently matched. Four source submissions were corrected; their exact rejected arguments were not preserved and cannot be recovered. The gateway file reports 71,630 actual tokens and 214,890 quota units (x3). Final prose is repetitive, changing response denominators deserve fuller explanation, and one ZeroSugar rationale has a reversed comparison sign despite the correct coverage count. This is an observed numeric success, not general model/text quality validation. |
| `apinex_prueba_vanilla_5.json` | User's fifth live run: `failed`, 28 successful Luna calls, 545.36 seconds; Original 8 calls, Vanilla 13, Cherry 7, ZeroSugar 0. Incorrect routing, repeated classification and missing individual text sources exhausted the workflow. The third Vanilla delegation retained 13 complete labels (8 positive, 3 negative, 2 mixed), but no independent review occurred and no answer was released. Gateway usage: 151,229 actual tokens / 453,687 quota units (x3); no HTTP 429 observed. The repairs above follow this failure and have not yet been tested live. |

Sixth-run observation, 2026-10-21: `apinex_prueba_vanilla_6.json` and
`logs/20261021_140043_cc88dedfe33b.jsonl` record 14 generation attempts, 13 successful calls,
270.188 seconds and final `failed`. Thirteen provisional labels were retained (9 positive,
2 negative, 2 mixed). Vanilla's later generation hit the output limit; Original exhausted
seven turns after six validation rejections, including two `Q3` matches. ZeroSugar made
zero calls; `revise` was the failure default, not an independent verdict. Semantic label
quality and live confirmation of the new repair remain pending.

These files are ignored local artifacts and may be absent in another checkout. Their metadata was checked; this maintenance task did not rerun them or certify the findings. Do not describe all live evaluation as unstarted. A comparative winner remains unestablished.

Seventh-run observation: `apinex_prueba_vanilla_7.json` and
`logs/20261021_151118_6e9a78baa4d6.jsonl` record `partial`, 18 successful calls and 349.719
seconds (Original 7, Vanilla 6, ZeroSugar 5). The 13 labels cover unchanged sources:
8 positive, 2 negative and 3 mixed. CMT27512 changed from positive to mixed. Quotes,
hashes and aggregation matched the scoped source in a read-only audit; semantic accuracy
remains unvalidated. Both reviews supported all 21 blocks with no deterministic issues,
but requested synthesis/presentation repair. The old format repeated 11 numeric cells
after the table. Current changes follow this observation; no live confirmation is claimed.

Eighth-run observation: `apinex_prueba_vanilla_8.json` and
`logs/20261021_171341_9c0e36b4cea2.jsonl` record `failed`, two successful calls and
25.187 seconds. Original's plans were rejected for `unexpected_clarification_basis` then
`clarification_basis_required`. No specialist, data tool or independent review ran. The
planning update above follows this failure; the saved run is preserved unchanged.

Eleventh-run observation, 2026-10-22: `apinex_prueba_vanilla_11.json` and
`logs/20261022_185013_34573b500c0b.jsonl` record `complete`, 9 successful calls
(Original 3, Vanilla 4, ZeroSugar 2), 172.812 seconds and one candidate. Source coverage,
hashes, excerpts and aggregation matched 13 comments (8 positive, 2 negative, 3 mixed)
in the read-only audit. Vanilla repaired one nonliteral excerpt; ZeroSugar repaired an
F2 citation submission, then accepted all eight blocks. Requested literal examples were
still absent from both visible answers, despite being present in attached evidence. The
verifier's completeness rationale incorrectly treated them as displayed. No Original
correction pass ran. Synthesis also blurred favorable recognition with access concerns.
The deliverable list was not persisted by the diagnostic allowlist, so its contents cannot
be reconstructed. This exposed review/trace limitations, not validated classifier quality.
The selected 2026-10-23 update follows this result. Preserve run eleven; a later authorized
live attempt should use a fresh filename such as `apinex_prueba_vanilla_12.json`.

Tenth-run observation, inspected 2026-10-21/22: `apinex_prueba_vanilla_10.json` and
`logs/20261021_233751_93460f0e607c.jsonl` record `partial`, 12 successful Luna calls
(Original 4, Vanilla 4, ZeroSugar 4) and 228.875 seconds. All 13 comments were classified
(8 positive, 2 negative, 3 mixed; zero neutral/indeterminate); current scoped source IDs,
hashes, literal excerpts and aggregation matched in a read-only audit. They belong to
SUR2134, dated 2026-09-30. Vanilla's batch repaired two nonliteral excerpts; each review
repaired a rating-schema submission. The final review supported all six included blocks
with zero deterministic issues but requested the positive/critical literal examples
missing from the visible answer. Both examples were already in attached evidence.
Original added patterns during its one correction pass but still omitted the examples;
two candidate versions exhausted the revision bound, not the 1000-second allowance.
The reviewer also objected to usable "ask the team:" question phrasing. Semantic labels
remain provisional; this result does not validate the new coordination update. Preserve
run ten and use a fresh filename such as `apinex_prueba_vanilla_11.json` for a later run.

Ninth-run observation: `apinex_prueba_vanilla_9.json` and
`logs/20261021_182928_c61f05bcd469.jsonl` record `failed`, 17 successful calls
(Original 8, Vanilla 9) and 328.235 seconds. Planning passed immediately without needing
normalization. All 13 comments were classified (9 positive, 2 negative, 2 mixed; 0 neutral
or indeterminate). A nonliteral excerpt was corrected on batch attempt two. Vanilla and
Original each had six final-answer rejections and exhausted seven turns; nine of the
twelve rejections were narrative digit matches. Complete evidence was retained but no
independent review ran. These are provisional labels, not validated sentiment accuracy.
The first-stage v3 change above follows this failure; the original artifacts are unchanged.

Offline historical audit: four local artifacts, 13 role executions across Original/Cherry/Vanilla, zero API calls; source review packet at `reports/grounding_audit_before_upgrade.json`. No complete classification labels were preserved in those files, so semantic classifier accuracy is unavailable. Human query/entailment review remains pending; no old narrative result was retroactively certified.

For testing instructions, use [TESTING_AND_RAG.md](TESTING_AND_RAG.md). Run commands from `Agent_Echo/` with the project's Python environment:

```powershell
python -m unittest discover -s tests
python run_agent.py --show-connections
python evaluate_live.py --list
```

The latter two list configuration/cases without making model requests. Live evaluations require an explicitly selected case and configured provider access. Reports and incremental execution logs are local evidence; inspect them before reporting outcomes.

## Decisions, proposals, and pending work

- The sixth run was inspected and motivated the repair above. The user deferred live
  repeats, the full suite, token-limit increases and new agents. Any later authorized live
  comparison must preserve run six and use a fresh artifact filename. The
  [historical command](TESTING_AND_RAG.md#next-live-test-sixth-luna-run) remains a reference.

- Preserve the five-role baseline while evaluating answer quality, usefulness, and provider/model fit.
- The user wants evidence-grounded conclusions and useful partial results when independent findings survive a component failure.
- The existing decision document historically deferred UI and enterprise integration. The group's local UI is now available as recorded above; enterprise integration remains deferred. Dedicated recommendation/planning/execution/monitoring roles are proposals, not implemented agents.
- The existing [brainstorming and decisions document](../echo_brainstorm_resumen_y_decisiones.md), reviewed 2026-10-17, already records architecture, reviewed live examples, limitations, and candidate extensions. It is the detailed source for those discussions; do not present every proposal as approved. This source is present locally but currently ignored by Git, so another checkout may not contain it.
- The current model-selection discussion is exploratory. Compare the same representative HR questions and inspect tool correctness, cited findings, unsupported claims, total task cost, and latency before choosing.

## Reading map and maintenance

| Need | Start here |
| --- | --- |
| Complete reference inventory and maintenance rules | [DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md) |
| Roles and worked examples | [AGENT_ROLES.md](AGENT_ROLES.md) |
| Scope/review/partial-result behavior | [WORKFLOW_RELIABILITY.md](WORKFLOW_RELIABILITY.md) |
| Setup and live/offline/RAG evaluation | [TESTING_AND_RAG.md](TESTING_AND_RAG.md) |
| Provider assignments and adapters | [connections.json](connections.json), [connections.py](agents/connections.py), [model.py](agents/model.py) |
| Product discussion and proposed extensions | [Existing decisions document](../echo_brainstorm_resumen_y_decisiones.md) |
| Dataset/import documentation | [files_update/README.md](../files_update/README.md) |

Read the orientation documents once per chat when Echo work first becomes relevant, unless their contents are already available in the chat context. Reuse that orientation for subsequent questions; reread only relevant sections if the documents change or verification is needed. Additional source files and other chats are consulted only as needed for the current request.

Update only affected sections after material changes, with a review date and source. Keep live observations separate from planned tests. This file is project documentation, separate from Codex's machine-local generated memories.

Documentation review, 2026-10-21: reconciled setup/profile precedence, selective Lime
execution, batch retries, literal citations, current test history and the next live case
across current guides and local background. Historical classroom inspection dates and
license notices were preserved. This review changed documentation only; no new API call,
runtime feature or measured accuracy result was introduced.
