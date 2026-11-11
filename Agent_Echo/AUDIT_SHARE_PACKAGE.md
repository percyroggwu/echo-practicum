# Echo multi-agent system: audit package for independent review

Prepared 2026-10-31 from the saved artifacts of a student practicum project (GWU, Fall 2026). This
document is self-contained. It is written so that another language model (for example Claude Opus
or ChatGPT) can review the analysis without access to the repository. Nothing here was executed
by the reviewer; all numbers were computed from saved report files and execution logs of live runs.

## 0. How to use this document

**Your task as reviewer.** Treat the analysis below as a hypothesis, not as a verdict. Challenge it.
Section 12 lists the specific questions. Please state where you disagree, which claims are not
supported by the evidence given, what is missing, and what you would do differently.

**Evidence labels used throughout.**
- `[OBSERVED]` computed by the author directly from the saved artifacts (JSON reports, JSONL logs,
  private exchange captures).
- `[AUDITOR-2]` taken from the project's existing audit documents written by a second auditor; the
  author did not re-verify it independently.
- `[INFERRED]` the author's reasoning from observations; not directly measured.
- `[PROPOSED]` a recommendation; nothing is implemented or approved.

**Limits you should keep in mind.** The sample is small (one run per code version, one test case).
The code changed between almost every run, so differences between runs are confounded. No human
labelled the data, so "correct" is never established by an independent source. Percentages are
descriptive, not estimates of a true success rate.

## 1. The system under audit

**Echo** is an HR / people-analytics prototype. A manager asks a natural-language question about
their team (for example about employee survey comments). The system answers using only data the
manager is authorized to see. It runs in a terminal and exports local files. The bundled data is
synthetic. Echo is the whole system, not an additional agent.

**Five agents (roles).** All are LLM-driven; code (Python) handles tools, validation and release.

| Agent | Responsibility |
| --- | --- |
| Original | Plans the analysis, delegates, synthesizes the final answer, proposes manager actions, and repairs the answer when the reviewer asks. |
| Cherry | Numeric evidence: read-only Text-to-SQL and a small catalog of validated metrics. |
| Vanilla | Text evidence: retrieval over comments, and full-population sentiment classification in batches of 20 (positive / negative / neutral / mixed / indeterminate). |
| Lime | Chooses supported charts from Cherry's SQL rows only; code exports SVG/CSV. |
| ZeroSugar | Independent reviewer. Two calls per candidate answer: (1) completeness, which sees only the question and the visible answer; (2) support, which sees the answer, evidence, claims, objective checks and prior corrections, with a judgment per finding and per assertion. |

**Flow.** Question and fixed scope, then Original's plan, then specialists (selected by need), then a
candidate answer, then ZeroSugar's two-phase review. If the review asks for changes, Original
revises (up to four drafts in total). Final states: `complete`, `partial`, `needs_clarification`,
`failed`. Unsupported findings are withheld; independently supported findings can be released as a
partial answer.

**Division of labour.** Models judge meaning, select and synthesize. Code dispatches tools,
computes aggregates, checks scope, citations, literal quotes and arithmetic, and applies release
rules. The project explicitly refuses to replace semantic judgment with wording-pattern rules.

**Budgets (unchanged across runs).** 32 model calls and 1000 seconds per workflow; 6000 output
tokens per call for the Luna profile; at most seven model turns per specialist loop; four drafts.

**Contract versions.** Over 10 days the answer contract (`source-facts`) went from v1 to v7 and the
review contract (`review`) from v1 to v7, with old versions kept replayable. Checkpoints hash every
agent module, so any code change makes saved workflows non-resumable.

**The test case (same in nearly every run).** Manager M14, team Data Platforms, third quarter of
2026, 13 eligible anonymous Recognition survey comments. Question:

> I'm preparing for a team check-in. Using all eligible anonymous Recognition survey comments for
> the third quarter of 2026, classify each comment as positive, negative, neutral, mixed, or
> indeterminate. Show the count and percentage in each category, including the denominator. Include
> a short literal excerpt illustrating a positive and a critical view if available, with source
> citations. Explain the main patterns and interpretation limits, and suggest two follow-up
> questions for the team. Base this analysis on comment text rather than numerical survey ratings,
> and do not identify respondents.

## 2. The test program

"Luna" is the model `free/gpt-6-luna` reached through an OpenAI-compatible gateway. Runs are
numbered in order. 38 Luna artifacts exist through run 50. Gemini (`gemini-3.8-flash`) and DeepSeek
(`deepseek-v4.1-flash`) were run through the same gateway for contrast. A run is "live": real model
calls with the real workflow. The offline suite (about 340-390 unit tests with scripted model
responses) is separate and passed throughout, including during the live failures.

**What changed after which run** (changes are applied after the run named; that run therefore does
not validate the change it motivated). Condensed from the project's history. `[AUDITOR-2]`

| Applied after | Change |
| --- | --- |
| Runs 4-9 (Oct 21) | Source-bound answer contract (v1 to v3); planning clarification rules; sentiment batching and retained progress; narrative digits made review signals, not rejections. |
| Runs 10-11 (Oct 22-23) | Coordination checklist, then retired; reviewer split into completeness and support calls. |
| Runs 12-14 (Oct 26) | Review-v2; answers v4; field-level error diagnostics. |
| Runs 15-17 (Oct 26) | Four-draft recovery; sentiment rubric v1 to v2 to v3 (general definitions); full comment context to the reviewer. |
| Runs 18-21 (Oct 27) | Contextual review fields; strict tool flags; `parallel_tool_calls=false`; review-v3 (keyed mandatory/addressed judgments). |
| Runs 22-24 (Oct 27) | Requested content versus supplementary actions; mandatory reasoned manager action. |
| Runs 25-29 (Oct 27) | Assertion-level support review (review-v4), then v5; full private capture and phase-only resume. |
| Runs 30-32 (Oct 28) | C1 update: reference-based quotes (EX_ ids), edit-based drafts, transport retries, correction challenge. Applied with no tests, by instruction. Runs 33/34 then crashed with `KeyError('quote')`. |
| Runs 33-36 (Oct 28) | Delivery repairs: answer capacity and stall detection. |
| Runs 37-38 (Oct 29) | Review field bounds and a compact truncation retry. |
| Runs 39-40 (Oct 29) | Smaller repair context; lifecycle-state feedback; all independent structural errors reported together. |
| Runs 41-42 (Oct 29) | Citation-namespace feedback; simultaneous-error handling. |
| Runs 44-45 (Oct 29) | Origin-bound assertion repair; source-facts-v5 (exact-quote presentation). |
| Runs 46-48 (Oct 30) | Review-v6 with an issue-linked safety veto; source-facts-v6. |
| Runs 49-50 (Oct 31) | Review-v7 / source-facts-v7; bounded explanation repair; fixed review-case scorer. |

## 3. Results

### 3.1 All Luna artifacts through run 50

`calls` = successful / attempted generation calls. `reviews` = completed candidate reviews (blank in
early runs that did not record it). Excluded rows have no successful analysis (connection failures
with zero successful calls, or a code crash before any analysis).

| Run | Status | Calls | Reviews | Drafts | Failure (category @ stage) |
| --- | --- | --- | --- | --- | --- |
| media | failed | 17/17 |  | 1 | invalid_review @ unrecorded |
| media_3 | needs_clarification | 1/1 |  | 0 |  |
| media_4 | complete | 9/9 |  | 1 |  |
| media_actualizada | partial | 19/19 |  | 2 |  |
| media_corregida [excluded] | failed | 0/1 |  | 0 | provider_connection @ unrecorded |
| 5 | failed | 28/28 |  | 0 | agent_turn_limit @ unrecorded |
| 6 | failed | 13/14 |  | 0 | agent_turn_limit @ unrecorded |
| 7 | partial | 18/18 |  | 2 |  |
| 8 | failed | 2/2 |  | 0 | invalid_plan @ planning |
| 9 | failed | 17/17 |  | 0 | agent_turn_limit @ answer_validation |
| 10 | partial | 12/12 |  | 2 |  |
| 11 | complete | 9/9 |  | 1 |  |
| 12 | failed | 12/12 |  | 1 | invalid_review @ verification |
| 13 | partial | 14/14 |  | 2 | invalid_review @ verification |
| 14 | failed | 12/12 | 0 | 1 | invalid_review @ verification |
| 15 | failed | 13/13 | 0 | 1 | invalid_review @ verification |
| 16 | complete | 15/15 | 2 | 2 |  |
| 17 | complete | 9/9 | 1 | 1 |  |
| 18 | complete | 27/27 | 1 | 4 |  |
| 19 | partial | 23/23 | 2 | 4 | invalid_review @ verification |
| 20 | failed | 11/11 | 0 | 1 | invalid_review @ verification |
| 21 | partial | 26/26 | 2 | 4 |  |
| 22 | complete | 10/10 | 1 | 1 |  |
| 23 | partial | 26/26 | 4 | 4 |  |
| 24 | partial | 22/22 | 2 | 3 | invalid_review @ verification |
| 27 | failed | 11/11 | 0 | 1 | invalid_review @ verification |
| 30 | complete | 18/18 | 2 | 2 |  |
| 33 [excluded] | failed | 1/2 |  |  | execution_error @ unrecorded |
| 35 | failed | 17/18 | 3 | 4 | output_token_limit @ verification |
| 38 | failed | 11/12 | 0 | 1 | output_token_limit @ verification |
| 40 | partial | 25/25 | 3 | 4 | invalid_review @ verification |
| 41 | partial | 20/20 | 4 | 4 |  |
| 45 | partial | 24/24 | 4 | 4 |  |
| 47 [excluded] | failed | 0/3 | 0 | 0 | provider_connection @ planning |
| 47 (network-enabled retry) | partial | 23/24 | 4 | 4 |  |
| 47 retry 1 [excluded] | failed | 0/3 | 0 | 0 | provider_connection @ planning |
| 47 retry 2 [excluded] | failed | 0/3 | 0 | 0 | provider_connection @ planning |
| 50 | failed | 13/13 | 0 | 1 | invalid_review @ verification |


Totals over the 33 evaluable runs `[OBSERVED]`: **7 complete (21%), 12 partial (36%), 13 failed
(39%), 1 needs_clarification (3%).**

### 3.2 Completion by period

| Period (code era) | Evaluable Luna runs | Complete |
| --- | --- | --- |
| Through run 14 (no review recovery) | 14 | 2 (media_4, 11) |
| Runs 15-24 (review-v2/v3) | 10 | 4 (16, 17, 18, 22) |
| Runs 27-30 (assertion review v4/v5) | 2 | 1 (30) |
| Runs 35-50 (after C1, delivery repairs, review-v6/v7 work) | 7 | 0 |

No Luna run has completed since run 30; no Gemini run since run 26. `[OBSERVED]` The cause cannot be
isolated because code, contract and reviewer changed together.

"Complete" does not mean correct. Run 11 was marked complete although its answer contains no
quotation characters, while the question required a literal positive and critical excerpt
(`[OBSERVED]`, checked in the saved answer). The accepted answers of runs 16 and 22 also had content
problems recorded by the project. The 7 completions are an upper bound on correct outputs.

### 3.3 Other providers (contrast)

| Run | Status | Calls | Reviews | Drafts | Failure (category @ stage) |
| --- | --- | --- | --- | --- | --- |
| DeepSeek 25 | failed | 21/22 | 0 | 1 | provider_connection @ verification |
| DeepSeek 28 | failed | 25/25 | 0 | 3 | invalid_review @ verification |
| DeepSeek 31 | failed | 32/32 | 0 | 4 | workflow_call_limit @ verification |
| Gemini 26 | complete | 14/14 | 2 | 2 |  |
| Gemini 29 | failed | 11/11 | 0 | 1 | invalid_review @ verification |
| Gemini 32 | failed | 17/18 | 0 | 1 | output_token_limit @ verification |
| Gemini 34 | failed | 1/1 |  |  | execution_error @ unrecorded |
| Gemini 36 | partial | 25/26 | 3 | 3 | agent_turn_limit @ answer_validation |
| Gemini 37 | failed | 0/1 | 0 | 0 | provider_http @ planning |
| Gemini 37 resume 1 | partial | 10/11 | 1 | 2 | output_token_limit @ verification |
| Gemini 39 | partial | 8/9 | 1 | 1 | output_token_limit @ generation |
| Gemini 42 | failed | 10/10 | 0 | 1 | invalid_review @ verification |
| Gemini 43 | failed | 0/3 | 0 | 0 | provider_connection @ planning |
| Gemini 44 | partial | 23/25 | 4 | 4 |  |
| Gemini 46 | failed | 0/3 | 0 | 0 | provider_connection @ planning |
| Gemini 46 network | failed | 8/9 | 0 | 0 | answer_delivery_stalled @ answer_validation |
| Gemini 46 retry1 | failed | 0/3 | 0 | 0 | provider_connection @ planning |
| Gemini 46 retry2 | failed | 0/3 | 0 | 0 | provider_connection @ planning |
| Gemini 48 | failed | 11/11 | 1 | 1 | answer_delivery_stalled @ answer_validation |
| Gemini 49 | partial | 20/20 | 2 | 3 | invalid_review @ verification |


## 4. What worked

1. **The classification is stable.** The labels of the 13 comments were compared across 40 runs and
   three models `[OBSERVED]`. Twelve comments have the same label in every run. Only one (CMT27512)
   varies, and its text is genuinely ambiguous. Source hashes, coverage and aggregates reproduced in
   every run. The table below shows that comment's label per Luna run.

Label of CMT27512 in the 27 Luna runs that stored 13 labels: **positive in 17** (runs 6, 9, 12, 13, 14, 16, 17, 18, 19, 23, 27, 30, 35, 38, 40, 45, 47_network); **mixed in 10** (runs 7, 10, 11, 15, 20, 21, 22, 24, 41, 50). Across Luna, Gemini and DeepSeek: positive 23, mixed 17 (40 runs through run 50). The other 12 comments never changed label in any of the 40 runs (verified). Early runs used an older rubric version (v1/v2); from run 18 onward the rubric version was constant (v3), so rubric changes do not explain the variation seen after that point.


2. **Objective gates work.** Scope, citation, literal-quote and arithmetic checks held. In run 49 a
   draft that swapped two stored labels was not released. `[AUDITOR-2]`
3. **Partial release is honest.** Run 37 (Gemini) released 9 supported findings and withheld 6;
   unsupported output was never presented as approved.
4. **Failures are reproducible.** Full private capture, checkpoints with strict identity checks, and
   dated, self-correcting audit documents.
5. **Case-specific wording rules were removed** in favour of general definitions plus model judgment.

## 5. Why the errors persist

1. **A long tail of protocol failures, not one bug.** Retained rejections across Luna runs fall into
   25 distinct codes `[OBSERVED]` (counts are minimums because early runs kept no diagnostics):

| Agent that produced the rejected submission | Validation code | Count |
| --- | --- | --- |
| Original | grounded_answer_required | 17 |
| ZeroSugar | assertion_citations | 12 |
| ZeroSugar | correction_replacement | 9 |
| Original | numeric_interpretation | 7 |
| ZeroSugar | review_fields | 7 |
| ZeroSugar | finding_coverage | 7 |
| Original | excerpt_source | 6 |
| ZeroSugar | completeness_items | 4 |
| Original | proposal_quote | 4 |
| Original | interpretation_source_not_text | 3 |
| Original | narrative_sources | 3 |
| ZeroSugar | rating_fields | 3 |
| ZeroSugar | numeric_review_coverage | 3 |
| Original | interpretation_quote_not_literal | 3 |
| ZeroSugar | correction_excerpt | 3 |
| ZeroSugar | correction_refinement_state | 3 |
| Original | interpretation_scope | 2 |
| ZeroSugar | correction_review_coverage | 2 |
| ZeroSugar | clarification_question | 2 |
| ZeroSugar | assertion_text_coverage | 2 |
| Original | answer_fields | 1 |
| Original | interpretation_quote_type | 1 |
| ZeroSugar | visible_correction_resolution | 1 |
| ZeroSugar | correction_kind | 1 |
| ZeroSugar | correction_fields | 1 |
| ZeroSugar | rating_dimensions | 1 |
| ZeroSugar | completeness_rationale | 1 |
| ZeroSugar | completeness_corrections | 1 |
| ZeroSugar | correction_policy_basis | 1 |
| ZeroSugar | correction_request_basis | 1 |
| Original | narrative_count | 1 |


   The dominant code changes with the era: `review_fields` in runs 14-15, `correction_replacement` in
   runs 18-21, `assertion_citations` in runs 40-50. Each repair removes the observed failure and the
   contract surface (review-v1 to v7, assertions, obligations, correction lifecycle, edit and
   reference schemas) produces another. `[INFERRED]` Run 50 ended on yet another failure: all three
   completeness responses contained two distinct tool calls although the request set
   `parallel_tool_calls=false`. `[AUDITOR-2]`
2. **The repair loop cannot converge by design.** In run 40 each repair fixed one duplication and
   created another because blocks persist unless explicitly removed; with a four-draft cap, even a
   structurally valid fourth review would have ended `partial`. `[AUDITOR-2]`
3. **The reviewer is unreliable in both directions.** False accept: run 11 (checked by the author).
   False rejects and contradictions: a scope objection in 4 of 4 rounds despite the authorized scope
   being supplied; assertions judged "contradicted" with reasons stating the opposite; one-character
   rating rationales (9 blocks in run 47, 3 in run 48); assertions attributed to text that is not in
   the block under review; a safety score of 2 with a one-character rationale that withheld 11
   supported findings (run 48). `[AUDITOR-2]` A structural incentive: a `revise` verdict without a
   correction is rejected by code (`zero_sugar.py:1461`), so a reviewer that wants to block must
   attach an obligation, and obligations accumulate (3/6/9/12 in run 21). `[AUDITOR-2]`
4. **The acceptance gate is all-or-nothing over free text.** One false objection among roughly 13
   findings with several assertions each prevents `complete`. `[INFERRED]`
5. **Changes shipped without verification.** Several updates (Oct 26-28) were applied with "no tests"
   by instruction. The audit of Oct 28 measured 91 failing tests where the documentation claimed 322
   passed; the C1 update was followed by the crash in runs 33/34. Run 30, the last completion,
   predates C1. `[AUDITOR-2]`
6. **Tests follow the last failure.** The offline suite validates contracts with scripted responses.
   Several repairs (A19, A20, A21) were never triggered in a live run. Green tests coexisted with
   failing live runs throughout. `[OBSERVED]` for the pattern, `[INFERRED]` for the cause.
7. **A failed review discards a complete candidate.** In run 50 an unreviewed 3,771-character
   candidate with a table and 13 stored labels existed; the manager received only "No verified answer
   was produced" and "No analysis was produced" (`[OBSERVED]`, saved report). Withholding unverified
   output is a deliberate project policy; the cost is that any reviewer-protocol failure is a total
   loss.

## 6. The second auditor's work and how this analysis relates to it

The repository holds a series of audit documents by a second auditor (Oct 28-31, about 2,700 lines),
which analyse runs 36-50 draft by draft and propose actionables A1-A46. Most were later authorized
and implemented in stages (A1-A2, A6-A8, A11-A12, A14, A16-A22, a revised A23-A31, and a
corrected "v7" plan); A3-A5, A9-A10 and A13 were deferred. The implementations were verified
offline by the project's own tests, and the live pairs that followed did not complete.

**Agreement.** The separation of system defects from model errors; the finding that run 48's
safety gate withheld 11 supported findings on an unexplained score; the finding that run 40 could not
converge; the habit of correcting earlier readings in each addendum.

**What this analysis adds.** Success rate by code era; the long-tail rejection distribution;
the stability of classification (which moves the focus from analysis quality to the reviewer and
contract); the cost trend (section 8); and the list of missing observations (section 7).

**Disagreement of strategy.** The audit series repairs each observed mechanism. That is the strategy
that has produced seven contract versions without raising the completion rate. One of the second
auditor's own parts concedes that repairing a rejection message would not have changed run 40's
outcome, yet the plan continues at the rejection level. `[INFERRED]`

## 7. What the live tests and audits have not observed

These are, in the author's view, what is needed to reach and to recognise a correct output.

1. **An independent definition of "correct".** There is no gold answer or fixed checklist. For this
   case a harness outside the runtime could check mechanically: five-category table, denominator 13,
   two literal excerpts that occur in the sources, two team questions, no respondent identification.
   Today "correct" means "accepted by the same system's reviewer" or "read by an auditor".
2. **Reviewer accuracy.** Nobody has measured the false-accept and false-reject rates of ZeroSugar
   on known-good and known-bad candidates. Nine controlled review cases and a scorer were added late,
   but their provider accuracy is recorded as unmeasured.
3. **A ceiling test.** Nobody has given the reviewer a human-written ideal answer to see whether it
   accepts it. If it does not, no generator repair can succeed.
4. **Repetition and variance.** The same code and case run five or more times, with a completion
   rate and interval. Differences between runs 40, 41 and 45 cannot currently be separated from noise.
5. **Per-draft quality.** Drafts 1-4 are never scored against the same checklist, although
   oscillation (run 40) and lost content (run 23) suggest later drafts can be worse.
6. **A baseline without review.** No run isolates the quality of the first candidate or what the
   two review phases add per token.
7. **Objection precision.** The fraction of reviewer corrections that are valid has been checked by
   hand for one run and never tabulated; it explains the persistent `revise`.
8. **Breadth.** Nearly every run uses one case. Cherry executed in 8 of the Luna logs and Lime in
   none `[OBSERVED]`; numeric, chart and multi-dimension paths have almost no recent live evidence.
9. **Human validation** of classification and of every semantic judgment.
10. **Real-output tests.** The suite uses scripted failures; it does not replay the distribution of
    real saved model outputs against new code, nor fuzz reviewer-like outputs.
11. **Cost as a requirement.** A 15,000-token repair target was measured, missed and then retired
    as a pass/fail criterion instead of being met; no component has a token budget.
12. **Process control.** Nothing prevents a live run on code that has not passed the offline suite.

## 8. Why token use increased

| Run | Status | Calls | Total input | Total output | Avg input / call | Max input / call | ZeroSugar calls | ZeroSugar input | Original calls | Original input |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | partial | 18 | 142k | 14k | 7.9k | 16k | 5 | 55k | 7 | 59k |
| 9 | failed | 17 | 115k | 11k | 6.7k | 12k | 0 | 0k | 8 | 51k |
| 10 | partial | 12 | 69k | 9k | 5.8k | 10k | 4 | 32k | 4 | 23k |
| 11 | complete | 9 | 48k | 7k | 5.3k | 10k | 2 | 19k | 3 | 15k |
| 12 | failed | 12 | 64k | 8k | 5.3k | 13k | 4 | 34k | 4 | 15k |
| 13 | partial | 14 | 73k | 7k | 5.2k | 14k | 5 | 19k | 5 | 40k |
| 14 | failed | 12 | 78k | 13k | 6.5k | 18k | 5 | 51k | 3 | 13k |
| 15 | failed | 13 | 69k | 8k | 5.3k | 12k | 6 | 42k | 3 | 12k |
| 16 | complete | 15 | 106k | 12k | 7.1k | 16k | 5 | 39k | 5 | 45k |
| 17 | complete | 9 | 47k | 5k | 5.3k | 14k | 2 | 17k | 3 | 14k |
| 18 | complete | 27 | 260k | 30k | 9.6k | 19k | 15 | 173k | 7 | 63k |
| 19 | partial | 23 | 269k | 29k | 11.7k | 22k | 13 | 172k | 7 | 84k |
| 20 | failed | 11 | 50k | 5k | 4.5k | 10k | 3 | 10k | 3 | 14k |
| 21 | partial | 26 | 281k | 33k | 10.8k | 22k | 12 | 147k | 10 | 117k |
| 22 | complete | 10 | 57k | 8k | 5.7k | 13k | 2 | 16k | 3 | 15k |
| 23 | partial | 26 | 295k | 29k | 11.3k | 21k | 13 | 155k | 9 | 123k |
| 24 | partial | 22 | 226k | 25k | 10.3k | 22k | 8 | 70k | 9 | 130k |
| 27 | failed | 11 | 88k | 12k | 8.0k | 18k | 4 | 48k | 4 | 25k |
| 30 | complete | 18 | 193k | 23k | 10.7k | 22k | 8 | 112k | 6 | 64k |
| 35 | failed | 18 | 309k | 27k | 17.2k | 45k | 8 | 100k | 7 | 184k |
| 38 | failed | 12 | 138k | 13k | 11.5k | 27k | 2 | 22k | 6 | 88k |
| 40 | partial | 25 | 483k | 36k | 19.3k | 44k | 14 | 248k | 8 | 209k |
| 41 | partial | 20 | 299k | 31k | 14.9k | 28k | 10 | 151k | 7 | 122k |
| 45 | partial | 24 | 434k | 34k | 18.1k | 33k | 11 | 173k | 10 | 235k |
| 47 (network-enabled) | partial | 24 | 369k | 37k | 15.4k | 28k | 12 | 169k | 8 | 155k |
| 50 | failed | 13 | 128k | 7k | 9.9k | 21k | 3 | 12k | 3 | 27k |


For the same question, input per workflow rose 6-9x between runs 17/22 and runs 40/45, and output
tokens 4-7x. `[OBSERVED]` The largest single call grew from about 13k input tokens (run 22) to
43-45k (runs 35 and 40).

**Drivers.**

1. **A larger fixed prompt resent on every call.** `[OBSERVED]` Sizes in characters from the private
   exchange captures (about 3-4 characters per token):

| Call | Run 30 (complete) | Run 45 (partial) | Run 50 (failed) |
| --- | --- | --- | --- |
| Original instructions | ~12k | 40-43k | 25-33k (Original / Vanilla final-answer calls) |
| Original tool schema | 1-2k | 11-13k | 6-9k |
| ZeroSugar support instructions | 16k | 18k | n/a |
| ZeroSugar support tool schema | 4-5k | 16.8k | n/a |
| ZeroSugar support evidence (history) | 35-56k over three attempts | 37.5k per attempt | n/a |

   In run 45 about 70% of one Original call (51k of 72k characters) is instructions plus tool
   schema, independent of the case. The timing matches the C1 contract (reference-based blocks, edit
   schema, correction handling); that C1 is the cause is `[INFERRED]`.
2. **Retries resend and accumulate the whole payload.** `[OBSERVED]` In run 30 the three support
   attempts carry histories of 35k, 45k and 56k characters; each retry includes the earlier attempts
   and their feedback. In run 40 one phase produced three support calls of 21-22k tokens each.
3. **More review calls.** `[OBSERVED]` Two phases per candidate, up to four candidates, plus retries,
   raised ZeroSugar from 2 calls (run 22) to 10-14, about 40-50% of a run's input tokens.
4. **Larger outputs.** `[OBSERVED]` Assertion-level support reviews return 2-5k output tokens per
   call and reached the 6000-token cap in Luna runs 35 and 38 and Gemini run 37.
5. **Evidence repeated across drafts.** `[OBSERVED]` Every support call carries the evidence, claims,
   labels and all accumulated obligations again; an Original call after the Vanilla handoff carries a
   19k-character tool output.
6. **Rework with no net progress.** `[INFERRED]` Oscillating drafts (run 40) spend the same tokens as
   converging ones.

Luna runs that completed used 47-260k input tokens (runs 17, 18, 22, 30); none of the 300-480k runs
completed. No token budget per component exists.

## 9. Scoring the agents (1-10, 10 = very good)

Scores combine design (definition, boundaries, tools, verifiability) and observed behaviour in the
Luna runs (reliability and cost). The "earlier" column is the author's assessment from documentation
alone, before reading the runs; the change reflects what the runs showed.

| Agent | Design | Observed | Score | Earlier | Reason |
| --- | --- | --- | --- | --- | --- |
| Cherry | 9 | 6 | 7 | 8 | Cleanest definition, replayable SQL, but executed in only 8 Luna logs and skipped in the sentiment-only runs; thin recent evidence. |
| Lime | 8 | 4 | 6 | 7 | Never executed in a Luna run; cannot chart sentiment, the case's main output; no live validation. |
| Vanilla | 6 | 8 | 7 | 5.5 | Classification stable for 12 of 13 comments across 40 runs and 3 models in about 4 calls. Dual role (retrieval/interpretation and classification) is a design weakness; no human validation. |
| Original | 5 | 4 | 4.5 | 5.5 | Planner, synthesizer, repairer and challenger in one role; most of the input-token growth; many failures are contract adherence (25 rejection codes), not reasoning; drafts oscillate. |
| ZeroSugar | 8 | 2 | 4 | 5 | Best concept (independent, two-phase, objective gates plus judgment) and worst behaviour: false accepts, false rejects, contradictions, protocol violations, 40-50% of calls and tokens, same model family as the producer, and a rule that forces it to invent corrections to block. |
| System (orchestration and governance) | 7 | 3 | 4.5 | 5.5 | Sound principles (model judges, code verifies, withhold the unsupported); no completion since run 30; 6-9x cost; no external definition of correct; no ablation or repeated trials; unverified changes shipped. |

## 10. Recommendations `[PROPOSED]`

1. Measure before changing again: build the external checklist harness (7.1), run the ceiling test
   (7.3) and measure the reviewer's error rates (7.2). None requires a runtime change.
2. Simplify the reviewer contract: a minimal verdict plus corrections, with identifiers, links and
   lifecycle derived in code. Allow a clean `revise` without a fabricated obligation.
3. Make review independent: a model different from the producer, plus per-draft quality scoring so
   iteration can stop when it stops improving.
4. Set token budgets per component; slim the instructions and schemas resent on every call; avoid
   replaying whole histories on retries.
5. When review fails, deliver the unreviewed candidate clearly labelled, keeping the withholding
   policy for anything presented as approved.
6. Gate live runs on the offline suite, and repeat a fixed configuration five or more times before
   attributing a change in outcome.
7. Widen the evaluation to other questions and to the numeric and chart paths.

## 11. Limits of this analysis

- One test case, one provider family for the main series, one run per code version.
- Rejection counts are minimums; private exchange captures exist only from run 30 onward and the
  prompt-size comparison rests on three runs.
- The author did not re-judge the semantic correctness of any label or answer, and did not verify
  all `[AUDITOR-2]` claims.
- Scores are judgments, not measurements.
- Token figures come from the gateway's per-call usage fields; they are not a billing reconciliation.

## 12. Questions for the reviewing model

Please answer each, citing which section or table supports your view.

1. **Diagnosis.** Is the main reason for the persistent failures the reviewer contract and the
   all-or-nothing gate, as argued in section 5? What alternative explanation fits the data (for
   example the generator, the gateway, the model choice, the case)? What evidence would separate them?
2. **Evidence quality.** Which conclusions in sections 3-8 are not supported by the data shown? Which
   are over-stated given n = 1 per code version?
3. **Missing observations.** Add or remove items from section 7. Design the smallest experiment
   (runs, repetitions, measures) that would show whether the reviewer or the generator limits success.
4. **Architecture.** Is a separate LLM reviewer with per-assertion judgments an appropriate design for
   this task? What would a simpler architecture look like, and what would it lose?
5. **Token cost.** Which of the drivers in section 8 would you address first, and how, without
   weakening the checks that matter?
6. **Scoring.** Re-score the five agents and the system on a 1-10 scale using the same criteria, and
   explain any score you would change.
7. **Process.** What process changes would prevent the regression pattern (fix the last failure, break
   something else, repeat)?
8. **Risks of my recommendations.** What could go wrong if sections 10.1-10.7 were followed?

Please separate what you can conclude from the document alone from what you would need to see in the
raw logs.
