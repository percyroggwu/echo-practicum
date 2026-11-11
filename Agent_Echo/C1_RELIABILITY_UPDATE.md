# Shared C1 reliability update — 2026-10-28

Implemented in the main application at the user's request. C2 grouped review and C4
specialized reviewer roles are **not** installed. Original, Cherry, Vanilla, Lime and
ZeroSugar remain the five roles; completeness and source-support review remain required.
No tests, builds, demos, model calls, provider probes or publication were performed.
Static source parsing and diff/reference inspection do not validate runtime behavior,
provider compatibility, semantic accuracy or a complete accepted answer.

## Responsibility and execution

The Python process started by `run_agent.py` executes the agents. The model requests
an available tool; `Specialist._run` dispatches the request to its Python handler.
For Vanilla, `analyze_survey_sentiment` dispatches to `VanillaAgent.analyze_sentiment`.
That handler requests classifications from Vanilla's configured model and directly calls
`partition_sentiment_labels`. The latter is a Python validator, not another agent or
semantic reviewer. Python computes counts and percentages; models judge meaning.
Original chooses and writes the final content; the renderer organizes its explicit
selection, extracts references and preserves replayable provenance.

## Identical-request transport recovery

`RunBudget.respond` makes at most two additional attempts for classified transient
connection/timeout/service errors, with 20/40-second backoff and the same instructions,
history, tools and tool requirement. Extra attempts consume the existing shared model
budget and respect the deadline and configured request pacer. The adapter's existing
429 handling remains in place. Authentication, invalid parameters, content refusal,
output truncation and malformed model deliveries are not transient transport retries.

After exhausted transport retries, a specialist interruption propagates to the workflow
checkpoint. It is not returned to Original as an invitation to rephrase or redelegate
the same analytical task. A request may have reached the provider before disconnection;
retrying generation does not establish that the failed attempt had no provider usage.

## Literal extraction instead of generated quote text

`agents/content.py` assigns `EX_...` identifiers to exact slices of authorized source
text. Sentence/chunk boundaries are mechanical; the complete released comment remains
the classification/review context. No segment is assigned a sentiment or interpretation
by code. Models choose a suitable reference; Python obtains its exact stored text.

- Sentiment delivery uses `citation_id`, `label`, `quote_ref`, `reason`. Non-indeterminate
  labels still require an excerpt belonging to that exact comment.
- Live narrative items use `text`, `citation_ids`, `quote_ref`. A quote must belong to
  one of that item's cited records. Proposals continue to use a null excerpt.
- Review corrections use `request_ref` into `question_excerpts`; support corrections
  may use null where the original question is not their basis. The model no longer
  reconstructs or concatenates `request_excerpt` text.

Code still validates literalness, IDs and coverage after extraction. Fragment relevance,
label defensibility and source entailment remain fallible model judgments.

## One official answer and reusable work

Live `submit_grounded_answer` delivery contains:

- `fact_ids`, `interpretations`, `proposals`: explicit additions;
- `reuse_ids`: existing `BLOCK_...` specialist/current-draft blocks to incorporate;
- `remove_ids`: explicit removal of blocks from the current saved draft.

The runtime supplies `reusable_blocks` and `current_draft`. A block carries its original
kind, content and binding to its scope and cited source versions. Reusing a block copies
that content/provenance rather than asking Original to regenerate it. Adding unrelated
evidence does not invalidate unchanged blocks; changed cited evidence invalidates reuse.
Unchanged current-draft blocks remain unless Original explicitly removes them. Original
can replace any block by removing it and adding its revised interpretation or proposal.
This is neither a mandatory per-question checklist nor a requirement to publish every
specialist observation. The resulting package still receives independent review.

Free-form model output is retained as unverified `DRAFT_...` text references rather than
lost on a structured-delivery retry. An agent can use `text={"draft_text_ref":"DRAFT_..."}`
inside a narrative addition and assign its kind/sources/excerpt without rewriting the
saved paragraph. Free-form text is never silently published, merged or approved. A model
can still omit important content; completeness review must assess the actual visible
answer against the question. The code does not infer a paragraph's intended meaning.

The persisted artifact remains canonical `source-facts-v4`: expanded `fact_ids`,
`interpretations`, `proposals`, with extracted `quote` strings. Existing v1/v2/v3/v4
replay and manager-facing claim fields remain supported. Live delivery and persisted
replay payloads intentionally have different administrative representations.

## Strengthened C1 and review obligations

The main ZeroSugar implementation now includes the common experimental C1 controls:
application-keyed finding schemas; permitted citation subsets; feedback showing received,
allowed, pending and retained references; and retention of explicit structurally valid
same-candidate finding judgments during delivery repair. Invalid explicit replacements
evict the previous cached value, including non-object replacements. No absent judgment
is converted into support. Invalid JSON/truncation is not guessed into a valid review.

Original verifies retained specialist source identity/content and explicitly checks that
the candidate packet retains every authorized specialist evidence ID. Retaining evidence
does not force all specialist conclusions into the visible answer.

Support review delivery may reference an active `related_correction_id` to refine the
same obligation, rather than assigning another identity to the same problem. The model
must explicitly judge that refined obligation mandatory and unaddressed. Code preserves
its prior text in diagnostic history and avoids adding that same ID twice. Semantic
equivalence between differently identified objections is not inferred by string rules.

Original can call `challenge_corrections` once per saved candidate before rewriting it.
The tool validates existing correction/finding IDs and a bounded counterargument, then
asks ZeroSugar to reconsider the **same** candidate against the question, sources and
obligations. Matching completeness and unaffected finding assessments may be reused;
challenged finding judgments are reopened. ZeroSugar supplies explicit judgments,
ratings and a complete support verdict. Python never withdraws a substantive objection
on Original's authority or accepts by retry count. The reconsidered verdict can be reused
only if Original subsequently submits the identical candidate/source/chart package.
Changed content is independently reviewed again.

This makes challenges explicit and traceable; it does not guarantee that a model will
notice its own false objection. Proposal reasoning is separate from evidence for its
premises: a new follow-up question need not already have its answer in the sources.

## Whole-workflow continuation

New Original executions capture a `kind=workflow` checkpoint in addition to phase points.
The artifact's `capture.resume_checkpoint` prefers the unfinished workflow point.
`--resume <new-failed-artifact-or-workflow-checkpoint>` restores the coordinator state and
continues its unfinished phase through review, justified repair and final/partial release.
It does not merely return the retried phase's diagnostic result.

Retained state includes the plan, original question, current draft and edit blocks,
pending tool calls/history, tool caches, specialist results and classifiers' valid labels,
numeric caches, completed reviews, same-candidate review judgments, obligations,
previous reviewed release candidate and remaining shared budget. Nested phase points
are linked to the workflow and draft attempt. A completed child call or review is reused
only for its matching retained request/candidate, never a newly delegated question.

Continuation validates checkpoint integrity, exact scope, database fingerprint,
implementation fingerprints and all role model/transport identities. It retains parent
lineage and writes new artifacts; it never overwrites the failed output. Default resume
limits inherit the original execution. Used calls and durably recorded elapsed time are
not reset; explicit CLI limit increases are required when the retained budget is exhausted.
The four-draft and three-delivery-attempt policies remain bounded; continuation does not
turn a non-interrupted, exhausted semantic revision loop into an unlimited run.

Recovery starts from the last durable state. A provider request interrupted before its
result was durably processed may need another identical request. Legacy **phase-only**
checkpoints lack the coordinator stack and cannot retroactively become whole workflows.
They retain their focused diagnostic behavior. Code/source/profile changes require an
explicit migration or a new run; old experiment snapshots are unchanged.

## Next validation, not executed

Future authorized validation must inspect a full accepted workflow, literal extraction,
content preservation through edits/reuse, justified challenge disposition and interruption
continuation at nested tool/review boundaries. Measure false objections, repeated work,
total provider usage and completion separately. Previous C1+C2/C1+C4 experiment results
do not validate this newly combined implementation.

## Schema-alias correction after runs 33/34

Both user-run providers completed planning and then hit the same local KeyError('quote')
before Vanilla. The canonical narrative schema shares a template; the live adapter now
detaches each branch before changing quote to quote_ref. Stored canonical schemas and
source extraction semantics are unchanged. Unexpected workflow exceptions are captured
privately and mark the workflow checkpoint failed. Static inspection only; no tests or
new provider requests followed this fix. See LIVE_TEST_HISTORY.md for observed scope.
