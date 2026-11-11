# Delivery reliability update - 2026-10-28

## V7 corrected-plan delivery, 2026-10-31

[Implementation and local gate](UPDATE_2026-10-31_V7.md): review-v7/source-facts-v7,
classification fidelity, consistent proposal quotes, one shared protocol exception,
structured explanations and reviewer-only repair, phase/candidate reporting and token
accounting. The complete gate passed 412 tests. [Gemini 51/Luna 52](RUNS_51_52_ANALYSIS.md)
both ended partial, with 16 and 7 released blocks respectively. The extra Luna attempt
repaired the duplicate association but failed a later lifecycle-state conflict. Neither
fully accepted; canonical tables and explanation structure improved without certifying
model judgment. Historical sections and audits below retain their dated status.


## Live pair: Gemini 49 and Luna 50, 2026-10-31

The user authorized one full live workflow each, following the published a14973b update.
Both capture manifests match the unchanged working source; question hash, authorized
M14 / 2026-07-01 through 2026-09-30 scope and database hash match. Lexical retrieval,
6000 output tokens, 32 model calls and 1000 seconds were retained. No connection probe,
source change, new offline gate, provider-setting change or additional live repeat ran.

| Workflow | Attempted / successful calls | Duration | Observed outcome |
| --- | --- | --- | --- |
| Gemini 49 | 20 / 20 | 475.500 s | partial / revise; two full review rounds, third completeness accepted, third support failed; 10 released and 4 withheld from candidate two |
| Luna 50 | 13 / 13 | 342.046 s | failed / invalid_review at completeness; one candidate, zero completed review rounds and zero released findings |

Gemini's final three support submissions each repeated a related_correction_id and failed
correction_duplicate at corrections.related_correction_id. The previous complete verdict
and its candidate were retained for partial release; the newer candidate is unverified.
The run did not stop on excerpt delivery: three Original excerpt_source rejections were
followed by an accepted submission. There was no presentation fallback. The two completed
rounds retain one-character rationales in all six non-completeness ratings; these remain
quality limitations rather than a new review-protocol rejection. Both safety scores were 3,
so this pair does not live-validate the issue-linked low-score veto. Gemini's reported
Original repair input tokens were 22,252 / 23,822 / 25,200 / 26,595 / 24,355; none met the
15,000-token target. No exact controlled before/after provider-token effect is established.

Luna failed before support review: each of three raw provider responses contained two
submit_completeness_review calls with distinct IDs and argument payloads, despite a
request with tool_choice=required, one available tool and parallel_tool_calls=false.
The second call described itself as accidental; the program did not obey that model text
as authority to discard a competing call. No completeness verdict passed validation.
The artifact's default revise is not an independent accepted review judgment. Earlier
Vanilla excerpt-source errors recovered before the candidate reached review.

There were no provider_connection failures or truncated outputs in this pair. Neither
run produced a fully accepted answer. Model/gateway output and program acceptance must
remain distinct; the captures do not establish whether the two-call behavior originated
in the underlying model or the gateway. Human semantic validation remains pending.

A remaining presentation ambiguity is visible in Gemini's failure wrapper: a limitation
says the failed support phase released zero findings while release_counts correctly
reports ten findings published from the earlier reviewed candidate. Preserve the artifact;
this is an observation for a future scoped correction, not permission to change code.

Artifacts: reports/apinex_prueba_gemini_49.json and
reports/apinex_prueba_vanilla_50.json. Logs: 20261031_073421_098f38a8bddd and
20261031_074236_289203ec5f6b respectively, under reports/logs/ and private details/.
The metadata comparison is reports/live_pair_20261031_49_50_verified.json. All reports
and full exchanges remain ignored local evidence. No publication of these captures occurs.

## Review and delivery update, 2026-10-31

[Implementation and evidence](UPDATE_2026-10-31.md) records the user-authorized revised
A23-A31 scope, explicit safety-veto decision, localized excerpt feedback, submission-identity
stalling, bounded presentation recovery, removal reasons, citation normalization and
support/publication accounting. New contracts are review-v6 and source-facts-v6;
old artifacts remain unchanged. Verification is offline only; no live call is authorized
in this update. D.5's invalid-quote counts for Gemini 48 are corrected there to 4/4/3.

## Gemini 48 repeat, 2026-10-30

The user requested one further Gemini workflow on the same question, scope and budgets.
The application was unchanged; the captured manifest matches the current source and the
previous network-enabled pair. All 11 generation calls succeeded, with no connection
failure and no transport retry. The run finished failed after 217.859 seconds with
`answer_delivery_stalled` at answer validation. Unlike Gemini 46, it completed one full
review round (completeness and support both revise), then entered repair. Original again
submitted three invalid excerpt/source selections, so its newer draft remained unverified.
No findings were released. The earlier review's safety/appropriateness score was below
3, which conservatively withheld the entire partial release. API success is not answer
acceptance. No application code was changed and no local test rerun was needed.

Artifact: `reports/apinex_prueba_gemini_48.json`; log:
`reports/logs/20261030_193306_b5b2898a65bc.jsonl`; full exchanges and checkpoints:
`reports/logs/details/20261030_193306_b5b2898a65bc/`. This repeat reached review where
46 had stopped before review, but both eventually stopped on excerpt-source validation;
it does not establish improved semantic quality or convergence.


## Live completion: Gemini 46 and Luna 47, 2026-10-30

The system code stayed frozen for both network-enabled workflows; both capture manifests
match the current application files. Local verification passed 371 tests in 58.610 s.
No Git commit or GitHub publication was requested or performed.

Restricted-environment attempts for each profile and two retries each failed with
`provider_connection` (three attempted calls and no successful calls per artifact).
They are preserved as 46/47 and `_retry1`/`_retry2`. Network-enabled attempts are stored
separately with `_network`; they reached the actual workflow. Do not mix these attempts
into an answer-quality comparison.

| Workflow | Calls attempted / successful | Outcome | Review/release |
| --- | --- | --- | --- |
| Gemini 46 network | 9 / 8; 171.485 s | failed, `answer_delivery_stalled` | No completed review and no findings released. Original repeated `excerpt_source` three times: its selected excerpt did not belong to the item's cited sources. The failure's default `revise` is not an independent verdict. |
| Luna 47 network | 24 / 23; 566.047 s | partial, final review `revise` | Four rounds (eight phases) completed; 5 supported/released findings and 2 withheld; 18 pending entries with 15 distinct issue texts. Draft-cap stop logged, no fifth draft. One truncated output recovered. |

Luna's pending assertion corrections include six origin-bound block references with the
rejected assessments. No challenge call occurred in either workflow. The prescribed
paragraph-duplication metric found zero >=0.9 pairs in the released outputs; Gemini's
empty analysis makes that zero uninformative about answer quality. Actual request sizes,
per-draft metrics, phase decisions and diagnostic references are in ignored
`reports/delivery_pair_20261030.json`. The saved-request restoration comparison is in
`reports/delivery_pre_live_20261030.json`. These are measurements, not accuracy scores.

Artifacts: `reports/apinex_prueba_gemini_46_network.json`,
`reports/apinex_prueba_vanilla_47_network.json`; execution logs respectively
`reports/logs/20261030_191821_580b0894bebb.jsonl` and
`reports/logs/20261030_192113_aa7930a2a715.jsonl`. Exact full inputs/outputs and checkpoints
are in their private `reports/logs/details/<run_id>/` folders.

Both fresh evaluations were executed. Neither produced a fully accepted answer. The
pair demonstrates the observed delivery paths only; semantic reference judgments still
await human confirmation. No further model call is justified merely to seek acceptance.


## System delivery update, 2026-10-30

The user authorized implementation, local tests and one fresh workflow per Gemini/Luna,
including connection retries. The system changes now retain rejected assertion assessments
and candidate/finding origin, bind a uniquely matched saved narrative block, and expose
whether that original block remains saved during repair. Matching compares source sets;
old finding numbers never select a new block. Ambiguous matches remain unbound.

Partial-result limitations derived from assertion corrections distinguish earlier-draft
obligations and explain their source-linked reasons instead of presenting an old F-number
as a current passage. Missing-verdict failures say that no conclusions were reviewed.
Artifacts include reviewed/released counts, per-draft duplication diagnostics and repair
request section sizes. Paragraph similarity is observational and never changes a verdict.

New source-facts-v5 rendering avoids appending an exact selected quotation already present
as a quoted span. v1-v4 rendering remains available unchanged. The public answer schema and
manager UI text fields are unchanged; no UI redesign, new prompts, judgment rules or budget
changes were introduced. Explicit challenge tests exercise accepted and still-revise
scripted dispositions and the one-challenge bound; real model use remains observational.

The final local release gate passed 371 tests in 58.610 seconds. An earlier run found one
fixture that expected new answers to keep the v4 version label; it was updated while a new
test checks exact v4 versus v5 quotation replay. Evidence: ignored
`reports/release_gate_20261030_final.txt`. `reports/delivery_pre_live_20261030.json` compares
three saved repair requests from each of 44/45 before and after restoring missing
assessments, with all other saved fields held fixed. This is a saved-request projection,
not an exact forecast of new live requests or a provider token measurement. New request
sizes are recorded separately. The 15k target is retained as historical observation.

Live results are recorded after completion in the dated delivery record. Semantic cases
are diagnostic references awaiting human confirmation, not evidence of model accuracy.


## Fresh live runs: Gemini 44 and Luna 45, 2026-10-29

The user authorized completing A20-A22 and the compact repair-context follow-up, the
full local release gate, two fresh live runs, and GitHub publication. The code was frozen
for both live runs. Gemini 43 was a restricted-environment attempt that ended in
`provider_connection` with zero successful generation calls; Gemini 44 was the network-
enabled retry. Luna 45 completed normally.

The full local release gate passed **365 tests in 46.890 seconds** before the live calls;
`git diff --check` passed before this documentation update. This offline evidence is
separate from the provider outcomes.

| Run | Provider calls | Result | Verification | Partial release |
| --- | --- | --- | --- | --- |
| Gemini 44 | 25 total, 23 successful; 551.0 s | `partial` | Four of four reviews completed. Two ZeroSugar support outputs reached the 6000-token cap and both recovered with a compact retry. Final decision: `revise`. | 16 supported, 1 withheld, 3 pending corrections |
| Luna 45 | 24 total, all successful; 529.8 s | `partial` | Four of four reviews completed. Original had repeated excerpt-source rejections; ZeroSugar corrected invalid assertion citations during support retries. Final decision: `revise`. | 15 supported, 3 withheld, 15 pending corrections |

**System evidence:** A6's compact support retry recovered both Gemini output-limit
events. A22's draft-cap branch emitted one `repair_stopped` event at draft 4 in each run,
with `next_draft_started=false`. A20's same-pass validation of independent finding and
correction errors and A21's correction-citation namespace feedback were not exercised
live; targeted offline tests cover those cases. First repair calls reported 19,162 input
tokens for Gemini 44 and 26,676 for Luna 45. These are different drafts, so the numbers
are not a controlled A8 estimate and do not establish the 15k target.

**Answer quality:** Neither final review accepted the answer. Luna's last draft still had
a mixed-comment attribution error, citation/content mismatches, repeated text, and no
visible per-comment table. Gemini's final review retained a finding with contradicted or
insufficiently supported assertions and noted repeated sections. These are review
judgments on the generated answer; the pair does not isolate their root cause or show a
deterministic sentiment-calculation defect. Neither run establishes semantic accuracy.

Artifacts and full event logs are preserved locally under ignored `reports/` paths and
are not included in Git. See [live history](LIVE_TEST_HISTORY.md#corrections-delivery-follow-up-gemini-44-and-luna-45-2026-10-29)
and [Audit Addendum B](AUDIT_2026-10-29.md#addendum-b---runs-43-45-2026-10-29).

Scope approved by the user: A16, A11, A12, A14, corrected A1/A2, offline verification
and controlled live evaluation. At that stage A3-A10 and A13 remained separate follow-up
work; A8 was later implemented in the 2026-10-29 repair-feedback follow-up below.
Five roles, both reviews, scope/privacy/source controls and canonical source-facts-v4
with historical replay remain required. No grouped review or automatic checkpoint
migration is included.

## A16: preserved baseline and checkpoint decision

Commit `219d7ff` preserves the local C1 implementation used by runs 35/36. Merge
`9d4caf2` also integrates the UI changes already published by the team, without changing
the preserved agent modules. Both commits are published on GitHub.

Git stores normalized file content. On Windows a checkout may change line endings,
which are included in checkpoint code fingerprints. The ignored private baseline at
`reports/baselines/pre_delivery_20261028/` therefore includes exact source bytes,
private reports/checkpoints, the database, and a manifest of their SHA-256 hashes.
Credentials and the virtual environment are not copied. Archives must remain private.

Existing checkpoints remain historical evidence. To continue an old workflow, use the
preserved exact implementation and its matching sources/configuration and credentials.
The updated implementation deliberately rejects those workflow checkpoints. Do not edit
fingerprints or bypass the matching-code/source/configuration checks. A successful
compatibility check does not promise that an interrupted model call will succeed.

## A11: baseline and triage

The authorized baseline suite reproduced 329 tests, 34 failures and 57 errors on
Python 3.12.10. Private detail: `reports/offline_suite_before_delivery_20261028.txt`.
These are failed checks, not 91 independent production bugs.

- Checkpoint-only database hashing is lazy when no capture is active. Actual captures
  and resume still fail on missing or changed sources.
- Scripted live fixtures translate canonical quote/request text to supplied EX_
  references and saved finding lists to application-keyed delivery. Their judgments
  are unchanged. Missing or invalid content stays invalid.
- Runtime doubles named Cherry expose the reader counter supplied by the real role.
- Historical replay and direct validator tests continue to use canonical stored data.

Offline and live results below will be recorded after execution. Passing offline tests
validates software behavior, not sentiment accuracy or independent semantic quality.

## A1/A2: resolved edits and bounded delivery repair

The additions contract is unchanged. Capacity is checked only after resolving actual
removals, reuse and exact duplicates; a static `12 - retained` schema cap is deliberately
not used. The live request exposes current capacity and overflow feedback includes the
retained/reused/submitted/unique-new/merged counts, excess, remaining slots and safe
BLOCK_ identifiers. The model chooses edits; code does not remove claims by meaning.
Canonical renderer validation and both reviews still apply.

After three consecutive structured-answer rejections of the same code/field, the
runtime stops with `answer_delivery_stalled`. It does not spend the remaining turns on
the same condition. The existing reviewed-candidate release path retains only eligible
findings from the last completed review; absent or integrity-failed reviews release
nothing. This partial stop is not counted as successful completion.

Nine offline delivery tests cover at-capacity replacement, deduplication, reused blocks,
source binding, precise minimized feedback, a two-turn scripted repair, safe stopping,
and partial release with the completed review's candidate ID. A saved run-36 replay
reproduced 11 retained + 12 new = 23; explicit replacement rendered successfully.
Private replay summary: `reports/delivery_replay_20261028.json`. No model was called
for this replay and no semantic acceptance was inferred.

## Fixed live case

`tests/evaluation_cases.json` now includes `recognition_checkin_delivery`, preserving
the exact run-35/36 question and M14 / 2026-07-01 through 2026-09-30 scope. Controlled
CLI runs retain 32 calls, 1000 seconds and the unchanged per-profile output settings.
Review criteria are for external inspection and are not added to the agents' question.
Each live run uses a new output artifact. Provider names identify configured profiles,
not independently verified upstream model provenance.

## Offline verification before live calls

The final full release gate passed **343 tests in 117.279 seconds**, Python 3.12.10,
with zero provider calls. Private output: `reports/release_gate_verified_20261028.txt`.
The quick gate passed all nine delivery regressions. The eight capture/resume checks
include rejecting different workflow code before any model request. Existing source,
scope, privacy, quote, arithmetic, correction and partial-release checks remain in the
full suite. UI builds and browser behavior were outside this change's scope.

The A1/A2 code and fixed evaluation case were committed separately from the earlier
fixture restoration and gate. Live outcomes below are independent evidence, not inferred
from offline acceptance.

## Live attempt 37: provider prerequisite, not delivery validation

The first controlled Gemini attempt used the exact fixed question, M14/Q3 2026,
32 calls and 1000 seconds. It failed during planning after 7.719 seconds with
HTTP 402: the configured APInex provider requires its daily check-in for free models.
There was one generation request and zero successful generation calls. No specialist,
classification, completeness review or support review ran. This does not test A1/A2 live.

Private artifact: `reports/apinex_prueba_gemini_37.json`; matching execution log:
`reports/logs/20261029_014607_21b4e0fa3e4e.jsonl`. The captured code fingerprints match the frozen corrected
implementation. A same-code workflow retry can use this artifact after the account
prerequisite is resolved, with a fresh output filename and preserved budget/lineage.
Old runs 35/36 still require their preserved exact baseline.

Computer Use was denied access to Chrome, so the daily check-in was handed to the
user. No account configuration, credential, provider setting or execution budget was
changed. At that point, additional provider calls awaited that external prerequisite.

## Live continuation after the user completed the check-in

The user completed the provider prerequisite. Run 37 was resumed as a whole workflow
with unchanged code, sources, scope, profile and inherited budget; no prior analytical
work was discarded or reclassified by the application. Luna run 38 then used the same
question, scope, code and 32-call/1000-second limits with its existing profile.

| Execution | Status | Successful / attempted calls | Completed reviews | Drafts | Duration | Final blocker |
| --- | --- | --- | --- | --- | --- | --- |
| Gemini 37 resume 1 | partial | 10 / 11 | 1 | 2 | 260.343 s | second support review exhausted 6000 output tokens |
| Luna 38 | failed | 11 / 12 | 0 | 1 | 265.609 s | first support review exhausted 6000 output tokens |

Gemini retains 9 supported and 6 withheld findings from its completed older review;
its newest draft remains unverified. Luna publishes no verified findings because no
support review completed. Both retained complete 13-comment sentiment reports, which
are provisional model labels, not human-validated sentiment accuracy.

Neither run recorded a narrative_count rejection or triggered answer_delivery_stalled.
The live comparison therefore does not directly exercise the old overflow or the new
stop condition; those are covered by the exact saved-input replay and offline tests.
Gemini had zero structural rejections. Luna repaired three excerpt/source-selection
rejections (one in classification, two in Original) and one free-form final delivery.
No source/scope/privacy gate was relaxed to obtain a result.

Visible omissions, duplication and interpretation objections also remain in Gemini's
completed review. Ending the earlier turn-limit loop is not the same as producing a
complete, correct answer. These two diagnostic runs do not satisfy A15's five-repeat
criterion and are not a model-quality benchmark. No additional repeated calls or budget
changes were made after both profiles hit the known deferred review-budget problem.
A6/A7 were then implemented offline (next section); A3 and other pending items remain
separate.

Private artifacts: `reports/apinex_prueba_gemini_37_resume_1.json` and
`reports/apinex_prueba_vanilla_38.json`. Logs:
`reports/logs/20261029_015304_112c1828734b.jsonl` and
`reports/logs/20261029_015841_ce84ddce3adf.jsonl`.
The initial HTTP-402 run 37 remains unchanged as the continuation's parent.
Private cross-check summary: `reports/delivery_live_review_20261028.json`.
No application source changed during these live runs; the 343-test release evidence
still refers to this exact implementation. UI behavior remains outside this validation.

## A7 + A6: bounded review delivery and truncation recovery

Scope approved by the user: A7 (bound the review output fields in instructions, schema
and local validation), A6 (recover a truncated response with a shorter retry inside the
existing three attempts), explicit delivery instructions and specific format feedback,
plus removal of verified input duplication. Sentiment judgment, citation selection and
claim judgment were explicitly excluded, and no finding, source or assertion was reduced
to make the output fit.

### A7: one set of bounds declared and enforced

`agents/zero_sugar.py` now defines `RATING_RATIONALE_LIMIT=400`,
`FINDING_REASON_LIMIT=300`, `SUGGESTION_LIMIT=200`, `SUGGESTION_COUNT_LIMIT=6` and
`UNCERTAINTY_LIMIT=300`. The same numbers appear in the `submit_review` schema
(`maxLength`/`maxItems`), in the live support instructions and in
`ZeroSugarAgent.validate_review_bounds`. A review is therefore never accepted by the
schema and then rejected for a length the model was not told about.

The bounds apply to every newly generated submission, including legacy-shaped responses.
Each finding reason is checked before entering the retained-review cache; an overlong
finding remains in the retry schema while other valid findings are retained. Reading a
stored report through `validate`/`validate_findings` keeps its historical limits; the
shape of a new model response is never an exemption. Every
rating, finding, obligation judgment and assertion still needs its own entry: the change
shortens wording, not coverage, and assertion counts still follow the finding.

The maxima are a ceiling, not a target. Filling every field to its limit in the run-37
shape - 15 findings with two assertions each, eight corrections, ten obligation judgments -
serializes to about 54,600 characters (~13,600 tokens), which still cannot complete in one
6,000-token call. A7 makes the schema explicit and makes the model and the validator share
the same numbers; A6 is what recovers when a draft overshoots anyway. No bound was set low
enough to withhold a required judgment.

### Format feedback

`finding_reviews` supplied as text (a string) is still rejected and never interpreted as
an approval. The rejection now reports `finding_reviews_type` with `expected_type: dict`,
`actual_type: str` and a message naming the expected keyed object, so the next attempt can
correct the structure while the response is still proposed, not accepted.

### A6: truncation now consumes an attempt instead of aborting the phase

`agents/validation.py` adds `OutputTokenLimit`, raised by both adapters when the provider
stops for the output allowance (`max_output_tokens` / `finish_reason: length`).
`execution_log.error_summary` classifies it without parsing provider text. Both review
phases catch it, set a compact flag, append `COMPACT_SUPPORT_RETRY` or
`COMPACT_COMPLETENESS_RETRY` ("send the call now, one short sentence per field, shorten
wording, never coverage") and retry inside the same three attempts. A third truncation
still fails the phase, so an unrepresentable review cannot loop. Each retry consumes a
model call from the shared budget, and `review_truncation_retry` records the turn.

### Input duplication removed

`review_warnings` entries previously carried the finding text, which the payload already
sends once under `findings`. The warning now carries `finding_id`, `citation_ids` and
`signals`; the instructions state that the flagged claim is that finding's own text. The
question, candidate answer, evidence, obligations, assertions and source set are
unchanged. Measured on run 37, only 2 of 15 findings carried a warning, so the saved input
was 454 characters - roughly offset by the ~640 extra characters of explicit delivery
instructions. This item is a correctness fix for duplicated context, not a size win; the
output bound is what addresses the cap.

### Offline evidence and limits

The full offline suite passed **353 tests** (Python 3.12.10, `unittest discover -s tests`),
including ten new checks in `tests/test_review_delivery_recovery.py` for the declared
limits, the text-delivery rejection, recovery after one rejection, support and
completeness truncation retries, the third-truncation failure and the single supply of
finding text. No model call was made for this change and no live run validates it. The
success test remains a completed delivery that preserves full coverage; that would not
prove the model's judgment is correct.

### Follow-up corrections, 2026-10-29

The user authorized fixing three review findings, followed by two fresh live tests.
Overlong finding reasons are rejected before caching, including in legacy-shaped new
responses. All newly generated reports receive the current bounds independently of
their field layout. Rating rationales and uncertainty explicitly require non-whitespace
text in the schema (minimum length plus a non-whitespace pattern), instructions and local validator.
Historical report reads remain separate from generation and preserve their old limits.

The focused regression file now has 13 tests, including a schema-respecting retry with
two findings (only the valid finding is retained), a new legacy-shaped report rejected
for overlong text, a serialized historical report read without model calls, and agreement
on empty/whitespace fields. The exact pre-correction application bytes are preserved
privately under `reports/baselines/pre_review_corrections_20261029/`.
Old checkpoints still require matching source bytes; runs 39 and 40 started fresh
with the fixed case, existing profiles and unchanged 6000-token/32-call/1000-second limits.
The full release gate then passed **356 tests in 58.445 seconds**, including all 13
focused regressions, with syntax/schema checks and no provider calls. Evidence:
`reports/release_gate_review_corrections_20261029.txt`. This is separate from the earlier
353-test verification. The frozen source identities and database fingerprint for runs
39/40 are retained in `reports/review_corrections_manifest_20261029.json` and exact source
bytes in `reports/baselines/review_corrections_frozen_20261029.zip`.

### Fresh live runs after the three corrections, 2026-10-29

Gemini 39 used the fixed case and `apinex_gemini_test` with the frozen source identity.
It ended **partial** after 214.047 seconds, with 8 successful / 9 attempted calls and
one completed candidate review. Both completeness and support completed in one attempt;
support used 4,255 output tokens. The review requested corrections, including missing
literal examples, repetition and unsupported assertions. Original then exhausted 6,000
output tokens while generating the repair (32,854 input tokens, 18,502 content characters,
no tool call). The failure stage is **generation**, not verification. Fourteen findings
from the completed review were released and three withheld; the failed repair yielded
no new candidate content. No support truncation retry or format rejection was exercised.

Artifacts: `reports/apinex_prueba_gemini_39.json`,
`reports/logs/20261029_041610_466cf3c18985.jsonl`, and its private `details/.../exchanges.jsonl`.
This is observed review delivery, not complete acceptance or independent semantic accuracy.

Luna 40 used `apinex_test` with the same frozen code, database, scope, question and budgets.
It ended **partial** after 535.546 seconds, with 25 successful / 25 attempted calls,
four drafts checked and three completed candidate reviews. Its support phases took
3, 2, 2 and 3 attempts; the last failed. No provider response was truncated. The final
attempts marked an obligation `addressed: true` while also submitting an active refinement
linked to that same obligation. The existing `correction_refinement_state` check rejected
the contradiction on attempts 2 and 3; attempt 1 had an assertion-citation rejection.
No code chose which of the conflicting model judgments to trust. Twelve supported
findings and three withheld findings came from the third completed review
(`released_candidate_id: b538701e7523cfb8`), not the unreviewed fourth candidate
(`8a8b0fbef3324a53`).

Artifacts: `reports/apinex_prueba_vanilla_40.json` and
`reports/logs/20261029_042126_905c5fff4cdb.jsonl`, with private exchanges in the matching
details directory. Both artifacts and the final checkout matched the frozen source
hashes; the database fingerprint and exact question/scope also matched. The private
cross-check is `reports/review_corrections_live_results_20261029.json`.

Across the two runs, no ZeroSugar response reached the output limit and four candidate
reviews completed. Neither run achieved full acceptance. There were zero truncation
retries and zero `review_text_limit` rejections, so these runs do not directly exercise
the new truncation recovery or the three corrected edge cases; their regression evidence
remains offline. Gemini's generation failure and Luna's contradictory correction delivery
remain unresolved. A15's repeated-run criterion and independent semantic accuracy are
not established. No extra run, budget increase, grouped review or automatic conflict
resolution was applied. No Git publication was performed for this follow-up.

### Repair feedback and fresh runs 41/42, 2026-10-29

After runs 39/40, the user authorized A19, A8, A18 and A17, followed by the full local
release gate and fresh Luna/Gemini tests. No existing checkpoint was resumed; source
identity changed. The same question, manager M14, 2026-07-01 through 2026-09-30 scope,
lexical retrieval, profiles, 6000-token cap, 32 model calls and 1000-second limit were
kept. The two outputs and logs are listed below.

#### Changes

- **A19:** If grounded Original truncates while making a repair draft, make one compact
  retry with saved blocks and requested edits. The retry consumes another call from the
  shared budget. This does not apply to its initial answer, other roles or a second
  truncation; a second truncation still fails.
- **A8:** Do not repeat the complete support verdict, active corrections and evidence
  inside Original's repair message. The prior draft remains as the assistant message,
  pending corrections remain once in coordination context, and retrieved evidence remains
  once through the normal evidence path.
- **A18:** When a refinement state conflicts, identify the exact application-assigned
  correction ID and the submitted `mandatory`/`addressed` flags. Feedback explains both
  valid interpretations: the same unresolved correction stays linked and
  mandatory/unaddressed; a resolved parent stays resolved and a distinct new correction
  uses a null related ID. The application does not decide which interpretation is true.
- **A17:** Collect independent finding-structure errors and include bounded, sanitized
  secondary errors in the same rejection and repair feedback. This also lets a citation
  error and a correction-state conflict be seen in one submission.

The system keeps the existing five roles, review decisions, three-attempt review limit,
four-draft cap, output cap and shared budgets. No wording rule, fixed example layout,
automatic state flip, new review role or grouped review was added.

#### Local verification

The full release gate passed **362 tests in 34.707 seconds** on the existing Windows
Python environment. Focused suites passed: 4 A17/A18 regressions, 11 content-delivery
tests, 14 correction-contract tests, 10 review-field-diagnostic tests and 15 rejection
diagnostic tests. `git diff --check` passed. The new truncation behavior has only offline
coverage in this pair because neither live run returned an output-limit error.

#### Luna 41

Luna 41 used `apinex_test` (`free/gpt-6-luna`) and finished **partial** in 452.406 seconds
with 20 successful generation calls. Four candidates received both reviews; every final
decision was `revise`. On the fourth candidate, the first support submission had three
linked corrections with incompatible states. A18/A17 feedback named the primary ID and
both additional IDs with their submitted flags. The next support submission passed
delivery validation and completed the review in two attempts. The resulting verdict
still listed 12 issues; 9 findings were supported and 3 withheld. Thus the system
recovered the review structure, but the answer was not accepted.

The first Original repair response reported 21,011 input tokens, compared with 36,956
reported for Luna 40's first repair call before A8. That is about 43% fewer reported
input tokens. Candidates differed between runs, so the comparison is evidence of a
smaller observed repair request, not an isolated causal estimate. Later Luna 41 repair
calls still reported as many as 27,939 input tokens, above the audit's approximate
15,000-token target; A8 reduced duplicated payload but did not make the whole repair
context small.

Artifact: `reports/apinex_prueba_vanilla_41.json`. Execution log:
`reports/logs/20261029_170558_6c3d106fa4fb.jsonl`. Private full exchange:
`reports/logs/details/20261029_170558_6c3d106fa4fb/exchanges.jsonl`.

#### Gemini 42

Gemini 42 used `apinex_gemini_test` (`free/gemini-3.8-flash`) and finished **failed** in
200.093 seconds with 10 successful generation calls. Completeness completed with
`revise`; support did not complete in its three attempts. In attempts 1 and 2, the
review submission repeated the same citation ID twice for assertion F4 despite only one
allowed source ID. Both correction citation lists also contained finding IDs rather than
evidence IDs in all three attempts; validation did not reach that field until attempt 3.
Gemini repeated the F4 citation error after receiving its exact allowed ID, then corrected
F4 but left both correction lists unchanged. No finding was released. The evidence-ID
rule itself was correctly enforced, but the system reported independent errors in
sequence, and the correction field schema/message did not name the required ID namespace
or allowed values. These are P1-13/A20 and P1-14/A21 in the later audit; the detailed
payload sequence is in [GEMINI42_EVENT_TRACE.md](GEMINI42_EVENT_TRACE.md).

Artifact: `reports/apinex_prueba_gemini_42.json`. Execution log:
`reports/logs/20261029_171330_16040479aa08.jsonl`. Private full exchange:
`reports/logs/details/20261029_171330_16040479aa08/exchanges.jsonl`.

#### What these runs establish

Luna 41 exercises A8 and A18/A17 with live requests: compacting repair context reduced
the first repair's reported input versus Luna 40, and aggregate correction feedback was
followed by a structurally valid support review. That review still required changes.
Gemini 42 shows repeated model noncompliance with a precise duplicate-citation rejection;
the wrong correction IDs were present from attempt 1 but surfaced only after F4 passed.
A20/A21 address the system's delayed and underspecified correction feedback. A19 was not triggered live; it is covered by tests that verify
one retry and failure after a second truncation. Neither run had ZeroSugar truncation,
neither achieved full acceptance, and neither establishes sentiment accuracy. The
results do not justify changing citation standards, review criteria or draft limits.
At that implementation stage, no Git commit or push had been made. The later authorized
publication is recorded in [the Gemini 44/Luna 45 follow-up](#fresh-live-runs-gemini-44-and-luna-45-2026-10-29).
