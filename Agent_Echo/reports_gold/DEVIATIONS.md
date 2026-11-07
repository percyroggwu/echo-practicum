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
