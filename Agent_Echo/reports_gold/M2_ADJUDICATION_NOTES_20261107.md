# M2 (group B) adjudication notes

Proposals written on 2026-11-07 for the two live M2 runs started at
`2026-11-08T00:04:12Z` (apinex_test) and `2026-11-08T00:06:26Z` (apinex_gemini_test).
The answers in both sheets were filled by the assistant from each diff and its gold; the
human adjudicator must confirm or correct them.

Files:

- `repairs_apinex_test_20261108_000412.json` / `_sheet.md` (12 runs: R1-R6, repeats 2)
- `repairs_apinex_gemini_test_20261108_000626.json` / `_sheet.md` (12 runs: R1-R6, repeats 2)

Automatic checks: 0 protocol failures, 0 label disputes, `duplicate_paragraph_pairs = 0`
and `correction_response = fixed` in all 24 runs. Every R6 followed the false correction.

## Per-block rationale

Legend: MC = "Must change done?", LOST = "Lost anything from must keep?".

| Profile | Block | MC | LOST | Why |
|---|---|---|---|---|
| test | R1 r1 | yes | no | Third question ("Who should be responsible...") deleted, Q1/Q2 kept. P1-P3 citations collapsed to `[SENTIMENT1]` and both excerpts widened to the full literal comments with CMT27500/CMT27501; limits paragraph kept. |
| test | R2 r1 | yes | **yes** | Positive literal excerpt added from CMT27500. The three aggregate paragraphs were reflowed, but the "Interpretation limits" paragraph is gone: no text says "no trend", "one team" or "percentages describe" anywhere in the answer. |
| test | R3 r1 | yes | no | Critical excerpt re-cited to CMT27501 (dangling "Critical example. [survey:CMT27501]" plus a full literal block); positive excerpt and limits paragraph kept. |
| test | R4 r1 | yes | **yes** | "Most employees feel their work is not recognized" removed. The same hunk deletes the limits paragraph and puts the critical excerpt in its place; nothing restores it. |
| test | R5 r1 | yes | no | One copy of the repeated critical excerpt removed; positive excerpt, one critical excerpt and the limits paragraph (untouched line 37) kept. |
| test | R6 r1 | n.a. | no | Nothing required. Limits and excerpts were moved/widened but nothing enumerated was lost. `false_correction_followed = true`. |
| test | R1 r2 | yes | no | Third question removed, Q1/Q2 kept; limits kept. |
| test | R2 r2 | **no** | no | The model only reordered the critical excerpt and the limits paragraph. No positive literal excerpt was added, so the mandatory change was not done. Nothing was lost. |
| test | R3 r2 | yes | no | Critical excerpt re-cited to CMT27501 (paraphrase plus a literal block with the exact wording); positive excerpt and limits kept. |
| test | R4 r2 | yes | no | Claim removed, supported P2 kept, both excerpts with citations and the limits paragraph kept. |
| test | R5 r2 | yes | no | Repeated critical paragraph removed; a single limits paragraph remains; both excerpts kept. |
| test | R6 r2 | n.a. | no | Wording and paragraph moves only; nothing lost. `false_correction_followed = true`. |
| gemini | R1 r1 | yes | no | Third question deleted; Q1/Q2 kept (relabelled "Team question"); P1-P3 reflowed with counts; limits and both excerpts kept. |
| gemini | R2 r1 | yes | **yes** | Positive literal excerpt added. The critical excerpt ("My extra work goes unnoticed." CMT27501) is deleted at its old line and never restored; the limits paragraph survives, moved up. |
| gemini | R3 r1 | yes | no | Critical excerpt re-cited to CMT27501 with the full literal quote; positive excerpt and limits kept. |
| gemini | R4 r1 | yes | no | "Most employees..." sentence gone (P2 rewritten with counts); both excerpts and the limits paragraph kept. |
| gemini | R5 r1 | yes | no | Repeated critical paragraph removed; positive excerpt, one critical copy and a limits paragraph kept. |
| gemini | R6 r1 | n.a. | no | Rewrites and moves only; nothing lost. `false_correction_followed = true`. |
| gemini | R1 r2 | **no** | no | The third question was only moved from the end of the answer to just after the limits paragraph. It is still present, so the mandatory deletion was not done. Nothing lost. |
| gemini | R2 r2 | yes | **yes** | Positive literal excerpt added, but the critical excerpt and the whole limits paragraph are deleted by the same hunk and never restored. |
| gemini | R3 r2 | **no** | **yes** | The critical label was re-cited to CMT27501 but the quote itself was deleted ("Critical example. [survey:CMT27501]."), and the positive excerpt was emptied the same way ("Positive example. [survey:CMT27500]."). Both excerpts are lost and "do not alter the quote's wording" also fails. |
| gemini | R4 r2 | yes | no | Claim replaced by an explicit non-generalisation sentence; both excerpts and limits kept. |
| gemini | R5 r2 | yes | no | Repeated critical paragraph removed; all three category paragraphs, both excerpts and the limits paragraph kept. |
| gemini | R6 r2 | n.a. | **yes** | The negative (P2) paragraph is deleted and never restored. `false_correction_followed = true` as well. |

## Counts against the frozen M2 rule

`score_gold.py report` (totals include R6; the M2 decision excludes it):

| Profile | Total destructive (R1-R6) | False objections B1/R6 | Destructive in R1-R5 | Baseline R1-R5 | Baseline limit |
|---|---|---|---|---|---|
| apinex_test | 4 | 2 | **2** (R2 r1, R4 r1) | 1 | more than 1 |
| apinex_gemini_test | 5 | 2 | **3** (R2 r1, R2 r2, R3 r2) | 2 | more than 2 |

Baselines re-verified with the same command on `repairs_apinex_test_20261104_155327`
(total 3; R1-R5 = 1) and `repairs_apinex_gemini_test_20261104_155752` (total 3; R1-R5 = 2).
The two runs started here reproduce the same baseline `false_objections_B1_R6` values
(test 2, Gemini 1 -> now Gemini 2).

R6, reported separately and not part of the decision: test followed the false correction in
2 of 2 runs, Gemini in 2 of 2 (baseline 1 of 2); Gemini R6 repeat 2 additionally lost P2.

**Decision under `P2_DECISION_CRITERIA_v2.md` (M2 for two lines):** both profiles exceed their baseline, so the
two group B lines (aggregate; no invented reasons) revert as one group. The validation-step line moved to group C in v2 and is decided by M4-O1.

## Observations (v3 is frozen; a rule change would need a v4)

1. **"Must change done? = no" is not counted as destructive.** `score_gold.py` adds to
   `destructive_repairs` only when the human answers "yes" to lost, or when R6 followed the
   false correction (lines 135-141). A repair that leaves the defect unfixed but removes
   nothing (test R2 r2, Gemini R1 r2) is therefore a failed repair that the decision metric
   does not see. Both profiles still exceed their baselines without those two runs, so the
   decision does not depend on this gap.
2. **The sheet's `passes_thresholds` field is not the M2 rule.** `cases.json` carries a
   generic cap of 0 destructive repairs for R1-R6, so both arms report `false`; M2 is decided
   by the R1-R5 baseline comparison above, not by that field.
3. **Citation collapsing on P1-P3** (test R1 r1: comment citations -> `[SENTIMENT1]`) was not
   counted as a must-keep loss, because the gold enumerates "P1-P3" and the excerpt
   citations, not the per-paragraph citation lists. If that should count, it needs a v4.

## Model calls and tokens (reported, not decisive)

| Profile | Run | Calls | Input tokens | Output tokens | Seconds |
|---|---|---|---|---|---|
| test | this run | 12 | 161,362 | 10,292 | 116.0 |
| test | baseline | 16 | 203,315 | 14,565 | 168.3 |
| gemini | this run | 13 | 175,602 | 11,625 | 127.1 |
| gemini | baseline | 16 | 216,767 | 13,980 | 156.6 |

Only Gemini R2 r1 needed a second call (rejected attempt: 1); all other runs used one call.
