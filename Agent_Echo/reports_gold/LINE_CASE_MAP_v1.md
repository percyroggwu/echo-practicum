# Line-to-case map, v1 (2026-11-05)

Step 1c of `audit final v8/NEXT_STEPS_PLAN_FINAL.md`. For each line under decision in
[P2_DECISION_CRITERIA_v1.md](P2_DECISION_CRITERIA_v1.md), this lists the gold cases that
exercise it. It is built from `GOLD_CASEBOOK_v1.md` (Parts B and C) and the saved answers, before
any live run. It does not change the frozen criteria. Step 5 uses it to choose which cases to
re-run after a revert.

"Exercises" means the line can change the outcome of the case: the case contains the situation
the line describes. A case that only receives the line in its prompt does not count.

## Group A: M1 (ZeroSugar completeness)

Line: "Echo's own manager-action requirement is checked in the support phase; do not report it
here."

| Case | Situation | Why it exercises the line |
|---|---|---|
| B6 | Manager action deleted | Completeness must not report the action as a user omission; support (ACTION_NOTE, code policy gap) must still flag it |
| B14 | Real answer (Gemini 51) without a manager action | Same as B6, on a real answer |
| B15 | Real answer (Luna 52 v1) without a manager action, plus missing excerpts and wrong category citations | Completeness must still report the missing excerpts while leaving the action to support |
| B16 | Real answer (Luna 52 v2) without a manager action, plus a missing critical excerpt | Same as B15 |
| B5 | Team questions replaced by actions | Boundary case: completeness must still report the missing questions; the line must not make it skip action/question items |

Control (no exercise expected): B1, the base answer with its action. Every other B case keeps
the action [X1] and does not exercise this line.

Expected effect: in v8 the missing action is detected in support (ACTION_NOTE and the code
policy gap), whatever completeness does. The line can therefore change duplicated or misplaced
issues in B6 and B14-B16 more than missed defects. Its regression signal is mainly in wrong
decisions or false objections on those cases, and on B5.

## Group B: M2 (Original repair)

| Line | Cases that exercise it | Why |
|---|---|---|
| A validation or information-gathering step is a valid action when evidence is thin | **None** | Every R candidate keeps action [X1], no correction asks for an action, and the evidence is not thin |
| Describe a category through its aggregate; selected examples do not represent the whole category | R4 (primary), R2 | R4 corrects "most employees feel ..." generalized from two comments. R2 adds an example, where a category claim could be written |
| Do not invent reasons for why a category is large or small | R4 | Qualifying the R4 claim is where an invented explanation of the negative count could appear |

R1, R3 and R5 do not exercise any group B line. They measure only the general effect of a longer
Original prompt on non-destructive editing, which is what the frozen R1-R5 criterion counts.

**Finding:** M2 cannot exercise the first group B line. The frozen criteria decide group B as one
group through the R1-R5 destructive count, so that line would be kept or reverted on the
evidence of the other two and of the general effect. Changing this needs
`P2_DECISION_CRITERIA_v2.md` before the first live run (for example, moving that line to group C
and adding an M4 case). This map does not change it.

## Group C: M4

No B or R case exercises these lines (checked 2026-11-05):

| Line | Why no gold case exercises it |
|---|---|
| Explained unavailable evidence satisfies the request | No B answer states that requested evidence is unavailable |
| `task_outcomes` line | `run_gold_review.py` calls the review without `task_outcomes` |
| `CHART_NOTE` | No case in `cases.json` has a chart, so the note is never sent |

M4 provides one case per line.

## Not under decision

The safety rule (pay, promotion, discipline, termination) is exercised by no case: no B answer
or R candidate mentions those terms. It is a product boundary adopted separately.

## Re-run sets for step 5

| Reverted group | Re-run | Compare against |
|---|---|---|
| A | B5, B6, B14, B15, B16 and control B1, both profiles, repeats 1 | The same cases in the M1 run that triggered the revert |
| B | R1-R5, both profiles, repeats 2 (the criterion counts R1-R5; R6 is not needed) | The R1-R5 destructive counts of the M2 run that triggered the revert |
| C | The M4 case of each reverted line | The M4 result with the line |
