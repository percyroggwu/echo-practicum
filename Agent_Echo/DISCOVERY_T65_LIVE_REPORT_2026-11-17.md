# Discovery T6.5 live runs, 2026-11-17

Status: in progress. Runs were made by the user with the `gw_azure` profile on `discovery_v1`
(2025-10-01 to 2026-06-30). Results are recorded as measured; nothing was replaced or rerun automatically.
Plan: [DISCOVERY_SCOPE_AND_PLAN_v10_2026-11-15.md](DISCOVERY_SCOPE_AND_PLAN_v10_2026-11-15.md) section 8.

## Gate 7, selection only (all 60 teams): fail, recorded

Run: `run_discovery_selection.py --profile gw_azure`, one selection call per team, 8 s apart.
Output: `reports/discovery_t65_selection.json`; score: `reports/discovery_t65_gate_report.json`
(`score_discovery.py --selection-report`).

| Measure | Value |
|---|---|
| Teams | 60 (55 with a selection call, 5 small teams with none) |
| Calls / failures / schema retries | 55 / 0 / 0 |
| Input / output tokens | 224,507 / 2,145 (plan estimate: 200-250k input) |
| Latency per call | median 1.6 s, max 11.3 s |
| Automatic plants | 120 |
| Reached by the code slot | 47 |
| Left to the selection call | 73; the model picked 45 (62%); random choice would reach about 18 |
| **Pool recall** | **92 / 120 = 77%** (target at least 95%) |

- All 28 missed plants are single-person plants whose person was in the summary the model saw.
  The misses are model choices, not code gaps. Which people were picked instead was not analyzed.
- M14 did not pick E0001 (P5), which the plan expects. M32 missed P3, P4, P6 and PL-M32-1.
- Missed by team: M01 (2), M03, M04, M05, M07, M11 (2), M12, M14 (2), M15, M17, M19, M20, M26 (2),
  M27, M29, M30 (2), M31, M32 (4), M33, M34, M39 (2), M48, M60. P3-P6 are not automatic plants and are
  not in the 120.
- n = 1 per team; run-to-run variance was not measured.
- **Decision (user, 2026-11-17):** record the result and continue. The team questions still measure
  whether Discovery finds what reached its pool.

## Team questions, first attempt: Discovery did not run

"How is my team doing?" for M14 and M32, with and without Discovery (`--no-discovery`).
Outputs: `reports/discovery_t65_m14_team(_off).json`, `reports/discovery_t65_m32_team(_off).json`.

- All four ended in `needs_clarification` after 1 call. Original's planner asked for a metric
  (`missing_field = "metric"`: survey trends, cross-team contributions or comment themes).
- The planning clarification returns before the subject check, so Discovery never runs on a question the
  planner finds too broad. `discovery_applied` is false in all four.
- This is a design gap the offline tests did not show, because they use a fixed plan. Plan section 2 gives
  "How is my team doing this quarter?" as an example question. Changing the planner would touch gate 11
  (P12 and P13 must still ask for clarification). Not changed.
- Next attempt: "How is my team doing on cross-team contributions?", same four runs.

## Team questions, second attempt: "How is my team doing on cross-team contributions?"

Outputs: `reports/discovery_t65_m14_team2(_off).json`, `reports/discovery_t65_m32_team2(_off).json`.
Score: `reports/discovery_t65_gate_report2.json` (`artifact_section_coverage`). The pool is read from
the reviewed people (findings plus model rejections, 10 per team); the artifact does not list pool IDs.

| Run | Status | Original calls | Discovery calls / input tokens | Drafts | Findings |
|---|---|---|---|---|---|
| M14 with | complete, accepted | 6 | 2 / 21,885 | 1 | 2 |
| M14 without | complete, accepted | 6 | none | 1 | none |
| M32 with | complete, accepted | 11 | 2 / 24,672 | 2 | 3 |
| M32 without | complete, accepted | 7 | none | 1 | none |

Both answers are the same Cherry table with a different interpretation; Discovery's section is the only
added content. Discovery does not feed Original's compose step, so the extra M32 draft is attributed to
run variance (n = 1), not to Discovery. Discovery's input was 22-25k tokens per run, above the plan's
16-18k estimate.

| Manager | Plant | In the pool | Result |
|---|---|---|---|
| M14 | P5 (E0001, hand built) | no | missed by selection |
| M14 | PL-M14-1 (E1412) | yes | **found** (DISC-1, A1/A4/A5) |
| M14 | PL-M14-2 (E0135) | no | missed by selection |
| M32 | P1 (E0010) | yes | **found** (DISC-1) |
| M32 | P4 (E1401, E1586, E0561) | 2 of 3 | **found** both pool members (DISC-2, DISC-3) |
| M32 | P2 (E2156) | yes | rejected by the model: `insufficient_evidence` |
| M32 | PL-M32-1 (E2293) | yes | rejected by the model: `insufficient_evidence` |
| M32 | PL-M32-2 (E1439) | yes | rejected by the model: `effort_without_impact` |
| M32 | P3 (E0728), P6 (E0970) | no | missed by selection |

- **Recall in the pool:** M14 1 of 1; M32 3 of 6 (counting P4 as found). The plan's "Discovery finds every
  positive that reached the pool" fails on M32.
- **Decoys:** none of D1-D8, PD-M14 or PD-M32 was reported. This point passes.
- **Unplanted finding:** M14 DISC-2 (E1580, Financial Planning) matches no plant or decoy. Not verified.
- **Selection variance:** M14's selected people differ from its gate 7 run; the question differs too.
- **Rendering:** one quote starts mid-word ("orking with Zoe Allen..."). Cosmetic; not investigated.

## Jonah question (M14, full workflow, after the fixes)

"What work has Jonah done for other teams that I may not have seen?" Output: `reports/discovery_t65_m14_jonah.json`.

- Complete and accepted. Original made 16 calls (planning, Cherry, ZeroSugar review); Discovery made 1
  call (named person, no selection), 7,092 input tokens.
- **Discovery found E0001 (Jonah Meyer, case P5)** with Customer Renewals as the beneficiary.
- **Original's answer contradicts it.** Cherry's query used `Employee_Name = 'Jonah'`, so it returned no
  rows, and the answer says no Jonah-specific cross-team work can be listed. The subject check had
  resolved the name to E0001, but the resolved ID is not passed to Cherry or Vanilla.
- **Fixed (2026-11-17, offline).** Original now adds the resolved people (ID and full name) to every Cherry
  and Vanilla task context, with a note to filter by `Employee_ID`. Confirm live with `jonah2`.

## Scope decisions (user, 2026-11-17)

- Gate 7 is not critical: a pool that is 5+5 (or 3+5) without the optimal five is acceptable.
- Gate 8 and D8 are skipped.
- The live demo with the professor uses M14 and Jonah Meyer (E0001).

## Still to run

The `jonah2`, `hidden` and `hard` rows ran on 2026-11-17: see [Live M14 round](#live-m14-round-10-runs-2026-11-17).
Gate 11 is still to run. The next round is listed in [Next live round](#next-live-round).

| Report | Question | Expected |
|---|---|---|
| `reports/discovery_t65_m14_jonah2.json` | The Jonah question, after the name fix | Cherry filters by `Employee_ID`; Original's answer and the Discovery section agree |
| `reports/discovery_t65_m14_hidden.json` | "Who on my team helped other teams without that work being visible to me?" | Discovery runs; cases found, no decoys; clean quotes |
| `reports/discovery_t65_m14_hard.json` | The hard sentiment question, Q2 2026 (gate 10) | Completes with `discovery_applied` true |
| `reports_gold/plans_apinex_test_<UTC>.json`, `reports_gold/plans_apinex_gemini_test_<UTC>.json` | M3 planning benchmark (gate 11) | Floors hold (test 18, Gemini 17); P12 and P13 ask for clarification in all runs |

## Diagnosis and fixes (2026-11-17)

These are offline checks only, with no live calls.
- The databases were opened read-only, and their hashes are unchanged.
- The answer key was read for diagnosis only. Runtime code, instructions and tests hold no plant IDs, employee IDs or case names. The new tests use synthetic data.
- Frozen decisions are kept:
  - a pool of 10: 5 picked by code, 5 by the model;
  - at most 8 items per person;
  - 3 logical calls;
  - no coded ranking.

**Scope (user decision, 2026-11-17).** Vague questions such as "How is my team doing?" are out of scope for Discovery testing. Live tests ask specific cross-team questions. The planner is not changed.

### 1. Selection (gate 7 pool recall 77%)

**Cause.** We rebuilt the old summary for the 55 selection teams (1,580 lines). Those teams had 78 plants left to selection: the model picked 46 and missed 32. Every distinguishing fact was already in the summary, but it was buried.

- **Volume dominated.**
  - Almost everyone helps about 12 teams, with 56-112 help records each.
  - Per-person totals hid the one partner team that stood out.
  - 53% of picks were in the team's top quartile by `help_records`, against 25% expected by chance.
  - Picked non-plants averaged 112.6 help records. Missed plants averaged 78.1.
- **The rare fact sat mid-table.**
  - `threads_without_request` > 0 holds for 65 of 78 plants, including 26 of the 32 missed.
  - It holds for only 36 of 1,502 non-plants.
  - It was the 7th of 17 numeric columns. Only 53 of the 275 picks had it.
- **The instruction misdirected.**
  - It cited "missing recognition events", but `recognition_events` counts all recognition, for any work. 32% of picks had none, against 3% of missed plants.
  - It cited "sustained extra load". 48% of picks had 6 or more weeks above the load range, against 31% of plants.
- **The summary was long.** It averaged about 2.2k tokens per team, mostly the `help_by_team` tail.
- **A column was duplicated.** `linked_blockers` always equalled `blockers_resolved`.

**Fix.**
- `agents/discovery.py:65-87` (`SUMMARY_COLUMNS`, `summary_table()`). Rare facts now come first and volume columns last.
  - New counts:
    - `partner_teams_praise_not_shared`: partner teams whose feedback is all unshared.
    - `partner_feedback_not_shared`
    - `partner_teams`
  - Renamed: `recognition_events` is now `recognition_events_any_work`.
  - Removed:
    - `help_by_team`
    - `contributions`
    - `threads_answered`
    - `partner_feedback`
    - `feedback_shared`
    - `linked_blockers`
  - The table stays in ID order, with no names and no score or satisfaction words.
  - `team_summary` lines, which the scorer checks, are unchanged.
- `agents/policies.py:43` (`DISCOVERY_SELECTION`). The instruction now:
  - treats volume and load as background;
  - points the model at facts that are rare within the table;
  - prefers people who combine several such facts;
  - says the recognition count does not show whether this work was recognized.

**Offline measurements.**

| Measure | Old summary | New summary |
|---|---|---|
| Summary text, 55 teams | 493,683 chars (about 123k tokens) | 74,803 chars (about 19k tokens) |

Token counts are chars/4 estimates.

| Fact present on the line | Plants | Missed plants | Non-plants |
|---|---|---|---|
| `threads_without_request` > 0 and `partner_teams_praise_not_shared` > 0 | 58 of 78 | 22 of 32 | 11 of 1,502 |
| Either of those two facts | 77 of 78 | 31 of 32 | - |

The combined pattern averages 1.25 lines per team, so it fits within 5 picks.

These checks cannot show whether the model now picks these people. Gate 7 must be rerun live.

**Tests.**
- New: `tests/test_discovery_selection_summary.py`, 5 tests, pass.
- Existing and unchanged: `test_discovery_phase4.py` (12 tests) and `test_discovery_t65_runners.py` (7 tests), pass.

### 2. Judgment (M32: three pool plants rejected)

**Cause.** Re-running `prefilter` on the logged selections reproduced both logged payloads exactly. The model returned only reason codes, so the causes come from comparing the payloads with the database.

Two defects in the evidence affected all three people.
- **Wasted slots.**
  - Only 6 of the 8 slots are free; the activity row and the self-review row are reserved.
  - Goal and outcome rows for every linked goal took first-round priority, up to 4 slots.
  - They pushed out the person's own contribution ("Accepted a short written summary...") and the second unshared feedback row.
- **Truncation in `_excerpt`.**
  - It cut each text to the sentence naming the person, which lost blocker closing context ("Closed after 5 days.").
  - When no sentence break came before the name, `rfind()` returned -1. The +2 then gave index 1 and dropped the first character ("orking", "hanks", "ositive feedback").

Per person:
- **E2293 (`insufficient_evidence`).**
  - The payload held one thin, cut feedback row, a blocker cut to its last sentence, and two goals, one missed.
  - The contribution and two feedback rows were outside the cap.
- **E1439 (`effort_without_impact`).**
  - The payload held two missed partner goals and the blocker without its closure.
  - The acceptance and the unshared feedback were outside the cap.
  - The instruction never said that a missed partner goal does not disprove the person's own impact.
- **E2156 (`insufficient_evidence`).**
  - All 14 informal threads exist in the database.
  - `help_by_team_and_quarter` showed 15 and 37 records over two quarters. The items sampled 2 threads.
  - This is mainly an instruction gap: nothing said that repeated informal help counts without feedback, or that the items are a sample.

Other findings:
- **M14 DISC-2 (E1580).** This is likely a false positive, although its facts are true.
  - The cited contribution is formal assigned work: the work request was completed on time, and `Work_Request_ID` was in the payload.
  - There is no unshared praise, no informal channel and no workload signal.
  - The finding rested only on no feedback and no recognition. The instruction had no rule for formal requests.
- **The quote "orking with Zoe Allen..." (M14 DISC-1).** The code cut it, not the model: it is the `_excerpt` bug above. The quote check passed because it compares against the same damaged text.

**Fix.**
- `agents/discovery_tools.py:507-527` (`_excerpt`):
  - Texts of 300 chars or less are kept whole.
  - The sentence start is used only when `rfind` finds one.
  - A forced start and the end both fall on word boundaries.
- `agents/discovery_tools.py:620-636` (`_person_items`):
  - Only the latest goal goes in the first round, as its latest outcome plus its target.
  - Other goal rows, and repeated outcomes of the same goal, go after all other candidates.
  - The cap and the reserved slots are unchanged.
- `agents/policies.py:61` (`DISCOVERY_JUDGMENT`):
  - Items are a sample. The counts cover all records.
  - Short feedback that names the person counts as praise.
  - Impact is any of these:
    - a closed blocker;
    - work the partner accepted or used;
    - a thread the partner thanked or confirmed done;
    - feedback naming the work.
  - A partner goal outcome alone does not show that the person had no impact.
  - Formal work-request work is reported only with unshared praise or misattributed credit. Missing feedback alone is not enough.
  - Repeated informal help to one team counts as hidden cross-team work without feedback only when it comes with weeks above the team range (reported as `no_feedback` with A3). Without that load it still needs an impact sign. Many threads with no acceptance, an open blocker and a missed goal stay `effort_without_impact`.
  - Review note (coordinating session, 2026-11-17): the subagents' first wording reported repeated informal help even without load or acceptance. That contradicted the plan's decoy D2 (many threads, no acceptance, goal missed, blocker open: no impact claim), so it was tightened to the plan's own A3 and impact rules. The Discovery test files pass after the change (132 tests).
  - `insufficient_evidence` applies only when no item and no count shows the person's own work for another team.

**Offline measurements.**

| Measure | Before | After |
|---|---|---|
| M32 payload | 53,058 chars | 54,931 chars (+3.5%) |
| M14 payload | 51,624 chars | 54,676 chars (+5.9%) |

Planted rows that reach the payload, across all 120 automatic plants:

| Planted rows | Before | After |
|---|---|---|
| Contributions | 0 of 45 | 43 of 45 |
| Unshared feedback rows | 135 of 285 | 188 of 285 |
| Plants with at least 2 unshared feedback rows plus a work row | 6 | 54 |
| Goal rows | 99 of 101 | 54 of 101 |

Goal rows fall by design: one goal pair is kept per person.

For the M32 people:
- E2293 and E1439 now carry the full-text blocker, both unshared feedback rows, the contribution and one goal pair.
- E2156's items are unchanged except for the repaired text.

These checks cannot show:
- how the model now judges these people;
- whether the repeated-help rule adds false positives on workload-only decoys (D4 style);
- whether the formal-request rule suppresses a real finding.

**Tests.**
- New: `tests/test_discovery_judgment_items.py`, 7 tests, pass.
- Existing and unchanged, all pass:
  - `test_discovery_prefilter`
  - `_t25`
  - `_phase2_boundaries`
  - `_phase3`
  - `_phase6`
  - `_signals`
  - `_t23`
  - `_t24`
  - `_subject`
  - `_precompute`
  - `_satisfaction`
  - `_access`
  - `_t65_runners`
  - `test_ui_offline_discovery`

**Full suite.** 512 tests passed, 4 skipped (`data/discovery_t65_fix_unit_results.txt`). Database hashes are unchanged.

### 3. Decisions

1. **Selection framing: accepted by the user (2026-11-17).** The column order and the instruction favor facts that are rare within the team. No code ranks people and the model still chooses.
2. **Load in selection: accepted by the user (2026-11-17).** The selection instruction now treats load as background, matching `workload_only` in judgment. People whose only signal is load (A3 style) are less likely to be chosen by the model. They can still enter through the code slots.

Still open, decided only after the next live gate 7:
3. **If live gate 7 stays below 95%.** The options change frozen decisions:
   - a larger model share of the pool;
   - or a second selection call, which is a 4th logical call costing about 0.3k summary tokens per team plus latency.
4. **The 8-item cap.** It leaves only 6 usable slots.
   - Showing more distinct informal threads (E2156 type) needs a higher cap, at about +4% payload per extra item.
   - Freeing the activity row instead means changing an existing test.

### 4. Recommended live reruns

- **Gate 7:** rerun selection only.
- **M14:** superseded by the "Still to run" table above ("this year" would narrow the period to 2026).
- **M32:** "Who on my team helped other teams without that work being visible to me?"

## Live M14 round, 10 runs (2026-11-17)

All `gw_azure`, full Original workflow, `discovery_v1`, manager M14. Summarized from the reports and their logs
(`reports/logs/<run_id>.jsonl`). `jonah2` ran before the Jonah name fix; `jonah2_2` and `jonah2_3` after it.
M14's cases: E0001 (P5, Customer Renewals), E1412 (PL-M14-1, Budget Controls), E0135 (PL-M14-2, Commercial
Finance); decoy E1254 (PD-M14). D1-D8 are all M32.

| Run | Status | Discovery findings | Discovery calls | Reviews | Drafts | Wall s | Tokens total |
|---|---|---|---|---|---|---|---|
| `jonah2` (pre-fix) | accepted | E0001 | 1 | revise, accept | 2 | 44.5 | 45.6k |
| `jonah2_2` | accepted | E0001 | 1 | revise, accept | 2 | 52.8 | 62.3k |
| `jonah2_3` | accepted | E0001 | 1 | revise, accept | 2 | 93.8 | 113.9k |
| `hidden` | accepted | E1412, E0135 | 2 | 3 | 3 | 70.1 | 108.8k |
| `hidden_2` | accepted | E1412, E0135 | 2 | 4 | 4 | 84.2 | 114.1k |
| `hidden_3` | **partial** | E1412, E0135, E0001 | 2 | 1 (accept, Completeness 1) | 1 | 36.5 | 42.7k |
| `hidden_4` | accepted | E1412, E0135, E0001 | 2 | 3 | 3 | 66.5 | 88.6k |
| `hard` | **partial** | E1412, E0135 | 2 | 4 revise | 4 (limit) | 218.0 | 285.8k |
| `hard_2` | accepted | E1412, E0135, E1183 | 2 | 2 | 2 | 165.2 | 221.2k |
| `hard_3` | accepted | E1412, E0135, E0001, E1183 | 2 | 1 | 1 | 68.1 | 121.3k |

- **Per role (input tokens).** Discovery used 20.6-20.9k per team question and 7.1k per named person, about
  20% of a team run; repair loops are dominated by Original and ZeroSugar (about 100k each in `hard`).
  Lime never ran. `hard` waited 60 s on three HTTP 429 retries, `hard_2` 40 s on two.
- **Jonah fix.** `jonah2_2`: `WHERE c.Employee_ID = 'E0001' AND c.Home_Team <> c.Beneficiary_Team`, 22 rows
  including Customer Renewals; the answer agrees with Discovery. `jonah2_3`: the plan asked Cherry to match
  team names in project titles; the query filters E0001 but returns 6 records / 3 names, and the answer
  omits Customer Renewals.
- **Discovery rules.** In all 10: at most 2 calls, no schema retry, every call refunded, checked by code and not
  reviewed by ZeroSugar. Quotes are whole sentences (not compared with the source messages).
- **`hidden_3` (partial).** Cherry called only `describe_schema` and declined ("aggregate counts only").
  A decline blocks acceptance, so the run was partial although ZeroSugar accepted; the limitation said
  "The numerical calculation or its population still requires correction". The answer said nobody could be
  identified while the Discovery section named three people.
- **`hard` (partial).** The plan's `period_hint` was "the second quarter of 2026", which the period reader
  did not recognize (`hint_not_applied`), so the run kept the fixed 9-month window. Vanilla's sentiment report
  covered three survey waves; Original can only edit text, and ZeroSugar asked three times to remove the
  non-Q2 rows until the draft limit. `hard_3` had the same evidence and was accepted: reviewer variance on the
  same defect. Discovery also reviewed all nine months for this question.
- **E1183.** One blocker (`BLK000284`, one day, Talent Development vs Campaign Operations). 18 people in M14
  resolved 36 such blockers in the window. Unplanted and weak; accepted as noise (user decision).

### Fixes after this round (offline only)

User decisions: P1 implement; P2 option a; P3 the period must always apply; P4 agreed; P5 accept as noise;
P6 run in parallel without extra request spacing; keep the Discovery section on every in-scope answer.
See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) ("Follow-up fixes") for the change list. The plan's
"Discovery before the drafts loop" is superseded: Discovery now runs beside Original and is joined in `run()`.

**Offline checks (2026-11-17).** The project venv points to a removed Python, so the suite ran on the system
Python 3.12.10, which lacks `fastapi` and `python-dotenv`: 488 tests ran, 4 skipped, 10 errors, all from the
environment. Four UI test modules and one Phase 6 test cannot import `fastapi`; four provider-connection tests
need `dotenv`; `test_request_pacing` reads the local ignored `connections.private.json`, which has no
Discovery role (it passes, 13 of 13, on a clean checkout of HEAD). The seven new tests pass. The UI tests were
not run for this round. No live calls.

**Environment fixed (2026-11-17).** `Agent_Echo/.venv` was recreated from the installed Python 3.12.10 with
both requirements files; the old Echo_UI environments were removed. Full suite: 522 tests, OK, 4 skipped,
including the UI tests.

### Next live round

The reports to generate after these fixes, with the commands and what each should show, are listed in
[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) ("Next live runs").

## Live M14 fix2 round, 12 runs (2026-11-18 UTC)

Run after the follow-up fixes P1-P4/P6 (commit `0afc67a`). All `gw_azure`, `discovery_v1`, M14, `--run-seconds 1000`.
Reports `reports/discovery_t65_m14_fix2_<question>_<n>.json`, logs `reports/logs/20261118_*.jsonl`. Tokens are
input+output summed over `model_response_usage`, attributed to the agent of the following `model_finished`.

| Run | Status | Drafts | Reviews | Wall s | Tokens | Top role | Discovery findings |
|---|---|---|---|---|---|---|---|
| `jonah_1` | complete | 2 | revise, accept | 44.0 | 82.4k | ZeroSugar | E0001 |
| `jonah_2` | complete | 1 | accept | 30.0 | 54.8k | ZeroSugar | E0001 |
| `jonah_3` | complete | 3 | revise, revise, accept | 49.2 | 66.3k | Cherry | E0001 |
| `hidden_1` | complete | 1 | accept | 36.3 | 89.8k | Cherry | E1412, E0135, E0001 |
| `hidden_2` | **partial** (Cherry declined) | 1 | accept | 46.1 | 43.2k | Discovery | E1412, E0135 |
| `hidden_3` | **partial** (Cherry declined) | 1 | accept | 24.5 | 43.5k | Discovery | E1412, E0135, E1876 |
| `hidden_4` | complete | 2 | revise, accept | 32.9 | 49.5k | Discovery | E1412, E0135, E0001 |
| `hidden_5` | complete | 1 | accept | 21.9 | 40.2k | Discovery | E1412, E0135, E0001 |
| `hard_1` | complete | 2 | revise, accept | 59.3 | 107.5k | Original | none |
| `hard_2` | complete | 1 | accept | 63.7 | 92.5k | ZeroSugar | none |
| `hard_3` | complete | 1 | accept | 62.8 | 92.0k | ZeroSugar | none |
| `hard_4` | complete | 2 | revise, accept | 95.9 | 138.0k | Original | none |

- **Means.** jonah 41.1 s / 67.9k tokens; hidden 32.3 s / 53.2k; hard 70.4 s / 107.5k (previous round: hard 121-286k).
  All 12 runs: 900k tokens, 567 s. By role: ZeroSugar 247k (27.5%), Original 225k (25.0%), Discovery 208k (23.1%),
  Cherry 117k (13.0%), Vanilla 103k (11.4%); Lime never ran. Discovery per run: about 7.4k (jonah), 21.5k (hidden),
  19.4k (hard).
- **Expectations met.** jonah: no `scope_narrowed`; Cherry filters `Employee_ID = 'E0001'` with
  `Home_Team <> Beneficiary_Team` in 3/3, no project titles. hard: `scope_narrowed` to 2026-04-01..2026-06-30 in 4/4,
  Discovery period Q2, no non-Q2 correction, Vanilla about 25.7k (was 45.7k), 4/4 complete. P1's decline text appears in
  `hidden_2`/`hidden_3`. P2's line is in every section with findings. Discovery: at most 2 calls, no schema retry,
  not reviewed by ZeroSugar, runs beside Cherry/Vanilla; the checkpoints' budget shows `paused_seconds` 0.0 and
  `refunded_models` equal to Discovery's calls in all 12 (the report JSON carries no budget).
- **Not met.** jonah: the answer names Customer Renewals in 2/3 (`jonah_3` no).

### Diagnosis (2026-11-18; proposals not approved or implemented)

- **D1. Aggregate answers to "who" / "what work" questions** (`hidden_2`-`hidden_5`, `jonah_3`). The planner always
  requests `cross_team_contributions` with `dimension=null` (one team-level row); Original asks Cherry whether evidence
  exists ("if none, say so"); Cherry's instruction prefers that metric. Cherry then submitted the aggregate without SQL
  (`hidden_4`/`_5`), declined after `describe_schema` (`hidden_2`/`_3`), or aggregated its own query to 18 distinct
  teams without naming them (`jonah_3`). The answers say the data cannot identify people or teams, although
  `OP_contributions` has both per row; the Discovery section below names them. Completeness review has no source
  evidence by design, so it accepted. Only `hidden_1` queried per person (its answer lists E1254 and E1183 from an
  exploratory column).
- **D2. Original answers before delegating.** First `submit_answer` without evidence rejected (`evidence_required`) in
  `jonah_1`, `jonah_2`, `hidden_1`, `hidden_4`, `hidden_5`; in `jonah_3` an empty draft reached a full review.
- **D3. No Discovery findings in Q2** (hard 4/4): all 10 pool people rejected `insufficient_evidence`. Plants are spread
  over 2025-Q4, 2026-Q1 and 2026-Q2 (`QUARTER_DAYS` in `data_discovery/plants.py`); consistent with P3, at about 19.4k
  tokens per empty section. Plant rows per quarter not verified.
- **D4. HTTP 429** in 4/12 runs (`hidden_2`, `hard_2`-`hard_4`), 20 s each; `hidden_2`'s hit Discovery's selection.
- **D5. E1876** (HR Business Partners), an unplanted finding in `hidden_3`; not checked. E1183 no longer appears
  (rejected `already_recognized`); decoy E1254 never.

Proposals: **A** Original asks Cherry for the analysis at the question's grain; Cherry writes `execute_sql` at that
grain when the prepared metric cannot answer and declines only after a query shows absence (alternative: an
`employee`/`beneficiary_team` dimension for the metric). **B** when the plan needs a specialist, Original's first turn
must delegate; check why `jonah_3`'s empty draft was not rejected. **C** keep D3 as designed. **D** no request spacing yet.
**E** check E1876 offline. **F** optional: add the budget snapshot to the report's `execution`.
