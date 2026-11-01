# Echo solution evaluation on a 1-10 scale, 2026-10-31

Criterion-by-criterion evaluation of the five agents and of the system as a whole, based on the
Luna live runs through run 50 and the project's existing audits. It is read-only: no runtime change,
test execution, model request or publication. It complements, and does not edit,
[AUDIT_LUNA_RUNS_THROUGH_50.md](AUDIT_LUNA_RUNS_THROUGH_50.md) (run-level analysis) and
[AUDIT_SHARE_PACKAGE.md](AUDIT_SHARE_PACKAGE.md) (self-contained copy for external reviewers).

**Evidence labels.** `[OBSERVED]` computed by the author from the saved reports, logs or private
exchange captures. `[AUDITOR-2]` taken from the second auditor's documents (`AUDIT_2026-10-28` to
`AUDIT_2026-10-31`, `RUNS_49_50_ANALYSIS.md`), not re-verified. `[INFERRED]` the author's reasoning.
`[PROPOSED]` a suggestion; nothing here is approved or implemented.

## 1. Summary

| Component | Score (reliability-weighted) | Score (equal weights) | One-line judgment |
| --- | --- | --- | --- |
| Cherry | **7.3** | 7.8 | Best-defined agent; its live evidence is one clean numeric success from October 21. |
| Vanilla | **6.8** | 6.9 | Classification is the most stable part of the system; its scale and retrieval paths are untested. |
| Lime | **5.9** | 6.6 | Sound design that has never run in a Luna workflow. |
| Original | **4.7** | 5.0 | Overloaded role; most of the cost growth; its failures are mostly contract adherence. |
| System (orchestration and governance) | **4.7** | 5.3 | Strong principles and audit trail; no completion since run 30 and 6-9x the cost. |
| ZeroSugar | **4.4** | 5.0 | The right idea, the weakest observed behaviour, and the gate that decides every outcome. |

The ranking is essentially the same under both weightings (Original and ZeroSugar tie at 5.0 when
weights are equal); only the spread changes. The scores below are
computed from the rubric in section 2. They replace the holistic numbers given earlier in the
conversation and in section 9 of `AUDIT_SHARE_PACKAGE.md` (7, 6, 7, 4.5, 4 and 4.5); no value
moved by more than 0.4.

**Where the runs ended** `[OBSERVED]`. Of 33 evaluable Luna runs, 7 completed. Of the 25 that did
not: 4 ended in Original's answer path before any review (runs 5, 6, 8, 9), 13 ended at the review
stage by protocol failure or output cap (11 `invalid_review`, 2 `output_token_limit`), and 8 reached
the four-draft cap with the reviewer still asking for changes. None of the 25 ended because of
Cherry, Lime or the classification step.

## 2. Method

### 2.1 Scale

| Score | Meaning |
| --- | --- |
| 1-2 | Absent or broken; no evidence it works. |
| 3-4 | Works occasionally; major defects dominate. |
| 5-6 | Works partly; material gaps in reliability, evidence or cost. |
| 7-8 | Good; minor gaps, evidenced. |
| 9-10 | Strong, evidenced under repeated trials, hard to improve. |

### 2.2 Criteria and weights

The same eight criteria score every agent and the system. For the system they apply to the
orchestration as a whole. Weights favour observed reliability and output quality, since a system
that does not produce correct answers is not rescued by tidy design.

| ID | Criterion | What a 10 looks like | Weight |
| --- | --- | --- | --- |
| C1 | Role definition and cohesion | One clear responsibility, explicit inputs and outputs, nothing misplaced. | 10% |
| C2 | Boundaries and tool design | Least privilege; deterministic checks where they suffice; no tool that invites misuse. | 10% |
| C3 | Verifiability | Any output can be replayed or checked independently of the model that produced it. | 10% |
| C4 | Observed reliability | Completes its task and follows its contract in repeated live trials. | 20% |
| C5 | Output-quality evidence | Independent evidence (gold data, human review, repeated trials) that outputs are correct. | 20% |
| C6 | Efficiency | Calls, tokens and time proportionate to the value delivered. | 10% |
| C7 | Observability and testability | Failures are diagnosable; tests predict live behaviour. | 10% |
| C8 | Safety, privacy and scope | Scope enforced in code; identity and sensitive data protected; no way for the model to widen access. | 10% |

### 2.3 Score matrix

| Criterion | Cherry | Lime | Vanilla | Original | ZeroSugar | System |
| --- | --- | --- | --- | --- | --- | --- |
| C1 Role definition | 9 | 8 | 5 | 4 | 7 | 7 |
| C2 Boundaries and tools | 9 | 9 | 7 | 6 | 6 | 8 |
| C3 Verifiability | 9 | 8 | 8 | 7 | 5 | 7 |
| C4 Observed reliability | 6 | 3 | 7 | 3 | 2 | 2 |
| C5 Output-quality evidence | 5 | 3 | 6 | 4 | 2 | 3 |
| C6 Efficiency | 8 | 8 | 8 | 2 | 2 | 2 |
| C7 Observability and testability | 7 | 6 | 7 | 7 | 8 | 6 |
| C8 Safety, privacy, scope | 9 | 8 | 7 | 7 | 8 | 7 |
| **Weighted** | **7.3** | **5.9** | **6.8** | **4.7** | **4.4** | **4.7** |
| **Equal weights** | 7.8 | 6.6 | 6.9 | 5.0 | 5.0 | 5.3 |

## 3. Evidence base

`[OBSERVED]` unless stated.

- **Runs.** 38 Luna artifacts through run 50; 33 evaluable. 7 complete, 12 partial, 13 failed,
  1 needs_clarification. Completions by period: through run 14, 2 of 14; runs 15-24, 4 of 10;
  runs 27-30, 1 of 2; runs 35-50, 0 of 7.
- **Where Luna's model calls went.** Across every Luna log on disk (full workflows and probes,
  including runs after 50): 578 calls. ZeroSugar 207 (36%), Original 204 (35%), Vanilla 143 (25%),
  Cherry 24 (4%), Lime 0. Lime executed on other profiles only (2 calls on `nvidia_test`, 2 on
  `google_test`, 1 offline fixture).
- **Cost.** Luna input tokens per workflow: 47-57k for the simple completions (runs 11, 17, 22)
  and 193k for run 30, against 299-483k for runs 35-45; the 300-480k runs did not complete.
  Average input per call rose from 5.3k to 15-19k.
- **Rejections.** Retained rejected submissions: Original 48 in 19 runs, ZeroSugar 65 in 15 runs.
  These are minimums because early runs kept no diagnostics.
- **Rating rationales.** In the stored Luna reviews, 94 of 308 rating rationales (31%) have two
  characters or fewer (a repeated entry per draft counts separately).
- **Classification.** Twelve of the 13 comments received the same label in all 40 runs examined
  (three models). CMT27512 varied (positive 23, mixed 17).
- **Pacing.** The Luna profile spaces requests 20 seconds apart, so wall-clock time includes waits
  (8-26 pacing waits per workflow).

## 4. Cherry (quantitative evidence): 7.3

**Role.** Read-only Text-to-SQL on a scoped in-memory copy of the data, plus a catalog of validated
metrics (`cross_team_contributions`, `survey_trend`). Returns numeric findings with `[SQLn]`
citations; SQL and returned rows are retained as evidence.

| Criterion | Score | Reasoning |
| --- | --- | --- |
| C1 | 9 | One responsibility (numbers). Does not interpret comments or choose charts. Declines out-of-role work through a structured outcome. |
| C2 | 9 | Read-only SQL on a physical copy limited to the manager and date scope. Metric arguments are bound parameters. A guard rejects the known contribution/feedback `JOIN + COUNT(*)` mistake `[AUDITOR-2]`. |
| C3 | 9 | ZeroSugar replays both the SQL and the metric definition. Numeric cells are rendered by code from source facts. |
| C4 | 6 | Run `media_4` (Oct 21) completed with 9 calls and 168.7 s; its source aggregates and numeric changes matched independently. Other early runs with Cherry failed or were partial, in part from routing errors (sentiment delegated to Cherry). Cherry's last full-workflow execution in a Luna log is dated Oct 21; later Cherry activity is limited to Oct 27 transport probes. |
| C5 | 5 | One clean success is thin evidence. The SQL-semantics risk (a valid query answering a different question) is acknowledged by the project and not measured. |
| C6 | 8 | About four calls when used; 4% of Luna calls. |
| C7 | 7 | SQL, arguments and rows are retained; metric replay exists. No recent live trace to show it still behaves. |
| C8 | 9 | Scope enforced in code; anonymous identity fields excluded; group thresholds apply. Names in authorized operational records are permitted by design. |

**Main risk** `[INFERRED]`. The agent has not run in a full Luna workflow since October 21, while the
code around it (answer contract, delegation, delivery, review) changed substantially. Regressions in
the numeric path would not have been seen.

**What would raise it to 8-9.** Five or more repeated live runs of three or four numeric questions
with gold answers; a larger metric catalog; a measured rate of SQL that executes but answers a
different question.

## 5. Vanilla (text evidence and sentiment): 6.8

**Role.** Retrieval over comments (FTS5/BM25, optional semantic and hybrid) with cited
interpretation, and a full-population sentiment classification tool that labels batches of 20
comments, validates coverage and exact quotes in code, and computes counts and percentages.

| Criterion | Score | Reasoning |
| --- | --- | --- |
| C1 | 5 | Two different jobs under one name: retrieval and interpretation, and a batch classifier. They fail differently, are tested differently and could be scored separately. |
| C2 | 7 | Code checks unique-ID coverage, literal excerpts (up to 400 characters), recomputed aggregates, and never emits partial percentages. Retrieved text is treated as evidence, not instruction. |
| C3 | 8 | Source hashes, excerpts and aggregates reproduced in every run examined; labels are retained per comment. |
| C4 | 7 | The classification step completed in every full Luna workflow examined. It needed one batch in each (13 comments, batch size 20) and 3-7 Vanilla calls per workflow. Earlier failures (runs 5-6) were routing and output-limit problems that were repaired. DeepSeek run 25 left 12 of 13 validated, a different model. |
| C5 | 6 | Very stable (12 of 13 labels identical in 40 runs), but stability is not correctness. No human labels exist; `human_validated=false` is fixed. CMT27512 flipped between positive and mixed in 10 of 27 Luna runs. |
| C6 | 8 | Classification costs one batch (finished 69-87 s into a run, including pacing waits). |
| C7 | 7 | Per-comment labels, hashes and batch events are retained. |
| C8 | 7 | Identity fields excluded and small groups suppressed. Free text is not automatically redacted, and the project states that real authentication and a free-text privacy review are unfinished. |

**Gaps that the 13-comment case hides** `[OBSERVED]` for the batch count, `[INFERRED]` for the risk.
The multi-batch path (more than 20 comments), the three-attempt retry per batch, and retained progress
across redelegation have not been exercised on real data at scale. The thematic retrieval path is not
the focus of this case, so its live evidence here is thin.

**What would raise it to 8-9.** A human-labelled held-out sample across all categories with
per-category precision and recall; a population above 20 comments; separation of the classifier from
the retrieval/interpretation role or separate scoring of each.

## 6. Lime (visualization): 5.9

**Role.** Chooses zero to three supported charts from Cherry's SQL rows only; code validates and
exports SVG, CSV and provenance JSON. Cannot run code, fetch files or invent numeric arrays.

| Criterion | Score | Reasoning |
| --- | --- | --- |
| C1 | 8 | Narrow and well bounded. Whether a chart helps is a judgment; everything else is code. Arguably a tool with a selection step rather than a full agent. |
| C2 | 9 | Specs refer to citation IDs and column names; the exporter reads the values. Validator rejects unknown sources or columns, truncated tables, non-numeric values, duplicate pairs, and means without denominators. Hard limits on charts, rows and series. |
| C3 | 8 | Provenance file ties each chart to its source rows. Reviewed as spec and data, not as a rendered image. |
| C4 | 3 | Zero executions in any Luna log. Four calls on other profiles in early runs. |
| C5 | 3 | No live evidence of chart quality; no visual inspection by a person. |
| C6 | 8 | Runs only when a chart is planned. |
| C7 | 6 | Offline tests cover validation. Live behaviour is unobserved. |
| C8 | 8 | No database access and no arbitrary files. |

**Structural limit.** Lime accepts only Cherry's SQL evidence, so it cannot chart sentiment, which is
this case's main output. A future path would need Cherry to produce a verified derived table.

**What would raise it to 8.** A live run that plans and exports a chart, with a person checking the
rendered output; a sentiment-to-chart path through Cherry.

## 7. Original (coordination and synthesis): 4.7

**Role.** Plans, selects specialists, integrates their results into the candidate answer, proposes
at least one reasoned manager action, answers review corrections, and may challenge a correction
before rewriting.

| Criterion | Score | Reasoning |
| --- | --- | --- |
| C1 | 4 | Planner, synthesizer, action proposer, repairer and challenger in one role, each with its own failure mode. |
| C2 | 6 | Cannot run SQL, widen access or choose chart types; delegation is typed. But its answer must satisfy a heavy structured contract (source references, edit semantics, capacity, counts). |
| C3 | 7 | Claims, source IDs and citations are rebuilt and replayed in code. |
| C4 | 3 | 48 retained rejections in 19 runs. Top codes: `grounded_answer_required` (17), `numeric_interpretation` (7), `excerpt_source` (6), `proposal_quote` (4). Runs 5, 6 and 9 ended on turn limits, run 8 on an invalid plan, run 33 on a code crash. Drafts oscillate across repairs. |
| C5 | 4 | Accepted or released answers had content problems: actions given instead of the requested questions (run 22), prose contradicting the stored label (run 24), two stored labels swapped in a draft (Gemini 49) `[AUDITOR-2]`, repeated passages and lost content across drafts. |
| C6 | 2 | Original's input grew from 14-15k tokens per workflow (runs 11, 17, 22) to 120-234k (runs 24, 40, 41, 45). Its instructions grew from about 12k to 40-43k characters and its tool schema from 1-2k to 11-13k. The call right after the Vanilla handoff grew from about 10k to 25k tokens. |
| C7 | 7 | Plans, drafts, rejections and repairs are logged and captured. |
| C8 | 7 | Respects the fixed scope; does not identify respondents. Honors the project's no-fabrication rules. |

**Reading of its failures** `[INFERRED]`. Most rejections concern the format of references and edits,
not the quality of reasoning. The agent is being asked to be a good analyst and a precise serializer
at once, and the second demand grew faster than the first.

**What would raise it to 7.** Split planning from synthesis or reduce the output contract; cap the
resent prompt; demonstrate non-oscillating repairs by scoring each draft against a fixed checklist.

## 8. ZeroSugar (independent review): 4.4

**Role.** Two sequential calls per candidate: completeness (question plus visible answer, no sources)
and support (answer, evidence, claims, objective checks, prior corrections, per-assertion judgments).
Code adds objective gates and decides release. A deterministic integrity failure or safety failure
blocks partial release.

| Criterion | Score | Reasoning |
| --- | --- | --- |
| C1 | 7 | Independent review is a clear, valuable role. Two phases are already two roles, and the correction lifecycle, release policy and safety scoring add further duties. |
| C2 | 6 | Gates for scope, sources and arithmetic live in code and cannot be withdrawn by the model. But the decisive step, release, rests on model judgments that are not independently checked. |
| C3 | 5 | Findings point to source subsets, so some judgments can be re-read. There is no ground truth against which the reviewer's verdicts can be scored, and several reviewer statements contradict their own evidence `[AUDITOR-2]`. |
| C4 | 2 | 65 retained rejections in 15 runs. 11 of 25 non-complete runs ended on `invalid_review`, 2 more on the output cap. In run 50 each of three completeness responses carried two distinct tool calls despite `parallel_tool_calls=false` `[AUDITOR-2]`. |
| C5 | 2 | False accept: run 11 was accepted without the required literal excerpt `[OBSERVED]`. False or inconsistent rejections `[AUDITOR-2]`: a scope objection raised in four of four rounds with the scope supplied; assertions judged "contradicted" with reasons stating the opposite; assertions attributed to text absent from the block; a safety score of 2 with a one-character rationale that withheld 11 supported findings (run 48). 31% of rating rationales have two characters or fewer. |
| C6 | 2 | 36% of Luna calls and about 40-50% of a workflow's input tokens (10-14 calls in the long runs, against 2 in a short completion). Support responses of 2-5k tokens hit the 6000-token cap in runs 35 and 38. Retries resend the full payload with accumulating history (35k, 45k and 56k characters over three attempts in run 30). |
| C7 | 8 | The best-traced component: phase status, attempts, rejection conditions and repair events are all recorded. |
| C8 | 8 | Scope and privacy gates are applied in code; unsupported findings are withheld. |

**Structural issues** `[AUDITOR-2]` unless noted.
- A `revise` verdict without a correction is rejected (`zero_sugar.py:1461`), so a reviewer that
  wants to block must attach an obligation. Obligations accumulate (3/6/9/12 in run 21).
- The acceptance rule is all-or-nothing over free text: one false objection among roughly 13
  findings with several assertions each blocks `complete`. `[INFERRED]`
- The default profile assigns the same model family to producer and reviewer, so independence is
  assumed, not shown. `[INFERRED]`

**What would raise it to 7.** Measured false-accept and false-reject rates on known-good and
known-bad answers; a ceiling test (does it accept a human-written ideal answer?); a minimal verdict
contract; a reviewer model different from the producer.

## 9. The system as a whole: 4.7

| Criterion | Score | Reasoning |
| --- | --- | --- |
| C1 Architecture clarity | 7 | Five roles with distinct responsibilities and a clear flow. The model judges and code verifies, which is the right principle. |
| C2 Boundaries | 8 | Fixed manager/date scope, read-only data tools, anonymous-identity exclusion, withheld unsupported output, controls the model cannot withdraw. |
| C3 Verifiability | 7 | Strong replay for numbers and quotes. Semantic correctness has no independent check. |
| C4 Observed reliability | 2 | 7 of 33 completions; none since run 30; none from Gemini since run 26. |
| C5 Output-quality evidence | 3 | No gold answers, no human labels, no repeated trials. Even completed runs had flaws. |
| C6 Efficiency | 2 | Cost per workflow up 6-9x with success falling. No per-component token budget. |
| C7 Observability and testability | 6 | Excellent traces. The 343-392 offline tests passed throughout the live failures, so they do not predict live success. |
| C8 Safety, privacy, scope | 7 | Good controls; free-text redaction, authentication and enterprise integration are unfinished. |

### 9.1 Dimensions beyond the agents

| Dimension | Score | Reasoning |
| --- | --- | --- |
| Problem fit and scope definition | 7 | A real need (manager-facing analysis of authorized data) with sensible limits and a synthetic dataset. |
| Architecture and decomposition | 6 | Roles are sensible; the two overloaded ones (Original, ZeroSugar) are where the failures concentrate. |
| Grounding and traceability | 8 | Source-bound facts, literal-quote checks, source hashes, replayable SQL. |
| Quality assurance design | 3 | The reviewer is the single point of failure for every outcome and its accuracy is unmeasured. |
| Reliability | 3 | 21% completion overall, 0 of the last 7. |
| Cost efficiency | 2 | 6-9x token growth for no measured gain. |
| Security, privacy, scope | 7 | Strong in code; known open items. |
| Observability and auditability | 8 | Private capture, strict checkpoints, dated audits that correct themselves. |
| Testing strategy | 4 | Offline tests with scripted responses follow the last failure; several repairs were never triggered live. |
| Process and change management | 3 | Updates applied without tests, 91 failing tests found against a documented "322 passed", the C1 crash, contract versions v1 to v7 in ten days, checkpoints that any code edit invalidates. |
| Quality validation (human or benchmark) | 2 | None. |
| Documentation | 6 | Extensive and honest about limits, but chronological; the current design is buried under history. |

## 10. Cross-cutting findings

1. **The failures are in the verification layer, not the analysis layer.** The classification step is
   stable and the evidence tools are sound. The reviewer and the answer contract it enforces account
   for essentially every non-completion.
2. **Complexity rose while success fell.** Seven contract versions, 25 rejection codes and a prompt
   several times larger coincide with the end of completions. The causal order cannot be proven from
   these runs `[INFERRED]`.
3. **Cost is a symptom.** Large fixed prompts, whole-payload retries and up to four drafts with two
   review phases each explain the growth. They multiply the same failure rather than reducing it.
4. **Nobody measured the quantity that matters.** Whether an answer is correct is never evaluated
   outside the system. Reviewer accuracy, per-draft quality and a no-review baseline are all missing.
5. **Safeguards worked; recovery did not.** Unsupported output was never released as approved, but a
   protocol failure discarded complete candidates (run 50: a 3,771-character candidate with a table
   and 13 labels, reported to the manager as "no analysis was produced").

## 11. Path to 8: measurable exit criteria `[PROPOSED]`

The thresholds are suggestions to be agreed, not project decisions.

| Target | Evidence required |
| --- | --- |
| ZeroSugar to 7 | On a fixed set of at least 20 candidates (known good, known bad, ideal human answer), false-accept and false-reject rates reported with intervals; ideal answer accepted in at least 4 of 5 trials; no more than 1 protocol rejection per 5 reviews. |
| Original to 7 | Five repeated runs per question with every draft scored against the checklist; scores non-decreasing across drafts in at least 4 of 5 runs; rejection codes per workflow below a stated bound. |
| Vanilla to 8 | Human-labelled sample covering every category; per-category precision and recall reported; a run on more than 20 comments exercising multi-batch retries. |
| Cherry to 8-9 | Three or four numeric questions with gold answers, five runs each, on the current code. |
| Lime to 8 | One live run that plans and exports a chart, inspected by a person. |
| System to 7 | Completion in at least 4 of 5 repeats of at least three distinct questions, as judged by the external checklist rather than the system's own reviewer; input tokens per workflow within an agreed budget; offline suite green before every live run. |

## 12. Sensitivity and limits

- **Weights.** The equal-weight column gives essentially the same ranking. Shifting more weight to
  C4 and C5 would lower ZeroSugar, Original and the system further, because those are their weakest
  criteria.
- **Sample.** One case (13 comments, one manager, one quarter), one run per code version, mostly one
  provider family. Percentages are descriptive, not estimates of a true rate.
- **Confounding.** Code, contract, rubric and reviewer changed together; the effect of any single
  change cannot be isolated.
- **Scores are judgments** informed by measurements. Cherry and Lime scores rest on very few live
  executions and are the least certain.
- **Not re-verified.** All `[AUDITOR-2]` statements. No label or answer was re-judged for semantic
  correctness by the author.
- **Token figures** come from the gateway's per-call usage fields, not a billing reconciliation.
  Character sizes of prompts come from three runs that have private captures.

## 13. Reproducibility

- Completion counts and failure categories: `status`, `execution`, `verification` and `failure` of
  each `reports/apinex_prueba_*.json`.
- Call shares: `model_started` events in `reports/logs/*.jsonl` with profile `apinex_test`, counted by
  agent; other profiles for Lime.
- Rejections: `diagnostics.rejected_attempts` plus `diagnostics.review_history[*].rejected_attempts`,
  grouped by the agent that produced the submission.
- Rating rationales: `ratings[*].rationale` in the stored `verification` blocks of Luna reports.
- Classification stability: `sentiment.<id>.labels` across all runs through 50.
- Prompt sizes: `model_input` events in `reports/logs/details/<run_id>/exchanges.jsonl`.

Artifacts are local and ignored by Git.
