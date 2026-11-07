# M1 adjudication notes (2026-11-07)

Basis for the answers written into the M1 sheets. They are proposals for the human
adjudicator, not frozen decisions. The counting rule is the one at the end of
`GOLD_CASEBOOK_v1.md`: one count per distinct mandatory correction the gold does not
require; do not count the `Gold must flag` defect; do not count label disputes already
listed in `Automatic: false_label_disputes`; do not count optional suggestions.

## Provenance and one deviation

`results_apinex_gemini_test_20261107_163700.json` has a protocol failure on B3 repeat 1
(`review_protocol_error`, four rejected completeness attempts). By the user's decision of
2026-11-07, `results_apinex_gemini_test_20261107_163700_b3replaced.json` replaces it with
the first completed diagnostic repeat (repeat 2 of
`results_apinex_gemini_test_20261107_220429.json`). The failed run is preserved in
`excluded_runs`; the original files are unchanged. This overrides the frozen stop rule in
`P2_DECISION_CRITERIA_v1.md`; it is recorded as D1 in `DEVIATIONS.md` (v3 is frozen and is not edited).

## apinex_test (`results_apinex_test_20261107_161602`)

| Case | Must flag | False | Reason |
|---|---|---|---|
| B1 | n.a. | 0 | No objections. |
| B2 | no | 1 | Only F8 (the action) is objected; the missing critical excerpt is not. |
| B3 | yes | 2 | Positive excerpt flagged (items 1, 5, 8). False: explicit denominator fractions; explicit zero row for neutral. |
| B4 | n.a. | 1 | F12 withheld and asked to be corrected over an additional third question; the excerpt note is optional. |
| B5 | yes | 0 | Item 1 names the missing follow-up questions. |
| B6 | yes | 0 | Item 1 names the missing action. |
| B7 | no | 0 | Accept with no objections; the P3/CMT27510 defect is missed. |
| B8 | yes | 0 | Item 1 targets the "most employees" overgeneralization. |
| B9 | yes | 0 | Item 1 corrects the CMT27500 citation to CMT27501. |
| B10 | yes | 1 | Item 1 flags the identity guess. False: demanding exactly two questions and removing the action. |
| B11 | no | 3 | The objections treat the totals table as wrong; none flags the missing per-comment table. False: 9 positive/4 mixed counts; five-category totals and citations; whole-quarter scope. |
| B12 | no | 0 | Accept with no objections; the missing limits are missed. |
| B13 | n.a. | 0 | The only dispute on CMT27512 is the automatic one. |
| B14 | no | 2 | Borderline-label note and question framing; the missing action is not flagged. |
| B15 | yes | 0 | Items 1, 2 and 5 cover the mixed-citation, action and excerpt defects. |
| B16 | yes | 0 | Items 1 and 2 cover the action and mixed-citation defects. |

Report: protocol 0, wrong decisions 4 (B4, B7, B12, B13), false objections 0,
missed defects 4 (B2, B7, B11, B12), unadjudicated 0. `passes_thresholds` is true because
the casebook Part D caps are absolute (1 / 4 / 0); it is not the P2 baseline comparison.

## apinex_gemini_test with B3 substituted (`..._b3replaced`)

| Case | Must flag | False | Reason |
|---|---|---|---|
| B1 | n.a. | 1 | The only non-label mandatory correction is reframing the action as a pilot. The CMT27512 dispute is automatic. |
| B2 | yes | 0 | Item 1 names the missing critical excerpt. |
| B3 | yes | 2 | Positive excerpt flagged (items 1, 5, 8). False: explicit denominators; explicit zero row for neutral. |
| B4 | n.a. | 0 | Accept with no objections. |
| B5 | yes | 1 | Item 1 names the missing questions. False: F9/F11 are treated as unsupported because they are actions. |
| B6 | yes | 0 | Item 1 names the missing action. |
| B7 | yes | 0 | Item 2 names CMT27510 cited as mixed. The two label disputes are automatic. |
| B8 | yes | 1 | Item 1 targets "most employees". False: the F4/F5/F6 citation-mismatch family, contradicted by the claims. |
| B9 | yes | 1 | Item 1 corrects the citation. False: asking that "provisional model labels" be presented as final. |
| B10 | yes | 3 | Item 7 flags the identity guess. False: excerpts said to be invisible; explicit denominator; the `[SENTIMENT1]` tag treated as an uncited source. |
| B11 | yes | 1 | Item 1 names the missing per-comment table. False: the single-survey-date scope complaint. |
| B12 | no | 2 | Only borderline-label corrections; the missing limits are not flagged. |
| B13 | n.a. | 0 | The F9 note says the repetition is acceptable. |
| B14 | yes | 0 | Item 1 names the missing action. |
| B15 | yes | 2 | Items 2, 3, 5, 7 cover the label, excerpt and action defects. False: the negative-theme claim; re-evaluating CMT27510/CMT27512 as mixed. |
| B16 | yes | 0 | Items 1 and 2 cover the action and mixed-citation defects. |

Report: protocol 0, wrong decisions 2 (B1, B13), false objections 1 (non-zero),
missed defects 1 (B12), unadjudicated 0. `passes_thresholds` is true for the same absolute
caps; it does not mean the arm matches its baseline.

## Result against the P2 baselines

| Metric | test baseline | test now | Gemini baseline | Gemini now |
|---|---|---|---|---|
| Protocol failures | 0 | 0 | 0 | 0 |
| Wrong decisions | 3 | 4 (worse) | 3 | 2 (better) |
| False objections B1/R6 | 0 | 0 | 0 | 1 (worse) |
| Missed defects B2-B13 | 1 | 4 (worse) | 4 | 1 (better) |

Both profiles regress on at least one v1 metric. Under the M1 rule in
`P2_DECISION_CRITERIA_v1.md` ("Both profiles regress: revert line A"), group A is reverted.
