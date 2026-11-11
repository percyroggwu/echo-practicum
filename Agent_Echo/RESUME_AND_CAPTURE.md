# Live phase retries and full local capture

## Review-v7 recovery and accounting, 2026-10-31

[The v7 update](UPDATE_2026-10-31_V7.md) keeps three ordinary attempts per review phase
and adds at most one shared protocol exception per workflow, charged to unchanged global
limits. Explanation-only repair uses remaining ordinary attempts and freezes substantive
judgments. Matching-code workflow snapshots preserve the exception count and request
accounting. Historical source identities are not bypassed.


## Identity and recovery after the 2026-10-31 update

[The new update](UPDATE_2026-10-31.md) preserves strict workflow source/data/profile
identity. Its one-use presentation fallback marker is retained in coordinator/specialist
snapshots. Completed Luna 47 checkpoints are not pending work, and Gemini 48's old
workflow cannot be resumed with changed source hashes. No migration bypass is added.
`measure_repair_delivery.py` (removed 2026-11-04 with the v7 code) read immutable historical snapshots for an offline scripted
measurement; it is not --resume, does not construct provider clients, and never rewrites
checkpoints or upgrades historical verdicts. Future derived live evaluations remain pending.

## System delivery follow-up, 2026-10-30

See [the implementation record](DELIVERY_RELIABILITY_UPDATE.md#system-delivery-update-2026-10-30) for origin-bound assertion repair details, observational duplication/request-size measurements, explicit challenge checks and the 371-test local gate. New answers use source-facts-v5; saved v1-v4 rendering remains unchanged. Runtime acceptance, scope/privacy and budgets remain unchanged. Live and semantic evidence are recorded separately.


## Checkpoint version decision, 2026-10-28

The user authorized delivery repairs after preserving the exact prior source bytes,
private reports and database in ignored `reports/baselines/pre_delivery_20261028/`.
Git commit `219d7ff` identifies the old implementation, but a Windows checkout can change
line endings included in code fingerprints; the private exact-byte archive is the
recovery source. Old workflow checkpoints are not migrated into the new code. Matching
scope/source/profile/configuration/code and integrity checks remain mandatory.
Database fingerprints for unwritten checkpoints are skipped only while capture is
inactive; missing source files still fail actual capture and resume. See
[DELIVERY_RELIABILITY_UPDATE.md](DELIVERY_RELIABILITY_UPDATE.md).

## Current whole-workflow continuation (2026-10-28)

New Original executions include a workflow checkpoint. Their `--resume` restores the
unfinished coordinator/tool/review stack and continues through the final review/release
path, preserving matching completed work and the remaining shared budget. Exact code,
source, scope and role configurations must match; outputs preserve parent lineage.
See [C1_RELIABILITY_UPDATE.md](C1_RELIABILITY_UPDATE.md) for details and limits.

Legacy explicit phase checkpoints keep the phase-only behavior documented below; their
older artifacts do not contain a coordinator stack. This implementation was applied
without tests, builds or API calls. It is not evidence of a completed accepted answer.

Updated 2026-10-27. This is implemented code awaiting live validation. The user requested
no local tests or builds and will run full model comparisons 30-32. Older artifacts/logs
remain unchanged. No new model request or GitHub publication was part of this update.

## Corrected option B: review-v5

Original is instructed to express independently reviewable interpretations with their
own source subsets, separating factual premises from new proposals. Existing finding IDs
are assigned by code; the answer/source-facts-v4 schema and historical replay remain.
ZeroSugar assesses the substantive assertions of every finding. A claim description is
concise (1-600 characters); it need not quote or reconstruct the finding, its table,
headings or citation formatting. Each assessment has factual/proposal kind, relevant
source subset, supported / contradicted / insufficient_evidence judgment and a reason.
Code assigns IDs such as F2:A1 to the accepted review's assessment entries.

Every finding still needs an assessment; known references, explicit judgments and bounds
are checked. A failed assertion withholds its entire finding and creates an Original
repair, even if the model otherwise accepts. Code does not prove semantic decomposition,
coverage or entailment. ZeroSugar must detect compound/omitted assertions and evaluate
proposal reasoning. A source table's values are replayed by code; metric relevance,
meaning and interpretation remain review responsibilities. No case-specific sentiment
rule, new agent, new mandatory model call or budget increase is introduced.

## What is retained

Each CLI execution now creates a private detail directory under
`reports/logs/details/<run_id>/`, already covered by the existing Git ignore rule:

- `exchanges.jsonl`: complete model instructions/history/tool schemas, returned model
  turns and arguments (including invalid JSON and rejected submissions), SDK request
  bodies and responses before completion validation, tool arguments/results, rejection
  feedback, usage counters and exception chains. Existing short JSONL logs stay minimized.
- `checkpoint_*.json`: retained phase inputs, scope, model profile/transport configuration,
  source-database fingerprint, code fingerprints and progress. Inputs and progress have
  integrity fingerprints. Checkpoints are local caller-owned files, not authentication.
- `manifest.json`: paths and versions. The output artifact's `capture` field links the
  exchange file and the latest failed/unfinished checkpoint.

Credentials are omitted: configured key values are registered for redaction, credential
fields and Bearer strings are redacted, and HTTP authorization headers/client objects
are not captured. Authorized question/source/answer content is intentionally retained
without the old diagnostic truncation; these detail files are not manager projections.
Full capture starts with this update. Rejected arguments absent from runs 27-29 cannot
be recovered retrospectively. Capture writes are flushed; a hard crash can still lose
an in-flight provider response that was never received. Capture failure stops execution
rather than silently claiming a complete trace.

## Resume a failed review without Original or Vanilla

Run from Agent_Echo using the existing environment. For example, after full run 30
has produced a failed artifact with a checkpoint:

```powershell
& '.\.venv\Scripts\python.exe' run_agent.py --resume '.\reports\apinex_prueba_vanilla_30.json' --run-seconds 1000 --output '.\reports\apinex_prueba_vanilla_30_resume_1.json'
```

No question, role, manager or profile is needed: they come from the checkpoint. Explicit
scope/profile arguments must match. Every output needs a new filename; existing outputs
are rejected before execution. The new artifact links its parent run/checkpoint. Each
manual retry has its own bounded call/time allowance; no automatic unbounded restart
or parent-output overwrite occurs. Counters in execution describe this attempt, not the
sum of its ancestors; prior attempts remain available through lineage and full traces.

For a review checkpoint, only ZeroSugar is constructed/called. Its failed completeness
phase is retried if necessary; completed completeness can be reused only for identical
question, answer, scope/team/chart context and completeness instructions/implementation.
Otherwise that subphase is invalidated and rerun. The retained source report, labels,
grounding and correction obligations accompany support review. Database fingerprints and
model/transport settings must match; no silent reclassification, changed-source reuse
or different-model substitution is allowed. Evidence is checked against scoped read-only
sources again, without model analysis by Vanilla or Cherry.

The retry stops at ZeroSugar's decision, including revise; it does not start an Original
repair/delegation loop. A completed phase remains an unverified/partial diagnostic result,
not a new complete Original answer. Candidate content and detailed assessments remain in
the artifact. A further invalid review produces a new failed checkpoint.

## Other recorded phases

Checkpoints also cover planning, specialist generation, sentiment batches and Lime's
chart planning. `--resume` dispatches only the retained phase. Planning/chart retries use
their saved phase inputs; specialist retries retain conversation, evidence and tool cache.
An Original generation retry has no delegation tools/handlers. Sentiment retries preserve
validated labels and retry unresolved records within a fresh bounded attempt under the
same rubric and sources. Completed analysis is not automatically rerun. Earlier-format
files without checkpoints fail explicitly rather than triggering a full Original run.

These are phase-level diagnostic retries, not general restoration of the original
coordinator process or a provider's internal state. A valid resumed specialist/plan/chart
does not automatically continue downstream phases or publish a manager answer. Code
changes use the current phase implementation and are recorded alongside parent versions;
changing upstream output requires a new dependent phase input, not reuse of an old verdict.

## Validation status and next full runs

Only source parsing, diff/whitespace and documentation/reference inspection were
performed. Existing fixtures were aligned and new capture/resume regressions were added
but not run, per user instruction. No unit tests, full workflow, build or API call has
validated review-v5, capture or phase resumption. The earlier 322-test result belongs to
review-v4 and must not be presented as validation of this update.

The next full runs are 30 Luna, 31 DeepSeek and 32 Gemini. The exact question, profiles,
scope and commands are in the [testing guide](TESTING_AND_RAG.md#next-three-model-runs-30-32-2026-10-27).
Compare delivery, real semantic errors, false review objections, calls, tokens and time;
successful formatting is not measured analytical accuracy.
