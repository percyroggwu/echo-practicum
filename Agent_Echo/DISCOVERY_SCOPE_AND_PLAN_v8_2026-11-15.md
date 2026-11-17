# Echo Discovery v8: proactive discovery of hidden cross-team work

Date: 2026-11-15. Status: proposed plan; documentation only. No runtime code, data, database or provider call was changed or made.

**Superseded on 2026-11-15 by [v9 (final)](DISCOVERY_SCOPE_AND_PLAN_v9_2026-11-15.md).** Kept as history. It superseded [v7](DISCOVERY_SCOPE_AND_PLAN_v7_2026-11-15.md), [v6](DISCOVERY_SCOPE_AND_PLAN_v6_2026-11-15.md) and [v5](DISCOVERY_SCOPE_AND_PLAN_v5_2026-11-14.md). It resolves the fourth audit's observations together with the user's decisions on them (section 12). Earlier history is kept in [v4](DISCOVERY_SCOPE_AND_PLAN_v4_2026-11-14.md), [v3](DISCOVERY_SCOPE_AND_PLAN_v3_2026-11-12.md), [the seven reviews](DISCOVERY_SEVEN_REVIEWS_2026-11-12.md), [v2](DISCOVERY_PLAN_v2_2026-11-11.md), [the review synthesis](DISCOVERY_REVIEW_SYNTHESIS_2026-11-11.md) and [the brainstorm](DISCOVERY_BRAINSTORM_AND_PLAN_2026-11-10.md).

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

3. **Subject check (code), right after `plan()`.** Code resolves the names and the period (section 3.2). This happens before `set_delegations`, in the same place where the plan's existing clarification return already sits ([original.py:1031-1036](agents/original.py)).
   - **Ambiguous name.** It uses that existing clarification return, which is the only clarification mechanism.
     - `clarification_basis.missing_field` gains the value `"subject"`. Today it allows only `manager_id`, `start_date`, `end_date`, `metric`, `task` and `other` ([original.py:182](agents/original.py)).
     - The name as the manager wrote it is the `request_excerpt`, which is a literal substring of the question.
     - Nothing is cached. The manager's answer starts a new run that keeps the original question (section 3.2).
   - **Out of scope.** A person or team outside the manager's scope, an unknown name, or a period outside the authorized dates stops the run with a message. No evidence is read.
4. **Discovery step (always).** `"Discovery"` is added to the delegation map ([original.py:627-631](agents/original.py)) and to `planned_roles` ([original.py:1039-1043](agents/original.py)).
   - **A new code path.** Right after `set_delegations`, `workflow()` calls Discovery **once**, before the drafts loop. There is no precedent at this point. Cherry's prepared metrics run inside `delegate()` ([original.py:366-379](agents/original.py)), when Original's model chooses to call Cherry. This step is new, and it is a code call, so no model can skip it.
   - **Called once.** The result is kept for the whole run. Repair and correction rounds never call Discovery again.
   - **What it runs.** The prefilter (3.3), its single judgment call (3.4) and the code checks (3.5).
5. **Original composes** its normal answer, exactly as today. It may ask Cherry for metrics and Vanilla for sentiment, so a team question still gets team metrics.
   - **What Original does not receive.** No Discovery findings and no `DISC-*` IDs. Its fact catalog and its limits (24 cited facts and 12 narrative items, [grounding.py:20-21](agents/grounding.py)) are unchanged, so Discovery uses none of those slots.
   - **Known side effect.** Original may independently propose something similar to a Discovery action, such as recognizing the same person. That is accepted.
6. **ZeroSugar** reviews Original's answer in both phases, as today. Its input and contract (`review-v8`) do not change.
7. **Release.** Code appends the **Discovery section** (3.5) after Original's reviewed answer.
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
| Nobody with that name exists | Say so; do not guess |
| The question names nobody | The subject is the manager's whole team (section 3.3 pool) |

Code never widens the roster or the dates. A partner team can appear only as the beneficiary of the manager's own people, never as a subject. Only an out-of-scope **subject** stops the run; a beneficiary focus never does. Gate 3 covers both question types.

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
1. The run ends with the clarification and the candidate list: name, team and ID for each.
2. The new request carries the **original question unchanged**, plus the manager's choice: `clarification: {"name_as_written": "Isabel", "employee_id": "E0xxx"}`.
3. A new run starts; the earlier one is not resumed. `plan()` reads the full original question again, so "recognize" and "this quarter" are kept.
4. **The chosen ID wins, without matching names.** The second plan may write the name differently, for example "Isabel García" or "Isabel G.". So when `clarification.employee_id` is present:
   - If the plan resolves to a single person, `resolve_subject` uses that ID directly.
   - If the plan names several people, the ID replaces the one name that matches several roster entries.
   - In both cases the ID must still be in the manager's team, or the run stops as out of scope.

The backend accepts the `clarification` field only together with a question, and the UI sends it from the clarification card.

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
- Every quote is an exact substring of its source.
- Every person is in the authorized roster, and every team and date is inside the analysis window.
- "Not recognized" is impossible when recognition coverage is partial or unknown.
- Every suggested action type is in the catalog and its trigger fits the finding. For example, A1 is not allowed when the finding is already recognized.
- **Privacy:** nothing shown to the manager names a person outside the manager's team or gives their ID. This applies to quotes, summaries, Original's answer and drafts. Code checks every release against the organization roster, replaces any leak with the placeholder, and counts it in the log.
  - **The one exception** is an allow-list entry per draft: `(action_id, partner_manager_id)`. It applies only to the recipient field of that A2 or A4 draft.
  - The same manager anywhere else, including in the draft body, is still replaced. A release-wide exception would either over-redact the recipient or under-redact everything else.

A finding that fails a check is withheld and recorded, not repaired. Discovery is not added to ZeroSugar's correction owners ([zero_sugar.py:103](agents/zero_sugar.py)).

**The Discovery section.** Code builds it from the checked result and appends it after Original's answer. It contains:
1. **A pointer line, written by code from the status.** The count can never exceed the findings shown.

   | Status | Pointer line |
   | --- | --- |
   | `findings`, `partial` | "Discovery found N contributions to other teams." N is exactly the number of findings shown |
   | `no_candidates`, `no_findings` | "No hidden-contribution findings in the selected evidence", followed by the coverage |
   | `all_withheld` | "Discovery could not produce verifiable findings" |
   | `failed_provider`, `failed_budget` | "Discovery could not complete the analysis", with the reason |

2. Up to 5 findings, each with its work summary, beneficiary team, why it matters, recognition and visibility state, quotes and source IDs.
3. For each finding, its action drafts, rendered from the fixed template for each action type (6.2) and filled only from the finding's fields.
4. One line per further finding (3.4).

Because code writes both the pointer and the section, neither can be omitted, reworded or invented by Original. The drafts add no claim that is not already in the finding.

**Provenance is marked.** The section is appended after review, so it is not part of `candidate.findings`, `release_counts` or the grounding check. The result therefore carries its own field:
- `discovery_section: {present, status, finding_ids, reviewed_by_zerosugar: false, checked_by_code: true}`;
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

**Budget.** Today `RunBudget` allows 32 model calls and 300 seconds per run ([runtime.py:97-138](agents/runtime.py), [original.py:433-434](agents/original.py)). Two facts rule out simply raising the limit:
- **The time limit is an absolute deadline.** It is fixed when the budget is created, there is no method to extend it, and exceeding it raises `RuntimeError` ([runtime.py:110](agents/runtime.py)). That error ends the whole run as `AgentRunError` ([runtime.py:203-210](agents/runtime.py)).
- **Agents close on an absolute threshold.** They begin closing when `remaining()["model_calls"]` drops to 2 for Original or 3 for the others ([runtime.py:306](agents/runtime.py)). A higher fixed limit would give Original extra turns on every question.

Two more facts matter for Discovery:
- **Network retries consume calls.** Inside `RunBudget.respond`, every transient network retry calls `consume("model")` again, with up to 3 attempts ([runtime.py:155-161](agents/runtime.py)). Rate-limit (429) retries happen inside the provider adapter and do not consume calls ([model.py:77-97](agents/model.py)).
- **There is no Discovery-specific timeout.** `check_request_deadline()` and `consume()` raise the same `RuntimeError("Workflow elapsed-time budget exceeded.")` ([request_pacing.py:20](agents/request_pacing.py), [runtime.py:110](agents/runtime.py)).

v8 therefore uses **Discovery's own cap, its own timeout and a refund recorded in separate fields** (user decision 2026-11-15):
1. **Own cap of 2 logical calls:** the judgment and one schema retry.
   - The network retries of a logical call belong to that call. They are all refunded with it, so they never count against the cap or the run.
   - Each logical call has its own time limit, 60 s to start. T4.6 recalibrates it from measured sizes.
2. **A check before every call**, including the schema retry and each network retry. If the run's remaining calls or seconds cannot cover the call, Discovery returns `failed_budget` without calling. `consume()` can therefore never raise a run-ending error inside Discovery.
3. **Own timeout exception.** A new `DiscoveryTimeout` class is raised by `check_request_deadline()` when the request runs inside Discovery and Discovery's own limit is reached. Discovery catches only that class and returns `failed_budget`. The run-level `RuntimeError` keeps its meaning.
4. **Refund after every call, without changing the raw counters.** `RunBudget` gains two fields, `refunded_models` and `paused_seconds`:
   - `remaining().model_calls = model_limit - models + refunded_models`;
   - the effective deadline is `deadline + paused_seconds`.

   `models` still counts every real call and matches the `request_costs` in the same artifact, and the original deadline is kept. `snapshot()`, `workflow_budget` and captures show the raw counters and the two refund fields side by side. `resume.py` keeps its current arithmetic on the raw values ([resume.py:222](agents/resume.py)) and adds the refunds explicitly.
5. **Effect.** Original and ZeroSugar see exactly the budget they would have had without Discovery: the same remaining calls, the same closing points and the same seconds. The with/without comparison (gate 10) is not affected by budget.

**Retries.**
- **Network errors:** at most 2 retries per logical call, as today. They consume calls, but they are refunded.
- **Rate limit (429):** handled inside the provider adapter, with no call consumed.
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

These figures are **floors from arithmetic, not measurements**. Before any live run, the prefilter output for M32 and M14 is counted with the provider's tokenizer offline (T2.5). GW's rate limit of about 50k tokens per minute was already exceeded once (run 6: 110k in 73 s). The judgment call is therefore paced with Echo's existing pacing, and its measured size sets the seconds allowance in 3.6.

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

Background rows cover all 2,500 employees over 2024-10-01 to 2026-09-30. Hand-built stories are planted in M32's and M14's teams (5.6), and automatic plants in every team (5.7). Counts are construction targets; the manifest records exact numbers.

| Table | Grain and key fields | Target rows | What it enables |
| --- | --- | --- | --- |
| `OP_team_goals` | One team goal per quarter: ID, team, owner manager, metric, target, due date | ~1,200 | Links help to the beneficiary's goal |
| `OP_goal_outcomes` | One goal measurement: value, numerator/denominator, measured at | ~5,000 | Goal met or missed |
| `OP_collab_threads` | One cross-team request thread: opened at, requesting team, requester, topic, optional work request | ~25,000 | Help that never became a formal request |
| `OP_collab_messages` | One message: thread, author type/ID, sent at, text, mentions | ~120,000 | Who asked, who answered, who was thanked |
| `OP_dependency_blockers` | One blocker: raised at, blocking team, blocked goal, resolved by, resolved at, days blocked | ~6,000 | Unblocking another team |
| `OP_incident_handoffs` | One incident or handoff: severity, responders, owning team, start/end, notes | ~3,000 | Firefighting and after-hours help |
| `OP_meeting_mentions` | One line of another team's notes: date, team, mentioned employee, text, optional work anchor | ~15,000 | Thanks where the home manager is absent |
| `HR_recognition_events` | One formal recognition: given by, visibility, type, one typed anchor, event date | ~4,000 | "Praised" versus "recognized"; follow-up for A1 |
| `OP_activity_weekly` | One employee-week: cross-team hours, after-hours minutes, meeting hours | ~260,000 (2,500 × 104 weeks) | Workload signal, repetition, and the team's normal range |
| `HR_employee_performance` | One employee per quarter: confidential pulse score (1-5), engagement, performance rating, goal attainment %, recorded date | ~20,000 (2,500 × 8 quarters) | Feeds `lowest_satisfaction` |
| Reused `HR_goals` | Individual goals from `data_extensions` | 12,670 | Inside or outside the person's goals |
| Reused `HR_self_review_items` | December 2025 self-review items from `data_extensions` | 12,129 | The employee's own account |
| `HR_one_on_ones` | One 1:1: manager, employee, date, **`Topic_Code`** (`workload`, `career`, `performance`, `recognition`, `other`), free-text notes | ~2,000 | Follow-up for A3, matched on `Topic_Code = workload` |
| `HR_review_notes` | One review note: employee, cycle, author, cited work anchor, date | ~1,000 | Follow-up for A5 |
| `OP_team_plans` | One planning item: team, partner team, item text, date | ~800 | Follow-up for A6 |
| `OP_source_coverage` | One row per source table × home team × quarter: `complete` or `partial`. The home team is the manager's team that owns the employees; beneficiary teams declare nothing. Seven tables declare coverage: `HR_recognition_feedback`, `HR_recognition_events`, `HR_one_on_ones`, `HR_review_notes`, `OP_team_plans`, `OP_meeting_mentions` and `OP_collab_messages` | ~3,400 (7 × 60 × 8) | Decides `not_yet` versus `unknown`, and "unknown" recognition states |

Columns added to the copied tables:

- **`HR_recognition_feedback`:**
  - `Interaction_At` (the real event date), `Author_Type` and a nullable `Contribution_ID`;
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
| History | 2024-10-01 to 2025-09-30 | Background and repeat patterns |
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
  - Half the people are among their team's 10 least satisfied.
  - The other half enter only through strong signals. These are placed only in the 55 teams with more than 15 people, because in smaller teams the pool is the whole team and the slot filters nothing.
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
| `agents/runtime.py`, `agents/request_pacing.py` | <ul><li>`RunBudget.refund(models, seconds)`, which adds to `refunded_models` and `paused_seconds` without changing `models` or `deadline`.</li><li>`remaining()` and the effective deadline use the two refund fields.</li><li>Network retries inside a Discovery call are attributed to that call.</li><li>A new `DiscoveryTimeout`, raised by `check_request_deadline()` within Discovery.</li><li>The refund fields in `snapshot()`.</li></ul> |
| `agents/original.py` | <ul><li>Plan schema: four new fields and the key-set update (162-265). There is no `needs_discovery` flag.</li><li>`"subject"` added to the `missing_field` enum (182).</li><li>`resolve_subject` right after `plan()`, before `set_delegations` (1028-1038).</li><li>`"Discovery"` in the delegation map and `planned_roles` (627-631, 1039-1043).</li><li>The new Discovery step, which always runs before the drafts loop, with a refund after each call.</li><li>The section and the `discovery_section` field at release, with the release check. The section is also published when Original's answer fails.</li><li>Stop messages for out-of-scope subjects (including comparisons with another team) and not-found subjects.</li><li>The clarification ID applied directly.</li><li>Nothing from Discovery reaches the compose step.</li></ul> |
| `agents/policies.py` | Discovery role text, plus the planning rule for `subject_names` versus `focus_hint` (a team asked about or compared against goes in `subject_names`; a beneficiary-only team goes in `focus_hint`) |
| `agents/grounding.py` | No change: Original cites no Discovery IDs |
| `agents/zero_sugar.py` | No change. Its input and `review-v8` contract stay the same, because the section is appended after review. Discovery is not in `OWNERS` |
| `agents/data_access.py` | Projections over the new tables; as-of = `end_date`, explicit on `discovery_v1`; `FollowUpScope` for the follow-up endpoint only |
| `agents/connections.py`, `connections.json` | Discovery model profile, the same GW profile as Original |
| `agents/resume.py`, `capture.py`, `execution_log.py`, `run_agent.py`, `check_release.py`, `__init__.py` | Sixth-role registration; capture of the call and the refund; `discovery_applied`; CLI `--database`, with `--end` mandatory on `discovery_v1`; a `clarification` argument; the export shows the section's provenance |
| `import_data.py`, `files_discovery_v1/`, generator | Section 5 |
| `.claude/agents/report-reader.md`, `score_discovery.py` (new) | Read `discovery_section` from the result. Findings are not in `candidate.findings` or `verification.reviews`, so a reader that skips the field would report "found nothing" |
| UI backend `app.py`, `offline.py` | Database selection; the fixed range on `discovery_v1`, where any other `start_date` or `end_date` is rejected; the `clarification` field passed to the run; actions store; follow-up endpoint; offline fixtures |
| UI frontend | <ul><li>A fixed, read-only date range for `discovery_v1`.</li><li>A clarification card that resends the original question with the choice.</li><li>Sixth agent on stage.</li><li>A Discovery section with its provenance label, typed action cards, decision buttons, follow-up badges and a simulation label.</li><li>No subject selector.</li></ul> |
| Tests | Section 8 gates; update fixtures that assumed five roles |

## 8. Evaluation and gates

**Offline, zero tokens:**

1. **Pool recall.** The prefilter's pool contains every hand-built positive (P1-P6), and P5 and P6 enter through the strong-signals slot. For all 60 managers it contains at least 95% of the automatic plants.
2. **Code checks.** Fabricated IDs, fabricated quotes, out-of-scope people, "not recognized" under unknown coverage and invalid action triggers are all withheld. Tested with synthetic bad model outputs.
3. **Subject and routing.**
   - Exact, ambiguous, unknown, out-of-scope, two-to-five-people and more-than-five cases give the right result.
   - On a fixed question set with recorded plan outputs:
     - Discovery runs on every in-scope question.
     - "How are we doing compared with Customer Renewals?" and a question about another team's person are rejected without reading evidence.
     - "Who on my team helped Customer Renewals?" is processed with Customer Renewals as the beneficiary focus.
   - Clarification: an ambiguous name produces `missing_field = "subject"`. The follow-up request with the original question plus the choice keeps the intent and the period ("recognize", "this quarter"), and processes only the chosen person. The chosen ID is used even when the second plan writes the name differently.
4. **Follow-up.**
   - P1's A1 and A4 are observed, and P3 is not yet.
   - An empty table under complete coverage gives not yet; partial coverage gives unknown.
   - A3 matches only `Topic_Code = workload`.
   - The follow-up scope cannot add a person outside the roster frozen at the as-of date.
5. **Regression offline.** The legacy import profile and the existing test suite still pass after five-role fixtures are updated.
6. **Audit cases.**
   - `no_candidates` and `no_findings` are reported separately, with coverage.
   - Failures never read as "no hidden work".
   - A July recognition does not hide P1's June finding. A July share reads as not shared on June 30.
   - On `discovery_v1`, any `start_date` or `end_date` other than the fixed range is rejected by both the backend and the CLI.
   - No external person's name reaches the manager. The partner manager appears only in the recipient field of their own A2 or A4 draft.
   - The 8-item selection keeps the closing context for D1 and D3.
   - The section:
     - is present for every status and matches the checked result exactly;
     - holds at most 5 findings with drafts plus at most 5 one-line findings;
     - has a pointer line whose count equals the findings shown, and no count when there are none;
     - is published when Original's answer fails;
     - carries `discovery_section` with `reviewed_by_zerosugar: false` in the result and in the export.
   - Original's compose input contains no Discovery content, and ZeroSugar's input matches the `review-v8` contract.
   - Correction rounds never call Discovery again.
   - Work references: a different ID on the same work closes A1, and an edit cannot add a foreign reference.
   - Budget:
     - Discovery makes at most 2 logical calls, even when network retries occur.
     - The raw `models` count equals the number of `request_costs`, and the refund appears only in the separate fields.
     - After the refunds, Original's remaining calls, closing turn and seconds equal a run without Discovery.
     - A `DiscoveryTimeout` gives `failed_budget` and the run continues.
     - With no budget left before the schema retry, Discovery spends no call.
   - The scorer and the report reader find P1-P6 through `discovery_section`.

**Live**, which needs explicit authorization:

7. **Findings.** Discovery finds P1-P6, and none of D1-D8 is reported as a hidden-work gap.
8. **Subjects.** Beneficiary team and team-versus-person are correct.
9. **Actions.** Each action type fits its finding, and there are zero claims about engagement, retention or productivity.
10. **Smoke test of the existing hard question.** One run with Discovery active. It completes, and `discovery_applied` is recorded. With n = 1 and today's completion rate (about 59%), this is a smoke test, **not** a regression measurement. Measuring regression would need repeated runs, which are requested explicitly if wanted.
11. **Planning benchmark M3 rerun.** The plan's instructions and schema change, and every earlier planning change re-ran M3. This one does too:
    - the documented floors hold (test 18, Gemini 17);
    - P12 and P13 still ask for clarification in all 8 runs.

Live design: two workflows per manager context, M32 and M14, each with and without Discovery, so four in total. Add the smoke run (gate 10) and the M3 rerun (gate 11). All use one frozen pack and the GW API profile. Report recall, rejected decoys, correct actions, tokens, calls, latency and `discovery_applied`. These runs demonstrate behavior; they do not rank quality.

## 9. Sequence

1. Approve v8 and the rule change; freeze the schema and stories.
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
| Q4 | Discovery's model | **User:** the same GW profile as Original |
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

The task list, contracts and suggested models are in [WORK_BREAKDOWN_DISCOVERY.md](WORK_BREAKDOWN_DISCOVERY.md).

## 11. Authorization register

| Action | Status |
| --- | --- |
| Write v8 and update current-document pointers | Done in this documentation task |
| Sixth role and guidance changes in [AGENTS.md](../AGENTS.md). Proposed wording: Discovery findings are checked by code and not corrected by ZeroSugar; the Discovery section is appended after review and marked as not reviewed; Original's text keeps both reviews; old-run replay is not required for Discovery | Requires explicit user approval |
| New data pack, generator, importer profile, Discovery agent, `RunBudget.refund`, Original changes, date and clarification transport, actions store, UI | Proposed; requires implementation approval |
| Refunding Discovery's actual use to the run budget, in separate fields (3.6) | User decision 2026-11-15 |
| Offline tests during approved implementation | Specify with that scope |
| Live runs (gates 7-11, including the M3 rerun) | Proposed; requires explicit authorization |
| Other budget or provider changes, Git publication, real employee data | Not authorized by this plan |

## 12. Changes from v7

The changes from v5 to v6 and from v6 to v7 are listed in [v6 §12](DISCOVERY_SCOPE_AND_PLAN_v6_2026-11-15.md) and [v7 §12](DISCOVERY_SCOPE_AND_PLAN_v7_2026-11-15.md).

| Observation | v7 | v8 |
| --- | --- | --- |
| The refund falsifies the captured budget | `refund` lowered `models` and moved the deadline | Separate `refunded_models` and `paused_seconds`; the raw counters and the original deadline stay true; `resume.py` keeps its arithmetic (3.6) |
| Network retries consume calls | "Count as one call", which was incorrect | Network retries are attributed to their logical call and refunded; a check runs before every call, including the schema retry (3.6) |
| No distinct timeout exception | Assumed to exist | New `DiscoveryTimeout`, raised by `check_request_deadline()` within Discovery (3.6) |
| `needs_discovery` is the only trigger | A model flag | No flag: Discovery runs on every in-scope question (3.1) |
| A named team could stop legitimate questions | Depended on where the model put the team | Questions about or comparing with another team are rejected; a beneficiary-only team is processed; gate 3 covers both (3.2) |
| Clarification name matching | The chosen ID was matched to the re-planned name | The chosen ID is applied directly (3.2) |
| `OP_activity_weekly` count | ~140,000 | ~260,000 for 104 weeks |
| `OP_source_coverage` grain | Ambiguous, ~20,000 | 7 tables × 60 home teams × 8 quarters, ~3,400 |
| `more_findings` versus Q11 | Unbounded one-line list | At most 5 one-line findings; the rest are counted |
| Evaluation tooling | Not listed | The report reader and the scorer read `discovery_section` |
| Actions API without authentication | Not stated | Stated: synthetic demo only |
| Only the range end fixed | Moving the start or end could hide the stories | The whole range is fixed and read-only on `discovery_v1` |
| Internal log content | Free reasons | Fixed enums; no source text or question |

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

v5's evidence list still applies to the earlier checks. The median-scope counts and the 715k-token figure are agent-reported. The Discovery token figures are arithmetic floors, not measurements. Line numbers can drift; current files govern.

No runtime implementation, data generation, database change, test, build, live call or publication was performed.
