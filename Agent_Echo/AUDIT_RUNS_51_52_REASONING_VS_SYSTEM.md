# Runs 51/52 error audit: model reasoning versus Echo system, 2026-11-01

Read-only audit of the latest live pair (Gemini 51, Luna 52), with carry-over from runs 49/50.
It separates model reasoning errors from Echo system errors and proposes corrections. Nothing
here is approved or implemented; no runtime change, test, model call or publication was made.

Sources: [RUNS_51_52_ANALYSIS.md](RUNS_51_52_ANALYSIS.md),
[SOLUTION_EVALUATION_1_TO_10.md](SOLUTION_EVALUATION_1_TO_10.md), the project knowledge graph
(`graphify query`), `diagnostics.rejected_attempts` / `review_history[*].rejected_attempts` of
`reports/apinex_prueba_gemini_51.json` and `reports/apinex_prueba_vanilla_52.json`, and the
cited code lines.

**Evidence labels.** `[OBSERVED]` checked against saved reports or code for this audit.
`[ANALYSIS]` taken from RUNS_51_52_ANALYSIS.md, not re-verified. `[INFERRED]` the author's
reasoning. `[PROPOSED]` a suggestion.

## 1. Conclusion

Reasoning errors lowered answer quality, but neither run stopped because of them. **Both
terminal stops were administrative bookkeeping**, with unused global budget `[OBSERVED]`:

- Gemini 51: Original spent its 7 turns on the same code, `answer_removal_reasons`; the
  removed-block list and the reason list never matched.
- Luna 52: ZeroSugar ended in `review_protocol_error` after three `correction_duplicate`
  rejections and one `correction_refinement_state` rejection.

This matches the 1-10 evaluation: Original is asked to be both a good analyst and a precise
serializer, and the serializer role is what fails.

## 2. Observed errors

| # | Error | Run | Evidence |
| --- | --- | --- | --- |
| E1 | Reviewer says CMT27506/07/11 are missing from a complete 13-row table; one reason says 11 rows | 52 | Source-built table replay contradicts it `[ANALYSIS]` |
| E2 | Completeness says 12 rows and no denominator; answer has 13 rows and `Eligible_Comments=13` | 51 | Captured answer `[ANALYSIS]` |
| E3 | Out-of-scope-team objection repeated despite trusted authorization context | 52 (and 4/4 rounds earlier) | `[ANALYSIS]`, `[AUDITOR-2]` |
| E4 | A literal CMT27500 quotation called a paraphrase | 52 | Source extraction `[ANALYSIS]` |
| E5 | Completeness checks source literalness, which belongs to support | 51 | `[ANALYSIS]` |
| E6 | Demands an anonymity declaration the user did not request | 52 | `[ANALYSIS]` |
| E7 | Original repair adds duplicated examples/questions instead of consolidating | 51 | `[ANALYSIS]` |
| E8 | Mixed-comment prose cites CMT27510/12, both stored positive | 52 | Stored labels `[ANALYSIS]` |
| E9 | Original removes 19 blocks (near rewrite) and sends 7 different removal/reason combinations | 51 | `[ANALYSIS]`; 7 rejections `[OBSERVED]` |
| E10 | Removal-reason feedback is generic; no missing/extra IDs (`detail: {}`) | 51 | [content.py:173-179](agents/content.py:173) `[OBSERVED]` |
| E11 | Serial validation: duplicate raised in `resolve_corrections` before refinement-state checks run; second error first surfaced on attempt 4 | 52 | [zero_sugar.py:1439](agents/zero_sugar.py:1439) precedes [:1450-1470](agents/zero_sugar.py:1450); raise at [content.py:109](agents/content.py:109) `[OBSERVED]` |
| E12 | One fact encoded twice: a `related_correction_id` link also requires `mandatory=true/addressed=false`. Luna contradicted it on both candidates (turn 2 of the first review too) | 52 | `review_history[0]` and `[1]` `[OBSERVED]` |
| E13 | Removal/reason counts are recorded only on success; rejected submissions leave no count | 51 | [runtime.py:421-430](agents/runtime.py:421) `[OBSERVED]` |
| E14 | A source-faithful canonical table withheld under a false absence objection | 52 | `[ANALYSIS]` |
| E15 | One supported/withheld count hides false versus legitimate withholding; final completeness rationale may come from an earlier phase | 52 | `[ANALYSIS]` |
| E16 | CMT27512 positive (Luna) versus mixed (Gemini) | 51/52 | Classifier disagreement, not a defect |
| E17 | Legitimate omissions: missing literal examples, missing critical example | 52 | Must not be dismissed because other objections are false |
| E18 | 270-324k input tokens for a partial result | 51/52 | Provider counters `[ANALYSIS]` |

## 3. Classification

**A. Model reasoning:** E1-E8, E16 (E17 is a correct objection).

Do not fix these with wording rules ("do not say the table is missing", "do not ask for
scope"). That is micro management, conflicts with project guidance against language-pattern
rules, and enlarges a prompt that is already about 40k characters. Instead `[PROPOSED]`:

- Measure first: run the nine-case instrument reviewer-only, on fixed candidates, for both
  providers, to obtain false-objection rates. No such number exists today.
- Reviewer independence: a different model family from the producer (evaluation C3/C5).
- Reviewer-only reassessment of a false objection, without forcing Original to rewrite;
  this cuts the loop that produces E7.
- No rules for E8 or E16: support review and a human-labelled sample cover them.

**B. Echo system:** E10, E11, E13, E15.

**C. Hybrid (system-induced model error):** E9, E12, E14. The model errs, but the contract
asks it to keep two representations of one fact in sync. Both terminal stops fall here.

## 4. Proposed corrections

**P1: system, cheap, no semantic change**

1. Joint validation (E11): `resolve_corrections` collects the duplicate instead of raising,
   and it is emitted with `refinement_errors` and finding errors in one `additional_errors`.
2. Localized removal feedback (E10): `missing_reason_ids`, `extra_reason_ids` (including a
   reason for an already removed block) and `duplicate_reason_ids` in the error details.
3. Diagnostics on rejection (E13): record `removed_count` and `reasons_supplied` for rejected
   submissions as well.
4. Reporting (E15): a withholding-reason category per withheld finding; raw support
   explanations kept apart from merged final ratings.
5. Offline fixtures from real captures: the turn-1 payloads of Luna 52 and Gemini 51. The
   412-test suite passes but does not predict live behavior.

**P2: contract simplification (removes administrative micro management; needs user decision)**

6. One list (E9): replace `remove_ids` + `removal_reasons` with
   `removals: [{block_id, reason}]`, making mismatch impossible. Lighter alternative: a
   missing reason becomes a diagnostic, not a block; it is an explanation field, not an
   integrity field, and it currently discarded a whole draft.
7. One encoding (E12): code derives `mandatory/addressed` for a linked correction, or
   `related_correction_id` is removed and code links by origin. **This contradicts an
   existing decision**: feedback currently "offers both valid encodings without choosing the
   model's meaning". The evidence is that the model contradicted itself on 2 of 2 candidates.

**P3: objective, not semantic, protection**

8. Canonical table (E14): when a block is code-rendered from source and coverage is already
   code-verified, an objection claiming absent IDs is checked against the IDs present, using
   structured IDs in the correction rather than text patterns. This is a coverage check, not
   a language rule, but the boundary is narrow and should be agreed first.

**Not recommended:** more prompt text, more retries (52 shows extra capacity does not fix
serial feedback), keyword rules, further live runs before P1 and the measurement in section 3.

**Suggested order:** P1, then the reviewer-only measurement, then a decision on P2, then P3.

## 5. Limits

- No label or answer was re-judged for semantic correctness. E1-E8 come from the runs 51/52
  analysis and were not re-verified; complete `exchanges.jsonl` files were not read.
- One case, one run per provider on frozen v7 code; counts are descriptive.
- Proposal 7 conflicts with an existing contract decision and is not a normalization.

## Addendum A - external review response, 2026-11-01

An external reviewer (ChatGPT, supplied by the user) reviewed this audit against the
relevant captures. This addendum records the response. Sections 1-5 above are preserved as
written; where this addendum corrects them, the addendum governs. No runtime, agent or code
change, test, model call or publication was made.

**Verified in the review.** The remaining global budgets match the reports: Gemini 51 used
19 of 32 calls in 420.766 s, Luna 52 used 16 of 32 in 351.593 s, against a 1000-second limit
`[OBSERVED]`. The reviewer's statement that the current code matches the 29 runtime files of
the live pair was not re-verified here; only Markdown documentation changed since then.

### A.1 Point-by-point response

| # | Reviewer observation | Response | Effect on this audit |
| --- | --- | --- | --- |
| 1 | An administrative stop does not mean the reasoning was sound | **Accepted** | Section 1 read as minimizing reasoning errors. The clearer split has three parts: (a) models generated incompatible arguments, (b) Python recovery was insufficient, (c) content judgments were wrong. Category C ("hybrid") mixed (a) with (b) |
| 2 | Gemini 51: Original added repetitions after ZeroSugar had already withdrawn the false count/denominator/quote objections and kept a legitimate repeated-questions correction | **Accepted; strengthens E7** | Editing deterioration cannot be attributed to reviewer instructions. Consistent with RUNS_51_52_ANALYSIS.md |
| 3 | E12 ("one fact encoded twice") oversimplifies; the link names the obligation, mandatory/addressed state whether it is still required and satisfied | **Accepted with nuance** | See A.2. Proposal 7's derivation option is withdrawn |
| 4 | E13 applies to summary diagnostics only; full captures retain both lists | **Accepted** | E13 overstated the gap. Evidence was not lost; it was absent from summaries and had to be reconstructed from `exchanges.jsonl`. It becomes a diagnostic convenience, not an observability defect |
| 5 | Canonical-table protection must stay objective | **Accepted** | An ID being present proves neither its sentiment label nor the interpretation. P3.8 may only remove an *absence* ground for withholding; any other ground keeps the block withheld |
| 6 | A different reviewer model family is a hypothesis to evaluate | **Accepted** | Recast as an A/B experiment after the nine-case reviewer-only measurement, not an improvement |
| 7 | `removals: [{block_id, reason}]` is sound but still needs checks | **Accepted** | Duplicate, identity and preservation-of-requested-content checks remain required |
| 8 | The open problem is not only Python accepting the model's output: ZeroSugar must recognize what is present and Original must improve the candidate when repairing | **Accepted and extended** | The nine-case instrument measures the reviewer only. No instrument measures whether an Original repair improves a candidate; see A.4 |

### A.2 E12 and proposal 7

Both readings are partly right.

- **The redundancy exists in the current contract.** For a linked correction, code requires
  `mandatory=true/addressed=false`, so for linked IDs the state is fully determined by the
  link: it either matches or conflicts. The field carries no free information there.
- **Deriving the state would hide a real ambiguity.** Luna's `addressed=true` plus a link can
  mean either "the obligation is still open and the state was miscoded" or "the obligation is
  satisfied and this is a new related issue that should not have been linked". Deriving picks
  the first reading and can retain a false requirement, which is the risk the reviewer names
  and the reason for the existing "offer both valid encodings" rule.

**Revised proposal 7 `[PROPOSED]`.** The option "code derives mandatory/addressed for a linked
correction" is withdrawn. Two options remain:

1. No contract change: report the conflict jointly with other independent errors (P1.1) and
   keep offering both valid encodings, as the current guidance requires.
2. Contract change, requires a user decision: the link becomes informational lineage that
   does not fix lifecycle state, so linking to an addressed correction is valid and the
   conflicting state cannot arise. No judgment is inferred by code.

Separately, Luna repeated the same duplicate link three times after localized feedback
naming the identity and both indices. That is a model compliance failure, not a parser one.

### A.3 Corrected statements

| Original statement | Corrected statement |
| --- | --- |
| Section 1: "Reasoning errors lowered answer quality, but neither run stopped because of them." | Both terminal stops occurred at administrative validation, but the arguments that failed it were model-generated (Original in 51, ZeroSugar in 52), Python recovery reported them insufficiently, and content judgments were wrong independently of the stop. |
| Section 3: "C. Hybrid (system-induced model error): E9, E12, E14." | E9 and E12 are model errors made easier by contract design; E14 is a model content error whose effect on publication follows the release policy. |
| E13: "rejected submissions leave no count" | Summary diagnostics and the short log carry no removal/reason counts for rejected submissions; the private captures retain both lists. |
| P2.7: "code derives mandatory/addressed for a linked correction" | Withdrawn; see A.2. |
| P3.8: absence objections checked against IDs present | Unchanged in scope, limited in effect: it can only remove an absence ground for withholding and certifies neither labels nor interpretation. |
| Section 3.A: "a different model family from the producer" | A hypothesis to test by A/B comparison after the reviewer-only measurement. |

### A.4 Effect on the companion improvement analysis

The reviewer did not review
[IMPROVEMENT_ANALYSIS_SCORES_AND_TOKENS.md](IMPROVEMENT_ANALYSIS_SCORES_AND_TOKENS.md), but
points 3, 5, 6, 7 and 8 apply to it. That document is not edited by this addendum; these
corrections govern its items until it is revised:

- **Z3** (derive linked-correction state) is withdrawn, as in A.2.
- **O1** (declarative final block list) is riskier than stated. Today a saved block stays
  unless it is listed in `remove_ids`; a declarative list turns an omitted block into a silent
  deletion, the content loss already observed in run 47. The single `removals` list is
  preferred, with the checks in A.1 point 7.
- **Z6** (different reviewer family) is an experiment, as in A.1 point 6.
- **Z7** (canonical-table absence check) has the limit in A.1 point 5.
- **New item:** fixed repair cases for Original (a saved candidate plus a legitimate
  correction, scored against a fixed checklist) to measure whether repairs improve a candidate.
  No such instrument exists today.

Token figures and the order P1, then measurement, then contract decisions are unchanged.

### A.5 Limits of this addendum

The removal/reason combinations cited by the reviewer (19/20, 19/6, 19/14, 6/14) were checked
against RUNS_51_52_ANALYSIS.md, not re-read from the captures. No semantic re-judgment of
labels or answers was made.
