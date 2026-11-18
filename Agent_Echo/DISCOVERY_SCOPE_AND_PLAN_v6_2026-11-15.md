# Echo Discovery v6: proactive discovery of hidden cross-team work

Date: 2026-11-15. Status: proposed plan; documentation only. No runtime code, data, database or provider call was changed or made.

**Superseded on 2026-11-15 by [v7](DISCOVERY_SCOPE_AND_PLAN_v7_2026-11-15.md)**, which resolves the third audit. Kept as history. It superseded [v5](DISCOVERY_SCOPE_AND_PLAN_v5_2026-11-14.md). Earlier history is kept in [v4](DISCOVERY_SCOPE_AND_PLAN_v4_2026-11-14.md), [v3](DISCOVERY_SCOPE_AND_PLAN_v3_2026-11-12.md), [the seven reviews](DISCOVERY_SEVEN_REVIEWS_2026-11-12.md), [v2](DISCOVERY_PLAN_v2_2026-11-11.md), [the review synthesis](DISCOVERY_REVIEW_SYNTHESIS_2026-11-11.md) and [the brainstorm](DISCOVERY_BRAINSTORM_AND_PLAN_2026-11-10.md).

v6 keeps v5's design: a code prefilter, a model judgment, no correction loop, actions and follow-up. It simplifies the integration (section 12): Original's existing planning step identifies the subject, Discovery runs like the other specialists, and code appends Discovery's results as a separate section that ZeroSugar does not review.

## 1. Business case and responsibilities

The team's business case:

> Help managers identify and recognize the contributions their employees make to other teams, which usually fall outside the manager's visibility. Employees support projects, resolve dependencies and help other departments meet their goals, but the evidence is scattered across records and feedback, so the contributions may not be considered when evaluating and recognizing performance. Echo gathers and analyzes that information so the manager understands which work deserves attention and decides how to act. From the evidence it proposes concrete steps (recognize a specific contribution, request feedback from the benefited team, talk about workload) and prepares drafts, keeping the manager in charge of the decision and of personalizing the recognition. Hoped-for engagement and retention effects are not demonstrated by the prototype.

**Business baseline assumption.** The company already records the sources Discovery reads in its systems: cross-team feedback surveys, collaboration threads, blockers, incident handoffs, meeting notes, formal recognitions, 1:1s, review notes and a confidential individual pulse check. The prototype represents those systems with synthetic data that the team defines (section 5).

| Responsibility | Owner |
| --- | --- |
| Understand from the manager's free-text question whether it concerns the team, one person or a few people | **Original's planning step** (model), with code checking names against the manager's roster |
| Select only the relevant records and texts | **Discovery's code prefilter** |
| Read that compact evidence and judge which work is valuable, hidden and unrecognized, who did it, which team benefited and which actions fit | **Discovery** (model) |
| Build the "Discovery" section of the answer: findings plus action drafts from fixed templates | **Code**, from Discovery's checked result |
| Answer the rest of the question, with an optional one-line pointer to the Discovery section | **Original** |
| Review Original's answer, including that pointer | **ZeroSugar** (unchanged role). The Discovery section is not reviewed (section 3.5) |
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
10. The planning step identifies the subject; Discovery is called like Cherry and Vanilla.
11. Discovery's results go in their own section at the end of the answer, which ZeroSugar does not evaluate.
12. At most 5 findings per answer.
13. ZeroSugar checks only that what Original says about Discovery is consistent with the findings.
14. People are described as "prioritized for review", never as a ranking.

## 3. How Discovery works

### 3.1 Route

1. The manager types an open question in the existing UI or CLI, for example "How is my team doing this quarter?", "What should I know about Isabel?" or "Who should I recognize?" The question does not have to mention hidden or unrecognized work.
2. **Planning.** Original's existing `plan()` call ([original.py:162-265](agents/original.py)) gets five more fields in its structured output:
   - `needs_discovery`;
   - `subject_kind` (`team | person | people`);
   - `subject_names`;
   - `period_hint`;
   - `focus_hint`, for example a named partner team or "workload".

   The planning rule is that **every** question about the manager's team or any of its members sets `needs_discovery = true`. A routing gate (section 8) checks this on a fixed question set. The plan's key-set validation ([original.py:227](agents/original.py)) is updated to match.
3. **Subject check (code).** Code resolves the names and the period (section 3.2).
   - An ambiguous name goes through the plan's existing clarification return ([original.py:1031-1036](agents/original.py)). This is the only clarification mechanism, and nothing is cached: when the manager answers, Echo starts a new run.
   - A person or team outside the manager's scope, an unknown name, or a period outside the authorized dates stops the run with a message. No evidence is read.
4. **Discovery call.** `"Discovery"` is added to the delegation map next to Cherry and Vanilla ([original.py:627-631](agents/original.py)) and to `planned_roles` ([original.py:1039-1043](agents/original.py)). Right after delegations are set, the workflow calls Discovery **once**. This follows the existing Cherry prepared-metrics pre-step ([original.py:364-380](agents/original.py)). It is a code call, so Original's model cannot skip it.
   - The result is kept for the whole run. Repair and correction rounds reuse it and never call Discovery again.
   - Discovery runs its prefilter (3.3), its judgment call (3.4) and the code checks (3.5).
5. **Original composes** its normal answer. It may still ask Cherry for metrics and Vanilla for sentiment, so a team question still gets team metrics. Original receives a short Discovery summary, with finding IDs, people, beneficiary teams and work summaries, so it can add one pointer sentence such as "There are also 2 contributions to other teams; see the Discovery section". Original does not write the Discovery section or its actions.
6. **ZeroSugar** reviews Original's answer in both phases, as today (3.5).
7. **Release.** Code appends the **Discovery section** (3.5) to the released answer. A release check confirms that the section is present when there are findings, and that it matches the checked Discovery result exactly. Actions go to the Action Center; follow-up runs on request (6.3).

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
| The team named is not the manager's team | **Do not process.** Same answer for the team |
| Nobody with that name exists | Say so; do not guess |
| The question names nobody | The subject is the manager's whole team (section 3.3 pool) |

Code never widens the roster or the dates. A partner team can appear only as the beneficiary of the manager's own people, never as a subject.

**Two date windows.** Today one `AccessScope` serves the whole run ([data_access.py:10-22](agents/data_access.py)), and its default `end_date` is 2026-09-30. Discovery needs two windows over the same manager and roster:

| Window | Dates in the demo | Used by | Rule |
| --- | --- | --- | --- |
| **Analysis** | up to the **as-of date**, 2026-06-30 | Discovery, Original, Cherry, Vanilla, ZeroSugar | Nothing after the as-of date is read, so a July event cannot change a June finding. On the `discovery_v1` database the as-of date must be given explicitly: there is no default, and a missing as-of stops the run |
| **Follow-up** | from the decision date (2026-07-01) to the follow-up end (2026-09-30) | Only the follow-up code (6.3) | Same manager. The roster is frozen at the as-of date. It reads only the follow-up source tables, only for the people and work in saved actions, and can never add a subject |

The follow-up window is a separate `FollowUpScope` object, used only by the follow-up endpoint. A gate (section 8) checks that it cannot widen the roster or the subjects.

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

The section reports how many further findings passed the checks but were not shown. The manager can then ask about a specific person to see them.

### 3.5 Integrity and the Discovery section

Discovery's judgments are not sent back for correction. Before anything is shown, inexpensive code checks run:

- Every cited ID exists in the pool Discovery received.
- Every quote is an exact substring of its source.
- Every person is in the authorized roster, and every team and date is inside the analysis window.
- "Not recognized" is impossible when recognition coverage is partial or unknown.
- Every suggested action type is in the catalog and its trigger fits the finding. For example, A1 is not allowed when the finding is already recognized.
- **Privacy:** nothing shown to the manager names a person outside the manager's team or gives their ID. This applies to quotes, summaries, Original's answer and drafts. The one exception is the partner manager named as the recipient of an A2 or A4 draft. Code checks every release against the organization roster, replaces any leak with the placeholder, and counts it in the log.

A finding that fails a check is withheld and recorded, not repaired. Discovery is not added to ZeroSugar's correction owners ([zero_sugar.py:103](agents/zero_sugar.py)).

**The Discovery section.** Code builds it from the checked result and appends it after Original's answer. It contains:
- the status and coverage;
- up to 5 findings, each with its work summary, beneficiary team, why it matters, recognition and visibility state, quotes and source IDs;
- for each finding, its action drafts rendered from the fixed template for each action type (6.2), filled only from the finding's fields;
- the count of further findings, if there are any.

Because code renders the section, it cannot be omitted, reworded or dropped by Original. Its drafts add no claim that is not already in the finding.

**What ZeroSugar reviews:**

| Item | Reviewed by ZeroSugar? |
| --- | --- |
| The Discovery section: findings and their action drafts | No. Code checks only |
| Original's pointer sentence or any other statement Original makes about a Discovery finding | Yes, in both phases. It checks only that the statement is consistent with the findings and their quotes. ZeroSugar does not see the pool, so it does not re-check the underlying evidence. A correction goes to Original and may not change or drop a finding |
| The rest of Original's answer and Original's own proposals | Yes, as today |

Known limit: if Discovery's model misreads a comment but cites correctly, no reviewer catches it. The section's drafts repeat Discovery's own `work_summary` and `why_it_matters`, so an overstatement there appears in the drafts too. Gates 7-9 measure this.

The manager's later edits to a draft are the manager's own words. They are stored as a new version and are not reviewed. The privacy replacement still applies, and nothing is sent externally.

### 3.6 When Discovery cannot finish, and the budget

| Status | Meaning | What the answer shows |
| --- | --- | --- |
| `failed_provider` | A model call failed after the bounded retries, or the output failed the schema twice | Discovery section: "Discovery could not complete the analysis". Original answers the rest normally |
| `failed_budget` | Discovery's added allowance ran out | Same message, naming the budget |
| `all_withheld` | Every finding failed the code checks | "Discovery could not produce verifiable findings", with the withheld count |
| `partial` | Some findings passed and some were withheld, or a cap cut the pool | The passing findings, plus how many were withheld or not reviewed |

None of these results is ever shown as "no hidden work". Each one is logged with its reason.

**Budget.** Today `RunBudget` allows 32 model calls and 300 seconds per run ([runtime.py:97-138](agents/runtime.py), [original.py:433-434](agents/original.py)). It has no concept of a reserved share. Instead of adding one, the limit grows by Discovery's own allowance whenever `needs_discovery` is true (user decision 2026-11-15):
- **2 more model calls:** the judgment call and one schema retry;
- **a fixed number of extra seconds.** The initial value is 60 s. T4.6 recalibrates it from measured runs, but the mechanism exists from T3.1.

Discovery may use only these 2 calls. Original and ZeroSugar keep the same budget they have today.

**Retries.**
- Connection and provider errors use Echo's existing bounded retries.
- A schema failure is retried once.
- A finding that fails the code checks is never retried.

If the whole run still exhausts its budget, the existing budget-exhaustion path ends the run with a limited result and a budget notice. Echo does not promise to continue the analysis.

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

Each run logs the prefilter version, caps and SQL hash, the way metric versions are logged today ([metrics.py:56](agents/metrics.py)).

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
| `OP_activity_weekly` | One employee-week: cross-team hours, after-hours minutes, meeting hours | ~140,000 | Workload signal |
| `HR_employee_performance` | One employee per quarter: confidential pulse score (1-5), engagement, performance rating, goal attainment %, recorded date | ~20,000 (2,500 × 8 quarters) | Feeds `lowest_satisfaction` |
| Reused `HR_goals` | Individual goals from `data_extensions` | 12,670 | Inside or outside the person's goals |
| Reused `HR_self_review_items` | December 2025 self-review items from `data_extensions` | 12,129 | The employee's own account |
| `HR_one_on_ones` | One 1:1: manager, employee, date, **`Topic_Code`** (`workload`, `career`, `performance`, `recognition`, `other`), free-text notes | ~2,000 | Follow-up for A3, matched on `Topic_Code = workload` |
| `HR_review_notes` | One review note: employee, cycle, author, cited work anchor, date | ~1,000 | Follow-up for A5 |
| `OP_team_plans` | One planning item: team, partner team, item text, date | ~800 | Follow-up for A6 |
| `OP_source_coverage` | One source table × team × quarter: `complete` or `partial` | ~20,000 | Decides `not_yet` versus `unknown` |

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
| `agents/discovery.py` (new) | A `Specialist` subclass ([runtime.py:179](agents/runtime.py)) that runs the prefilter, one judgment call with one schema retry, the code checks, the top-5 rule and the `discovery-result-v1` result |
| `agents/discovery_tools.py`, `agents/discovery_checks.py`, `agents/discovery_section.py` (new) | Subject resolution, pool tools and prefilter; code checks; section and action rendering from templates |
| `agents/original.py` | <ul><li>Plan schema and rule: five new fields and the key-set update (162-265).</li><li>`"Discovery"` in the delegation map and `planned_roles` (627-631, 1037-1043).</li><li>The Discovery pre-step after delegations, modelled on Cherry's prepared metrics (364-380).</li><li>Budget increase when `needs_discovery` (433-434).</li><li>Short summary to the compose step.</li><li>Section appended at release, with the release check.</li><li>Stop messages for out-of-scope and not-found subjects.</li></ul> |
| `agents/policies.py` | Discovery role text, plus the planning rule for `needs_discovery` |
| `agents/grounding.py` | Let Original cite `DISC-*` finding IDs in its pointer sentence ([75, 303-304](agents/grounding.py)). The Discovery section stays outside the 24-fact and 12-narrative limits |
| `agents/zero_sugar.py` | Receive the findings and quotes as given context, to check Original's statements about them. Exclude the Discovery section. Discovery is not in `OWNERS` |
| `agents/data_access.py` | Projections over the new tables; mandatory as-of on `discovery_v1`; `FollowUpScope` for the follow-up endpoint only |
| `agents/connections.py`, `connections.json` | Discovery model profile, the same GW profile as Original |
| `agents/resume.py`, `capture.py`, `execution_log.py`, `run_agent.py`, `check_release.py`, `__init__.py` | Sixth-role registration, capture, CLI `--database` and `--as-of` |
| `import_data.py`, `files_discovery_v1/`, generator | Section 5 |
| UI backend `app.py`, `offline.py` | Database selection, actions store, follow-up endpoint, offline fixtures |
| UI frontend | Sixth agent on stage, a Discovery section with typed action cards, decision buttons, follow-up badges and a simulation label. No subject selector |
| Tests | Section 8 gates; update fixtures that assumed five roles |

## 8. Evaluation and gates

**Offline, zero tokens:**

1. **Pool recall.** The prefilter's pool contains every hand-built positive (P1-P6), and P5 and P6 enter through the strong-signals slot. For all 60 managers it contains at least 95% of the automatic plants.
2. **Code checks.** Fabricated IDs, fabricated quotes, out-of-scope people, "not recognized" under unknown coverage and invalid action triggers are all withheld. Tested with synthetic bad model outputs.
3. **Subject and routing.**
   - Exact, ambiguous, unknown, out-of-scope, two-to-five-people and more-than-five cases give the right result.
   - On a fixed question set with recorded plan outputs, every team or member question sets `needs_discovery` and no other question does.
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
   - A missing as-of on `discovery_v1` stops the run.
   - No external person's name reaches the manager.
   - The 8-item selection keeps the closing context for D1 and D3.
   - The Discovery section is present whenever there are findings, matches the checked result exactly, and holds at most 5 findings plus the count of the rest.
   - Correction rounds never call Discovery again.
   - Work references: a different ID on the same work closes A1, and an edit cannot add a foreign reference.
   - Budget: Discovery makes at most 2 calls, and the run limit grows by exactly that allowance.

**Live**, which needs explicit authorization:

7. **Findings.** Discovery finds P1-P6, and none of D1-D8 is reported as a hidden-work gap.
8. **Subjects.** Beneficiary team and team-versus-person are correct.
9. **Actions.** Each action type fits its finding. There are zero claims about engagement, retention or productivity. Original's pointer is consistent with the section.
10. **Regression live.** One run of the existing hard question with Discovery active completes with the same release status class as today.

Live design: two workflows per manager context, M32 and M14, each with and without Discovery, so four in total, plus the regression run. All use one frozen pack, question and GW API profile. Report recall, rejected decoys, correct actions, tokens, calls and latency. These runs demonstrate behavior; they do not rank quality.

## 9. Sequence

1. Approve v6 and the rule change; freeze the schema and stories.
2. Generator, `files_discovery_v1/`, importer profile, validated database; offline token count of the pool.
3. Discovery: prefilter, judgment, checks, section rendering; offline gates 1-3.
4. Original integration (plan fields, pre-step, budget, release section), ZeroSugar exclusion, actions store, follow-up, UI; offline gates 4-6.
5. Demo candidate.
6. Authorized live runs (gates 7-10).
7. Contingency and presentation.

If time runs short, cut follow-up for A5 and A6, the M14 live pair and UI polish first. Do not cut Discovery's judgment, the hand-built stories (including P5), the automatic plants, or follow-up for A1, A2 and A4.

## 10. Decisions

| ID | Question | Decision |
| --- | --- | --- |
| Q1 | Does ZeroSugar review Discovery content? | **User:** no for the Discovery section; yes for what Original says about it, for consistency only (3.5) |
| Q2 | Who enters the team-question pool? | **User:** the 10 least satisfied plus up to 5 with the strongest signals (3.3) |
| Q3 | Background data scope | **User:** whole organization, weekly grain, templated |
| Q4 | Discovery's model | **User:** the same GW profile as Original |
| Q5 | Does Cherry's `cross_team_contributions` metric stay? | **User:** yes |
| Q6 | Rafay's `data_extensions` side project | **User:** required as P5 in M14 (5.6) |
| Q7 | Satisfaction measure | **User:** a confidential individual 1-5 pulse per quarter |
| Q8 | Which managers get plants | **User:** hand-built for M32 and M14; automatic for all 60 (5.7) |
| Q9 | How Original calls Discovery | **User:** the planning step identifies the subject; Discovery is called like Cherry and Vanilla, with no new workflow (3.1) |
| Q10 | How findings reach the manager | **User:** in a separate Discovery section at the end, which ZeroSugar does not evaluate; built by code so it cannot be dropped (3.5) |
| Q11 | How many findings | **User:** at most 5 (3.4) |
| Q12 | How people are described | **User:** "prioritized for review", never a ranking (5.6) |
| Q13 | Budget for Discovery | **User:** the run limit grows by Discovery's own allowance (3.6) |

The task list, contracts and suggested models are in [WORK_BREAKDOWN_DISCOVERY.md](WORK_BREAKDOWN_DISCOVERY.md).

## 11. Authorization register

| Action | Status |
| --- | --- |
| Write v6 and update current-document pointers | Done in this documentation task |
| Sixth role and guidance changes in [AGENTS.md](../AGENTS.md). Proposed wording: Discovery findings are checked by code and not corrected by ZeroSugar; the Discovery section is not reviewed; Original's text keeps both reviews; old-run replay is not required for Discovery | Requires explicit user approval |
| New data pack, generator, importer profile, Discovery agent, Original and ZeroSugar changes, actions store, UI | Proposed; requires implementation approval |
| Run-limit increase equal to Discovery's allowance (3.6) | User decision 2026-11-15; applies only when `needs_discovery` |
| Offline tests during approved implementation | Specify with that scope |
| Live runs (gates 7-10) | Proposed; requires explicit authorization |
| Other budget or provider changes, Git publication, real employee data | Not authorized by this plan |

## 12. Changes from v5

| Topic | v5 | v6 |
| --- | --- | --- |
| Subject identification | A separate Discovery model call | A field in Original's existing planning call. Discovery makes one fewer call |
| Calling Discovery | An `ask_discovery` tool "before planning", which the code order does not allow | A code pre-step after planning, like Cherry's prepared metrics. Discovery joins the delegation map |
| Findings reaching the manager | Through Original's answer, with no guarantee | A code-built Discovery section, appended at release, with a presence check |
| Answer caps | Findings and actions competed with the 24-fact and 12-narrative limits | The section sits outside those limits. At most 5 findings, chosen by a fixed rule |
| Actions | Typed proposals by Original with an `origin` rule and `own_wording` | Discovery actions are code-rendered records in the section. Original's own proposals keep today's schema and review. The `origin` rule is no longer needed |
| ZeroSugar | Reviewed Original's text about findings, implied against evidence | Checks only consistency with the findings and quotes |
| Dates | One scope, contradictory wording | An analysis window (mandatory as-of) and a separate `FollowUpScope` |
| Budget | A reserve that `RunBudget` cannot express | The run limit grows by Discovery's 2-call allowance |
| Several named people | Undefined | Two to five people processed; more than five clarified |
| Clarification | Two mechanisms | One: the planning step |
| A3 follow-up | Free-text topic | `Topic_Code = workload` |
| Figures | 1,900 employees; ~13k tokens | 2,500 employees (~20,000 pulse rows); ~18-20k tokens, to be measured |
| Tests | No regression run | Gate 10: the existing hard question with Discovery active |

## 13. Evidence and limits

Checked by the parent session on 2026-11-15, read only:
- `plan()` and its key-set validation (`original.py:162-265`, 227);
- the plan-before-delegation order (`original.py:1028-1043`);
- the two-entry delegation map (`original.py:631`);
- `RunBudget` (`runtime.py:97-138`);
- the answer limits (`grounding.py:20-21`);
- the roster: 2,500 employees, 60 managers, 10 to 85 people per team, and 5 teams with 15 or fewer people.

v5's evidence list still applies to the earlier checks. The median-scope counts and the 715k-token figure are agent-reported. The Discovery token figures are arithmetic floors, not measurements. Line numbers can drift; current files govern.

No runtime implementation, data generation, database change, test, build, live call or publication was performed.
