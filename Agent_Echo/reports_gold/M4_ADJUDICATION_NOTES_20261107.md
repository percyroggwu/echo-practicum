# M4 (group C) adjudication notes

Proposals written on 2026-11-07 for the two live M4 runs started at
`2026-11-08T00:40:28Z` (apinex_test, "with" arm first) and `2026-11-08T00:48:09Z`
(apinex_gemini_test, "without" arm first). Cases sha256 `aa1f4d2a9368` (frozen,
`M4_SHA256`). Criteria: `P2_DECISION_CRITERIA_v3.md`.

The answers in both sheets were filled by the assistant; the human adjudicator must confirm or
correct them. Sheets:

- `m4_apinex_test_20261108_004028_sheet.md` (8 blocks: C1-C3 x 2 arms, O1 x 2 repeats)
- `m4_apinex_gemini_test_20261108_004809_sheet.md` (same 8 blocks)

The Gemini `C2 with` block ended in `review_protocol_error` and is not adjudicated, as v3
requires. It is not evidence for or against the `task_outcomes` line.

## C1-C3: mishandling per arm

Question asked in each block: did ZeroSugar raise a false objection, or a false "data absent"
claim, **about the case's point**? Objections about other topics do not count.

| Case | Point | Profile | Without | With | Decision |
|---|---|---|---|---|---|
| C1 | Requested neutral excerpt is unavailable (0 neutral comments) | test | no | no | revert: no observed failure |
| C1 | same | gemini | no | no | revert: no observed failure |
| C2 | Declined Cherry task listed; survey ratings exist but were not requested | test | no | no | revert: no observed failure |
| C2 | same | gemini | no | not adjudicated | revert: no evidence |
| C3 | Correct chart: percent of responses, Responses denominator, no causal claim | test | **yes** | **yes** | revert + open defect |
| C3 | same | gemini | no | **yes** | revert: the line makes the case worse |

What counted and what did not:

- **C1 test without**: issue 1 mentions the neutral excerpt but says "the deliverable is
  satisfied by explicit non-existence"; its fix is to keep the statement. That is not a false
  objection and not a false absence claim. Issue 2 (three follow-up items instead of two) is a
  different topic. Issue 3 in the Gemini run (F13 limits missing) is also a different topic.
- **C2 test with**: the four issues are the CMT27512 label, the single-date comment coverage,
  the disputed labels and the F2 withholding. None treats the declined Cherry task as absence of
  data, and none claims ratings data is missing. Issue 2 asks to confirm comment coverage for
  Q3; it is not a false "data absent" claim and does not concern the case's point.
- **C3 test without**: with `CHART_NOTE` blanked, issue 1 says "no chart image is present in the
  deliverable; only chart metadata exists". The chart exists in the payload; this is the false
  missing-chart claim the line is meant to prevent.
- **C3 test with**: issues 1 and 4 object that the answer implies which practices caused the
  rise. The answer says "The rise shows change over time, not its cause" and its action is to
  ask the team which practices changed, with the benefit called an assumption. The objection is
  false and is about the "no causal claim" part of the point.
- **C3 gemini with**: with `CHART_NOTE` present, issue 1 still says "The requested chart is
  missing from the visible output". False objection about the point. Without the line the same
  case was accepted, so the line made this run worse.

C3 therefore reverts on both profiles. For `apinex_test` both arms mishandle the point, which v3
records as an **open defect**: `CHART_NOTE` does not fix what it claims to fix. For
`apinex_gemini_test` the with-line arm mishandles a case the without-line arm handled.

## O1: the Original validation line

Condition 2 is automatic and true in all four runs (the added proposal cites CMT27501 and
CMT27502). Condition 6: no protocol failures in the four repair runs.

| Run | 1. Validation step, no B6 question repeated | 3. Benefit as assumption | 4. No invented cause | 5. No content lost |
|---|---|---|---|---|
| test repeat 1 | **no** | **no** | yes | yes |
| test repeat 2 | **no** | **no** | yes | yes |
| gemini repeat 1 | **no** | **no** | yes | yes |
| gemini repeat 2 | **no** | yes | yes | yes |

Condition 1: every run proposes a direct fix, not a validation or information-gathering step:

- test 1: "Introduce a rule that project summaries and thank-yous list all contributors ... and
  add a follow-up check".
- test 2: "institute a standing recognition reminder at the end of each delivery week".
- gemini 1: "review project summaries and thank-you practices to ensure support work is
  consistently included" (a corrective review presented as settled; the closest call of the
  four).
- gemini 2: "Make a rule that project summaries and thank-yous list all contributors by name".

Condition 3: only Gemini repeat 2 states an "Assumed benefit". The other three assert "this
addresses ..." or state no benefit at all; none uses may/could/to check whether.

Condition 4: no run explains why the negative count is small or why support work is left out.

Condition 5: the sheet's missing-line list is verbatim matching, so it flags reformatting.
Checked against the actual answers, nothing is lost in any run:

- test 1: "recaps naming contributors" vs "recaps that name contributors"; the two example
  lines grew to the full literal quotes (the critical CMT27501 example is still present at the
  top of the interpretation); "all comments are from one team" vs "come from". All present.
- test 2: the two "Ask the team" lines appear as "Team question" with the same text and
  citations; limits add "(not human-validated)" and "all 13 comments".
- gemini 1: the two example lines appear as label-only lines plus full literal blocks; P1,
  limits and both questions present.
- gemini 2: the mixed paragraph keeps its three citations and adds "overall positive experience
  with caveats"; limits are expanded; both questions appear as "Team question".

As the user noted, in repeat 2 of both profiles the two re-rendered questions are the B6
questions, not new proposals. The harness lists them under "Added proposals" only because the
payload text changed from "Ask the team:" to "Team question:". They were not counted as added
proposals for condition 1.

Condition 1 fails in all four runs, so the O1 line reverts. This is the base rate that v3
predicted: the removed B6 action was a concrete fix, and Original proposes a fix again.

## Per-line decisions (v3)

| Line | Decision |
|---|---|
| C1, unavailable evidence satisfies the request | Revert: neither arm mishandled the point on either profile |
| C2, declined task is not evidence data is absent | Revert: no arm mishandled; Gemini with-line run not adjudicated |
| C3, `CHART_NOTE` | Revert; open defect on apinex_test (both arms mishandled), made the case worse on apinex_gemini_test |
| O1, validation step is a valid action | Revert: condition 1 fails in all four runs |

All four group C lines revert. No prompt line stays.

## Cost

| Profile | Runs | Model calls | Input tokens | Output tokens | Seconds |
|---|---|---|---|---|---|
| apinex_test | 8 | 18 | 152,921 | 15,543 | 373.2 |
| apinex_gemini_test | 8 | 18 | 156,503 | 21,264 | 405.7 |

Both are inside the v3 range of 14-76 calls per profile. Rejected attempts: test 4 (C1 with 2,
C3 without 2); Gemini 4 (C1 without 1, C2 with 3).

## Harness notes for the next update

1. `repair_checks` compares candidate lines verbatim, so every wording change shows up as a
   missing line. It is a diagnostic only (v3), but it would be cheaper to compare normalized
   text.
2. Re-rendered B6 questions ("Ask the team:" -> "Team question:") are counted as added
   proposals by the payload comparison. Condition 1 was adjudicated on the substantive new
   proposal.
3. There is no `report` subcommand for M4; the per-line decision is adjudicated by hand from
   these sheets.
