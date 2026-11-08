# Re-runs after the priority-2 revert (2026-11-07)

The decisions of M1, M2 and M4 were taken before these runs and do not depend on them. The
frozen criteria are unchanged: v1 governs M1, v2 governs M2, v3 governs M4. These six runs only
record how the reverted code (`revert-p2-lines`, the seven lines absent) behaves on the same
cases. No case was re-run to obtain a preferred result, and no answer in the consolidated
sheets was revised.

The adjudicated answers are proposals filled by the assistant; the human adjudicator must
confirm or correct them. The testing convention is the one in `GOLD_CASEBOOK_v1.md` (Part B,
false objection = a mandatory correction to something the gold says is fine, or one that
contradicts the gold) and the one used in `M1_ADJUDICATION_NOTES_20261107.md`.

## The six runs

| Measurement | File | Blocks | Calls | Input tokens | Output tokens | Seconds |
|---|---|---|---|---|---|---|
| M1 test | `results_apinex_test_20261108_031856` | B1, B5, B6, B14-B16 | 16 | 149,759 | 22,344 | 437.8 |
| M1 Gemini | `results_apinex_gemini_test_20261108_033716` | same | 19 | 167,207 | 23,721 | 524.4 |
| M2 test | `repairs_apinex_test_20261108_032741` | R1-R5 x 2 | 14 | 191,820 | 12,253 | 135.3 |
| M2 Gemini | `repairs_apinex_gemini_test_20261108_034915` | R1-R5 x 2 | 10 | 133,872 | 8,841 | 95.3 |
| M4 test | `m4_reverted_apinex_test_20261108_033044` | C1-C3, once | 7 | 43,854 | 6,435 | 157.3 |
| M4 Gemini | `m4_reverted_apinex_gemini_test_20261108_035117` | C1-C3, once | 6 | 41,073 | 5,710 | 158.2 |

All 38 blocks completed; there is no protocol failure. The M4 runs refused to start unless every
group C line was absent, and their `prompt_sha256` values confirm it. C3 has `e3b0c44298fc`, the
empty `CHART_NOTE`, as in the consolidated "without" arm. C2 has `548eccb10009`, the same support
prompt as the consolidated "without" arm. C1 has `85efb04827f6`, not the "without" arm's
`7190ef60520b`, because line A was removed from the same completeness prompt.

## M1 (group A already reverted)

Per-case answers written into the sheets. `n.a.` means the gold has no must-flag defect.

| Case | Gold | Consolidated run (test) | Re-run (test) | Consolidated run (Gemini) | Re-run (Gemini) |
|---|---|---|---|---|---|
| B1 | accept | n.a. / 0 | n.a. / **2** | n.a. / 1 | n.a. / 0 |
| B5 | revise | yes / 0 | **no** / **2** | yes / 1 | **no** / 1 |
| B6 | revise | yes / 0 | yes / 0 | yes / 0 | yes / 0 |
| B14 | revise | no / 2 | no / 0 | yes / 0 | yes / 1 |
| B15 | revise | yes / 0 | yes / 0 | yes / 2 | yes / 2 |
| B16 | revise | yes / 0 | yes / 1 | yes / 0 | **no** / 0 |

(`Must flag found? / false objections`; bold marks a change from the consolidated run.)

`score_gold.py report` on the re-runs, next to the consolidated and v8 numbers:

| Metric | v8 test | consolidated test | re-run test | v8 Gemini | consolidated Gemini | re-run Gemini |
|---|---|---|---|---|---|---|
| Protocol failures | 0 | 0 | 0 | 0 | 0 | 0 |
| Wrong decisions | 3 | 4 | **2** | 3 | 2 | **0** |
| False objections B1/R6 (runs) | 0 | 0 | **1** | 0 | 1 | **0** |
| Missed defects B2-B13 | 1 | 4 | **1** | 4 | 1 | **1** |

Reading, without a decision:

- On these six cases both profiles improve on wrong decisions and missed defects against v8
  (test 2/1 vs 3/1; Gemini 0/1 vs 3/4). That is expected: the line that had made each profile
  regress is gone. These are the same six cases, not the 16-case measurement.
- Test has one false-objection run against 0 in v8: B1, with two "correct or qualify" items on
  F6 and F7 that the same review later calls supported. Gemini B1 moved the other way, from one
  false label dispute to none. This is the B1 flip both runs show: with one repeat per case it
  is noise.
- Both profiles now miss B5 (the review never mentions the missing follow-up questions). It was
  found in both consolidated runs.
- `passes_thresholds` is the generic casebook cap (0 destructive repairs in R1-R6). It is not
  the P2 rule and is not used here.

## M2 (group B already reverted)

Ten blocks per profile: R1-R5, repeats 1 and 2. MC = "Must change done?", LOST = "Lost anything
from must keep?".

| Profile | Block | MC | LOST | What happened |
|---|---|---|---|---|
| test | R1 r1 | **no** | no | Q3 was moved, not deleted (removed at its old line, re-added above the questions). |
| test | R2 r1 | yes | **yes** | Positive excerpt added, but the critical excerpt is replaced by the limits paragraph and never restored. |
| test | R3 r1 | yes | no | Critical excerpt re-cited to CMT27501 as a longer literal quote; positive excerpt and limits kept. |
| test | R4 r1 | yes | **yes** | "Most employees..." removed; both excerpts are replaced by paraphrases ("... showing ...") with no literal quote. |
| test | R5 r1 | yes | no | Repeated critical paragraph removed; both excerpts and the limits paragraph kept. |
| test | R1 r2 | **no** | no | Q3 moved again, not deleted. |
| test | R2 r2 | yes | no | Positive and critical excerpts widened; limits moved and kept. |
| test | R3 r2 | yes | no | Same re-citation as R3 r1. |
| test | R4 r2 | yes | no | Claim replaced by "Neither comment claims broad non-recognition"; excerpts widened, limits kept. |
| test | R5 r2 | yes | no | Duplicate critical paragraph removed; both excerpts kept. |
| Gemini | R1 r1 | **no** | no | Q3 moved, not deleted. |
| Gemini | R2 r1 | yes | no | Positive excerpt added; critical excerpt widened and kept. |
| Gemini | R3 r1 | yes | no | Re-citation to CMT27501 with the full literal quote. |
| Gemini | R4 r1 | yes | no | Claim removed; excerpts widened, limits kept. |
| Gemini | R5 r1 | yes | no | Duplicate critical paragraph removed; one positive and one critical excerpt remain. |
| Gemini | R1 r2 | yes | no | Q3 deleted. |
| Gemini | R2 r2 | yes | **yes** | Positive excerpt added (CMT27503), but the critical excerpt and the whole limits paragraph are deleted by the same hunk. |
| Gemini | R3 r2 | yes | no | Re-citation with a longer literal quote. |
| Gemini | R4 r2 | yes | no | Claim removed; excerpts widened, limits kept. |
| Gemini | R5 r2 | **no** | no | The duplicate critical pair was removed at its old place and re-added at the top, so the critical excerpt is still duplicated. |

Destructive repairs in R1-R5, next to the numbers already recorded:

| Profile | v8 baseline | consolidated run | re-run | Where the re-run loses content |
|---|---|---|---|---|
| apinex_test | 1 | 2 | **2** | R2 r1 (critical excerpt), R4 r1 (both excerpts paraphrased) |
| apinex_gemini_test | 2 | 3 | **1** | R2 r2 (critical excerpt and limits) |

Reading, without a decision:

- The test profile is still at the consolidated level (2) and one above its v8 baseline (1). The
  loss is the same kind seen before, not a new failure mode: R4 r1 repeats the consolidated
  R2 r1 mistake of putting the critical excerpt where the limits paragraph was, and R2 r1 loses
  a different member of the same must-keep list.
- Gemini falls to 1, below both its baseline (2) and the consolidated run (3). With one loss in
  ten repairs, a single case is the whole difference.
- Two repairs leave the defect unfixed without losing anything (test R1 r1 and r2: Q3 moved).
  `score_gold.py` does not count "Must change done? = no" as destructive; the M2 notes already
  record that gap.
- R6 was not part of the re-run set.

## M4 (group C already reverted)

| Case | Point | test | Gemini | Consolidated "without" arm |
|---|---|---|---|---|
| C1 | Requested neutral excerpt is unavailable | no | no | handled on both |
| C2 | Declined Cherry task is listed; ratings were not requested | no | no | handled on both |
| C3 | Correct chart: percent of responses, Responses denominator, no causal claim | **yes** | **yes** | test mishandled, Gemini handled |

- **test C3**: "No chart was actually rendered ... the 'chart' appears as a metadata object" is a
  false missing-chart claim; the chart exists in the payload. Same failure as the consolidated
  without arm, so the false claim is reproducible without the line.
- **Gemini C3**: the review says the answer contains "32 out of 36" and an 8.8% denominator
  explanation. Neither string nor any equivalent claim is in the frozen answer (each quarter
  uses its own denominator). This is a false "unsupported content" objection about the chart's
  denominator, i.e. about the case's point. The consolidated without arm had handled this case,
  so this is a one-case regression on n=1.
- C1 and C2 are handled as before on both profiles: the reviews' objections concern labels, the
  single survey date or CMT27507, not the case's point.

## Close calls in the proposals (for the human adjudicator)

1. **M1 test B5 = no / 2.** The review never mentions the follow-up questions, so the must-flag
   defect is missed. The two counted false objections are the demand for a second negative
   excerpt (CMT27502), when the question asks for one positive and one critical view, and the
   demand to restate the counts in prose when the table already shows them with the denominator.
   A third item ("F1 contradicted") is not counted because F1's content is not visible in the
   sheet.
2. **M1 test B1 = 2.** The two counted items are the "correct or qualify" corrections to F6 and
   F7, which the same review later reports as SUPPORTED. Items 1 and 2 explicitly ask for no
   change and are not counted.
3. **M1 test B16 = yes / 1.** The review finds the mixed-citation defect and asks for a genuine
   critical excerpt, but never flags the missing action. The single false objection is the
   "composite positive excerpt" claim: the quoted text is CMT27500's full literal quote, and the
   gold says the literal positive quote is correct.
4. **M1 Gemini B5 = no / 1.** The questions are missed. The counted false objection is
   "CMT27510 is miscategorized as mixed": the answer labels it positive, so the premise is wrong
   (the request is also conditional). If label remarks are excluded from false objections, this
   becomes 0.
5. **M1 Gemini B14 = yes / 1.** The counted false objection is the demand to consolidate the
   repeated example blocks, which the gold tolerates. The F11 denominator note is not counted:
   it accepts the count of 13 and asks about the provenance of the claim.
6. **M1 Gemini B15 = yes / 2.** The two counted items are (a) "literal_examples is empty, provide
   the text of all 13 comments" (the evidence has the texts and the question asks for two
   excerpts) and (b) "the table omits neutral and indeterminate rows" (both rows exist with
   zero). Repeated excerpt demands are the genuine must-flag defect, not false objections.
7. **M1 Gemini B16 = no / 0.** Only the mixed-citation defect is flagged; the missing critical
   excerpt and the missing action are not.
8. **M2 R3 (both profiles, both repeats) = yes / no.** The excerpt is widened to a longer literal
   quote that still contains the original sentence. If a widened quote counts as altering the
   quote's wording, all four R3 blocks become losses (+2 destructive per profile). The decision
   is unaffected because group B is already reverted.
9. **M2 test R1 and Gemini R1 r1 = must change no.** The third question is moved, not deleted.
   Gemini R1 r2 deleted it and is counted yes.

## Caveats

- M1 and M4 have one run per case; M2 has two. A single case changes a count in every table
  above, and B1 moved in opposite directions on the two profiles.
- The M4 harness still compares candidate lines verbatim (`candidate_lines_missing`), counts
  re-rendered B6 questions as added proposals, and has no `report` subcommand. None of these
  affects C1-C3, which are adjudicated from the issues, not from O1.
- The re-runs compare the reverted code with the consolidated code and with the v8 baselines;
  the reverted code is not byte-identical to v8 (it keeps the other consolidated changes).
