# Human gold v1: freeze record, cases and scoring, 2026-11-03

**Frozen gold.** [GOLD_CASEBOOK_v1.md](GOLD_CASEBOOK_v1.md), filled by annotator "User1" and frozen
on 2026-11-03. SHA-256 `24d84029a130e2288878c31d880f6ca35a5792967daeffa3778d67484d5197d3`.
Companion [GOLD_REAL_CANDIDATES.md](GOLD_REAL_CANDIDATES.md), SHA-256
`fb953afd4a1691ea9eeb95f838419ab654da5e57a3460050c4e7fc5f265e6927`. Any change to the gold
becomes v2; `gold_cases.py` refuses a casebook whose hash differs. `GOLD_CASEBOOK_DRAFT.md`
is the working copy and is not used by the scripts.

One annotator, one question; no second annotation yet. No model has been run on these cases.

## Cases

`python gold_cases.py` writes `reports_gold/cases.json`. `reports_gold/` is tracked in git (moved
from the ignored `reports/gold_v1` on 2026-11-04): it holds the cases, their source runs
`apinex_prueba_gemini_51.json` and `apinex_prueba_vanilla_52.json`, every M1/M2 result and the
adjudicated sheets, so a clean clone can rebuild and rescore. The dataset is synthetic. It holds the parsed gold, 16 reviewer cases and 6 repair inputs.

- **B1-B13** are rendered by Echo's own source-facts-v7 renderer from the Gemini 51 evidence,
  so each candidate is exactly what Echo would produce. One difference from the casebook's
  display: Q1 and Q2 carry citations ([CMT27501, CMT27502] and [CMT27508, CMT27512]) because the
  renderer requires a source per item.
- **B9 and B11 cannot be produced by the renderer.** A quote cited to a comment that does not
  contain it, and a missing per-comment table, are rejected or flagged by code. They are
  tampered copies, and Echo's objective audit flags them ("Grounded answer selection cannot be
  reproduced", "Canonical per-comment classification display is missing"). They test the code
  gate, not reviewer judgment; score them separately.
- **B14-B16** are the saved 51/52 candidates with their own evidence and classification.
- The build checks that exactly B9 and B11 fail the objective audit; every other case passes it.
- **R1-R6** pair a Part B candidate with one Echo-format correction (owner Original). R6 is the
  false correction.

## Scoring

`score_gold.py` takes a results file from a future measurement run.

| Decided by code | Decided by the annotator (adjudication sheet) |
| --- | --- |
| Decision versus gold; protocol failures; label disputes against Part A (disputing a label the annotator accepts is a false objection); whether Original disputed R6; a diff of every repair | Whether the objections include each "Must flag" item; how many objections are false; whether a repair did "Must change" without losing "Must keep" |

No model text is matched by keywords and no model judges another model. `score_gold.py sheet`
writes the sheet in the casebook's `>` format; `score_gold.py report` totals each agent
version and profile against the Part D thresholds (1 of 6 false objections on B1/R6, 4 of 30
missed defects on B2-B13, 0 destructive repairs). An arm with unanswered sheet entries
reports `passes_thresholds: null`. Protocol failures count as failures.

## Verification

`tests/test_gold_cases.py` (4 tests; skipped without the local reports) checks the hash, the
case set, the objective-audit split, the declared variants and the scorer on scripted results.
Full offline suite: 425 tests passed. These verify the instrument, not any model.

## Running M1 (executed by the user, not by the coding assistant)

`run_gold_review.py` feeds the cases to ZeroSugar v7 and/or v8 with a real profile, one review
at a time, versions interleaved within each case. Only ZeroSugar is called. Each review has its
own budget (8 model calls, 600 s) and runs with `require_sentiment` and `require_actionable`
as in the workflow. Results are saved after every review to a new
`reports_gold/results_<profile>_<UTC>.json` in the format `score_gold.py` reads; the usual
execution log and private capture are written under `reports/logs/`. APInex pacing is 10 s
since 2026-11-03.

```powershell
..\Echo_UI\.venv-windows\Scripts\python.exe -B gold_cases.py
..\Echo_UI\.venv-windows\Scripts\python.exe -B run_gold_review.py --profile apinex_test --cases B1,B2,B7,B15 --dry-run
..\Echo_UI\.venv-windows\Scripts\python.exe -B run_gold_review.py --profile apinex_test --cases B1,B2,B7,B15 --repeats 1
..\Echo_UI\.venv-windows\Scripts\python.exe -B score_gold.py sheet reports\gold_v1\<results>.json reports\gold_v1\<results>_sheet.md
```

Smoke first (8 reviews, at least 16 calls). The full M1 set is 16 cases x 3 repeats x 2
versions per profile = 96 reviews (at least 192 calls); run it once per profile. The runner was
verified offline with a scripted v8 review only; the v7 path and every live call are untested.
M2 (R1-R6 through Original) needs a separate runner.

## First adjudicated M1 result, 2026-11-04

Runs `results_apinex_test_20261103_201450.json` (Luna) and
`results_apinex_gemini_test_20261103_220124.json` (Gemini): 16 cases, v7 and v8, **one repeat**.
Adjudicated by the annotator in the two `_sheet.md` files.

| Arm | Missed defects B2-B13 (of 10) | Missed B14-B16 | False objections, all cases | B1 false objections | Protocol failures |
| --- | --- | --- | --- | --- | --- |
| Luna v7 | 4 (B3, B6, B7, B12) | B14, B15 | 24 | 2 | 1 |
| Luna v8 | 1 (B12) | B14 | 15 | 0 | 0 |
| Gemini v7 | 3 (B6, B8, B11) | B14 | 31 | 4 | 1 |
| Gemini v8 | 4 (B2, B8, B11, B12) | none | 15 | 0 | 0 |

`score_gold.py report` printed `passes_thresholds: true` for all four arms, but the Part D caps are
absolute counts written for three repeats (4 of 30, 1 of 6). Scaled to one repeat (4/30 = 13% of
10 runs), only Luna v8 is within the missed-defect threshold; all arms meet the B1 cap; R6 (M2)
was not run. One repeat and one question: these are descriptive, not estimates of a rate.

## M2 repair runner, 2026-11-04

`run_gold_repair.py` runs R1-R6 through Original v7 and/or v8 for one repair round: the Part B
candidate is loaded as the saved draft (`block_catalog` of its grounding payload), one gold
correction is pending, no specialist is offered and no review follows. v7 receives the same
repair message and pending-correction context as its workflow; a v7 `challenge_corrections`
call is recorded as a dispute instead of starting a review. v8 receives `open_corrections`
and answers each with `correction_responses`. Budget per repair: 14 model calls, 600 s.
Results (`repairs_<profile>_<UTC>.json`) use the format `score_gold.py sheet/report` reads.
Verified offline with scripted v8 (R1) and v7 (R6) repairs; no live call by the assistant.

## First adjudicated M2 result, 2026-11-04

Files: `reports_gold/repairs_apinex_test_20261104_142206.json` (Luna) and
`reports_gold/repairs_apinex_gemini_test_20261104_142737.json` (Gemini), one repeat, with
the user's adjudication in the `*_sheet.md` files next to them. "Must change done" counts R1-R5
(R6 has nothing to change); "lost must keep" is the user's answer; `score_gold.py report`
counts a destructive repair when must-keep content was lost or the false correction R6 was
followed.

| Arm | Must change done (R1-R5) | Lost must keep | R6 | Destructive (report) | Input tokens |
|---|---|---|---|---|---|
| Luna v7 | 3 (R2, R3, R4) | R1, R2, R4, R6 | followed | 4 | 166,722 |
| Luna v8 | 4 (R2-R5) | none | followed | 1 | 108,502 |
| Gemini v7 | 2 (R2, R3) | R1, R6 | followed | 2 | 109,795 |
| Gemini v8 | 4 (R2-R5) | none | disputed | 0 (passes) | 94,055 |

R1 (keep exactly two questions) failed in every arm. v7 deletes must-keep content (the
action, the critical excerpt, the limits paragraph); v8 loses nothing. The failure left in v8
is duplication, which the user did not count as a loss: repairs re-added content that was
already saved (a second excerpt of the same comment beside the short one, the team questions
restated under another prefix, the action repeated) instead of reusing or replacing the saved
block. Because v8 keeps saved blocks unless removed, an addition without a removal becomes a
copy; the same pattern produced the duplicated answer of live run 53.

Response: Original v8 duplicate guard (`AGENTS_V8_DESIGN.md`, section 10).

## M2 rerun of v8 with the rejecting guard, 2026-11-04 (superseded, not adjudicated)

Files: Luna `repairs_apinex_test_20261104_152236.json` (1 repeat) and `..._152817.json`
(2 repeats); Gemini `repairs_apinex_gemini_test_20261104_152523.json` (1) and `..._153636.json`
(2): 36 v8 repairs. The guard fired in 34 of them and final duplicates fell to 1, but the
retries deleted content: about 12 repairs lost P1-P3, the action, a question or an excerpt
(the logs show a full restatement rejected with 7 repeats, then a retry that removed the saved
blocks and dropped the restatements). Input tokens roughly doubled. R6 was answered "fixed" in
all 6 runs. These runs measure a superseded version and were not adjudicated; the guard now
normalizes instead of rejecting.

## M2 v8 with the normalizing duplicate guard, 2026-11-04 (adjudicated)

Files: Luna `repairs_apinex_test_20261104_155327.json`, Gemini
`repairs_apinex_gemini_test_20261104_155752.json`, 2 repeats each (24 v8 repairs), with the
user's adjudication in the `*_sheet.md` files next to them.

| Arm | Must change done (R1-R5) | Lost must keep | R6 disputed | Destructive (report) | Duplicate pairs | Input tokens per repair |
|---|---|---|---|---|---|---|
| Luna v8, first M2 (1 rep) | 4 of 5 | 0 of 6 | 0 of 1 | 1 | several per repair | 18k |
| Luna v8, normalizing guard | 9 of 10 | 1 of 12 (R2 rep 2) | 0 of 2 | 3 | 1 in 12 | 17k |
| Gemini v8, first M2 (1 rep) | 4 of 5 | 0 of 6 | 1 of 1 | 0 | several per repair | 16k |
| Gemini v8, normalizing guard | 9 of 10 | 2 of 12 (R2 reps 1, 2) | 1 of 2 | 3 | 0 in 12 | 18k |

- Duplication is solved: 1 pair in 24 repairs, against copies in most first-M2 repairs; the
  normalization replaced 4-9 restated blocks in every repair at no extra call.
- The remaining failures are reasoning, not delivery: R2 removed or swapped the saved critical
  excerpt while adding the positive one (3 of 4; the logs show an explicit model removal "replaced"
  without a replacement), R1 kept a third question once per model, and R6 was answered "fixed"
  in 3 of 4 (the table was never damaged).
- `score_gold.py report` marks both arms as failing because its thresholds are absolute counts
  (0 destructive repairs) and do not scale with repeats; with 2 repeats the same rate counts twice.
- In the full workflow ZeroSugar v8 reviews each repair, so a dropped requested excerpt (R2) is
  a defect its completeness review is built to flag; M2 measures Original alone.
