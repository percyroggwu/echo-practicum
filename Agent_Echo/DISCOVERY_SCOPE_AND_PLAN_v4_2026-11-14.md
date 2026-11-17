# Echo Discovery v4: a focused, evidence-backed demonstration

Date: 2026-11-14. Status: proposed implementation plan; documentation only.

This is the current Discovery plan. It supersedes the recommendations in [v3](DISCOVERY_SCOPE_AND_PLAN_v3_2026-11-12.md), preserving that document, [its seven reviews](DISCOVERY_SEVEN_REVIEWS_2026-11-12.md), [v2](DISCOVERY_PLAN_v2_2026-11-11.md), [the earlier review synthesis](DISCOVERY_REVIEW_SYNTHESIS_2026-11-11.md) and [the initial brainstorm](DISCOVERY_BRAINSTORM_AND_PLAN_2026-11-10.md) as history. It incorporates the November 14 auditor observations and the subsequent source checks, with the qualifications recorded below. Creating this plan does not authorize runtime changes or live evaluations.

## 1. Outcome and minimum demonstration

Investigate employees' accounts of unrecognized work and proactively identify supported work without an employee account. Explain the benefit to the home or beneficiary team, distinguish the recorded recognition state, and prepare a proportionate manager response supported by citations.

The first delivery is one manager review, one partner-team context, one initial knowledge cutoff, and one composed analytical report. Every eligible employee account receives an assessment, including routine work, unfinished work, disputed claims and work without an accepted contribution. The proactive path must demonstrate a positive finding as well as a negative control.

Deliver a manager-visible work-case summary, source-linked findings, eligible/assessed/unassessed coverage, and a draft response for every eligible employee account. A response is prepared, not delivered. There is no manager-action approval, employee delivery claim or closure claim in this version.

Do not claim improved engagement, retention, employee productivity or revenue from the demonstration. Discovery is useful only if the evidence and resulting decisions are useful; adding a role is not itself an improvement.

## 2. Selected scope and calendar

| Dimension | Selected v4 design |
| --- | --- |
| Home review | M32, Sales Operations |
| Focal employees | E0002, E0010, E0032, E0058, E0107, E0162 |
| Beneficiary context | Infrastructure, M16; relevant goals, process evidence and confirmations only |
| Baseline evidence | 2026-01-05 through 2026-03-29 |
| Eligible work | 2026-03-30 through 2026-06-21 |
| Knowledge cutoff | 2026-06-21, inclusive |
| Follow-up | Deferred; no August snapshot or later action history in this delivery |

These roster IDs were checked during v3 planning; revalidate employment, manager and team relationships against the selected source snapshot before constructing v4 records. If incompatible, stop source construction and document a revised roster rather than silently moving people or dates.

Baseline and work windows are each 84 days. Comparable measurement subwindows must be specified per metric; baseline evidence does not enlarge work eligibility. A source must be recorded by cutoff, even when its event date is earlier. Later records never enter the initial result.

The review covers the six-person cohort, not every employee on M32's team. M16 does not authorize access to Infrastructure employee rosters, personal goals or unrelated work.

## 3. Existing extension: reuse without changing its meaning

[The existing extension](../data_extensions/README.md) describes 12,670 `HR_goals` rows, 12,129 `HR_self_review_items` rows, a private answer key and a planted M14 project. Its self-reviews concern December 2025; 2026 contains goals only. These are not already equivalent to the v4 March-June 2026 intake and work histories.

On November 14, a read-only inspection of this checkout's `data/echo.db` found the eleven original tables and neither extension table. The README describes a load capability, not proof of this local database's current contents. Reinspect the selected database when implementation starts; do not generalize this observation to other machines.

Selected reuse decisions:

- Reuse relevant 2026 `HR_goals` records after checking cohort ownership, applicability and completeness. Keep `HR_goals` as the canonical goal family; do not introduce a duplicate `OP_goals` master.
- Reuse self-review schema ideas and generator utilities where appropriate. Preserve the existing December 2025 self-reviews; do not relabel their dates, treat them as June 2026 intake, or assume their claims are independently corroborated.
- Construct a small, explicitly new 2026 employee-account source. An optional provenance link to an earlier self-review is historical context, never an eligibility shortcut.
- Preserve the M14 planted case and `QA_discovery_answer_key.csv` unchanged. They are not the M32 demonstration or its answer key. Runtime projections must exclude every QA answer key.
- Leave `files_update/`, the extension CSVs/generator and the current database unchanged. Create `files_discovery_v1/` and a separate `data/echo_discovery_v1.db`, selected consistently throughout CLI, UI, specialists, reviewer and evaluation.

The importer currently fixes eleven filenames and maps SQL types by column name. Build a versioned package profile with exact permitted files, per-column types, references, nullability and loading order. Preserve the legacy profile. Numeric values, numerators and denominators must have validated numeric types. A validated rebuild of the Discovery database must never replace `data/echo.db`.

## 4. Evidence design and construction worksheet

Table count follows required facts. Removing a relation is acceptable only if all source grains, multiplicities and acceptance checks still work. This scope reduction is not a new arbitrary table quota.

| Source family | Grain and minimum contract |
| --- | --- |
| Reused `HR_goals` | One applicable goal assignment. Preserve source IDs; document effective dates and known-by dates. If goal revision history is required, enrich the selected package schema explicitly with version identity and supersession; do not invent history from `Set_Date`. |
| New `OP_employee_work_reports` | One named employee account: ID, employee, submitted/recorded dates, work dates, narrative, claimed benefit and requested response. No contribution FK is required. |
| New `OP_work_report_links` | One account-to-request/contribution/work-event reference, with origin and recorded date. Exactly one target per row. Retain many-to-many references and duplicate account origins. Do not replace this with a single FK when an account spans several tasks. |
| New `OP_work_events` | One dated assignment, delivery, acceptance, rejection, completion, reopening, blocker or milestone event. Include actor, request/work anchor, event and recorded dates, deliverable/criterion, origin and source reference. |
| New `OP_outcome_observations` | One measured case or aggregate observation: metric-definition version, process/team, window, value/unit, count/exposure as applicable, case ID where applicable, source, method and recorded date. |
| New `OP_metric_definitions` | One versioned metric: grain, formula/statistic, unit, population, inclusion/exclusion rules, timestamp rules, comparable windows and missingness handling. Producer and reviewer read the same definitions. |
| New `HR_work_review_events` | One pre-cutoff source event recording sharing, acknowledgment or recognition, including work/account anchor, actor, recipient, event/recorded dates, event type and source provenance. This is read-only source history, not a writable action ledger. |
| Enriched existing feedback | One work-specific confirmation. Permit a request/report/event anchor without a contribution. Require at least one valid work anchor, typed author identity, source provenance and dates. A manager or employee author must resolve to the corresponding master; do not use fabricated manager IDs for peers. |
| Reused/enriched operational sources | Projects, requests, accepted contributions and relevant priority decisions with consistent IDs and selected-package provenance. Preserve legacy semantics under the legacy profile. |

Recognition source history remains necessary to distinguish already recognized work from an apparent gap. Deferring the action ledger does not justify dropping recognition evidence.

### 4.1 Construction targets

| Item | Target for the compact pack |
| --- | --- |
| Population | Six focal employees; two manager/team contexts |
| Work | Approximately 12 distinct work cases, represented by approximately 18 requests and their relevant projects/contributions |
| Employee accounts | At least eight eligible accounts: one per employee, one additional overlapping account, and one additional unsupported-credit account; plus three excluded-account controls |
| Formal goals | Complete applicable individual goals for all six employees and relevant home/partner goals; exact count comes from selected sources |
| Work events | Approximately 40, including accepted and unfinished work and raw timing observations where needed |
| Confirmations | At least two independent source chains for S4; work-specific confirmation for each supported positive case; deliberately conflicting sources in one control |
| Recognition history | Exact events needed for acknowledged, shared, recognized and unknown states; no fabricated dispositions to satisfy a quota |
| Metrics | At least three definitions covering process duration, rate/quality and milestone/goal attainment |

Targets are not generated counts. The manifest records actual quantities and reconciles shared rows. Do not assert that six people represent six independent observations of a team-level outcome.

The private worksheet is a CSV or Markdown table, one row per scenario/account/work-case association. Required columns: scenario ID; account IDs; work-case/source IDs; focal employee; goal IDs; event/recorded dates; cutoff eligibility; confirming author and original source chain; metric/version/raw-observation IDs; recognition history; expected supported/unsupported/alternate interpretation; forbidden inference; intended visible output; acceptance check. A second reconciliation lists every distinct runtime row and its source family. Shared evidence is referenced, not counted twice.

Scenario IDs, expected decisions and private answer-key columns never enter runtime tables or model prompts. Ordinary factual links and employee-supplied references are legitimate runtime evidence.

### 4.2 Recalculable measurement rules

- A median such as 8 versus 5 business days requires all 40 and 44 case-level observations, start/end timestamps, calendar convention and inclusion rules. Those counts are optional illustrations; omit or replace the example if the compact pack cannot supply the raw observations. Do not infer a median from aggregate totals.
- Rates retain numerator, denominator, exposure, unit and comparable windows. Show descriptive differences with sample-size limitations; an observed decrease is not automatically a reliable improvement or a causal effect.
- Do not reproduce the auditor's approximate p-value as an established result. Any inferential analysis needs an explicit method and assumptions; it is not required for this small demonstration. If intervals are shown, name the method and compute them reproducibly.
- Cherry computes approved measures; ZeroSugar can independently recalculate them from the same authorized raw source. Do not multiply request hours through feedback/contribution joins or allocate shared credit without evidence.
- Separate delivered work, accepted output, observed outcome and attributed mechanism. Qualitative beneficiary confirmation can be useful without invented financial values.

## 5. Cases and acceptance matrix

The case identifiers below retain v3 meaning where possible. Every positive source chain has background distractors; the pack must not announce its intended verdict in a conspicuous source sentence.

| Case or promise | Required evidence | Visible acceptance |
| --- | --- | --- |
| S1: routine home-team value | Named account, accepted tasks, applicable goal and home-team confirmation | Explain supported routine benefit and prepare a proportionate response; goal alignment is not an exclusion. |
| S2: partner-team help | Account, delivery/acceptance, beneficiary need or goal, confirmation and governed sharing history | Explain who benefited and the supported result without exposing unrelated partner data. |
| S4: work without contribution row | Named account, no accepted-contribution row, at least two delivery/acceptance events and two independent confirmation chains | Investigate and assess the work; do not pretend an accepted-contribution record exists. |
| S5-P: positive proactive discovery | Work has no employee account; cohort-attributed delivery/acceptance, relevant goal/need, beneficiary confirmation and supported result; recognition coverage specified | Automatically surface a useful work/benefit finding and a justified recognition/coordination proposal. The operation starts without a manager asking about that item. |
| S7: already recognized | Concern plus dated, relevant recognition evidence known by cutoff | Preserve the concern, explain recorded recognition and avoid invented missing credit or duplicate-credit proposals. |
| S10: effort, unfinished output | Account, blocker/current work history and possible praise, but no acceptance | Acknowledge effort and propose help; do not claim completed delivery or realized benefit. |
| N1: contradicted account | An employee claim with explicit contradictory operational evidence | Distinguish the claim from the supported facts and show the unresolved/contradicted portion. |
| N2: credit for another person's work | Claim plus source attribution identifying the actual contributor(s) | Do not assign credit to the claimant without support; expose no unrelated personnel details. |
| N3: scope/time exclusions | Three account controls: outside cohort, outside work window, and recorded after cutoff | Exclude through trusted rules and reconcile exclusion IDs/reasons privately; do not leak excluded narratives to the model or manager report. |
| N4: conflicting confirmations | Independent sources disagree on an important claim | Show uncertainty/conflict instead of silently selecting the favorable source. |
| N5: overlapping accounts | Two eligible accounts reference related work | Preserve both accounts and their responses while avoiding duplicate work totals or credit. |
| N6: proactive negative control | No account; routine work with existing acknowledgment and no supported recognition gap | Describe value when relevant, without inventing an exceptional opportunity or gap. |
| Coverage and review | Manifest, assessed IDs, outstanding items and both review phases | No eligible account disappears; incomplete assessment or failed required review cannot produce a complete report. |
| Response boundary | Assessment, reason, responsible manager and proposed next step for each eligible account | Output is explicitly a prepared draft, never a sent acknowledgment or completed human action. |

The same work can support more than one control, with explicit worksheet mapping. For S5-P, no account may reference that work indirectly; checking only a blank direct FK is insufficient. S9's earlier negative-control idea is retained as N6. S3, S6, S8 and S11 are deferred as standalone demonstrations, not silently declared satisfied.

## 6. Inclusion, scope and privacy

Keep `AccessScope` unchanged for legacy artifacts. Introduce a separate immutable, versioned review context (proposed name `ReviewScope`) containing cohort, work window, baseline/evidence windows, cutoff, selected source/profile and task-spec identity. Bind that context into new artifact identities and reviewer checks. Old artifacts retain their original equality and replay rules; adding optional context must not retroactively change their dictionaries.

Deterministic entry rules:

1. Employee accounts enter if the employee is in the cohort, claimed work overlaps the work window, and submitted/recorded dates are no later than cutoff.
2. Contributions enter if cohort-owned, accepted in the work window and known by cutoff.
3. Operational work enters from a cohort-owned request completion or a cohort-attributed delivered/accepted/completed/milestone-accepted event in the work window and known by cutoff. Assignment, blockers and reopening enrich existing work rather than each creating a new case.
4. Goals, outcomes and confirmations enrich eligible work only. They cannot expand the employee population. Baseline sources are available solely for approved comparisons.

Use explicit source references for initial deduplication; model-proposed semantic merges require a reviewed reason. Keep account-origin IDs independently of case grouping. Unknown recognition coverage means unknown recognition state, not proof of no recognition.

Partner projection is an explicit list of permitted fields and work/process/team identifiers. M16 receives only a minimal confirmation request or relevant work context in the scenario, never the employee's complaint or the full home-manager analytical report. There is no external sending in v4.

Employee-account narratives are visible only in the selected home-review projection and restricted private execution captures. If the concern is about the home manager, hold the substantive account out of that manager's projection and mark it as requiring an independently designated reviewer. Do not invent an escalation recipient or claim escalation was delivered. Such a case cannot receive an ordinary complete home-manager disposition without the designated review path.

Anonymous survey ingestion is deferred from the compact demonstration. Existing five-response suppression remains unchanged. Any later S11 requires invited/respondent population definitions, release thresholds, content review and assessment of linkage to named narratives; ten invitees alone is not an anonymity guarantee.

The local manager selector/API is a simulation, not authenticated organizational authority. Label it accordingly. Full private captures may copy source narratives; no credentials belong in captures, and private captures are not manager exports. Proposed pilot retention is 30 days after final demonstration, followed by owner-performed deletion of raw narrative captures and retention of de-identified evaluation summaries. This is a proposed policy, not an automatic deletion authorization or an implemented enforcement mechanism; retention/access ownership must be settled before any real employee data is used.

## 7. Roles, task specification and review

| Role | v4 responsibility |
| --- | --- |
| Discovery, proposed sixth role | Reconcile account and proactive leads, propose reviewed case merges, interpret work/goal/beneficiary relationships and report claim-specific evidence states and recognition relevance. |
| Cherry | Recalculate approved measures from typed source observations and metric definitions. |
| Vanilla | Interpret authorized narratives as needed; sentiment never gates inclusion or establishes work. |
| Original | Coordinate, compose the report, account for every eligible account and prepare proportionate draft responses. |
| Lime | Present reviewed numeric results only when a chart helps. |
| ZeroSugar | Independently check task completeness and source support, including attribution, calculations, cutoff, recognition and draft-versus-delivery claims. |

Restore a versioned `review_task_spec_v1` supplied by trusted product code. It defines the cohort review, account accounting, proactive search, evidence distinctions and required visible outputs in this plan. Record `task_origin=product_spec` and its version/hash. ZeroSugar receives the actual task specification; do not invent user quotations to support product requirements or apply a sentiment question's completeness contract to Discovery.

Restore an anchored relevance rubric: identifiable work; supported beneficiary benefit; comparison with applicable goals/ordinary reporting; and a decision justified by evidence. Report claim-specific `supported`, `unresolved` or `conflicting` states separately from proactive priority (`surface`, `not_priority`, `unresolved`). No numeric employee scores, exceptional-value admission gate, forced finding quota or keyword substitute for semantic judgment.

All eligible accounts receive assessment regardless of priority. Proactive prioritization cannot erase routine value or unresolved accounts. Prefer amended existing specialists if matched evidence shows that the separate role adds no useful benefit; if the small comparison is inconclusive, say so rather than asserting equivalence or superiority.

Use the existing independent completeness and support phases on the composed report. There is no additional mandatory Discovery approval cycle. Independently supported blocks may be released partially; failed required review cannot yield complete acceptance.

## 8. Existing harness integration and compatibility

Implement sequentially in the existing harness. For a trusted `team_review` operation, enumerate sources and run the required proactive/account assessment before ordinary model planning can omit it. Keep ad-hoc operations selective. No new orchestrator, scheduler or runtime parallelism.

| Integration area | Required implementation checks |
| --- | --- |
| `import_data.py`, new package profile | Exact schema, dependency order, types, FKs, event/knowledge dates and isolated output database; preserve eleven-table import behavior. |
| `agents/data_access.py`, `agents/tools.py` | Review-context projection, deterministic union/exclusions, partner field restrictions and raw metric observations for both producer and reviewer. |
| Proposed `agents/discovery.py`, rubric | Reuse `Specialist`; structured lineage, evidence states, account coverage, proactive results and reviewed merge reasons. |
| `agents/original.py` | Role construction, pre-planning review hook, explicit dispatch and correction ownership. Extend delegation sets and the tool-to-role map; it currently assumes only `ask_cherry` and `ask_vanilla`. |
| `connections.json`, `agents/connections.py`, `agents/__init__.py`, `agents/runtime.py` | Sixth-role/profile registration and shared accounting; preserve private configuration and explicit overrides. |
| `agents/zero_sugar.py` | Extend `OWNERS`, source access and task-spec checks. Its `run()` already reconstructs sources when given a database. Reuse that capability, but wire it into the actual Original review path, which currently constructs the reviewer without `database` and calls review directly; passing an argument alone does not make `run()` execute. |
| `agents/grounding.py`, `content.py`, `findings.py`, `validation.py`, `policies.py` | Extend producer/owner assumptions, citation/source kinds, numeric lineage, repair and release semantics with versioned contracts. Preserve independent judgment and old replay. |
| `run_agent.py`, `check_release.py`, `agents/resume.py` | Operation/database/context transport, owner assumptions and artifact checking. Do not restore Original workflow checkpoint resumption. |
| `agents/capture.py`, `agents/execution_log.py` | Bind task/context/source/schema/metric/rubric/model/budget identities and coverage to new captures without exposing credentials or raw private payloads in manager exports. |
| UI backend `app.py`, `offline.py`; frontend `api.ts`, `agents.ts`, `events.ts`, `AgentStage.tsx` | Minimal review start and report/status projection; sixth-role/event types and matching offline fixtures. Locate actual paths and assumptions in the current checkout before editing. No action-approval queue. |
| Discovery evaluation modules and existing tests | Separate casebook/scoring from sentiment gold; extend current active data, workflow, review, capture and compatibility checks. Do not revive archived old-protocol tests. |

Budget plan: retain current configured limits unless separately approved. Before live calls, produce a coverage/batch estimate with total model/tool calls, retries, input/output limits, wall time and reserved synthesis/review capacity. Freeze both comparison arms' limits. If the declared population cannot fit, reduce source presentation or revise the explicit design before evaluation. Never truncate silently or increase limits automatically.

No reviewed-result cache or durable same-key startup deduplication in v4. Explicit runs have unique artifact IDs and require an intentional start; refresh must not automatically relaunch analysis. Preserve existing process cancellation/cleanup and mark abandoned runs interrupted/failed rather than perpetually running. New runs start fresh; saved reports remain historical artifacts, not automatically reusable current results.

## 9. States and visible output

| Dimension | Allowed transition and actor | Terminal meaning |
| --- | --- | --- |
| Analysis operation | Runtime: `created -> running -> complete / partial / failed / interrupted` | `complete` requires declared coverage and both reviews; partial retains supported output; retry is a new run ID. |
| Account assessment | Runtime enumerates `eligible -> assessed`; reviewer accepts release or withholds claims | Assessed does not mean every employee claim is true. Eligibility exclusions stay in the restricted reconciliation. |
| Claim evidence | Discovery proposes supported/unresolved/conflicting; ZeroSugar independently reviews | Store reviewed claim state with source lineage; withhold unsupported assertions. |
| Recognition state | Derived from known source events and their coverage as of cutoff | `recognized`, `shared_without_recorded_recognition`, `not_shared`, or `unknown`; conflict is explicitly reported. |
| Draft response | Original prepares; ZeroSugar reviews; runtime exports or withholds | `prepared_reviewed` or `withheld`; no delivered, approved or closed human-action state exists in v4. |

Store operation creation/start/end timestamps, assessment/review times, source event/recorded dates, and the fixed knowledge cutoff separately. A new source snapshot creates a new analytical run. `closed` is intentionally not available: there is no implemented human-action workflow to close.

The manager report contains: review scope/cutoff and mode; source coverage; supported work/benefit findings; uncertainties; recognition context; and one draft response per eligible account with rationale, responsible manager and proposed next step. A response owner is proposed responsibility, not evidence that the person accepted an assignment. Show partial or withheld sections honestly.

## 10. Evaluation and implementation gates

Create a private `GOLD_DISCOVERY_v1` casebook covering section 5 with acceptable alternate interpretations, required sources, prohibited claims and human adjudication fields. Build dedicated Discovery case generation/scoring modules. Reuse capture, runner and adjudication conventions; do not modify the frozen M1-M4 sentiment gold or describe its scorer as a generic plug-in evaluator.

Offline checks precede live evaluation: profile/schema/types/FKs/counts; roster and cutoff; report-only work; proactive positive/negative entry; source-chain independence; overlapping origins; scope exclusions before model access; partner privacy; recognition coverage; raw arithmetic; task completeness; both review phases; budgets and interrupted runs; old artifact replay; UI mode/type projections.

Proposed live design: **four complete cohort-review workflows total**, all on one frozen pack, task, model/deployment and comparable limits: two runs with amended current specialists, two with a separate Discovery specialist. Each workflow covers the same scenario pack; this is not two runs per scenario. Baseline roles get the same evidence, task and required proactive activation, so the contrast tests the role division rather than data or activation differences.

Use the institution-provided GW API profile for the proposed demonstration, subject to deployment access and verification of course requirements from the current syllabus before scheduling. Current context records local `gpt-5.4` selection; it is not a frozen Discovery evaluation choice. No API success, token sufficiency or provider requirement is established merely by this plan. Freeze actual provider/model/settings before calls. No general-purpose-product comparison in v4.

Human adjudicators should be blind to arm where feasible; record supported alternatives and disagreements. Report raw per-case results, false/missed findings, eligible-account coverage, source/calculation fidelity, useful draft responses, protocol failures, tokens, calls and latency. Four runs demonstrate behavior on this pack; they do not establish a statistically reliable quality ranking.

| Gate | Deliverable and stop condition |
| --- | --- |
| G0: design | Scope, schema/metric definitions, task/rubric, privacy and authorization register settled. Do not generate data against unresolved source grains. |
| G1: source pack | Separate reproducible database and exact manifest; worksheet/gold private; raw observations and source chains reconciled. |
| G2: offline capability | Both arms complete required dispatch/source/review contracts offline; legacy compatibility checks pass. No live claim from offline results. |
| G3: live demonstration | Four explicitly authorized workflows; report each actual result without automatic replacement of failures. |
| G4: handoff | Minimal manager report, citations, draft responses, limitations and concise comparison; no superiority claim beyond evidence. |

Planning targets, not commitments: scope approval November 18; validated source pack November 24; demo candidate December 1; December 2-8 for correction/presentation contingency. The auditor names December 10 as the final date; confirm against the course schedule before relying on it. If time contracts, defer charts and UI polish before removing source support, proactive positive discovery or independent review.

## 11. Authorization register

| Action | Status after creating v4 |
| --- | --- |
| Write v4 and update its current-document pointers | Authorized by the request to create version 4. |
| Add sixth runtime role, schemas/data, importer and UI changes | Proposed; creating the plan is not implementation approval. |
| Run appropriate offline checks during an approved implementation | Specify with that implementation scope; no checks were run merely by writing this document. |
| Change workflow budgets or private model/provider settings | Not authorized here; freeze proposed values and obtain approval if changes are needed. |
| Four GW workflows | Proposed total; require explicit authorization before execution. No automatic repeats or failed-run replacement. |
| Git publication, deployment, external messages, real employee-data use | Not authorized by this plan. |
| Thirty-day raw-capture deletion policy | Proposed policy only; no deletion or automation authorized. |

Existing task-specific authorizations retain their original scope. There is no universal rule limiting every future task to two calls or two workflows. No additional confirmation is needed to finish the documentation work already requested.

## 12. Changes from v3 and auditor disposition

| Topic | v4 decision |
| --- | --- |
| Scope/calendar burden | One cohort, one partner, initial cutoff only. Full action lifecycle, reusable results, durable duplicate starts and general-purpose comparison deferred. |
| Existing extension | Reuse relevant 2026 goals and utilities; preserve 2025 self-reviews, M14 case and QA key; construct period-correct intake separately. |
| Import and scope compatibility | Isolated package/database, explicit numeric types and separate versioned review context; preserve `AccessScope` and legacy profile. |
| Missing proactive proof | S5-P is a positive no-account case and an explicit acceptance-matrix row; N6 remains the negative control. |
| Feedback and corroboration | Anchor reported work without contribution and support real author types; judge independent source chains, not manager count alone. |
| Timeline leakage | Do not pre-seed generated dispositions for all accounts. Include only genuine pre-cutoff acknowledgments/recognition; draft responses are outputs. No arbitrary 50/60-event quota. |
| Metric support | Raw samples for medians, explicit definitions and typed observations; distinguish descriptive changes from reliable or causal improvement. |
| Anonymous linkage | Remove S11 from this demo; five responses or ten invitees alone do not establish anonymity. |
| Evaluation cost | Dedicated Discovery evaluator and four whole-pack workflows total, not scenario-by-arm multiplication. |
| Lost v2 detail | Restore task spec, relevance rubric, interrupted-run handling and the decision to prefer existing roles when a separate role adds no supported benefit. |
| Vocabulary and states | Explicit glossary, transitions, timestamps and no simulated approval/closure presented as real. |

## 13. Glossary and verification limits

| Term | Meaning |
| --- | --- |
| Employee account / work report | A person's submitted account of work and requested response; source evidence, not a confirmed verdict. |
| Analytical report | Echo's reviewed output for the cohort operation; distinct from an employee account. |
| Work case | A derived grouping of related source records, retaining all account origins and contributors. |
| Collection contract | Versioned source rules for grain, provenance, coverage, dates, authors, known missingness and interpretation boundaries. |
| Partner allowlist | Explicit work/process/team identifiers and fields permitted in the partner evidence projection. |
| Bounded execution | Fixed declared population and call/tool/token/time/retry limits, with explicit incomplete coverage on exhaustion. |
| Independent confirmation | A separately originating source with relevant direct knowledge; copied or relayed versions of one account do not create additional independent confirmation. |
| Worksheet | Private scenario-to-source construction and reconciliation table defined in section 4.1. |

Evidence for this revision: current v3 and seven-review documents; relevant v2/review sections; `data_extensions/README.md` and CSV headers; importer/type rules; feedback dictionary; scoped survey release; reviewer/source reconstruction, artifact scope equality and Original delegation/reviewer wiring; and the current sentiment gold modules. The graph was used for source navigation and can contain stale line locations; current files govern.

Only plan documentation and current-document pointers were changed. No runtime implementation, source generation, database mutation, test/build execution, live provider call or publication was performed. Source counts beyond the documented extension and inspected database table inventory are construction targets, not verified generated results.
