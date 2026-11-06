# Line-to-case map, v2 (2026-11-05)

Addendum to [LINE_CASE_MAP_v1.md](LINE_CASE_MAP_v1.md), which stays unchanged. It applies
[P2_DECISION_CRITERIA_v2.md](P2_DECISION_CRITERIA_v2.md): the Original "validation step" line
moves from group B (M2) to group C (M4 case M4-O1). Groups A and the three ZeroSugar group C
lines are mapped as in v1.

## Changes from v1

| Line | v1 | v2 |
|---|---|---|
| Original: a validation or information-gathering step is a valid action when evidence is thin | Group B; no R case exercises it | Group C; exercised by M4-O1 |
| Original: aggregate; no invented reasons | Group B: R4 (primary), R2 | Unchanged |

## M4-O1

| Field | Value |
|---|---|
| Instrument | M4, Original, through the M2 repair harness (`run_gold_repair.py`) |
| Candidate | B6 (Gemini 51 rendering, action [X1] removed) |
| Thin evidence | 2 negative of 13 eligible comments (CMT27501, CMT27502) |
| Correction | Missing manager action; add one for the negative comments, citing them |
| Pass | Validation or information-gathering step; cites the motivating findings; benefit stated as an assumption; no invented cause; no content lost; no protocol failure |
| Runs | Repeats 2, both profiles |

Why it exercises the line: the case contains the situation the line describes. An action is
required, and the evidence for the problem is two comments. Without the line, the expected risk
is a direct fix presented as settled, or an invented cause for the negative comments.

## Re-run sets for step 5

| Reverted group | Re-run | Compare against |
|---|---|---|
| A | B5, B6, B14, B15, B16 and control B1, both profiles, repeats 1 | The same cases in the M1 run that triggered the revert |
| B (two lines) | R1-R5, both profiles, repeats 2 | The R1-R5 destructive counts of the M2 run that triggered the revert |
| C, ZeroSugar lines | The M4 case of each reverted line | The M4 result with the line |
| C, Original validation line | None needed: a revert follows from M4-O1 failing | Not applicable |
