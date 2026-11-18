# Work breakdown: building Discovery in Echo (v9 history)

> **Superseded by [the current breakdown](WORK_BREAKDOWN_DISCOVERY.md)**, which follows plan v10. Kept as history of the errata tables in §12.

Date: 2026-11-15. Status: proposed task list for implementing [Discovery plan v9 (final)](DISCOVERY_SCOPE_AND_PLAN_v9_2026-11-15.md). This document authorizes nothing by itself. Task T0.1 and the live runs (T6.5) need explicit user approval. It replaces the breakdowns written for v5 to v8. The plan is frozen. Implementation-level contracts from the fifth audit are acceptance criteria in §12, and further review happens on the code.

Each task lists the files it touches, how to know it is done, and a suggested model and effort if a subagent does it.

**Model guidance:**

| Suggestion | Use for |
| --- | --- |
| **Fable medium / high** | The hardest, highest-risk work. That means the lead session that coordinates the subagents, the Discovery specialist, the Original workflow change, and the final independent review, which runs at high |
| **Opus high** | Core design and subtle logic: role text, section and templates, hand-built stories, story freeze |
| **Opus medium** | Larger, well-specified work with judgment: generator, signal SQL, text templates, schema freeze |
| **Sonnet high** | Precise code with clear contracts: importer, code checks, scoped projections, follow-up rules |
| **Sonnet medium** | Routine code, tests and documentation: endpoints, UI wiring, fixtures, registration |
| **Haiku high / low** | Work where a mistake is cheap to spot and no code is edited: running checks, summarizing logs and reports, `graphify update .` |

This follows Anthropic's model guidance (claude.dev, "Which Claude model should you build with?"; Claude Academy, "Choosing the right Claude model"):

- **Opus 5.5 is the default.** Move a task to Fable 5.2 when Opus at high falls short, for architecture-level work, and for long unattended or subagent-leading runs.
- **Try Fable before pushing Opus past high.** Fable at high scored about the same as Opus at max on the cited benchmark, at roughly half the cost per task.
- **Escalate in steps.** First give the model a way to verify its work. Then raise effort one level. Only then move up a model.
- **Keep code edits and judgment calls off Haiku.**
- **Cost.** Fable costs twice Opus per token ($8/$40 against $4/$20 per million input/output tokens), and its availability depends on the plan.

Two writers never edit the same file at the same time. Tasks in the same phase marked "parallel" touch different files.

## 1. Contracts

### 1.1 What Original's planning step adds

These fields are new in the `plan()` structured output (plan §3.1):

| Field | Type | Notes |
| --- | --- | --- |
| `subject_kind` | `team \| person \| people \| other_team` | `other_team` covers a question about, or comparing with, another team; it is rejected. There is no `needs_discovery` flag: Discovery runs on every in-scope question |
| `subject_names` | list of strings | Names or IDs as written; empty for a whole-team question |
| `period_hint` | string or null | For example "this quarter". Code intersects it with the analysis window |
| `focus_hint` | string or null | A topic such as "workload", or a partner team named **only as the beneficiary** of the manager's team's help. A team that is asked about or compared against goes in `subject_names` instead |

### 1.2 Input that Discovery receives

| Field | Source | Notes |
| --- | --- | --- |
| `question` | The manager's text, verbatim | |
| `subject` | Code's resolution of the plan fields (plan §3.2) | Employee IDs, all inside the manager's team, or the whole team |
| `manager_id`, `start_date`, `end_date` | Trusted application scope, sent by the UI and the CLI | The model cannot change them. On `discovery_v1`, the whole range is fixed: 2025-10-01 to 2026-06-30. `end_date` is the **as-of**, and any other start or end is rejected. Nothing later is read |
| `clarification` | Optional, from the clarification card | `{name_as_written, employee_id}`. It always arrives together with the original question. The `employee_id` is applied directly, never by matching names (plan §3.2) |
| `database` | CLI/UI selection | `data/echo_discovery_v1.db` |
| `budget` | Original's `RunBudget` | Discovery has its own cap of 2 logical calls and a per-call time limit, checked before every call including retries. Network retries are attributed to their logical call. The actual use is refunded in a `finally` block for every logical call, on success, schema failure, provider error and `DiscoveryTimeout` alike, into `refunded_models` and `paused_seconds`; the raw counters are not changed (plan §3.6) |

### 1.3 Output that Discovery returns (`discovery-result-v1`)

```json
{
  "discovery_version": "discovery-v1",
  "status": "findings | partial | no_candidates | no_findings | all_withheld | failed_provider | failed_budget",
  "subject": {"kind": "team | person | people", "employee_ids": ["E0010"], "team": "Sales Operations"},
  "period": {"start": "2025-10-01", "end": "2026-06-30", "as_of": "2026-06-30", "narrowed_from_hint": false},
  "coverage": {"team_size": 75, "people_reviewed": 13, "caps_hit": ["items_per_person"]},
  "findings": [{
    "finding_id": "DISC-1",
    "kind": "person | team_pattern",
    "employee_ids": ["E0010"],
    "beneficiary_team": "Enterprise Accounts",
    "work_summary": "Resolved the export blocker that delayed the renewal-accuracy goal.",
    "why_it_matters": "The blocked goal was met after the fix.",
    "visibility_state": "praise_not_shared | no_feedback | shared",
    "recognition_state": "recognized | not_recognized | unknown",
    "evidence_ids": ["BLK-0412", "MSG-88120", "FB-30211"],
    "work_refs": [{"type": "blocker", "id": "BLK-0412"}, {"type": "thread", "id": "THR-20931"}],
    "quotes": [{"source_id": "MSG-88120", "text": "exact substring"}],
    "actions": [{"action_id": "ACT-1", "action_type": "A1", "subject_kind": "person", "subject_id": "E0010",
                 "beneficiary_team": "Enterprise Accounts", "work_refs": ["..."], "draft_text": "rendered template"}]
  }],
  "more_findings": {"listed": [{"finding_id": "DISC-6", "employee_id": "E0555", "beneficiary_team": "Infrastructure"}], "not_listed": 2},
  "team_pattern_leads": [{"beneficiary_team": "Infrastructure", "people": 4, "hidden_items": 11, "judged": "supported | not_supported"}],
  "internal": {"pool": {"size": 13, "entered_by": {"low_satisfaction": 10, "strong_signals": 5, "both": 2}},
               "rejected": [{"employee_id": "E1748", "reason": "already recognized"}],
               "withheld": [{"finding_id": "DISC-4", "check": "quote_not_in_source"}], "redactions": 3},
  "usage": {"calls": 1, "input_tokens": 0, "output_tokens": 0}
}
```

- **Findings.** `findings` holds at most 5 entries, chosen by the fixed rule in plan §3.4. `more_findings.listed` holds up to 5 further findings that passed the checks, shown as one line each. `more_findings.not_listed` counts any beyond that.
- **Code-built fields.** `work_refs` is the union of the anchors of the cited evidence. `actions` are typed records with drafts rendered from templates. The model never writes either one.
- **`internal`.** It goes to the execution log only and is never shown to the manager (plan §5.6, privacy). `rejected.reason` and `withheld.check` are fixed enums. They never copy source text or the question.
- **Statuses.** Clarification (for unresolved or ambiguous names) and out-of-scope (for names identified outside the team) are not Discovery statuses: they are handled by the planning step and the subject check before Discovery runs. `no_candidates` means that no judgment call was made.

### 1.4 What reaches the manager

1. **Original's answer**, exactly as today. Original receives nothing from Discovery and cites no `DISC-*` IDs. Its own proposals keep today's schema (`{text, citation_ids}`) and today's review (`review-v8`).
2. **The Discovery section**, appended by code after review. It contains:
   - the **pointer line, written by code** from the status (plan §3.5), whose count equals the findings shown;
   - the coverage;
   - up to 5 findings with their action cards;
   - up to 5 further findings in one line each; any beyond that are only counted.

   ZeroSugar does not review the section. A release check confirms that it is present for every status and identical to the checked result. It is published even when Original's answer fails.
3. **Provenance in the result:** `discovery_section: {present, status, finding_ids, reviewed_by_zerosugar: false, checked_by_code: true}`, shown in the export and the UI.

## 2. Phase 0: rules and freeze

| ID | Task | Files | Done when | Model |
| --- | --- | --- | --- | --- |
| T0.1 | **Change project rules** (needs user approval). The new rules: <ul><li>Allow six roles.</li><li>Discovery's findings are checked by code and not corrected by ZeroSugar.</li><li>The Discovery section is not reviewed.</li><li>Original's text keeps both reviews.</li><li>Replaying old runs is not required for Discovery.</li></ul> | [`Final_Project/AGENTS.md`](../AGENTS.md) (lines 21, 35, 48-50, 159), [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md), [`DOCUMENTATION_MAP.md`](DOCUMENTATION_MAP.md) | The rules no longer contradict v9; the user approved the text | Sonnet medium |
| T0.2 | **Freeze the data schema.** Data dictionary (with a `Type` column) and manifest covering: <ul><li>the 14 new tables;</li><li>the reused `HR_goals` and `HR_self_review_items`;</li><li>the added columns, including the work anchors, the feedback share fields, the `Topic_Code` values, and `Record_Coverage` redefined as `complete | partial` per feedback row.</li></ul> Also define the private answer-key format (`hand_built` / `automatic`) | `files_discovery_v1/QA_data_dictionary.csv`, `QA_manifest.csv` (new) | Every table and column in plan §5.4 has a type, key and nullability | Opus medium |
| T0.3 | **Freeze the stories.** One row per story or decoy: IDs, dates, sources, expected result, prohibited claim | Private worksheet next to the answer key | P1-P6 and D1-D8 are fully specified, including satisfaction alignment and P1's July share | Opus high |

## 3. Phase 1: data

| ID | Task | Files | Done when | Model |
| --- | --- | --- | --- | --- |
| T1.1 | **Importer profiles.** <ul><li>`--profile legacy\|discovery_v1`, with the file list from the manifest and types from the dictionary.</li><li>Checks: `*_At` validation, one-anchor checks, share-date checks and `Topic_Code` values.</li><li>Profile table counts and new indexes.</li><li>Never writes `data/echo.db` by default.</li></ul> | [`import_data.py`](import_data.py) | The legacy import is unchanged; the discovery profile loads the generator output | Sonnet high |
| T1.2 | **Background generator, operations** (parallel with T1.3): team goals and outcomes, threads and messages, blockers, incidents, meeting mentions. Covers the whole organization over the analysis and follow-up windows (2025-10-01 to 2026-09-30), with a fixed seed | New `data_discovery/generate_discovery_v1.py` (operations module) | Row counts near the targets; real variance across people | Opus medium |
| T1.3 | **Background generator, HR** (parallel with T1.2): <ul><li>`HR_employee_performance` for all 2,500 employees over 4 quarters (about 10,000 rows);</li><li>`HR_recognition_events`;</li><li>`Record_Coverage` regenerated as `complete | partial`: mostly `complete`, about 5% `partial` in the background, and `partial` for D5. The old free text is not copied;</li><li>the new columns on feedback, contributions and capacity;</li><li>`HR_one_on_ones` with `Topic_Code`, `HR_review_notes` and `OP_team_plans`;</li><li>the `OP_source_coverage` declarations: 7 tables × 60 home teams × 4 quarters, about 1,700 rows;</li><li>`OP_activity_weekly` for 52 weeks, about 130,000 rows;</li><li>copies of `HR_goals` and `HR_self_review_items`.</li></ul> | Same generator (HR module) | <ul><li>Satisfaction and workload vary.</li><li>Feedback has real event dates and dated shares, some shared later than they were written.</li><li>Evidence rows carry work anchors.</li><li>Every follow-up rule has a source table and a coverage declaration.</li></ul> | Opus medium |
| T1.4 | **Text templates.** At least 60 per text family, with slots, tones and vague variants, plus a scan that rejects verdict words | Generator template files | Template counts met; the leakage scan passes | Opus medium |
| T1.5 | **Hand-built stories** for M32 (P1-P4, P6, D1-D8) and M14 (P5, adding 2026 corroboration) | Generator (stories module) | <ul><li>Sources exist with the frozen IDs and dates.</li><li>Satisfaction alignment holds.</li><li>P3's feedback coverage for 2026-Q3 is declared complete.</li><li>Every feedback row cited by P1-P6 has `Record_Coverage = complete`, and `HR_recognition_events` coverage is `complete` for their teams and quarters.</li><li>One of P1's June praises has a July share date.</li></ul> | Opus high |
| T1.6 | **Automatic plants:** 2 cases and 1 decoy for each of the 60 managers, with a fixed seed. The split per team: <ul><li>53 teams: 1 plant in the low-satisfaction slot and 1 in the strong-signals slot.</li><li>The 5 teams with 15 people or fewer (M41, M58, M42, M46, M49): 2 low-satisfaction plants.</li><li>M32 and M14: 2 strong-signals plants, because the hand-built stories take precedence (plan §5.6, 5.7).</li></ul> Every feedback row a plant cites is `complete` | Generator (plants module) | 120 cases and 60 decoys in the private answer key, split about 63 low-satisfaction / 57 strong-signals; no plant displaces a hand-built story from its slot | Sonnet high |
| T1.7 | **Build and verify the data.** Build `data/echo_discovery_v1.db` and a QA report covering counts, FKs, variance, leakage scan and story presence. It also checks that every feedback row cited by a story or plant is `complete`, and that `OP_source_coverage` is `complete` everywhere except the one named test row (M41, `HR_recognition_feedback`, 2026-Q3) | Build script, report | The report passes; `data/echo.db` is untouched | Sonnet medium |

## 4. Phase 2: data access and code tools

| ID | Task | Files | Done when | Model |
| --- | --- | --- | --- | --- |
| T2.1 | **Scoped access and the two date windows.** <ul><li>Projections over the new tables, restricted to the manager's team and the analysis window. Partner teams appear only as beneficiaries.</li><li>External people are replaced with stable role-and-team placeholders before the pool is built.</li><li>Shared state is read from share dates, never from the flag.</li><li>On `discovery_v1`, the range is fixed and the as-of is its `end_date`, with no fallback to `SCOPE_MAX`.</li><li>A separate `FollowUpScope` for the follow-up endpoint only, with the roster frozen at the as-of date.</li></ul> | [`agents/data_access.py`](agents/data_access.py) | <ul><li>No subject outside the manager's team, and no external name or ID in the pool.</li><li>No event after the as-of date; a July share reads as not shared on June 30.</li><li>A missing as-of stops the run.</li><li>`FollowUpScope` cannot add people.</li></ul> | Sonnet high |
| T2.2 | **`resolve_subject` tool.** Maps the plan's names, IDs and period to the roster. Matching ignores accents and case. Returns: process person / process 2-5 people / whole team / whole team with beneficiary focus / clarify (ambiguous, unresolved, or more than 5) / reject (a name that resolves to another team's person or another team, or a comparison with another team; returned to Original as a `declined` result with `reason_code = subject_out_of_scope`). An incoming `clarification.employee_id` is applied directly. A comparison with time ("last quarter") is a team question | `agents/discovery_tools.py` (new) | Unit tests cover each plan §3.2 case, including the comparison question, the beneficiary-only question, a re-planned name written differently, "Tomas" finding "Tomás", and an unresolved name giving a clarification instead of a stop | Sonnet medium |
| T2.3 | **`lowest_satisfaction` tool.** Returns the 10 least satisfied, ordered by score, then change, then ID | Same file | Deterministic order; ties broken | Sonnet medium |
| T2.4 | **`strongest_signals` tool.** Signal SQL for the plan §3.3 signals plus self-review entries. Requires at least two independent types; returns up to 5 more people. **Beneficiary-focus mode:** when the question names a beneficiary team, it returns up to 15 people ranked by independent signal types toward that team, then volume, then recency, and the satisfaction slot is not used (plan §3.3) | Same file | P5, P6 and D3 enter through this slot; in focus mode on "Infrastructure" in M32, every P4 member is returned | Opus medium |
| T2.5 | **Evidence prefilter and token count.** <ul><li>Item caps: 8 per person for a team question, 10 per person for 2-5 people, 25 for one person.</li><li>Within each person, closing context comes first. In beneficiary-focus mode, evidence about the named team comes first, then closing context, and team-pattern leads are computed only for that team.</li><li>Workload's normal range and repetition are computed inside the analysis window.</li><li>Texts are trimmed to 300 characters and keep their source IDs and `work_refs`.</li><li>Also includes name-in-other-people's-text matches, self-review items and team-pattern leads.</li><li>Caps are recorded.</li><li>Counts the pool's tokens for M32 and M14 offline with the provider's tokenizer.</li></ul> | Same file | Pool within caps; D1 and D3 keep their contradicting context; in focus mode the named team's evidence reaches the pool; recall gate (T6.2); measured token sizes recorded | Opus medium |
| T2.6 | **Precompute at import:** visibility events (including one dated `shared` event per share), quarter keys and the employee-name mention index, each with event and recorded dates | Generator or importer post-step | A July recognition does not hide a June finding; a July share does not mark June feedback as shared | Sonnet medium |

## 5. Phase 3: the Discovery agent

| ID | Task | Files | Done when | Model |
| --- | --- | --- | --- | --- |
| T3.1 | **Discovery agent: its own small class, not a `Specialist`.** The `Specialist` loop has 7 model turns and needs a terminal tool ([runtime.py:302-320](agents/runtime.py)), so Discovery does not use it. <ul><li>It runs the prefilter, then calls `budget.consume("model")` and `budget.respond(...)` directly for one judgment call (structured: findings, rejected, suggested action types). It allows one schema retry.</li><li>Own cap: 2 logical calls and a per-call time limit. Network retries belong to their logical call. A budget check runs before every call, including the schema retry, and gives `failed_budget` without calling. `DiscoveryTimeout` (T3.6) gives `failed_budget` without ending the run.</li><li>It calls `budget.refund(...)` in a `finally` block for every logical call, whatever the outcome.</li><li>Time limits, starting at 120/135 s and then set from a measured latency (one authorized call or the gate 10 p95): <ul><li>Each request's timeout is the time left before the 120 s limit, so 120 s is a real cap.</li><li>The profile's 135 s timeout is a backstop.</li><li>Before a retry backoff that would pass the limit, Discovery raises `DiscoveryTimeout` at once.</li></ul></li><li>Then come the code checks (T3.3), `work_refs`, the top-5 rule, the rendering (T3.5) and `discovery-result-v1`.</li></ul> | `agents/discovery.py` (new) | <ul><li>Offline replay with recorded outputs gives valid results.</li><li>It never makes more than 2 logical calls, even with network retries.</li><li>A timeout gives `failed_budget`, and the run continues.</li></ul> | Fable medium |
| T3.2 | **Role text.** For Discovery: <ul><li>cite only given IDs and quote exactly;</li><li>never say "not recognized" under unknown coverage;</li><li>team pattern versus person;</li><li>suggest action types only from the catalog;</li><li>no engagement, retention or productivity claims, and no ranking.</li></ul> For Original's planning rule: a team asked about or compared against goes in `subject_names`; a partner team named only as beneficiary goes in `focus_hint` | [`agents/policies.py`](agents/policies.py), `agents/discovery.py`, [`agents/original.py`](agents/original.py) (planning instructions near 76-91) | Role text reviewed against plan §3.1, §3.4-3.5 | Opus high |
| T3.3 | **Code checks.** <ul><li>IDs exist in the pool. Quotes are exact substrings of the pool's visible text (trimmed, with placeholders), and that text is what gets published. People are in scope.</li><li>No `not_recognized` under unknown coverage.</li><li>Action triggers fit the finding.</li><li>No external name or ID in the section; leaks are replaced and counted. Original's answer is never modified after review.</li><li>A failing finding is withheld and recorded.</li></ul> | `agents/discovery_checks.py` (new) | Synthetic bad outputs are all withheld | Sonnet high |
| T3.4 | **Register the role.** Model profile (the same GW model as Original) with its own `timeout_seconds` and `max_retries: 0`, so the SDK never repeats a request outside Echo's checks, and no pacing interval (135 s to start as a backstop, set from measured latency; today's profiles use 45 s). The per-call limit in T3.1 stays below it. Role registry and exports | [`connections.json`](connections.json), [`agents/connections.py`](agents/connections.py) (13, 41), [`agents/__init__.py`](agents/__init__.py), [`agents/runtime.py`](agents/runtime.py) | The CLI and Original can construct Discovery | Sonnet medium |
| T3.5 | **Section, pointer and action templates.** <ul><li>One draft template per action type (A1-A6), filled only from finding fields.</li><li>The pointer line per status (plan §3.5).</li><li>A renderer for the section: pointer, coverage, findings, action cards, and up to 5 further findings in one line each.</li><li>A per-draft privacy allow-list `(action_id, partner_manager_id)` for the A2/A4 recipient field only.</li></ul> | `agents/discovery_section.py` (new) | <ul><li>Rendering is deterministic.</li><li>The pointer count equals the findings shown, and there is no count when there are none.</li><li>Drafts contain no field outside the finding.</li><li>The partner manager appears only in their own recipient field.</li></ul> | Opus high |
| T3.6 | **Budget refund and Discovery timeout.** <ul><li>`RunBudget.refund(models, seconds)` adds to new `refunded_models` and `paused_seconds` fields. It never changes `models` or `deadline`.</li><li>`remaining()` and the effective deadline use the two fields.</li><li>Network retries inside a Discovery call are attributed to that call.</li><li>A new `DiscoveryTimeout` class, raised by `check_request_deadline()` within Discovery.</li><li>`connections.py` stores `timeout_seconds` on the model object as `request_timeout`. Only when `respond()` received a per-call deadline does `send_request` pass `timeout = min(time left, request_timeout)`; the other agents keep their client timeout.</li><li>In the retry path, `consume("model")` moves after the checks that can refuse a retry.</li><li>Both fields are recorded in `snapshot()`, `workflow_budget` and captures. `resume.py` keeps its arithmetic on raw values and adds the refunds explicitly.</li></ul> | [`agents/runtime.py`](agents/runtime.py) (97-161), [`agents/request_pacing.py`](agents/request_pacing.py) (20), [`agents/model.py`](agents/model.py) (74-97, 117-119), [`agents/connections.py`](agents/connections.py) (127), [`agents/capture.py`](agents/capture.py), [`agents/resume.py`](agents/resume.py) (222) | <ul><li>After the refunds, `remaining()` equals a run without Discovery.</li><li>Raw `models` minus the `request_transport_retry` events equals the number of `request_costs`.</li><li>Resume restores the refunds.</li><li>Outside Discovery, a run-level timeout is still a `RuntimeError`; inside, it gives `failed_budget`.</li><li>A hung request ends at the 120 s limit, not at 135 s.</li></ul> | Sonnet high |

## 6. Phase 4: connecting with the other agents

| ID | Task | Files | Done when | Model |
| --- | --- | --- | --- | --- |
| T4.1 | **Original: workflow order, subject check and Discovery step.** <ul><li>Add the §1.1 fields to the plan schema, update its key-set check, and add `"subject"` to the `missing_field` enum.</li><li>Use this single order in `workflow()`: `plan()` → `resolve_subject` → `set_delegations` → Discovery step → drafts loop.</li><li>The single rule: an unresolved name gets a clarification, and a name identified outside the manager's team is rejected. Both are normal `AgentResult`s with their message, not failures. A rejection reuses the existing `declined` status (`reason_code = subject_out_of_scope`), which the Brief, the presentation and the slide export already show; a clarification uses `needs_clarification`. A clarification fills `clarification_candidates` from the roster and uses `missing_field = "subject"`, with the name as written as `request_excerpt`. An incoming `clarification.employee_id` is applied directly.</li><li>Add `"Discovery"` to `planned_roles` only. The tool-to-role map (631) stays unchanged.</li><li>Add `setdefault` defaults for the four new plan fields in the non-live block (221-223), so saved plans and demo replays load.</li><li>Add one join point in `run()` that attaches `discovery_section` to every exit, including `incomplete()` (479-500, 1138).</li><li>The Discovery step is a new code path that runs on **every** in-scope question, once, before the drafts loop. There is no `needs_discovery` flag. Its result is kept for the run.</li><li>Nothing from Discovery is passed to the compose step.</li></ul> | [`agents/original.py`](agents/original.py) (162-265, 182, 627-631, 1024-1052) | <ul><li>Out-of-scope questions read no evidence.</li><li>`no_candidates` costs no model call beyond planning.</li><li>`failed_budget` and `failed_provider` still yield Original's answer.</li><li>The routing and clarification gates pass on recorded plans.</li><li>Original's remaining budget equals a run without Discovery.</li></ul> | Fable medium |
| T4.2 | **Original: release section and provenance.** <ul><li>Append the section after review, and add the `discovery_section` field.</li><li>The release check confirms the section is present for every status and identical to the checked result. When Discovery did not run, it is `{present: false, status: "not_run", finding_ids: []}`.</li><li>`self.discovery` is reset at the start of every `run()` (426-444).</li><li>The section is published even when Original's answer fails.</li><li>The section sits outside the 24-fact and 12-narrative limits and outside `release_counts`.</li></ul> | [`agents/original.py`](agents/original.py) (release path near 1083), [`check_release.py`](check_release.py) | Section present, exact and marked in every offline status case, including a failed Original answer and a declined question; a second question in the same process never carries the first one's section | Opus high |
| T4.3 | **Grounding: no change.** Original cites no Discovery IDs | none | Existing tests pass | — |
| T4.4 | **ZeroSugar: no change.** Its input and `review-v8` contract stay the same, because the section is appended after review. Discovery is not in `OWNERS` | none (verify only) | A test confirms that ZeroSugar's input contains no Discovery content | Sonnet medium |
| T4.5 | **Cherry, Vanilla, Lime: no functional change.** Team questions still get Cherry metrics and Vanilla sentiment when the plan asks for them | none | Existing tests pass | — |
| T4.6 | **Runtime plumbing and calibration.** <ul><li>Capture of Discovery's call, the refund, token accounting and execution-log events.</li><li>`discovery_applied` in every run record.</li><li>CLI: `--database`, the fixed `--start/--end` range on `discovery_v1`, and a `clarification` argument.</li><li>The `report-reader` agent definition reads `discovery_section`.</li><li>Release role loop and resume role maps.</li><li>Export shows the section's provenance.</li><li>Recalibrate the per-call time limit from measured offline sizes.</li></ul> | [`agents/capture.py`](agents/capture.py), [`agents/execution_log.py`](agents/execution_log.py), [`agents/resume.py`](agents/resume.py), [`run_agent.py`](run_agent.py), [`check_release.py`](check_release.py), `.claude/agents/report-reader.md` | A full offline workflow records Discovery's call, refund, tokens and `discovery_applied`; a range other than the fixed one on `discovery_v1` is rejected; the report reader reports Discovery findings | Sonnet medium |

## 7. Phase 5: actions, follow-up and UI

| ID | Task | Files | Done when | Model |
| --- | --- | --- | --- | --- |
| T5.1 | **Actions store.** A `manager_actions` SQLite store separate from the source database, with `POST/GET/PATCH /api/managers/{id}/actions`. States: proposed, then accepted, edited or dismissed with a reason. Each saved version stores its `work_refs`; an edit may remove references, or add only references from the same finding. Note in the README: the endpoints have no authentication (manager selection is a demo, not a login), so the store is for synthetic data only | [`../Echo_UI/backend/app.py`](../Echo_UI/backend/app.py) | Decisions persist across browsers and restarts; an edit with a foreign reference is rejected | Sonnet medium |
| T5.2 | **Follow-up endpoint.** Python code, no model. Uses `FollowUpScope` only. <ul><li>Per-action rules from plan §6.3 match person, `work_refs`, recipient and date.</li><li>A3 matches on `Topic_Code = workload`.</li><li>A4 matches a share event, using `Shared_With_Home_Manager_At` between the decision and the follow-up end.</li><li>Runs only for `accepted` or `edited` actions, from the decision date. A `proposed` action returns "pending decision". Uses the last saved version and skips dismissed actions.</li><li>With no match, coverage decides: complete gives `not_yet`; partial or undeclared gives `unknown`.</li></ul> | Same file | <ul><li>P1's A1 and A4 are observed, and P3 is not yet.</li><li>A proposed action gets no follow-up result.</li><li>An empty table under complete coverage gives not yet.</li><li>A share before the decision does not close A4.</li><li>Recognition for other work does not close A1.</li><li>Partial coverage gives unknown.</li></ul> | Sonnet high |
| T5.3 | **Frontend.** <ul><li>Sixth agent on stage.</li><li>A Discovery section with the "Checked by code; not reviewed by ZeroSugar" label, typed action cards, accept/edit/dismiss buttons and follow-up badges.</li><li>A "Simulation: observed means a record exists in the synthetic data" label.</li><li>No subject selector.</li></ul> | [`agents.ts`](../Echo_UI/frontend/src/lib/agents.ts), [`events.ts`](../Echo_UI/frontend/src/lib/events.ts), [`AgentStage.tsx`](../Echo_UI/frontend/src/manager/AgentStage.tsx), `AgentStrip.tsx`, `Brief.tsx`, Action Center files | Build passes; a manager can decide an action and see its follow-up. Through the manager projection: <ul><li>a run with Discovery shows six agents on stage, driven by `agent="Discovery"` events;</li><li>a declined out-of-scope question shows its message and a "Why" card with `checked_by: "code"` and two next steps, not "couldn't finish".</li></ul> | Sonnet medium |
| T5.4 | **Offline fixtures.** Discovery events, section and actions for offline/demo mode | [`../Echo_UI/backend/offline.py`](../Echo_UI/backend/offline.py) | The offline demo shows the sixth agent and its section | Sonnet medium |
| T5.5 | **Date and clarification transport.** <ul><li>The whole `discovery_v1` range is fixed at 2025-10-01 to 2026-06-30 and shown read-only.</li><li>The backend rejects any other or missing `start_date` or `end_date`, with no `SCOPE_MAX` fallback.</li><li>The clarification card shows the candidates and resends the original question plus `clarification`. The backend passes both to the run.</li></ul> | [`../Echo_UI/backend/app.py`](../Echo_UI/backend/app.py) (338, 396, 454), [`ManagerApp.tsx`](../Echo_UI/frontend/src/manager/ManagerApp.tsx) (440), clarification card | <ul><li>A UI question on `discovery_v1` runs with as-of 2026-06-30.</li><li>A missing or different start or end is rejected.</li><li>"What should I recognize Isabel for this quarter?" with two Isabels, answered "Isabel García", keeps "recognize" and "this quarter".</li></ul> | Sonnet medium |

## 8. Phase 6: tests and evaluation

| ID | Task | Files | Done when | Model |
| --- | --- | --- | --- | --- |
| T6.1 | **Unit tests** covering: <ul><li>plan fields; Discovery running on every in-scope question; rejection of comparison questions; beneficiary-only questions;</li><li>subject and period resolution;</li><li>both pool tools, as-of filtering and balanced selection;</li><li>placeholders and leak checks;</li><li>the top-5 rule, section rendering and the release check;</li><li>every Discovery status; the 2-call cap with network retries; the check before the schema retry; `DiscoveryTimeout`; refund fields with unchanged raw counters;</li><li>the pointer line per status, `discovery_section` provenance and publication when Original fails;</li><li>clarification with `missing_field = "subject"`, the resent question, and the ID applied when the re-planned name differs;</li><li>the fixed-range rules on `discovery_v1`;</li><li>`FollowUpScope` and each follow-up rule.</li></ul> | `tests/test_discovery_*.py` (new) | All pass | Sonnet medium |
| T6.2 | **Offline scorer** for gates 1-6 in plan §8, including at least 95% recall of the automatic plants across the 60 managers. It reads findings from `discovery_section`, not from `candidate.findings` | `score_discovery.py` (new) | A gate report with no model calls | Sonnet high |
| T6.3 | **Update existing tests and fixtures** that assume five roles or the old plan key set | `tests/`, `tests/fixtures.py` | Full offline suite passes | Sonnet medium |
| T6.4 | **Independent review** of the whole change before live runs | Diff of all phases | Findings fixed or recorded | Fable high (or `/code-review`) |
| T6.5 | **Live runs** (need user authorization). <ul><li>M32 and M14, each with and without Discovery.</li><li>One smoke run of the existing hard question with Discovery active (gate 10, not a regression measurement).</li><li>The M3 planning benchmark rerun: the floors hold (test 18, Gemini 17), and P12/P13 ask for clarification in all 8 runs (gate 11). If it fails, fix the planning instructions and rerun. If it still fails, move subject identification to a separate small call and restore `plan()`.</li></ul> | `reports/` | Raw results reported with `discovery_applied`; nothing replaced automatically | Run by the user. Use the `report-reader` agent or Haiku high to summarize |

## 9. Phase 7: documentation

| ID | Task | Files | Done when | Model |
| --- | --- | --- | --- | --- |
| T7.1 | **Update guides:** agents/workflow guide, testing guide, dataset documentation, UI and CLI READMEs, current-state sections | Files listed in [`DOCUMENTATION_MAP.md`](DOCUMENTATION_MAP.md), [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) | Links checked; implemented behavior and observed results kept separate | Sonnet medium |
| T7.2 | **Refresh the code graph** after code changes (`graphify update .`) | `graphify-out/` | Graph rebuilt | Haiku low |

## 10. Order and dependencies

```text
T0.1 approval ─┐
T0.2, T0.3 ────┼─> T1.1 ─┐
               └─> T1.2 ║ T1.3 ║ T1.4 ─> T1.5 ─> T1.6 ─> T1.7
T1.7 ─> T2.1 ─> T2.2 ║ T2.3 ║ T2.4 ─> T2.5 (T2.6 with T1.7)
T2.5 ─> T3.1 ─> T3.2, T3.3, T3.4, T3.5   (T3.6 parallel, needed by T3.1's tests)
T3.* ─> T4.1 ─> T4.2 ─> T4.4, T4.6
T3.5 ─> T5.1 ─> T5.2 ─> T5.3 ║ T5.4 ║ T5.5
T4.*, T5.* ─> T6.1, T6.3 ─> T6.2 ─> T6.4 ─> T6.5 (authorized) ─> T7.1, T7.2
```

`║` marks tasks that can run in parallel because they touch different files. T3.1 can start once the T2 tool signatures are frozen, using recorded fixture pools.

## 11. Rules for every task

- Code, prompts and documentation in English; explanations to the user in Spanish.
- Never read or print credentials. Never load an answer key into the runtime database or a prompt.
- Report what was actually run; offline results do not establish live quality.
- Before any code search in a subagent, run `graphify query "<question>"` first (project rule).

## 12. Implementation notes from the fifth audit (acceptance criteria)

These are code-level contracts. They are not design decisions. Each one belongs to the task named and is closed by that task's tests (T6.1), not by another plan version.

| Note | Task | Done when |
| --- | --- | --- |
| Discovery's result lives in `AgentResult.discovery`, not in `child_results`. `delegate()` is never called with "Discovery", because `specialist()` would build a Vanilla for any name other than Cherry | T4.1 | `check_handoff` passes in every run with Discovery; ZeroSugar's task outcomes contain no Discovery entry; the UI stage reads `AgentResult.discovery` |
| The section lives in `discovery_section.rendered`, never in `answer` | T4.2 | The audit's `candidate_id(released["answer"], ...)` matches the reviewed candidate; `discovery_section` is present on every exit of `run()`, including both `incomplete()` paths (479-500, 1138). Original catches its errors itself, so the `run_agent.py` failure artifact is not the path |
| Every budget enforcement point uses the effective values: `consume()`'s call and deadline checks, the request deadline set in `respond()`, and the retry path (`consume` on retry, `remaining()["seconds"] <= delay`) | T3.6 | With 2 refunded calls, Original's closing turn at exhaustion completes. Seconds are extended by `paused_seconds`. Within Discovery, the retry path raises `DiscoveryTimeout` |
| `respond()` accepts an optional per-call deadline. The request deadline is the earlier of that and the effective run deadline | T3.6 | Each Discovery request's timeout is the time left before its 120 s limit, capped by the model's stored `request_timeout`; other agents get no per-request timeout. A logical call ends by about 120 s. Before a retry backoff that would pass the limit, `DiscoveryTimeout` is raised at once. The 135 s profile timeout is a backstop. The run deadline still applies |
| `resume.py`: `remaining_seconds` in `snapshot()` already reflects the effective deadline, so resume adds nothing; the model check uses effective calls. Original workflows are not resumed (`original.py:427-428`), so this matters only for specialist checkpoints and captures | T3.6 | No double counting; a run with refunded calls is not rejected as exhausted |
| `missing_field` enum duplicated in the schema (182) and its validation (327-328) | T4.1 | Both include `"subject"`; a code-built clarification basis passes validation |
| `recording_key(manager, start, end, question)` ignores the clarification (`app.py:351`) | T5.5 | The key includes the clarification's `employee_id`; the demo replay tells the first request from the second |
| Panels outside the run (`manager_pulse`, `partners`, `updates`) default to `SCOPE_MAX` | T5.5 | On `discovery_v1` they use the fixed range, or show their own range label, so a July event is not shown next to an "unrecognized at June 30" finding without explanation |
| The section's further findings and the period line | T3.5 | The result carries `more_findings.listed` (at most 5 `{finding_id, employee_id, beneficiary_team}`) and `more_findings.not_listed`, matching §1.3. `period.narrowed_from_hint` is rendered as a period line |
| Coverage precedence | T3.3, T5.2 | Findings read row-level `Record_Coverage`; follow-up reads `OP_source_coverage`; neither reads the other |
| Pointer wording | T3.5 | "N findings about contributions to other teams"; a team-pattern finding counts as one and names its people |
| Evaluation tooling reads the section | T4.6, T6.2 | `report-reader` and `score_discovery.py` read `discovery_section` |
| Clarification transport | T5.5 | `RunRequest` gains `clarification` (`app.py:335-344`). The manager view passes `clarification_candidates` through instead of emptying the clarification (`app.py:537`). The backend accepts only an `employee_id` from the manager's roster |
| `run_seconds` for demo and gate runs | T4.6, T6.5 | Each run states its `run_seconds`. The UI default is 900 s (`app.py:344`) and the CLI default is 300 s, so gate reports name the value used |

**Errata 1 (sixth audit).** The rows above were added or corrected after the sixth audit, matching plan §14. The design is unchanged.

**Errata 2 (seventh audit).** These rows match plan §14, Errata 2:

| Note | Task | Done when |
| --- | --- | --- |
| The manager page shows the section | T5.5 | `discovery_section` is in the manager-view allow-list (`without_comment_text`, `app.py:514-541`). A test against `/api/runs/{id}?view=manager` finds it; testing the artifact alone does not count |
| Refund on every outcome | T3.1, T3.6 | After a `DiscoveryTimeout`, a provider failure or a schema failure, `remaining()` equals a run without Discovery |
| Privacy gate scope | T3.3, T4.2 | No external name in the Discovery section except the A2/A4 recipient. Original's released answer is byte-identical to the reviewed candidate |
| "Not recognized" | T3.3 | Allowed only if every cited feedback row is `complete` and `HR_recognition_events` coverage is `complete` for the work's team and quarters; otherwise `unknown` |

**Errata 3 (eighth audit).** These rows match plan §14, Errata 3:

| Note | Task | Done when |
| --- | --- | --- |
| A fully specified declined result | T4.1 | The result carries: <ul><li>`task_outcome = {status: "declined", reason_code: "subject_out_of_scope"}`;</li><li>`verification = {decision: "declined", drafts_checked: 0}`;</li><li>`guardrail = {rule, detail, checked_by: "code"}`;</li><li>two `next_steps`.</li></ul> Two tests on the manager projection. The offline declined artifact is not copied |
| The stage comes from events | T4.6, T5.3 | Discovery emits `agent_turn` and finish events with `agent="Discovery"`. `AgentResult.discovery` is not projected to the page |
| Latency-based time limit | T3.1, T3.4, T6.5 | The pair starts at 120/135 s and is set from a measured latency. A latency `failed_budget` in gate 10 is investigated, not accepted |
| Named `partial` coverage row | T1.3, T1.7 | Exactly one `OP_source_coverage` row is `partial`, and gate 4 uses it |
| One-line findings carry `finding_id` | T3.5 | `finding_ids` covers detailed and one-line findings; the pointer count equals `len(finding_ids)` |

**Errata 4 (ninth audit).** These rows match plan §14, Errata 4:

| Note | Task | Done when |
| --- | --- | --- |
| Boundary-check semantics of the 120 s limit | T3.1, T3.6 | **Superseded by Errata 5:** a hung call ends at the 120 s limit with `failed_budget` |
| No SDK retry | T3.4 | Discovery's profile has `max_retries: 0`; a test loads it and checks the value |
| Gate 4's `partial` case | T5.2, T6.2 | A code-built, accepted A4 from an M41 plant, with no later share, against the named `partial` row, gives `unknown` |
| The "Why" card check | T5.3 | The test reads `guardrail.checked_by` from the manager projection; the card shows `rule` and `detail` |

**Errata 5 (tenth audit).** These rows match plan §14, Errata 5:

| Note | Task | Done when |
| --- | --- | --- |
| Call count with network retries | T3.6, gate 6 | Raw `models` minus the `request_transport_retry` events equals the number of `request_costs` |
| 120 s is a real cap | T3.6 | A test with a request that never answers ends at about 120 s with `failed_budget`; a 5xx at 90 s gives a retry with only the time left |
| Which deadline expired | T3.6 | Inside Discovery either expiry gives `failed_budget`; Original then has the seconds it had before Discovery |
| No pacing | T3.4 | Discovery's profile has no `request_interval_seconds`; a 429 gives `failed_provider`, refunded |

**Errata 6 (eleventh audit).** These rows match plan §14, Errata 6:

| Note | Task | Done when |
| --- | --- | --- |
| Refused retry is not counted | T3.6 | In the "request never answers" test: `models` = 1, `request_costs` = 1, `request_transport_retry` events = 0 |
| Per-request timeout only for Discovery | T3.6 | A test shows Original's requests carry no per-request `timeout` (still 45 s), and Discovery's carry at most the time left |
