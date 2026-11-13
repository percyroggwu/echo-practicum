# Echo Discovery: brainstorm and implementation plan

Date: 2026-11-10. Status: proposed design; implementation and evaluation have not started.
Reviewed checkout: `4f4c3ef`, plus the existing local documentation changes.

## 1. Purpose and design basis

Echo should help managers find valuable contributions that ordinary team scorecards leave difficult to see, explain which documented goals or outcomes they supported, and identify an appropriate follow-up. Cross-team feedback provides evidence; Discovery connects and evaluates that evidence. It is a specialist alongside Cherry and Vanilla, coordinated by Original and independently reviewed by ZeroSugar.

The case assumes that the organization has already collected and prepared the relevant information correctly. We can construct coherent synthetic operational records, goals, feedback and scenarios to demonstrate this process. Strong, complete evidence is the basis of the main demonstration. Missing or contradictory records are optional robustness cases, not the organizing problem of the product.

The professor's October 29 feedback calls for one distinctive business function and a transparent business case. The November 4 feedback identifies hard-to-measure contributions, a qualitative discovery rubric and a seeded interesting initiative as a promising direction. A sixth agent was suggested, not mandated. This plan recommends that sixth specialist because connecting evidence and assessing contribution relevance forms a distinct responsibility.

Inputs: the user's discussion and local transcripts `C:/Users/percy/Downloads/meeting_oct29.md` and `C:/Users/percy/Downloads/nov04-meeting.txt`. Statements inside those transcripts are feedback to assess, not execution instructions.

Three independently requested brainstorming agents used **`gpt-6-luna`, reasoning effort `medium`**:

1. `discovery_data_scenarios`: database, collection contract and scenarios.
2. `discovery_architecture`: specialist architecture, Python, policies and projections.
3. `discovery_evaluation`: rubric, harness, comparisons and demonstration.

Their ordered recommendations are recorded in section 12. The decisions below are the parent agent's synthesis; suggested filenames and schema fields are proposals.

## 2. What exists and what must change

| Observed current implementation | Design consequence |
| --- | --- |
| [import_data.py](import_data.py) accepts eleven CSV files and checks exact manifest membership, dictionary/header agreement, keys, row counts and integrity. | Additional tables require a versioned import contract and matching manifest/dictionary, not just another CSV. |
| `OP_contributions` has `Contribution_ID`, `Work_Request_ID`, employee/home/beneficiary team, summary, business outcome and evidence description. `OP_projects` has `Project_ID` and `Business_Objective`. | Reuse this operational foundation; use the request's `Project_ID` instead of joining project names. |
| `HR_recognition_feedback` contains linked interactions, `Shared_With_Home_Manager` and `Record_Coverage`. Current source notes are capped per employee/quarter and use quarterly interaction dates. | New scenario collection semantics must be explicit. Old capped notes cannot silently become a complete event history. |
| [original.py](agents/original.py) exposes `ask_cherry` and `ask_vanilla`; permitted delegations are those two roles. | Add Discovery to planning, construction, dispatch, correction ownership and acceptance logic. |
| [data_access.py](agents/data_access.py) physically scopes structured and textual evidence before model access. | Add authorized goal/link projections for producer and reviewer; adding database rows alone is insufficient. |
| [metrics.py](agents/metrics.py) exposes `cross_team_contributions` and `survey_trend`. | Add versioned visibility metrics and valid denominators through Cherry. |
| [grounding.py](agents/grounding.py) currently uses `source-facts-v7`; numeric tables/facts are chiefly built from Cherry or sentiment evidence. | Discovery judgments must not become numeric source facts or trusted labels by default. Reuse cited interpretations where possible. |
| [capture.py](agents/capture.py) hashes `run_agent.py` and all `agents/*.py`; database bytes also have an identity. | New Python agent/rubric modules are automatically included; add explicit rubric/data-contract identities if they live outside that set. Preserve strict old identities. |
| Current gold tooling separates automatic checks from human adjudication and freezes casebook identities. | Add a versioned Discovery case family using these conventions; preserve existing frozen gold. |

These are scoped source inspections, not a full repository audit or a functional validation.

## 3. Consolidated priority order

| Rank | Priority | Work package | Completion criterion |
| --- | --- | --- | --- |
| 1 | P0 | Define the business question, collection contract and operational states. | One agreed definition sheet and complete expected scenario outcomes. |
| 2 | P0 | Build a versioned scenario data pack with formal goals and goal links. | Reproducible import and valid multi-table records; private answers excluded from runtime. |
| 3 | P0 | Extend scoped access and deterministic visibility/goal tools. | The same authorized source records are available to Discovery and ZeroSugar; unrelated partner data stays excluded. |
| 4 | P0 | Add a small versioned Discovery rubric and specialist. | Standalone cited candidate findings with judgments separate from source facts. |
| 5 | P0 | Integrate Original planning, delegation and synthesis. | Discovery is selected for relevant questions and skipped for ordinary numeric/sentiment questions. |
| 6 | P0 | Extend independent review, correction routing and release contracts. | Both review phases operate on the actual final answer and supported findings can survive an unrelated failure. |
| 7 | P0 | Build offline contract, data and scripted workflow checks. | All required regressions and old-artifact replay checks pass on the implemented change. |
| 8 | P1 | Extend manager views, demo mode and exports. | One coherent discovery-to-action story appears consistently across CLI/UI and exported evidence. |
| 9 | P1 | Freeze a human-reviewed Discovery casebook and run a bounded comparison. | Report discovery quality, false findings, routing, cost and latency separately. |
| 10 | P1 | Prepare the presentation and explicit business assumptions. | Show a useful decision and a transparent value calculation, with scenario assumptions clearly identified. |
| 11 | P2 | Extend robustness and scale only when needed. | Additional cases address an observed limitation rather than speculative infrastructure. |

Ranks 2-7 form the first complete vertical slice. Rank 8 makes it presentable. This task creates the plan only; these are future implementation steps.

## 4. Database and scenario collection design

### 4.1 Recommended minimum schema extension

Reuse projects as initiatives and existing contribution/feedback records as evidence. Recommend **two new runtime tables** for the complete beyond-KPI demonstration:

| Proposed table | Grain and initial fields | Why it earns its place |
| --- | --- | --- |
| `OP_goals` | One documented formal goal for an employee or team and period: `Goal_ID`, `Team`, optional `Employee_ID`, optional `Project_ID`, `Period_Start_Date`, `Period_End_Date`, `Goal_Text`, `Success_Criterion`, `Data_Origin`. | Establishes the formal scorecard against which a beyond-goal interpretation can be assessed. A project's general objective alone does not establish an employee's assigned goals. |
| `OP_contribution_goal_links` | One documented relationship: `Link_ID`, `Contribution_ID`, `Goal_ID`, `Link_Explanation`, `Evidence_Reference`, `Confirmation_Date`, `Confirmed_By_Manager_ID`, `Data_Origin`. | Makes the beneficiary goal and confirmation traceable, supports several contributions/goals and avoids text-name joins. |

The dictionary must define team-owned versus employee-owned goals, nullable fields and foreign keys. A team goal is represented by `Team` with `Employee_ID` empty; an employee goal also names its employee. Owner semantics and goal-period coverage are validated. Use existing project objectives for initiative context and avoid a new initiatives table.

An unlinked contribution is not automatically beyond-KPI work. Discovery compares the contribution with the complete in-period formal goal set available under the collection contract. It explains substantive alignment or additional relevance. Goal-link rows are documented business relationships, not hidden evaluation answers such as `Exceptional_Value=True`.

For a narrower cross-team-only release, existing project objectives plus the link table may suffice. The recommended two-table design includes the beyond-formal-goals scenario discussed with the professor.

### 4.2 Collection contract and targeted field additions

Create a versioned dataset contract describing coverage, accepted-work semantics, formal-goal completeness, source IDs, responsible collectors, review cutoff and governed feedback/recognition channels. Complete collection is a valid explicit assumption of this scenario.

- Retain contribution, request, goal and interaction grains. Keep original evidence text alongside confirmation and provenance.
- For the new event-based scenarios, add `Shared_Date` and `Shared_To_Manager_ID` to feedback records if the existing quarterly flag cannot establish when and to whom feedback became available. Keep recipient-of-original-feedback distinct from recipient-of-sharing.
- Define `Interaction_Date` as the recorded recognition/feedback event date for the new profile. Preserve the old quarterly-review semantics under the legacy profile. Record dates and quarter cutoffs must not be silently interchanged.
- Record a contribution's `Project_ID` through its existing `Work_Request_ID`; add a direct foreign key only if there is a real need independent of requests.
- Employee-initiated work can be documented retrospectively in operational requests without making it part of the employee's original formal goals. Explain that distinction in the data contract.
- Named operational feedback can support contributor-level findings. Anonymous survey comments provide team context or initiative leads; they must not be linked to an employee identity.

### 4.3 Operational visibility states

Calculate states in Python/SQL from governed events and a selected review cutoff. Use the runtime collection profile, not a model guess, to interpret coverage:

1. `recognized`: a linked manager-recognition event exists by cutoff.
2. `shared_no_recorded_recognition`: sharing to the correct home manager is documented by cutoff and no linked recognition event exists by cutoff.
3. `not_shared`: the complete governed workflow or explicit current record establishes that sharing had not occurred by cutoff.
4. `unknown`: the applicable collection profile cannot resolve the state.

State transitions are temporal: a later sharing event supersedes an earlier unshared state; different dates are not automatically contradictory. Reserve conflict diagnostics for genuinely incompatible same-state evidence. Recognition takes precedence for the recognition classification even when no sharing event exists: recognition itself need not have followed partner sharing.

Call these documented workflow states in explanatory text. The case can explicitly define them as its operational meaning of noticed/recognized. Discovery's relevance assessment is a separate axis: recognized work may still reveal an opportunity worth supporting or expanding.

### 4.4 Versioning and integrity

Proposed new source directory: `files_discovery_v1/`, with versioned manifest/dictionary and collection contract. Preserve `files_update/`, classroom source references, license notices and prior database/capture identities. Build a new database artifact before changing the selected default; never overwrite a historical run's inputs.

Extend [import_data.py](import_data.py) with explicit legacy/discovery profiles, each having an exact approved file set. Avoid a generic accept-all-CSV importer. Validate references, types, goal periods, employee/request consistency, date ordering, home-manager sharing, goal confirmations, coverage declarations and private-label exclusion. New numeric fields must be added to the existing type declarations if used.

Select the versioned database consistently across CLI, UI, specialist constructors and evaluation runners. `run_agent.py` currently supplies `data/echo.db` at construction sites; centralize an explicit selected database path (a proposed `--database` option for the CLI) rather than scattering alternate paths. Bind the selected dataset/profile identity into artifacts and refuse incompatible profile/schema combinations.

Aggregate effort at its true grain. `Actual_Hours` belongs to a work request: joining it to several contribution or feedback rows must not multiply it. Shared request hours cannot be allocated to different recognition states without an explicit supported allocation. Report request-level totals separately or omit that breakdown.

## 5. Main scenario pack

Seed **six coherent scenarios** inside a realistic background corpus. Each uses correctly collected operational records; expected answers live only in the private casebook. Do not select a suspicious case by its ID or put an expected verdict into a runtime column.

| ID | Story and strong evidence to construct | Expected discovery and decision |
| --- | --- | --- |
| D1 | A home-team contributor helps another team meet a documented delivery goal. Accepted artifact, beneficiary confirmation, goal link and explicit unshared state exist. | Connect the work to the beneficiary goal; route the contribution to the home manager for review. |
| D2 | A similarly valuable contribution was shared with the home manager, with no recognition event by the controlled cutoff. | Distinguish a recognition follow-up from a visibility follow-up. |
| D3 | A valuable contribution is already shared and recognized. | Explain its value if requested; do not create a recognition-gap alert. |
| D4 | Several independent named feedback records and accepted artifacts describe an employee-initiated improvement outside the documented formal plan. Beneficiary goal/outcome confirmations are available. | Connect the fragments into one candidate initiative; explain why sponsorship or a broader trial deserves consideration. This is the principal qualitative-discovery story. |
| D5 | Mentoring, coordination or a handoff improvement helps a partner team achieve a documented onboarding/release milestone. The support and acceptance are explicitly recorded. | Surface a difficult-to-measure enabling contribution without assigning a person-level productivity score. |
| D6 | Positive praise and a well-completed routine task exist, but the complete formal plan and outcome records show an ordinary already-accounted-for activity. | Keep sentiment, successful routine delivery and additional discovery value distinct. A positive comment alone does not require an exceptional-opportunity alert. |

For D4, use several comments with different wording and complementary details plus unrelated background comments. Give enough evidence for a defensible synthesis without explicitly naming it an exceptional discovery. Multiple comments copied from one report are not independent confirmations.

Add targeted integrity/robustness fixtures separately: repeated feedback for one contribution; multiple contributions for one request; later recognition after cutoff; out-of-scope partner records; anonymous text; incomplete retrieval; genuine conflicting records. These test implementation behavior without making incomplete data the main case narrative.

## 6. Discovery contract and rubric

Proposed files: `agents/discovery.py` and `agents/discovery_rubric.py`. Human-readable companion: `DISCOVERY_RUBRIC_v1.md`. Keep one authoritative versioned rubric definition and make the document match it; do not maintain divergent producer/reviewer criteria.

**Input:** Original's bounded analytical question; trusted manager/date scope and cutoff; approved read-only tools; collection-contract/rubric identities. Discovery accesses its own scoped corpus through shared infrastructure and is not forced through Vanilla.

**Tools:** reuse scoped lexical retrieval initially. Add deterministic `list_discovery_candidates` and `get_contribution_context` only for necessary goal/event relationships and bounded enumeration. Tool names are proposals; expose a small interface rather than an unconstrained new query language.

**Output:** candidate ID; contribution/initiative source IDs; beneficiary and goal references; concise finding; documented outcome; rubric assessments with reasons; separately derived visibility state; unresolved questions; coverage summary. Original retains ownership of manager actions and final presentation.

Use four qualitative dimensions with 0-2 anchors:

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Contribution specificity | No identifiable contribution. | Work described but scope is incomplete. | Specific work/initiative and contributors or authorized group are traceable. |
| Beneficiary and outcome support | No supported beneficiary/result. | Contribution and beneficiary are supported; result partly established. | Explicit goal/outcome link and confirmation support the described benefit. |
| Relevance beyond ordinary reporting | Evidence shows ordinary accounted-for activity, or no comparison is possible. | Possible cross-team/enabling relevance. | Formal plan and evidence establish a meaningful contribution that ordinary scorecard review would miss or underdescribe. |
| Decision relevance | No supported reason for additional attention. | A plausible follow-up is identified. | Evidence motivates a concrete review, recognition, sponsorship or expansion decision. |

Scores organize explanations; their sum does not automatically establish truth or release a finding. A score of zero due to unresolved comparison must carry that reason, not mean poor employee performance. Return `surface`, `not_priority` or `unresolved` through contextual model judgment. No mandatory finding count, revenue forecast or employee ranking. Visibility is excluded from the relevance total so D3 can be valuable without having a recognition gap.

Named-goal questions may use targeted retrieval. Broad discovery questions use bounded enumeration of the eligible candidate population, then linked context retrieval, with completed/remaining counts and truncation status. A few search hits cannot support an exhaustive discovery claim. Reuse completed work; report partial coverage if the budget prevents completion.

## 7. Python, agent, policy and harness changes

| Area | Existing targets | Proposed change |
| --- | --- | --- |
| Collection/import | [import_data.py](import_data.py), `files_update/` contract conventions | New versioned dataset/profile; two tables and event fields above; existing profile remains reproducible. |
| Authorized evidence | [data_access.py](agents/data_access.py), [tools.py](agents/tools.py), [semantic_search.py](agents/semantic_search.py) | Project approved goals and goal links after contributor scoping. Expose linked beneficiary context only; do not grant the beneficiary roster or unrelated goals. Reuse retrieval/citation construction. |
| Metrics | [metrics.py](agents/metrics.py), [cherry.py](agents/cherry.py) | Add versioned visibility-state breakdown with disjoint states, denominator and cutoff. Cherry owns quantitative calculations; retain legacy metric replay. |
| New specialist | [runtime.py](agents/runtime.py), [__init__.py](agents/__init__.py) | Add/register Discovery using existing `Specialist`, result and bounded tool loops. Avoid a second orchestration framework. |
| Planning | [original.py](agents/original.py) | Add a Discovery planning flag, `ask_discovery`, construction, permitted task type, dispatch and retained results. Include it only where required; numeric-only and sentiment-only tasks must stay selective. |
| Roles/models/CLI | [connections.py](agents/connections.py), `connections.json`, [run_agent.py](run_agent.py) | Extend the five-role registry to six, allow inherited profile configuration and standalone Discovery invocation. Update any connection checks and role lists. No provider/model change is needed for the feature. |
| Shared policies | [policies.py](agents/policies.py) | Add Discovery to specialist decline/routing language; preserve origin-neutral analysis, source authority, anonymity, scope and budgets. Put relevance-specific instructions in Discovery's module/rubric. |
| Evidence/delivery | [grounding.py](agents/grounding.py), [content.py](agents/content.py), [findings.py](agents/findings.py), [validation.py](agents/validation.py) | Reuse cited interpretations and source envelopes first. Add typed goal/link source support where required; keep model scores as judgments. Numeric facts still come from Cherry. Version any changed serialized meaning; preserve source-facts-v1-v7 replay. |
| Independent review | [zero_sugar.py](agents/zero_sugar.py) | Supply authorized source context and rubric independently. Completeness checks visible requested work; support checks actual claims, goal links and relevance reasoning. Candidate scores are not trusted verdicts. Preserve both phases. |
| Corrections | `original.py`, `zero_sugar.py`, `findings.py` | Synthesis/presentation corrections belong to Original; faulty discovery interpretations or source selection return to Discovery. Deterministic tool errors are corrected in Python. Preserve identities, reassessment and justified disputes; no self-approval. |
| Execution/capture | [runtime.py](agents/runtime.py), [capture.py](agents/capture.py), [resume.py](agents/resume.py), [execution_log.py](agents/execution_log.py) | Account for Discovery in existing budgets/statuses and capture. New agent modules are already covered by Python source hashing. Add contract/rubric identity and workflow snapshots as needed. Preserve currently unsupported workflow-resume restrictions; do not re-enable old continuation as part of Discovery. |
| Presentation | [app.py](../Echo_UI/backend/app.py), [offline.py](../Echo_UI/backend/offline.py), [api.ts](../Echo_UI/frontend/src/lib/api.ts), manager view/export files | Add role/status display, findings and safe source/goal details. Align demo and live output shapes. A demo path must be identified as scripted. |

Do not add mandatory reviewer phases, raise global budgets or make all six agents run for every question. Keep Lime optional and fed by supported Cherry numeric evidence. If a Discovery chart is needed, Cherry supplies its numeric source rather than sending a model relevance score directly to Lime.

## 8. Evaluation and acceptance

Reuse the conventions and helpers in [gold_cases.py](gold_cases.py), [gold_plans.py](gold_plans.py), [gold_m4.py](gold_m4.py), [score_gold.py](score_gold.py) and existing runners. Existing scorers have case-family-specific assumptions: add a thin Discovery extension rather than silently reinterpret frozen M1-M4 results.

Proposed additions: `GOLD_DISCOVERY_v1.md`, `gold_discovery.py`, `run_gold_discovery.py` and a scoring extension only where existing scoring cannot represent discovery findings. Keep expected contributions, required source links, acceptable interpretations and prohibited inferences in evaluator-only fixtures. Runtime source directories and model prompts must exclude gold labels. Human adjudicators use the reference during scoring; all compared systems remain blind to it.

| Layer | What to verify |
| --- | --- |
| Data/import | Exact profile schema, source/goal references, temporal state transitions, controlled coverage, dates, non-duplicating effort totals. |
| Specialist contract | Valid scope/citations, candidate/reference structure, bounded retrieval, state/score separation and partial coverage. |
| Planning/repair | Discovery questions route correctly; ordinary tasks do not invoke it; finding corrections return to the right owner and retain valid work. |
| Review | Catch exaggerated outcome/goal claims, missed requested findings and fabricated recognition gaps; accept supported interpretations without enforcing exact wording. |
| Scripted end-to-end | Extend current [test_workflow_scenarios.py](tests/test_workflow_scenarios.py) and relevant role/release/capture regressions. Do not reactivate archived old-protocol tests. |
| Human semantic evaluation | Did the live model find the meaningful contribution, connect the right sources and recommend proportionate attention? |
| UI/export | Safe projections, correct role/status/evidence display and demo/live shape parity. |

Proposed gates, to freeze before implementation evaluation:

1. All required deterministic/regression checks pass, including old artifact replay and scope isolation.
2. Each D1-D6 case has a human-reviewed reference before live model runs.
3. First bounded live comparison: two repeats of each D1-D6 case per configuration, fixed order and frozen inputs. Compare **current Echo** with **Echo + Discovery** first; report raw counts, protocol failures, matched reference findings and false findings. No critical unsupported factual claim, scope leak or false recognition-gap alert may be released in this set. Each positive case's core finding must be recovered in both repeats before it is called demo-ready. These are proposed small-case gates, not general-accuracy claims.
4. Report human-rated usefulness and evidence fidelity separately from model acceptance, schema validity and workflow completion. Do not tune the private answers to rescue a failed run; create a new version if the case contract changes.
5. Freeze a shared per-run call/time budget before testing. Discovery consumes that existing budget; do not create an extra review allowance. Record eligible/processed candidates, calls, tokens where available, time, partial coverage and cost assumptions. Keep analytical errors separate from delivery/protocol failures.

A later comparison against a general-purpose ChatGPT workflow can address the professor/judge objection. Give it the same permitted evidence, task definitions, goal context and rubric, without gold answers; record operator preparation and access differences. Match model configuration where possible and disclose unavoidable differences. A first-run chatbot with less context would be an unfair baseline. Measure the effort needed to reach a useful, traceable decision as well as output quality.

No offline model stub, planted successful example or ZeroSugar acceptance establishes live semantic capability by itself. Strong designed evidence makes the intended scenario testable; evaluation checks whether the system actually uses it correctly.

## 9. Manager demonstration and business case

Lead with D4: a useful initiative is fragmented across properly collected records and sits outside the contributor's formal goals. Show the goal comparison, beneficiary outcome, source links and Discovery's explanation. Original turns the supported finding into a proposed manager decision; ZeroSugar reviews it. Then show D1/D2 and briefly D3 to distinguish visibility, recognition and already-resolved cases.

Manager view recommendation: a compact contribution card showing work, beneficiary, documented result, relevance explanation, visibility state and next action. Add the disjoint visibility breakdown to the existing team view. An Across teams view can follow using scoped hours given/received and goals supported; resolving inbound/outbound access rules is required before exposing another team's work. Reuse Gaps and draft-note flows where appropriate. Do not make late-work analytics an independent new project.

Business value: reduce the effort needed to discover, understand and discuss overlooked contributions; improve the information available for recognition, coordination or sponsorship decisions. These are the intended benefits. Scenario economics may use explicit manager-review time, task frequency, operating cost and alternative assumptions. Counted effort is not automatically saved capacity or new revenue. Recalculate all demonstration percentages from the final versioned data; the previously discussed 70%/13%/18% and 245,000 hours are not verified results of this plan.

## 10. Implementation sequence and deliverables

1. **Contract and casebook draft:** freeze operational definitions, goal ownership, six scenario stories and source requirements. Deliver the schema/data dictionary diff, collection contract and private expected findings.
2. **Data and tools:** generate the versioned records, validate import, implement goal projections and visibility metrics. Deliver the new reproducible database artifact and deterministic checks.
3. **Standalone Discovery:** implement the rubric, retrieval/context tools and cited candidate output on D4 first, with D3/D6 controls. Deliver candidate artifacts and coverage metadata.
4. **Complete workflow:** wire planning, delegation, independent review, correction routing, captures and release. Deliver scripted end-to-end checks and backward-compatibility results.
5. **Presentation:** align CLI/UI/demo/export, add contribution cards and reuse the existing action paths. Deliver a reviewable end-to-end demonstration.
6. **Bounded semantic measurement:** freeze identities, run the defined comparison, adjudicate results and record actual cost/time. Deliver a results table including failures and unresolved cases.
7. **Documentation:** update role/workflow/source/testing guides, both READMEs as affected, dataset contract, documentation map, project context and [../AGENTS.md](../AGENTS.md) to distinguish current six-role implementation from historical five-role behavior once the feature is implemented. Refresh the code graph after code changes, following repository instructions.

## 11. Decisions resolved and deliberately deferred

- **Selected:** a new peer specialist, two-table goal extension for the full scope, strong primary scenarios, existing orchestration/review machinery, and relevance separated from visibility.
- **Adapted from agent proposals:** the data proposal's single goal-link table becomes two tables because a formal scorecard is necessary for the beyond-KPI claim. Reuse project objectives for context, not as a substitute for employee/team goals.
- **Adapted:** the evaluation proposal's visibility dimension becomes a separate deterministic state. Already-recognized valuable work remains eligible for opportunity discovery.
- **Deferred:** a new generic evidence framework, dedicated initiative/outcome/recognition-status tables, embeddings dependency, enterprise ingestion, sending emails/invites, user-authentication redesign, automatic personnel actions, productivity rankings and changes to global budgets.
- **Deferred:** missing/contradictory data as a central demonstration. Such cases belong to bounded robustness fixtures after the strong main stories work.
- **Preserved:** private gold separation, anonymous-survey protections, strict source/data identities, old profiles and artifacts, independent review and source-grounded partial release.

Runtime integration requires changes beyond the standalone specialist. The five-role restriction in current guidance remains the current behavior; implementation of this proposed extension must explicitly update it to six. This plan does not claim that agent behavior can remain unchanged or that existing test totals validate Discovery.

## 12. Ordered recommendations from the three brainstorming agents

These are condensed ranked inputs, including suggestions that were adapted above.

### A. Data and scenarios — GPT-6 Luna, medium

1. **P0:** Reuse contribution/feedback grains and add an explicit contribution-to-goal link.
2. **P0:** Define sharing, recognition, as-of cutoff and authorized beneficiary context.
3. **P0:** Extend collection documentation, dictionary/import checks and scope controls.
4. **P1:** Seed linked cross-team, shared/unrecognized and recognized cases with expected findings outside runtime.
5. **P1:** Prevent request-hour multiplication and distinguish missing/late/contradictory records in robustness fixtures.
6. **P2:** Version the new source drop and preserve the original dataset/captures.

### B. Agent architecture — GPT-6 Luna, medium

1. **P0:** Add Discovery as a bounded peer using `Specialist`; extend Original and role/profile registration.
2. **P0:** Separate cited source records from rubric judgments and independently review both.
3. **P1:** Reuse scoped retrieval, add only necessary context/coverage tools and bound broad searches.
4. **P1:** Route corrections by responsibility and preserve selective execution/shared budgets.
5. **P1:** Align UI, CLI, projections and exports without exposing private captures.
6. **P2:** Cover contract, scope, budget, replay and presentation parity.

### C. Rubric, evaluation and demonstration — GPT-6 Luna, medium

1. **P0:** Use a small anchored rubric with reasons, source links and an unresolved result option.
2. **P0:** Keep discovery and independent evidence review separate.
3. **P1:** Build positive scenarios plus recognized, routine/sentiment-only and targeted robustness controls.
4. **P1:** Extend gold conventions; separate automated checks, human semantic adjudication and live results.
5. **P1:** Freeze acceptance/budget criteria and compare the same evidence under the same scope.
6. **P2:** Present one strong end-to-end story with transparent business assumptions.

## 13. Verification of this planning task

Completed: three requested Luna/medium brainstorming tasks; graph-guided source inspection; parent synthesis; plan creation and reference/content review. No application code, prompts, database records, model profiles or frozen gold cases were changed. No application tests/builds, provider connection probes, live Echo workflows or Git publication were performed. Existing unrelated documentation changes were preserved.
