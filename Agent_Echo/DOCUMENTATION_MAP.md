# Echo documentation map

Proposed correction work, 2026-11-01:
[CORRECTION_UPDATE_PLAN_2026-11-01.md](CORRECTION_UPDATE_PLAN_2026-11-01.md) specifies
joint validation, actionable edit feedback, separate reviewer/repair measurements,
versioned removals, bounded absence disputes and cost experiments after runs 51/52.
Read it when planning or implementing that follow-up. Documentation only; runtime changes,
tests, provider evaluations and publication are not authorized by creation of the plan.

Human gold v1, frozen 2026-11-03: [GOLD_V1_RECORD.md](GOLD_V1_RECORD.md) records the frozen
[GOLD_CASEBOOK_v1.md](GOLD_CASEBOOK_v1.md) (hash, annotator), the cases built by `gold_cases.py`
and the human/automatic scoring in `score_gold.py`. No model has been run on it.
[GOLD_CASEBOOK_DRAFT.md](GOLD_CASEBOOK_DRAFT.md) is the working copy.

New agent versions, 2026-11-01: [AGENTS_V8_DESIGN.md](AGENTS_V8_DESIGN.md) analyzes Original
and ZeroSugar in full and documents `OriginalAgentV8` / `ZeroSugarAgentV8` (new files, not the
default; offline tests only, no live call) and the seven changes that need approval.

Current live evidence, 2026-10-31: [RUNS_51_52_ANALYSIS.md](RUNS_51_52_ANALYSIS.md)
records the 412-test v7 gate and two frozen-code workflows, both partial. It separates
canonical fidelity and structured-explanation delivery from remaining false reviewer
claims, Original editing errors and serial administrative-validation limits. See the
[implementation](UPDATE_2026-10-31_V7.md) for exact contracts and bounded recovery.
[AUDIT_RUNS_51_52_REASONING_VS_SYSTEM.md](AUDIT_RUNS_51_52_REASONING_VS_SYSTEM.md) (2026-11-01)
separates model reasoning errors from Echo system errors in that pair and proposes P1-P3
corrections. Read-only; it approves and implements nothing.
[IMPROVEMENT_ANALYSIS_SCORES_AND_TOKENS.md](IMPROVEMENT_ANALYSIS_SCORES_AND_TOKENS.md)
(2026-11-01, revision 2) measures per-agent token use and rejection families across 42
workflow logs and proposes per-agent and system changes to raise the 1-10 scores and cut input
tokens. Analysis only.


Current implementation, 2026-10-31: [UPDATE_2026-10-31_V7.md](UPDATE_2026-10-31_V7.md)
records the user-approved corrected plan, review-v7/source-facts-v7 contracts, bounded
protocol/explanation repair, classification fidelity, cost accounting and the fixed
review-case scorer. It supersedes earlier proposed-policy status only for its explicit
scope. Historical audits are preserved. See its verification section for actual results.


Independent audit, 2026-10-31:
[AUDIT_LUNA_RUNS_THROUGH_50.md](AUDIT_LUNA_RUNS_THROUGH_50.md) tabulates the 33 evaluable
Luna runs through run 50 by code era, the rejection-code distribution, label stability,
token growth from the logs and captures, the observations the tests and audits have not
made, and a re-scored agent assessment. Read-only; it approves and implements nothing.
[AUDIT_SHARE_PACKAGE.md](AUDIT_SHARE_PACKAGE.md) is a self-contained version (system
description, full run tables, evidence labels and reviewer questions) for sharing with
external reviewers who cannot see the repository.
[SOLUTION_EVALUATION_1_TO_10.md](SOLUTION_EVALUATION_1_TO_10.md) scores the five agents and
the system on a 1-10 rubric (eight weighted criteria, evidence per score, sensitivity and
proposed exit criteria). Read-only; it approves and implements nothing.

Current contrast, 2026-10-31:
[ADDENDUM_E_COMPARISON.md](ADDENDUM_E_COMPARISON.md) compares Addendum E with the runs
49/50 analysis and actual saved correction identities, explains the rating-stage count
difference, and distinguishes recovery-policy proposals from verified measurements.
It does not edit the audit, approve proposals or change runtime behavior.

Current case analysis, 2026-10-31:
[RUNS_49_50_ANALYSIS.md](RUNS_49_50_ANALYSIS.md) separates reasoning mistakes, upstream
tool-protocol violations, confirmed handoff/schema/reporting defects and recovery-policy
limits in the saved Gemini 49/Luna 50 runs. It records evidence and recommendations,
not implementation, a new live run or a semantic accuracy benchmark.

Current update, 2026-10-31:
[UPDATE_2026-10-31.md](UPDATE_2026-10-31.md) records the authorized revised A23-A31 scope,
the issue-linked safety-veto policy, review-v6/source-facts-v6 compatibility, local
verification, four-draft offline measurement, audit count correction and pending live
criteria. Runtime sources include review_delivery.py, content.py, runtime.py,
zero_sugar.py, original.py, findings.py, grounding.py and capture/resume snapshots.
Historical audit proposals below retain their original dated status; the new update
states which changes are now implemented. No live model calls are included.

Current delivery update, 2026-10-29:
[DELIVERY_RELIABILITY_UPDATE.md](DELIVERY_RELIABILITY_UPDATE.md) records the authorized
A7/A6 scope, A19/A8/A18/A17 repairs and A20-A22. The latest section records the 365-test
release gate and Gemini/Luna runs 43-45, distinguishing delivery recovery from answer
acceptance and noting which live cases were not triggered. Current delivery sources are
content.py, grounding.py, original.py, runtime.py, validation.py and zero_sugar.py;
checkpoint identity remains strict. A3-A5/A9-A10/A13 remain separate follow-up work.

Historical delivery update, 2026-10-28:
[DELIVERY_RELIABILITY_UPDATE.md](DELIVERY_RELIABILITY_UPDATE.md) records the authorized
A16/A11/A12/A14/A1/A2 scope, exact-byte baseline, release gate and observed verification.
Current delivery sources are content.py, grounding.py, runtime.py and validation.py;
checkpoint identity remains strict. At that point A3-A10/A13 remained separate follow-up
work; A8 was later implemented as recorded above.

Current update, 2026-10-28: [C1_RELIABILITY_UPDATE.md](C1_RELIABILITY_UPDATE.md) is the
current shared delivery/recovery guide. It supersedes the older descriptions of generated
quote fields, full answer regeneration and phase-only Original recovery for newly created
workflow checkpoints. Existing historical sections below retain their dated meaning.
No C2/C4, tests, builds, APIs or publication were included in this implementation.

Current update, 2026-10-27: [RESUME_AND_CAPTURE.md](RESUME_AND_CAPTURE.md) supersedes v4's
literal reconstruction with review-v5, documents full private exchanges/checkpoints,
credential omission and phase-only `--resume`. Runtime sources include agents/capture.py,
agents/resume.py, model/execution logging, role entry points and run_agent.py. Readmes,
roles, source grounding, context, project guidance, UI types and the testing guide are
aligned. [Runs 30-32 and retry commands](TESTING_AND_RAG.md#next-three-model-runs-30-32-2026-10-27)
are pending user execution. No local tests, build, API call or publication; prior test
totals do not validate this update. [History](LIVE_TEST_HISTORY.md) includes runs 27-29.

Current update, 2026-10-27: [review-v4](WORKFLOW_RELIABILITY.md#assertion-level-support-review-review-v4-2026-10-27)
adds explicit per-assertion evidence assessments, coverage/reference validation and
whole-finding withholding on a failed assertion. Roles, source grounding, README, context,
project guidance and UI types/details are aligned. [322 offline checks and the frontend
build](TESTING_AND_RAG.md#assertion-level-support-review-2026-10-27) passed; live semantic
quality and expanded-provider-schema compatibility remain unverified. The new
[LIVE_TEST_HISTORY.md](LIVE_TEST_HISTORY.md) compares runs 15-26 and distinguishes changes
applied after each run from that run's results. Older dated entries remain history.

Reviewed: 2026-10-26 (America/New_York), against the current local implementation
and the saved live artifacts through run eighteen. Current answers use source-facts-v4;
historical test/replay counts below predate it. This is an index and maintenance guide, not an
additional runtime policy or a benchmark. No new provider request was made for this review.

## Current entry points and responsibilities

| Reference | Purpose and authority |
| --- | --- |
| [Workspace guidance](../../AGENTS.md) | Routes Practicum work to the Echo project; also covers unrelated coursework. Local parent file, outside the Echo Git repository. |
| [Project guidance](../AGENTS.md) | Instructions for the coding assistant maintaining Echo; read with the context file once per chat. Echo does not load this file as an agent prompt. |
| [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | Compact current state, observed runs, approved decisions and next test. |
| [Repository README](../README.md) | Clone/setup, repository contents and collaboration. |
| [Application README](README.md) | Running Echo, configuration, artifacts, statuses and data access. |
| [UI README](../Echo_UI/README.md) | Group-built local manager UI and technical console; its startup script targets macOS/Linux. Current Windows startup evidence and command are recorded in PROJECT_CONTEXT.md. |
| [AGENT_ROLES.md](AGENT_ROLES.md) | Responsibilities, tools, inputs/outputs and boundaries of all five roles. |
| [WORKFLOW_RELIABILITY.md](WORKFLOW_RELIABILITY.md) | Planning, bounded retries, declines, retained evidence, structured repair feedback, independent review, release gates and minimized diagnostics. |
| [SOURCE_GROUNDING.md](SOURCE_GROUNDING.md) | Source-bound numeric facts, cited synthesis, literal examples, v2 presentation and v1 replay compatibility. |
| [TESTING_AND_RAG.md](TESTING_AND_RAG.md) | Offline checks, provider probes, live evaluation, pacing and retrieval inspection. Latest suite result is dated there; a test count is not classifier accuracy. |
| [REFERENCE_VALIDATION.md](REFERENCE_VALIDATION.md) | Historical classroom comparison with current implementation corrections. Historical source-review dates are distinct from the current documentation review. |
| [AUDIT_2026-10-28.md](AUDIT_2026-10-28.md) | Dated engineering-process audit with a line-level read of ZeroSugar and Original, the two structural loops, backend actionables and the out-of-scope UI surface. Not a runtime contract and not a quality benchmark. |
| [AUDIT_2026-10-29.md](AUDIT_2026-10-29.md) | Dated delivery diagnosis of live runs 39 and 40, read beside the 28 audit without modifying it: the rule separating system defects from model behaviour, findings P0-6/P1-11/P1-12, actionables A17-A19 and the gated plan. Addendum A audits 41/42 and actionables A20-A22. Addendum B records implementation and runs 43-45, including which behaviors were verified offline versus live and the answer-quality limits. Not a runtime contract or quality benchmark. |
| [AUDIT_2026-10-30.md](AUDIT_2026-10-30.md) | Dated continuation read beside the 29 audit without modifying it: corrections to that record, the per-draft evidence for runs 43-45, verification of the reported results, observations 19-30 separating system, model and reviewer, the release and limitation defects, the A8 measurement status and the decision register. Not a runtime contract or quality benchmark. |
| [AUDIT_2026-10-31.md](AUDIT_2026-10-31.md) | Dated continuation read beside the 30 audit: corrections to the 46-48 record, verification of the Gemini 48 and Luna 47 results, observations 32-48 (the excerpt rejection with no item index, the `SENTIMENT1` contract trap, the stall rule counting different submissions as repetitions, the safety gate that withheld 11 supported findings, repair content loss and duplicate-ID rejections), the token measurements and proposed A23-A31. Addendum E, appended without editing Addendum D, audits runs 49-50 and files observations 49-61 (the duplicate-refinement rejection, the two-call completeness response and its guard, one-character rationales, the repeated limits paragraph and excerpt, and the diagnostics that did or did not act), with proposed A32-A38. Addendum F reviews the 49-50 remediation plan, files observation 62 (two of thirteen labels swapped in draft 3, which completeness accepted with score 3) and proposes A39-A46, leaving A43, A45 and A46 open. Nothing in it is approved or implemented. Not a runtime contract or quality benchmark. |
| [UPDATE_PLAN_2026-10-30.md](UPDATE_PLAN_2026-10-30.md) | Authorized system update after contrasting Addendum C with runs 44/45: complete repair assessments, correction/content identity, honest partial-result presentation, bounded excerpt rendering, reviewer evaluation and A8 measurement. Includes evidence refinements and an explicit acceptance-policy boundary. Implemented system scope; 371 local tests and fresh Gemini 46/Luna 47 evaluations recorded in the delivery history. Neither live answer was fully accepted. |
| [GEMINI42_EVENT_TRACE.md](GEMINI42_EVENT_TRACE.md) | Detailed run-42 event reconstruction: Original/Vanilla/ZeroSugar call sequence, ZeroSugar inputs and tool outputs, citations per finding, rejected fields, retry feedback and release outcome. Read with the raw private exchange log for full payloads; the trace includes only the two excerpts needed to audit the citation mismatch, not the full comment set. |
| [Dataset README](../files_update/README.md) | Synthetic source definitions, periods, denominators and privacy assumptions; runtime behavior belongs to the code and application guides. |
| [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) | Attribution and reproduced license text. Preserve notices; do not rewrite them as project status. Reviewed without changing the license. |

## Executable configuration and instructions

| Source | Controls |
| --- | --- |
| [connections.json](connections.json) and [connections.py](agents/connections.py) | Non-secret model/endpoint/API settings, limits, role selection and key loading. Only key values come from process variables or ignored `.env`. |
| [.env.example](.env.example) | Empty key-name template; never actual credentials. |
| [policies.py](agents/policies.py) | Six common rules composed into analysis/model calls. This is the executable policy source, separate from coding-assistant guidance. |
| [Original](agents/original.py), [Cherry](agents/cherry.py), [Vanilla](agents/vanilla.py), [Lime](agents/lime.py), [ZeroSugar](agents/zero_sugar.py) | Role-specific prompts, tools and call paths. Shared rules do not transfer SQL, classification or verification ownership. |
| [run_agent.py](run_agent.py), [runtime.py](agents/runtime.py), [data_access.py](agents/data_access.py), [grounding.py](agents/grounding.py) | CLI scope/options, execution, source restrictions and deterministic checks. Code is authoritative when prose disagrees. |

## Local background and historical drafts

These four files are intentionally ignored by the repository and may be absent from a
clone. Their current-status notes were reviewed locally; inclusion here does not publish
them or approve their proposals.

| Local reference | How to use it |
| --- | --- |
| [technical_setup_agents.md](../technical_setup_agents.md) | Current local setup directions plus the distinction between installed SDKs and implemented adapters. |
| [echo_brainstorm_resumen_y_decisiones.md](../echo_brainstorm_resumen_y_decisiones.md) | Product/architecture proposals and unresolved decisions. Current reliability repairs preserve the five roles; proposed business execution is not implemented. |
| [brainstorm_employee_engagement.md](../brainstorm_employee_engagement.md) | September problem exploration, retained as history rather than current runtime specifications. |
| [alternativas_employee_engagement.md](../alternativas_employee_engagement.md) | September project/market comparison, not a refreshed market assessment or final selection. |

## Reasoned actions and review simplification after run twenty-three (2026-10-27)

The [current workflow](WORKFLOW_RELIABILITY.md#reasoned-actions-and-review-simplification-after-run-twenty-three-2026-10-27)
records the mandatory reasoned action for Original and a support-only contextual policy
correction, separate from user-requested completeness. Context, roles, source grounding,
README and testing guide are aligned. Novel action ideas remain proposals; objective
gates and prior artifacts remain. The [88 focused checks](TESTING_AND_RAG.md#reasoned-actions-and-review-simplification-after-run-twenty-three-2026-10-27)
do not establish improved live model judgment. No API call or publication.

## Explicit correction judgments after run twenty-one (2026-10-27)

The [review-v3 contract](WORKFLOW_RELIABILITY.md#explicit-correction-judgments-after-run-twenty-one-2026-10-27)
uses keyed semantic judgments and code-derived states, with canonical exports and legacy
v2 reading retained. Full repair text is supplied once; no sources or obligations are
removed. PROJECT_CONTEXT.md, README.md, AGENT_ROLES.md, SOURCE_GROUNDING.md, the testing
guide, project guidance and UI description/types are aligned. The
[validation record](TESTING_AND_RAG.md#explicit-correction-judgments-after-run-twenty-one-2026-10-27)
distinguishes the 147 focused software checks from live failures and analytical quality.
No publication, complete workflow run or UI build.

## Strict Chat transport follow-up (2026-10-27)

The [single-call follow-up](TESTING_AND_RAG.md#single-call-review-follow-up-after-run-twenty-2026-10-27)
adds the transport cardinality setting and content-free rationale diagnostics. Thirty-six
focused checks passed; one live saved-candidate completeness recheck completed with a
revise verdict. Complete workflow quality remains unverified; historical runs are retained.

The [transport checks](TESTING_AND_RAG.md#strict-chat-transport-follow-up-2026-10-27)
cover explicit strict-flag forwarding, three focused adapter checks and two minimal or
synthetic APInex Luna calls without employee data. PROJECT_CONTEXT.md, README.md,
WORKFLOW_RELIABILITY.md and project guidance record the scope and limits. Correction
semantics, both review phases and release gates are unchanged; full analytic quality
and other providers remain unverified. No GitHub publication.

## Current local semantic-review update (2026-10-26)

The [run-eighteen contextual contract](WORKFLOW_RELIABILITY.md#contextual-support-review-fields-after-run-eighteen-2026-10-26)
omits inactive administrative assessment fields from the support tool. Empty defaults
apply only when trusted task lists are empty; active coverage and source/review gates
remain. Actual-schema diagnostics and count-only support_contract metadata are retained.
Tests are aligned but unrun; no API calls or publication. V3 semantic guidance is unchanged.

The [run-seventeen simplification](WORKFLOW_RELIABILITY.md#general-semantic-guidance-after-run-seventeen-2026-10-26)
is current: shared rubric v3 gives general definitions and contextual model judgment.
Case-specific live guidance was removed; v1/v2 histories, full comment input, correction
traceability, all data controls and both reviews remain. Existing fixtures are aligned
without execution. No tests, provider calls, commit or GitHub publication.

The [run-sixteen follow-up](WORKFLOW_RELIABILITY.md#sentiment-and-correction-grounding-after-run-sixteen-2026-10-26)
adds shared versioned definitions in `agents/sentiment_rubric.py`, stored v2 rubric identity,
v1 replay, literal request grounding for new omissions, retained correction excerpts and
full released-group comment/label input to support review. Original's existing challenge
path and ZeroSugar's existing reassessment lifecycle remain responsible for judging
corrections. Counts-only coverage diagnostics and existing privacy/input-size bounds
apply; no new roles, provider settings or budgets. Guides and project context are aligned.
The user requested no tests or GitHub push; validation and live quality remain pending.
Run sixteen is retained evidence for the preceding version.

## Current local review recovery (2026-10-26)

The [recovery contract](WORKFLOW_RELIABILITY.md#review-recovery-after-run-fifteen-2026-10-26)
covers four total drafts with early stopping and unchanged shared budgets, optional
annotation normalization, conservative correction retention, justified
withdrawal of false omissions, and repair-only handoff after incomplete support. Original
still requires both reviews before acceptance. Completeness sees trusted scope/team
context; Cherry/Vanilla retain it from ScopedData. Prompts distinguish examples from
category totals. Context, roles, source contract, READMEs, testing and project guidance
are aligned. Source versions, provider settings, budgets and UI remain unchanged. This
update is local, without GitHub publication or a new live test.

## Current field-diagnostic follow-up (2026-10-26)

The [diagnostic contract](WORKFLOW_RELIABILITY.md#field-error-diagnostics-follow-up-2026-10-26)
updates validation.py, ZeroSugar field checks/repair records and focused regressions.
Current guides/context are aligned; source versions, semantics, roles, UI and provider
settings remain unchanged by this follow-up. Preserve run fourteen as observed evidence.

## Current review/data update (2026-10-26)

The current [workflow contract](WORKFLOW_RELIABILITY.md#review-and-data-contract-update-2026-10-26)
covers origin-neutral role instructions, canonical corrections/reassessment, metric relevance,
phase persistence, versioned partial release, v4/v1-v3 replay, export neutrality and the UI
projection. Update these guides together; historical sections retain their dated meaning.

## Maintenance rules

The 2026-10-26 core audit follow-up is recorded in PROJECT_CONTEXT.md, README.md,
AGENT_ROLES.md, WORKFLOW_RELIABILITY.md and TESTING_AND_RAG.md. It changes pending-review
coverage, Responses output-limit propagation and budgeted Chat request checkpoints;
source rendering, provider configuration and Echo_UI remain unchanged.

1. Verify changed behavior in code/configuration and the relevant result/log before updating claims.
2. Update the context entry and affected operating guides together. Update this map when a
   reference is added, moved, retired or changes purpose; do not copy every implementation
   detail into each file.
3. Preserve historical dates, failed runs and unapproved proposals. Separate implemented,
   observed, locally tested and pending-live behavior. Keep source-bearing reports local.
4. Check relative links, commands and contradictory old instructions. Documentation-only
   updates need content/link review, not live model requests or a new reasoning benchmark.
5. Generated Codex memory, classroom sources, source datasets and license text are not
   automatically edited by project-document maintenance.

The selected 2026-10-23 update is documented in the [current workflow](WORKFLOW_RELIABILITY.md#autonomous-synthesis-and-two-stage-review-2026-10-23), role guide, source contract,
README and testing guide. It retires mandatory deliverable planning and adds separate
completeness/support review calls with metadata-only phase traces. Specialist interfaces,
source replay and the manager UI artifact interface are retained. The full agent suite
passed 242 offline tests; no live provider call was made. GitHub publication is authorized.

Run eleven and its false completeness acceptance are recorded in PROJECT_CONTEXT.md.
For a later authorized repetition keep M14/Q3 2026 and `--profile apinex_test --run-seconds
1000`, preserving earlier artifacts with a fresh output such as
`reports/apinex_prueba_vanilla_12.json`. These offline checks do not certify the next live answer.
The group's manager chat UI remains available locally; natural-language date resolution,
authentication and enterprise writes remain deferred.

Historical documentation review checks: 17 Markdown references and 147 relative file/heading links checked without
errors; documented CLI options checked against `--help`. License text was unchanged.
Only APInex's descriptive status label changed in `connections.json`; endpoints, keys,
model assignments, limits and pacing settings were unchanged. The 207-test result belongs
to the prior implementation verification, not a new run for this documentation update.
