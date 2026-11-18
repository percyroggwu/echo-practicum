# Echo Discovery v5: proactive discovery of hidden cross-team work

Date: 2026-11-14 (rewritten the same day after user corrections). Status: proposed plan; documentation only. No runtime code, data, database or provider call was changed or made.

**Superseded on 2026-11-15 by [v6](DISCOVERY_SCOPE_AND_PLAN_v6_2026-11-15.md)**, which simplifies the integration with Original and ZeroSugar. Kept as history. It superseded [v4](DISCOVERY_SCOPE_AND_PLAN_v4_2026-11-14.md) and keeps it, [v3](DISCOVERY_SCOPE_AND_PLAN_v3_2026-11-12.md), [the seven reviews](DISCOVERY_SEVEN_REVIEWS_2026-11-12.md), [v2](DISCOVERY_PLAN_v2_2026-11-11.md), [the review synthesis](DISCOVERY_REVIEW_SYNTHESIS_2026-11-11.md) and [the brainstorm](DISCOVERY_BRAINSTORM_AND_PLAN_2026-11-10.md) as history.

## 1. Business case and responsibilities

The team's business case:

> Help managers identify and recognize the contributions their employees make to other teams, which usually fall outside the manager's visibility. Employees support projects, resolve dependencies and help other departments meet their goals, but the evidence is scattered across records and feedback, so the contributions may not be considered when evaluating and recognizing performance. Echo gathers and analyzes that information so the manager understands which work deserves attention and decides how to act. From the evidence it proposes concrete steps (recognize a specific contribution, request feedback from the benefited team, talk about workload) and prepares drafts, keeping the manager in charge of the decision and of personalizing the recognition. Hoped-for engagement and retention effects are not demonstrated by the prototype.

v3 and v4 drifted toward employee-submitted accounts, home-team routine work, anonymous surveys and responses back to the employee, and v4 deferred follow-up. v5 re-centers on proactive discovery.

| Responsibility | Owner |
| --- | --- |
| Understand from the manager's free-text question whether it concerns the team or a specific person | **Discovery** (model), with code checking names against the manager's roster |
| Select only the relevant records and texts | **Discovery's code prefilter** |
| Read that compact evidence and judge which work is valuable, hidden and unrecognized, who did it and which team benefited | **Discovery** (model) |
| Turn findings into proposed manager actions; Discovery-origin drafts are rendered by code from templates (section 3.5) | **Original** |
| Decide, edit or dismiss each action | **Manager** |
| Show later whether the action happened | Follow-up check over later source records |
| Review Original's answer text, including anything Original adds about a Discovery finding, and actions that do not come from Discovery | **ZeroSugar** (unchanged role). Discovery findings and Discovery-origin actions and drafts are excluded (section 3.5) |

One-line goal: **Discovery finds the valuable hidden work; Original tells the manager what to do; follow-up shows whether it happened.**

## 2. User decisions (2026-11-14)

1. Discovery performs the search itself.
2. Discovery uses a model, because recognizing unrecognized work in a comment or message requires reading and judgment. Code does not decide that.
3. Code selects only the most relevant evidence before the model reads anything. No model receives the whole dataset.
4. The manager writes the question as free text, about the team or a specific person. There is no subject selector in the UI.
5. Discovery's output is not challenged with ZeroSugar correction loops the way Cherry and Vanilla outputs are today.
6. Actions and follow-up are core to Echo and are not deferred.
7. Reopening or replaying earlier live runs (for example runs 50 to 110) is not a requirement for Discovery. Compatibility with old saved runs does not constrain this design.
8. The team generates whatever synthetic data the baseline needs, without limiting the design to a minimum.

## 3. How Discovery works

### 3.1 Route

1. The manager types an open question about the team or a person in the existing UI or CLI, for example "How is my team doing this quarter?", "What should I know about Isabel?" or "Who should I recognize?" The question does not have to mention hidden or unrecognized work.
2. **Every** question about the manager's team or one of its members goes to Discovery first, with the original wording, before Original's question-led planning. Discovery's path is its own: Original does not rewrite the question or choose the subject.
3. Discovery runs three steps (3.2-3.4). It separates two "nothing found" cases:
   - **`no_candidates`**: the code prefilter selected no evidence at all. There is no judgment call, so the cost stops after the subject call and the prefilter.
   - **`no_findings`**: evidence was selected, and the model judged that it shows no valuable hidden work. This always needs the judgment call.

   In both cases the manager sees "no hidden-contribution findings **in the selected evidence**", together with the coverage: how many people were reviewed out of how many in the team, and which caps were reached. It is never presented as proof that no hidden work exists. Failures are a third kind of result (section 3.6).
4. Original composes the answer and the typed action proposals with drafts (section 6), including Discovery's findings when there are any. Original may still ask Cherry for metrics or Vanilla for broader sentiment.
5. ZeroSugar reviews Original's composed answer (section 3.5). Release; actions appear in the Action Center; follow-up runs on request.

### 3.2 Step 1: identify the subject (model + code check)

- A small structured model call reads only the question and returns `{subject_kind: team | person | people, names_or_ids: [...], period_hint, focus_hint}`. `focus_hint` captures things like a named partner team or "workload".
- Code resolves every name, ID or team against the organization roster and the manager's authorized team, which today means employees whose `Pilot_Manager_ID` is the manager ([data_access.py:39-44](agents/data_access.py)):

| Case | Result |
| --- | --- |
| Exactly one person in the manager's team | Process that person |
| Several people in the manager's team share the name | Ask which one (existing clarification path, [original.py:1031-1036](agents/original.py)) |
| The person belongs to another manager's team | **Do not process.** Answer that the person is outside the manager's team; read no evidence and make no judgment call |
| The team named is not the manager's team | **Do not process.** Same answer for the team |
| Nobody with that name exists | Say so; do not guess |
| The question names nobody | The subject is the manager's whole team |

- Code never widens the roster or the dates. A partner team can appear only as the beneficiary of the manager's own people, never as a subject.

**Period and as-of date.** The question's **as-of date** is the authorized `end_date` (2026-06-30 in the demo). Code resolves `period_hint` against the authorized date range:

- If there is no hint, the period is the default analysis window: the three quarters ending at the as-of date.
- If there is a hint ("this quarter", "since January"), the period is the hint intersected with the authorized range. When the intersection is smaller than the hint asked for, the answer says so.
- If the intersection is empty, the result is `out_of_scope` with "that period is outside the authorized dates". No evidence is read.

The model never chooses dates. It only supplies the hint.

### 3.3 Step 2: select the relevant evidence (code)

Code builds a **candidate pool** with fixed, versioned SQL and simple text matching over the authorized data. It does not judge value; it narrows what the model will read.

Selection signals (each stored as a reason the record was selected):

- Help for another team: contribution, request thread, resolved blocker, incident handoff or meeting mention where the beneficiary is not the home team.
- Visibility gap: partner feedback not shared with the home manager, help with no formal work request, help mentioned only in another team's notes.
- Recognition gap: no recognition event for that work, or recognition coverage unknown.
- Importance: the beneficiary team linked the help to one of its goals, or the blocker it resolved delayed a goal.
- Repetition: hidden help in two or more quarters.
- Workload: cross-team or after-hours load above the team's normal range.
- **Name in someone else's text:** a scoped employee's name appears in partner messages, notes or feedback about work recorded under someone else. Only the model can judge whether this means real, unrecognized help, so code finds these mentions and passes them on.
- **Work described in the employee's own self-review:** a `HR_self_review_items` entry (from `data_extensions`) describes help to another team, or an initiative that matches no goal and no record. Code passes the text on, and the model weighs it against other sources. A self-review is the employee's own account, so it never counts as corroboration by itself.

**Who enters the pool for a team question (user decisions, 2026-11-14).** The pool is the union of two code tools, with duplicates removed:

1. `lowest_satisfaction(team, period, n=10)` returns the **10 people with the lowest satisfaction** in the manager's team. It reads the new identified table `HR_employee_performance` (section 5.4) and orders by the latest satisfaction score, then the change from the previous quarter, then ID.
2. `strongest_signals(team, period, n=5)` returns **up to 5 more people with the strongest hidden-work signals**, whatever their satisfaction. It orders by the number of independent signal types above (at least two required), then by volume, then by recency. This keeps a satisfied person with strong evidence, such as E0001 in P5, from being dropped.

The pool therefore holds 10 to 15 people. Each one records why it entered (`low_satisfaction`, `strong_signals` or both). A person with high satisfaction and only one weak signal is not surfaced in a team question. That person is still found when the manager asks about them directly.

**Nothing after the as-of date.** Every selection input is computed as of the question's as-of date and excludes any event whose event date or recorded date is later. This covers recognition and visibility flags, name mentions, signals and satisfaction (the latest score recorded on or before that date). The pack contains follow-up events from July to September 2026 that would otherwise leak in. For example, a July recognition must not hide a valid June finding. In the same way, feedback written in June and shared in July still counts as **not shared** at a June 30 as-of date. Whether feedback was shared is read only from its dated share fields (section 5.4), never from the current Yes/No flag. Follow-up checks (section 6.3) are the only code that reads after the as-of date.

**Caps and balanced selection.** Each person contributes at most 8 evidence items. They are not simply the newest praise. For each work item selected, the closing context comes first, because it can confirm or contradict the lead:

1. The **recognition state** of that work as of the as-of date: a recognition event if one exists, otherwise an explicit "no recognition event recorded" fact together with its coverage.
2. **Attribution:** who holds the record, and any other contributor named in the sources.
3. **Status or outcome:** acceptance, blocker resolution, or the linked goal's result.

The remaining slots go to supporting items, most specific and then newest first. Texts are trimmed to 300 characters around the relevant sentence, and each item keeps its source ID. A single-person question keeps up to 25 items with the same ordering. All caps are versioned parameters. Reaching a cap is recorded, never hidden.

**Team-pattern leads.** Code counts hidden help toward each beneficiary team across the whole team. These counts are only a **lead**: they never establish on their own that a valuable hidden pattern exists. For each lead, code adds up to two sample items per person involved, within the caps. The model decides whether the samples support a team finding.

**External people in texts.** A text can mention or be written by people outside the manager's team. They are authors, beneficiaries or co-contributors, never subjects. Before the pool reaches the model, code replaces each such person with a stable placeholder that names only their role and team, for example `[Customer Renewals colleague 2]`. Stable placeholders keep attribution judgments possible, so the model can still tell that the thanks went to someone else (P6, D3). The beneficiary team's manager may still be named as the recipient of an A2 or A4 draft.

Code never sends the full contents of `text_documents` ([data_access.py:146](agents/data_access.py)) or whole tables.

### 3.4 Step 3: judge (model)

One batched model call receives the candidate pool and returns, for each candidate: whether there is valuable cross-team work the manager probably does not see; what the work was; the benefiting team; why it matters (goal, blocker, incident); the recognition state (`recognized`, `not_recognized`, `unknown`); whether it is a person finding or a team pattern; the cited source IDs; and candidates that were rejected, with a short reason.

The model decides team pattern versus individual: if several people show the same hidden help toward one team, it reports a team finding and still lists the people the evidence names, because the manager acts on people.

### 3.5 Integrity without a correction loop

Discovery's judgments are not sent back for correction. Its output is checked by inexpensive code checks before Original sees it:

- Every cited ID exists in the candidate pool Discovery received.
- Every quoted phrase is an exact substring of the cited source.
- Every person is in the authorized roster; every team and date is inside the authorized scope.
- "Not recognized" is impossible when recognition coverage for that work is partial or unknown.
- **Privacy:** nothing that reaches the manager names a person outside the manager's team, or gives their ID. That covers quotes, summaries, Original's answer text and drafts. Such people appear only as a role and team placeholder. The one exception is the partner manager named as the recipient of an A2 or A4 draft. Code checks every release against the organization roster and replaces any leak with the placeholder. Leaks are counted in the log.

A finding that fails a check is withheld and recorded; it is not repaired. Discovery is not added to ZeroSugar's correction owners ([zero_sugar.py:103](agents/zero_sugar.py)).

**What ZeroSugar reviews and what it does not (user decision, 2026-11-14):**

| Item | Reviewed by ZeroSugar? | Correction goes to |
| --- | --- | --- |
| Discovery findings | No. They are fixed premises: ZeroSugar may not dispute or re-judge them | Nobody; failed code checks withhold the finding |
| Actions and drafts with `origin = discovery` | No | Nobody; failed code checks reclassify or withhold them (below) |
| Original's answer text, including any interpretation, implication or extra claim Original adds about a finding | Yes, both phases | **Original only**. A correction may change Original's added wording but may not ask to change or drop the Discovery finding it rests on |
| Actions and drafts with `origin = other` | Yes, as today | Original |

**`origin` is assigned by code, never by Original.** A proposal gets `origin = discovery` only if all of these hold:
- every citation is a Discovery finding ID from this run;
- its action type is listed in that finding's `suggested_action_types`;
- its subject is the finding's employee or team, inside the manager's team.

Otherwise code sets `origin = other`, and the proposal goes through normal review. Original cannot skip review by labelling a proposal as Discovery.

**Code checks on Discovery-origin actions and drafts:**
- The cited finding IDs exist, and the action type matches the catalog (section 6.2).
- The status is never shown as sent or done.
- **Drafts are built from structured slots, not free text.** Code cannot reliably detect a new claim in free prose: "it saved the client" adds a conclusion without adding any ID, number or date. So a Discovery-origin draft is rendered by code from a fixed template per action type (section 6.2). The template's slots are filled only from the linked finding's fields: subject name, beneficiary team, partner manager (A2 and A4 only), `work_summary`, `why_it_matters`, quotes and work references. Original chooses the action and the finding; it does not write the text of a Discovery-origin draft.
- If Original wants its own wording, that proposal gets `origin = other` and ZeroSugar reviews it like any other answer text.
- Accepted risk: the template repeats Discovery's own `work_summary` and `why_it_matters`. If those overstate the work, the draft overstates it too. This is the same known limit as for findings (below), and gate 9 measures it.
- The manager's later edits are the manager's own words. They are stored as a new version and not reviewed. The privacy replacement still applies, and nothing is sent externally.

ZeroSugar can replay Discovery's prefilter SQL, like the existing metric replay ([zero_sugar.py:335-346](agents/zero_sugar.py)), at no token cost.

Known limit: if Discovery's model misreads a comment but cites correctly, no reviewer will catch that. The offline and live gates in section 8 are designed to measure it.

### 3.6 When Discovery cannot finish

| Status | Meaning | What Original does |
| --- | --- | --- |
| `failed_provider` | A model call failed after the existing bounded retries | Shows "Discovery could not complete the analysis". Answers the rest of the question with the other roles. Makes no Discovery-origin actions |
| `failed_budget` | Discovery could not start, or could not finish, within its allowance without using Original's reserve (below) | Same message, naming the budget as the reason. Original continues on its reserve. No automatic budget increase |
| `all_withheld` | The model returned findings, but every one failed the code checks | "Discovery could not produce verifiable findings", with the withheld count. Never "no hidden work" |
| `partial` | Some findings passed and some were withheld, or a cap cut the pool | Shows the passing findings, plus how many were withheld or not reviewed |

None of these results is ever turned into "no hidden work" or "no findings". Each one is recorded in the execution log, together with its reason.

**Budget reserve and retries.** Discovery shares Original's run budget (`RunBudget`: model calls, tool calls and seconds; [original.py:433-434](agents/original.py)), so it must not use up what Original needs afterwards.
- **Allowance.** Discovery may use at most **3 model calls**: the subject call, the judgment call, and one schema retry (next rule). It also has a fixed time slice, set from measured runs in T4.6.
- **Reserve.** Before each Discovery call, code checks that the call still leaves Original's reserve untouched. The reserve covers Original's composition plus both ZeroSugar phases and one correction round; its size is also set from measured runs in T4.6.
  - If the check fails before the subject call, Discovery does not run. The result is `failed_budget`, and Original answers with the other roles.
  - If it fails before the judgment call, the result is `failed_budget` too, without spending the call.
- **Retries.**
  - Connection and provider errors use only Echo's existing bounded retries. If those fail, the result is `failed_provider`.
  - If the model's output fails the JSON schema, Discovery retries once. A second schema failure gives `failed_provider`.
  - A finding that fails the code checks is never retried; it is withheld.
  - All retries count toward Discovery's allowance.
- **When even the reserve runs out**, for example because Original's own correction round takes longer, the run ends through the existing budget-exhaustion path. That path returns a limited result: validated findings and any reviewed text that is already complete, plus a budget notice. Echo makes no promise to continue the analysis in that case.

## 4. Token budget

Measured context, 2026-11-14, read only:

- Recent live runs are input-heavy: `reports/gwu_original_8.json` has 9 calls and about 64k input and 4.9k output tokens, with a largest single call of 13.3k input.
- A median manager scope has about 48 employees, 1,413 contributions, 783 feedback rows and 2,940 work requests. Sending all of it to a model would be roughly 715k tokens; one quarter is roughly 90k. These counts are agent-reported.

Planned Discovery cost:

| Call | Input | Output |
| --- | --- | --- |
| Subject identification | about 0.5k tokens (question plus instructions) | about 0.1k |
| Judgment, team question | about 11k tokens (up to 15 people × up to 8 items × about 80 tokens, plus team-pattern counts and instructions) | about 2k |
| Judgment, one person | about 3k tokens | about 0.8k |

Original receives only the validated findings, not the candidate pool. Planned total for a team question: roughly 13k Discovery tokens, compared with about 90k for one quarter of raw data. Discovery's calls come from the existing shared run budget, within the allowance and reserve rules in section 3.6. Any increase needs approval.

Precomputed at import, always keeping each underlying event's event date and recorded date so that query-time filtering by as-of date stays exact (section 3.3):
- per-contribution visibility events (praised, shared, recognized), not final flags;
- quarter keys;
- an index of employee-name mentions in partner texts. Each run logs the prefilter version, caps and SQL hash, the same way metric versions are logged today ([metrics.py:56](agents/metrics.py)).

## 5. Data baseline

### 5.1 Why the current data cannot demonstrate Discovery

Read-only checks of `data/echo.db` (eleven tables; the `data_extensions` tables are not loaded):

- 66,192 of 77,333 contributions (86%) are cross-team. Cross-team help is normal here, so it is not a signal.
- Feedback has only 8 distinct `Interaction_Date` values (quarter ends). An employee has at most three rows per quarter, and every row needs a `Contribution_ID` and a manager author ([QA_data_dictionary.csv:94-98](../files_update/QA_data_dictionary.csv)).
- Contribution text comes from about nine summary templates and nine `Business_Outcome` values. There are no team goals or measured outcomes for the beneficiary team.
- In M32's scope every employee looks alike. Each has 10 to 17 cross-team contributions and about six feedback rows. That figure is agent-reported.

The new data must create **variance**: in who helps whom, whether it mattered to a goal, whether praise reached the home manager, whether recognition followed and how heavy the load was. **The signal must also live in the text**, because the model reads it. For example, a message to another team says "Isabel stayed late to fix the export so we could close the quarter", and no record credits Isabel.

### 5.2 What exists today and what we create

| Already in the database (kept, copied into the new pack) | What we create that does not exist |
| --- | --- |
| Employees and managers, with each employee's manager | Team goals for every team, with target and due date (`OP_team_goals`) |
| Projects and their objective | Measured results of those goals: met or missed (`OP_goal_outcomes`) |
| Formal work requests with hours | Informal help requests between teams that never became a formal request, with their messages (`OP_collab_threads`, `OP_collab_messages`) |
| Accepted contributions with home and beneficiary team | Blockers between teams: who was blocked, for how long and who resolved it (`OP_dependency_blockers`) |
| Feedback and manager recognition notes, at quarter-end dates, with a "shared with home manager" flag | Incidents and on-call handoffs where someone helped another team, including after hours (`OP_incident_handoffs`) |
| Weekly available hours | Lines from other teams' meeting notes that mention people (`OP_meeting_mentions`) |
| Priority decisions and escalations | Formal recognition events separate from feedback: award, shout-out, nomination (`HR_recognition_events`) |
| Team surveys and program participation | Weekly cross-team hours, after-hours minutes and meeting hours (`OP_activity_weekly`) |
| Team-level, anonymous survey scores only | Identified per-employee satisfaction, engagement and performance per quarter (`HR_employee_performance`) |
| `data_extensions`: individual goals and December 2025 self-reviews with Rafay's planted renewal-risk side project, not loaded into any database today | Loaded into the new pack: goals become context and self-reviews become a Discovery source. The side project gets 2026 corroboration (5.6, P5) |
| | Follow-up records for A3, A5 and A6 (`HR_one_on_ones`, `HR_review_notes`, `OP_team_plans`) and coverage declarations per source, team and quarter (`OP_source_coverage`) |
| | Real event dates and author type on feedback; feedback without a contribution; goal, effort and channel on contributions; after-hours on capacity |
| | Varied text that carries the signal, hand-built stories and decoys (5.6), automatic plants for every manager (5.7), follow-up events from July to September 2026, and private answer keys |

### 5.3 Packaging

A separate versioned pack `files_discovery_v1/` and database `data/echo_discovery_v1.db`, so experiments do not disturb the current demo data. The pack contains:
- copies of the eleven current tables, with added columns;
- copies of `HR_goals` and `HR_self_review_items` from `data_extensions/`, keeping their IDs;
- the new tables.

`files_update/`, `data/echo.db` and the `data_extensions/` folder stay unchanged. The extension's `QA_discovery_answer_key.csv` is never loaded.

`import_data.py` changes:

- A `--profile legacy|discovery_v1` option. The file list comes from the profile's manifest instead of the fixed `FILES` tuple ([import_data.py:17-29](import_data.py)).
- Column types come from a `Type` column in the data dictionary instead of sets of column names ([import_data.py:30-42](import_data.py)), so numbers do not load as text.
- ISO validation for `*_At` timestamps.
- An "exactly one anchor" check for polymorphic links.
- Share-date checks on feedback: the share date is not earlier than `Interaction_At`, and the flag matches the share date (section 5.4).
- Table-count checks that follow the selected profile.
- Indexes for the new tables.
- A default output that is never `data/echo.db`.

### 5.4 New and extended source tables

Background rows cover all employees over the existing horizon, 2024-10-01 to 2026-09-30. Rich hand-built stories are planted in M32's and M14's teams (5.6). Simple automatic plants go in every manager's team (5.7). Counts are construction targets; the manifest records the exact numbers after generation.

| Table | Grain and key fields | Target rows | What it enables |
| --- | --- | --- | --- |
| `OP_team_goals` | One team goal per quarter: ID, team, owner manager, metric, target, due date | ~1,200 | Links help to the beneficiary team's goal |
| `OP_goal_outcomes` | One goal measurement: value, numerator/denominator, measured at | ~5,000 | Shows whether the goal was met or missed |
| `OP_collab_threads` | One cross-team request thread: opened at, requesting team, requester, topic, optional work request | ~25,000 | Help that never became a formal request |
| `OP_collab_messages` | One message: thread, author type/ID, sent at, text, mentions | ~120,000 | Varied text showing who asked, who answered and who was thanked |
| `OP_dependency_blockers` | One blocker: raised at, blocking team, blocked goal, resolved by, resolved at, days blocked | ~6,000 | Evidence of unblocking another team |
| `OP_incident_handoffs` | One incident or on-call handoff: severity, responders, owning team, start/end, notes | ~3,000 | Firefighting for other teams, after-hours help |
| `OP_meeting_mentions` | One line of another team's meeting notes: date, team, mentioned employee, text, optional work anchor (section 6.4) | ~15,000 | Thanks given where the home manager is absent |
| `HR_recognition_events` | One formal recognition: given by, visibility, type, one typed anchor, event date | ~4,000 | Separates "praised" from "recognized"; needed for decoys and follow-up |
| `OP_activity_weekly` | One employee-week: cross-team hours, after-hours minutes, meeting hours | ~140,000 | A workload signal with real variance |
| `HR_employee_performance` | One employee per quarter: identified satisfaction score (1-5, from a confidential individual pulse check), engagement score, performance rating, goal attainment %, recorded date | ~15,000 (1,900 employees × 8 quarters) | Feeds `lowest_satisfaction` for team questions. No such per-employee table exists today; current survey scores are team-level and anonymous |
| Reused `HR_goals` | Individual goals from `data_extensions`, with source IDs kept | 12,670 | Whether help was inside or outside the person's goals |
| Reused `HR_self_review_items` | One December 2025 self-review item from `data_extensions`, with source IDs kept | 12,129 | The employee's own description of help or initiatives that match no goal or record |
| `HR_one_on_ones` | One 1:1 meeting: manager, employee, date, topics | ~2,000 (follow-up window plus background) | Follow-up for A3 |
| `HR_review_notes` | One performance-review note: employee, cycle, author, cited work anchor, date | ~1,000 | Follow-up for A5 |
| `OP_team_plans` | One team planning item: team, partner team, item text, date | ~800 | Follow-up for A6 |
| `OP_source_coverage` | One source table × team × quarter: `complete` or `partial` | ~20,000 | Decides `not_yet` versus `unknown` in follow-up, and "unknown" recognition states |

Columns added to the copied tables:

- `HR_recognition_feedback`: `Interaction_At` (the real event date), `Author_Type`, a nullable `Contribution_ID`, and optional thread/blocker/incident anchors with an at-least-one-anchor check. It also gets two dated share fields:
  - `Shared_With_Home_Manager_At`: when the feedback became visible to the home manager. It is null if the feedback was never shared.
  - `Share_Recorded_At`: when that share was recorded.

  Feedback counts as shared at date *t* only if both dates are on or before *t*. The legacy `Shared_With_Home_Manager` flag is kept for compatibility but becomes derived: it is `Yes` exactly when `Shared_With_Home_Manager_At` is set. Discovery and follow-up never read the flag. The importer rejects a share date earlier than `Interaction_At` and a flag that disagrees with the date.
- `OP_contributions`: `Team_Goal_ID`, `Effort_Hours`, `Request_Channel` (formal or informal).
- `OP_capacity`: `After_Hours`, `Cross_Team_Hours`.

No column states the expected verdict: no impact tier, no "hidden" flag. That content belongs only in the private answer key.

Text: at least 60 templates per text family, with slot variation, realistic specificity, a range of tones, and deliberately vague messages such as "thanks!". Specific text must not announce the answer.

### 5.5 Dates inside the data

| Window | Dates | Use |
| --- | --- | --- |
| History | 2024-10-01 to 2025-09-30 | Background and repeat patterns |
| Analysis | 2025-10-01 to 2026-06-30 | Planted hidden work, including the December 2025 self-reviews. The analysis date range ends on June 30 |
| Follow-up | 2026-07-01 to 2026-09-30 | Later recognition, feedback and messages that show whether the actions happened |

In the demo, manager decisions carry a simulated date of 2026-07-01. Follow-up compares later source events against that date. The real time of the click is stored separately.

### 5.6 Planted stories and decoys

All employees below belong to M32 (Sales Operations), except P5's people, as checked in `HR_employees` on 2026-11-14. P5's six employees are E0001 (M14, Data Platforms), E0046 (M46, Data Platforms), E0051 and E0066 (M31, Customer Renewals), and E0074 and E0085 (M01, Customer Care).

| ID | Subject | Plant | Expected result |
| --- | --- | --- | --- |
| P1 | E0010, person | Resolves a 9-day blocker on Enterprise Accounts' (M29) renewal-accuracy goal, which is then met. Three partner praises, none shared by June 30; no recognition. In the follow-up window, one June praise is shared in July (`Shared_With_Home_Manager_At` in July) | Found, with the praise still unshared at the as-of date. A1 recognize and A4 ask M29 to copy the home manager. Follow-up: a July recognition event makes A1 **Observed**; the July share of the June praise makes A4 **Observed** |
| P2 | E2156, person | 14 informal threads for Customer Renewals (M31) with no work request; after-hours above 6 h/week for five weeks | Found. A3 workload conversation and A1 recognize |
| P3 | E0728, person | Night incident handoff for Escalation Services (M03); thanked in M03 meeting notes; no formal feedback | Found. A2 request feedback from M03. Follow-up: nothing, so **Not yet** |
| P4 | Team pattern | Several M32 members repeatedly help Infrastructure (M16) over three quarters; feedback never shared | Team finding that names the people involved. A6 team process change and A4 |
| P6 | E0970, person | Named only inside other people's feedback and messages ("thanks to Mara and E0970's fix…") for work recorded under E0107; no record of their own | Found only by reading text: credit the real contributor |
| P5 (required) | E0001, M14; the same project for M46, M31 and M01 | Rafay's planted renewal-risk early-warning tool. It already appears in the six December 2025 self-reviews and matches no goal and no record. The new pack adds 2026 corroboration: threads and messages with Customer Renewals, a Customer Renewals meeting mention, and a measured renewal-goal outcome that cites the alerts. E0001's satisfaction is deliberately **not** among M14's 10 lowest | When M14 asks about the team, Discovery finds E0001 through the strong-signals slot and reports the initiative, naming co-contributors' teams but not their names. When M46, M31 or M01 ask, each finds their own people. A1 recognize, A2 request feedback from Customer Renewals, A5 review note. The extension's own answer key stays unchanged |
| D1 | E1748 | Same volume as P1, but already recognized and all feedback shared | Not a gap; the work may still be described |
| D2 | E1333 | Many threads, but no acceptance, the goal is missed and the blocker is still open | Acknowledge the effort; make no impact claim |
| D3 | E0107 | Holds the record for P6's work, but the messages show E0970 did it | Do not credit E0107 for it |
| D4 | E2233 | High after-hours, caused by covering for leave on their own team | Only a workload topic, not hidden cross-team work |
| D5 | Any | Partial `Record_Coverage` on the relevant feedback | Recognition state **unknown**, never "not recognized" |
| D6 | Any | Help inside the home team (home team = beneficiary team) | Not a cross-team finding |
| D7 | One of the 10 least satisfied | Low satisfaction with no hidden cross-team work (for example, an own-team conflict) | Report no hidden-contribution finding; do not invent one to explain the low score |
| D8 | High satisfaction | Hidden cross-team help with only one weak signal | Not in a team question's pool; found when the manager asks about the person |

Satisfaction alignment for M32:
- P1, P2, P3 and at least two P4 members rank among the 10 least satisfied.
- P6 has high satisfaction and must enter through the strong-signals slot.
- D1, D2, D4 and D7 are also among the 10 least satisfied, so the model has to tell real hidden work apart from look-alikes.
- D3 enters through the strong-signals slot because it holds the record, so the misattribution must be caught by reading.

Privacy: the identified satisfaction score is sensitive. It is visible only for the manager's own team. It is never linked to or derived from the anonymous survey, and it is never shown as a ranking to the manager. It only decides whose evidence is read.

Background noise: about 5% of profiles in each team are near misses, with one strong signal only. Expected answers live only in a private `QA_discovery_v1_answer_key.csv`, which is never loaded or put in a prompt.

### 5.7 Automatic plants in every manager's team (user decision, 2026-11-14)

The generator also plants **two simple hidden contributions in each of the 60 managers' teams**, about 120 cases, chosen at random with a fixed seed.

- **Shape.** Each case is help to another team with partner praise that was not shared, a corroborating thread or blocker, and no recognition. Half of the people are among their team's 10 least satisfied; the other half enter only through strong signals.
- **Decoys.** Each team also gets one simple decoy: either the same work already recognized, or own-team help.
- **Answer key.** The answers go in the same private key, with a `hand_built` or `automatic` marker.

This tests whether Discovery works for every manager, not just M32 and M14. The code part (subject resolution, both pool tools, prefilter recall) is checked offline for all 60 managers at no token cost. The model judgment is checked live only on M32 and M14.

## 6. Actions, drafts, decision and follow-up

### 6.1 What exists

- Original must propose at least one cited action for the manager ([original.py:45-48](agents/original.py)). The proposal schema is only `{text, citation_ids}` ([original.py:678](agents/original.py)).
- The UI has nine action kinds ([api.ts:200](../Echo_UI/frontend/src/lib/api.ts)) and assigns them with regular expressions over free text ([visual.tsx:99-123](../Echo_UI/frontend/src/manager/visual.tsx)).
- The Action Center stores meetings and team events in browser `localStorage` ([actionStore.ts](../Echo_UI/frontend/src/manager/actionStore.ts)). Its states are Draft, Planned, "Confirmed in prototype", Cancelled and Completed ([actionTypes.ts:1-6](../Echo_UI/frontend/src/manager/actionTypes.ts)). Completed is a manual click with no evidence behind it.
- Offline fixtures already produce recognize, partner and one-to-one actions ([offline.py:546-559, 715-725](../Echo_UI/backend/offline.py)). `GET /recognition-queue` exists ([app.py:244](../Echo_UI/backend/app.py)).

### 6.2 Action catalog

| Action | Subject | Trigger | Draft template (slots filled by code from the finding) | Must not claim |
| --- | --- | --- | --- | --- |
| A1 Recognize a contribution | person | Supported hidden work, not recognized | Recognition note for the manager to personalize | "Never recognized" when coverage is partial; effects on engagement or retention |
| A2 Request feedback from the benefited team | person | Help with no partner feedback | Message to the partner manager | That the partner valued the work |
| A3 Workload conversation | person | Cross-team or after-hours load above the normal range | Agenda for a 1:1 | Burnout or a performance judgment |
| A4 Ask for visibility | person or team | Partner praise not shared with the home manager | Note asking the partner to copy the home manager | Bad intent by the partner |
| A5 Performance-review note | person | Supported help outside the person's goals | Review note marked "to verify" | That the work was formally assessed |
| A6 Team process change | team | Repeated pattern toward one partner team | Planning item | Savings or productivity gains |

Original's proposal schema gains `action_type`, `subject_kind`, `subject_id`, `beneficiary_team`, `finding_ids` and an optional `own_wording`. Code then adds `origin`, `work_refs` (section 6.4) and `draft_text`.
- **Without `own_wording`:** code renders `draft_text` from the action's template and the finding's slots. The proposal can then be `origin = discovery`, which is not reviewed by ZeroSugar but passes the code checks.
- **With `own_wording`:** the proposal is always `origin = other` and is reviewed as part of the answer (section 3.5).

### 6.3 Decision and follow-up

- **States.** A proposal is `proposed`, then becomes `accepted`, `edited` or `dismissed` (with a reason). Follow-up then gives `observed`, `not_yet` or `unknown`. Nothing is shown as sent or done without a matching source record.
- **Persistence.** A server-side SQLite store, `manager_actions`, kept separate from the source database, with `POST/GET/PATCH /api/managers/{id}/actions`. Discovery actions leave `localStorage`; existing meeting and event actions can stay there for now.
- **Follow-up rules.** Each action has its own match condition. A source event counts only if it matches the action's **person, work, recipient and date**. The date must be on or after the decision date and no later than the follow-up end (2026-09-30).

| Action | `observed` when a source event shows | Source table |
| --- | --- | --- |
| A1 Recognize | A recognition **for the subject employee**, whose anchor is **one of the proposal's `work_refs`** (section 6.4). Recognition for other work does not count | `HR_recognition_events` |
| A2 Request feedback | New partner feedback **written by the beneficiary team** about **one of the finding's work items** | `HR_recognition_feedback` (author team = beneficiary team) |
| A4 Ask for visibility | A **share event** in the follow-up interval: partner feedback about the finding's work items from the beneficiary team, whose `Shared_With_Home_Manager_At` falls between the decision date and the follow-up end. The feedback itself may be older, such as a June praise shared in July. Feedback shared before the decision does not count, and neither does new feedback that is still unshared. This is different from A2 | `HR_recognition_feedback` (`Shared_With_Home_Manager_At`, `Share_Recorded_At`) |
| A3 Workload conversation | A 1:1 between the home manager and the subject with a workload topic | `HR_one_on_ones` (new, follow-up window) |
| A5 Review note | A review note for the subject that cites one of the finding's work items | `HR_review_notes` (new, follow-up window) |
| A6 Team process change | A plan item for the manager's team that names the beneficiary team | `OP_team_plans` (new, follow-up window) |

- "Work items" in the table above means the proposal's `work_refs` (section 6.4). A2, A4 and A5 match only when the event's anchor is one of them. A3 and A6 are not tied to a work item. They match on person, recipient or partner team, and date.
- **`not_yet` versus `unknown`: the coverage declaration decides, not the presence of rows.**
  - `observed`: a matching event exists in the follow-up interval. This is true under any coverage.
  - `not_yet`: there is no matching event, and `OP_source_coverage` declares `complete` for the action's source table, for that team, in every quarter that touches the interval from the decision to the follow-up end. An empty source table under complete coverage is exactly the `not_yet` case: the record would be there if the action had happened.
  - `unknown`: there is no matching event, and coverage is `partial` or not declared for any part of that interval (for example a `Record_Coverage` gap).
  - P3 depends on this. Its data declares `HR_recognition_feedback` complete for M32's team in 2026-Q3, so the absence of feedback from M03 gives `not_yet`. Gate 4 also includes a case with partial coverage, which must give `unknown`.
- **Edited proposals.** Matching uses the version the manager saved last: its subject, recipient, `work_refs` and action type. If the manager changed the action type, the new type's rule applies. The original proposal stays in the history but is never matched.
- **Dismissed proposals** are never checked.
- **UI.** The UI shows the three follow-up results and any dismissal reason, and is labelled as a simulation: nothing is sent externally.

### 6.4 Work references: one identity from finding to follow-up

A message, a blocker and a recognition can have different IDs and still be about the same work. So every link from finding to action to follow-up uses one shared contract, the **work reference**: `{"type": "contribution | thread | blocker | incident", "id": "..."}`. No new table is needed.

- **In the data.** Every evidence row carries its work anchors as columns. Messages carry their thread. Feedback and recognition events carry one typed anchor (section 5.4). Meeting mentions and review notes carry an optional cited anchor. Self-review items may have none.
- **In the pool.** Code attaches each item's resolved `work_refs` next to its source ID. Code builds these; the model does not.
- **In the finding.** Code computes `work_refs` as the union of the anchors of the finding's cited `evidence_ids`. The model cannot invent one.
  - A finding with no anchored evidence (only self-review or unanchored mentions) has empty `work_refs`.
  - Such a finding can still be shown and can still propose A3 or A6.
  - Its A1, A2, A4 and A5 proposals always get follow-up `unknown`, because there is no work to match. The UI says so.
- **In the proposal.** Code copies the finding's `work_refs` into the proposal. Original cannot add references.
- **In `manager_actions`.** Each saved version stores its own `work_refs`. When editing, the manager may remove references but may add only references from the same finding. Follow-up uses the last saved version.

Estimated effort: about 4 to 5 days. That is roughly 1 day for the store and endpoints, 1.5 for typed proposals, 1 for follow-up and 1 for the UI.

## 7. Integration checklist

| Area | Work |
| --- | --- |
| `agents/discovery.py` (new) | A `Specialist` subclass ([runtime.py:179](agents/runtime.py)) with three steps: subject call, prefilter, judgment call. Plus code checks, typed findings and versioned caps |
| `connections.json`, `agents/connections.py` | A Discovery model profile on the GW API ([connections.py:13, 41](agents/connections.py)) |
| `agents/original.py` | `ask_discovery` tool and handler, delegation sets, tool-to-role map (today it raises `KeyError` for unknown tools), routing every team or person question to Discovery first, handling every Discovery status (3.1, 3.6), typed proposals with code-assigned `origin` ([149-160, 344, 356, 627-631, 1037-1043, 678](agents/original.py)) |
| `agents/policies.py` | Discovery role text: cite only given IDs, never "not recognized" under unknown coverage, no engagement claims, no productivity ranking |
| `agents/grounding.py` | Accept Discovery as a producer of findings ([75, 114, 303-304, 336-339, 482](agents/grounding.py)) |
| `agents/zero_sugar.py` | Treat Discovery findings as given input, and optionally replay the prefilter SQL. Discovery is deliberately not in `OWNERS` |
| `agents/data_access.py` | Discovery projections over the new tables, inside the manager's authorized team and dates. Add fields to `AccessScope` only if Discovery needs them (decision 7) |
| `agents/resume.py`, `agents/capture.py`, `agents/execution_log.py`, `run_agent.py`, `check_release.py`, `agents/__init__.py` | Sixth-role registration, capture of Discovery calls, CLI `--database` |
| `import_data.py`, `files_discovery_v1/`, generator | Section 5 |
| UI backend `app.py`, `offline.py` | Database selection, actions store and endpoints, follow-up endpoint, offline fixtures for the sixth role |
| UI frontend `agents.ts`, `events.ts`, `AgentStage.tsx`, `AgentStrip.tsx`, `Brief.tsx`, Action Center | Sixth agent on stage, typed actions, decision buttons, follow-up badges. No subject selector |
| Tests | Agent contracts, Discovery code checks, prefilter recall, release boundaries. Update or retire fixtures that assumed five roles |

## 8. Evaluation and gates

**Offline, zero tokens** (deterministic parts):

1. The prefilter's candidate pool contains every hand-built positive (P1-P6) for its question. P5 and P6 enter through the strong-signals slot. For all 60 managers, the pool contains at least 95% of the automatic plants (5.7).
2. Code checks reject fabricated IDs, fabricated quotes, out-of-scope people and "not recognized" under unknown coverage. Test this with synthetic bad model outputs.
3. Subject resolution: exact, ambiguous and unknown names give the right ID or a clarification.
4. Follow-up rules: P1 is observed. P3 is not yet: there is no event, and coverage is complete. A source table that is empty under complete coverage gives not yet; the same absence under partial or undeclared coverage gives unknown. Nothing is marked done without a record.
5. Legacy import profile and the existing test suite still pass, after five-role fixtures are updated.
6. Audit cases:
   - `no_candidates` versus `no_findings` are reported separately, and both show coverage.
   - Provider failure, budget exhaustion and all-withheld results never read as "no hidden work".
   - A July recognition does not hide P1's June finding.
   - Share dates: P1's June praise shared in July reads as not shared at the June 30 as-of date, and makes A4 observed in follow-up. A share before the decision date does not close A4. The derived flag always agrees with the share date.
   - No external person's name reaches the manager.
   - The 8-item selection keeps the recognition, attribution and outcome context for D1 and D3.
   - A proposal that Original labels as Discovery but that fails the origin rule goes to review.
   - A1 is not closed by a recognition for different work. A2 and A4 are told apart.
   - `unknown` is returned under partial coverage.
   - Work references: a recognition with a different ID that is anchored to the same thread or blocker closes A1. A manager edit cannot add a reference that is not in the finding. A finding with no anchored evidence gives `unknown` for A1, A2, A4 and A5.
   - Drafts: a Discovery-origin `draft_text` is exactly the rendered template. Any `own_wording` sends the proposal to review.
   - Budget: with Original's reserve not available, Discovery spends no call and returns `failed_budget`, and Original still answers. A second schema failure gives `failed_provider`, and Discovery never makes more than 3 calls.

**Live**, which needs explicit authorization:

7. Discovery's judgment finds P1-P6, and none of D1-D8 is reported as a hidden-work gap.
8. Beneficiary team and team-versus-person are correct.
9. Each action type matches its finding; drafts cite existing IDs; there are zero claims about engagement, retention or productivity.

Live design: **two workflows per manager context** on one frozen pack, question and GW API profile, covering M32 and M14, so four in total. In each context, one workflow is current Echo without Discovery and the other is Echo with Discovery. Report recall of the planted work, rejected decoys, correct typed proposals, tokens, calls and latency. Two runs demonstrate behavior; they do not rank quality. If they show instability, request more runs explicitly instead of adding them automatically.

## 9. Sequence

1. Approve v5 and the rule change; freeze the schema and planted stories.
2. Generator, `files_discovery_v1/`, importer profile, validated database.
3. `discovery.py`: subject step, prefilter, judgment call, code checks; offline gates 1-3.
4. Original integration, typed proposals, actions store, follow-up, UI; offline gates 4-6.
5. Demo candidate.
6. Four authorized live workflows (M32 and M14, each with and without Discovery).
7. Contingency and presentation.

If time runs short, cut follow-up records for A5/A6, the M14 live pair and UI polish first. Do not cut Discovery's judgment, the hand-built stories (including P5), the automatic plants, or follow-up for A1, A2 and A4.

## 10. Decisions (2026-11-14, all confirmed by the user)

| ID | Question | Decision |
| --- | --- | --- |
| Q1 | Does ZeroSugar review Original's text built on Discovery findings? | **User:** yes for Original's answer text; **no** for the actions and drafts that come from Discovery. Code checks still apply (section 3.5) |
| Q2 | Who enters the team-question pool? | **User:** the 10 least satisfied people (new `HR_employee_performance` table) plus up to 5 more with the strongest hidden-work signals, chosen by two code tools (section 3.3) |
| Q3 | Background data for the whole organization or only M32 and partners? | **User:** whole organization, weekly grain, templated |
| Q4 | Which model for Discovery's two calls? | **User:** the same GW profile as Original |
| Q5 | Does Cherry's `cross_team_contributions` metric stay? | **User:** stays. Discovery does not replace metrics |
| Q6 | Use Rafay's `data_extensions` side project? | **User:** yes. It is required as P5 in M14, with self-reviews as a Discovery source and 2026 corroboration (5.6) |
| Q7 | How is satisfaction measured in `HR_employee_performance`? | **User:** a confidential individual 1-5 pulse score per quarter |
| Q8 | Which managers get planted stories? | **User:** hand-built stories for M32 and M14; two automatic plants and one decoy for every one of the 60 managers (5.7) |

The task-by-task implementation list, contracts and suggested subagent models are in [WORK_BREAKDOWN_DISCOVERY.md](WORK_BREAKDOWN_DISCOVERY.md).

## 11. Authorization register

| Action | Status |
| --- | --- |
| Rewrite v5 and update current-document pointers | Done in this documentation task |
| Sixth role and guidance changes in [AGENTS.md](../AGENTS.md): "preserve the existing five roles" (line 49), independent review of every finding, and preservation of old replay. Proposed wording: Discovery findings are checked by code and not corrected by ZeroSugar; Original's text keeps both reviews; old-run replay is not required for Discovery | Requires explicit user approval |
| New data pack, generator, importer profile, Discovery agent, actions store, UI changes | Proposed; requires implementation approval |
| Offline tests during approved implementation | Specify with that scope |
| Four GW live workflows (M32 and M14) | Proposed; requires explicit authorization |
| Budget or provider changes, Git publication, real employee data | Not authorized by this plan |

## 12. Corrections in this rewrite and changes from v4

| Topic | Decision |
| --- | --- |
| Discovery's nature | A model reads selected evidence and judges. Code selects, checks and caps. (The first draft of v5 wrongly proposed a code-only Discovery.) |
| Question | Free text from the manager. Discovery identifies team versus person; code only resolves names. (The first draft wrongly proposed a UI selector.) |
| Tokens | About 13k per team question, from code-selected evidence for the 10 least satisfied people plus up to 5 with the strongest signals, not the full data |
| Old runs | Not a constraint. v4's separate cohort `ReviewScope` and its replay protections are dropped |
| Center of the design | Proactive cross-team discovery. Employee accounts, home-team routine work (S1) and anonymous surveys (S11) leave the core |
| Actions and follow-up | Core: typed actions, Discovery-origin drafts rendered from templates (Original's own wording is reviewed), one work-reference contract from finding to follow-up, decisions stored on the server, follow-up from later source events decided by declared coverage |
| Budget | Discovery uses at most 3 calls, including one schema retry, and never touches Original's reserve. If the reserve itself runs out, Echo returns a limited result instead of promising to continue |
| Data | A larger baseline: fourteen new tables (including identified per-employee satisfaction, follow-up records and coverage declarations), new columns on existing tables, signal in the text, planted stories (including one that can only be found by reading text) and decoys |
| Kept from v4 | Separate pack and database, importer profile, `HR_goals` reuse, extension and its answer key untouched, no verdict columns at runtime, no engagement claims |

## 13. Evidence and limits

Four Claude Opus brainstorm subagents (medium effort) examined architecture, the data baseline, evidence selection and token use, and actions, follow-up and evaluation. The parent re-checked several of their findings:

- Original's delegation and metric pre-step lines, and ZeroSugar's replay lines.
- Contribution and feedback-date counts, and the table inventory of `data/echo.db`.
- The managers of every planted employee ID.
- Token figures in `gwu_original_8.json`.
- `_visibility_sql` and `invisible_work` in `offline.py`, and the Action Center states.

The median-scope row counts, the 715k-token figure and M32's per-employee counts are agent-reported. The Discovery token figures in section 4 are estimates, not measurements. Line numbers can drift; current files govern.

No runtime implementation, data generation, database change, test, build, live call or publication was performed.
