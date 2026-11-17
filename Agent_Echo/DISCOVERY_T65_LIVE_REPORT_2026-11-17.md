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
  resolved the name to E0001, but the resolved ID is not passed to Cherry or Vanilla. Open; to fix before
  the demo.

## Scope decisions (user, 2026-11-17)

- Gate 7 is not critical: a pool that is 5+5 (or 3+5) without the optimal five is acceptable.
- Gate 8 and D8 are skipped.
- The live demo with the professor uses M14 and Jonah Meyer (E0001).

## Still to run

| Report | Question | Expected |
|---|---|---|
| `reports/discovery_t65_m14_jonah2.json` | The Jonah question, after the name fix | Original's answer and the Discovery section agree |
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
