# Echo Discovery v9 (final): proactive discovery of hidden cross-team work

> **Superseded by [v10](DISCOVERY_SCOPE_AND_PLAN_v10_2026-11-15.md)**, which folds Errata 1-6 into one document. Kept as history: §14 is the audit trail, and some of its rows describe values that later errata replaced.

Date: 2026-11-15. Status: **final proposed plan, frozen except for errata**; documentation only. Design review happens on the implementation (`/code-review`), not on this document. Implementation-level contracts found in the fifth audit are acceptance criteria in [the work breakdown](WORK_BREAKDOWN_DISCOVERY.md) (§12). **Errata 1 to 6** (sixth to eleventh audits, same day) fix contradictions and contract gaps without changing the design (section 14). No runtime code, data, database or provider call was changed or made.

This is the current Discovery plan. It supersedes [v8](DISCOVERY_SCOPE_AND_PLAN_v8_2026-11-15.md), [v7](DISCOVERY_SCOPE_AND_PLAN_v7_2026-11-15.md), [v6](DISCOVERY_SCOPE_AND_PLAN_v6_2026-11-15.md) and [v5](DISCOVERY_SCOPE_AND_PLAN_v5_2026-11-14.md). It records the user's decisions on the fifth audit and two further observations (section 12). Earlier history is kept in [v4](DISCOVERY_SCOPE_AND_PLAN_v4_2026-11-14.md), [v3](DISCOVERY_SCOPE_AND_PLAN_v3_2026-11-12.md), [the seven reviews](DISCOVERY_SEVEN_REVIEWS_2026-11-12.md), [v2](DISCOVERY_PLAN_v2_2026-11-11.md), [the review synthesis](DISCOVERY_REVIEW_SYNTHESIS_2026-11-11.md) and [the brainstorm](DISCOVERY_BRAINSTORM_AND_PLAN_2026-11-10.md).

The design in short:
- **Kept from v5:** a code prefilter, a model judgment, no correction loop, actions and follow-up.
- **Kept from v6:** Original's existing planning step identifies the subject, and code appends Discovery's results as a separate section that ZeroSugar does not review.
- **New in v7:**
  - Original receives nothing from Discovery. Code also writes the one-line pointer to the section, so ZeroSugar's input does not change.
  - Discovery is a small class of its own with one judgment call.
  - Its cost is refunded to the run budget, so Original keeps exactly today's budget.
- **New in v8:**
  - Discovery runs on **every** in-scope question. No planning flag can skip it.
  - Questions about another team, or comparing with one, are rejected. A partner team named only as the beneficiary of the manager's team's help is allowed.
  - A clarification choice is applied by employee ID.
  - The refund is recorded in separate fields, so the raw counters stay true.
  - Discovery gets its own timeout exception.
- **New in v9:**
  - A beneficiary team in the question governs who enters the pool and which evidence is read.
  - A name that does not resolve leads to a clarification, never to a dead run.
  - The workload and repetition baselines are computed inside the analysis window.
  - Follow-up runs only for actions the manager accepted or edited.
  - A failed M3 rerun has a written fallback.
  - The extra cost per question is an accepted decision.

## 1. Business case and responsibilities

The team's business case:

> Help managers identify and recognize the contributions their employees make to other teams, which usually fall outside the manager's visibility. Employees support projects, resolve dependencies and help other departments meet their goals, but the evidence is scattered across records and feedback, so the contributions may not be considered when evaluating and recognizing performance. Echo gathers and analyzes that information so the manager understands which work deserves attention and decides how to act. From the evidence it proposes concrete steps (recognize a specific contribution, request feedback from the benefited team, talk about workload) and prepares drafts, keeping the manager in charge of the decision and of personalizing the recognition. Hoped-for engagement and retention effects are not demonstrated by the prototype.

**Business baseline assumption.** The company already records the sources Discovery reads in its systems: cross-team feedback surveys, collaboration threads, blockers, incident handoffs, meeting notes, formal recognitions, 1:1s, review notes and a confidential individual pulse check. The prototype represents those systems with synthetic data that the team defines (section 5).

| Responsibility | Owner |
| --- | --- |
| Understand from the manager's free-text question whether it concerns the team, one person or a few people | **Original's planning step** (model), with code checking names against the manager's roster |
| Select only the relevant records and texts | **Discovery's code prefilter** |
| Read that compact evidence and judge which work is valuable, hidden and unrecognized, who did it, which team benefited and which actions fit | **Discovery** (model) |
| Build the "Discovery" section of the answer, with its one-line pointer, findings and action drafts from fixed templates | **Code**, from Discovery's checked result |
| Answer the rest of the question, as today and without Discovery's results | **Original** |
| Review Original's answer | **ZeroSugar** (unchanged role and input, `review-v8`). The Discovery section and its pointer are not reviewed (section 3.5) |
| Decide, edit or dismiss each action | **Manager** |
| Show later whether the action happened | Follow-up code over later source records |

One-line goal: **Discovery finds the valuable hidden work and proposes what to do; the manager decides; follow-up shows whether it happened.**

## 2. User decisions

From 2026-11-14:

1. Discovery performs the search itself.
2. Discovery uses a model, because recognizing unrecognized work in a comment or message requires reading and judgment. Code does not decide that.
3. Code selects only the most relevant evidence before the model reads anything. No model receives the whole dataset.
4. The manager writes the question as free text. There is no subject selector in the UI.
5. Discovery's output is not challenged with ZeroSugar correction loops the way Cherry and Vanilla outputs are today.
6. Actions and follow-up are core to Echo and are not deferred.
7. Reopening or replaying earlier live runs is not a requirement for Discovery.
8. The team generates whatever synthetic data the baseline needs.

From 2026-11-15:

9. Adding Discovery may change Echo's planning step, connections, tools and database as needed. No separate workflow is created.
10. The planning step identifies the subject; Discovery is called like the other agents, without a new workflow.
11. Discovery's results go in their own section at the end of the answer, which ZeroSugar does not evaluate.
12. At most 5 findings per answer.
13. People are described as "prioritized for review", never as a ranking.
14. (v7) Original does not receive Discovery's results; code writes the pointer and the section, so ZeroSugar has nothing Discovery-related to review.
15. (v7) Discovery's own calls and seconds are refunded to the run budget.
16. (v7) The as-of date is the `end_date` the UI and CLI already send.
17. (v7) After a clarification, the new run keeps the original question and adds the manager's choice.
18. (v8) Discovery runs on every question that is inside the manager's scope. Every Echo question is about the manager's own team.
19. (v8) A question about another team, or about a person from another team, is rejected, including comparisons with another team. A question that names another team only as the beneficiary of the manager's team's help ("Who on my team helped Customer Renewals?") is processed.
20. (v8) A clarification choice is applied by its employee ID, never by matching names.
21. (v9) When the question names a beneficiary team, finding the people who helped that team governs the selection (3.3).
22. (v9) Name matching ignores accents and case. A name that still does not resolve leads to a clarification. A run stops only for a name that resolves to a real team or person outside the manager's team.
23. (v9) "Normal" workload and repetition are measured inside the analysis window. Discovery does not read the history window.
24. (v9) If the M3 rerun fails its floors, first fix the planning instructions. If that is not enough, move subject identification back to a separate small call (as in v5) and leave `plan()` untouched.
25. (v9) The extra Discovery cost on every question, about 18-20k input tokens and 1-2 calls, is accepted. It is measured afterwards with `discovery_applied` and the per-run token counts.
26. (v9) Follow-up runs only for accepted or edited actions.

## 3. How Discovery works

### 3.1 Route

1. The manager types an open question in the existing UI or CLI, for example "How is my team doing this quarter?", "What should I know about Isabel?" or "Who should I recognize?" The question does not have to mention hidden or unrecognized work.
2. **Planning.** Original's existing `plan()` call ([original.py:162-265](agents/original.py)) gets four more fields in its structured output:
   - `subject_kind`: `team | person | people | other_team`;
   - `subject_names`: the people or team the question is **about**, including a team it compares against;
   - `period_hint`;
   - `focus_hint`: a topic such as "workload", or a partner team that the question names **only as the beneficiary** of the manager's team's help.

   The plan's key-set validation ([original.py:227](agents/original.py)) is updated to match.

   **There is no `needs_discovery` flag.** Discovery runs on every question that passes the subject check, so no planning output can skip it. Every Echo question is scoped to the manager's own team by `AccessScope`, so every in-scope question is a team or member question. A question that names nobody is a whole-team question.
The single order in `workflow()` is: **`plan()` → `resolve_subject` (clarify or stop) → `set_delegations` → Discovery step → Original's drafts loop.**

3. **Subject check (code), right after `plan()`.** Code resolves the names and the period (section 3.2). This happens before `set_delegations`, in the same place where the plan's existing clarification return already sits ([original.py:1032-1037](agents/original.py)).
   - **Ambiguous name.** It uses that existing clarification return, which is the only clarification mechanism.
     - `clarification_basis.missing_field` gains the value `"subject"`. Today it allows only `manager_id`, `start_date`, `end_date`, `metric`, `task` and `other` ([original.py:182](agents/original.py)).
     - The name as the manager wrote it is the `request_excerpt`, which is a literal substring of the question.
     - Nothing is cached. The manager's answer starts a new run that keeps the original question (section 3.2).
   - **The single rule.** An unresolved name gets a clarification. A name identified as a person or team outside the manager's team is rejected, and so is a period outside the authorized dates. No evidence is read.
   - **Result shape.** A rejection or a clarification is a normal `AgentResult`, not an exception and not a failure.
     - **A rejection reuses the existing `declined` status**, which already means "declined before any data is read" ([app.py:445](../Echo_UI/backend/app.py)). The Brief, the presentation and the slide export already show it ([Brief.tsx:207, 263-269](../Echo_UI/frontend/src/manager/Brief.tsx), [app.py:1427-1432](../Echo_UI/backend/app.py)). No new status exists, so no layer needs one. The rejection result is fully specified, because the Brief also renders a "Why" card from `guardrail` and `next_steps` ([Brief.tsx:271-275](../Echo_UI/frontend/src/manager/Brief.tsx)):
       - `answer`: the message, for example "Echo answers only about your own team";
       - `task_outcome = {status: "declined", reason_code: "subject_out_of_scope"}`;
       - `verification = {decision: "declined", drafts_checked: 0}`;
       - `guardrail = {rule: "Echo answers only about your own team", detail: <the name that resolved outside the team>, checked_by: "code"}`, never `"ZeroSugar"`, because ZeroSugar never saw it;
       - `next_steps`: two lines, "Ask about your own team or one of its members" and "Ask who on your team helped that team".

       The existing offline declined artifact ([offline.py:1446-1453](../Echo_UI/backend/offline.py)) is not copied, because it says that ZeroSugar checked the decision.
     - **A clarification** uses the existing `needs_clarification`.
     - So the UI shows the message, and gate 3 can tell "rejected" from "broken".
4. **Discovery step (always).**
   - **Where it is recorded.** Discovery is added to `planned_roles` ([original.py:1039-1043](agents/original.py)). It is not a tool, so the tool-to-role map ([original.py:631](agents/original.py)) does not change, and `delegate()` is never called with "Discovery".
   - **Where its result lives.** In a new `AgentResult.discovery` field, **not** in `child_results`. So the evidence handoff check ([original.py:1140-1145](agents/original.py)) and ZeroSugar's task outcomes are unaffected.
   - **How the stage shows it.** The agent stage is event-driven ([AgentStage.tsx:41](../Echo_UI/frontend/src/manager/AgentStage.tsx)). The sixth agent's state therefore comes from `agent_turn` and finish events with `agent="Discovery"`, like the other agents. The section's content comes from `discovery_section`. `AgentResult.discovery` is not sent to the page.
   - **A new code path.** Right after `set_delegations`, `workflow()` calls Discovery **once**, before the drafts loop. There is no precedent at this point. Cherry's prepared metrics run inside `delegate()` ([original.py:366-379](agents/original.py)), when Original's model chooses to call Cherry. This step is new, and it is a code call, so no model can skip it.
   - **Called once.** The result is kept for the whole run. Repair and correction rounds never call Discovery again.
   - **What it runs.** The prefilter (3.3), its single judgment call (3.4) and the code checks (3.5).
5. **Original composes** its normal answer, exactly as today. It may ask Cherry for metrics and Vanilla for sentiment, so a team question still gets team metrics.
   - **What Original does not receive.** No Discovery findings and no `DISC-*` IDs. Its fact catalog and its limits (24 cited facts and 12 narrative items, [grounding.py:20-21](agents/grounding.py)) are unchanged, so Discovery uses none of those slots.
   - **Known side effects.**
     - Original may independently propose something similar to a Discovery action, such as recognizing the same person.
     - The reverse can also happen: Original's answer may say that everything is recognized while the section shows hidden contributions. Original never sees Discovery's evidence, so the two are not reconciled. The section's provenance label tells the manager which part comes from which source.
     - Both are accepted known limits.
6. **ZeroSugar** reviews Original's answer in both phases, as today. Its input and contract (`review-v8`) do not change.
7. **Release.** Code renders the **Discovery section** (3.5) into its own field, `discovery_section.rendered`.
   - It is never concatenated into `answer`, so the reviewed candidate's identity and the grounding audit stay intact.
   - The export and the UI show it after the answer.
   - A release check confirms that the section is present for every Discovery status and matches the checked result exactly.
   - If Original's answer fails or is withheld, the section is still published when Discovery succeeded, because that is when it matters most. The result shows both statuses separately.
   - Actions go to the Action Center; follow-up runs on request (6.3).

Two "nothing found" results are kept apart:
- **`no_candidates`**: the prefilter selected no evidence. No judgment call is made.
- **`no_findings`**: the model judged the selected evidence and found no valuable hidden work.

In both cases the section says "no hidden-contribution findings **in the selected evidence**", with the coverage: how many people were reviewed out of how many in the team, and which caps were reached. It is never presented as proof that no hidden work exists. Failures are a third kind of result (3.6).

### 3.2 Subject, period and the two date windows

Code resolves every name, ID or team from the plan against the organization roster and the manager's authorized team: employees whose `Pilot_Manager_ID` is the manager ([data_access.py:39-44](agents/data_access.py)).

| Case | Result |
| --- | --- |
| Exactly one person in the manager's team | Process that person (up to 25 evidence items) |
| Two to five named people, all in the manager's team | Process exactly those people (up to 10 items each). Example: "How are Isabel and Tomás?" |
| More than five named people | Clarification: ask about the whole team or up to five people |
| Several people in the manager's team share a name | Clarification through the plan's existing path |
| A named person belongs to another manager's team | **Do not process.** Say the person is outside the manager's team. Read no evidence and make no judgment call |
| The question is about another team, or compares the manager's team with another team (`subject_kind = other_team`, or a team in `subject_names` that is not the manager's), for example "How are we doing compared with Customer Renewals?" | **Do not process.** Say that Echo answers only about the manager's own team. Read no evidence; no comparison |
| Another team is named only as the beneficiary of the manager's team's help (`focus_hint`), for example "Who on my team helped Customer Renewals?" | **Process** the manager's whole team, with that team as the beneficiary focus. The partner team is never a subject |
| A name that does not resolve, after matching that ignores accents and case ("Tomas" finds "Tomás") | Clarification: ask who was meant, listing close matches from the manager's team. Never stop, never guess |
| The question names nobody | The subject is the manager's whole team (section 3.3 pool) |

Code never widens the roster or the dates. A partner team can appear only as the beneficiary of the manager's own people, never as a subject. A run stops only when a name **resolves** to a real team or person outside the manager's team. An unresolved name gets a clarification, and a beneficiary focus never stops the run. A comparison with time, such as "compared with last quarter", is not another team; it is processed as a team question. Gate 3 covers these cases.

**Two date windows.** Today one `AccessScope` serves the whole run ([data_access.py:10-22](agents/data_access.py)), and its default `end_date` is 2026-09-30. Discovery needs two windows over the same manager and roster:

| Window | Dates in the demo | Used by | Rule |
| --- | --- | --- | --- |
| **Analysis** | up to the **as-of date**, 2026-06-30 | Discovery, Original, Cherry, Vanilla, ZeroSugar | Nothing after the as-of date is read, so a July event cannot change a June finding. The as-of date is the request's `end_date` (below) |
| **Follow-up** | from the decision date (2026-07-01) to the follow-up end (2026-09-30) | Only the follow-up code (6.3) | Same manager. The roster is frozen at the as-of date. It reads only the follow-up source tables, only for the people and work in saved actions, and can never add a subject |

The follow-up window is a separate `FollowUpScope` object, used only by the follow-up endpoint. A gate (section 8) checks that it cannot widen the roster or the subjects.

**How the as-of date travels.** No new parameter is needed, because the UI already sends a date range:
- The Manager UI builds `start_date` and `end_date` from its range ([ManagerApp.tsx:440](../Echo_UI/frontend/src/manager/ManagerApp.tsx)).
- The backend turns them into `AccessScope` ([app.py:396](../Echo_UI/backend/app.py)) and passes `--start/--end` to the Echo process ([app.py:454](../Echo_UI/backend/app.py)).
- For `discovery_v1`, that `end_date` **is** the as-of date. Three rules apply:
  - **Fixed range.** The whole range is fixed for `discovery_v1`, not only its end: 2025-10-01 to 2026-06-30. The UI shows it read-only. Otherwise a manager who moved the range to 2026-03-31 would move the as-of date, and the planted stories would silently disappear.
  - **No silent fill.** The backend rejects a `discovery_v1` request whose `start_date` or `end_date` is missing or differs from the fixed range. Today a missing date falls back to `SCOPE_MAX`, 2026-09-30 ([app.py:338](../Echo_UI/backend/app.py)). A later `end_date` would also expose follow-up data to the analysis. A `period_hint` still narrows the period inside the fixed range (below).
  - **CLI.** `--end` is mandatory on `discovery_v1`, and no separate `--as-of` option exists.

**Clarification keeps the question.** Suppose the manager asks "What should I recognize Isabel for this quarter?" and there are two Isabels.
1. The run ends with the clarification and the candidate list.
   - `resolve_subject` builds the list from the manager's roster only: name, team and ID for each match.
   - It goes in a new `AgentResult.clarification_candidates` field. Today a clarification is only a string ([original.py:1034-1036](agents/original.py)).
   - The manager view must pass the field through. Today it empties `clarification_questions` ([app.py:537](../Echo_UI/backend/app.py)).
2. The new request carries the **original question unchanged**, plus the manager's choice: `clarification: {"name_as_written": "Isabel", "employee_id": "E0xxx"}`.
3. A new run starts; the earlier one is not resumed. `plan()` reads the full original question again, so "recognize" and "this quarter" are kept.
4. **The chosen ID wins, without matching names.** The second plan may write the name differently, for example "Isabel García" or "Isabel G.". So when `clarification.employee_id` is present:
   - If the plan resolves to a single person, `resolve_subject` uses that ID directly.
   - If the plan names several people, the ID replaces the one name that matches several roster entries.
   - In both cases the ID must still be in the manager's team, or the run stops as out of scope.

The backend accepts the `clarification` field only together with a question, and the UI sends it from the clarification card. `RunRequest` gains the field ([app.py:335-344](../Echo_UI/backend/app.py)). The backend accepts only an `employee_id` that belongs to the manager's roster, and `resolve_subject` checks it again.

**Period hint.** With no hint, the period is the three quarters ending at the as-of date. A hint ("this quarter", "since January") is intersected with the analysis window. When the intersection is smaller than the hint asked for, the answer says so. When it is empty, the run stops with "that period is outside the authorized dates". The model never chooses dates.

### 3.3 Select the relevant evidence (code)

Code builds a **candidate pool** with fixed, versioned SQL and simple text matching over the authorized data. It does not judge value; it narrows what the model will read.

Selection signals (each stored as a reason the record was selected):

- **Help for another team:** a contribution, request thread, resolved blocker, incident handoff or meeting mention where the beneficiary is not the home team.
- **Visibility gap:** partner feedback not shared with the home manager, help with no formal work request, or help mentioned only in another team's notes.
- **Recognition gap:** no recognition event for that work, or recognition coverage unknown.
- **Importance:** the beneficiary team linked the help to one of its goals, or the blocker it resolved delayed a goal.
- **Repetition:** hidden help in two or more quarters.
- **Workload:** cross-team or after-hours load above the team's normal range.
- **Name in someone else's text:** a scoped employee's name appears in partner messages, notes or feedback about work recorded under someone else.
- **Work described in the employee's own self-review:** an `HR_self_review_items` entry describes help to another team, or an initiative that matches no goal and no record. A self-review never counts as corroboration by itself.

**Who enters the pool for a team question.** Two code tools are combined, with duplicates removed:

1. `lowest_satisfaction(team, period, n=10)` returns the 10 people in the manager's team with the lowest latest score in `HR_employee_performance` (section 5.4). Ties are ordered by the change from the previous quarter, then by ID.
2. `strongest_signals(team, period, n=5)` returns up to 5 more people with the strongest hidden-work signals, whatever their satisfaction. It requires at least two independent signal types, then orders by volume and recency. This keeps a satisfied person with strong evidence, such as E0001 in P5, from being dropped.

The pool holds 10 to 15 people. In the 5 of 60 teams with 15 people or fewer, the pool is the whole team. Each person records why they entered, but that reason is internal (section 5.6, privacy).

**Beneficiary focus governs (user decision 2026-11-15).** When the question names a beneficiary team, as in "Who on my team helped Customer Renewals?":
- **The pool changes.** The satisfaction slot is not used. The pool is up to 15 people from the manager's team with the strongest evidence of help **to that team**, ordered by:
  1. independent signal types toward that team;
  2. volume;
  3. recency.
- **The evidence changes.** Each person's 8 items are filled with evidence about that team first, then with closing context. Team-pattern leads are computed only for that team.
- **The caps stay.** Gate 1 checks that evidence about the named team reaches the pool for every planted helper of that team, not only that the question is accepted.

**Baselines inside the analysis window.** The team's "normal range" for workload is the team's median and spread over the three analysis quarters. "Repetition" means two or more of those quarters. Discovery reads nothing before the analysis window, which also matches the data access, because every query is filtered to the scope dates ([data_access.py:64-72](agents/data_access.py)).

**Nothing after the as-of date.** Every selection input is computed at the as-of date and excludes any event whose event date or recorded date is later. That covers recognition, shared state, name mentions, signals and satisfaction.
- For example, a July recognition must not hide a valid June finding.
- Feedback written in June and shared in July counts as **not shared** on June 30. Shared state is read only from the dated share fields (5.4), never from the Yes/No flag.

**Caps and balanced selection.** Each person in a team question contributes at most 8 evidence items. For each selected work item, the closing context comes first, because it can confirm or contradict the lead:

1. The **recognition state** at the as-of date: a recognition event, or an explicit "no recognition event recorded" fact with its coverage.
2. **Attribution:** who holds the record, and any other contributor named in the sources.
3. **Status or outcome:** acceptance, blocker resolution, or the linked goal's result.

The remaining slots go to supporting items, the most specific first, then the newest. Texts are trimmed to 300 characters around the relevant sentence. Each item keeps its source ID and its resolved `work_refs` (6.4). A one-person question keeps up to 25 items; a question about two to five people keeps up to 10 per person. All caps are versioned parameters, and reaching a cap is recorded.

**Team-pattern leads.** Code counts hidden help toward each beneficiary team across the whole team. A count is only a lead. For each lead, code adds up to two sample items per person involved, within the caps, and the model decides whether the samples support a team finding.

**External people in texts.** People outside the manager's team are authors, beneficiaries or co-contributors, never subjects. Before the pool reaches the model, code replaces each one with a stable placeholder naming only their role and team, for example `[Customer Renewals colleague 2]`. This keeps attribution judgments possible (P6, D3). The beneficiary team's manager may be named as the recipient of an A2 or A4 draft.

Code never sends the full contents of `text_documents` ([data_access.py:146](agents/data_access.py)) or whole tables.

### 3.4 Judge (model)

One batched model call receives the candidate pool. For each candidate it returns:
- whether there is valuable cross-team work the manager probably does not see, and what the work was;
- the benefiting team, and why the work matters (goal, blocker, incident);
- the recognition state (`recognized`, `not_recognized`, `unknown`);
- person finding or team pattern;
- the cited source IDs and exact quotes;
- the fitting action types from the catalog (6.2);
- if rejected, a short reason.

If several people show the same hidden help toward one team, the model reports a team finding and still lists the people the evidence names.

**At most 5 findings.** After the code checks, code keeps at most 5 findings using a fixed rule:
1. number of independent source types cited;
2. whether a beneficiary goal or blocker is linked;
3. recency.

Further findings that passed the checks are not hidden. The section lists **up to 5 more** in one line each, with the person and the beneficiary team, and without drafts. Any beyond that are only counted. Nothing is promised about a later question. In total the section shows at most 5 findings with drafts plus at most 5 one-line findings.

### 3.5 Integrity and the Discovery section

Discovery's judgments are not sent back for correction. Before anything is shown, inexpensive code checks run:

- Every cited ID exists in the pool Discovery received.
- Every quote is an exact substring of the **text the model saw in the pool**, which is trimmed to 300 characters and carries the external-person placeholders. The published quote is that same text. Checking against the raw database row would reject every quote that contains a placeholder.
- Every person is in the authorized roster, and every team and date is inside the analysis window.
- **When a finding may say "not recognized".** All three conditions must hold:
  1. no recognition event for the work exists at the as-of date;
  2. `OP_source_coverage` declares `HR_recognition_events` `complete` for the home team in the quarters of the work, so the absence of an event is meaningful;
  3. **every** cited feedback row has `Record_Coverage = complete`.

  If any cited feedback row is `partial`, or condition 2 fails, the state is `unknown`. A finding that cites no feedback row, such as P3's meeting notes and incident, depends only on conditions 1 and 2.

  **Which source each check reads.** Findings read the row level for cited feedback, and the table level only for the absence of recognition events. Follow-up reads `OP_source_coverage` only. Each check names its source, so the two never give conflicting answers about the same fact.
- Every suggested action type is in the catalog and its trigger fits the finding. For example, A1 is not allowed when the finding is already recognized.
- **Privacy:** nothing in the Discovery section names a person outside the manager's team or gives their ID. This applies to its quotes, summaries and drafts. Code checks the section against the organization roster, replaces any leak with the placeholder, and counts it in the log.
  - **Original's answer is not modified after review.** A replacement there would break the reviewed candidate's identity and the grounding audit, and the manager would read text no reviewer approved. Original receives nothing from Discovery, so its answer keeps today's privacy behavior.
  - **The one exception** is an allow-list entry per draft: `(action_id, partner_manager_id)`. It applies only to the recipient field of that A2 or A4 draft.
  - The same manager anywhere else, including in the draft body, is still replaced. A release-wide exception would either over-redact the recipient or under-redact everything else.

A finding that fails a check is withheld and recorded, not repaired. Discovery is not added to ZeroSugar's correction owners ([zero_sugar.py:103](agents/zero_sugar.py)).

**The Discovery section.** Code builds it from the checked result into `discovery_section.rendered`, a field of its own that the export and the UI show after Original's answer. It is never concatenated into `answer`. It contains:
1. **A pointer line, written by code from the status.** The count can never exceed the findings shown.

   | Status | Pointer line |
   | --- | --- |
   | `findings`, `partial` | "Discovery found N findings about contributions to other teams." N is exactly the number of findings shown: the detailed findings plus the one-line findings. A team-pattern finding counts as one finding and names its people |
   | `no_candidates`, `no_findings` | "No hidden-contribution findings in the selected evidence", followed by the coverage |
   | `all_withheld` | "Discovery could not produce verifiable findings" |
   | `failed_provider`, `failed_budget` | "Discovery could not complete the analysis", with the reason |

2. Up to 5 findings, each with its work summary, beneficiary team, why it matters, recognition and visibility state, quotes and source IDs.
3. For each finding, its action drafts, rendered from the fixed template for each action type (6.2) and filled only from the finding's fields.
4. Up to 5 further findings in one line each, with the person and the beneficiary team (3.4). The result carries these as a list, not only as a count.
5. The period line: the period analyzed, and a note when it was narrowed from the manager's hint (`period.narrowed_from_hint`).

Because code writes both the pointer and the section, neither can be omitted, reworded or invented by Original. The drafts add no claim that is not already in the finding.

**Provenance is marked.** The section is appended after review, so it is not part of `candidate.findings`, `release_counts` or the grounding check. The result therefore carries its own field:
- `discovery_section: {present, status, finding_ids, reviewed_by_zerosugar: false, checked_by_code: true}`, where `finding_ids` covers every finding shown, both the detailed ones and the one-line ones (each one-line entry carries its `finding_id`);
- the export and the UI show "Checked by code; not reviewed by ZeroSugar" on the section, so it is never read as part of the reviewed count.

**What ZeroSugar reviews:**

| Item | Reviewed by ZeroSugar? |
| --- | --- |
| The Discovery section, including its pointer, findings and action drafts | No. Code checks only |
| Original's answer and Original's own proposals | Yes, as today. Original receives no Discovery results, so this text contains nothing from Discovery |

Known limit: if Discovery's model misreads a comment but cites correctly, no reviewer catches it. The section's drafts repeat Discovery's own `work_summary` and `why_it_matters`, so an overstatement there appears in the drafts too. Gates 7-9 measure this.

The manager's later edits to a draft are the manager's own words. They are stored as a new version and are not reviewed. The privacy replacement still applies, and nothing is sent externally.

### 3.6 When Discovery cannot finish, and the budget

| Status | Meaning | What the answer shows |
| --- | --- | --- |
| `failed_provider` | A model call failed after the bounded retries, or the output failed the schema twice | Discovery section: "Discovery could not complete the analysis". Original answers the rest normally |
| `failed_budget` | Discovery's own cap was reached (2 calls or its time limit), or the run had no room left for its call | Same message, naming the budget. The run continues |
| `all_withheld` | Every finding failed the code checks | "Discovery could not produce verifiable findings", with the withheld count |
| `partial` | Some findings passed and some were withheld, or a cap cut the pool | The passing findings, plus how many were withheld or not reviewed |

None of these results is ever shown as "no hidden work". Each one is logged with its reason.

**Budget.** Today `RunBudget` allows, by default in the CLI, 32 model calls and 300 seconds per run ([runtime.py:97-138](agents/runtime.py), [original.py:433-434](agents/original.py)). Two facts rule out simply raising the limit:
- **The time limit is an absolute deadline.** It is fixed when the budget is created, there is no method to extend it, and exceeding it raises `RuntimeError` ([runtime.py:110](agents/runtime.py)). That error ends the whole run as `AgentRunError` ([runtime.py:203-210](agents/runtime.py)).
- **Agents close on an absolute threshold.** They begin closing when `remaining()["model_calls"]` drops to 2 for Original or 3 for the others ([runtime.py:306](agents/runtime.py)). A higher fixed limit would give Original extra turns on every question.

Two more facts matter for Discovery:
- **Network retries consume calls.** Inside `RunBudget.respond`, every transient network retry calls `consume("model")` again, with up to 3 attempts ([runtime.py:155-161](agents/runtime.py)). Rate-limit (429) retries happen inside the provider adapter and do not consume calls ([model.py:77-97](agents/model.py)).
- **There is no Discovery-specific timeout.** `check_request_deadline()` and `consume()` raise the same `RuntimeError("Workflow elapsed-time budget exceeded.")` ([request_pacing.py:20](agents/request_pacing.py), [runtime.py:110](agents/runtime.py)).

v8 therefore uses **Discovery's own cap, its own timeout and a refund recorded in separate fields** (user decision 2026-11-15):
1. **Own cap of 2 logical calls:** the judgment and one schema retry.
   - The network retries of a logical call belong to that call. They are all refunded with it, so they never count against the cap or the run.
   - Each logical call has its own time limit, a boundary check set below Discovery's connection timeout. It starts at **120 s under a 135 s profile timeout** (Errata 3; the semantics are below, Errata 4).
     - Latency is set mainly by the output, about 2k tokens. At 25 tokens per second that alone takes 80 s, so 80/90 would sit on the edge, and every question could return "Discovery could not complete the analysis".
     - The pair is set from a **real latency measurement**: one authorized call, or the p95 of the gate 10 run. It is then lowered if the measurement allows.
     - A `failed_budget` caused by latency in gate 10 is a failure to investigate, not an acceptable result.
     - Discovery gets its own profile entry: the same GW model as Original, with its own `timeout_seconds` and `max_retries: 0`. Its time limit comes from measured latency, not from the input size.
     - **What the two numbers do (Errata 4, corrected by Errata 5).** Echo's deadline is checked only at boundaries: before a request and after a retry's backoff ([runtime.py:154](agents/runtime.py), [runtime.py:168](agents/runtime.py), [model.py:78-81](agents/model.py)). It never cuts a request in flight. So Discovery also passes the time left as the request's own timeout:
       - **Each request's timeout is the time left before Discovery's 120 s limit,** capped by the profile's 135 s (Errata 6):
         - `connections.py` stores the profile's `timeout_seconds` on the model object as `request_timeout` (today it lives only in the client, [connections.py:127](agents/connections.py), [model.py:117-119](agents/model.py)).
         - `respond()` sets a separate per-call deadline only when it receives one, which only Discovery does. `send_request` then passes `timeout = min(time left before that deadline, request_timeout)` through the SDK's per-request `timeout` option.
         - With no per-call deadline, nothing is passed, so Original, ZeroSugar and the specialists keep their 45 s client timeout unchanged. A logical call, network retries included, therefore ends by about 120 s. The 135 s profile timeout is only a backstop.
       - **Before a retry backoff,** if the 120 s would pass during the wait, Discovery raises `DiscoveryTimeout` at once, without sleeping. This is the same position as the existing seconds check ([runtime.py:163-164](agents/runtime.py)).
       - **`max_retries: 0`** in Discovery's profile ([connections.py:104](agents/connections.py)). With the default of 1, which today's GW profiles use, the SDK would repeat a request by itself, outside Echo's checks.
       - **Worst case:** about 120 s for the judgment call plus about 120 s for the schema retry, so about 240 s for Discovery. Those seconds are refunded and extend the run's deadline, so the run's wall clock can reach about `run_seconds` + 240 s (about 540 s with the CLI's 300 s). Gate 10 judges the run budget, not the wall clock. Measured latency (T4.6) is expected to lower it.
   - For reference, today's GW profiles for the other agents use 45 s ([connections.json:24](connections.json)). Discovery does not use those profiles; it has its own 135 s profile.
   - Demo and gate runs state their `run_seconds` explicitly. The UI sends 900 s by default ([app.py:344](../Echo_UI/backend/app.py)), while the CLI uses 300 s.
2. **A check before every call**, including the schema retry and each network retry. If the run's remaining calls or seconds cannot cover the call, Discovery returns `failed_budget` without calling. `consume()` can therefore never raise a run-ending error inside Discovery.
3. **Own timeout exception.** A new `DiscoveryTimeout` class is raised by `check_request_deadline()` when the request runs inside Discovery and its request deadline is reached. That deadline is the earlier of Discovery's limit and the run's, and the check cannot tell them apart, so inside Discovery both give `failed_budget`. After the refund, Original has the seconds it had before Discovery. Outside Discovery, the run-level `RuntimeError` keeps its meaning.
4. **Refund in a `finally` block for every logical call, without changing the raw counters.** It runs on every outcome: success, schema failure, provider error and `DiscoveryTimeout`. So `failed_budget` and `failed_provider` return their calls and seconds too. `RunBudget` gains two fields, `refunded_models` and `paused_seconds`:
   - `remaining().model_calls = model_limit - models + refunded_models`;
   - the effective deadline is `deadline + paused_seconds`.

   `models` still counts every real call, network retries included ([runtime.py:161](agents/runtime.py)), and the original deadline is kept. Each logical call writes one `request_costs` entry, so the check is: `models` minus the `request_transport_retry` events ([runtime.py:165](agents/runtime.py)) equals the number of `request_costs`.
   - **One change to the retry path keeps that check true (Errata 6).** Today `consume("model")` runs before the checks that can refuse a retry ([runtime.py:161-164](agents/runtime.py)), so a refused retry is counted but never recorded. `consume("model")` moves to just before `record("request_transport_retry")`, after every refusal check: Discovery's pre-backoff check and the existing seconds check. A refused retry is then neither counted nor recorded. This also fixes the same gap for the other agents; the refused path still raises as today. `snapshot()`, `workflow_budget` and captures show the raw counters and the two refund fields side by side.

   **Every enforcement point uses the effective values.** This covers:
   - the call check in `consume()`;
   - the deadline check in `consume()`;
   - the request deadline that `respond()` sets;
   - the retry path inside `respond()`.

   If they used the raw values, Original's closing turn would fail deterministically at budget exhaustion. Within Discovery, the retry path raises `DiscoveryTimeout`, not the generic error. `respond()` accepts an optional per-call deadline, which is how Discovery's per-call limit is applied. Original workflows are never resumed ([original.py:427-428](agents/original.py)), so the refund fields matter only for snapshots and captures. The detailed acceptance criteria are in breakdown §12.
5. **Effect.** Original and ZeroSugar see exactly the budget they would have had without Discovery: the same remaining calls, the same closing points and the same seconds. The with/without comparison (gate 10) is not affected by budget.

**Retries.**
- **Network errors:** at most 2 retries per logical call, as today, all within its 120 s. They consume calls, but they are refunded.
- **Rate limit (429):** not retried, because Discovery's profile, like today's GW profiles, declares no pacing interval ([model.py:90](agents/model.py)). Discovery returns `failed_provider`, and its use is refunded.
- **Schema failure:** retried once, after a new budget check.
- **Failed code checks:** a finding that fails them is never retried.

If the whole run still exhausts its budget later, the existing budget-exhaustion path ends it with a limited result and a budget notice. A Discovery section that was already built is still published (3.1, step 7).

## 4. Token budget

Measured context, 2026-11-14, read only:

- Recent live runs are input-heavy: `reports/gwu_original_8.json` has 9 calls and about 64k input and 4.9k output tokens. Its largest single call has 13.3k input.
- A median manager scope has about 48 employees and 1,413 contributions. Sending all of it would be roughly 715k tokens; one quarter is roughly 90k. These counts are agent-reported.

Planned Discovery cost (subject identification now rides on the existing planning call, adding about 0.1k output):

| Call | Input | Output |
| --- | --- | --- |
| Judgment, team question | about 18-20k tokens: up to 15 people × 8 items × about 130 tokens (300-character text, ID, `work_refs`), plus leads and instructions | about 2k |
| Judgment, one person | about 4k tokens | about 0.8k |
| Judgment, two to five people | about 1.4k per person, plus instructions | about 0.5k per person |

These figures are **floors from arithmetic, not measurements**. Before any live run, the prefilter output for M32 and M14 is counted with the provider's tokenizer offline (T2.5). GW's rate limit of about 50k tokens per minute was already exceeded once (run 6: 110k in 73 s). Echo's pacing is not active for it: today's GW profile declares no `request_interval_seconds` ([connections.json:20-29](connections.json)), and a pacer is installed only when one is declared ([connections.py:142](agents/connections.py)). Whether Discovery's profile needs one is decided from gate 10, not assumed. Its measured **latency**, not its input size, sets the time limit in 3.6.

Precomputed at import, each keeping its event and recorded dates so filtering at the as-of date stays exact:
- per-contribution visibility events (praised, shared, recognized), with one dated `shared` event per share;
- quarter keys;
- an index of employee-name mentions in partner texts.

Each run logs the prefilter version, caps and SQL hash, the way metric versions are logged today ([metrics.py:56](agents/metrics.py)). Every run also records `discovery_applied` (true or false), together with Discovery's calls, tokens, seconds and refund. That makes it possible to measure later what Discovery costs and whether it changes completion rates. Today the completion rate is about 59% on the hard question (32 of 54).

The internal log entries `rejected.reason` and `withheld.check` use fixed enums, such as `already_recognized`, `own_team_help` or `quote_not_in_source`. Following the project rule, they never copy source text or the question.

## 5. Data baseline

### 5.1 Why the current data cannot demonstrate Discovery

Read-only checks of `data/echo.db` (eleven tables; the `data_extensions` tables are not loaded):

- **Cross-team help is normal, so it is no signal.** 66,192 of 77,333 contributions (86%) are cross-team.
- **Feedback has no real dates.** It has only 8 distinct `Interaction_Date` values (quarter ends), and every row needs a `Contribution_ID` and a manager author ([QA_data_dictionary.csv:94-98](../files_update/QA_data_dictionary.csv)).
- **The text is uniform.** Contribution text comes from about nine summary templates and nine `Business_Outcome` values. There are no team goals or measured outcomes.
- **The roster is larger than v5 assumed.** `HR_employees` has 2,500 employees in 60 managers' teams, with 10 to 85 people per team (checked 2026-11-15).

The new data must create **variance**: in who helps whom, whether it mattered, whether praise reached the home manager, whether recognition followed, and how heavy the load was. **The signal must also live in the text**, because the model reads it.

### 5.2 What exists today and what we create

| Already in the database (kept, copied into the new pack) | What we create |
| --- | --- |
| Employees and managers | Team goals with target and due date (`OP_team_goals`) |
| Projects and their objective | Measured goal results (`OP_goal_outcomes`) |
| Formal work requests with hours | Informal help threads and messages (`OP_collab_threads`, `OP_collab_messages`) |
| Accepted contributions with home and beneficiary team | Blockers between teams (`OP_dependency_blockers`) |
| Feedback at quarter-end dates with a "shared with home manager" flag | Incidents and on-call handoffs (`OP_incident_handoffs`) |
| Weekly available hours | Mentions in other teams' meeting notes (`OP_meeting_mentions`) |
| Priority decisions and escalations | Formal recognition events (`HR_recognition_events`) |
| Team surveys and program participation | Weekly cross-team and after-hours activity (`OP_activity_weekly`) |
| Team-level, anonymous survey scores only | Identified per-employee pulse, engagement and performance (`HR_employee_performance`) |
| `data_extensions`: goals and December 2025 self-reviews, not loaded today | Loaded: goals as context, self-reviews as a Discovery source, 2026 corroboration for P5 |
| | Follow-up records (`HR_one_on_ones`, `HR_review_notes`, `OP_team_plans`) and coverage declarations (`OP_source_coverage`) |
| | Real event dates, dated shares and author type on feedback; goal, effort and channel on contributions; after-hours on capacity; work anchors on evidence rows |
| | Varied text, hand-built stories and decoys (5.6), automatic plants (5.7), follow-up events from July to September 2026, private answer keys |

### 5.3 Packaging

A separate versioned pack `files_discovery_v1/` and database `data/echo_discovery_v1.db`. The pack contains:
- copies of the eleven current tables, with added columns;
- copies of `HR_goals` and `HR_self_review_items` from `data_extensions/`, keeping their IDs;
- the new tables.

`files_update/`, `data/echo.db` and `data_extensions/` stay unchanged. The extension's `QA_discovery_answer_key.csv` is never loaded.

`import_data.py` changes:
- a `--profile legacy|discovery_v1` option, with the file list taken from the profile's manifest instead of the fixed `FILES` tuple ([import_data.py:17-29](import_data.py));
- column types from a `Type` column in the data dictionary ([import_data.py:30-42](import_data.py));
- ISO validation for `*_At` timestamps;
- an "exactly one anchor" check for polymorphic links;
- share-date checks on feedback (5.4);
- a check that `Topic_Code` uses only its allowed values;
- table-count checks per profile;
- indexes for the new tables;
- a default output that is never `data/echo.db`.

### 5.4 New and extended source tables

New tables cover all 2,500 employees over the analysis and follow-up windows, 2025-10-01 to 2026-09-30. Copied legacy tables keep their full horizon. Hand-built stories are planted in M32's and M14's teams (5.6), and automatic plants in every team (5.7). Counts are construction targets; the manifest records exact numbers.

| Table | Grain and key fields | Target rows | What it enables |
| --- | --- | --- | --- |
| `OP_team_goals` | One team goal: ID, team, owner manager, metric, target, due date. About 2-3 goals per team per quarter | ~600 (60 × 4 × 2.5) | Links help to the beneficiary's goal |
| `OP_goal_outcomes` | One goal measurement: value, numerator/denominator, measured at | ~2,400 (about 4 per goal) | Goal met or missed |
| `OP_collab_threads` | One cross-team request thread: opened at, requesting team, requester, topic, optional work request | ~25,000 | Help that never became a formal request |
| `OP_collab_messages` | One message: thread, author type/ID, sent at, text, mentions | ~120,000 | Who asked, who answered, who was thanked |
| `OP_dependency_blockers` | One blocker: raised at, blocking team, blocked goal, resolved by, resolved at, days blocked | ~6,000 | Unblocking another team |
| `OP_incident_handoffs` | One incident or handoff: severity, responders, owning team, start/end, notes | ~3,000 | Firefighting and after-hours help |
| `OP_meeting_mentions` | One line of another team's notes: date, team, mentioned employee, text, optional work anchor | ~15,000 | Thanks where the home manager is absent |
| `HR_recognition_events` | One formal recognition: given by, visibility, type, one typed anchor, event date | ~4,000 | "Praised" versus "recognized"; follow-up for A1 |
| `OP_activity_weekly` | One employee-week: cross-team hours, after-hours minutes, meeting hours | ~130,000 (2,500 × 52 weeks) | Workload signal, repetition, and the team's normal range inside the analysis window |
| `HR_employee_performance` | One employee per quarter: confidential pulse score (1-5), engagement, performance rating, goal attainment %, recorded date | ~10,000 (2,500 × 4 quarters) | Feeds `lowest_satisfaction` |
| Reused `HR_goals` | Individual goals from `data_extensions` | 12,670 | Inside or outside the person's goals |
| Reused `HR_self_review_items` | December 2025 self-review items from `data_extensions` | 12,129 | The employee's own account |
| `HR_one_on_ones` | One 1:1: manager, employee, date, **`Topic_Code`** (`workload`, `career`, `performance`, `recognition`, `other`), free-text notes | ~2,000 | Follow-up for A3, matched on `Topic_Code = workload` |
| `HR_review_notes` | One review note: employee, cycle, author, cited work anchor, date | ~1,000 | Follow-up for A5 |
| `OP_team_plans` | One planning item: team, partner team, item text, date | ~800 | Follow-up for A6 |
| `OP_source_coverage` | One row per source table × home team × quarter: `complete` or `partial`. The home team is the manager's team that owns the employees; beneficiary teams declare nothing. Seven tables declare coverage: `HR_recognition_feedback`, `HR_recognition_events`, `HR_one_on_ones`, `HR_review_notes`, `OP_team_plans`, `OP_meeting_mentions` and `OP_collab_messages` | ~1,700 (7 × 60 × 4). **Every row is `complete` except one named row:** `HR_recognition_feedback`, M41, 2026-Q3, which gives gate 4's `partial` → `unknown` follow-up case through one of M41's automatic plants. No row is `partial` at random | Decides `not_yet` versus `unknown` in follow-up. For findings, only the `HR_recognition_events` row is read, and only for whether a missing recognition event is meaningful (3.5) |

Columns added to the copied tables:

- **`HR_recognition_feedback`:**
  - `Interaction_At` (the real event date), `Author_Type` and a nullable `Contribution_ID`;
  - **`Record_Coverage` regenerated as an enum `complete | partial`**, set per feedback row. In `data/echo.db`, every one of the 42,542 rows says that other conversations "may be unrecorded" ([QA_data_dictionary.csv:107](../files_update/QA_data_dictionary.csv)). Under that wording, every finding would be `unknown`, A1 could never be proposed, and P1 could not pass gates 4 and 7. In the pack:
    - most rows are `complete`;
    - D5's rows are `partial`;
    - background rows carry about 5% `partial`, never on a row cited by a story or plant;
    - **every feedback row cited by P1-P6 or by an automatic plant is `complete`**, and the build QA checks this;
    - the old free text is not copied;
  - optional thread, blocker and incident anchors, with an at-least-one-anchor check;
  - `Shared_With_Home_Manager_At`: when the feedback became visible to the home manager, null if never;
  - `Share_Recorded_At`: when that share was recorded.

  Feedback counts as shared at date *t* only if both dates are on or before *t*. The legacy `Shared_With_Home_Manager` flag is derived from the date and is never read by Discovery or follow-up. The importer rejects a share date earlier than `Interaction_At`, and a flag that disagrees with the date.
- **`OP_contributions`:** `Team_Goal_ID`, `Effort_Hours`, `Request_Channel` (formal or informal).
- **`OP_capacity`:** `After_Hours`, `Cross_Team_Hours`.

No column states the expected verdict. Text: at least 60 templates per text family, with slot variation, a range of tones and deliberately vague messages. Specific text must not announce the answer.

### 5.5 Dates inside the data

| Window | Dates | Use |
| --- | --- | --- |
| History | 2024-10-01 to 2025-09-30 | Legacy tables only. Discovery does not read it, and no new table is generated for it |
| Analysis | 2025-10-01 to 2026-06-30 | Planted hidden work, including the December 2025 self-reviews. The as-of date is June 30 |
| Follow-up | 2026-07-01 to 2026-09-30 | Later records that show whether the actions happened |

Manager decisions carry a simulated date of 2026-07-01. The real time of the click is stored separately.

### 5.6 Planted stories and decoys

All employees below belong to M32 (Sales Operations), except P5's. P5's six employees are:
- E0001 (M14, Data Platforms);
- E0046 (M46, Data Platforms);
- E0051 and E0066 (M31, Customer Renewals);
- E0074 and E0085 (M01, Customer Care).

| ID | Subject | Plant | Expected result |
| --- | --- | --- | --- |
| P1 | E0010, person | Resolves a 9-day blocker on Enterprise Accounts' (M29) renewal-accuracy goal, which is then met. Three partner praises, none shared by June 30; no recognition. One June praise is shared in July | Found, praise still unshared at the as-of date. A1 recognize and A4 ask M29 to copy the home manager. Follow-up: a July recognition makes A1 **Observed**; the July share makes A4 **Observed** |
| P2 | E2156, person | 14 informal threads for Customer Renewals (M31) with no work request; after-hours above 6 h/week for five weeks | Found. A3 workload conversation and A1 recognize |
| P3 | E0728, person | Night incident handoff for Escalation Services (M03); thanked in M03 meeting notes; no formal feedback. Feedback coverage for M32 in 2026-Q3 is declared complete | Found. A2 request feedback from M03. Follow-up: nothing, so **Not yet** |
| P4 | Team pattern | Several M32 members repeatedly help Infrastructure (M16) over three quarters; feedback never shared | Team finding naming the people. A6 and A4 |
| P5 (required) | E0001, M14; the same project for M46, M31 and M01 | Rafay's renewal-risk early-warning tool, already in six December 2025 self-reviews and matching no goal or record. The pack adds 2026 corroboration: threads with Customer Renewals, a meeting mention and a renewal-goal outcome citing the alerts. E0001's satisfaction is **not** among M14's 10 lowest | M14's team question finds E0001 through the strong-signals slot, naming co-contributors' teams but not their names. M46, M31 and M01 each find their own people. A1, A2 to Customer Renewals, A5 |
| P6 | E0970, person | Named only inside other people's feedback and messages, for work recorded under E0107 | Found only by reading text: credit the real contributor |
| D1 | E1748 | Same volume as P1, but already recognized and all feedback shared | Not a gap |
| D2 | E1333 | Many threads, but no acceptance, goal missed, blocker still open | Acknowledge effort; no impact claim |
| D3 | E0107 | Holds the record for P6's work | Do not credit E0107 |
| D4 | E2233 | High after-hours from covering leave on their own team | Workload only, not hidden cross-team work |
| D5 | Any | Partial `Record_Coverage` on the relevant feedback | Recognition state **unknown** |
| D6 | Any | Help inside the home team | Not a cross-team finding |
| D7 | One of the 10 least satisfied | Low satisfaction, no hidden cross-team work | No finding; do not invent one |
| D8 | High satisfaction | Hidden help with only one weak signal | Not in a team question's pool; found when asked about directly |

Satisfaction alignment for M32:
- P1, P2, P3 and at least two P4 members are among the 10 least satisfied, and so are D1, D2, D4 and D7.
- P6 and D3 enter through the strong-signals slot.
- **Precedence with automatic plants.** The hand-built stories fill M32's low-satisfaction slot. M14's hand-built story, P5, uses the strong-signals slot. So in M32 and M14 both automatic plants use the strong-signals slot. That keeps M32's strong slot within 5 people (P6, D3 and 2 plants) and M14's within 3 (E0001 and 2 plants).

**Privacy of the pulse score.** The identified pulse score is sensitive.
- It is visible only for the manager's own team and is never linked to the anonymous survey.
- It only decides whose evidence is read.
- The manager sees findings and their actions. The manager does not see the pool, the reason a person entered it, or rejected candidates.
- People are described as "prioritized for review", never ranked. A finding can come from either the low-satisfaction slot or the strong-signals slot, so appearing in one does not reveal which slot it was.

Background noise: about 5% of profiles per team are near misses. Expected answers live only in a private `QA_discovery_v1_answer_key.csv`, which is never loaded or put in a prompt.

### 5.7 Automatic plants in every manager's team

The generator plants **two simple hidden contributions in each of the 60 teams**, about 120 cases, with a fixed seed.

- **Shape.** Each case is help to another team: partner praise not shared, a corroborating thread or blocker, and no recognition.
- **Which slot they test.**
  - In 53 teams, one plant is among the 10 least satisfied and the other enters only through strong signals.
  - In the 5 teams with 15 people or fewer (M41, M58, M42, M46, M49), both plants are in the low-satisfaction slot, because the pool is the whole team and the strong-signals slot filters nothing.
  - In M32 and M14, both use the strong-signals slot (5.6).
  - That gives about 63 plants tested through low satisfaction and 57 through strong signals. The totals stay at 120 plants and 60 decoys.
- **Decoys.** Each team also gets one simple decoy: the same work already recognized, or own-team help.
- **Answer key.** Answers go in the same private key, marked `hand_built` or `automatic`.

The code part (subject resolution, both pool tools, prefilter recall) is checked offline for all 60 managers at no token cost. The model judgment is checked live only on M32 and M14.

## 6. Actions, decision and follow-up

### 6.1 What exists

- Original must propose at least one cited action ([original.py:45-48](agents/original.py)), with the schema `{text, citation_ids}` ([original.py:678](agents/original.py)). **This stays unchanged**: Original's own proposals keep that schema and keep ZeroSugar review.
- The UI assigns action kinds with regular expressions over free text ([visual.tsx:99-123](../Echo_UI/frontend/src/manager/visual.tsx)). The Action Center keeps meetings and events in browser `localStorage` ([actionStore.ts](../Echo_UI/frontend/src/manager/actionStore.ts)), and "Completed" is a manual click with no evidence behind it ([actionTypes.ts:1-6](../Echo_UI/frontend/src/manager/actionTypes.ts)).

### 6.2 Discovery action catalog

Discovery actions are typed records built by code in the Discovery section. The model suggests the action types; code checks that each trigger fits and renders the draft from the template.

| Action | Subject | Trigger | Draft template (slots filled by code from the finding) | Must not claim |
| --- | --- | --- | --- | --- |
| A1 Recognize a contribution | person | Supported hidden work, not recognized | Recognition note for the manager to personalize | "Never recognized" under partial coverage; engagement or retention effects |
| A2 Request feedback from the benefited team | person | Help with no partner feedback | Message to the partner manager | That the partner valued the work |
| A3 Workload conversation | person | Cross-team or after-hours load above the normal range | Agenda for a 1:1 | Burnout or a performance judgment |
| A4 Ask for visibility | person or team | Partner praise not shared with the home manager | Note asking the partner to copy the home manager | Bad intent by the partner |
| A5 Performance-review note | person | Supported help outside the person's goals | Review note marked "to verify" | That the work was formally assessed |
| A6 Team process change | team | Repeated pattern toward one partner team | Planning item | Savings or productivity gains |

Each action record has the following fields: `action_id`, `action_type`, `subject_kind`, `subject_id`, `beneficiary_team`, `finding_id`, `work_refs` (6.4) and `draft_text`.

### 6.3 Decision and follow-up

- **States.** An action starts as `proposed` and the manager makes it `accepted`, `edited` or `dismissed`, with a reason when dismissing. Follow-up gives `observed`, `not_yet` or `unknown`. Nothing is shown as sent or done without a matching source record.
- **Persistence.** A server-side SQLite store, `manager_actions`, separate from the source database, with `POST/GET/PATCH /api/managers/{id}/actions`. Discovery actions leave `localStorage`; existing meeting and event actions can stay there.
  - **No authentication.** Manager selection is a demo, not a login ([data_access.py:10-22](agents/data_access.py)), and the endpoints have no authentication. The store holds employee names, quotes from other teams' texts and drafts, so it is for the synthetic demo only and must never hold real data.
- **Only decided actions are followed up.**
  - Follow-up runs only for actions that are `accepted` or `edited`. The decision date is the date of that decision, simulated as 2026-07-01 in the demo.
  - A `proposed` action shows "pending decision" and gets no follow-up result.
  - A `dismissed` action is never checked.
- **Follow-up is code, not an agent.** A Python endpoint reads only the follow-up window (3.2), using `FollowUpScope`. A source event counts only if it matches the action's **person, work, recipient and date**: on or after the decision date and no later than the follow-up end.

| Action | `observed` when a source event shows | Source table |
| --- | --- | --- |
| A1 Recognize | A recognition for the subject employee whose anchor is one of the action's `work_refs`. Recognition for other work does not count | `HR_recognition_events` |
| A2 Request feedback | New feedback written by the beneficiary team about one of the `work_refs` | `HR_recognition_feedback` (author team = beneficiary team) |
| A3 Workload conversation | A 1:1 between the home manager and the subject with `Topic_Code = workload` | `HR_one_on_ones` |
| A4 Ask for visibility | A **share event**: feedback from the beneficiary team about one of the `work_refs`, whose `Shared_With_Home_Manager_At` falls between the decision and the follow-up end. The feedback itself may be older (a June praise shared in July). A share before the decision does not count | `HR_recognition_feedback` (`Shared_With_Home_Manager_At`, `Share_Recorded_At`) |
| A5 Review note | A review note for the subject that cites one of the `work_refs` | `HR_review_notes` |
| A6 Team process change | A plan item for the manager's team that names the beneficiary team | `OP_team_plans` |

- **`not_yet` versus `unknown`: the coverage declaration decides, not the presence of rows.**
  - `observed`: a matching event exists, under any coverage.
  - `not_yet`: no matching event, and `OP_source_coverage` declares `complete` for the source table and team in every quarter of the follow-up interval. An empty table under complete coverage is exactly `not_yet`.
  - `unknown`: no matching event, and coverage is `partial` or undeclared for part of the interval.
  - P3 depends on this.
- **Edited actions.** Matching uses the last saved version. If the manager changed the action type, the new type's rule applies. Earlier versions stay in the history but are never matched.
- **Dismissed actions** are never checked.
- **UI label.** The UI shows the three results and any dismissal reason. It is labelled "Simulation". "Observed" means that a matching record exists in the synthetic source data. Nothing is sent externally.

### 6.4 Work references: one identity from finding to follow-up

A message, a blocker and a recognition can have different IDs and still be about the same work. Every link from finding to action to follow-up uses one contract, the **work reference**: `{"type": "contribution | thread | blocker | incident", "id": "..."}`. No new table is needed.

- **In the data.** Evidence rows carry their work anchors as columns:
  - messages carry their thread;
  - feedback and recognition events carry one typed anchor;
  - meeting mentions and review notes carry an optional anchor;
  - self-review items may have none.
- **In the pool.** Code attaches each item's `work_refs`. The model does not write them.
- **In the finding.** Code computes `work_refs` as the union of the anchors of the cited evidence.
  - A finding with no anchored evidence has empty `work_refs`. It can still be shown, and it can still produce A3 or A6.
  - Its A1, A2, A4 and A5 actions always get `unknown`, and the UI says why.
- **In the action.** Code copies the finding's `work_refs`.
- **In `manager_actions`.** Each saved version stores its own `work_refs`. When editing, the manager may remove references, and may add only references from the same finding.

## 7. Integration checklist

| Area | Work |
| --- | --- |
| `agents/discovery.py` (new) | A **small class of its own**, not a `Specialist` subclass. `Specialist.run` is a loop of up to 8 iterations with 7 model turns, and it needs a terminal tool ([runtime.py:302-320](agents/runtime.py)), which does not fit one call. The class calls `budget.consume("model")` and `budget.respond(...)` directly: one judgment call and one schema retry, with its own time limit. It runs the prefilter, the code checks and the top-5 rule, and returns `discovery-result-v1`. It records one `agent_turn` per call |
| `agents/discovery_tools.py`, `agents/discovery_checks.py`, `agents/discovery_section.py` (new) | Subject resolution, pool tools and prefilter; code checks; the pointer, the section and action rendering from templates |
| `agents/runtime.py`, `agents/request_pacing.py` | <ul><li>`RunBudget.refund(models, seconds)`, which adds to `refunded_models` and `paused_seconds` without changing `models` or `deadline`.</li><li>`remaining()` and the effective deadline use the two refund fields.</li><li>Network retries inside a Discovery call are attributed to that call.</li><li>A new `DiscoveryTimeout`, raised by `check_request_deadline()` within Discovery.</li><li>`respond()` takes an optional per-call deadline, kept separately from the run's.</li><li>In the retry path, `consume("model")` moves after the checks that can refuse a retry.</li><li>The refund fields in `snapshot()`.</li></ul> |
| `agents/model.py` | `send_request` passes a per-request `timeout` only when a per-call deadline is set: the time left, capped by the model's `request_timeout`. No change for the other agents |
| `agents/original.py` | <ul><li>Plan schema: four new fields and the key-set update (162-265). There is no `needs_discovery` flag.</li><li>`"subject"` added to the `missing_field` enum in both places: the schema (182) and its validation (327-328).</li><li>`resolve_subject` right after `plan()`, before `set_delegations` (1028-1038).</li><li>`"Discovery"` in `planned_roles` (1039-1043), not in the tool-to-role map (631). Its result goes in `AgentResult.discovery`, not in `child_results`.</li><li>The new Discovery step, which always runs before the drafts loop, with a refund in a `finally` block for every logical call.</li><li>`discovery_section.rendered` at release, never concatenated into `answer`, with the release check. The section is also published when Original's answer fails.</li><li>Normal `AgentResult`s for rejections: identified out-of-scope subjects, including comparisons with another team. A clarification with `clarification_candidates` for unresolved or ambiguous names. Neither is a failure.</li><li>Four `setdefault` defaults for the new plan fields in the non-live block (221-223), so saved plans and demo replays keep loading.</li><li>One join point that attaches `discovery_section` to every exit of `run()`, including `incomplete()` (479-500, 1138).</li><li>`self.discovery` reset with the other per-run state (426-444); `discovery_section` is `not_run` when Discovery did not run.</li><li>The clarification ID applied directly.</li><li>Nothing from Discovery reaches the compose step.</li></ul> |
| `agents/policies.py` | Discovery role text, plus the planning rule for `subject_names` versus `focus_hint` (a team asked about or compared against goes in `subject_names`; a beneficiary-only team goes in `focus_hint`) |
| `agents/grounding.py` | No change: Original cites no Discovery IDs |
| `agents/zero_sugar.py` | No change. Its input and `review-v8` contract stay the same, because the section is appended after review. Discovery is not in `OWNERS` |
| `agents/data_access.py` | Projections over the new tables; as-of = `end_date`, explicit on `discovery_v1`; `FollowUpScope` for the follow-up endpoint only |
| `agents/connections.py`, `connections.json` | Discovery's own profile entry: the same GW model as Original, `timeout_seconds` 135 to start as a backstop, set from measured latency (today's profiles use 45 s); `max_retries: 0`; no pacing interval. `connections.py` stores `timeout_seconds` on every model object as `request_timeout` |
| `agents/resume.py`, `capture.py`, `execution_log.py`, `run_agent.py`, `check_release.py`, `__init__.py` | Sixth-role registration; capture of the call and the refund; `discovery_applied`; CLI `--database`, with `--end` mandatory on `discovery_v1`; a `clarification` argument; the export shows the section's provenance |
| `import_data.py`, `files_discovery_v1/`, generator | Section 5 |
| `.claude/agents/report-reader.md`, `score_discovery.py` (new) | Read `discovery_section` from the result. Findings are not in `candidate.findings` or `verification.reviews`, so a reader that skips the field would report "found nothing" |
| UI backend `app.py`, `offline.py` | `discovery_section` added to the manager-view allow-list (`without_comment_text`, [app.py:514-541](../Echo_UI/backend/app.py)); database selection; the fixed range on `discovery_v1`, where any other `start_date` or `end_date` is rejected; the `clarification` field passed to the run; actions store; follow-up endpoint; offline fixtures |
| UI frontend | <ul><li>A fixed, read-only date range for `discovery_v1`.</li><li>A clarification card that resends the original question with the choice.</li><li>Sixth agent on stage.</li><li>A Discovery section with its provenance label, typed action cards, decision buttons, follow-up badges and a simulation label.</li><li>No subject selector.</li></ul> |
| Tests | Section 8 gates; update fixtures that assumed five roles |

## 8. Evaluation and gates

**Offline, zero tokens:**

1. **Pool recall.**
   - The prefilter's pool contains every hand-built positive (P1-P6), and P5 and P6 enter through the strong-signals slot.
   - For all 60 managers it contains at least 95% of the automatic plants.
   - P5's other managers (M46, M31, M01) are checked here, offline only.
   - **Beneficiary focus:** for "Who on my team helped Infrastructure?" in M32, every P4 member enters the pool, with evidence about Infrastructure.
2. **Code checks.** Fabricated IDs, fabricated quotes, out-of-scope people, "not recognized" under unknown coverage and invalid action triggers are all withheld. Tested with synthetic bad model outputs.
3. **Subject and routing.**
   - Exact, ambiguous, unknown, out-of-scope, two-to-five-people and more-than-five cases give the right result.
   - On a fixed question set with recorded plan outputs:
     - Discovery runs on every in-scope question.
     - "How are we doing compared with Customer Renewals?" and a question about another team's person are rejected as `declined` without reading evidence.
     - "Who on my team helped Customer Renewals?" is processed with Customer Renewals as the beneficiary focus.
   - Name matching ignores accents and case. An unresolved name gives a clarification, not a stop. "Compared with last quarter" is processed as a team question.
   - Clarification: an ambiguous name produces `missing_field = "subject"`. The follow-up request with the original question plus the choice keeps the intent and the period ("recognize", "this quarter"), and processes only the chosen person. The chosen ID is used even when the second plan writes the name differently.
4. **Follow-up.**
   - P1's A1 and A4 are observed, and P3 is not yet.
   - A `proposed` action gets no follow-up result; it shows "pending decision".
   - An empty table under complete coverage gives not yet. Partial coverage gives unknown, tested with a case built by code: an **accepted A4** from one of M41's automatic plants, with no later share, against the named `partial` row (M41, `HR_recognition_feedback`, 2026-Q3) gives `unknown`. A4 is used because the plant has partner praise, so A2's trigger does not apply. The case does not wait for the model to propose the action.
   - A3 matches only `Topic_Code = workload`.
   - The follow-up scope cannot add a person outside the roster frozen at the as-of date.
5. **Regression offline.** The legacy import profile and the existing test suite still pass after five-role fixtures are updated.
6. **Audit cases.**
   - `no_candidates` and `no_findings` are reported separately, with coverage.
   - Failures never read as "no hidden work".
   - A July recognition does not hide P1's June finding. A July share reads as not shared on June 30.
   - On `discovery_v1`, any `start_date` or `end_date` other than the fixed range is rejected by both the backend and the CLI.
   - No external person's name appears in the Discovery section, except the partner manager in the recipient field of their own A2 or A4 draft.
   - Original's released answer is byte-identical to the reviewed candidate. It is never redacted after review, and its privacy behavior is today's.
   - The 8-item selection keeps the closing context for D1 and D3.
   - The section:
     - is present for every status and matches the checked result exactly. When Discovery did not run (a rejection or a clarification), it is `{present: false, status: "not_run", finding_ids: []}`;
     - is reset at the start of every `run()`, so a second question never carries the first one's section;
     - reaches the manager page: a test against `/api/runs/{id}?view=manager` finds it, not only the artifact;
   - The manager page shows six agents in a run with Discovery.
   - A declined out-of-scope question, through the manager projection:
     - shows the message, plus a "Why" card with the guardrail's `rule` and `detail` and two next steps;
     - the projection's `guardrail` object has `checked_by: "code"`, never "ZeroSugar". The card itself shows only `rule` and `detail` ([Brief.tsx:271-273](../Echo_UI/frontend/src/manager/Brief.tsx)).
     - holds at most 5 findings with drafts plus at most 5 one-line findings;
     - has a pointer line whose count equals the findings shown, and no count when there are none;
     - is published when Original's answer fails;
     - carries `discovery_section` with `reviewed_by_zerosugar: false` in the result and in the export.
   - Original's compose input contains no Discovery content, and ZeroSugar's input matches the `review-v8` contract.
   - Correction rounds never call Discovery again.
   - Work references: a different ID on the same work closes A1, and an edit cannot add a foreign reference.
   - Budget:
     - After a `DiscoveryTimeout`, a provider failure or a schema failure, `remaining()` equals a run without Discovery.
     - Discovery makes at most 2 logical calls, even when network retries occur.
     - The raw `models` count minus the `request_transport_retry` events equals the number of `request_costs`, and the refund appears only in the separate fields.
     - After the refunds, Original's remaining calls, closing turn and seconds equal a run without Discovery.
     - A `DiscoveryTimeout` gives `failed_budget` and the run continues.
     - With no budget left before the schema retry, Discovery spends no call.
   - The scorer and the report reader find P1-P6 through `discovery_section`.
   - `answer` never contains the section, and the reviewed candidate's identity matches the released answer.
   - The section survives in the failure artifact when Original fails.
   - A run that exhausts its budget after Discovery still completes Original's closing turn.

**Live**, which needs explicit authorization:

7. **Findings.** Discovery finds P1-P6 in the M32 and M14 team questions.
   - None of D1-D8 is reported as a hidden-work gap in those team questions.
   - D8 is checked separately: a question about that person directly should find it.
8. **Subjects.** Beneficiary team and team-versus-person are correct.
9. **Actions.** Each action type fits its finding, and there are zero claims about engagement, retention or productivity.
10. **Smoke test of the existing hard question.** One run with Discovery active. It completes, and `discovery_applied` is recorded. With n = 1 and today's completion rate (about 59%), this is a smoke test, **not** a regression measurement. Measuring regression would need repeated runs, which are requested explicitly if wanted.
11. **Planning benchmark M3 rerun.** The plan's instructions and schema change, and every earlier planning change re-ran M3. This one does too:
    - the documented floors hold (test 18, Gemini 17);
    - P12 and P13 still ask for clarification in all 8 runs.
    - **If it fails:** first fix the planning instructions and rerun. If the floors still fail, move subject identification to a separate small call, as in v5, and restore `plan()` to its current schema. Discovery is not reverted.

Live design: two workflows per manager context, M32 and M14, each with and without Discovery, so four in total. Add the smoke run (gate 10) and the M3 rerun (gate 11). All use one frozen pack and the GW API profile. Report recall, rejected decoys, correct actions, tokens, calls, latency and `discovery_applied`. These runs demonstrate behavior; they do not rank quality.

## 9. Sequence

1. Approve v9 and the rule change; freeze the schema and stories. The plan is frozen from here on.
2. Generator, `files_discovery_v1/`, importer profile, validated database; offline token count of the pool.
3. Discovery: prefilter, judgment, checks, section rendering, `RunBudget.refund`, `DiscoveryTimeout`; offline gates 1-3.
4. Original integration (plan fields, subject check, Discovery step, refund, release section), date and clarification transport, actions store, follow-up, UI; offline gates 4-6.
5. Demo candidate.
6. Authorized live runs (gates 7-11).
7. Contingency and presentation.

If time runs short, cut follow-up for A5 and A6, the M14 live pair and UI polish first. Do not cut Discovery's judgment, the hand-built stories (including P5), the automatic plants, or follow-up for A1, A2 and A4.

## 10. Decisions

| ID | Question | Decision |
| --- | --- | --- |
| Q1 | Does ZeroSugar review Discovery content? | **User:** no. In v7, Original receives nothing from Discovery and code writes the pointer, so nothing Discovery-related reaches review (3.5) |
| Q2 | Who enters the team-question pool? | **User:** the 10 least satisfied plus up to 5 with the strongest signals (3.3) |
| Q3 | Background data scope | **User:** whole organization, weekly grain, templated |
| Q4 | Discovery's model | **User:** the same GW model as Original. It has its own profile entry; the per-call cap is 120 s (each request gets the time left) and the profile's 135 s timeout is a backstop, both set from measured latency (3.6, Errata 5 and 6) |
| Q5 | Does Cherry's `cross_team_contributions` metric stay? | **User:** yes |
| Q6 | Rafay's `data_extensions` side project | **User:** required as P5 in M14 (5.6) |
| Q7 | Satisfaction measure | **User:** a confidential individual 1-5 pulse per quarter |
| Q8 | Which managers get plants | **User:** hand-built for M32 and M14; automatic for all 60 (5.7) |
| Q9 | How Original calls Discovery | **User:** the planning step identifies the subject, and Discovery runs once as a step in the existing workflow. There is no new workflow (3.1) |
| Q10 | How findings reach the manager | **User:** in a separate Discovery section at the end, which ZeroSugar does not evaluate; built by code so it cannot be dropped (3.5) |
| Q11 | How many findings | **User:** at most 5 with drafts. v8 adds at most 5 more as one-line entries; any beyond that are only counted (3.4) |
| Q12 | How people are described | **User:** "prioritized for review", never a ranking (5.6) |
| Q13 | Budget for Discovery | **User (v7):** Discovery has its own 2-call cap and time limit, and its actual use is refunded, so Original keeps today's budget (3.6) |
| Q14 | Where the as-of date comes from | **User (v7):** the `end_date` that the UI and CLI already send. It is explicit on `discovery_v1` and never later than the configured as-of (3.2) |
| Q15 | What a clarification keeps | **User (v7):** the new run receives the original question plus the chosen person (3.2) |
| Q16 | Planning benchmark | **v7:** re-run M3 with its floors and the P12/P13 clarification check (gate 11) |
| Q17 | When does Discovery run? | **User (v8):** on every in-scope question. There is no `needs_discovery` flag (3.1) |
| Q18 | Questions about other teams | **User (v8):** rejected, including comparisons. A partner team named only as the beneficiary of the manager's team's help is allowed (3.2) |
| Q19 | Clarification matching | **v8:** the chosen employee ID is applied directly, never by name matching (3.2) |
| Q20 | Beneficiary focus | **User (v9):** finding who helped the named team governs the pool and the evidence (3.3) |
| Q21 | Unresolved names | **v9:** accent- and case-insensitive matching, then a clarification. A run stops only for a name that resolves outside the team (3.2) |
| Q22 | Baseline window | **v9:** inside the analysis window; no history read (3.3) |
| Q23 | M3 failure | **v9:** fix the instructions, then fall back to a separate subject call (gate 11) |
| Q24 | Cost per question | **User (v9):** accepted and measured afterwards (§2, decision 25) |
| Q25 | Follow-up for undecided actions | **User (v9):** none; only accepted or edited actions are followed up (6.3) |

The task list, contracts and suggested models are in [WORK_BREAKDOWN_DISCOVERY.md](WORK_BREAKDOWN_DISCOVERY.md).

## 11. Authorization register

| Action | Status |
| --- | --- |
| Write v9 (final) and update current-document pointers | Done in this documentation task |
| Sixth role and guidance changes in [AGENTS.md](../AGENTS.md). Proposed wording: Discovery findings are checked by code and not corrected by ZeroSugar; the Discovery section is appended after review and marked as not reviewed; Original's text keeps both reviews; old-run replay is not required for Discovery | Requires explicit user approval |
| New data pack, generator, importer profile, Discovery agent, `RunBudget.refund`, Original changes, date and clarification transport, actions store, UI | Proposed; requires implementation approval |
| Refunding Discovery's actual use to the run budget, in separate fields (3.6) | User decision 2026-11-15 |
| Offline tests during approved implementation | Specify with that scope |
| Live runs (gates 7-11, including the M3 rerun) | Proposed; requires explicit authorization |
| Other budget or provider changes, Git publication, real employee data | Not authorized by this plan |

## 12. Changes from v8

Earlier changes are listed in [v6 §12](DISCOVERY_SCOPE_AND_PLAN_v6_2026-11-15.md), [v7 §12](DISCOVERY_SCOPE_AND_PLAN_v7_2026-11-15.md) and [v8 §12](DISCOVERY_SCOPE_AND_PLAN_v8_2026-11-15.md).

Design-level decisions from the fifth audit and the user's last two observations:

| Observation | v8 | v9 |
| --- | --- | --- |
| A beneficiary focus does not reach evidence selection | Undefined | The focus governs the pool and the evidence; gate 1 checks it reaches the model (3.3) |
| Follow-up for `proposed` actions | Undefined | None. Only accepted or edited actions; the decision date is the decision's (6.3) |
| A hard subject filter kills legitimate questions | An unknown name stopped the run | Accent- and case-insensitive matching, then a clarification. A run stops only for a name resolved outside the team (3.2) |
| No baseline window for workload and repetition | 104 generated weeks that the scope could not read | Baselines inside the analysis window. New tables cover only the analysis and follow-up windows (3.3, 5.4) |
| Gate 11 had no failure rule | Informative only | Fix the instructions, then fall back to a separate subject call (gate 11) |
| D8 versus gate 7; P5 for other managers | Contradictory; no gate | Gate 7 checks D8 separately; P5's other managers are covered offline by gate 1 |
| Mandatory cost | Implicit | An accepted decision, measured afterwards (decision 25) |

Contract-level corrections written into the plan:
- Discovery's result lives in `AgentResult.discovery`, not in `child_results`.
- The section lives in `discovery_section.rendered`, never in `answer`.
- Every budget enforcement point uses the effective values.
- `respond()` accepts a per-call deadline.
- Coverage precedence: row level for findings, table level for follow-up.
- The section carries its further-findings list and the period line.
- The pointer counts findings, not "contributions".
- Plant precedence in M32 and M14.
- Corrected `OP_team_goals` and `OP_goal_outcomes` counts.

The remaining implementation notes from the fifth audit are acceptance criteria in [breakdown §12](WORK_BREAKDOWN_DISCOVERY.md). They are: the duplicated `missing_field` enum, the recording key including the clarification, `resume.py` semantics and panels outside the run.

## 13. Evidence and limits

Checked by the parent session on 2026-11-15, read only:
- `plan()` and its key-set validation (`original.py:162-265`, 227);
- the plan-before-delegation order (`original.py:1028-1043`);
- the two-entry delegation map (`original.py:631`);
- `RunBudget` (`runtime.py:97-138`);
- the answer limits (`grounding.py:20-21`);
- the roster: 2,500 employees, 60 managers, 10 to 85 people per team, and 5 teams with 15 or fewer people.

Added for v7:
- the absolute deadline and the run-ending error (`runtime.py:110, 203-210`);
- the closing threshold (`runtime.py:306`);
- the `Specialist` loop (`runtime.py:302`);
- the `missing_field` enum (`original.py:182`);
- Cherry's prepared metrics inside `delegate()` (`original.py:366-379`);
- `REVIEW_VERSION = "review-v8"` (`zero_sugar.py:26`);
- the UI date transport (`ManagerApp.tsx:440`, `app.py:338, 396, 454`).

Added for v8:
- network retries calling `consume("model")` (`runtime.py:155-161`);
- the shared deadline error (`request_pacing.py:20`);
- the resume arithmetic (`resume.py:222`).

Added for v9 (spot-checked by the parent session):
- `check_handoff` and its `evidence_handoff_coverage` error (`original.py:1140-1145`);
- `child_results` appended in `delegate()` (`original.py:398, 409`);
- Original workflows not resumable (`original.py:427-428`);
- the raw checks in `consume()` (`runtime.py:109-113`);
- the scope-date filter in `employee_rows` (`data_access.py:64-72`);
- `recording_key` (`app.py:351`).

The other line references in the fifth audit are taken from the auditor and are confirmed during implementation.

v5's evidence list still applies to the earlier checks. The median-scope counts and the 715k-token figure are agent-reported. The Discovery token figures are arithmetic floors, not measurements. Line numbers can drift; current files govern.

No runtime implementation, data generation, database change, test, build, live call or publication was performed.

## 14. Errata (1 to 6)

### Errata 1 (sixth audit, 2026-11-15)

These fix contradictions and contract gaps in the frozen plan. The design is unchanged.

| Observation | Correction |
| --- | --- |
| `Record_Coverage` today makes every finding "partial" | It is regenerated as `complete \| partial` per feedback row in the pack (5.4) |
| §3.1 still stopped the run on an unknown name | One rule: unresolved → clarification; identified outside the team → rejection (3.1) |
| The section's survival on failure had no mechanism, and the old note named `run_agent.py` | Original catches every error and returns `incomplete()`, so the join point is `run()` itself, covering every exit including `incomplete()` (7, breakdown §12) |
| Clarification had no candidate list or transport field | `AgentResult.clarification_candidates` from the roster; the manager view passes it through; `RunRequest.clarification`, validated against the roster (3.2) |
| Privacy replacement on Original's answer breaks the reviewed identity | The replacement is limited to the Discovery section. Original's answer is never modified after review (3.5) |
| Quotes versus placeholders | Quotes are checked against the pool's visible text, and that same text is published (3.5) |
| Saved plans fail the exact key set | `setdefault` defaults for the four new fields (7) |
| A stop had no result shape | Rejections and clarifications are normal `AgentResult`s with their message (3.1) |
| A 60 s per-call limit sat above the 45 s profile timeout | ~~Discovery's own profile timeout, starting at 90 s, is its per-call limit~~ **Superseded by Errata 2, then Errata 3:** the limit is 120 s under a 135 s profile timeout, set from a measured latency. `run_seconds` is stated per run (3.6) |
| Original can contradict the section | Recorded as an accepted known limit (3.1) |
| `OP_source_coverage` was also said to decide recognition states | Follow-up only (5.4) |
| Plant split | About 63 through low satisfaction and 57 through strong signals; the totals are unchanged (5.7) |
| Line reference for the clarification return | 1032-1037 |

### Errata 2 (seventh audit, 2026-11-15)

The design is unchanged.

| Observation | Correction |
| --- | --- |
| The refund missed the failure and timeout paths | The refund runs in `finally` for every logical call; a gate checks `remaining()` after a timeout (3.6, gate 6) |
| The section did not reach the manager page | `discovery_section` is added to the manager-view allow-list (`app.py:514-541`); the gate tests `/api/runs/{id}?view=manager` (7, gate 6) |
| `out_of_scope` existed in no layer | Rejections reuse `declined`, which every layer already shows, with `reason_code = subject_out_of_scope` (3.1) |
| The privacy gate could not pass because of Original's existing text | The gate covers the Discovery section; a separate gate checks that Original's answer is byte-identical to the reviewed candidate (gate 6) |
| Stories' feedback rows could fall in the 5% `partial` | Every feedback row cited by P1-P6 or a plant is `complete`, checked by the build QA (5.4) |
| "Not recognized" with several rows or none | All cited rows are `complete`, plus declared coverage for the absence of recognition events (3.5) |
| The per-call limit equaled the transport timeout | 80 s per call under a 90 s profile timeout. **Superseded by Errata 3:** 120 s under 135 s, from a measured latency (3.6) |
| Q4 and §7 said "same GW profile" | The same GW model with its own profile entry (Q4, 7) |
| `discovery_section` had no "not run" shape and no reset | `{present: false, status: "not_run"}`, reset in `run()` (gate 6) |
| "300 seconds" without "by default" | Marked as the CLI default (3.6) |
| "Frozen" next to errata | "Frozen except for errata" (header) |

### Errata 3 (eighth audit, 2026-11-15)

The design is unchanged.

| Observation | Correction |
| --- | --- |
| The `declined` rejection was half-specified for the Brief's "Why" card | Full result specified: `task_outcome`, `verification` with `drafts_checked: 0`, `guardrail` with `checked_by: "code"`, and two `next_steps`. The offline declined artifact is not copied (3.1, gate 6) |
| The stage was said to come from `AgentResult.discovery` | The stage is event-driven, from `agent="Discovery"` events. A gate checks six agents on the manager page (3.1, gate 6) |
| 80/90 s was not based on measured latency | 120 s under 135 s to start, set from a measured latency. A latency `failed_budget` in gate 10 is a failure to investigate (3.6) |
| Random `partial` rows in `OP_source_coverage` could hit the stories | All rows are `complete` except one named test row, M41 `HR_recognition_feedback` 2026-Q3 (5.4) |
| An obsolete timeout row in Errata 1 | Marked as superseded |
| The §7 checklist still said "after each call" | The refund runs in `finally` |
| The headings hid Errata 2 | Headings for Errata 1, 2 and 3 |
| The pointer count versus `finding_ids` | The pointer counts detailed plus one-line findings, and `finding_ids` covers both (3.5) |

### Errata 4 (ninth audit, 2026-11-15)

The design is unchanged.

| Observation | Correction |
| --- | --- |
| The 120/135 s pair did not behave as described | Echo's deadline is a boundary check. 135 s, the transport timeout, is the real per-call cap; 120 s only stops a further attempt, and it does so before the backoff instead of after it. A late correct response is used. The worst cases are about 135 s for one hung call and about 270 s with a schema retry. Errata 2's and 3's claims about which error appears for which pair are withdrawn (3.6). **Superseded by Errata 5:** each request's timeout is the time left before 120 s, so 120 s is the real cap |
| Gate 4's `partial` case was not named | An accepted A4 from an M41 plant, built by code, with no later share, gives `unknown` (gate 4) |
| The "Why" card does not show `checked_by` | The gate checks the projection's `guardrail` object; the card shows `rule` and `detail` (gate 6) |
| Found while applying this errata: the 135 s cap assumed no SDK retry | Discovery's profile sets `max_retries: 0`; the SDK default of 1 would double a hung call to about 270 s (3.6, T3.4) |
| The 45 s note could be read as Discovery's timeout | Marked as a reference to the other agents' profiles (3.6) |
| The breakdown's §12 omitted `finding_id` in one-line findings | Fixed in the breakdown |
| The pointer headings still said "final, frozen" | Changed to "frozen except for errata" |

### Errata 5 (tenth audit, 2026-11-15)

The design is unchanged.

| Observation | Correction |
| --- | --- |
| "Raw `models` equals the number of `request_costs`" is false after a network retry | `models` minus the `request_transport_retry` events equals the number of `request_costs` (3.6, gate 6, T3.6) |
| A permitted retry could run to about 255 s, because the 135 s client timeout restarts per attempt | Each request's timeout is the time left before the 120 s limit, passed per request. A logical call ends by about 120 s; about 240 s per question with the schema retry (3.6, T3.6) |
| The timeout was still "sized for an 18-20k-token input" in two places | Removed; measured latency sets it (3.6, T3.4) |
| The §7 checklist omitted `max_retries: 0` | Added (7) |
| One request deadline cannot tell Discovery's limit from the run's | Inside Discovery both give `failed_budget`; outside, the run-level `RuntimeError` keeps its meaning (3.6, T3.6) |
| "Paced with Echo's existing pacing" had no profile behind it | Discovery is not paced, like today's GW profile; a 429 gives `failed_provider`, refunded. A pacing interval is decided from gate 10 (3.6, 4) |

### Errata 6 (eleventh audit, 2026-11-15)

The design is unchanged.

| Observation | Correction |
| --- | --- |
| A refused retry is counted but never recorded, so the call-count check failed on its own test | `consume("model")` moves after every check that can refuse a retry; a refused retry is neither counted nor recorded (3.6, 7) |
| The per-request timeout had no stored profile cap and would have changed every agent's timeout | The model object stores `request_timeout`; the per-request timeout is passed only when Discovery sets a per-call deadline (3.6, 7) |
| "Under the CLI's 300 s" read as a wall-clock cap | The refund extends the run: wall clock up to about `run_seconds` + 240 s. Gate 10 judges the budget (3.6) |
| §7 had no row for `agents/model.py` | Added (7) |
| Q4 still credited the pair to Errata 3 | Q4 states the 120 s cap and 135 s backstop (Q4) |
