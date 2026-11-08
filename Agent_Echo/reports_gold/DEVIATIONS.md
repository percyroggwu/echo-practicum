# Deviations and decisions, priority 2 study

Started 2026-11-07, after the first live run. The frozen criteria
([v1](P2_DECISION_CRITERIA_v1.md), [v2](P2_DECISION_CRITERIA_v2.md),
[v3](P2_DECISION_CRITERIA_v3.md)) are not edited after a live run. This file records, in
order, each departure from them and each decision taken under them, with its evidence.

## D1 (2026-11-07): M1, Gemini B3 replaced by a diagnostic re-run

**Rule.** v1 stop condition: "Any new protocol failure stops the evaluation of that
measurement. It is diagnosed first and is not counted as evidence for or against any line."

**What happened.** In `results_apinex_gemini_test_20261107_163700.json`, B3 repeat 1 ended in a
protocol failure (`review_protocol_error`). In all four completeness attempts Gemini returned
two `submit_completeness_review` calls, which the validator rejects (`tool_call_count`). The
other 15 cases and all 16 apinex_test cases completed.

**Diagnosis.** B3 was re-run three times on apinex_gemini_test
(`results_apinex_gemini_test_20261107_220429.json`, repeats 2-4). All three completed, with no
`tool_call_count` rejection and a correct `revise` that flags the missing positive excerpt. The
apinex_test M1 baseline of 2026-11-03 had the same rejection twice and recovered both times. The
failure is an intermittent tool-call format error of the model (1 of 4 B3 runs), not a defect of
the case or the harness.

**Deviation.** By the user's decision, `results_apinex_gemini_test_20261107_163700_b3replaced.json`
replaces B3 repeat 1 with the first completed re-run (repeat 2), and adjudication continues. The
failed run is kept in `excluded_runs` with a `provenance` note, and the original results files are
unchanged. Repeat 2 is the first completed re-run in time, not the best of the three. The
`provenance` note and `M1_ADJUDICATION_NOTES_20261107.md` said the deviation "must be recorded in
v3". v3 is frozen, so it is recorded here instead.

**Effect on the decision.** None. Gemini regresses on false objections in B1 (a false
`CMT27512` label dispute, counted automatically), which does not depend on B3. Under the literal
stop rule, with no B3 evidence, the decision below is the same.

## M1 decision (2026-11-07): revert line A

Adjudicated sheets: `results_apinex_test_20261107_161602_sheet.md` and
`results_apinex_gemini_test_20261107_163700_b3replaced_sheet.md`. The case-by-case reasons are in
[M1_ADJUDICATION_NOTES_20261107.md](M1_ADJUDICATION_NOTES_20261107.md). `score_gold.py report`
gives:

| Metric | apinex_test baseline | apinex_test now | Gemini baseline | Gemini now |
|---|---|---|---|---|
| Protocol failures | 0 | 0 | 0 | 0 (after D1) |
| Wrong decisions | 3 | **4** | 3 | 2 |
| False objections B1/R6 | 0 | 0 | 0 | **1** |
| Missed defects B2-B13 | 1 | **4** | 4 | 1 |

Both profiles regress (bold = worse than the baseline). Under v1 ("Both profiles regress:
revert line A"), line A, "the manager-action requirement is checked in support" in the
ZeroSugar completeness prompt, is reverted. The revert is applied in step 5, on a new branch from
`a76b30f`. The re-run set is B5, B6, B14, B15, B16 and control B1, both profiles, repeats 1
([LINE_CASE_MAP_v2.md](LINE_CASE_MAP_v2.md)).

Sensitivity: the only contested answer that moves a count is apinex_test B11 (`no`). As `yes`,
missed defects become 3, still above the baseline of 1.

Observations, not part of the rule:
- Gemini's regression rests on one observation (n=1), while it improved on wrong decisions and
  missed defects. v1 has no compensation between metrics.
- Gemini disputed the stored `mixed` label of CMT27512 as `positive` in B1, B7 and the B3
  re-runs. The gold accepts `mixed`, so this false dispute recurs.

## M2 decision (2026-11-08): revert the two group B lines

Adjudicated sheets: `repairs_apinex_test_20261108_000412_sheet.md` and
`repairs_apinex_gemini_test_20261108_000626_sheet.md`. The block-by-block reasons are in
[M2_ADJUDICATION_NOTES_20261107.md](M2_ADJUDICATION_NOTES_20261107.md). No protocol failure, so no
deviation. Rule: v2, M2 for two lines.

| Profile | Destructive in R1-R5 | Runs | Baseline | Exceeds |
|---|---|---|---|---|
| apinex_test | **2** | R2 r1, R4 r1 (limits paragraph deleted) | 1 | yes |
| apinex_gemini_test | **3** | R2 r1 (critical excerpt deleted), R2 r2 (critical excerpt and limits deleted), R3 r2 (both excerpts emptied) | 2 | yes |

Each of the five losses was checked against the answer text: the limits paragraph or the excerpt
quote is absent, and each is listed in that case's "Must keep". Both profiles exceed their
baseline, so the two group B Original lines, "describe a category through its aggregate" and "do
not invent reasons for why a category is large or small", are reverted in step 5. The re-run set
is R1-R5, both profiles, repeats 2 ([LINE_CASE_MAP_v2.md](LINE_CASE_MAP_v2.md)). The
validation-step line is not part of this decision: v2 moved it to M4-O1.

Sensitivity: the decision changes only if one loss is overturned in each profile, since either
profile exceeding is enough to revert.

R6, reported separately and not deciding: the false correction was followed in 2 of 2 runs on
apinex_test (baseline 2 of 2) and 2 of 2 on apinex_gemini_test (baseline 1 of 2).

Observation, not part of the rule: `score_gold.py` counts a repair as destructive only when
content is lost. Repairs that leave the defect unfixed without losing anything (apinex_test R2
r2, apinex_gemini_test R1 r2) are not counted.

## M3 result (2026-11-08): stopped by protocol failures; plan() defect diagnosed

Results: `plans_apinex_test_20261108_001849.json` and
`plans_apinex_gemini_test_20261108_002436.json` (14 cases x 2 repeats per profile). Rule: v1 M3,
with the hard cases as clarified in v2 (P1, P10, P11). No failed run was re-run or replaced.

| Profile | Passed | Pass rate | Hard cases failed | Protocol failures |
|---|---|---|---|---|
| apinex_test | 17 of 28 | 60.7% | P1, P10, P11 | P12 r1, P13 r1 |
| apinex_gemini_test | 15 of 28 | 53.6% | P1, P10 | P8 r1, P8 r2, P9 r1, P12 r1, P13 r1 |

**Stop condition.** Both profiles have protocol failures, so the M3 evaluation stops (v1).

**Diagnosis.** All seven failures are `invalid_plan` after two model calls, and they share one
cause in `OriginalAgent.plan()` (`agents/original.py`, unchanged since `a76b30f`). Planning
allows two attempts (`for attempt in range(1, 3)`). The first valid clarification is always
rejected with `clarification_recheck`, to make the model reconsider, and that rejection uses one
of the two attempts:
- A clarification first asked on attempt 2 can never be accepted. This applies to Gemini P8 r1,
  P8 r2, P9 r1, P12 r1 and P13 r1, where attempt 1 failed for another reason: an unknown survey
  dimension, a missing `request_ref`, two calls in one turn, or a metric without
  `needs_numbers`.
- A clarification first asked on attempt 1 must be repeated on attempt 2 with no error. On
  apinex_test P12 r1 and P13 r1, attempt 2 dropped `clarification_basis.request_ref`, and no
  attempt was left to correct it.

This is a code defect, not a prompt line under decision, and not an intermittent model fault.
Re-running the failures would probably repeat them, and replacing a lucky pass would hide the
defect, so they were not re-run.

**Effect.** M3 fails whatever happens to the seven runs. If all seven passed, apinex_test would
reach 19 of 28 (68%) and apinex_gemini_test 20 of 28 (71%), both below 85%, and P1 and P10 would
still fail on both profiles. M3 reverts no line. Under v1 it records the observed failures.

**Recurring failures** (both repeats or two cases, so v1 allows a later fix that cites them):

| Failure | Where |
|---|---|
| The clarification recheck uses up the last planning attempt | 7 runs, 5 cases, both profiles (above) |
| P1 (hard, runs 63-66 question): `needs_numbers` true when not needed | apinex_test r2; apinex_gemini_test r1, r2 |
| P10 (hard): `needs_sentiment` true when not needed | apinex_test r1; apinex_gemini_test r1, r2 |
| `include_chart` true when no chart was asked | apinex_test P3 r2, P7 r1, P7 r2, P8 r2, P11 r2, P14 r1 |
| P7: `needs_sentiment` and `include_chart` | apinex_gemini_test r1, r2 |
| P11 (hard): `metrics` | apinex_test r1, r2 |
| After the recheck, the needed clarification is dropped (`clarify`) | apinex_gemini_test P12 r2, P13 r2 |

Follow-up, outside the priority 2 decision: fix `plan()` so the clarification recheck does not
use up the last attempt, test it offline, and re-run M3 afterwards. v1 also says the 85%
threshold and the hard-case list are revisited after this first M3 run, in a new criteria
version that applies from the next run.

## M4 decision (2026-11-08): revert all four group C lines

Results and adjudicated sheets: `m4_apinex_test_20261108_004028` (arm order "with first") and
`m4_apinex_gemini_test_20261108_004809` ("without first"); cases sha256 `aa1f4d2a9368` (frozen).
The reasons are in [M4_ADJUDICATION_NOTES_20261107.md](M4_ADJUDICATION_NOTES_20261107.md).
Rule: v3. Each "without" run recorded a `prompt_sha256` different from its "with" run, and O1
recorded the same Original prompt hash on both profiles.

**Protocol failure (v3: stops that line only).** Gemini C2 "with": the support phase was
rejected three times, twice for `safety_index` (field `safety_issue_index`) and once for
`tool_call_count`. These are format errors unrelated to the case's point. The run is not
evidence, and line C2 reverts.

| Line | test without / with | Gemini without / with | Decision (v3 table) |
|---|---|---|---|
| C1, unavailable evidence satisfies the request | handled / handled | handled / handled | Revert: no observed failure |
| C2, `task_outcomes`: a declined task is not absent data | handled / handled | handled / protocol failure | Revert: no observed failure; no evidence with the line on Gemini |
| C3, `CHART_NOTE` | mishandled / mishandled | handled / mishandled | Revert. Open defect: on apinex_test both arms falsely object about the chart or a causal claim, so the line does not fix what it claims to fix. On Gemini the line makes the case worse |
| O1, a validation step is a valid action when evidence is thin | Condition 1 fails in repeats 1 and 2 | Condition 1 fails in repeats 1 and 2 | Revert: every run proposes a direct fix (the base rate v3 predicted) |

The decision does not depend on contested answers. C2 and C3 revert whatever the adjudication
of a single block. C1 would need a "mishandled without" on both profiles to be kept, and O1
would need condition 1 to pass in all four runs.

## Priority 2 outcome (2026-11-08)

All seven prompt lines under decision revert. The revert happens in step 5: a new branch from
`a76b30f` that removes only these lines; `consolidate-agents` is not touched.

| Group | Lines | Decided by | Re-run set after the revert |
|---|---|---|---|
| A | Manager-action requirement checked in support (ZeroSugar completeness) | M1 | B5, B6, B14, B15, B16 and control B1, both profiles, repeats 1 |
| B | Aggregate; no invented reasons (Original) | M2 | R1-R5, both profiles, repeats 2 |
| C | Unavailable evidence; `task_outcomes`; `CHART_NOTE` (ZeroSugar) | M4 | M4 C1-C3, compared with the "with" results above |
| C | Validation step (Original) | M4-O1 | None |

M3 reverted nothing. It recorded the `plan()` clarification-recheck defect and the recurring
planning failures above, for a separate fix and a later M3 run.

## D2 (2026-11-08): step 5 branch base

**Plan.** `NEXT_STEPS_PLAN_FINAL.md` step 5 says to create "a new branch from `a76b30f` that
removes only the failed lines".

**Deviation.** Branch `revert-p2-lines` starts from `8ad6a85`, the head of `consolidate-agents`,
not from `a76b30f`. Between the two commits, `git diff a76b30f 8ad6a85 -- Agent_Echo/agents
Echo_UI` is empty, so the code under evaluation is the same. The later commits add only the
measurement tooling, frozen cases and records (M3 and M4 harnesses, criteria v2 and v3, results,
this file), which the step 5 re-runs need. `consolidate-agents` is not touched.

## Step 5 (2026-11-08): the seven lines removed

On `revert-p2-lines`, `agents/original.py` and `agents/zero_sugar.py` lose exactly the seven
lines, and nothing else in the prompts changes:

| Group | Removed text | Prompt |
|---|---|---|
| A | "Echo's own manager-action requirement is checked in the support phase; do not report it here." | `COMPLETENESS_INSTRUCTIONS` |
| B | "Describe a category through its aggregate; selected examples do not represent the whole category." | Original `INSTRUCTIONS` |
| B | "Do not invent reasons for why a category is large or small." | Original `INSTRUCTIONS` |
| C | "If the answer explains that requested evidence is unavailable, that satisfies the request." | `COMPLETENESS_INSTRUCTIONS` |
| C | "task_outcomes lists each specialist task; a declined or failed task is not evidence that data is absent." | `SUPPORT_INSTRUCTIONS` |
| C | `CHART_NOTE` (the constant and its use) | support instructions |
| C | "When evidence is thin, a validation or information-gathering step is a valid action." | Original `INSTRUCTIONS` |

`run_gold_m4.py --reverted` runs C1-C3 once on the reverted code. It refuses to start if any
of the lines is still present, and it writes `m4_reverted_<profile>_<UTC>.json`. The four M4
tests that need the lines in the code are skipped on this branch, and they pass on
`consolidate-agents`.

The re-run sets of the priority 2 outcome table ran live on 2026-11-08. Details and per-block
answers are in [RERUN_COMPARISON_20261107.md](RERUN_COMPARISON_20261107.md). They change no
decision; the results are recorded as observations on the reverted code.

| Re-run | Result | Comparison |
|---|---|---|
| M1 test, 6 cases | wrong 2, false-objection runs 1 (B1), missed 1 (B5) | v8: 3 / 0 / 1; consolidated: 4 / 0 / 4 |
| M1 Gemini, 6 cases | wrong 0, false-objection runs 0, missed 1 (B5) | v8: 3 / 0 / 4; consolidated: 2 / 1 / 1 |
| M2 test, R1-R5 x 2 | destructive 2 (R2 r1, R4 r1) | v8: 1; consolidated: 2 |
| M2 Gemini, R1-R5 x 2 | destructive 1 (R2 r2) | v8: 2; consolidated: 3 |
| M4 test, C1-C3 | C3 mishandled (false missing-chart claim) | consolidated "without": C3 mishandled |
| M4 Gemini, C1-C3 | C3 mishandled (invented "32 out of 36" and 8.8% claims) | consolidated "without": C3 handled |

All 38 blocks completed, no protocol failure. The M4 runs used an empty prompt addition, which
confirms the C lines are absent. On these samples the reverted code improves on wrong decisions
and missed defects against the M1 v8 baselines (test 2/1 vs 3/1; Gemini 0/1 vs 3/4), with one
test false-objection run (B1) against v8's 0; on M2 it stays one loss above its v8 baseline on
test and falls below it on Gemini; and it reproduces the C3 false chart objection on test. The
M2 test loss and the Gemini C3 one-case regression are reported as findings, not re-measured.

The M2 and M4 sheet answers of the consolidated runs were confirmed by the user on 2026-11-08,
and their "filled by the assistant as a proposal" headers were removed. The six re-run sheets
keep that header until the user confirms them.

## Step 5 re-runs (2026-11-08): reverted code on the same cases

On `revert-p2-lines`, with no protocol failure in 38 runs. The adjudication is in the six
`*_20261108_03*_sheet.md` files, and the case-by-case reasons and close calls are in
[RERUN_COMPARISON_20261107.md](RERUN_COMPARISON_20261107.md). The answers were confirmed by the
user on 2026-11-08 and the proposal headers removed. These runs do not reopen any decision: the
frozen criteria define none for them, and nothing was re-run to get a preferred result. The
counts below were checked with `score_gold.py report`.

| Group | Metric | test: v8 / with line / reverted | Gemini: v8 / with line / reverted |
|---|---|---|---|
| A (B1, B5, B6, B14-B16) | Wrong decisions | 3 / 4 / 2 | 3 / 2 / 0 |
| A | False objections B1 | 0 / 0 / 1 | 0 / 1 / 0 |
| A | Missed defects B2-B13 | 1 / 4 / 1 | 4 / 1 / 1 |
| B (R1-R5 x 2) | Destructive repairs | 1 / 2 / 2 | 2 / 3 / 1 |
| C | Cases mishandled (C1, C2, C3) | n.a. / C3 / C3 | n.a. / C3 / C3 |

The v8 and with-line numbers for group A cover all 16 cases, while the reverted numbers cover the
six re-run cases. They show the direction of change, not a like-for-like total.

Reading:
- **A.** On these cases the reverted code is at or below the v8 baseline on wrong decisions and
  missed defects, on both profiles. B1 flipped in opposite directions on the two profiles (n=1).
  Both profiles now miss B5, which both with-line runs found.
- **B.** apinex_test stays at 2, one above its v8 baseline of 1. apinex_gemini_test drops to 1,
  below its baseline. Removing the two group B lines did not bring apinex_test back to v8, so its
  excess destructive repairs are not explained by those lines alone.
- **C.** C3 is mishandled without `CHART_NOTE` on both profiles. On apinex_test it is the same
  false "no chart rendered" claim as the with-line and without-line arms. On Gemini it is a false
  "unsupported 32 out of 36" objection about the denominator; neither string is in the frozen
  answer. Together with M4, C3 fails with or without the line: the open defect is in the
  review of charts, not in the line.

## D3 and step 6 (2026-11-08): live runs 67-69

Step 6 called for one Luna run and one Gemini run with the runs 63-66 question and scope (M14,
2026-07-01 to 2026-09-30), on `revert-p2-lines`. The user ran Gemini twice (68, then 69). Run 68
is the step 6 run, and 69 is recorded as a repeat. Neither one replaces the other.

| Run | Profile | Status | Plan | Calls | Seconds | Where it stopped |
|---|---|---|---|---|---|---|
| 67 | apinex_test | partial | numbers false, no chart, no clarification | 18 | 270 | First review `revise` (CMT27512 positive vs mixed; no manager action). The revised draft hit the 6,000 output-token cap twice (`output_token_limit`, answer_validation); the reviewed draft was released. |
| 68 | apinex_gemini_test | partial | numbers false, no chart, no clarification | 15 | 258 | Draft 2 support review failed 3 attempts (`finding_missing`, a 6,000-token reasoning truncation, `assertion_coverage`; `review_protocol_error`); the reviewed draft 1 was released. |
| 69 | apinex_gemini_test | complete / accept | numbers **true**, no chart, no clarification | 21 | 275 | `needs_numbers` true sent a text question to Cherry, which failed harmlessly; one support review truncated at 6,000 tokens and recovered. |

All three classify the same 13 comments as 9 positive, 2 negative, 2 mixed, as run 63 did.

Against runs 63-66: no run asked the manager for data (65 and 66 did), none added a chart (64
did), and `label_group_sources` was never rejected (64: five times). The planning fixes therefore
hold in the full system. The remaining planning error is `needs_numbers` true on a sentiment-only
question (1 of 3), the same as M3 hard case P1. The two partial runs failed after planning, at
the 6,000 output-token cap that runs 64 and 69 also hit. This is recorded as an open item, not a
priority 2 line.
