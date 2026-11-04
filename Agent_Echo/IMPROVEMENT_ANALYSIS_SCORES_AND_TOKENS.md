# Agent improvements for score and token use: analysis, 2026-11-01

Analysis only. It proposes changes per agent and for the system that would raise the scores in
[SOLUTION_EVALUATION_1_TO_10.md](SOLUTION_EVALUATION_1_TO_10.md) and reduce input tokens per
workflow. Nothing here is approved or implemented; no runtime change, test, model call or
publication was made. It builds on
[AUDIT_RUNS_51_52_REASONING_VS_SYSTEM.md](AUDIT_RUNS_51_52_REASONING_VS_SYSTEM.md) (E/P numbers
and Addendum A) and extends section 7 of
[AUDIT_LUNA_RUNS_THROUGH_50.md](AUDIT_LUNA_RUNS_THROUGH_50.md) (Luna token growth) to every
profile and to runs 51/52.

**Revision 2, 2026-11-01.** Revision 1 measured only runs 51/52, although the request covered
all previous runs. This revision re-derives the token and rejection evidence from every workflow
log with usage counters, checks each proposal against what is already implemented and against
the history of earlier fixes, and changes several items. Section 8 lists every change. Item IDs
from revision 1 are kept, except Cherry's C1-C3, renamed K1-K3 because they collided with the
criteria C1-C8. Addendum A of the audit still governs Z3, O1, Z6 and Z7.

**Revision 3, 2026-11-01.** Corrects token figures identified in
[CORRECTION_UPDATE_PLAN_2026-11-01.md](CORRECTION_UPDATE_PLAN_2026-11-01.md) section 2: the X1
Luna 52 saving, the section 7 loop-saving range and O2's token reasoning. Recomputed from the
run 52 log: the failing candidate's four support calls were 27,636 + 28,760 + 31,235 + 33,726 =
121,357 input tokens (revision 1 reported 121,378). Nothing else changed.

**Evidence labels.** `[OBSERVED]` computed for this document from `reports/logs/*.jsonl`
(`model_started`, `review_phase_started`, `model_response_usage`), the private captures
(`model_input` in `reports/logs/details/<run_id>/exchanges.jsonl`) or the `rejected_attempts`
lists of `reports/apinex_prueba_*.json`. `[INFERRED]` the author's reasoning or arithmetic
projection. `[PROPOSED]` a suggestion. Token counts are provider counters, not a billing
reconciliation. Character counts are JSON lengths of captured fields.

**Constraints kept.** Five roles, both review phases, objective source/scope/quote/arithmetic
gates, manager/date scope, partial-release controls and replay of saved versions. No proposal
adds language-pattern or case-specific wording rules. Contract changes that need a user decision
are named as such.

## 1. Scope and method

- **Runs.** 42 workflow logs with at least eight usage-counted calls, 2026-10-21 to 2026-10-31:
  Luna (`apinex_test`), Gemini, DeepSeek. Runs before 12 mostly lack usage counters; the four
  October 21-22 logs that have them are included by log ID. Smaller logs (probes, rechecks,
  configuration errors) are excluded.
- **Attribution.** Each `model_response_usage` is assigned to the agent of the preceding
  `model_started`; ZeroSugar calls are split by the current `review_phase_started` phase.
- **Captures.** Full prompt captures exist from run 30 onward. Component sizes below come from
  runs 30, 35 and 52.
- **Rejections.** Entries in `rejected_attempts` (top level and per review round), grouped by
  failure family. Counts are approximate: early runs kept fewer diagnostics, and an entry may
  appear in both the summary and a review round.
- **Periods.** "Before" is runs through 2026-10-27 (through run 32); "after" is from 2026-10-28
  (run 35 onward), when the C1 shared reliability update entered. The boundary is a date, not a
  proven cause.

## 2. Where the tokens went, all runs

### 2.1 Period comparison `[OBSERVED]`

| Period | Runs | Complete | Median input | Median calls | Input per call | Median review rounds | Runs with a truncated call | Original / ZS support / Vanilla share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Through 2026-10-27 | 25 | 7 | 111k | 15 | 8.5k | 1 | 1 | 36% / 38% / 17% |
| From 2026-10-28 | 17 | 0 | 299k | 18 | 17.0k | 2 | 8 | 54% / 33% / 11% |

Calls per run barely changed (15 to 18). **Input per call doubled**, and the median number of
review rounds went from 1 to 2. Truncated responses, which buy nothing, appeared in 8 of 17 later
runs and consumed about 211k input tokens across them.

### 2.2 Per run `[OBSERVED]`

Input tokens by agent. "ZS compl." includes the single-phase review of the October 21-22 logs.
"Support calls/phases" shows retries: more calls than phases means rejected or truncated
attempts. Runs 12-29 are identified from their logs as listed in
[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).

| Run | Profile | Status | Calls | Input | Original | Vanilla | ZS compl. | ZS support | Rounds | Support calls/phases | Truncated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| log 20261021_151118 | Luna | partial | 18 | 142k | 59k | 28k | 55k | 0k | 0 | 0/0 | 0 |
| log 20261021_182928 | Luna | failed | 17 | 115k | 51k | 64k | 0k | 0k | 0 | 0/0 | 0 |
| log 20261021_233751 | Luna | partial | 12 | 69k | 23k | 14k | 32k | 0k | 0 | 0/0 | 0 |
| log 20261022_185013 | Luna | complete | 9 | 48k | 15k | 14k | 19k | 0k | 0 | 0/0 | 0 |
| 12 | Luna | failed | 12 | 64k | 15k | 15k | 2k | 32k | 1 | 3/1 | 0 |
| 13 | Luna | partial | 14 | 73k | 40k | 14k | 10k | 8k | 2 | 1/1 | 0 |
| 14 | Luna | failed | 12 | 78k | 13k | 15k | 6k | 45k | 1 | 3/1 | 0 |
| 15 | Luna | failed | 13 | 69k | 12k | 15k | 9k | 33k | 1 | 3/1 | 0 |
| 16 | Luna | complete | 15 | 106k | 45k | 22k | 5k | 34k | 2 | 3/2 | 0 |
| 17 | Luna | complete | 9 | 47k | 14k | 17k | 3k | 14k | 1 | 1/1 | 0 |
| 18 | Luna | complete | 27 | 260k | 63k | 25k | 13k | 160k | 4 | 10/4 | 0 |
| 19 | Luna | partial | 23 | 269k | 84k | 14k | 11k | 161k | 4 | 9/4 | 0 |
| 20 | Luna | failed | 11 | 50k | 14k | 25k | 10k | 0k | 1 | 0/0 | 0 |
| 21 | Luna | partial | 26 | 281k | 117k | 16k | 11k | 137k | 4 | 8/4 | 0 |
| 22 | Luna | complete | 10 | 57k | 15k | 26k | 3k | 13k | 1 | 1/1 | 0 |
| 23 | Luna | partial | 26 | 295k | 123k | 17k | 17k | 138k | 4 | 8/4 | 0 |
| 24 | Luna | partial | 22 | 226k | 130k | 26k | 18k | 52k | 3 | 3/2 | 0 |
| 25 | DeepSeek | failed | 21 | 161k | 75k | 83k | 3k | 0k | 1 | 0/0 | 0 |
| 26 | Gemini | complete | 14 | 111k | 47k | 17k | 5k | 42k | 2 | 3/2 | 0 |
| 27 | Luna | failed | 11 | 88k | 25k | 14k | 3k | 46k | 1 | 3/1 | 0 |
| 28 | DeepSeek | failed | 25 | 216k | 75k | 17k | 23k | 100k | 3 | 6/2 | 0 |
| 29 | Gemini | failed | 11 | 87k | 24k | 14k | 3k | 47k | 1 | 3/1 | 0 |
| 30 | Luna | complete | 18 | 193k | 64k | 17k | 6k | 107k | 2 | 6/2 | 0 |
| 31 | DeepSeek | failed | 32 | 372k | 130k | 16k | 8k | 170k | 4 | 9/3 | 0 |
| 32 | Gemini | failed | 18 | 156k | 26k | 75k | 3k | 52k | 1 | 3/1 | 1 |
| 35 | Luna | failed | 18 | 309k | 184k | 25k | 14k | 85k | 4 | 4/4 | 1 |
| 36 | Gemini | partial | 25 | **828k** | **704k** | 25k | 12k | 87k | 3 | 4/3 | 0 |
| 37_resume_1 | Gemini | partial | 11 | 131k | 57k | 26k | 7k | 41k | 2 | 2/2 | 1 |
| 38 | Luna | failed | 12 | 138k | 88k | 28k | 3k | 19k | 1 | 1/1 | 1 |
| 39 | Gemini | partial | 9 | 107k | 57k | 26k | 4k | 21k | 1 | 1/1 | 1 |
| 40 | Luna | partial | 25 | 483k | 209k | 26k | 15k | 233k | 4 | 10/4 | 0 |
| 41 | Luna | partial | 20 | 299k | 122k | 26k | 15k | 136k | 4 | 6/4 | 0 |
| 42 | Gemini | failed | 10 | 117k | 24k | 26k | 4k | 64k | 1 | 3/1 | 0 |
| 44 | Gemini | partial | 25 | 432k | 206k | 26k | 15k | 185k | 4 | 8/4 | 2 |
| 45 | Luna | partial | 24 | 434k | 235k | 26k | 15k | 158k | 4 | 7/4 | 0 |
| 46_network | Gemini | failed | 8 | 90k | 64k | 26k | 0k | 0k | 0 | 0/0 | 0 |
| 47_network | Luna | partial | 24 | 369k | 155k | 45k | 12k | 157k | 4 | 8/4 | 1 |
| 48 | Gemini | failed | 11 | 159k | 110k | 26k | 4k | 20k | 1 | 1/1 | 0 |
| 49 | Gemini | partial | 20 | 327k | 153k | 29k | 12k | 134k | 3 | 5/3 | 0 |
| 50 | Luna | failed | 13 | 128k | 27k | 89k | 12k | 0k | 1 | 0/0 | 0 |
| 51 | Gemini | partial | 19 | 324k | 212k | 27k | 8k | 78k | 2 | 3/2 | 1 |
| 52 | Luna | partial | 16 | 270k | 44k | 27k | 8k | 192k | 2 | 7/2 | 1 |

### 2.3 Four drivers, multiplied

Workflow input is roughly (size per call) × (review rounds) × (attempts per round). All three
factors grew; truncation adds waste on top.

**D1. Per-call size doubled at the 2026-10-28 boundary** `[OBSERVED]`. Captured characters
(instructions / history / tool schema):

| Call | Run 30 (10-27) | Run 35 (10-28) | Run 52 (10-31) |
| --- | --- | --- | --- |
| Original, first draft | 11k / 22k / 1k | 32k / 20k / 7k | 27k / 30k / 4k |
| Original, first repair | 11k / 54k / 2k | 41k / 62k / 9k | 30k / 17k / 5k |
| Vanilla, classification | 13k / 12k / 3k | 23k / 12k / 5k | 25k / 14k / 5k |
| ZeroSugar support, first attempt | 15k / 35k / 4k | 16k / 38k / 16k | 18k / 43k / 19k |

In provider tokens: Original's first draft call went from 9-10k (runs 17, 22, 30) to 18-25k;
the first support call from 13k to 19-25k; Vanilla's total per run from a median of 17k to
25-29k in every later run without a Vanilla loop, a fixed increase of about 10k. The growth is in instructions and tool schemas, not in
case data. The timing matches the C1 contract (reference-based blocks, edit schema, excerpt
catalogs, keyed per-finding review schema), as section 7 of the Luna audit already noted; that C1
is the cause is inferred from timing and content.

One reduction is visible: A8 (2026-10-29) cut Original's repair history from 54-62k characters
(runs 30, 35) to 17k (run 52). The remaining repair bulk is instructions (27-30k), not history.

**D2. More review rounds** `[OBSERVED]`. Every run above 400k used four rounds (40, 44, 45) or
an Original loop (36). One round now costs about 45-60k input (Original draft or repair, both
review phases); four rounds alone approach 200-240k. The four-draft cap is a user decision (A15
and the 2026-10-26 recovery update), so this analysis does not propose changing it; it proposes
measuring whether rounds 3-4 improve a candidate (O4, O6).

**D3. Failing retry loops resend a growing history** `[OBSERVED]`:

| Run | Loop | Cost |
| --- | --- | --- |
| Gemini 36 | Original, 15 calls growing to 64k each (seven `narrative_count` rejections) | 704k, 85% of the run; the most expensive run on record |
| Gemini 51 | Original, seven `answer_removal_reasons` rejections, 18k to 29k per call | 170k, 52% |
| Luna 52 | Support on the second candidate, 27.6k to 33.7k per call | 121k, 45% |
| Luna 40 | Support, 10 calls over four phases | 233k support |
| Luna 50 | Vanilla, 89k (69% of the run) before the completeness double-call failure | 89k |
| Gemini 32, DeepSeek 25 | Vanilla, 8 calls / 75k and 83k | 75-83k |

Within one phase the history grows each retry: Original 4 to 16 messages in 51, support 1 to 7
messages and 52.9k to 89.9k characters in 52 (both revision 1 measurements, unchanged). Vanilla
loops were absent from revision 1, which called Vanilla "small and fine".

**D4. Truncated support attempts** `[OBSERVED]`. One run before 10-28 (Gemini 32) versus eight
after (35, 37_resume_1, 38, 39, 44 twice, 47, 51, 52), about 211k input tokens in total. The
compact retry (A6/A7) recovers the phase but the first attempt is always paid.

**Measurement caveat** `[OBSERVED]` for 51/52. Every call reports `reasoning_tokens` equal to
`output_tokens` minus one and no cached-token field, so reasoning versus visible output, and
whether prefix caching applies, cannot be measured from these counters.

## 3. What fails, across all runs

### 3.1 Rejection families `[OBSERVED]`, approximate

| Family | Agent | Entries | Runs | First / last seen | Still live? |
| --- | --- | --- | --- | --- | --- |
| Excerpt or quote not from the cited source; proposal quote | Original | 37 | 21 | run 7 / Gemini 49 | Yes |
| Correction link, refinement state, duplicate, consolidation | ZeroSugar | 42 | 11 | run 12 / Luna 52 | Yes; under every review contract since run 12 |
| Citation not in the finding's subset | ZeroSugar | 29 | 8 | run 30 / Luna 47 | Not in 48-52; cause not established |
| Free-form text instead of the answer tool | Original 23, Vanilla 4 | 27 | 19 | run 13 / Luna 47 | Not in 48-52; cause not established |
| Every finding exactly once | ZeroSugar | 17 | 10 | run 7 / Gemini 32 | **No: 0 since the keyed schema (run 35)** |
| Literal assertion coverage (review-v4) | ZeroSugar | 15 | 3 | runs 27-29 | No; retired by review-v5 |
| Narrative capacity (`narrative_count`) | Original | 7 | 1 | Gemini 36 | No; A1/A2 |
| Removal reasons | Original | 7 | 1 | Gemini 51 | One run so far |

### 3.2 What earlier fixes show

- **Worked, and must not be undone.** The keyed per-finding support schema
  (`bind_finding_schema`, [zero_sugar.py:462](agents/zero_sugar.py:462)) coincides with the end
  of "every finding exactly once" (17 entries in 10 runs before, 0 after). A1/A2 ended the
  narrative-capacity loop. A8 cut repair history.
- **Did not end the family.** Correction-link errors survived review-v1 through v7, A17/A18
  joint reporting and localized feedback. Excerpt/source errors survived the C1 reference-based
  excerpts and the 10-31 localization. A fix aimed at the last observed code has repeatedly
  moved the failure to a neighbouring code.
- **Never exercised.** Original's `challenge_corrections` tool was offered in 57 captured
  requests (runs 35-52) and called in none: no `correction_challenge_completed` event exists in
  any of the 394 logs. Proposals that rely on the challenge path start from zero live evidence.
- **Revision 1 prioritized the last failure.** Its first contract item (O1/X3) targets a family
  seen in one run, while the two most widespread families (Original excerpt/source, ZeroSugar
  correction link) had no dedicated item. That is the pattern the evaluation criticizes ("tests
  follow the last failure").

## 4. Cross-cutting changes

| ID | Change | Status | Score effect | Token effect `[INFERRED]` |
| --- | --- | --- | --- | --- |
| X1 | Joint validation: `resolve_corrections` collects the duplicate instead of raising, reported with refinement and finding errors (audit P1.1) | Extends A17/A18/A20; only this serial path remains | ZeroSugar C4 | Luna 52: joint reporting surfaces both errors on attempt 1, so the earliest success is attempt 2, which would skip 64,961 tokens (24%); skipping 93,721 (35%) would need success on attempt 1, which X1 cannot provide. Neither is an achieved saving: a successful review leads to further work the failed run never reached. **No effect on Gemini 51**: its seven rejections were one code; revision 1's 130k figure belongs to P1.2/O1 and assumes they work on retry 2 |
| X2 | Delta retries inside a phase: resend the last submission and the localized error, not the whole growing history | New for within-phase retries; A8 already covers cross-round repair context | C6 everywhere | Caps retry cost near the first-attempt size; touches D3 in every loop above |
| X3 | One `removals` list (audit P2.6) | Contract decision; see O1 | Original C4 | Small in history (one run) |
| X4 | Per-component input budget reported per run (planning, specialist, draft, completeness, support, repair), with an agreed ceiling | New | System C6, C7 | Would have flagged the 10-28 doubling on its first run |
| X5 | Offline fixtures replayed from real captures, **one per still-live family in 3.1**, not only the 51/52 turn-1 payloads | Extends audit P1.5 | System C7 | Prevents live runs that fail on known contracts |
| X6 | Stable static prefix first, dynamic data after; check whether the gateway supports prefix caching | New | C6 | Unknown until measured (caveat in 2.3) |
| X7 | Attribute the 10-28 fixed-size growth component by component (catalogs, edit schema, keyed review schema, Vanilla classification instructions) and set a size target for each | New; covers O2, V5 and Z2 | C6 for Original, Vanilla, ZeroSugar | Returning per-call size from 17k to the earlier 8.5k at equal calls would roughly halve a run; an upper bound, not a forecast |

X1, X2, X4, X5 and X7's measurement are system changes. X3 changes the answer contract.

## 5. Per agent

### 5.1 ZeroSugar (4.4)

Weakest criteria: C4 2, C5 2, C6 2, C3 5.

| ID | Change | Status | Criteria | Notes |
| --- | --- | --- | --- | --- |
| Z1 | Reason text only for assertions judged not supported; supported ones return judgment and source subset | New | C6, C4 | Today `reason` is required for every assertion ([zero_sugar.py:334-335](agents/zero_sugar.py:334)). Targets D4, which hit eight runs since 10-28 |
| Z2 | **Changed.** Keep the keyed per-finding schema and its per-finding citation enums; shrink only repeated text inside it (descriptions copied per finding), after checking which schema features each provider accepts | Changed | C6 | Revision 1 proposed a generic array. History in 3.2: the keyed schema coincides with the end of a 17-entry family. A generic array saves characters and probably brings that family back |
| Z3 | Derive linked-correction state | **Withdrawn** (Addendum A.2) | C4 | See Z9 |
| Z4 | Reviewer-only reassessment of one disputed objection instead of a full redraft and two reviews | **Changed:** first find out why `challenge_corrections` was never called in 57 offers (instruction, conditions, tool competition), using captures | C4, C6 | The existing path has no live evidence (3.2); scoping it is premature |
| Z5 | False-objection and missed-defect rates with the nine-case instrument, reviewer-only, both providers | Unchanged | C5, C3 | The cheapest way to move C5 |
| Z6 | A/B comparison of a reviewer from another model family, after Z5 | Experiment (Addendum A.1) | C3, C5 | A hypothesis, not an improvement |
| Z7 | Absence objections against code-rendered canonical blocks as structured IDs, checked against IDs present (P3.8) | Limited (Addendum A.1) | C5, C2 | Removes only an absence ground; certifies neither labels nor interpretation |
| Z8 | Rating rationales | **Changed:** review-v7 already requires structured `rating_explanations` with bounded repair. The 31% one-character figure predates v7. Measure v7 explanations (seven delivered in three completed reviews of 51/52) and their repair cost before any change | C3, C6 | No new change proposed now |
| Z9 | Correction-link family: build fixtures from every capture of it (runs 30-52), then decide Addendum A.2 option 2 (link as informational lineage) with that evidence | New | C4 | The longest-lived ZeroSugar failure (42 entries, 11 runs, runs 12-52). Encoding changes alone have not ended it |
| Z10 | Citation-subset family: find out why it occurred with per-finding citation enums (29 entries in runs 30-47) and why it stopped | New, measurement | C4, C7 | If providers do not enforce enums, schema constraints are not a reliable guard `[INFERRED]` |

### 5.2 Original (4.7)

Weakest criteria: C6 2, C4 3, C1 4, C5 4.

| ID | Change | Status | Criteria | Notes |
| --- | --- | --- | --- | --- |
| O1 | One `removals: [{block_id, reason}]` list replacing `remove_ids` + `removal_reasons` (P2.6) | Contract decision; lower priority than O7/O8 | C4, C2 | Duplicate, identity and preservation checks remain. The declarative-list variant is rejected: an omitted block would become a silent deletion (run 47). Seen in one run |
| O2 | Reduce what each Original request carries: a compact ID index instead of full catalog entries, and in repairs only the entries the open corrections cite; full entries still available through existing tools | Changed (revision 3) | C6 | Instructions went from 11k to 27-41k characters at 10-28 and are now most of a repair call (2.3). Revision 1's "send once as a tool result" saves nothing: models are stateless and a tool result stays in the history resent with every later call. Only smaller content, or provider prefix caching (X6), lowers input |
| O3 | Repair packet limited to open corrections, affected blocks and their sources | **Largely implemented as A8** | C6, C4 | History fell from 54-62k to 17k characters. What remains is O2 (instructions) and X2 (within-repair retries) |
| O4 | Score each draft against a fixed checklist outside the system | Unchanged | C5 | Answers whether rounds 3-4 help (D2) |
| O5 | Score planning apart from synthesis, not as a new role | Unchanged | C1 | Planning costs about 2-3k per run |
| O6 | Fixed repair cases: saved candidate plus a legitimate correction, repair scored against a checklist | Unchanged (Addendum A.4) | C4, C5 | No instrument measures whether an Original repair improves a candidate |
| O7 | Excerpt/source family: fixtures from its captured occurrences (DeepSeek 31, Gemini 32/44/46/48/49, Luna 38/40/45/47); measure whether a selected excerpt can be offered by reference only | New | C4, C2 | The most widespread Original failure (37 entries in 21 runs), not covered in revision 1 |
| O8 | Free-form output instead of the answer tool: check per provider whether the tool requirement reaches the request on every answer turn | New, system check | C4 | 23 Original entries in 16 runs, through run 47. Cause not established `[INFERRED]` |

E7/E8 (duplication instead of consolidation; prose contradicting stored labels) stay with
review and measurement (O4, O6), not new wording rules.

### 5.3 Vanilla (6.8)

Weakest criteria: C1 5, C5 6.

| ID | Change | Status | Criteria | Notes |
| --- | --- | --- | --- | --- |
| V1 | Score the classifier and the retrieval/interpretation path separately | Unchanged | C1, C5 | Evaluation change only |
| V2 | Human-labelled sample covering every category; per-category precision and recall | Unchanged | C5 | CMT27512 positive in Luna 52, mixed in Gemini 51 |
| V3 | A run with more than 20 comments to exercise multi-batch and retries | Unchanged | C4, C7 | The case always uses one batch |
| V4 | Check whether the second `search_text` turn adds information that Original then rewrites | Unchanged, measure first | C6 | `[INFERRED]` |
| V5 | Classification instructions grew from 13k to 23-25k characters at 10-28; identify what was added and whether Vanilla needs it | New (part of X7) | C6 | About 10k fixed tokens per run since run 35 |
| V6 | Vanilla loops in Gemini 32, DeepSeek 25 and Luna 50 (75-89k each): classify their rejection codes from the captures where available | New | C4, C6 | Absent from revision 1 |

### 5.4 Cherry (7.3)

Weakest criteria: C5 5, C4 6. Among the 42 logs, Cherry was called only in DeepSeek 31 (47k).

| ID | Change | Criteria | Notes |
| --- | --- | --- | --- |
| K1 | Three or four numeric questions with gold answers, five runs each, on current code | C4, C5 | Evidence only; also the only way to see regressions in the numeric path since October 21 |
| K2 | Measure the rate of SQL that executes but answers a different question | C5 | Known, unmeasured risk |
| K3 | Extend the metric catalog for the questions above | C5 | Catalog metrics are replayed by ZeroSugar |

### 5.5 Lime (5.9)

Weakest criteria: C4 3, C5 3.

| ID | Change | Criteria | Notes |
| --- | --- | --- | --- |
| L1 | One live run that plans and exports a chart, inspected by a person | C4, C5 | The gap is evidence, not design |
| L2 | Sentiment chart through a verified derived table from Cherry | C4 | Lime cannot chart this case's main output today |

### 5.6 System (4.7)

Weakest: C4 2, C6 2, C5 3; beyond the agents, quality validation 2, process and change
management 3, testing strategy 4 (evaluation 9.1). Revision 1 had no system section.

| ID | Change | Criteria | Notes |
| --- | --- | --- | --- |
| S1 | Measurement freeze: no contract-version change during a measurement series, so repeated runs compare like with like | C4, C5, process | v1-v7 in ten days confounds every comparison (evaluation 12) |
| S2 | Offline gate green and the X5 capture fixtures passing before every live run | C7, testing | The 343-412 tests passed throughout the live failures |
| S3 | External checklist for completion, separate from Echo's reviewer (evaluation 11) | C5, quality validation | Required for the System-to-7 criterion |
| S4 | X4 budget per component with a stop or warning when a component exceeds it | C6 | Turns D1 into a visible regression |

## 6. How the scores can move

Criteria C4 and C5 (40% of every score) are scored from live and benchmark evidence. **No code
change moves them by itself**; they move only after new measured runs on the changed code.
Revision 1's "C4 2 to 5 with X1/X2/Z1/Z2 alone" is withdrawn as a statement about scores.

| Criterion | What can raise it | Items |
| --- | --- | --- |
| C6 Efficiency (Original, ZeroSugar, System) | Smaller per-call size and fewer failing retries, shown in a fresh measured run | X2, X7, O2, V5, Z1, Z2, X4 |
| C4 Observed reliability | Fewer protocol stops on the still-live families, shown in repeated runs | X1, X5, O7, O8, Z9, Z10, S1, S2 |
| C5 Output-quality evidence | Independent measurement | Z5, O4, O6, V2, K1, L1, S3 |
| C3/C7 | Replayable fixtures and component budgets | X4, X5, Z10 |

The exit criteria in section 11 of the evaluation remain the targets.

## 7. Order and expected effect

| Step | Items | Kind | Effect `[INFERRED]` |
| --- | --- | --- | --- |
| 0 | X5 fixtures for every still-live family; X4 and X7 measurements | Measurement, offline | Baseline of sizes and known failures before any change |
| 1 | X1, X2, O8, Z10 | System only | Fewer protocol stops and cheaper retries (D3) |
| 2 | O2, V5, Z2 (as changed), Z1 | Payload shape | Addresses D1 and D4 |
| 3 | Z9 decision with fixture evidence; O1/X3 | Contract decisions | The longest-lived family first; removal reasons after |
| 4 | Z5, O4, O6, V2, K1, L1, S3 | Quality measurement, under S1 | The only way to raise C5 |
| 5 | Z4 (after its root cause), Z6, Z7, X6, V4 | After measurement | Depend on step 4 results or gateway capabilities |

**Not recommended:** more instruction text; more retries or larger output caps without Z1;
wording rules for false objections; replacing the keyed review schema; more full live workflows
before steps 0-2 and 4.

**Projection** `[INFERRED]`. For a run like the later median (299k, 18 calls): returning
per-call size to the pre-10-28 level would bound it near 150k; removing a truncated first support
attempt saves 20-25k more; ending one failing loop of the 51/52 kind earlier skips about
65k (Luna 52, success on support attempt 2) to 131k (Gemini 51, success on repair retry 2,
skipping 130,725). These overlap and are bounds from past runs, not a measurement or an
achieved saving: a workflow that gets past the loop spends tokens on work the failed run never
reached. A fresh measured run on changed code is required.

## 8. Changes from revision 1

- Evidence widened from runs 51/52 to 42 workflow logs (all profiles), with a period comparison,
  a per-run table, rejection families and the effect of earlier fixes.
- New drivers: per-call doubling at 10-28 (D1), review rounds (D2), Vanilla loops and Gemini 36
  (D3), truncation across eight runs (D4).
- X1: scoped to the remaining serial path; Gemini 51 saving re-attributed to P1.2/O1.
- X5 widened to every still-live family; X7 and S1-S4 added.
- Z2 reversed (keep the keyed schema); Z4 now starts with why the challenge was never called;
  Z8 replaced by measurement of v7 explanations; Z9, Z10 added.
- O3 marked as largely implemented (A8); O7, O8 added; O1 lowered in priority.
- V5, V6 added. Cherry items renamed K1-K3.
- Section 6 added; the claim that code changes alone raise C4 is withdrawn.
- Revision 3: X1 Luna 52 saving corrected from about 94k to 64,961 (attempt 2); section 7 loop
  range corrected from 90-170k to about 65-131k; O2's tool-result reasoning withdrawn.

## 9. Limits

- One case (13 comments, M14/Q3); one run per code version, mostly; code, contract and reviewer
  changed together, so no single change's effect is isolated.
- Attribution by the preceding `model_started` assumes calls are sequential, which the logs show.
- Rejection counts are approximate (section 1). "Still live" means seen in runs 48-52 or not.
- Captures were read for sizes only (runs 30, 35, 52), not for content; no label, answer or
  verdict was re-judged.
- Token figures are provider counters; character sizes are not tokens (roughly 3-4 per token).
