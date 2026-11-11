# Correction update plan after Gemini 51 and Luna 52

Date: 2026-11-01, America/New_York.

**Status: proposed implementation plan.** The user requested this document. Creating it
does not authorize runtime changes, tests, API calls, new budgets, model reassignment or
Git publication. No item below is implemented by this document.

## 1. Intended outcome and responsibility

Produce answers that faithfully display retained evidence, satisfy the request and remain
stable during repair. Achieving that requires three independently evaluated capabilities:

| Responsibility | Owner | What success means |
| --- | --- | --- |
| Analysis and editing | The model executing Original | Repairs the actual defect while preserving correct content and provenance. |
| Completeness and support judgment | The model executing ZeroSugar | Detects real defects, recognizes present material and explains judgments coherently. |
| Delivery, integrity, recovery and publication | Python | Supplies consistent contracts, reports independently detectable errors together, preserves state and enforces release controls. |

Passing a Python validator establishes conformance to its checks. It does not establish
that a model interpreted evidence correctly. Conversely, a model disagreement does not
justify accepting a malformed review or withholding a code-verified fact for a false reason.

The update has four tracks: delivery corrections, separate capability measurements,
contract simplification and bounded resolution of objectively disputed absence claims.
Token reductions are measured within each track, not assumed to imply better answers.

## 2. Evidence and baseline

Authoritative inputs:

- [Runs 51/52 analysis](RUNS_51_52_ANALYSIS.md).
- [Audit, with Addendum A governing its corrected statements](AUDIT_RUNS_51_52_REASONING_VS_SYSTEM.md#addendum-a---external-review-response-2026-11-01).
- [Improvement and token analysis](IMPROVEMENT_ANALYSIS_SCORES_AND_TOKENS.md), subject to the numerical correction below.
- [Implemented v7 contract](UPDATE_2026-10-31_V7.md).
- Private reports, exchanges and checkpoints identified in those documents.

| Baseline | Gemini 51 | Luna 52 |
| --- | --- | --- |
| Outcome | Partial | Partial |
| Generation calls / successful | 19 / 18 | 16 / 15 |
| Elapsed seconds | 420.766 | 351.593 |
| Completed candidate reviews | 2 | 1 |
| Published findings / withheld | 16 / 0 | 7 / 2 |
| Provider input tokens | 324,402 | 269,775 |
| Terminal defect | Seven incompatible removal/reason submissions from Original | Three duplicate correction links; fourth attempt repaired the duplicate and failed an existing lifecycle-state conflict |

Both stopped with global budget remaining. All four candidates submitted to review
contained 13 classifications faithful to their own classifier records. The three completed
support reviews delivered seven structured explanations each. These improvements remain.

Numerical correction: Luna's failing candidate used 27,636 + 28,760 + 31,235 + 33,726 =
**121,357** input tokens. Finishing on attempt two would skip **64,961** tokens; finishing
on attempt one would skip **93,721**. Neither is an achieved saving. Full future workflows
may perform additional useful work that these failed runs never reached.

## 3. Scope and invariants

Keep the five existing roles and both review phases. Keep manager/date/privacy scoping,
read-only data access, source hashes, literal quotations, structured arithmetic,
classification fidelity, correction history, the issue-linked safety veto and existing
partial-release controls. Retain historical answer/review readers and strict checkpoint
source/data/profile identity checks.

The initial engineering package keeps the current global limits: 32 model calls,
1000 seconds, existing tool limits and 6000 provider output tokens for the reference
workflows. Keep three ordinary attempts per review phase, the existing one shared
protocol exception per workflow, the four-draft bound and existing generation turn caps.
Explanation repair continues to consume remaining ordinary support attempts.

The plan does not add lexical truth gates, infer obligation judgments, choose competing
review calls by order, release unverified cached findings or promise a completed answer
through larger retry limits. Structured coverage checks are limited to trusted rendered
records, not arbitrary natural-language meaning.

Cherry/Lime redesign, sentiment rubric changes, new retrieval systems, authentication,
model migration and blanket prompt expansion are outside this correction package.

## 4. Recommended sequence

| Stage | Work | Exit condition |
| --- | --- | --- |
| 0 | Preserve baseline and prepare captured/synthetic cases | Exact source/data/profile identities and expected symptoms documented. |
| 1 | P1: joint validation, removal feedback, diagnostics and phase reporting | Actual delivery regressions pass locally without changing judgment or release semantics. |
| 2 | Evaluate ZeroSugar and Original separately | Complete baseline measurements, including protocol failures and unanticipated objections. |
| 3 | Simplify explicit removals | One-list delivery works, preserves content and old readers, and reduces this failure surface. |
| 4 | Resolve structured absence disputes, if measurement confirms the need | Disproved absence grounds are reassessed coherently without automatic semantic approval. |
| 5 | Evaluate smaller requests and optional reviewer variants | Measured cost reduction with no demonstrated loss of controlled quality or coverage. |
| 6 | Full workflow evaluation | Current code passes local checks; new full runs are separately authorized and externally assessed. |

Stages 0-2 are the first recommended implementation package. Stage 3 is the recommended
contract change. Stage 4 needs an explicit publication/reassessment decision. Stage 5 is
experimental, and is not a reason to postpone the confirmed delivery fixes.

## 5. Stage 1: delivery corrections in Python

### P1.1 Joint correction validation

Current behavior: [resolve_corrections](agents/content.py) raises on a duplicate link before
[ZeroSugar's later lifecycle checks](agents/zero_sugar.py) execute. Luna's addressed/pending
conflict was present from the first submission but only surfaced after the duplicate was fixed.

Implement one validation path that returns normalized data, independently valid items and
a bounded list of errors. It should inspect request references, correction identities,
duplicate links and lifecycle consistency without stopping at the first independent error.
Keep the existing meaning of linked refinements: the model must choose a consistent
encoding; Python does not decide whether the obligation is required or addressed.

Dependency rules matter: an unknown ID cannot receive a trusted lifecycle judgment, and
an unparseable root cannot receive item checks. Report those prerequisites without inventing
values. A known duplicate ID can still be checked against its supplied lifecycle judgment.
Independent finding validation/cache remains available, bound to the exact candidate,
question, sources and scope. An invalid explicit replacement must invalidate that item's
old cached judgment. This is repair context, not partial approval of an atomic review.

Use the existing primary-error plus additional_errors feedback shape. Include item position,
conflicting position, exact valid identity and offending boolean states where applicable.
Bound short feedback to eight additional items, report total/error-overflow counts and
retain full detail privately. Deterministic ordering and a repeated-condition identity
must include all surfaced conditions rather than only the first code.

**Acceptance:** a sanitized Luna-shaped first submission reports correction_duplicate and
correction_refinement_state together. Correcting only one still fails. Correcting both can
complete validation. Neither failure consumes a model call inside the validator itself.

### P1.2 Localized removal feedback

Preserve the v7 one-reason-per-removal requirement during Stage 1. Report:

- removed_count and reasons_supplied;
- missing_reason_ids, extra_reason_ids and duplicate_reason_ids;
- invalid item positions and reason type/length failures;
- whether an extra ID belongs to an available but no-longer-saved block, when known.

Validate individual items even if cardinalities already differ. Extend the bounded safe
feedback allowlist in [validation.py](agents/validation.py) so these fields actually reach
the model. Do not include source text or untrusted arbitrary strings in short logs.

**Acceptance:** the Gemini-shaped 19/20 case identifies the stale extra block; 19/6 identifies
all missing reasons; 19/14 reports both missing and extra IDs; 6/14 also reports both sets.
Keep explicit IDs/source binding checks. Provide actionable feedback for malformed arrays
without an exception in the diagnostic path.

### P1.3 Diagnostics and phase-specific reporting

Record attempted removal/reason counts before delivery validation, labeling the outcome
rejected or validated. Successful edits remain distinct from attempted edits. Private
captures already retain the submitted lists; this adds accessible summaries.

Keep raw completeness, raw support explanations and the final projection separate. Attach
phase/candidate/review identity and provenance to exported ratings. A finding's blocking
categories should describe mechanism: objective integrity, model support judgment, active
mandatory obligation, explicit safety veto or incomplete/disputed review. Python must not
label a semantic objection false merely because another phase disagrees.

**Acceptance:** a manager projection never implies zero workflow publications because the
latest phase released zero. The earlier released candidate and newer unverified candidate
remain identifiable. Explanation completeness is distinguished from semantic correctness.

### P1.4 Local regression surface

Exercise actual delivery entry points, including rejection feedback, retry schemas, cache
binding, budgets and publication. Helper-only tests supplement these checks. Include:

| Case | Required result |
| --- | --- |
| Luna duplicate plus lifecycle conflict in one submission | Both errors are visible before another model attempt. |
| Invalid correction plus valid finding entries | Entries retained for repair; review not published as complete. |
| Explicit invalid replacement of a cached finding | Prior cached approval cannot reappear silently. |
| Gemini missing/extra reason combinations | Exact bounded differences reported. |
| More errors than short-feedback capacity | Total counts/overflow visible; full detail retained privately. |
| Repeated versus changed malformed submission | Diagnostics distinguish changed content from an identical retry. |
| Exhausted phase or global budget | Defined stop; no hidden additional model turn. |
| Resumed matching-code workflow | Counters and candidate/cache identities preserved. |
| Earlier completed review plus failed latest review | Only previously eligible findings may publish. |
| Historical answer and review versions | Stored semantics/replay remain unchanged. |

Use synthetic tracked fixtures that reproduce the real failing structures. Keep full real
employee/comment captures in ignored local storage. Preserve original artifacts. Run the
complete documented local gate after focused regressions pass. The previous 412-test result
does not validate new code.

## 6. Stage 2: measure the models separately

### M1. ZeroSugar controlled evaluation

The existing [review_cases.py](review_cases.py) and [scorer](evaluate_review_cases.py) provide
fixtures and annotated scoring, not a provider runner. Extend them before claiming a general
false-objection measurement. Add an explicitly authorized runner using the actual ZeroSugar
instructions, visible-answer/source separation and model adapter, with expected labels kept
out of model inputs.

Start with 13 controlled cases: the existing nine, plus authorized single-team scope,
anonymity respected without a mandatory declaration, valid zero-count categories and a
complete 13-row classification table. Include actual literal quotation/source checks.
The clean cases may be challenged for actual semantic defects; they are not certified
merely by fixture names. Independently review annotations before using them as gold.

The current closed defect-ID list cannot represent invented scope/anonymity objections.
Add categories for those and retain every unexpected objection as an explicit false-positive
candidate for annotation. Unknown objections must not disappear or make the case unscorable.
Store raw text and adjudication separately. Version the corpus/scorer and bind results to
their exact hash, profile, code, candidate and annotation method.

Run a four-case smoke batch first, then the full set if delivery works. For two profiles,
13 cases and one repetition, expect 26 two-phase reviews: 52 initial phase calls, with
retries counted separately. Proposed evaluation cap: seven total model calls and
1000 seconds per case, including transport retries; phase limits may stop earlier. This
is a new evaluation budget requiring authorization, not work hidden inside two full runs.
The smoke cases count toward the 13 rather than being silently repeated.

Measure separately:

- completed/failed review delivery and attempts, including incomplete phases;
- false objections, missed known defects, precision/recall and false-accept/false-reject counts;
- complete-case coverage and unexpected/unadjudicated objections;
- correct quotations, scope handling and label-map fidelity versus sentiment judgment;
- provider tokens, seconds and retry purpose.

Proposed advancement gate: all cases attempted; zero false objections and zero missed defects
on the explicitly annotated critical controls; no unadjudicated objections used to claim
success. Protocol failures are failures, not excluded observations. A one-repetition smoke
cannot establish reliability. Before full-workflow claims, repeat the controlled set three
times per profile, report all outcomes and uncertainty, and keep a held-out set for tuning
checks. The thresholds are proposals for controlled cases, not proof of production accuracy.

### M2. Original repair evaluation

Use frozen candidate/evidence/scope plus an explicit correction and invoke the same Original
delivery path used in the application. Create a new evaluation execution; do not bypass
checkpoint source identity to resume old workflows under changed code. Prepared evidence
must not trigger fresh retrieval or reclassification merely to repair presentation.

| Case | Requested change | Preservation checks |
| --- | --- | --- |
| R1 | Remove an extra third question | Keep 13 labels, both examples, sources and the two requested questions. |
| R2 | Add a missing positive example | Retain the critical example and correct analysis. |
| R3 | Repair one example's wrong citation | Exact quote/source binding; unaffected facts unchanged. |
| R4 | Qualify a claim unsupported by its sources | Fix the claim without deleting other fulfilled requirements. |
| R5 | Consolidate repeated examples/limits/questions | Preserve distinct information and relevant source sets. |
| R6 | Control: a correction falsely claims an existing row is absent | Challenge/reassess the objection rather than deleting/reconstructing correct classifications. |

R6 is a false-correction control, not a legitimate repair task. Keep its score separate.
Measure correction resolution, factual/source preservation, requirement regressions,
duplication, delivery failures and cost. Use deterministic checks for structured labels,
arithmetic, source identity and literal quotations. Use independent human annotation for
semantic preservation and whether two paragraphs are meaningfully redundant. Similarity
scores are diagnostic only; do not freeze every word of unaffected prose.

The existing measure_repair_delivery.py measures scripted request sizes, not these abilities.
Proposed gate: all five legitimate cases resolved with zero critical preservation regressions;
the false-correction control does not induce a destructive edit. After one smoke per profile,
repeat three times, preserving failed attempts and every intermediate candidate. A failed
capability measurement redirects work to the failing role; it does not justify loosening
Python's integrity checks.

Proposed M2 cap: 14 total model calls and 1000 seconds per case, including transport and
any ZeroSugar challenge calls. Original retains its seven-turn cap; the remaining calls
are headroom for the existing bounded review path in the false-correction control, not
additional Original turns. One full pass is 12 executions (six cases, two profiles),
at most 168 model calls. Begin with R1/R6 per profile; count them toward that pass.
Three full passes would permit at most 504 calls and require that explicit batch scope.
Every generated repair remains an evaluation candidate, not a manager-published answer.

## 7. Stage 3: one explicit removals list

Recommended contract decision: replace the two parallel live-delivery lists with:

```json
{
  "removals": [
    {"block_id": "BLOCK_existing", "reason": "Consolidated into the cited replacement."}
  ]
}
```

Keep omitted saved blocks by default. Omission from a replacement list is not deletion.
Validate unique IDs, membership in the current saved candidate, bounded nonempty reasons,
source-bound reuse and final capacity after removals/reuse/additions. Keep both reviews
and active obligations to assess whether a removal lost requested meaning. Python can
validate structure/provenance; semantic preservation remains model/human judgment.

Normalize the new list once into existing internal edit operations. Old saved delivery
records remain readable through their explicit version. Reject mixed old/new encodings
in one submission instead of choosing one. The wire schema and implementation must agree.
Unversioned historical delivery is treated as v1 by its historical reader/source identity;
do not fabricate a v2 marker or bypass checkpoint checks to continue it under new code.
Do not make missing reasons nonblocking in this recommended package; that is a different
policy, unnecessary once the parallel-list mismatch is removed.

**Acceptance:** the observed 19-removal/20-reason mismatch cannot be expressed as independent
lists. Duplicate IDs, unknown IDs and unjustified content loss remain possible and tested.
The R1/R5 model cases must demonstrate useful editing; schema simplification alone is not
evidence that the model consolidates correctly.

## 8. Stage 4: objective absence disputes and reassessment

Only introduce this after M1 confirms false absence claims remain material. It needs a
new structured review field and an explicit decision about how disputed reviews publish.

For a coverage objection, require the actual finding ID and claimed missing source IDs.
Compare them against the trusted expected set and the exact code-rendered records for the
same candidate/scope. An ID in source evidence but absent from the visible answer does
not refute a visible-answer omission. Never identify coverage objections by keywords.

If the supposedly absent IDs are visibly present, create an objectively disputed absence
ground. Ask the model executing ZeroSugar to reassess that ground and its dependent
finding/correction judgments on the same frozen candidate. The candidate is not rewritten.
Existing independent objections remain active. The application must track the affected
assessment, correction, lifecycle judgment, phase rating and publication reason together;
removing text from one list is insufficient.

Proposed budget: one combined reconsideration per candidate, shared with an explicit
Original challenge rather than one allowance per entry point. Charge it to remaining
ordinary support attempts and the global budget; no second protocol exception. Persist
the allowance and frozen identities. The existing challenge_corrections calls the review
pipeline and is not already a cheap single-finding tool; a narrowed interface requires
implementation and coverage tests, not just a new prompt.

Use one candidate/phase attempt ledger for ordinary delivery, explanation repair and
reconsideration. One ordinary support call leaves at most two ordinary calls for all
remaining purposes combined. A third completed ordinary call leaves none, even when
global budget remains. Entering the challenge tool must not reset that ledger. An extra
protocol attempt cannot be repurposed as an additional semantic reconsideration.

If the model withdraws the absence ground, it must still supply coherent remaining
judgments. A valid independent semantic objection still withholds the finding. If the
dispute or review is unresolved, mark it explicitly, withhold that finding and prevent
full acceptance. Apply existing partial-release rules only after a valid integrated review;
otherwise retain the last previously publishable candidate. Never auto-approve a block
because its table was built by Python.

Acceptance cases include present ID falsely called absent, genuinely absent visible ID,
partially displayed tables, suppressed records, changed candidates, a correct coverage
table with a real semantic-label objection, exhausted reconsideration budget and a withdrawn
absence objection that must not remain active in another projection.

Keep the current lifecycle meaning in the recommended package. Making related links purely
historical lineage is deferred: it also requires rules for new versus continuing work,
multiple descendants, closure and duplicate handling. Removing the current validation
would not resolve contradictory repair requests by itself.

## 9. Stage 5: request size and output experiments

Start with compact retries for administrative fields: stable candidate/evidence plus one
validated-state packet, unresolved edits and localized errors; avoid accumulating every
rejected full response. Retain all turns in private capture. Models are stateless: moving
a catalog into an earlier tool result does not remove its input-token cost if it remains
in every request. Measure the serialized request and provider usage.

Keep all relevant sources available, including context needed to challenge an objection.
A targeted repair packet must not hide the original request, source/scope binding or other
required content whose preservation needs checking. Completeness and final support still
review the full resulting candidate. A narrowed patch request is not a narrowed final review.

Then compare one variant at a time: smaller per-finding schemas, generic arrays with exact
coverage validation, or shorter reasons for supported assertions. Keep seven structured
rating explanations; historical one-letter rates do not describe the completed v7 reviews.
Reasons for contradicted/insufficient assertions must remain evaluable. These variants
change the review wire contract or evidence available to an auditor; they are experiments,
not pure logging changes. Adopt only if controlled judgments/coverage do not regress.

Use identical frozen cases and profiles, paired results and provider counters. Report
failed executions too. Proposed efficiency target: at least 20% lower total input tokens
on matched controlled executions, with all critical quality gates preserved. Treat the
old 15k repair-input target as a measurement reference, not a truth/release gate. The
120-150k full-workflow projection is unproven and is not this plan's acceptance threshold.
Provider caching and different reviewer families require separate measured experiments.

## 10. Contracts, checkpoints and terminal states

| Change | Proposed version handling |
| --- | --- |
| Joint feedback/diagnostic additions with unchanged submissions and judgments | Keep review-v7/source-facts-v7; implementation hashes distinguish code. |
| One-list removal delivery | Add explicit answer-edit-v2 delivery identity, with the current format treated as v1. Resolved canonical payload/rendering remains source-facts-v7. |
| Structured coverage grounds or materially different support fields | New review-v8 wire contract; preserve v1-v7 saved readers. |
| Corpus categories and repair evaluation | Separate versioned corpus/scorer identities; never substitute for runtime contract versions. |

Verify delivery identity reaches schemas, capture, checkpoints/resumption and exported
metadata; model text cannot select or override its contract. If a change alters canonical
rendering, add a new source-facts version then, rather than silently reusing v7. Full
workflow continuation remains limited to matching code/data/profile identity. Historical
captures are immutable inputs to new evaluations, not automatically migrated checkpoints.

| State at stop | Treatment |
| --- | --- |
| Invalid delivery; no earlier completed review | Generated candidate retained privately; no reviewed conclusions published. |
| Invalid latest review; earlier publishable candidate | Publish only eligible earlier findings, with phase/candidate-specific limits. |
| Valid review; real mandatory work remains | Existing partial release; route only actual requested work to its responsible role. |
| Only reviewer explanations remain incomplete | Preserve substantive judgments; bounded ZeroSugar repair; no automatic Original rewrite. |
| Objectively disputed absence ground unresolved | No full acceptance; withhold affected finding; apply the integrated-review rule above. |
| Both reviews valid; no blockers; current facts/source controls pass | Eligible for complete status, followed by external quality evaluation. |

The wire contract may be processed successfully while the content is still poor. Report
those outcomes separately in every local/live result.

## 11. Work locations and execution record

Expected implementation locations, to verify when implementation is authorized:

| Files | Responsibility |
| --- | --- |
| agents/content.py, agents/validation.py | Edit/correction normalization and bounded safe feedback. |
| agents/zero_sugar.py, agents/review_v7.py | Joint review validation, retained judgments and structured explanation integration. |
| agents/runtime.py, agents/original.py | Attempted edits, repair context, challenge routing and manager projections. |
| agents/capture.py, agents/resume.py | Contract/counter persistence and strict continuation identities. |
| agents/grounding.py | Preserve v7 canonical classification and historical rendering; change only for a demonstrated need. |
| review_cases.py, evaluate_review_cases.py | Extended corpus, complete scoring and a separately bounded actual-review runner. |
| tests/ and a repair-evaluation entry point | Actual-path regressions and separate Original capability cases. |
| Echo_UI/frontend/src/lib/api.ts and affected projections | Additive or versioned exported metadata as required. |

Keep validation in one module interface returning normalized data plus errors, and share
that path between normal execution and retries. Use existing dependency injection/model
factories for scripted and real adapters; do not introduce another role or a generic
framework for one caller.

Update current guides through [DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md) after each
authorized stage. Keep approved scope, implemented behavior, local verification, measured
provider outcomes and proposals visibly distinct. Preserve historical audits.

## 12. Release and decision gates

The implementation authorization should name the stage package. This plan recommends:

1. Implement Stage 1 and the evaluation instruments; run focused and full local checks.
2. Authorize bounded reviewer/repair measurements, with profiles and call caps recorded.
3. Decide on the removals contract using those results; verify locally and in controlled
   model cases before full workflows.
4. Add objective-dispute handling and token variants only with their explicit policies,
   versions and comparison results.
5. Authorize one fresh full workflow per selected profile as a smoke comparison. Freeze
   code/data/question between them; use new filenames and preserve all outcomes. A failed
   smoke does not authorize automatic repeats.

Before a full workflow, require the current local gate, controlled capability results,
no unexplained critical regression, current source/schema identities and an agreed cost
cap. Assess the final answer externally for correct coverage, exact examples, source
fidelity, justified patterns, appropriate team questions and editing quality. For broader
reliability claims, separately authorize repetitions and additional questions rather than
claiming success from a single accepted example.

**Decisions recommended now, not executed:** keep lifecycle judgments model-owned; select
one explicit removals list; implement joint administrative validation; measure ZeroSugar
and Original separately; keep all retry/global limits unchanged. Defer lineage-only links,
automatic removal of disputed grounds, different reviewer families and review-schema
compression until their evaluation and publication implications are explicit.

The expected engineering result is fewer avoidable delivery failures and clearer diagnosis.
Good final answers remain an empirical requirement. If ZeroSugar still invents omissions,
or Original still loses correct content, the capability measurement fails and the full
workflow gate stays closed; Python is not relaxed to make those measurements pass.
