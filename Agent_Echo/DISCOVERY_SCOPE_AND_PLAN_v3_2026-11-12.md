# Echo Discovery v3: unrecognized-work review, impact and response

Date: 2026-11-12. Status: proposed scope and implementation plan only.

This supersedes the design recommendations in [v2](DISCOVERY_PLAN_v2_2026-11-11.md), preserving it as history. [Seven role-specific reviews](DISCOVERY_SEVEN_REVIEWS_2026-11-12.md) informed this redesign. All used GPT-6 Luna with medium reasoning. No implementation, source generation or application evaluation occurred.

## 1. Exact scope and intended value

**Investigate work that employees indicate is unrecognized, explain its supported benefit to their own or another team, and provide a traceable manager response and follow-up.** Also proactively identify relevant work without requiring an employee to report it or a manager to know what to ask.

Every eligible employee indication receives an assessed disposition, including routine work, work within formal goals, work without an accepted contribution record and work already recognized. Discovery does not require exceptional innovation, cross-team activity, negative sentiment or missing KPI coverage to investigate a concern.

The product delivers an evidence-backed account of work and impact, an actionable recognition/credit/coordination decision for the manager, and an acknowledgment/status extract the manager can give the employee. It does not promise increased engagement, retention or revenue as a measured result of this demonstration.

### What v2 actually covered

V2's population was accepted `OP_contributions` in a manager/date scope. It proposed formal goals, automatic discovery and reusable reports. It did not sufficiently specify employee-reported work without that row, source completion/impact histories, new record quantities, a fixed pilot roster/calendar or accountable response to the person. The limitation was in the selected design, not a user constraint.

### In and out

| Included in this proposed pilot | Outside this pilot |
| --- | --- |
| Named employee reports collected before analysis; reports without an accepted contribution. | Building enterprise collection connectors or a new employee login/portal. |
| Proactive review of authorized contributions and task-delivery evidence, including home-team work. | Detecting work absent from every available source or identifying anonymous survey authors. |
| Completion, acceptance, milestones, problems resolved, goal progress and comparable process observations. | Individual productivity scores, promotion/pay decisions or automatic causal/financial valuations. |
| Named beneficiary confirmation and team-level anonymous leads. | Unrestricted access to partner rosters or their personnel data. |
| Proposed manager response, an explicit locally approved disposition and separately recorded follow-up. | Automatic email/calendar/HR-system writeback or treating a draft as delivered. |
| CLI/UI report, safe evidence, current status, reuse and a follow-up snapshot. | A broad new dashboard suite or parallel-agent/scheduler redesign. |

Correct prior collection is an explicit scenario assumption. We will construct strong, coherent records rather than rely on the current generic narratives or fill gaps with model knowledge. The requirement is sufficient evidence, not a predetermined table count.

## 2. Finite pilot population and calendar

Proposed pilot roster, selected from existing employee records employed throughout the complete calendar below:

| Home-manager review | Team | Six employee IDs |
| --- | --- | --- |
| M32 | Sales Operations | E0002, E0010, E0032, E0058, E0107, E0162 |
| M03 | Escalation Services | E0125, E0140, E0226, E0257, E0349, E0426 |
| M06 | Accounting Operations | E0015, E0020, E0089, E0093, E0214, E0246 |

Two additional beneficiary contexts: Infrastructure (manager M16) and Enterprise Accounts (manager M29). They provide relevant team goals, process observations and named confirmations, not an authorization to scan those employee rosters. Thus the pack has **18 focal employees, three home review cohorts, five relevant teams and five manager contexts**. Each manager operation assesses only its own six-person pilot cohort. Results must not be presented as a complete analysis of every employee in the existing organization or team.

| Window | Exact dates | Purpose |
| --- | --- | --- |
| Baseline: 12 weeks | 2026-01-05 to 2026-03-29 | Comparable pre-work process observations and prior recognition context. |
| Work/review: 12 weeks | 2026-03-30 to 2026-06-21 | Eligible work, employee indications and task events. |
| Initial knowledge cutoff | 2026-06-21 | First analytical review and recognition state. |
| Follow-up: 8 weeks | 2026-06-22 to 2026-08-16 | Recorded manager responses, recognition/credit and subsequent observations. |
| Follow-up knowledge cutoff | 2026-08-16 | A new reviewed version of the same work cohort with later evidence. |

All dates fit the legacy global data horizon, but work eligibility, authorized evidence windows and knowledge cutoff are distinct. The current single-date-filter projection must be extended: baseline/follow-up sources are available only through trusted review context, not by letting a model widen scope. Before/after measures must use their explicitly comparable windows; a 12-week rate and 8-week count cannot be compared as if identical.

Roster IDs and dates are proposed scope decisions, not generated new data. Revalidate roster/source identity when implementing; any change produces a documented new pack version.

Initial reports must concern work overlapping the work window and be submitted/recorded by June 21. A report about that same work first recorded during follow-up enters the August 16 version, never the earlier result. Preserve its original work dates and later submission/knowledge dates. Show changed eligible-report counts between versions instead of implying the first review missed a source it could not yet know.

## 3. Required evidence and concrete data-construction work

Current `files_update/QA_manifest.csv` declares 77,333 contributions, 159,779 work requests and 42,542 feedback records across the wider pack. These counts do not demonstrate the needed case evidence. Existing feedback is quarterly/capped, and task requests chiefly expose final/current snapshots. Preserve that legacy pack and its meaning.

Create a separate proposed `files_discovery_v1/` pack, with its own exact manifest, dictionary, collection contract, coverage declarations and reproducible database artifact. New rows are required, not optional cosmetic additions.

### 3.1 Initial record-construction targets

| Source or output family | Proposed target | Construction requirement |
| --- | --- | --- |
| Employee/manager roster | 18 focal employee rows; 5 manager rows | Fixed pilot and named beneficiary scope above. |
| Projects/work requests | 8 projects; 30 requests | Realistic home/cross-team needs, deliverables, original/revised commitments and self-initiated capture where applicable. |
| Accepted contributions | 24 | Summaries and accepted-work evidence; a report can exist without one. |
| Named employee work reports | At least 19 | One report per focal employee plus at least one additional indication for the duplicate/merge test. |
| Employee-supplied work references | About 30 links | Reports may cite zero, one or several tasks/deliveries; preserve which references the employee supplied. |
| Goal versions/assignments | 24 | 18 individual goals, five team goals and one documented revision; include complete applicable plan coverage. |
| Task/delivery/acceptance/history events | About 90 | Explicit completion and acceptance, milestones, relevant changes, reopening/rework and one unfinished control. |
| Named operational feedback | At least 40 | Specific home/partner corroboration, complementary details and independent sources; not repeated template praise. |
| Outcome observations | At least 30 | Defined metric, value/unit, observation window, population/denominator where applicable, method, source and knowledge date. |
| Sharing/recognition/response history | At least 50 events | Include acknowledgment and disposition for the 19 reports, plus relevant baseline/follow-up sharing, recognition, credit and check-back events. Do not invent recognition grants to fill a quota. |
| Anonymous team context | One eligible survey group: six comments and matching summary | No employee identity link; group meets existing release thresholds. |
| Manager dispositions/follow-up | One assessed response per named report; events for actions due by follow-up | Some may remain openly pending. Proposed action, approved intent and completed delivery are separate. |

These are generation targets and scenario minima, not existing records or hard caps. The final manifest records exact actual quantities. If coherent scenarios require more rows or another relation, add them and document why; never remove needed evidence to preserve these targets.

### 3.2 Recommended schema, derived from source grains

Six new source relations are recommended for this finite scope. This is not a limit. Reuse existing entities and do not create duplicate masters merely to increase the table count.

| Relation | Grain, core fields and justification |
| --- | --- |
| **New `OP_employee_work_reports`** | One named employee indication: `Report_ID`, employee FK, submitted/recorded dates, work-period bounds, narrative, claimed beneficiary/need, requested response and origin. Contribution/request FKs are not required for entry. A report states the person's account, not an independently confirmed verdict. |
| **New `OP_work_report_links`** | One employee-supplied/operational source reference: `Link_ID`, `Report_ID`, exactly one request/contribution/work-event target, link origin and recorded date. Supports several tasks per report and several reports about the same work without comma-separated ID fields. Discovery-derived matches remain in the analytical artifact. |
| **New `OP_goals`** | One formal goal assignment/version: owner type, employee FK or canonical team, effective period, text/success criterion, optional metric/target/unit, recorded date and superseded goal. Goal-aligned work remains eligible for recognition. |
| **New `OP_work_events`** | One dated work event: `Event_ID`, request and/or report anchor, actor, event/recorded dates, event type, deliverable key/description, acceptance criterion, source text/reference and origin. Represents delivery, acceptance/rejection, completion, milestone, reopening or changed commitment. It covers the chosen deliverable history without a separate artifact master. |
| **New `OP_outcome_observations`** | One observed team/process/goal measure: ID, metric code, team, relevant goal/project FK, period, value, unit, numerator/denominator where applicable, method/source, recorded date and completeness. Metric definitions/comparison rules are supplied by the approved collection contract. No model-created impact label. |
| **New `HR_work_review_events`** | One recorded sharing, acknowledgment, recognition, credit, manager disposition or follow-up event: ID, typed action, target report/work/contribution, actor, recipient, event/recorded dates, channel, status, source/reference and origin. Dates and event type distinguish being seen, being recognized and an action occurring. |

**Enrich/reuse:** `OP_projects`, `OP_work_requests`, `OP_contributions`, `OP_priority_decisions` and `HR_recognition_feedback`. Add report/work-event anchors to operational feedback when needed so a beneficiary can confirm reported work before an accepted contribution exists. A new-profile feedback row must have a valid work/report anchor and a named source. Current manager-author fields can support the planned confirmations; add peer-author fields only if selected cases actually use employee-authored feedback.

The new profile uses event-grain feedback without the legacy quarterly cap. Do not duplicate messages into a second generic beneficiary-feedback table. `HR_work_review_events` is the new profile's authoritative state-event source; a feedback message can be linked to a recognition event but must not count as a second recognition grant. Preserve legacy `Manager recognition` semantics under the legacy profile.

Recalculate pilot manager roster counts and coverage for the selected cohort; do not carry the wider source team's employee totals into a six-person pilot report. Retained non-core application tables must have explicit profile-defined rows, headers and manifest counts, including valid zero-row tables when unused. Anonymous survey groups must have consistent invitation/response/comment counts and satisfy current release thresholds.

Ordinary factual relationships are legitimate input: employee to report, report to cited task, task to delivery, measurement to its goal/process, feedback to the work discussed. What stays private is the expected analytical verdict, intended exceptional-value flag and hidden evaluation answer. Discovery still has to reconcile sources and explain their meaning; it need not rediscover every foreign key.

## 4. Scenario construction and expected useful decisions

The eleven main scenario families below cover the required behaviors. Their private reference defines accepted interpretations, required sources and prohibited inferences. They share the finite pack; rows can support several related cases without being counted twice in totals.

| Case | Required records to construct | Useful result |
| --- | --- | --- |
| S1 — Routine home-team work, unrecognized | Employee report; three completed/accepted tasks; applicable formal goal; two specific home-team confirmations; comparable quality/on-time observations. | Give routine supported work credit even though it is assigned work. Provide a cited acknowledgment/recognition proposal. |
| S2 — Cross-team help not shared | Report, accepted work and partner milestone; beneficiary goal; two confirmations; explicit not-shared state in complete workflow. | Explain which team benefited and route the evidence to the home manager. |
| S3 — Shared but not recognized | Strong work/outcome evidence; dated sharing to correct manager; no recognition event by initial cutoff. | Recognition follow-up, distinct from a visibility action. |
| S4 — Report without canonical contribution | Named report; no `OP_contributions` row; at least two delivery/acceptance events and two independent confirmations, with relevant result observations. | Investigate and substantiate work without requiring the missing row. Recommend recording credit; do not pretend the row already existed. |
| S5 — Employee-initiated improvement | Several related tasks/contributions; at least three complementary named feedback records; full formal plan; baseline/follow-up measurements. | Explain the initiative and supported team benefit, then propose recognition, sponsorship or a broader trial. |
| S6 — Mentoring/coordination/handoff | Accepted handoff/checklist events; named recipient lead confirmation; readiness or onboarding milestone observation. | Recognize enabling work using observed qualitative/checklist evidence, without inventing monetary value. |
| S7 — Work already recognized | Report expressing a concern; strong work evidence; earlier dated recognition/credit source. | Show what recognition is recorded, acknowledge the concern and propose clarification if needed. Do not duplicate credit or dismiss the person's perspective. |
| S8 — Overlapping indications/shared work | Two indications and a proactive contribution refer to related work; named sources identify each collaborator's role. | Merge analysis while retaining every report and contributor; no duplicate hours, credit or disappearance of a person's concern. |
| S9 — Proactive routine control | Successful routine work, complete goals and existing acknowledgment; no employee report for this extra work item. | Accurately describe value when relevant without manufacturing an exceptional opportunity or recognition gap. |
| S10 — Effort reported, delivery unfinished | Named report, blocker/current work events and positive feedback, but no accepted-delivery event. | Acknowledge effort, show the actual state and propose help/unblocking. Do not claim completed output or achieved impact. |
| S11 — Anonymous team indication | Six release-eligible comments and team-level operational/process context; no identity mapping. | Surface a team-level lead and a team follow-up. Never identify an individual for recognition from the survey. |

For each positive case, the construction worksheet records an employee indication (when applicable), work evidence, acceptance/beneficiary confirmation, relevant goal/result, recognition history and an owner/response path. Add background records with realistic language and overlapping topics. Do not insert a conspicuous expected-answer sentence or select evidence by evaluation IDs.

The private construction worksheet must map every scenario and every named report to actual source IDs, focal employee(s), applicable goals, source/event/knowledge windows, confirmation authors and provenance, measurements, expected response and receipt events. Reconcile its distinct rows to the final manifest and note shared evidence explicitly. The same original account copied into two messages is one confirmation source, not independent corroboration. Scenario identifiers and expected analytical judgments stay outside the runtime pack.

### Illustrative measurements to generate

These are proposed scenario values, not current results:

- **Process time:** median approval time 8 to 5 business days, with 40 and 44 observed cases, consistent timing definition and dated implementation evidence.
- **Reliability:** repeated issues 6/100 versus 2/105 comparable transactions; preserve count and exposure, not counts alone.
- **Goal progress:** 194/200 required records meet a criterion against a 95% target; source observations and accepted remediation tasks support the explanation.
- **Milestone:** a dependency accepted on May 20 against an agreed May 31 commitment, with the receiving release checklist and contributors' roles.
- **Enabling work:** 4/4 receiving colleagues complete a defined handoff checklist; do not translate that into a productivity ranking.

Select compatible windows inside the pilot calendar for each case. Cherry calculates rates/deltas/attainment from these sources. Discovery distinguishes delivered, accepted, milestone achieved and beneficiary result. A case may explicitly record an attributed mechanism; otherwise state documented contribution and observed change separately. Synthetic origin is not a reason to reject a correctly specified scenario.

These retrospective team observations describe the employee's work and its documented context. They are not evidence that Echo or Discovery caused the improvement. Evaluate the system's response/understanding benefits separately; do not infer a causal effect of the software from these seeded before/after values.

## 5. Claims, work cases and response lifecycle

The candidate manifest is a union of named reports, eligible operational contributions, relevant delivery/work events and a separate team-level anonymous-lead channel. No accepted-contribution, cross-team, negative-sentiment, exceptional-value or outside-KPI filter may hide an employee report.

Deterministic inclusion rules for this pilot:

- **Reports:** employee belongs to the trusted cohort; claimed work overlaps the work window; submission/recorded date is no later than cutoff. Every such report enters, regardless of matching status.
- **Contributions:** employee belongs to the cohort; accepted-work date falls in the work window; source is known by cutoff.
- **Operational work:** a cohort-owned request has a recorded completion in the work window, or a cohort-attributed event of type `delivered`, `accepted`, `completed` or `milestone_accepted` occurs in that window and is known by cutoff. These can create a lead without a contribution/report. Reopening/blocker/assignment/plan-change events enrich related work; they do not each create another case.
- **Anonymous context:** a release-eligible home-team survey group dated within the work window and known by cutoff can create a team-level lead. Count groups and source comments separately; do not create an attributed employee case from it.

If several entry records explicitly reference the same work, retain each origin but create one initial work-case anchor. Otherwise keep separate leads until a reviewed merge is supported. Manifest checks reconcile included/excluded IDs, rule and reason against source counts. Goals, measurements and unrelated feedback enrich authorized cases rather than expanding the employee population.

Derive a work case with explicit source lineage. Known source references support deterministic deduplication; semantic merges require a reason and remain reviewable. One case may explain several reports, and a report may reference several tasks. Keep every original report visible in coverage and response tracking. Preserve multiple contributors without inventing credit percentages.

Track three independent dimensions:

1. **Evidence/analysis:** unassessed; assessed with supported, unresolved or conflicting claims; reviewed/released or withheld. Assessing a report is not accepting its every claim.
2. **Recorded visibility/recognition:** not shared, shared without recorded recognition, recognized or unknown, as of the controlled cutoff.
3. **Human response/action:** awaiting response, proposed, manager-approved, recorded as delivered/completed, deferred or still open.

A report can finish analysis while a manager follow-up remains open. A complete analytical operation requires all declared eligible items assessed and required review completed; it does not require all humans to have completed their actions. Closure requires the appropriate response and dated completion/acknowledgment evidence. A model proposal or manager approval of intent alone cannot establish delivery.

For each employee indication, show its assessed disposition, owner, rationale, proposed next action and check-back date. Suggested pilot service targets are acknowledgment within three calendar days and a disposition or explicit update within seven; these are scenario process assumptions to evaluate, not measured organizational promises.

Prepare an employee-ready status/response artifact for every named report. Track `prepared`, `handed_to_manager` and `recorded_delivered_to_employee` separately. Only a dated delivery/receipt record can establish that an acknowledgment reached the employee. When that record is absent, report manager readiness or an open response, not completed employee acknowledgment. The follow-up worksheet must specify which receipts are present and which cases intentionally remain open.

## 6. What each agent does

| Role | Responsibility in this scope |
| --- | --- |
| Discovery, proposed specialist | Reconcile reported and proactive leads, assemble work cases, compare plans, relate supported work/beneficiary/results and explain recognition relevance. Every report receives an assessment; proactive findings can be prioritized separately. |
| Cherry | Compute completion/on-time/acceptance/rework measures, goal progress, process observations and timing/recognition statistics with correct grain, units and denominators. |
| Vanilla | Interpret text/sentiment when needed; sentiment is neither proof of a contribution nor the admission gate. |
| Original | Coordinate additional analysis, preserve each person's concern, synthesize supported findings and propose proportionate manager responses/actions. |
| Lime | Present supported Cherry metrics when a chart is useful. |
| ZeroSugar | Independently assess visible completeness and underlying source support, including attribution, numeric claims, recognition state and proposed-versus-performed action. |

Keep the separate Discovery role as the proposed design, but compare it with amended existing specialists on the same source pack and task. Agent count is not a benefit by itself.

## 7. Existing harness: concrete extension

Reuse the existing harness rather than adding a competing orchestrator. Verified baseline: `OriginalAgent.run()` resets transient work, creates the shared budget and capture, and rejects workflow resumption. `workflow()` currently starts with question-led planning. The reviewer can obtain its sources from Cherry/Vanilla child instances, which is insufficient for a Discovery-only report.

| Files/seam | Proposed work |
| --- | --- |
| [import_data.py](import_data.py), versioned manifest/dictionary | Exact new source profile, full approved schema, FK/type/time validation and consistent database selection. Create approved schemas and load in validated dependency order, including self-referenced goal revisions. |
| [data_access.py](agents/data_access.py), [tools.py](agents/tools.py) | Trusted cohort/work/evidence/cutoff scope; deterministic union manifest; report/work-case context; goal/outcome/event projections. Same authorized context for producer and reviewer. |
| Proposed `agents/discovery.py` and rubric | Typed candidates with origins, work/beneficiary/result claims, source references, evidence states, response needs and coverage. Reuse existing `Specialist`. |
| [original.py](agents/original.py): `run`, `workflow` | Add trusted operation/task context. For `team_review`, execute the Discovery hook before model planning. A named `investigate_report` task can target one indication. Neither requires the model to predict an unknown contribution. |
| `original.py`: construction/delegation/repair | Explicit new role/task handling, source handoff and owner-directed corrections; do not treat every non-Cherry role as Vanilla. |
| [runtime.py](agents/runtime.py), [connections.py](agents/connections.py), [run_agent.py](run_agent.py), [__init__.py](agents/__init__.py) | Role registry, operation/cohort/cutoff/database arguments, result metadata and shared accounting. Preserve unrelated private-profile work. |
| [policies.py](agents/policies.py) | Add role ownership/decline language; require each named report to be accounted for, routine work eligibility, source authority and proposed/performed action distinction. Keep origin-neutral analysis. |
| [zero_sugar.py](agents/zero_sugar.py), Original reviewer construction | Independent scoped source reconstruction without requiring Vanilla or Cherry to have run; extend correction owners and validate all new source references. |
| [grounding.py](agents/grounding.py), [content.py](agents/content.py), [findings.py](agents/findings.py), [validation.py](agents/validation.py) | Cited task/event/goal/observation interpretations, correct numerical provenance and reviewed report identities. Model relevance is a judgment, not a deterministic fact. Version changed contracts and preserve old replay. |
| [capture.py](agents/capture.py), [execution_log.py](agents/execution_log.py), [resume.py](agents/resume.py) | Capture operation, cohort, source window/cutoff, population, metrics/rubric, merged lineage and budgets. Reuse released artifacts; do not restore unsupported Original workflow resume. |
| Report storage and local action ledger | Strict report-key validation and atomic writes. Separate manager-approved actions from analyst source data and independently record completion evidence. |
| [app.py](../Echo_UI/backend/app.py), [offline.py](../Echo_UI/backend/offline.py), [api.ts](../Echo_UI/frontend/src/lib/api.ts), manager views | Review/report operations, durable duplicate-start prevention, safe evidence/response queue, scope/coverage/freshness, status extract/draft and follow-up version. Preserve demo/replay/live labels. |

Initial flow: trusted review start → complete source manifest → bounded Discovery/Cherry evidence work as needed → Original composition → existing ZeroSugar completeness/support review → supported release and response queue. There is one composed-report approval path, not a duplicate mandatory Discovery approval cycle. Failed required work prevents a complete report; independently supported blocks may still be partial.

The first version is sequential. Baseline budgets are existing configuration, not validated capacity for this new pilot. Replace v2's arbitrary three-call Discovery ceiling with a documented coverage-based batch plan and explicit accounting/reserved capacity for synthesis and both reviews. Before semantic runs, freeze total/phase limits using source sizes and offline dispatch checks, then measure actual provider behavior. No silent budget increase, unbounded retries or completeness claim after partial processing.

## 8. Access, persistence and action boundary

Trusted scope includes pilot cohort, home manager, work period, authorized baseline/follow-up windows and knowledge cutoff. A model cannot enlarge any of them. Partner goals, measurements and confirmations are projected only for the relevant work/process/team under an allowlist; partner employee goals/rosters remain excluded. Retain anonymity and survey thresholds.

Employee reports are already collected in this case. Do not require a new portal or actual enterprise integration to demonstrate intake. Add a manager-facing response queue and employee-facing draft/status export. The application may store an explicit manager-approved disposition in a separate local append-only ledger, with actor, report/case, action, status, owner/date and source/report identity. Agents cannot approve their own suggestions. Local approval is not an external message, HR-system change or completed recognition event.

The follow-up source snapshot can supply recorded delivery/recognition/results under the controlled scenario; alternatively a manager explicitly records a completed local action with provenance. Mark simulation/offline mode and actual action state accurately. No sent-message claim without a recorded delivery event.

The approved source snapshot and local ledger use the same typed event semantics but retain distinct origins/IDs. Merge them for current status only under the authorized projection, deduplicate references to the same real action and bind the ledger snapshot into report identity. Model proposals cannot be appended as completed source events.

Reuse a released report only when task, cohort/authorization, work/evidence windows, cutoff, source/profile/schema, applicable action-ledger snapshot, rubric/metric definitions, relevant code and model configuration match. Partial reports stay partial; stale reports are historical, not current context. Reopening a valid report adds no model calls. Changed evidence or approved actions yields a new version; deepening keeps parent lineage. New ad-hoc wording still goes through ordinary answer review.

Deduplicate same-key starts durably at the API/subprocess boundary. Keep analysis status, recognition status and human follow-up status separate in storage and display.

## 9. Requirements-to-evidence acceptance matrix

| Promise | Required source/records | Analysis | Visible artifact and acceptance |
| --- | --- | --- | --- |
| Hear employees' indications | Every scoped named report, including no contribution and duplicate origins | Enumerate, reconcile, preserve concern and scope | Response queue accounts for every report; none disappear behind a value score. |
| Show home-team benefit | Delivery/acceptance, named home-team confirmation, applicable plan/result | Supported contribution and quantitative/qualitative benefit | S1 routine assigned work is represented fairly and has a useful response. |
| Show partner-team benefit | Beneficiary team, work/milestone evidence, confirmations, relevant results | Trace who helped whom and what result is supported | S2/S4/S5 show correct goal/outcome links without exposing unrelated partner data. |
| Quantify only measured results | Compatible metric definitions, windows, unit, counts/denominators and source | Cherry calculations; Discovery attribution interpretation | Reproduce values and avoid multiplying hours or credit through joins. |
| Distinguish recognition states | Sharing, recognition and acknowledgment events with recipients/cutoff | Deterministic event state; independently reviewed explanation | S3 is not called recognized merely because feedback was shared; S7 gets no false duplicate-credit alert. |
| Support a response, not just a finding | Owner, disposition, proposed action, recorded approval/completion/check-back | Separate proposal, decision and delivery | Every named report has a response/status extract or explicitly open owner-tracked case. |
| Preserve anonymity | Team survey evidence without identity mappings | Team-level lead only | S11 never assigns the comments to an employee. |
| Report honest completion | Manifest, assessed sources and unassessed/truncated population | Coverage independent from human closure | Fully assessed analysis can be complete with open follow-ups; unassessed population cannot be called complete-empty. |

Fail the design review before implementation if any promise has no source grain, construction requirement, responsible analysis, visible outcome or check. Passing source/import checks does not establish semantic quality.

## 10. Evaluation and implementation sequence

Freeze a private `GOLD_DISCOVERY_v1` casebook with source references and expected/acceptable interpretations for S1-S11. Keep expected verdicts outside runtime tables/prompts and preserve existing M1-M4 gold. Reuse [gold_cases.py](gold_cases.py), [score_gold.py](score_gold.py) and runner conventions with a thin Discovery case family. Extend current [test_workflow_scenarios.py](tests/test_workflow_scenarios.py) and applicable data/role/release/capture tests; do not revive archived old-protocol tests.

Offline checks cover schema/FKs and exact counts; date/knowledge windows; cohort/partner access; all report origins and deduplication; accepted versus unfinished work; goal revisions; metric arithmetic/grain; sharing versus recognition; response state; required-phase/budget/review failures; source lookup without Vanilla; cache invalidation/idempotent starts; mode labels; and old replay.

Semantic evaluation separates data, role and workflow effects. Compare current analytical roles supplied with the stronger pack/task/rubric, a separate Discovery role on those same inputs, and the automatic review/reuse lifecycle. Include a prepared general-purpose workflow with equivalent permitted information and disclose actual model/product/access differences. Do not describe a generic API simulation as a measured ChatGPT product result.

Use two controlled repeats per scenario/configuration as a demonstration gate, with raw per-case reporting. Blind human adjudicators to configuration; permit supported alternate interpretations and record disagreements. Report evidence fidelity, missed/false findings, report-accounting coverage, useful recognition/response proposals, protocol failures, preparation effort and latency/call usage separately. A simulated follow-up can demonstrate correct tracking but is not evidence of real employee engagement improvement.

Required demo gates: no lost named report; S4 investigated without accepted contribution; supported routine benefit in S1; no false accepted outcome in S10; no false recognition state or identity exposure; correct measured results; and no claim that a proposed action happened. Follow-up closure is checked against dated source/manager evidence, separately from analytical completion.

| Phase | Deliverable |
| --- | --- |
| P0 — Scope and evidence | This finite cohort/calendar, scenario construction worksheet, source dictionary/profile, metric definitions and private expected outcomes. |
| P0 — Source construction | New and enriched records above, exact manifest, valid versioned import and consistent selected database. |
| P0 — Analytical capability | Shared scoped dossiers, union manifest/work cases, Discovery role and Cherry measures with explicit lineage. |
| P0 — Complete review path | Automatic/targeted operations, independent two-phase review, correction routing, partial release and report reuse. |
| P1 — Response and follow-up | Manager queue, explicit approval ledger, employee-facing draft/status extract, later-evidence report version. |
| P1 — Verification and presentation | Offline contracts, frozen semantic comparison, one home-team and one partner-team story with report-to-response trace. |

Update affected agent/workflow/source/testing guides, dataset documentation, both UI/CLI READMEs, context/map and role guidance when the implementation exists. Refresh the code graph after future code changes. This plan does not change runtime authorization, model profiles or current source artifacts.

## 11. Planning verification and limits

Seven role-specific analyses completed. The parent inspected current schema/projection/import conventions and manifest descriptions, verified the proposed dates (84/84/56 days), and checked that the chosen roster IDs are employed throughout those windows. It has not constructed the new records, validated their eventual counts, run the harness or tested Discovery. Current checkout was `ec4bc8a` with unrelated local work, preserved unchanged.

Only documentation was added/updated for this task. Table and record recommendations are scope-derived design decisions, not a claim that existing evidence already suffices. Any further source relation needed to meet the acceptance matrix must be designed rather than rejected to meet a table quota.
