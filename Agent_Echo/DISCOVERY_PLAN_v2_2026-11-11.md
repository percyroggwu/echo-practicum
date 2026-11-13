# Echo Discovery plan v2: proactive contribution review

Date: 2026-11-11. Status: proposed plan; no implementation started.

This replaces the design recommendations in [the November 10 plan](DISCOVERY_BRAINSTORM_AND_PLAN_2026-11-10.md), which remains a historical record. It incorporates [five independent reviews and parent decisions](DISCOVERY_REVIEW_SYNTHESIS_2026-11-11.md). All five requested reviewers used **GPT-6 Luna, medium**; three reviewed the entire plan in parallel, one reviewed table information and one reviewed the existing harness.

## 1. Product contract

When a manager begins a review of their team for a selected period, Echo proactively looks for valuable contributions that ordinary scorecard review may miss or underdescribe. A useful finding states:

- What work or initiative occurred.
- Which authorized contributor or group performed it and who benefited.
- Which documented goal, milestone or outcome the evidence connects it to.
- How it relates to the contributor's formal goals and ordinary reporting.
- What proportionate manager decision merits consideration.

Discovery is a specialist alongside Cherry and Vanilla. Its initial activation is guaranteed by the application, not chosen by Original's model. Original coordinates the report and manager actions; ZeroSugar independently reviews the composed output. Recognition/visibility is a separate contextual axis, not the definition of contribution value.

The main scenarios explicitly assume correct prior collection and complete, coherent source evidence. Building that synthetic information is part of the future project work. Strong evidence does not require a prewritten conclusion or precomputed contribution-to-goal association.

## 2. Explicit activation and manager flow

Introduce three operation kinds, separate from execution modes `live`, `offline` and `replay`:

| Operation | Trigger and behavior |
| --- | --- |
| `team_review` | Manager enters/starts a review for trusted scope and period. Return a matching completed report if available; otherwise automatically run Discovery before Original planning. No special discovery question is required. |
| `ad_hoc` | Manager asks an ordinary question. Original selects the needed specialists and may use a valid reviewed report as context. It does not silently start a complete discovery pass. |
| `deepen` | Manager or Original requests a specific investigation from a report finding. Run bounded additional analysis and review the new output as a linked version. Do not overwrite the previous approved report. |

The UI can automatically initiate `team_review` when the review workspace is entered in the selected execution mode. Use a POST operation with a stable operation key, not model calls in GET page/overview requests. Repeated page loads and refreshes reuse the same current result or running job. The CLI exposes the same explicit operation, for example proposed `--operation team_review`, with manager, dates, cutoff and selected database/profile supplied by the application.

The trusted product code defines `review_task_spec_v1`: investigate evidence-backed contributions in the authorized population, explain relevance, separate visibility where useful and propose supported follow-ups. Store `task_origin=product_spec` and its version/hash. This is a product task, not a fabricated user quotation. Completeness obligations come from this actual specification; a policy-derived obligation must not invent `request_excerpt` text.

The first runtime implementation is sequential. Discovery may be independent of Original's selection without running concurrently with Cherry/Vanilla. Parallel execution would require separate design for shared counters, capture, cancellation and failure; defer it until latency measurements justify it.

## 3. One execution and approval path

Proposed lifecycle:

1. Resolve trusted scope, period, cutoff, roster and immutable dataset identity. Resolve the requested execution mode and operation.
2. Atomically look up or start the review operation. Return a valid completed report, or the already-running job, when the key matches.
3. Start the existing Original workflow. Its `run()` initializes the shared budget, transient state and workflow capture.
4. In `workflow()`, before the model's `plan(question)`, the `team_review` hook enumerates the candidate population and runs Discovery under phase guards. Seed cited results into the existing child-results/evidence handoff; do not bypass scope/source checks.
5. Original plans any additional Cherry/Vanilla/Lime work and composes the manager review using Discovery's candidates. It cannot disable the required initial investigation. A targeted `ask_discovery` is available for deepening or correcting findings.
6. ZeroSugar performs the existing two phases on the composed report: visible completeness against the product task, then evidence support and claim review. It reconstructs the same authorized source context independently.
7. Existing release controls produce complete, partial or failed output. Persist released report blocks with their actual review identity, scope, evidence and coverage. Unreviewed candidates stay internal.

This uses one initial synthesis/review/release cycle. There is no default extra review of Discovery followed by another full review of identical initial content. A later ad-hoc answer is a new candidate and receives normal review of that answer; a cached report's approval does not automatically approve new wording or new claims.

## 4. Coverage, source access and Discovery work

### 4.1 Candidate population

For the first controlled release, the population is all accepted `OP_contributions` for the home manager's authorized employees in the selected contribution period and known by the review cutoff. Include home-team and cross-team work, already-recognized work and routine work. Do not filter candidates by recognition gaps, keywords, expected value, goal-link presence or evaluation case IDs.

Construct a deterministic manifest ordered by contribution date and stable ID. Page through it and retrieve related context. Requests/projects are context and useful batching groups, not a rule that every contribution in one project is one finding. Discovery can combine contributions across dossiers when the sources support one initiative.

This deliberately excludes work absent from all contribution records in this first case scope. Employee-initiated work can be retrospectively captured as accepted work without having been a formal assigned goal. The demonstration discovers an overlooked relationship/value within correctly collected information; it does not claim to detect undocumented activity.

Coverage records distinguish eligible contributions, visited contributions, contributions assessed with required context, remaining contributions and context truncation. Track contextual sources separately so several comments for one contribution do not inflate population coverage. A full-manifest count is not evidence that all context was read or assessed.

### 4.2 Scoped dossier

Discovery and ZeroSugar receive the same permitted fields through shared backend projections:

- Contribution ID/date/summary, home and beneficiary team, accepted-work description and recorded business outcome.
- Related request/project IDs, deliverable, project objective and dated operational context.
- Complete applicable employee and home-team formal goals; relevant beneficiary-team goal context for this scoped work.
- Linked named partner feedback: source ID, date, author/beneficiary team, message and any explicit acceptance/outcome confirmation.
- Governed sharing/recognition events and collection-profile coverage where used.
- Source/projection identity, cutoff and coverage metadata.

Authorize beneficiary context through the scoped contribution's beneficiary team, request/project and relevant period, with an allowlist for goal text, success criterion and source/date fields. Permit the relevant beneficiary-team goal set needed to discover alignment; do not require a prefilled goal link to retrieve it. Do not expose beneficiary employee goals, rosters, unrelated projects or unrelated personnel feedback.

Use named operational feedback for person-level attribution. Anonymous survey text can supply team-level context or an initiative lead but cannot identify its author. Existing survey suppression rules remain. Search can retrieve supplemental context; search ranking does not determine the candidate universe or establish exhaustive coverage.

## 5. Recommended information model

### 5.1 Required addition: one assigned-goal table

Add proposed `OP_goals`, one row per version of one formal goal assigned to one owner for an effective period:

| Field | Meaning and constraint |
| --- | --- |
| `Goal_ID` | Stable unique row/version ID. |
| `Owner_Type` | `employee` or `team`; explicit rather than inferred from a blank field. |
| `Employee_ID` | Required FK for employee goals; null for team goals. |
| `Team` | Canonical existing pilot team name. For employee goals it must agree with the scenario's roster assignment. |
| `Period_Start_Date`, `Period_End_Date` | Goal applicability interval. |
| `Goal_Text`, `Success_Criterion` | Source content describing assigned expectations. |
| `Recorded_Date` | When this version became part of the recorded plan. |
| `Supersedes_Goal_ID` | Optional self-reference to a prior version; no cycles or incompatible owner changes. |
| `Data_Origin` | Preserve scenario provenance conventions. |

Validate team values against the current pilot roster; no separately verified team master table exists, so this plan does not invent a `Team_ID` foreign key. Define that active home-team goals apply to team members in addition to individual goals. The controlled case retains static team/manager assignments. The collection contract declares completeness of applicable goal sets by owner/period, including explicit owners with no individual goals.

Resolve applicable versions using goal period and knowledge cutoff; a later revision must not rewrite what the review knew earlier. If the current importer needs chronological insertion of self-references, generate earlier versions first and validate the chain. Separate reusable goal definitions/assignments can wait until many-owner shared goals require them.

### 5.2 Relationships Discovery derives

**Do not require `OP_contribution_goal_links` as input.** The relationship is one of the analytical outputs to discover. Store a derived relationship inside the report with contribution IDs, goal IDs, cited supporting passages, relationship interpretation and evidence state.

No link does not mean beyond-KPI work. Compare the contribution substantively with the complete applicable goal set. A meaningful contribution may support a beneficiary goal while being outside, or underdescribed by, the contributor's formal plan.

Prior human-confirmed associations may later be sources for reconciliation questions, with confirmer/date/provenance. They are excluded from the primary discovery-input cases. Do not store hidden expected mappings or `Exceptional_Value` verdicts in runtime records.

### 5.3 Reuse and enrich current records

Reuse `OP_projects`, `OP_work_requests`, `OP_contributions` and `HR_recognition_feedback`. Join project context through `Work_Request_ID` and `Project_ID`, not readable names. Accepted-work descriptions and independent named beneficiary interactions carry artifact/result confirmation. Do not add a generic evidence/initiative/outcome table unless the selected scenarios demonstrably cannot fit these sources.

For new scenarios, make sharing recipient/date explicit where needed, using proposed `Shared_To_Manager_ID` and `Shared_Date` on feedback. Distinguish the recipient of original feedback from the recipient of a later sharing action. A single sharing action per recorded feedback item is sufficient for this first scope; repeated distribution would justify an event relation later.

The new collection profile defines event dates, source knowledge dates when delayed entry is represented, goal completeness and complete governed recognition channels. Preserve legacy quarterly/capped feedback semantics under the legacy profile. Do not reinterpret old notes as a complete event history.

Derive visibility by cutoff: `recognized`, `shared_no_recorded_recognition`, `not_shared` or `unknown`. Later legitimate sharing supersedes an earlier unshared state; incompatible same-time evidence is a separate conflict. Recognized work may still merit expansion. These states remain separate from relevance.

`Actual_Hours` remains request-grain data. Do not multiply it through contribution/feedback joins or allocate one request's hours across recognition states without a supported allocation. General hours dashboards are deferred.

### 5.4 Versioned source selection

Create proposed `files_discovery_v1/` with the governed source pack, exact manifest/dictionary and collection contract. Preserve `files_update/`, classroom sources, licenses and old database/capture identities. Extend [import_data.py](import_data.py) with explicit legacy/discovery file profiles; keep its exact membership, type, FK, header, row-count and integrity checks.

Build a new database artifact and select its path/profile consistently in CLI, UI, specialists and runners. Current construction sites hardcode `data/echo.db`; introduce one explicit selected-database setting rather than divergent replacements. Bind profile/schema/data identities into the operation. Runtime analysis remains read-only.

## 6. Interpretation and relevance contract

Proposed modules: `agents/discovery.py` and `agents/discovery_rubric.py`. The readable rubric can be generated from the same authoritative definition or checked against it.

Discovery first reports evidence state for the contribution, beneficiary/outcome and formal-plan comparison: `supported`, `unresolved` or `conflicting`. These are claim-specific judgments subject to review, not deterministic certification of meaning.

Then it assesses relevance using anchored descriptions:

1. **Specific contribution:** identifiable work with authorized contributors and sources.
2. **Beneficiary benefit:** supported relationship to a documented need, goal, milestone or outcome.
3. **Underdescribed contribution:** substantive comparison with formal goals/reporting explains what ordinary review would miss.
4. **Decision relevance:** a proportionate recognition, coordination, sponsorship or expansion decision is motivated by the evidence.

Use `surface`, `not_priority` or `unresolved` with concise source-linked reasons. Omit numeric score totals: they add precision without establishing truth and can confuse missing evidence with low value. Do not force a number of findings or rank employee productivity. A complete empty result is valid; an incomplete search with no released finding is not proof that no opportunity exists.

Separate occurrence of work, occurrence of an outcome and the source's statement of how the work helped. A beneficiary confirmation supports documented contribution; it does not automatically establish a measured causal effect or financial return. Original owns final manager actions and preserves that distinction.

ZeroSugar receives the underlying authorized sources, applicable goal context, cutoff and rubric independently. It sees the final candidate claims it must assess, but producer confidence or prior approval cannot substitute for its own evidence judgment. Python verifies identifiers, scope, temporal rules and arithmetic; it does not decide semantic importance with keyword rules.

## 7. Harness extension map

Harness here means runtime orchestration, tool dispatch, state, budgets, review, release, capture and entry points, as well as evaluation tooling.

| Existing location | Required extension |
| --- | --- |
| [original.py](agents/original.py): `run`, `workflow` | Accept trusted operation/review context. Initialize state/budget/capture as today; run the automatic review hook before model planning. Register required Discovery work independently of planning flags. |
| `original.py`: `specialist`, `delegate`, `set_delegations`, repair routing | Explicit Discovery construction/task type; no fallback treating every non-Cherry role as Vanilla. Add targeted deepening/repair and retained cited evidence. |
| [runtime.py](agents/runtime.py): `AgentResult`, `Specialist`, `RunBudget` | Reuse the current loop/result path. Add typed discovery report metadata and bounded phase accounting. Include transport retries and repairs in shared limits. |
| [data_access.py](agents/data_access.py), [tools.py](agents/tools.py) | Add deterministic manifest/context tools and goal projection. Enforce contributor scope, partner allowlist, cutoff and source IDs before model access. |
| [grounding.py](agents/grounding.py), [content.py](agents/content.py), [findings.py](agents/findings.py), [validation.py](agents/validation.py) | Preserve citation/answer contracts; admit required goal-source fields and typed report metadata. Model judgments are not Cherry numeric facts. Version changed serialized meaning and preserve old replay. |
| `original.py`: `reviewer`; [zero_sugar.py](agents/zero_sugar.py) | Reconstruct source lookup from shared authorized backend even if Vanilla never ran. Review product-task completeness and source support through existing two phases. Extend correction-owner validation for Discovery. |
| `original.py`: `accept`, incomplete/release handling | Required incomplete Discovery cannot yield a complete report; release only independently supported blocks as partial. Keep requested-answer and discovery coverage statuses distinct. |
| [connections.py](agents/connections.py), [__init__.py](agents/__init__.py), [run_agent.py](run_agent.py) | Extend role registry to six; inherit model profile normally. Add operation, selected database and cutoff/context arguments. Keep ordinary ad-hoc behavior selective. |
| [policies.py](agents/policies.py) | Add the role to decline/ownership rules. Keep origin-neutral evidence analysis, scope, anonymity, source authority and bounded execution. Put discovery-specific relevance rules in its own module. |
| [capture.py](agents/capture.py), [execution_log.py](agents/execution_log.py), [resume.py](agents/resume.py) | Capture operation/task, data/rubric/projection identity, coverage, parent report and reuse status. Python source hashing already includes new `agents/*.py`. Preserve the prohibition on resuming Original workflows. |
| Proposed `agents/discovery_reports.py` | Small report-key/storage/validation helper, not another orchestrator. Atomic reviewed-artifact writes, strict reuse validation and parent-version lineage. |
| [app.py](../Echo_UI/backend/app.py): request/start/watch/replay/projections; [api.ts](../Echo_UI/frontend/src/lib/api.ts) | Carry operation identity into the existing CLI subprocess path; deduplicate repeated starts; present safe report/status/source summaries. Align offline/replay contracts and label execution mode. |

A trusted product-spec failure/omission uses the existing policy/task obligation semantics, not fictitious user wording. Factual interpretation/source-selection corrections return to Discovery; synthesis/action phrasing belongs to Original; deterministic source/tool faults are Python fixes. Existing candidate/correction identities, draft limits, disputes and reassessment remain.

## 8. Budgets, status and reusable reports

### 8.1 Limits inside the current budget

Current defaults are 32 model calls, 48 tool calls and 300 seconds per workflow. Keep them unchanged. A Discovery phase guard must count all work, including transport retries, within that same `RunBudget`; it is not an extra allowance.

Starting design parameters to freeze and calibrate before live evaluation: Discovery at most 3 model calls, 12 tools and 90 seconds, while preserving at least 6 model calls, 6 tools and 120 seconds for planning/synthesis/review. Stop before a new operation would consume the reserved floor. Apply the active phase guard at `consume/respond`, not only between high-level tasks. These are proposed conservative ceilings, not measured sufficient capacity or a guarantee of completion. If the pilot cannot be assessed within them, reduce the declared pilot population or revise the explicit parameters before a new frozen evaluation; never silently truncate and claim completeness.

Keep current total draft/retry limits and both review phases. If review itself cannot complete, follow current withholding rules. Runtime parallel execution and automatic cap increases remain out of scope.

### 8.2 Reusable report identity

Key a report by operation/task-spec hash; authorized manager/team/roster identity; period and cutoff; database/source snapshot and schema/profile; collection contract; rubric; projection/retrieval/analysis code; producer model/profile/settings; execution mode; and coverage-plan parameters. Resolve actual selected configuration, not just a mutable profile name.

Persist the released report as an internal versioned JSON artifact using the existing artifact/capture conventions. It contains released blocks, source references, review/candidate identities, eligible/assessed/remaining counts, limitations, provenance, creation time and optional parent report ID. Raw private capture contents are not the manager projection.

| Operation state | Meaning and reuse |
| --- | --- |
| `running` | A same-key job exists. Return that job rather than launching another. |
| `complete` | All required review work and declared coverage completed and released. May contain no findings. Reopen without model calls if identity still matches. |
| `partial` | Incomplete coverage or unresolved required work; only supported released blocks are visible. Never promote to complete or use as a complete-result cache hit. |
| `failed` | No releasable result for the operation. Explain the actual failure; no automatic repeated retries on page refresh. |

Show freshness and coverage. Changed identity means stale for current analysis. An old report can remain historical only within still-authorized scope and with its original identity; it is not current context by default. A targeted deepening creates a new candidate/report version and uses the normal release path.

Use atomic same-key reservation at the API/launcher boundary to deduplicate page loads/subprocess starts. Existing run directories can store job metadata; a small create-if-absent lock or equivalent is sufficient. On completion/failure release the reservation. After a process interruption, detect the absent job and mark interrupted/failed rather than serving an eternal running result. Do not build a general scheduling system or restore workflow checkpoints to implement reuse.

## 9. Strong scenario pack and controls

Keep private expected findings/mappings outside runtime source tables and prompts. Seed a realistic background corpus with sources carrying complementary facts, not explicit exceptional-value labels.

| Case | Complete source chain | Expected decision |
| --- | --- | --- |
| D1 | Accepted cross-team work; beneficiary goal/outcome confirmation; complete home goals; explicit governed unshared state. | Surface contribution value and a visibility follow-up. |
| D2 | Equally strong contribution; sharing to correct manager before cutoff; no recognition event in complete captured workflow. | Recognition follow-up, distinct from visibility. |
| D3 | Valuable contribution already recognized; outcome and goals recorded. | No invented recognition gap; value may still justify expansion if supported. |
| D4a | Employee-initiated improvement spread across several accepted contributions and independent named feedback; formal goals and beneficiary results complete; no input goal mapping. | Synthesize a useful initiative and motivate sponsorship or a trial. |
| D4b | A second initiative with different wording and source layout, plus unrelated positive background comments. | Demonstrate relationship finding beyond one memorized planted pattern. |
| D5 | Mentoring/coordination/handoff work, partner milestone and explicit confirmation. | Explain enabling value without productivity scoring. |
| D6 | Positive praise for routine successful work fully represented in the formal plan. | Do not equate sentiment or ordinary completion with an additional opportunity. |

Scenario records can include retrospective operational capture of employee-initiated work; traceability does not make it an original assigned goal. Document why the manager's ordinary scorecard view would underdescribe the contribution.

Separate robustness fixtures cover duplicate feedback, multiple contributions per request, later recognition, a revised goal after cutoff, out-of-scope records, anonymous text, incomplete pagination, budget stops and failed review. These are engineering checks, not a requirement that the main demonstration have weak data.

## 10. Evaluation harness and value test

Use existing freeze/result/adjudication conventions from [gold_cases.py](gold_cases.py), [gold_plans.py](gold_plans.py), [gold_m4.py](gold_m4.py) and [score_gold.py](score_gold.py). M1-M4 remain frozen; their specialized scoring is not reinterpreted as discovery quality.

Proposed additions: `GOLD_DISCOVERY_v1.md`, `gold_discovery.py`, `run_gold_discovery.py`, plus the smallest dedicated scoring extension needed for contribution/source relationships and human adjudication. Do not create another general evaluation framework.

Offline checks must cover trigger-before-plan, skipped automatic scan for ad-hoc, fixed population/pagination, source projection with no Vanilla, required Discovery failures, budget reserve including retries, owner-routed corrections, two-phase release, complete-empty versus partial-empty, report hits/misses/invalidation, repeated starts, crash cleanup, new-version deepening, UI/CLI/demo contracts and legacy replay. Extend current [test_workflow_scenarios.py](tests/test_workflow_scenarios.py) and relevant role/release/data/capture checks; archived old-protocol tests remain archived.

For semantic evaluation, freeze data, source IDs, task/rubric, model settings, budget and hidden expected findings before runs. Run two repeats of the seven main cases per configuration as a controlled demo gate; report raw per-case outcomes rather than a general accuracy claim. Human adjudicators are blinded to configuration and internal producer assessments; compare against the private reference, allow supported alternative wording and resolve disagreements by a recorded second review.

Use a common evidence/task foundation:

1. **Guided existing-specialist baseline:** existing Original/Vanilla analytical roles receive the same authorized dossiers, formal goals, task and rubric. This separates gains from better data/rubrics from gains due to a separate Discovery role.
2. **Proactive Discovery workflow:** the new activation/report lifecycle and specialist on the same sources and settings.
3. **Prepared general-purpose workflow:** equivalent permitted evidence, task and rubric, no hidden answers. Record actual product/model/access differences. A generic API simulation must not be described as a measured ChatGPT product result.

Measure useful supported findings, missed reference findings, false opportunities/recognition alerts, source fidelity, assessed-population coverage, protocol/release failures, preparation steps/time, model/tool usage and elapsed time. Workflow automation/effort and analytical quality are separate outcomes. Use an agreed task script to measure operator effort rather than inferred savings.

Proposed demonstration gates: all required offline checks pass; no released critical unsupported claim or scope leak; no false recognition gap on D3 or exceptional-opportunity alert on D6; each positive reference relationship is found with supporting sources in both repeats. A failed gate remains a recorded result. Prefer the simpler existing-specialist design if the new role offers no useful analytical or workflow gain. Neither a small gate nor ZeroSugar acceptance establishes broad production reliability.

These comparisons and live calls are future work, not authorized executions performed by this planning task.

## 11. Implementation sequence and boundaries

| Order | Deliverable | Exit condition |
| --- | --- | --- |
| 1 — P0 | Trusted operation/task specification, report identity, source/goal/coverage contracts and private case references. | Activation, source facts versus derived relationships and expected outputs are unambiguous. |
| 2 — P0 | Versioned data pack, one goals table, exact import profile and selected database path. | Coherent D1-D6/D4 variants import reproducibly with labels excluded. |
| 3 — P0 | Authorized candidate/dossier tools and standalone Discovery. | Fixed-population coverage and cited relationships work under bounded scripted contracts. |
| 4 — P0 | Review-mode hook, synthesis, independent review, correction ownership and release. | Complete/partial/failure semantics and unchanged legacy behavior pass offline checks. |
| 5 — P0 | Persisted released report, idempotent start/reopen and freshness display. | Reopening the same review adds no calls; invalid identity cannot reuse a current result. |
| 6 — P1 | Existing manager presentation with contribution card, sources, decision and coverage/freshness. | One clear D4-to-decision demonstration, with D3/D6 controls and mode labels. |
| 7 — P1 | Frozen matched semantic/effort comparison. | Results support or reject the distinct-role and workflow-value hypotheses. |
| 8 — P1 | Operating guides, dataset docs, context/map and role guidance updated for implemented behavior. | Current six-role behavior is distinguished from historical five-role evidence. |

Defer broad recognition dashboards, across-team hours views, parallel agents, new scheduler/orchestrator, new enterprise ingestion, automatic external messages/invites, employee ranking, generic source ontology, mandatory contribution-goal source links and workflow resumption. Preserve read-only data access, anonymity, strict identities, both reviews and supported partial release. Refresh the code graph after future code changes as the repository requires.

The main implementation risk is added work competing with an already bounded workflow. The plan addresses it through a finite population, phase guards, one initial approval path and report reuse. Completion/latency remains to be measured. All described behavior is proposed; the runtime still has five roles and no Discovery report lifecycle.

## 12. Planning-task verification

Five Luna/medium analyses completed and were synthesized; decisive runtime/table claims were checked against current files. The parent created this plan and the review record, preserved the November 10 plan, and reviewed references/content. Only documentation changed. No database generation, Python/prompt/profile change, tests/builds, live Echo runs, provider probes or Git publication occurred.
