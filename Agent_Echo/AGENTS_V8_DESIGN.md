# Original v8 and ZeroSugar v8: analysis and design, 2026-11-01

**Status.** Implemented as new files at the user's request; existing agents, contracts and
runtime are unchanged and remain the default. Verified offline only: 9 new scripted tests and
the full suite (421 tests, 36.4 s) pass. **No live model call was made**, so nothing here shows
that v8 completes reviews with a real provider. Not committed or published.

| File | Content |
| --- | --- |
| [agents/zero_sugar_v8.py](agents/zero_sugar_v8.py) | `ZeroSugarAgentV8`, review-v8 contract |
| [agents/original_v8.py](agents/original_v8.py) | `OriginalAgentV8`, answer-edit-v2 delivery |
| [tests/test_v8_agents.py](tests/test_v8_agents.py) | Offline delivery tests (scripted judgments) |
| [run_agent_v8.py](run_agent_v8.py) | Same CLI as `run_agent.py`, with both v8 classes |

Sources: [SOLUTION_EVALUATION_1_TO_10.md](SOLUTION_EVALUATION_1_TO_10.md),
[AUDIT_RUNS_51_52_REASONING_VS_SYSTEM.md](AUDIT_RUNS_51_52_REASONING_VS_SYSTEM.md) and its
Addendum A, [IMPROVEMENT_ANALYSIS_SCORES_AND_TOKENS.md](IMPROVEMENT_ANALYSIS_SCORES_AND_TOKENS.md)
revision 3, [CORRECTION_UPDATE_PLAN_2026-11-01.md](CORRECTION_UPDATE_PLAN_2026-11-01.md), and a
full read of `original.py`, `zero_sugar.py`, `runtime.py`, `content.py`, `grounding.py`,
`validation.py`, `review_delivery.py` and `review_v7.py`.

## 1. Scope each agent should have

| | Original | ZeroSugar |
| --- | --- | --- |
| Owns | Planning, delegation, integration, the manager-facing answer, at least one reasoned action, a response to every open correction | Two independent judgments: visible completeness (no evidence) and evidence support (per claim) |
| Model judgment | What to say, which evidence matters, how to phrase it, whether a correction is right | Whether claims are supported, whether labels are defensible, whether requested content is missing, whether an old correction still applies |
| Code, not the model | Quote text and its citation, table rendering, IDs, counts, removal bookkeeping | Quote literalness, table arithmetic and coverage, scope, IDs, correction lifecycle mapping, release decision |
| Must not | Type quotations, restate table numbers, verify itself | Rewrite the answer, re-check code-verified facts, ask for other teams or identities, administer link graphs |

The v7 contracts asked both models to do code's work: Original kept two parallel lists and
matched excerpts to sources by hand; ZeroSugar kept a correction link graph, two booleans per
obligation and structured references for seven ratings. Most terminal stops came from that
work, not from the analysis.

## 2. What failed, and where v8 answers it

Counts from the rejection families in the improvement analysis (revision 2, approximate) and
runs 51/52.

| Family | Agent | Evidence | Root cause | v8 response | Kind |
| --- | --- | --- | --- | --- | --- |
| Excerpt not from the item's cited source | Original | 37 entries, 21 runs, still live | Model must pair an `EX_` reference with matching `citation_ids` | `examples: [{excerpt_ref, label}]`; code derives the citation from the excerpt | Removed by construction |
| Correction link, duplicate, refinement state | ZeroSugar | 42 entries, 11 runs, ended Luna 52 | Link field plus mandatory/addressed must agree | One `status` per obligation (open / satisfied / withdrawn); no link field; refinement goes in the note | Removed by construction |
| Serial validation | Both | Luna 52 found its second error on attempt 4 | First error raised before later checks | Every check runs; all errors return in one feedback with paths and allowed IDs | System fix |
| Removal/reason mismatch | Original | Ended Gemini 51 (7 turns) | Two parallel lists | One `removals: [{block_id, reason}]` list | Removed by construction |
| Growing retry history | Both | Failing loops cost 45-52% of input in 51/52 | Each rejected attempt stays in history | Retries send payload + latest attempt only | Token fix |
| Truncated first support attempt | ZeroSugar | 8 of 17 runs since 10-28 | Reason text for every assertion plus 7 structured explanations | Reasons only for failed assertions; one short note per rating | Token fix |
| False absence objections | ZeroSugar (model) | Luna 52, Gemini 51 | Model misreads a code-rendered table | `visible_inventory` states what is rendered; classification tables reviewed through `label_disputes`; absences naming comment IDs get a code note (revised 2026-11-03: never dropped) | Objective note |
| Out-of-scope and paraphrase objections | ZeroSugar (model) | Luna 52, earlier 4/4 rounds | Model re-checks what code guarantees | Instructions state what code verified and forbid re-checking it | Prompt micro-management |
| Prose about one category citing other labels | Original (model) | Luna 52 "mixed" prose citing positive comments | No check links prose to stored labels | Optional `label_group`; code checks the cited comments carry that label | Objective guard |
| Duplicated content after repair | Original (model) | Gemini 51 | Editing skill | "One idea per item; check saved_answer first" rule; measured by repair cases, not enforced | Model capability, measure |
| Challenge path never used | Original | 0 of 57 offers | Separate tool competing with answering | Inline `correction_responses` (fixed / disputed with note) shown to the next review | Workflow change |
| Revision without a repairable item | ZeroSugar | Draft loops; v7 forced revise on low Accuracy/Safety | Score treated as a blocker | Decision derived from items only; low scores without an item recorded as `unexplained_low_scores` | Contract change |
| Case-specific prompts | Original planner | "For Recognition comment percentages..." | Tuned to the one test question | Neutral planning and role prompts; a test asserts no prompt names the case | Generality |

## 3. Where v8 micro-manages, and where it does not

Micro-management is applied only where the task is mechanical or objectively checkable:

- **Delivery shape.** IDs from enums, one list per operation, derived citations, one status
  per obligation. These are bookkeeping; the model gains nothing by doing them.
- **What not to re-check.** ZeroSugar is told exactly which facts code verified (quotes,
  tables, arithmetic, scope) and that it must not object to them.
- **Requested counts and duplicates.** Original is told to deliver the requested number of
  items and to check its saved answer before adding an idea.
- **Absences that name IDs.** Annotated with the IDs the rendered table shows; the objection always stays (revised 2026-11-03).

Judgment stays free: what an interpretation says, whether a label is defensible, whether a
claim is supported, whether a correction is justified, what action to propose. No rule
inspects wording, and no keyword triggers a rejection.

## 4. Size and token effect

Measured offline on the 13-comment fixture (characters, not tokens):

| Component | v7 | v8 | Change |
| --- | --- | --- | --- |
| ZeroSugar support instructions (with sentiment and action notes) | 15,180 | 3,618 | -76% |
| ZeroSugar completeness instructions | 2,611 | 1,549 | -41% |
| Support tool schema, 4 findings (v7 without its rating-explanation schema) | 8,165 | 6,648 | -19% |
| Original role instructions (v7 also adds ~3.3k of runtime contract text) | 4,580 | 2,576 | -44% |
| Shared policy, unchanged on every call | 2,608 | 2,608 | 0 |

Also removed: duplicated comment text in the review payload (labels now reference evidence),
claim text in delegation results, catalogs in the instructions (now one workspace message
per call, with long fact texts shortened). Original's static instructions no longer change
between turns, so a provider that caches prompt prefixes can reuse them.

`[INFERRED]` On the observed failure loops, joint feedback plus latest-attempt retries would
have shortened them, and the two constructions above remove the loops that ended 51 and 52.
None of this is a measured live saving; a workflow that gets past a loop spends tokens on
work the failed run never reached.

## 5. Other questions

The case so far is one question. v8 avoids case knowledge:

- Prompts name no topic, team or dataset; `test_prompts_do_not_name_the_single_test_case`
  guards it.
- `visible_inventory` describes any rendered table (classification records, or source rows
  with columns and row counts).
- Label disputes and `label_group` appear only when classification records exist; numeric,
  chart and pure-text questions use the ordinary assertion path.
- Numeric coverage, chart review (Lime) and the action policy are kept from v7.

Untested: numeric-only, chart, multi-batch (>20 comments) and clarification questions. The
offline tests use the sentiment fixture only.

## 6. Kept, changed and not supported

**Kept unchanged:** five roles, both review phases with completeness blind to evidence,
assertion-level support review (option B) for every non-classification finding, objective
audits (`audit`, `audit_claims`, sentiment replay), issue-linked safety veto, source-facts-v7
canonical payload and renderer, evidence handoff checks, three attempts per phase plus the
shared protocol exception, the four-draft bound, the support-failure repair handoff
(`ReviewRepairNeeded`), partial release through the inherited `incomplete()`, planning
validation, specialists, budgets and limits.

**Changed, needing explicit approval before any live use** (each departs from an earlier
decision):

1. Ratings carry one short note instead of review-v7's structured `rating_explanations` with
   references and a repair call.
2. The overall decision is derived from items; a low score alone no longer forces revision.
3. A completeness "revise" with no missing item is accepted, its rationale kept as a
   suggestion.
4. (Withdrawn 2026-11-03.) Dropping an absence ground whose named IDs are rendered was a defect: in the
   smoke run those IDs named comments to quote, so a table row did not satisfy the objection.
5. Obligations take one status; there is no link field (it goes further than Addendum A.2
   option 2 by removing links entirely).
6. The challenge tool is replaced by inline correction responses.
7. Classification tables are reviewed through label disputes instead of free assertions.

**Not supported:** `--resume` of v8 workflows (it raises), the offline `--demo` fixtures (they
emit v7 tool names), and continuation of saved v7 checkpoints with v8 code.

## 7. Verification and next steps

Run offline:

```powershell
..\Echo_UI\.venv-windows\Scripts\python.exe -B -m unittest discover -s tests -p test_v8_agents.py
```

The tests check delivery mechanics with scripted judgments: absence annotation, flat support schema, joint errors
and latest-attempt retries, label disputes routed to Vanilla, obligation status with
Original's dispute visible, low scores without items, derived example citations replaying
in review, joint Original delivery errors, mandatory correction responses, and neutral
prompts. They do not measure judgment quality.

`[PROPOSED]` before any live comparison:

1. Approve or reject the seven changes in section 6.
2. Run the nine-case reviewer instrument through `ZeroSugarAgentV8` (reviewer-only), add
   a realistic 13-row candidate (CORRECTION_UPDATE_PLAN M1), and compare false objections
   with review-v7 on the same cases.
3. Build the Original repair cases (M2: R1-R6) and run them through `OriginalAgentV8`.
4. Only then, one fresh workflow per profile with `run_agent_v8.py`, new output filenames
   and unchanged budgets, assessed externally.

## 8. Smoke run and revision, 2026-11-03

The user ran the reviewer smoke (B1, B2, B7, B15; v7 and v8; `apinex_test`; one repeat;
results `reports/gold_v1/results_apinex_test_20261103_091327.json`). All 8 reviews completed.
Two v8 defects were found in this code, not in the model:

1. **Absence guard.** In B2 and B15 the v8 reviewer did report the missing excerpts, naming the
   comments that should be quoted in `missing_source_ids`; code dropped those objections because
   the IDs were in the per-comment table. Fixed: the objection is always kept, with a `code_note`
   stating which named comments the table shows; the reviewer and Original judge it.
2. **Truncation.** All 3 truncated v8 support attempts sent the keyed `findings` object as an
   escaped JSON string and then emitted padding whitespace until the 6000-token cap; all 5
   completed attempts sent an object. Fixed: `assertions` and `label_disputes` are flat arrays
   with a `finding_id` per item, the instructions and compact retry forbid strings containing
   JSON, and a stringified list is rejected with feedback. Support schema on the fixture:
   6,648 to 5,089 characters. v7 truncations had a different cause (long verbose output) and v7,
   the comparison baseline, is unchanged.

The first smoke's v8 results came from the earlier code, so they are not comparable with a rerun.
The flat schema gives up per-finding citation enums; citations are still checked per finding in
code, with the allowed IDs in the feedback. 427 offline tests passed; no live call was made.

### Second smoke and delivery normalizations, 2026-11-03

Second smoke (`results_apinex_test_20261103_094501.json`): no truncation in v8, but B2 and B15
failed support delivery after three attempts on four mechanical slips: assertion citations
from another finding (a cost of the flat schema), omitted findings (mostly the application
boundary text and tables), `policy_requirement` with a wrong owner or excerpt, and label
"disputes" proposing the stored label. Revised on the user's instruction, with diagnostics in
`delivery_normalizations`:

1. Citations outside the finding are removed; a supported factual assertion left with none
   is still rejected.
2. `policy_requirement` gets owner Original and request_ref null, its only valid values.
3. A dispute proposing the stored label is dropped as a no-op.
4. The renderer's application boundary statement (`limitation`, `application_boundary`) is
   no longer requested from the reviewer; it is marked application text and stays covered
   by the objective audit. **This changes the "review every finding" invariant for that one
   application-generated block and was approved by the user on 2026-11-03.**

Omitted model findings remain an error; no judgment is inferred. 428 offline tests passed;
the v8 results of both earlier smokes predate this code.

### Explicit action, category and dispute judgments, 2026-11-03

Across the smokes no reviewer (v7 or v8, Luna or Gemini) reported the missing manager action
in B15, both v8 runs on Gemini disputed labels they themselves called defensible, and prose
grouping a positive comment as mixed (B7, B15) was caught inconsistently. Revised on the
user's instruction; the model states each judgment explicitly and code derives the
consequence:

1. `manager_actions` (when `require_actionable`): the proposal findings the reviewer judges
   to be concrete manager actions. An empty list creates the policy correction (owner
   Original) in code, unless the reviewer already raised one.
2. `category_claims` (when classification records exist): which sentiment category an
   interpretation describes. Code compares each cited comment with its stored label; a
   mismatch withholds the finding and creates an Original correction naming the comments.
3. `label_disputes[].stored_label_defensible`: a dispute the reviewer marks defensible is
   dropped as a no-op.

Which proposals are actions, which category a sentence describes and whether a label is
defensible remain model judgments; no wording is inspected. The producer side (Original v8
typing its proposals as action or team question) is not implemented; M1 measures the
reviewer only. 432 offline tests passed; no live call by the assistant.

`manager_actions` is requested only when every finding carries a renderer kind (a
source-bound answer). For an untyped legacy answer there are no proposal findings, so an
empty list would mean nothing; the reviewer then uses the earlier instruction (raise a
`policy_requirement` new issue). Covered by an offline test; 433 tests passed.

### Corrections after the fourth Luna/Gemini smokes, 2026-11-03

Captures of `results_apinex_test_20261103_110552.json` and
`results_apinex_gemini_test_20261103_111744.json` showed: the reviewer listed every proposal,
team questions included, as a manager action (so B15 stayed undetected) and once listed none
(a code-derived false policy correction in B7); a two-category paragraph (B15 F4, negative and
mixed) produced a false category mismatch; completeness called a code-copied excerpt a
paraphrase; and an `assertion_evidence_required` rejection made the reviewer downgrade a
supported claim. Revised on the user's instruction:

1. `manager_actions` is replaced by `proposal_types`: every proposal finding is classified
   exactly once as `action`, `team_question` or `other`; no `action` creates the policy
   correction. Per-item classification replaces "list the ones that are".
2. `category_claims[].labels` accepts several categories; only cited comments whose stored
   label is in none of them mismatch. A finding withheld by this check shows that reason.
3. Completeness instructions state that every `Excerpt: "..."` was copied by code and is literal.
4. A supported factual assertion without citations receives its finding's citations
   (`supported_assertion_citations_defaulted`) instead of a rejection.

Whether a proposal is an action and which categories a paragraph describes remain model
judgments. 435 offline tests passed; no live call by the assistant.

### Instruction adjustments after the 3-repeat smokes, 2026-11-03

With three repeats per model, v8 scored 12/18 (Luna) and 14/18 (Gemini) against v7's 10/18
and had no protocol failures, but B1 was accepted only 1 of 3 times per model and Luna typed
B15's requested follow-up questions as actions. Instruction-only adjustments, on the user's
instruction: proposals are classified by what the user asked for (requested questions are
`team_question`, requested actions or recommendations are `action`); stored labels are taken
as given in assertions and disputed only in `label_disputes`; a short contiguous fragment
satisfies a request for a short literal excerpt. No code path changed. 435 offline tests
passed; re-measurement is limited to v8 on B1 and B15 (v7 unchanged).

## 9. Adoption of ZeroSugar v8, 2026-11-04

After the adjudicated gold M1 (GOLD_V1_RECORD.md), the user adopted ZeroSugar v8 as Echo's
reviewer for every profile and kept Original v7. `OriginalAgent.reviewer_class` is now
`ZeroSugarAgentV8` (workflow review and the v7 `challenge_corrections` path, whose challenge is
shown to v8 as a disputed obligation), and `run_agent.py zerosugar`/`lime` use v8. The offline
`--demo` fixture now speaks review-v8. Kept on review-v7: legacy phase-only resumption
(`agents/resume.py`, saved checkpoints need their own implementation) and the scripted Original
workflow tests, pinned to v7 in `tests/test_agents.py` as review-v7 regressions. The adoption
accepts the contract changes listed in section 6 for the reviewer. Original v8 remains
unadopted and unmeasured (M2). 437 offline tests and the demo passed; the first live
end-to-end workflow with Original v7 + ZeroSugar v8 is pending.

### First live end-to-end run with ZeroSugar v8: Luna 53, 2026-11-04

`reports/apinex_prueba_vanilla_53.json` (log `20261104_071938_52a2d1cb5a44`), same question,
scope and budgets as runs 51/52, Original v7 + ZeroSugar v8: **complete / accept**, the first
complete workflow since run 30. 17 calls, 306 s, 181,052 input tokens (Luna 52: 269,775;
Gemini 51: 324,402). Three drafts, three completed reviews, no protocol failure; three
rejected review submissions were repaired, 17 delivery normalizations applied.

- Draft 1 had only team questions (four, duplicated); v8 derived the missing-action policy
  correction from `proposal_types`.
- Draft 2 added one action (its text cut off) but dropped the two requested questions;
  completeness accepted it and support kept only the action obligation open, so the missing
  requested questions were not reported.
- Draft 3 restored the questions and kept both the cut-off action and a full second copy, and
  repeated the whole analysis (population, labels, illustrations, pattern, limitation) twice.
  v8 accepted it. The gold treats a repeated example as harmless (B13), but the accepted
  answer also states "each respondent submitted one comment", which anonymous comment data
  cannot establish, and attributes the "access is inconsistent" concern to CMT27512.

Acceptance is not answer quality: duplication comes from Original v7's repairs (adding blocks
without removing earlier ones), and the reviewer missed the dropped questions and the
unsupported claim. No code change followed this run.

### Live run Gemini 54 (Original v7 + ZeroSugar v8), 2026-11-04

`reports/apinex_prueba_gemini_54.json` (log `20261104_072839_e4fd5061fdc1`): **partial**, stopped at
the 32-call limit after 596 s and 547,533 input tokens; 15 findings released from the third
reviewed candidate. Original used 13 calls and 349,890 tokens: seven delivery rejections
(`answer_removal_reasons` five times, `narrative_count`, `excerpt_source`) and, in the second
repair, a recalculation request sent to Cherry, which declined it (5 calls). The released
answer repeats its coverage, critical and mixed paragraphs. v8 again raised the missing action
on draft 1. It then marked a CMT27511 label dispute defensible (dropped) yet raised the same
concern as a Vanilla-owned new issue on the classification findings in reviews 2 and 3, which
alone kept the last candidate at revise; the annotator's gold accepts mixed for CMT27511.
Original v7 then wrote a labeling paragraph into the answer. No code change followed this run.

## 10. Original v8 duplicate guard, 2026-11-04

Gold M2 (one Original repair round per R case; `GOLD_V1_RECORD.md`) showed that v8 follows
corrections better than v7 and never lost must-keep content, but most of its repairs added a
second copy of something already saved. This is a system gap, not a reasoning one: the
contract keeps saved blocks unless they are removed, and nothing checked whether an addition
repeated one. The instruction "never add a second copy" was already in the prompt.

`check_submission` now compares every new item with the blocks that stay (saved minus
removals, plus reused) and with the earlier new items of the same submission:
- a literal example repeats another when both quote the same sources (a longer excerpt of
  CMT27500 beside the saved short one);
- any other interpretation or proposal repeats another of the same kind when their content
  words, ignoring citations and a short leading label such as "Team question:", overlap by
  word Jaccard 0.6 or more.
Calibration on the gold answers: distinct items of B1 overlap at most 0.25, and the copies
re-added in M2 at 0.6-1.0. Copies already inside the saved draft (B13) are left alone;
removing them is the correction's job.

First version, rejected: a repeat was the `duplicate_item` delivery error. The v8 M2 rerun
(36 repairs, `GOLD_V1_RECORD.md`) showed why that fails: models resubmit the whole answer as
new items, the error then listed up to 7 repeats, and the retry removed the saved blocks *and*
dropped the restatements, so about a third of the repairs lost paragraphs, the action or a
question. Current version, normalization: a new item that repeats a kept block replaces it
(code adds the removal, reason "Restated by a new item; code keeps the new version."), and a
repeat inside the submission is dropped. No retry is spent and nothing is lost; the event
`answer_duplicates_normalized` records the counts. Offline replay of the 36 logged first
submissions through the normalization: 29 accepted in one call with all must-keep content and
no duplicate; the other 7 also carried a `label_group` error that a live retry would fix.

Not covered: a rephrased copy below 0.6 overlap, and Original v7, which stays in production.
Offline tests: `tests/test_gold_cases.py` (restated question replaces the saved one in one call;
full restatement loses nothing; second excerpt of a saved example; no false positive on B1). Next measurement: rerun M2 for v8.

## 11. Adoption of Original v8, 2026-11-04

The user adopted Original v8 after the adjudicated M2 (section 10, `GOLD_V1_RECORD.md`): v8
made the requested change in 18 of 20 repairs (v7: 5 of 10), lost must-keep content in 3 of 24
(v7: 6 of 12) and no longer duplicates. Changes:
- `run_agent.py` imports `OriginalAgentV8 as OriginalAgent`; its reviewer is ZeroSugar v8.
- `agents/resume.py` full-workflow continuation refuses, because a checkpoint with matching
  code comes from an Original v8 workflow, which cannot resume; legacy phase resume keeps v7.
- `ScriptedDemoModel` answers v8's `submit_answer` with workspace IDs, so `--demo` accepts.
- `run_agent_v8.py` is now equivalent to `run_agent.py`.
Not yet run live in the full workflow (planning, specialists, review, repair). Open from M2:
R2 removes a saved requested excerpt while adding another; R6 is mostly answered "fixed".
