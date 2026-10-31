# Proposed update plan after Gemini 44 and Luna 45

Date: 2026-10-30 (America/New_York).

Status: execution authorized by the user on 2026-10-30, including local verification and
one live workflow per Gemini/Luna with connection retries. See DELIVERY_RELIABILITY_UPDATE.md
for actual implementation and evidence; the plan text below preserves the original scope.
GitHub publication is not included. Semantic human confirmation remains a diagnostic follow-up.

Revision after G1-G6: only application mechanisms and diagnostic reporting are proposed
for change. Model reasoning, sentiment definitions, reviewer judgment rules, prompts,
acceptance policy and release policy are outside this update. U5 is diagnostic, not a
semantic release gate. No audit appendix is created by this revision.

Execution result: the system mechanisms and local regression checks are implemented.
The requested live pair and connection retries were executed: Gemini 46 network failed
in structured answer delivery, Luna 47 network finished partial/revise. U5 remains a
diagnostic evaluation with human confirmation pending, as intended. Saved-request size
comparisons are controlled projections; actual new call sizes are reported separately.
See [the delivery record](DELIVERY_RELIABILITY_UPDATE.md#live-completion-gemini-46-and-luna-47-2026-10-30).

## Outcome and scope

Make repairs actionable, keep corrections attached to the content they concern, and
make partial results understandable. Evaluate reviewer judgment separately from software
delivery. Preserve the five roles and the existing tools; no installation is needed for
the proposed application changes or offline tests.

Start with the current Windows checkout and its existing
`Agent_Echo/.venv/Scripts/python.exe`. Runs 44/45 used identical application manifests,
which matched the current source when this plan was prepared. Their raw reports,
exchanges and checkpoints remain historical evidence, not editable fixtures.

The main references are [Addendum C](AUDIT_2026-10-30.md),
[the earlier audit](AUDIT_2026-10-29.md),
[the delivery record](DELIVERY_RELIABILITY_UPDATE.md), and
[the testing guide](TESTING_AND_RAG.md).

## Evidence corrections this plan uses

These refinements do not rewrite either audit.

| Observation | Working conclusion for implementation |
| --- | --- |
| A6 recovered two truncated Gemini support responses; A22 stopped both runs after draft 4 | Preserve both mechanisms. Neither proves semantic accuracy. |
| A20/A21's specific cases did not occur in the live pair | Retain their offline regression coverage; do not claim new live validation. |
| Luna F2 attributes a positive comment to the mixed group | A real generation/synthesis error. |
| Luna's final F4/F6 are rejected for content they do not contain | Reviewer errors, not established citation/content defects. Addendum C observation 28 must not be used as proof that all three rejections were justified. |
| Luna publishes F5/F12 while retaining old complaints with those numbers | The old complaints originate in draft 3; the final F5/F12 contain different text and are supported by draft 4's review. Investigate identity and historical-obligation presentation, not an assumed bypass of current withholding. |
| Luna has 15 correction entries and 12 distinct issue texts | Exact text duplication is established. Text uniqueness alone does not establish the number of independent semantic obligations. |
| Luna has a prose classification and a stated denominator | A per-comment table or a separate denominator row is not mandatory. The published answer still lacks an excerpt illustrating a positive view. |
| Gemini's reviewer says the category counts sum to 11 and approves a false "both comments" attribution | Reviewer mistakes coexist with valid objections. Review completion is not a correctness score. |
| Automatic assertion repairs say to consult assessments, but compact repair inputs omit them | A confirmed system information-loss defect. Fix this before judging repair convergence. |
| Gemini received duplication corrections in drafts 2-4, including explicit removal instructions, yet rendered excerpt tags rose from 2 in draft 3 to 4 in draft 4; the final published answer had 5 paragraph pairs with Jaccard >= 0.9 | Exact resolved-item deduplication already exists in `content.py`; default retention also exists. Near-identical blocks survive. U3 owns mandatory per-draft reporting; U4 addresses only the exact inline quote case. No similarity-based deletion is proposed. |
| Luna's F6 critical excerpt was falsely rejected, but the same excerpt remained supported and published in F8 | Record a false rejection, not loss of the entire requested critical illustration. The missing published positive illustration is a separate omission. |
| No `challenge_corrections` call occurred in either run 44 or 45 | The mechanism exists, but this pair provides no live evidence that it is used or resolves a dispute. |

## Boundaries retained throughout

- Four total drafts: the initial draft and at most three repairs. Three attempts per
  review phase; existing shared call/time budgets, pacing and output caps remain.
- Both review phases, source/scope/privacy checks, literal quotation checks,
  complete finding coverage, arithmetic replay and whole-finding withholding remain.
- Original can challenge an unjustified correction; ZeroSugar independently judges
  correction disposition. No automatic semantic acceptance or silent obligation closure.
- No mandatory per-question checklist, new wording rejection rules, grouped review,
  new role, provider switch, schema relaxation or reduced evidence/assertion coverage.
- Keep historical answer/review replay and strict checkpoint identities. Changed code
  needs fresh runs; never edit old checkpoint fingerprints to resume them.
- Keep detailed source text private. New trace metadata uses identifiers; it does not
  copy questions or sources into short logs or public projections.

## Batch 1: repair information and identity first

### U1 - Deliver the rejected assertion assessments once

Priority: first implementation task.

Change `agents/zero_sugar.py` where assertion repairs are derived, and
`agents/original.py` where repair context is assembled. For each such correction,
include its origin candidate/finding identity and the rejected assertion's claim,
assessment, reason and source IDs. Supply this detail once, alongside the existing
pending correction. Do not restore the entire serialized verdict or repeat the evidence.

Use existing retained review data. The application supplies identities and assessments;
the model does not reconstruct missing feedback. Preserve all failed assertions rather
than selecting a sample to save tokens. Report the actual size of the complete repair
request and continue under the unchanged execution/provider limits and error handling.
U1 introduces no new size threshold or size-based rejection and never silently drops
required detail. Existing provider or execution failures remain explicit failures.

Restoring missing assessments can increase the request before duplicate sections are
removed; no reduction is predicted in advance. Before any new live pair, U6 must produce
an offline before/after size report for the same scripted inputs, including the assessment
detail added by U1 and the size of every repair round. A large observed packet is reported
as such, not treated as a new semantic or acceptance failure.

Verification: a scripted failed compound finding reaches Original with every rejected
assertion and its reason; supported unrelated findings and the evidence remain available;
the full verdict and source packet are not duplicated. A second scripted case covers
repair after an incomplete support phase, without treating it as approval.

### U2 - Bind corrections to their original and current content

Priority: implement with U1 before interpreting another live repair.

Reuse existing candidate identities and `BLOCK_` content identities. Keep finding labels
such as F4 local to their candidate. Provide a compact mapping from an origin finding to
the saved block(s) Original can edit; expose current identity separately when the block
survives. A removed or replaced block has no automatic same-number successor.

Carry origin metadata through correction refinements and the existing lifecycle. Use
the existing `related_correction_id` mechanism for an explicitly recognized recurring
obligation. Reuse deterministic identity only for the same bound issue on unchanged
content; similar prose is not sufficient to merge issues. Broader equivalence remains a
model judgment, with history preserved. Do not restore the removed consolidation graph.

Expected owners: `zero_sugar.py`, `original.py`, `content.py`, and shared result/capture
readers only where the new metadata crosses their boundary. Prefer additive internal
metadata to changing model-authored fields or the established answer contract.

Verification: reorder and replace blocks across four scripted drafts. A draft-3 F5
correction never attaches to an unrelated draft-4 F5. An unchanged offending block stays
blocking, a genuine replacement is reassessed, and a false objection can be explicitly
withdrawn. Identical text about different blocks is not automatically merged. Stored
older reports remain readable without invented origin mappings.

Exit from batch 1: U1/U2 regressions pass and every repair instruction can be traced to
the actual content and assessments it names. Do not optimize the packet further before
this information-preservation check passes.

## Batch 2: publish an accurate account of the result

### U3 - Separate current gaps, historical obligations and execution failures

Use `agents/findings.py` and `OriginalAgent.incomplete()` to produce self-contained
manager-facing limitations. Describe the affected topic and actionable gap, not an
unresolvable internal label such as "Finding F5". Distinguish an unresolved complaint
about an earlier version from a current failed finding; preserve the detailed records
privately and do not silently close the earlier obligation.

Report correction-entry counts separately from known unique obligation counts. Deduplicate
display messages only; do not claim that 12 unique strings prove 12 independent problems.
When identity cannot be established, report that uncertainty instead of a fabricated count.

Show reviewed/supported/released counts and the reason for a partial or failed result.
A provider failure with no candidate must say that no analysis was produced, rather than
request correction of nonexistent conclusions. Do not change the last-completed-review
release rule to solve misleading limitation wording.

Record the raw completeness and support decisions, final disposition and candidate ID
together for each draft. Preserve explicit withdrawals and their reasons. This makes
differences between phase judgments visible without silently changing the acceptance gate.

U3 also owns mandatory duplication observations for every reviewed draft and the released
answer, separately. Report the count and block/paragraph identifier pairs with Jaccard
>= 0.9, including an explicit zero when none exist. Use a declared variant of Addendum
C.5's method: split on blank lines, remove citation tags, trim, keep paragraphs with at
least 60 remaining characters, lowercase, and form Unicode word sets with Python's
`re.findall(r'\w+', text)`. Score their intersection over union. Record the metric
version and recompute the saved baseline with that same convention; do not mistake a
method change for a model change. Store scores and identifiers in the report; keep
source-bearing text in private artifacts. The audit reports five such pairs in run
44's published answer; that historical count is not a prediction for a new run.

This is an obligatory measurement, not an automatic content deletion or acceptance rule.
Similar blocks may contain different qualifications or citations. The system's success
criterion is complete, reproducible reporting; it does not guarantee zero semantic
repetition from the model. Report the direction across drafts even if it worsens.

Verification covers zero-candidate failure, incomplete support with no releasable review,
fallback to an earlier completed review, and a current supported block whose number was
used by an older rejected block. The reader-facing text must not imply that an invalid
review approved a release.

If public result fields change, update `Echo_UI/backend/app.py` and
`Echo_UI/frontend/src/lib/api.ts`, plus the existing result display/export that consumes
them. Keep the UI change limited to those projections; no redesign or private trace dump.

### U4 - Avoid adding an identical selected excerpt twice

Keep this smaller presentation task separate from U1/U2. At rendering time, when the
exact validated selected quote is already present as an unambiguous quoted span in the
item's text, do not append the same excerpt again. Otherwise preserve normal extraction
and rendering. Do not rewrite narrative meaning or infer quote equivalence by similarity.
Keep the existing model delivery instructions unchanged in this system-only update.

Rendering changes require an explicit current rendering identity with historical replay
preserved; do not change what saved v1-v4 answers mean. If this cannot be done locally
without changing the answer/replay contract, split U4 into a later change rather than
expanding batch 1. Cross-block semantic deduplication remains outside deterministic code.

Verification: the selected quote renders once in the new path; a quote absent from text
still renders; a partially matching or differently attributed quote is not removed; saved
historical renderings still replay. The complete rendered candidate is reviewed before
release. A scripted explicit replacement removes its old block; near-duplicate narratives
remain a review matter, not an automatic deletion rule.

## Batch 3: evaluate judgment and packet size separately

### U5 - Diagnose reviewer behavior against fixed, human-checked cases

Status: diagnostic only, with a human reference and no acceptable-error threshold. U5
does not pass or fail the software release and cannot certify reviewer reliability.
What can fail the system gate is corrupted input, missing feedback, wrong identity,
incorrect routing or a changed lifecycle rule, all covered by U1-U3 tests.

Use the captured 44/45 cases privately as regression evidence and create small generic
fixtures for code tests. Include valid prose classifications, a real missing positive
excerpt, a valid F4 falsely described as another comment, a valid negative excerpt falsely
described as a denominator statement, an actual label misattribution, and the false
"both comments mention busy periods" attribution.

Offline tests establish input fidelity, identity handling, feedback availability and
review routing. A scripted correct verdict does not establish real reviewer accuracy.
For semantic evaluation, record a human assessment and evidence rationale per case,
including unresolved ambiguities, then compare actual model judgments with that reference.

Reuse the current challenge path for disputed corrections; do not add automatic challenge
calls, extra review stages or a second reviewer. Neither run 44 nor 45 called that path:
its live behavior is unexercised in this evidence pair. An explicitly invoked scripted
test must check that it receives the intended current candidate and correction, preserves
scope/budgets, and records the model's disposition without automatic closure. That test
does not establish that a real model will choose to challenge or judge correctly.

No prompt or reviewer-rule change is included. Existing instructions already prohibit
preferred formats and require review of the supplied block. Correct input delivery is a
system responsibility; choosing the right semantic judgment remains a model behavior.

Measure false rejections, missed real defects and preservation of requested content as
separate outcomes. Record both phases; do not score quality by supported-block count or
the word `accept` alone. Keep the full five-role workflow for application evaluation.

### U6 - Measure A8 without losing required information

Use a fixed scripted workflow with four drafts and three repair requests, comparing the
same question, evidence, corrections and schemas before and after the packet change.
Check U1 completeness before comparing size. Count duplicate sections and record bytes/
characters for instructions, history, evidence, saved blocks, schemas and repair details.

Disposition of the historical 15,000-token target: this revised plan retires it as a
pass/fail criterion and retains it as a historical comparison point only. It is not
replaced by an invented token proxy or an arbitrary character ceiling. Addendum C.9's
older target remains part of the historical record; this plan proposes the replacement
criterion rather than claiming that the historical decision was already amended there.

The implementable A8 system gate is: every required assessment is supplied once in its
designated repair-detail section; the canonical evidence packet, available-block catalog
and full verdict are not redundantly serialized as extra copies; identities and meaning
are preserved; and before/after byte and character sizes are reported for all three
repairs with identical scripted inputs. Context fields with different purposes are not
merged merely because they contain some of the same text. No numeric size-reduction
claim is required to pass this information-preservation and duplication-removal gate.

Record provider-reported tokens when later authorized live runs supply them, identifying
the measurement source. The current dependencies provide no verified provider-compatible
offline tokenizer. Character counts remain character counts; no installation is proposed.
Live tokens are observations, not a controlled before/after effect estimate.

Report the actual size and remaining duplication even if the complete packet grows. Do
not narrow findings, evidence or obligations, increase budgets, or claim improvement by
moving the same repeated material to another field. U3's >= 0.9 paragraph-pair observations
remain mandatory alongside these request-size measurements.

## Verification and later live evaluation

After implementation is authorized:

1. Run focused regressions for U1/U2, then U3/U4 where included, using the existing tests
   in `test_workflow_repairs.py`, `test_review_delivery_recovery.py`,
   `test_review_contract_v3.py`, `test_content_delivery.py` and `test_capture_resume.py`.
   Add cases for the actual failures; avoid duplicating tests that restate the implementation.
2. Run the full existing Windows release gate from `Agent_Echo`:
   `& '.\.venv\Scripts\python.exe' -B check_release.py`, then `git diff --check`.
   Build/check the UI only if its contract or displayed behavior changed, using its own
   verified Windows workflow. Record actual results; 365 is the old baseline, not a target.
3. Preserve exact source/configuration/data identities and raw historical artifacts. Freeze
   the evaluated code. Write all new evidence to fresh, unused paths.
4. With scoped live-call authorization, run one fresh Gemini workflow and one fresh Luna
   workflow on the same M14/Recognition/Q3-2026 question, lexical retrieval and current
   budgets. Evaluate each separately; generator/reviewer model differences remain confounded.
5. Publish a per-draft comparison of phase decisions, corrections with origin/current
   identities, retained requested content, repair sizes, calls, timing and released gaps.
   Include >= 0.9 duplication-pair counts and identifiers for each draft and the released
   answer, and record whether a challenge call actually occurred. Missing observations
   are a reporting failure; a nonzero duplication count is not an automatic rejection.
   Have a human compare the final answer and limitations with the actual question and sources.
6. Stop expanding the change when the specified checks pass. A further defect gets its own
   diagnosis. Do not spend more calls seeking an `accept` label or increase the draft cap.

One live pair is diagnostic, not a reliability benchmark. The historical A15 five-run
delivery evaluation is a separate later step; 4/5 complete does not certify sentiment or
review accuracy. No new live result, test success or publication is implied by this plan.

## Success criteria and decision boundary

The proposed local release criteria are actionable repair detail, correct content identity,
preserved lifecycle judgments, accurate release provenance and honest user-facing failure
text, with historical replay and existing gates intact.

For the new live pair, record three outcomes independently: delivery completion, compliance
with the user's requested content, and factual/reviewer correctness. A four-draft partial
result is allowed by the design; it still needs a human assessment of whether its released
content and stated limitations faithfully describe the reviewed evidence. Record that
assessment and rationale in a new ignored evaluation report linked from the delivery record.

As checked for this revision, local Addendum C.9 still describes agreement that both
reviews accept the same draft and explains that the current gate merges completeness
obligations into support. This is a dated audit statement, not an instruction to change
the runtime gate. U1-U6 preserve the current explicit support-phase reassessment path,
record the raw decisions, and introduce neither a requirement for two literal `accept`
values nor another completeness call. Acceptance-policy changes remain outside scope,
regardless of later edits to the audit's wording.

Human semantic judgments, false-rejection rates and missed-defect counts remain diagnostic
observations. They must be disclosed even when all system checks pass; a software release
must not be described as a validated improvement in model reasoning.

Implementation approval would cover the chosen batches and their offline verification;
live calls, GitHub publication and any acceptance-policy change must be explicitly included
in the execution scope. They are not authorized by the request to generate this plan.

## Documentation delivery

When changes are implemented, update `PROJECT_CONTEXT.md`, `DOCUMENTATION_MAP.md`,
`DELIVERY_RELIABILITY_UPDATE.md`, `WORKFLOW_RELIABILITY.md`, `RESUME_AND_CAPTURE.md` and
`TESTING_AND_RAG.md` only where their contracts or observed results change. Update
`SOURCE_GROUNDING.md` and UI types/export documentation if U4 or public projections change.
Keep audits dated and historical; append corrections instead of rewriting their evidence.
