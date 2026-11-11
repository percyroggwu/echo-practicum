# Auditing the Echo solution and the 2026-11-01 improvement analysis

Independent audit, 2026-11-01. Read-only. No model/API call, no test suite, no build, no
runtime, prompt, configuration, checkpoint or artifact change was made for this document, and
no credential file was opened. The only file written is this one.

Subject: the Echo workflow as it currently stands (code, contract, logs, artifacts) and the
claims of [IMPROVEMENT_ANALYSIS_SCORES_AND_TOKENS.md](IMPROVEMENT_ANALYSIS_SCORES_AND_TOKENS.md)
**revision 3** (that document was revised at 04:42 on 2026-11-01, after
[CORRECTION_UPDATE_PLAN_2026-11-01.md](CORRECTION_UPDATE_PLAN_2026-11-01.md); this audit was
performed against revision 3, not revision 2).

Evidence labels: `[OBSERVED]` recomputed here from logs, private captures or artifacts, or read
directly in source at the cited line. `[INFERRED]` my reasoning. `[PROPOSED]` a recommendation.
`[NOT VERIFIED]` a claim I could not check; the reason is given. Numbers are provider counters
or character lengths; neither is a bill, and characters are not tokens.

---

## 1. Verdict

**The system's design is stronger than its evidence, and its evidence is stronger than its
outcomes.** The architecture is coherent and its instrumentation is unusually complete: five
roles, six shared rules, two independent reviews, objective source/scope/quote/arithmetic gates,
a release gate that withholds unsupported findings, strict replay identity, and captures that
retain every request, response, rejected argument and tool result for 144 runs. Very few
student projects can reconstruct a failing trajectory this precisely. The problem is not that
the system cannot be examined; it is that what the examination shows is repeated termination by
its own protocol, against a case (13 comments, one manager, one quarter) on which no quality
measurement exists.

The current state, recomputed over the 42 workflow logs that carry usage counters `[OBSERVED]`:
7 complete, 18 partial, 17 failed; the last complete workflow is run 30
(`reports/logs/20261027_210103_1d22ae65cfb5.jsonl`), so the completion rate after 2026-10-27 is
0/17. Of the 27 runs that record a terminal `error_category`, **15 are protocol-shaped** (14
`invalid_review` at stage `verification`, 1 `review_protocol_error`) and 5 more are
`output_token_limit`; only 5 end inside the answer path itself (`agent_turn_limit` 3,
`answer_delivery_stalled` 2).

The companion analysis is directionally correct and most of its arithmetic reproduces exactly:
the population, the period split, the medians, the doubling of input per call, the truncation
cost, the run-36 outlier, and (as of revision 3) the Luna 52 counterfactual. Its weak points are
material rather than decorative: ZeroSugar rejection counts are inflated by copying each event
twice, the correction family is wider than the stated 11 runs, the per-round cost figure is only
true for Original's own calls, and — the largest omission — **it never examines why runs
terminate**, so it treats the system's dominant failure mode (its own review protocol exhausting
three attempts) as background rather than as the main object.

Position on the framing question, stated up front and defended in section 5: **"administrative
bookkeeping, not reasoning" is correct for the mechanism that ends most runs and wrong as a
statement about analytical quality.** Nothing in 42 runs shows that Echo analysed the 13 comments
incorrectly, because nothing measures that. What is shown is that submissions die on list
cardinality, derived lifecycle states and schema-conformance — with two distinct sub-cases: one
where the checker withheld the datum it had (run 51) and one where the checker supplied it and
the model repeated the error anyway (run 52).

---

## 2. Method and evidence base

- **Sources.** `Agent_Echo/reports/logs/*.jsonl` (394 logs), private captures
  `Agent_Echo/reports/logs/details/<run_id>/exchanges.jsonl` (144 directories, 499 captured
  `model_input` requests, from the first capture on 2026-10-27 21:01 onward),
  `Agent_Echo/reports/apinex_prueba_*.json` (60 artifacts), and source files read at the cited
  lines. Scripts used for recomputation live outside the repository
  (`%TEMP%\opencode\audit_*.py`); nothing was written into the project.
- **Population.** Workflow logs with at least eight `model_response_usage` events: 42, split by
  log date into ≤2026-10-27 (25) and ≥2026-10-28 (17). The four 2026-10-21/22 logs that carry
  counters are included, as in the companion analysis. The eleven shorter logs (probes,
  reconnects, `offline_scripted_demo` runs on 2026-11-01) are excluded from all totals below;
  they remain in the 394-log count.
- **Attribution.** Each `model_response_usage` is assigned to the agent of the preceding
  `model_started`; ZeroSugar calls are split into completeness and support by the current
  `review_phase_started.phase`. The logs show sequential calls, so the assumption holds
  `[OBSERVED]`.
- **Truncation.** A call is truncated when `output_tokens >= output_limit` (6000, matching
  `connections.json`) or when a `review_truncation_retry` event follows it.
- **Rejection counting — the one place I deviate from the companion analysis.** A rejection that
  occurs in a review round is written twice in the artifact: once inside
  `diagnostics.review_history[i].rejected_attempts` and once in the summary list
  `diagnostics.verification.rejected_attempts`. The companion analysis counts both copies (its
  §1 admits "an entry may appear in both the summary and a review round"). I drop a summary copy
  when an identical tuple of `validation_code`, `field`, `rejection_index`, `item_index`,
  `correction_id` and `reason` exists in a round. Every count marked "deduplicated" below uses that
  rule; where a claim reproduces only with duplicates counted, I say so.
- **What I did not do.** I did not run the 412-test gate or any test, did not call a provider,
  did not rebuild the knowledge graph (`graphify-out/` is untouched because no code changed), and
  did not re-judge any answer, label or verdict. Captures were read for argument structure and
  sizes; I did not read them for content quality beyond quoting the rejection reasons.
- **Retractions of my own provisional suspicions** (stated because an audit that only accumulates
  accusations is not an audit):
  1. I first read "Gemini 51 … 170k, 52%" as a misattribution. It is not: the seven
     `answer_removal_reasons` calls carry 169,600 input tokens, 52.3% of 324,402. Only the
     *column definition* is inconsistent with the run-36 row (section 7.2).
  2. I first suspected the wall-clock budget had been overrun in run 51 (420.8 s elapsed against a
     300 s default). Wrong: the run was explicitly launched with `--run-seconds 1000` and
     `--model-call-limit 32` (`execution_configuration.arguments`).
  3. I first suspected revision 3 ignored the correction plan. Wrong: revision 3 cites it and
     adopts its §2 corrections; the timestamp shows it was written six minutes after the plan.
  4. My first count of "every finding exactly once" (12 in 9 runs) came from a path that missed
     the review-round copies; the reproducible figure is 17 raw / 13 deduplicated in 10 runs.

---

## 3. Independent re-verification of the companion analysis

All values `[OBSERVED]` unless marked. "Doc" is revision 3 with its line numbers.

| # | Claim (doc) | Doc value | Audited value | Status |
| --- | --- | --- | --- | --- |
| 1 | Population and split (§1, §2.1) | 42 logs, 25 / 17 | 42 logs, 25 / 17 | Verified |
| 2 | Median input per run (§2.1) | 111k → 299k | 111,417 → 298,913 | Verified |
| 3 | Input per call (§2.1) | 8.5k → 17.0k | 8,530 → 17,048 | Verified |
| 4 | Median calls per run (§2.1) | 15 → 18 | 15 → 18 | Verified |
| 5 | Median review rounds (§2.1) | 1 → 2 | 1 → 2 (support phases) | Verified |
| 6 | Agent shares (§2.1) | 36/38/17 and 54/33/11 | 35.7/38.3/17.0 and 53.6/32.6/10.6 (Original / ZS support / Vanilla; completeness 7.6% and 3.2% excluded from the printed columns) | Verified, definition clear |
| 7 | Truncation (§2.1, §2.3 D4) | 1 run before, 8 after, ~211k tokens | 1 run / 21,843 tokens before; 8 runs / 9 calls / 210,947 after (total 232,790) | Verified |
| 8 | Gemini 36 (§2.3 D3) | 704k, 85% of the run | 703,695 of 827,747 = 85.0% | Verified |
| 9 | Gemini 51 loop (§2.3 D3) | 170k, 52% | 169,600 over the seven rejecting calls = 52.3%; answer-path Original is 212,110 = 65.4% | Verified for the stated subset; column definition differs from row 8 (see 7.2) |
| 10 | Luna 52 support (§2.3 D3, rev 3) | 121,357, 45% | 121,357 (27,636 + 28,760 + 31,235 + 33,726) = 45.0% of 269,775 | Verified |
| 11 | Counterfactuals (§4 X1, §7) | 64,961 / 93,721 / 130,725 | 31,235+33,726 = 64,961; 28,760+64,961 = 93,721; 22,909+24,298+26,273+27,907+29,338 = 130,725 | Verified arithmetic |
| 12 | "One round costs 45-60k; four rounds 200-240k" (§2.3 D2) | 45-60k | Reproducible only for Original's own calls: 51.5k (Gemini 44), 58.8k (Luna 45), but 30.5k (Luna 41). Whole-round cost (total/rounds) is 75-135k, median ≈105k; the four-round runs in the doc's own table are 432-483k | Understated when read as round cost |
| 13 | Component sizes (§2.3 D1) | 11k/22k/1k, 32k/20k/7k, 27k/30k/4k | 11,918/22,798/1,833; 32,167/20,070/7,461; 27,213/30,233/4,487 | Verified within rounding (run 30 tool schema is 1.8k, printed 1k) |
| 14 | Excerpt/quote family (§3.1) | 37 entries, 21 runs | 37 in 21 runs (`excerpt_source` 17, `interpretation_quote_not_literal` 9, `proposal_quote` 8, `interpretation_source_not_text` 3) | Verified |
| 15 | Free-form instead of the answer tool (§3.1) | 27 (Original 23, Vanilla 4), 19 runs | 27 in 19 (`grounded_answer_required` 23 in 16 artifacts; 4 Vanilla delegation entries) | Verified exactly |
| 16 | Every finding exactly once (§3.1) | 17 entries, 10 runs | 17 raw, **13 deduplicated**, 10 runs, last Gemini 32 | Run count verified, entry count inflated by 4 copies |
| 17 | Citation not in the finding's subset (§3.1) | 29 entries, 8 runs | 23 deduplicated, 8 runs, run 30 → Luna 47 | Entries inflated by 6 copies |
| 18 | Literal assertion coverage, review-v4 (§3.1) | 15 entries, 3 runs | 10 deduplicated, 3 runs (runs 27-29) | Entries inflated by 5 copies |
| 19 | Correction family (§3.1, §5.1 Z9) | 42 entries, 11 runs, run 12 → 52 | 40 deduplicated, **16 runs**, run 12 (`vanilla_12`) → `vanilla_52` | Entry count close; run count materially low |
| 20 | Narrative capacity (§3.1) | 7 entries, 1 run, "No; A1/A2" | 7 in Gemini 36 confirmed; plus 1 in Gemini 44 and 1 in `vanilla_47_network` with a **different** message ("The resolved narrative list exceeds its item limit") that was accepted after repair | Partly verified; family not dead |
| 21 | Removal reasons (§3.1) | 7 entries, 1 run | 7 in Gemini 51, `detail: {}` on all seven | Verified |
| 22 | Unused challenge (§3.2) | 57 offers, 0 calls, 394 logs | 57 `model_input` requests across 13 runs offer `challenge_corrections`; 0 calls; 0 `correction_challenge_completed` events in 394 logs and 144 captures | Verified |
| 23 | Agent scores (§5.1-5.5) | ZS 4.4, Original 4.7, Vanilla 6.8, Cherry 7.3, Lime 5.9 | Same values in [SOLUTION_EVALUATION_1_TO_10.md](SOLUTION_EVALUATION_1_TO_10.md) | Verified |
| 24 | No completion since run 30 (§2.1) | 0 completes after 10-27 | Last complete log `20261027_210103_1d22ae65cfb5` (run 30); 0/17 after | Verified |
| 25 | CMT27512 flip (§5.3 V2) | positive in Luna 52, mixed in Gemini 51 | 24 positive / 18 mixed over 42 artifacts, but the flip is not agent-linked: Luna 50 mixed, Gemini 44/46 positive, Gemini 49/51 mixed, Luna 52 positive | Verified as a fact; the implied agent correlation is not |

Summary: 17 of 25 rows verify as stated; 6 verify only after a definition correction (rows 9,
16-19, 25); 1 is understated when read as whole-round cost (row 12); 1 is only partly true because
the family was declared dead (row 20). No row is fabricated, and no row required an invented
number to check.

---

## 4. Architecture and contract audit

### 4.1 What holds up

- **Role separation and controls** `[OBSERVED]`. Five roles (`agents/*.py`), six shared rules in
  `agents/policies.py` lines 4-32, both review phases required, objective source/scope/quote/
  arithmetic gates, manager/date scoping, and a release gate that withholds unsupported findings
  (`zero_sugar.py:1483`). The 2026-10-23 decision to keep citations by finding ID and to forbid
  mandatory per-question checklists is reflected in the code, not only in the documentation.
- **Instrumentation.** `agents/capture.py:73-83` hashes `run_agent.py` and every `agents/*.py` for
  each capture; logs and captures contain request inputs, model arguments (including rejected
  ones), tool results and phase checkpoints. This is why a failure can be diagnosed at all: the
  run-51 analysis below rests entirely on those captures.
- **Budget accounting.** `runtime.py:100` (32 model calls, 48 tool calls, 300 s, 256 embeddings),
  `run_agent.py:151-152` (tool limit grows by 2 per extra model call), transport retries charged
  to the model budget. Budget exhaustion is reported as `remaining` in the terminal events, and
  runs 51/52 stopped with 13 and 16 calls unused, i.e. they were not budget-limited but
  protocol-limited `[OBSERVED]`.
- **Replay identity.** `resume.py:195-308` requires matching `source_versions()`, database hash
  and connection fields. Old runs cannot be resumed under changed code — the correct conservative
  choice, with a cost named in 4.2.

### 4.2 Contract defects that matter

**(a) An error that knows the answer and does not say it.** `content.py:171-179` validates
`removal_reasons` with a single compound condition: list length must equal `len(set(remove))`,
each entry must be exactly `{block_id, reason}`, each `block_id` must be in `remove`, each reason
1-300 characters, and no duplicates. On failure it raises
`ValidationError('answer_removal_reasons', 'removal_reasons', 'Explain each explicitly removed block once; ...')`
with no details. The sibling `narrative_count` error in the same function
(`content.py:213-220`) carries `expected_count`, `actual_count`, `retained_count`, `excess`,
`remaining_slots`, `removable_block_ids`. The codebase therefore already has the pattern for a
localised error and does not use it where the localisation is cheapest.

**(b) A rule the model is told, then told to break.** `zero_sugar.py:220-226` instructs the model
that `addressed` "asks whether the current VISIBLE … addressed when the user requested it in the
answer". `zero_sugar.py:1454-1455` then requires `addressed is False` for every linked refinement,
regardless of content. Run 52 submitted `addressed: true` with `mandatory: true` and was rejected
twice (`correction_refinement_state`, `expected_addressed: false`). The model followed the
instruction it was given; the validator enforced a different, unstated rule.

**(c) Serial validation defeats joint reporting.** `zero_sugar.py:1439` calls
`resolve_corrections`, which raises on the first duplicate/identity problem
(`content.py:90-114`); the lifecycle loop that collects refinement and finding errors runs at
`1450-1470`, and the joint error list at `1511-1531` is unreachable for that path. Run 52 shows
the consequence: three `correction_duplicate` attempts consumed all three protocol attempts, and
the `correction_refinement_state` error was only surfaced after the loop had already failed. The
known fix (audit P1.1) is still open.

**(d) A tool nobody calls.** `original.py:105-110` defines `challenge_corrections` with a clear
description; `original.py:303-353` implements it and records `correction_challenge_completed`.
It was offered in 57 requests over 13 runs and called zero times `[OBSERVED]`. No event records
why: there is no counterfactual, no "considered and declined", and no instruction anywhere telling
Original when challenging is preferable to rewriting. This is an instrumented dead branch, not a
broken one.

**(e) Maintenance against reproducibility.** Because `source_versions()` hashes every agent
module, any fix orphans every saved workflow, and the private captures are then the only bridge to
old behaviour. That is acceptable, but it means each contract change permanently destroys the
ability to re-measure the previous version — which is why the absence of a repeated-measure design
(section 6) cannot be repaired later.

**(f) The only quality instrument is unused.** `review_cases.py` defines nine controlled cases
over five synthetic comments with eight declared defect IDs; `evaluate_review_cases.py` scores
annotated judgments and requires `reviewer_id`, `annotation_method` and the corpus hash;
`tests/test_review_cases.py` exists. No scored result file exists in `reports/`, and the defaults
record `model_evaluated: false`. The instrument that would answer "does the review catch planted
defects?" has never been pointed at the system.

---

## 5. Failure taxonomy and root cause

### 5.1 What actually ends runs `[OBSERVED]`

Terminal category in the last failure event of each of the 42 runs:

| Terminal category | Stage | Runs | Share of 27 recorded terminations |
| --- | --- | --- | --- |
| `invalid_review` | verification | 14 | 52% |
| `output_token_limit` | verification 4, generation 1 | 5 | 19% |
| `agent_turn_limit` | answer_validation | 3 | 11% |
| `answer_delivery_stalled` | answer_validation | 2 | 7% |
| `provider_connection` | verification | 1 | 4% |
| `workflow_call_limit` | verification | 1 | 4% |
| `review_protocol_error` | verification | 1 | 4% |

7 runs completed; 8 ended partial without any of these events. `invalid_review` is not a content
judgement: in `reports/logs/20261031_073421_098f38a8bddd.jsonl` it follows
`review_protocol_stopped` with `attempts_used: 3`, `support_review_completed: false`, and a
preceding `correction_duplicate` rejection. **The dominant way this system fails is that its own
review submission does not validate three times.**

### 5.2 Two mechanisms, not one — the evidence for the position

Run 51 (`20261031_184919_4a532e3a56e9`) `[OBSERVED]` from the capture's submitted arguments:
the first acceptable draft removed 1 block with 1 reason (300 characters); every later attempt
contradicted its own list length — remove 19 / reasons 20, then 6, then 20, then 14, 14, 14, and
finally remove 6 / reasons 14 (the reasons described the blocks it *kept*). Seven rejections, all
with the identical message and `detail: {}`. The schema description (`content.py:227`) does say
"One reason per remove_ids entry; [] if none", so the rule was available; the model still failed
to count, and the checker still declined to say "20 reasons for 19 removals; unmatched
BLOCK_…". This is arithmetic on a list, not analysis of a comment.

Run 52 (`20261031_185641_3fac4ea27b96`): the `correction_duplicate` rejection carries
`item_index: 2`, `conflicting_item_index: 1`, `correction_id`, i.e. it *is* localised; the model
resubmitted the same conflicting pair three times. The second failure
(`correction_refinement_state`) is the instruction/validator contradiction of 4.2(b). So run 52
contains one genuine model non-compliance and one contract trap.

### 5.3 Position

- **Administrative bookkeeping, not reasoning, is the correct description of the termination
  mechanism.** Every recorded termination is a schema, cardinality, lifecycle-state, truncation or
  connection event. Not one failure event reports that the analysis was wrong. The system does not
  fail because Echo misreads 13 comments; it fails while packaging the review of its own answer.
- **It is not evidence about analytical quality.** The same corpus cannot show the analysis was
  right either. 12 of 13 labels are stable across 42 artifacts, which measures determinism, not
  correctness (section 6).
- **The protocol's specific pathology is that retries resample rather than converge.** Where the
  error is unlocalised (run 51) the model guesses a list length; where it is localised but the
  rule contradicts the instruction (run 52) the model repeats. In both cases the loop terminates
  the run before any content judgement is reached. That is a contract-ergonomics defect, and it is
  cheaper to fix than any modelling change.

---

## 6. The quality-evidence gap and a minimum credible measurement

### 6.1 What exists `[OBSERVED]`

- One case: 13 anonymous M14/Q3 Recognition comments. Every workflow, every profile, every code
  version used it.
- Label stability: 13 distinct comments in 42 sentiment blocks; 12 carry the same label in all 42;
  `survey:CMT27512` is 24 positive / 18 mixed, varying within the same profile on adjacent runs
  (Luna 50 mixed, Luna 52 positive; Gemini 49 and 51 mixed, Gemini 44 and 46 positive).
- No human labels, no gold answer, no per-category precision or recall, for any run.
- Review self-assessment quality: 94 of 315 Luna/Media rating rows (29.8%) and 50 of 112 Gemini
  rows (44.6%) carry a rationale of two characters or fewer (e.g. `"rationale": "F"`); overall
  144/427 = 33.7%. A one-letter rationale is not evidence that the reviewer examined the answer.
- The nine-case controlled instrument exists and has never been scored (section 4.2(f)).
- Acceptance is not quality: 16 findings released in run 51 and 7 in run 52 under partial status;
  release means the gate did not block, not that the findings are correct.

### 6.2 What this cannot support

Any statement of the form "the system produces good analysis", "the reviewer catches X% of
defects", "the score would rise to N after change Y", or "the model reasons well but formats
badly". None of these is measured. The companion analysis is careful about this (its §6 withdraws
the claim that code changes raise C4 alone); the evaluation's own scores are explicitly
evidence-limited. That caution should be preserved, not hardened into a conclusion.

### 6.3 Minimum credible design `[PROPOSED]`

Four steps, in this order, each cheap enough to run before any further contract change.

| Step | Instrument | Output | Cost |
| --- | --- | --- | --- |
| 1 | Two independent humans label the 13 comments blind (5 categories); report Cohen's κ and the disagreement set, especially CMT27512 | Inter-rater ceiling; the only defensible gold for this case | ~1.5 h human, no API |
| 2 | Score the nine controlled cases with two raters against their declared defect IDs, using `evaluate_review_cases.py` | False-accept / false-reject on explicit defects, with reviewer identity and corpus hash recorded | ~3 h human, no API |
| 3 | Three repeats per provider on the frozen case and source, unchanged code, capped at the current 32 calls | Run-to-run variance separated from code effects; completion and protocol-stop rates with n=3 | ≤192 model calls, ≤1.8M input tokens at the observed 300k ceiling, ~2 h wall clock at the 20 s request interval |
| 4 | Pre-register the pass conditions before step 3 (e.g. κ ≥ 0.6, zero false accepts on the nine cases, no protocol termination in 3 of 3 repeats) | A criterion that a later change can fail | none |

Step 2 is the highest information per hour: it tests the reviewer, which is the gate that decides
every outcome, without a live call. Step 1 is small (n=13 gives roughly ±27 points on a
proportion at 95% confidence) and should be reported as a ceiling, not as a benchmark.

No dollar estimate is given: provider prices are not in the repository and I did not read the
credential or billing files.

---

## 7. Assessment of the companion analysis (revision 3)

### 7.1 What it gets right

- Population, period boundary and the four drivers reproduce (section 3, rows 1-8, 13-15).
- The self-criticism in §3.2 — that revision 1 prioritised the last failure while the two widest
  families had no item — is correct and rare; I re-derived the same asymmetry.
- `X1`'s re-attribution is honest and arithmetically exact: joint validation cannot save the
  93,721 tokens that would require success on attempt 1, and it does nothing for Gemini 51.
- `Z2` (keep the keyed schema) is the best decision in the document: the keyed per-finding schema
  coincides with the disappearance of the "every finding exactly once" family after run 35.
- The measurement caveat about `reasoning_tokens = output_tokens - 1` and the missing cached-token
  field is correct and important; it is why prefix caching cannot be claimed either way.
- The "not recommended" list is sound in substance: more instruction text, more retries without
  better feedback, wording rules for false objections, replacing the keyed schema, and more full
  live workflows before measurement are all unsupported. It matches what 42 runs show.

### 7.2 Where it overreaches

- **Token projection (§7).** "One round costs about 45-60k; four rounds alone approach 200-240k"
  is reproducible only for Original's own calls (51.5k in Gemini 44, 58.8k in Luna 45, 30.5k in
  Luna 41). A whole round — Original plus both review phases — is 75-135k, and the four-round runs
  in the doc's own table are 432-483k. The 150k bound in the projection is therefore optimistic by
  roughly the review phases' share, though it is labelled `[INFERRED]` and hedged.
- **Entry counts (§3.1).** Four of the eight rows double-count each rejection (summary copy plus
  round copy): 17→13, 29→23, 15→10, 42→40. Run counts are right in three of those four rows; the
  correction family is wider than stated (16 runs, not 11). The doc calls these counts
  "approximate" in §1, which is honest, but §3.2 then reasons from the same numbers as if they
  were counts of distinct failures.
- **A family declared dead that is not (§3.1, row "Narrative capacity").** Seven entries in
  Gemini 36 are the 12-item cap. Two later entries carry the same code with a different message
  (resolved-list overflow after merging) and were accepted after repair. The conclusion "No;
  A1/A2" is right for the cap and wrong for the family.
- **A cause attributed to the agent (§5.3 V2).** "CMT27512 positive in Luna 52, mixed in Gemini
  51" is true but implies an agent or model effect that the 42 artifacts do not show: the label
  flips within both profiles on adjacent runs.
- **The D3 "Cost" column mixes definitions.** Run 36's 704k is the whole Original agent (85% of
  the run); run 51's 170k is the seven rejecting calls only (52%); run 52's 121k is one
  candidate's support calls (45%). Each is individually defensible; side by side they invite
  comparison that the numbers do not support.

### 7.3 What it omits

1. **Termination taxonomy.** 14 `invalid_review` and 5 `output_token_limit` terminations are never
   tabulated. The document organises the evidence by rejection family, which answers "what do
   reviewers reject" but not "what ends runs" — and those are different questions with different
   fixes.
2. **The non-localising removal-reason error.** Run 51 is described as seven rejections costing
   170k; the fact that all seven messages are byte-identical with `detail: {}`, while the sibling
   `narrative_count` error carries counts and IDs, is the actionable finding and is absent.
3. **The `addressed` contradiction.** `zero_sugar.py:1454-1455` versus `220-226` is not mentioned,
   although it is the second of run 52's two protocol failures.
4. **Eight partial runs with no terminal category**, and the observation that 51/52 stopped with
   13 and 16 calls unused — i.e. budget headroom is not the constraint.
5. **The evidence behind the scores.** "No completion since run 30" appears as a fact in §2.1 but
   is not connected to §5: the per-agent scores it quotes are anchored on pre-10-28 successes and
   post-10-28 protocol failures, and the *absence of any completion after run 30* is precisely what
   holds observed reliability low. The document treats the scores as context instead of as a
   consequence of the evidence it just tabulated.

### 7.4 Ordering

The proposed order (measure → protocol → payload shape → contract decisions → quality
measurement) is close to the correction plan's stage order and is the right shape. Two objections:

- **Quality measurement is scheduled last (step 4) while §6 argues that C4 and C5 (40% of every
  score) move only through measurement.** If the argument is right, measurement belongs at step 1,
  before payload-shape work whose effect cannot be judged without it.
- **S1 ("measurement freeze") appears in no step at all.** It is the precondition for every other
  item and is easy to adopt: no contract-version change during a measurement series.

### 7.5 Already implemented, duplicated or omitted

| Item | Status found | Note |
| --- | --- | --- |
| O3 repair packet | Largely implemented as A8; the doc says so | History fell 54-62k → 17k characters; correct |
| Z3 derive linked-correction state | Withdrawn in Addendum A.2; doc agrees | Correct |
| Z8 rating rationales | Changed to "measure v7 explanations"; doc agrees | Still unmeasured; 29.8%/44.6% short rationales are the baseline to beat |
| X1 | Extends existing A17/A18/A20 | Honest; the only remaining serial path is `zero_sugar.py:1439` |
| O1 and X3 | The same change listed twice | Acknowledged as "Contract decision; see O1" |
| Z9 / Z10 | Measurement items that overlap V1-V6 | Their real content is "build fixtures from captures", which X5 generalises |
| Z4 | "Find out why the challenge was never called" | The only item that addresses a fully instrumented dead branch; cheap, and no live run is needed |
| Missing item | None proposed for the non-localising validation errors of 4.2(a) | The cheapest available fix in the whole document's scope |

---

## 8. Prioritised recommendations

Four kinds, in the order they should be executed. "Cheap" means no live call.

### 8.1 Measurement only (no runtime change)

| ID | Action | Basis | Cost |
| --- | --- | --- | --- |
| M1 | Two-rater blind labelling of the 13 comments; report κ and the CMT27512 disagreement | §6.1, row 25 | ~1.5 h |
| M2 | Score the nine controlled cases with two raters and record reviewer identity, method and corpus hash | `review_cases.py`, `evaluate_review_cases.py` | ~3 h |
| M3 | Tabulate terminal category per run for every future run; publish it beside the rejection families | §5.1 | minutes |
| M4 | Count deduplicated rejections (summary + round) in every future analysis; state the rule | §2 | minutes |
| M5 | Three repeats per provider, frozen case, unchanged code, before any contract change | §6.3 step 3 | ≤192 calls |

### 8.2 System and protocol fixes (code, no user decision)

| ID | Action | Basis | Risk |
| --- | --- | --- | --- |
| P1 | Localise the removal-reason error: `expected_count`, `actual_count`, missing and extra `block_id`s, as `narrative_count` already does | `content.py:171-179` vs `213-220`; run 51 | Low; testable offline |
| P2 | Collect instead of raise in `resolve_corrections` so refinement and finding errors are reported in one pass | `zero_sugar.py:1439` vs `1450-1470`; run 52 | Medium; changes rejection ordering, needs fixtures |
| P3 | Make the `addressed` rule consistent: either derive the state and stop asking, or require `False` only where the correction is new in this submission and say so in the schema | `zero_sugar.py:1454-1455` vs `220-226` | Low |
| P4 | Log the reason a tool was offered but not called (or at least count offers vs calls per role) and surface `challenge_corrections` in the repair instruction | 57 offers, 0 calls | Low |
| P5 | Add a per-component input budget report per run, with a warning threshold | §2.1 doubling; X4 | Low |
| P6 | Record a cause string on `workflow_failed` beyond `error_category` (which attempt, which field) | §5.1 | Low |

### 8.3 Contract and user decisions

| ID | Decision | Why it cannot be decided here |
| --- | --- | --- |
| D1 | Whether a review that never validates should be retryable in a resumed phase rather than ending the run | Changes what "partial release" means; the 2026-10-26 recovery contract is a user decision |
| D2 | Whether `remove_ids` + `removal_reasons` collapse into one list | Answer contract; the doc already flags it (O1/X3) |
| D3 | Whether linked refinements may ever be `addressed: true` in the same submission | Alters review semantics, not just wording |
| D4 | Whether a measurement freeze (no contract change during a series) is adopted | A process commitment, not a code change |

### 8.4 Should NOT do

- Do not add instruction text or wording rules for false objections; run 51 failed on a stated
  rule, and more text would not have helped.
- Do not raise output caps or retry counts without localised errors; truncation is 5 of 27
  terminations and each retry resends the whole history.
- Do not replace the keyed per-finding schema; it coincides with the end of a 17-entry family.
- Do not run more full live workflows before M1/M2 and the P1/P3 fixtures exist; the 42-run corpus
  already contains more failure evidence than can currently be interpreted.
- Do not claim, in any document, that a code change raises C4 or C5 before a measured run.

---

## 9. Audit limits

- No live call, no test run, no build; the 412-test claim is `[NOT VERIFIED]` here by instruction.
- The corpus is one case (13 comments, M14/Q3 Recognition). Nothing here generalises to other
  managers, quarters, sizes or question types.
- Logs and captures are the system's own instrumentation. I verified internal consistency, not
  provider truth: `input_tokens` and `output_tokens` are counters, and reasoning tokens cannot be
  separated from visible output (every `reasoning_tokens` equals `output_tokens - 1`).
- Deduplication is my rule, stated in section 2. A different rule gives different entry counts;
  run counts are more robust than entry counts in every family I checked.
- Run numbering (12-52) comes from the artifact filenames; the mapping from log IDs to numbers is
  taken from `PROJECT_CONTEXT.md` and the artifacts, not re-derived from git history.
- Captures were read for argument structure and sizes, not for the semantic quality of any answer.
- The audited document may change again; this audit applies to revision 3 as of 04:42 on
  2026-11-01, and `DOCUMENTATION_MAP.md` was deliberately not updated (no existing file may be
  modified in this task).

---

## 10. Open questions for the user

1. **Is "completion" the target, or is "defensible partial release" acceptable?** 18 of 42 runs
   are partial, and partial runs do release content (17 findings in Gemini 44, 18 in Luna 45; where
   the artifact records explicit counts, from run 47 onward: 5, 10, 16, 7). If a partial answer that
   survives both reviews is acceptable, the 0/17 completion rate means something different than it
   looks; if not, the protocol stop is the only metric that matters.
2. **What may be changed in the review contract without a new authorization?** P1 and P3 change
   error text and a derived rule; P2 changes validation order. The current guidance authorises
   documentation and offline verification, not behaviour.
3. **Are you willing to re-run the same case three times unchanged?** Without repeats, no
   difference between code versions can be separated from run-to-run variance, and the CMT27512
   flip already shows that variance exists inside one profile.
4. **Who can serve as the independent raters for M1/M2?** The instrument requires a reviewer ID
   and an annotation method; self-annotation by the project author would not meet its own stated
   purpose.
5. **Is the challenge path (`challenge_corrections`) wanted at all?** If yes, P4; if no, deleting
   it removes a branch that has been part of the contract since 2026-10-23 and has never been called.
6. **Should old checkpoints remain resumable after P1-P3?** Strict identity makes that impossible;
   the choice is between preserving replay and fixing the protocol.
