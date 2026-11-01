# Independent audit of the Luna live runs through run 50, 2026-10-31

Read-only audit of the saved report JSON, execution logs, private exchange captures and the
existing audit documents. No runtime change, test execution, model request or publication was
performed. Figures were computed directly from the artifacts; where a figure is an inference it
is labelled as such. This audit is read beside, and does not edit, `AUDIT_2026-10-28.md`,
`AUDIT_2026-10-29.md`, `AUDIT_2026-10-30.md`, `AUDIT_2026-10-31.md` (Addenda D-F),
`RUNS_49_50_ANALYSIS.md` and `ADDENDUM_E_COMPARISON.md`.

## 1. Scope, method and limits

**Scope.** All Luna (`free/gpt-6-luna`, profile `apinex_test`) artifacts: `apinex_prueba_media*`
and `apinex_prueba_vanilla_5` to `_50`, with matching `reports/logs/*.jsonl`. Gemini and DeepSeek
runs are used only as contrast. Run 51 and the 51/52 pair are outside the requested range.

**Method.** (a) Status, call, review and failure fields of every report JSON; (b) rejection
diagnostics (`diagnostics.rejected_attempts`, `review_history`); (c) per-comment sentiment labels
from `sentiment.*.labels`; (d) per-call token usage from the JSONL logs; (e) input section sizes
from `reports/logs/details/<run>/exchanges.jsonl` for runs 30, 45 and 50.

**Limits.**
- n = 1 per code identity, and the code changed between nearly every run. Percentages are
  descriptive, not estimates of a true success rate.
- Rejection diagnostics are absent or minimized for early runs, so rejection counts are minimums.
- Private exchanges exist only from run 30 onward; the character sizes in section 7 come from three
  runs. Characters are not tokens (roughly 3-4 characters per token).
- Semantic label quality was not re-judged. "Stable" below means identical across runs, not correct.

## 2. Outcomes

Of 38 Luna artifacts, five were excluded as unusable for quality evaluation: four
provider-connection failures with zero successful calls (`media_corregida` and the three run-47
attempts before the network-enabled retry) and one code crash before any analysis (run 33,
`KeyError('quote')`). That leaves **33 evaluable runs**:
**7 complete (21 %), 12 partial (36 %), 13 failed (39 %), 1 needs_clarification (3 %).**

| Period (code era) | Evaluable runs | Complete |
| --- | --- | --- |
| Through run 14 (no review recovery) | 14 | 2 (media_4, 11) |
| Runs 15-24 (review-v2/v3) | 10 | 4 (16, 17, 18, 22) |
| Runs 27-30 (assertion review v4/v5) | 2 | 1 (30) |
| Runs 35-50 (after C1, delivery repairs, review-v6/v7 work) | 7 | **0** |

No Luna run has completed since run 30, and no Gemini run since run 26. The cause cannot be
isolated because code, contract version and reviewer all changed together, but the direction is
unambiguous: contract complexity and cost rose while completion fell.

"Complete" is not "correct". Run 11 was marked complete, yet its answer contains no quotation
characters although the question required a literal positive and critical excerpt (verified in the
saved answer). Runs 16 and 22 were also accepted with the content problems recorded in
`LIVE_TEST_HISTORY.md`. Seven completions are therefore an upper bound on correct outputs.

## 3. What was done well

1. **Classification is stable.** Comparing the labels of the 13 comments across 40 runs and three
   models, 12 comments have the same label in every run. Only CMT27512 varies (positive 23 times,
   mixed 17; in Luna 17 and 10). The text is genuinely ambiguous. Source hashes, coverage and
   aggregates reproduced in every run. The sentiment path is not the main source of failure.
2. **Objective gates work.** Source, scope, literal-quote and arithmetic checks held. In run 49 a
   swapped-label draft was not released.
3. **Partial release is honest.** Run 37 released 9 supported findings and withheld 6. Unsupported
   output was never presented as approved.
4. **Evidence handling is exemplary.** Full private capture, input-bound checkpoints, strict
   identity checks and dated, self-correcting audits make failures reproducible.
5. **Case-specific rules were removed.** Rubric v3 leaves interpretation to the model.

## 4. What went wrong, and why the errors persist

1. **The failure is a long tail, not a bug.** Retained rejections across Luna runs fall into 25
   distinct codes; the largest (`grounded_answer_required`) accounts for 17, `assertion_citations`
   for 12, `correction_replacement` for 9. The dominant code changes with the era
   (`review_fields` in runs 14-15, `correction_replacement` in 18-21, `assertion_citations` in
   40-50). Each repair removes the observed failure and the surface produces another, because the
   surface (review-v1 to v7, assertions, obligations, correction lifecycle, edit and reference
   schemas) keeps growing. Run 50 ended on a different failure again: three completeness responses,
   each with two distinct tool calls despite `parallel_tool_calls=false`.
2. **The repair loop cannot converge by design.** Audit 29 (Parts E-F) showed that in run 40 each
   repair fixed one duplication and created another, and that a valid fourth review would still have
   ended `partial` because `MAX_DRAFTS` is 4. Repairing the rejection message would not have changed
   the outcome.
3. **The reviewer is unreliable in both directions.** False accept: run 11. False rejects and
   contradictions, per Audit 31 D.7: a scope objection in 4 of 4 rounds despite supplied
   `authorized_scope`; assertions judged contradicted with reasons stating the opposite;
   one-character rating rationales (9 blocks in run 47, 3 in run 48); assertions attributed to text
   absent from the block.
   Structural incentive: a `revise` verdict without a correction is rejected
   (`zero_sugar.py:1461`), so a reviewer that wants to block must attach an obligation, and
   obligations accumulate (3/6/9/12 in run 21).
4. **The gate is all-or-nothing over free text.** One false objection among roughly 13 findings with
   several assertions each prevents `complete`. (Reasoning, not measured.)
5. **Changes shipped unverified.** Several updates (2026-10-26 to 28) were applied without tests by
   instruction. Audit 28 measured 91 red tests against a documented "322 passed"; the C1 update was
   followed by the run 33/34 `KeyError`. Run 30, the last completion, predates C1.
6. **Tests follow the last failure.** The offline suite (343 to 392 tests) validates contracts with
   scripted responses; A19, A20 and A21 were never triggered live. Green tests coexisted with red
   live runs throughout.
7. **A candidate is discarded when review fails.** In run 50 an unreviewed 3,771-character candidate
   with the table and 13 stored labels existed; the manager received only "No verified answer was
   produced" and "No analysis was produced" (S3 in `RUNS_49_50_ANALYSIS.md`). This is a stated
   project policy, but it makes every reviewer-protocol failure a total loss.

## 5. Contrast with the second auditor

**Agreement.** The system-versus-model separation rule; the run 48 finding that a safety score of 2
with a one-character rationale withheld 11 supported findings; the finding that run 40 could not
converge; the correction of earlier readings in each addendum.

**What this audit adds.** Success rate by code era; the long-tail rejection distribution; the
stability of classification (which moves the focus from analysis quality to reviewer and contract);
the cost trend (section 7); and the gap list in section 6.

**Disagreement of strategy.** The audit series proposes A1-A46, each repairing an observed mechanism.
That is the strategy that produced seven contract versions without raising the completion rate. Audit
29 Part F already concedes that repairing a rejection would not change the outcome; the plan
nevertheless continues at the rejection level.

## 6. What the new tests and the audits have not observed

The following would be required to reach, and to know that the system reached, a correct output.

1. **An independent definition of "correct".** There is no gold answer or fixed checklist. For this
   case a harness outside the runtime could check mechanically: five-category table, denominator 13,
   two literal excerpts that occur in the sources, two team questions, no respondent identification.
   Today "correct" means "accepted by the same system's reviewer" or "read by an auditor".
2. **Reviewer accuracy.** No one has measured ZeroSugar's false-accept and false-reject rates by
   feeding it known-good and known-bad candidates repeatedly. The nine controlled review cases and
   scorer added in v7 exist, but their provider accuracy is recorded as unmeasured. This is the most
   important component and its error rate is unknown.
3. **A ceiling test.** Nobody has given the reviewer a human-written ideal answer to see whether it
   accepts. If it does not, no amount of generator repair can succeed. Audit 29 Part F suggests this
   may already be the situation.
4. **Repetition and variance.** Same code, same case, five or more runs, with a completion rate and
   interval. Differences between runs 40, 41 and 45 cannot currently be separated from noise.
5. **Per-draft quality.** Nobody scores draft 1, 2, 3 and 4 against the same checklist. Observed
   oscillation (run 40) and lost content (run 23) suggest later drafts can be worse, in which case the
   iteration costs tokens and reduces quality.
6. **A baseline without review.** No run isolates how good the first candidate is, nor what the two
   review phases add per token.
7. **Objection precision.** Audit 31 D.7 checked one run by hand. The fraction of reviewer
   corrections that are valid, per run, has never been tabulated; it is the quantity that explains
   the persistent `revise`.
8. **Breadth.** Nearly every run uses one case (M14, Q3 Recognition, 13 comments). Cherry executed in
   8 Luna logs and Lime in none; `role_skipped` appears in the runs reviewed. Numeric, chart and
   multi-dimension paths have almost no recent live evidence.
9. **Human validation.** Classification and every semantic judgment remain unvalidated by people.
10. **Real-output tests.** The suite uses scripted failures. It does not replay the distribution of
    real saved model outputs against new code, nor fuzz reviewer-like outputs.
11. **Cost as a requirement.** The 15,000-token repair target was measured, missed and then retired
    as a pass/fail criterion (U6) rather than achieved. No component has a token budget.
12. **Process control.** No gate prevents a live run from using code that has not passed the suite.

## 7. Why token use increased

**Measurement (Luna, from logs).**

| Run | Era | Calls | Input tokens | Output tokens | Avg input / call | ZeroSugar calls |
| --- | --- | --- | --- | --- | --- | --- |
| 17 | Oct 26, complete | 9 | 47k | 5k | 5.3k | 2 |
| 22 | Oct 27, complete | 10 | 56k | 8k | 5.7k | 2 |
| 18 | Oct 27, complete | 27 | 260k | 30k | 9.6k | 15 |
| 30 | Oct 27, complete | 18 | 193k | 22k | 10.7k | 8 |
| 35 | Oct 28, failed | 18 | 309k | 26k | 17.2k | 8 |
| 40 | Oct 29, partial | 25 | 483k | 36k | 19.3k | 14 |
| 41 | Oct 29, partial | 20 | 299k | 31k | 14.9k | 10 |
| 45 | Oct 29, partial | 24 | 434k | 34k | 18.1k | 11 |
| 47 (network) | Oct 30, partial | 24 | 369k | 37k | 15.4k | 12 |

For the same question, input per workflow rose 6-9x between runs 17/22 and runs 40/45, and output
tokens 4-7x. The largest single call grew from about 13k (run 22) to 43-45k (runs 35 and 40) input
tokens.

**Drivers (observed unless marked).**

1. **A larger fixed prompt resent on every call.** From the private captures (characters):
   Original instructions about 12k (run 30) versus 40-43k (run 45); Original tool schema 1-2k versus
   11-13k; ZeroSugar support tool schema 4-5k versus 16.8k. In run 45, 51k of 72k characters
   (about 70 %) of an Original call are instructions plus tool schema, independent of the case. The
   timing matches the C1 contract (reference-based blocks, edit schema, correction handling).
   That the C1 contract is the cause is an inference from timing and content.
2. **Retries resend and accumulate the whole payload.** In run 30 the three support attempts have
   history of 35k, 45k and 56k characters; a third attempt carries both earlier attempts and their
   feedback. In run 40 one phase produced three support calls of 21-22k tokens each.
3. **More review calls.** Two phases per candidate, up to four candidates, plus retries, raised
   ZeroSugar from 2 calls (run 22) to 10-14. Its share of input tokens is roughly 40-50 % of a run.
4. **Larger outputs.** Assertion-level support reviews return 2-5k output tokens per call and
   reached the 6,000-token cap in Luna runs 35 and 38 and Gemini run 37.
5. **Evidence repeated across drafts.** In run 45 a ZeroSugar support call carries 37.5k characters
   of history (evidence, claims, labels, obligations) every time it runs; an Original call after the
   Vanilla handoff carries a 19k-character tool output. Obligations accumulate and are resent.
6. **Rework with no net progress.** Repair drafts that oscillate (run 40) spend the same tokens as
   drafts that converge.

**Consequence.** Cost grew faster than any measured quality. The Luna runs that completed used
47-260k input tokens (runs 17, 18, 22, 30); none of the 300-480k runs completed. No token budget per
component exists to stop this.

## 8. Re-assessment of the agents (1-10)

Scores combine design (definition, boundaries, tools, verifiability) and observed behavior
(reliability and cost in the Luna runs). Where a score changed from the earlier documentation-only
assessment, the reason is given.

| Agent | Design | Observed | Score | Change and reason |
| --- | --- | --- | --- | --- |
| Cherry | 9 | 6 | **7** | Was 8. Cleanest definition and replayable SQL, but executed in only 8 of the Luna logs and skipped in the sentiment-only runs reviewed; evidence of its quality is thin. |
| Lime | 8 | 4 | **6** | Was 7. Never executed in any Luna log. A sound design with no live validation; cannot chart sentiment, the case's main output. |
| Vanilla | 6 | 8 | **7** | Was 5.5. Raised: classification was stable in 12 of 13 comments across 40 runs and 3 models, in about 4 calls. The dual role (retrieval/interpretation and classification) remains a design weakness; still unvalidated by people. |
| Original | 5 | 4 | **4.5** | Was 5.5. Carries the planner, synthesizer, repairer and challenger roles, and most of the input-token growth (120-234k per run). Many failures are contract adherence (25 rejection codes), not reasoning; drafts oscillate. |
| ZeroSugar | 8 | 2 | **4** | Was 5. Best concept (independent, two-phase, objective gates plus judgment) and the worst behavior: false accepts, false rejects, contradictions, protocol violations, 40-50 % of calls and tokens, same model family as the producer, and a rule that forces it to invent corrections to block. |
| System (orchestration and governance) | 7 | 3 | **4.5** | Was 5.5. Sound principles (model judges, code verifies, withhold the unsupported); zero completions since run 30, 6-9x cost, no external definition of correct, no ablation or repeated trials, unverified changes shipped. |

## 9. Recommendations

1. **Measure before changing again.** Build the external checklist harness (section 6.1), run the
   ceiling test (6.3) and measure ZeroSugar's error rates (6.2). These need no runtime change.
2. **Simplify the reviewer contract.** A minimal verdict plus corrections, with identifiers, links
   and lifecycle derived in code. Allow a clean `revise` without a fabricated obligation.
3. **Make review independent.** Use a different model from the producer, and score per-draft
   quality so iteration can stop when it stops improving.
4. **Set token budgets per component.** Slim the instructions and schemas that are resent on every
   call and avoid replaying whole histories on retries.
5. **Deliver the candidate.** When review fails, return the unreviewed candidate clearly labelled,
   keeping the withholding policy for findings presented as approved.
6. **Gate live runs on the offline suite**, and repeat a fixed configuration five or more times
   before attributing any change in outcome.
7. **Widen the evaluation** to other questions and to the numeric and chart paths.

## 10. Reproducibility

- Status table: fields `status`, `execution`, `verification`, `failure` of each
  `reports/apinex_prueba_*.json`.
- Rejection codes: `diagnostics.rejected_attempts` plus `diagnostics.review_history[*].rejected_attempts`.
- Label stability: `sentiment.<id>.labels[*].{citation_id,label}` across all runs with 13 labels.
- Tokens: `model_response_usage` events in `reports/logs/*.jsonl`, attributed to the agent of the
  preceding `model_started`; profile `apinex_test`; runs with at least 8 calls.
- Section sizes: `model_input` events in `reports/logs/details/<run_id>/exchanges.jsonl`.

Artifacts are local and ignored by Git. Nothing here approves or implements a change.
