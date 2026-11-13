# Audit handoff: v8 consolidation to count-overflow truncation, 2026-11-10

This file summarizes everything changed from v8 adoption (2026-11-04) to 2026-11-10. It lists
every change, its evidence, the files to read and the points that need a second look. It is a
map: the record of each decision is in `PROJECT_CONTEXT.md` (newest first) and
`reports_gold/DEVIATIONS.md`.

The git root is `Final_Project/`; paths below are relative to `Final_Project/Agent_Echo/`
unless they start with `Final_Project/`.

## 1. Working rules that governed this period

These rules come from the project owner. Check the changes against them.

- Live model calls are run by the owner, never by the coding assistant. Run captures are in
  `reports/` (JSON reports) and `reports/logs/details/<run_id>/exchanges.jsonl`.
- Credentials stay in the ignored `.env`.
- No new prompt rule without an observed failure. A prompt line is kept only with a measured
  benefit (the "M4 standard").
- Frozen decision criteria are never edited after a live run; a change needs a new version
  (`reports_gold/P2_DECISION_CRITERIA_v1.md` to `_v4.md`, hashes in
  `reports_gold/FREEZE_RECORD.md`).
- Criteria v4 rule 3 governs planning changes. A change is kept only if its target case
  passes in both repeats on both profiles and neither profile falls below its floor (18 for
  `apinex_test`, 17 for `apinex_gemini_test`).
- Code fixes are diagnosed from run captures, kept minimal and come with a test.

## 2. Branches and tags

| Ref | Commit | State |
|---|---|---|
| tag `v8-consolidated` | `a76b30f` | One version each of Original and ZeroSugar. |
| tag `v8-verified` | `3f9ccb7` | Gold tooling pointed at `reports_gold`. Commit order: `fc8cd4a`, `e0e919d`, `3f9ccb7`, then `a76b30f`. |
| tag `v8-shipped` | `52b3003` | Priority 2 closed; all seven restored v7 prompt lines reverted. |
| `main` = `origin/main` | `05b7684` | Shipped plus follow-ups, through live runs 91-95. |
| `count-overflow-truncation` | `4f4c3ef` | One commit on `main`. **Not pushed, not merged, not live-tested.** |
| `narrative-count-feedback` | `24bf15d` | One commit on `main` (pushed). **Rejected, not merged**: see section 5. |
| `v8-followups`, `planning-clarification-rule`, `review-truncation-spare`, `sentiment-numbers-normalization`, `remove-clarification-recheck`, `revert-p2-lines`, `consolidate-agents` | various | Feature branches already in `main` (fast-forward). They can be deleted. |

## 3. Timeline of commits

```
fc8cd4a 11-04 Adopt Original v8 and ZeroSugar v8 with human gold evaluation
e0e919d 11-04 Track gold evaluation data in reports_gold
3f9ccb7 11-04 Point gold tooling at reports_gold                      [v8-verified]
a76b30f 11-04 Consolidate Original and ZeroSugar into one version each [v8-consolidated]
2907912 .. 52b3003  11-05..11-08  Priority 2 measurement (M1-M4) and revert [v8-shipped]
c23bf23 11-08 Fix casebook hashing, the planning recheck and the reviewer chart inventory
abeb1b2 .. ca22f46  11-08  C3 measurement, criteria v4 freeze, M3 re-run
16774e6 11-08 Drop label objections raised outside label_disputes
edf08b7 11-09 Truncate excess assertions when all are supported
2e6144a 11-09 Close label-filter safety bypass; ignore unplanned specialist failures on accept
2989051 11-09 Ignore resent supported assertions for settled findings
93916a8 11-09 Record the review fixes, live runs 70-80 and the planning prompt trial
12962df 11-09 Record no-change decisions on the time cap and reasoning_effort
0e8c9e9 11-09 Drop clarifications on plans that already select a specialist
92fa811 11-09 Let a truncated review attempt earn the spare attempt
3163f80 11-09 Record the spare review attempt and live runs 81-90
6d5fab3 11-09 Normalize numbers off sentiment plans with no catalog metric
736879b 11-10 Remove the planning clarification recheck
05b7684 11-10 Record live runs 91-95 on both planning changes            [main]
4f4c3ef 11-10 Trim a repeated count overflow instead of rejecting it again [count-overflow-truncation]
24bf15d 11-10 Ask for fewer narrative items when no saved block can be removed [rejected]
```

To list the files of any commit: `git show --stat <commit>`.

## 4. Changes by phase

### 4.1 v8 adoption and consolidation (`fc8cd4a`, `a76b30f`)

- Original v8 and ZeroSugar v8 were adopted after human gold evaluation
  (`GOLD_CASEBOOK_v1.md`, `GOLD_V1_RECORD.md`, `gold_cases.py`, `score_gold.py`,
  `run_gold_review.py`, `run_gold_repair.py`).
- Consolidation gave each agent a single version, in `agents/original.py` and
  `agents/zero_sugar.py`.
  - Deleted: `agents/original_v8.py`, `agents/zero_sugar_v8.py`, `agents/review_v7.py`,
    `run_agent_v8.py`, `measure_repair_delivery.py`, and eight review-v7 test files.
  - Agent code went from about 4,350 to 2,380 lines.
  - `tests/test_v8_agents.py` was renamed `tests/test_agent_contracts.py`. Shared helpers moved
    to `tests/fixtures.py`, and `tests/test_workflow_scenarios.py` was added.
  - 50 v7-protocol scenarios were archived, not run, in `old_protocol_tests/`.
- Design and audit: `AGENTS_V8_DESIGN.md` (section 12), `AUDIT_PROMPTS_V7_VS_CURRENT.md`.
- **To check:** that no current code path still imports a deleted module, and that
  `old_protocol_tests/` is excluded from the gate (`tests/` only).

### 4.2 Priority 2: seven restored v7 prompt lines measured and reverted (`2907912`..`52b3003`)

- Seven one-line rules restored from v7 were measured with frozen criteria:
  - M1: reviewer gold;
  - M2: repair gold;
  - M3: planning gold, in `gold_plans.py` and `run_gold_plans.py`;
  - M4: group C cases, in `gold_m4.py` and `run_gold_m4.py`.
- All seven were reverted (`9c693e6`). The evidence is in:
  - `reports_gold/DEVIATIONS.md`;
  - `reports_gold/M1_ADJUDICATION_NOTES_20261107.md`, `M2_...`, `M4_...`;
  - `reports_gold/RERUN_COMPARISON_20261107.md`.
- A product boundary was adopted separately, outside priority 2: pay, promotion, discipline or
  termination use is a safety concern (support review).
- **To check:** that `agents/original.py` and `agents/zero_sugar.py` contain none of the seven
  lines listed in `PROJECT_CONTEXT.md`, "Prompt audit and planning fixes after runs 63-66".

### 4.3 Follow-ups after v8-shipped (`c23bf23`..`ca22f46`)

- `gold_cases.sha256()` normalizes CRLF to LF. The old hash is still accepted as
  `LEGACY_CASEBOOK_SHA256`.
- The planning recheck stopped spending a planning attempt. This was later removed entirely;
  see 4.6.
- `visible_inventory` lists rendered charts (C3). A trial prompt line was reverted.
- Criteria v4 frozen (`reports_gold/P2_DECISION_CRITERIA_v4.md`).
- The output-token cap was not raised; the evidence is recorded in `PROJECT_CONTEXT.md`.

### 4.4 Review fixes from live captures (`16774e6`, `edf08b7`, `2e6144a`, `2989051`, `92fa811`)

All are in `agents/zero_sugar.py` unless noted. Tests are in `tests/test_agent_contracts.py`.

| Commit | Rule | Normalization event | From run |
|---|---|---|---|
| `16774e6` | Drop a Vanilla new issue that targets a classification table and cites one of its labeled comments. Absences (`missing_deliverable`) are never dropped. | `label_issue_outside_disputes_dropped` | Luna 67 |
| `edf08b7` | More than 12 assertions and all supported: keep the first 12. | `supported_assertions_truncated` | Gemini 68 |
| `2e6144a` | Label filter honors `safety_issue_index` only with a safety score of 1 or 2. In `agents/original.py`, `accept()` blocks only on failures of planned specialists (`planned_roles`). | none | Luna 72, Gemini 71 |
| `2989051` | Supported assertions for findings not pending are dropped instead of failing the attempt. | `assertion_outside_pending_dropped` | Luna 74 |
| `92fa811` | A review phase with a truncated attempt may use the run's single shared protocol exception (`budget.reserve_review_protocol_repair()`). | none | Gemini 68; Luna 70, 72, 74, 81 |

- **To check:**
  - that each filter drops only what the reviewer cannot act on, and never a safety issue
    or an absence;
  - that `planned_roles` defaults to the old behavior when unset (`getattr(..., None)`);
  - that the protocol exception is still capped at one per run.

### 4.5 Planning normalizations (`0e8c9e9`, `6d5fab3`)

In `agents/original.py` `_plan()`; tests are in `tests/test_clarification_policy.py`.

- `clarification_with_specialist`: a clarification is dropped when the same plan selects a
  specialist. M3 under v4 rule 3 passed: test 20, Gemini 21.
- `sentiment_numbers_normalized`: a sentiment plan with `needs_numbers` and no catalog
  metric gets `needs_numbers` and `include_chart` set to false. M3 passed: test 21,
  Gemini 17. The code carries a `shortcut:` comment, because a later repair can still bring
  Cherry in.
- Live: it fired in runs 91, 93 and 95, and no run since then called Cherry.

### 4.6 Planning clarification recheck removed (`736879b`)

- `plan()` no longer runs a reconsideration turn: planning uses at most two attempts. The
  `reconsidered_clarification` code and the `clarification_recheck` ValidationError are gone.
- Why: over 10 saved M3 runs, the recheck dropped 9 of 36 needed clarifications (P12, P13), and
  it rescued no pass once `clarification_with_specialist` existed.
- M3: test 20, Gemini 22.
- **Accepted risk:** a false clarification on a plan with no specialist (live run 73) now
  always reaches the user.
- `run_gold_plans.py` keeps `MODEL_CALLS = 5` (two planning attempts plus transport
  retries). **To check** whether 5 is still the right cap.

### 4.7 Count-overflow truncation (`4f4c3ef`, branch `count-overflow-truncation`)

- The first `narrative_count` (12 interpretations or proposals) or `fact_ids_count` (24)
  rejection in one answer delivery works as before. A later overflow in the same delivery is
  trimmed by `resolve_answer(..., truncate=True)` in `agents/content.py`.
- Order kept: new items first, then reused blocks, then retained blocks, in their original
  order. Each trim is recorded as event `answer_count_truncated` and in diagnostics
  `answer_truncations`.
- Files:
  - `agents/content.py`: `COUNT_CODES`, trim logic.
  - `agents/grounding.py`: `FACT_ID_LIMIT = 24`.
  - `agents/original.py`: the `overflowed` flag in `_run`, and `finish(..., truncate=)`.
  - `agents/runtime.py`: the `overflowed` flag in the specialist loop, and the diagnostics key.
- Tests:
  - `tests/test_content_delivery.py`: order, fact IDs, specialist loop. The stall test now
    uses an unknown `reuse_ids` entry instead of an overflow.
  - `tests/test_agent_contracts.py`: `test_a_second_narrative_overflow_is_trimmed_instead_of_rejected_again`.
- Evidence: count rejections appeared in 15 of 37 runs since 67. Runs 93, 99 and medium Luna 2
  ended in `agent_turn_limit` on these loops with run budget left.
- This reverses the earlier rule "no content is removed automatically". The reviewer still
  checks the trimmed payload, which is the one replayed (`result.grounding["payload"]`).
- **To check:**
  - A trim entry is recorded even if that submission is then rejected for another error
    (diagnostics only).
  - `overflowed` is set from any count code, not per field.
  - Is "new first" the right priority when a repair round reuses many reviewed blocks?
    (Run 99 reused 8 to 17 blocks.)

## 5. Tried and rejected (no runtime change in `main`)

| Change | Where | Why rejected |
|---|---|---|
| Two planning prompt edits (P1 `needs_numbers`, P7/P10 `needs_sentiment`) | never committed | Failed v4 rule 3: Gemini fell to 16. See `reports_gold/DEVIATIONS.md`, "Planning prompt trial". |
| Completeness line "tables and charts listed are visible" | never committed | No gain on C3. |
| Clearer `narrative_count` correction text when no saved block exists | `24bf15d` on `narrative-count-feedback` | Fired 4 times in run 99; Gemini oversent every time. The limits are already in the tool schema (`maxItems`). |
| Raising the 12-item narrative limit | discussed, not implemented | Longer answers, more review surface, product decision. |
| Per-request time cap, `reasoning_effort` | decided no change | See `PROJECT_CONTEXT.md`, "Review fixes and live runs 70-80". |

## 6. Live results since run 67

The hard question has hash `8a96adb1` and 598 characters. The medium question is
`MEDIUM_QUESTION` in `tests/test_clarification_policy.py`, with window 2026-01-01 to
2026-09-30. Each report's capture holds `code_versions`, so the code hash behind each run can be
checked.

| Runs | Code | Complete |
|---|---|---|
| 67-69 | `v8-shipped` | 1 of 3 |
| 70-72 | `edf08b7` | 0 of 3 |
| 73-76 | `2e6144a` | 1 of 4 |
| 77-80 | `2989051` | 4 of 4 |
| 81-84 | `0e8c9e9` | 3 of 4 |
| 85-90 | `92fa811` | 2 of 6 |
| 91-95 | `736879b` | 3 of 5 |
| 96-99 | `24bf15d` | 1 of 4 |
| medium Luna/Gemini 1-2 | `24bf15d` | 1 of 4 |

- Hard question since run 67: 15 of 33 complete. Most partial runs still release an earlier
  reviewed draft.
- Failure classes still open, seen on both questions:
  - review churn across drafts (85, 90, 95, medium Luna 1);
  - a review attempt with no tool call (`tool_call_count`: 86, 98, medium Gemini 1);
  - reasoning-only output truncations (96: Original `output_token_limit`);
  - `finding_missing` on the first support attempt, in nearly every run, absorbed by
    retries (medium Gemini 2 had 53 and still completed);
  - count loops (addressed by 4.7, not yet live-tested).
- Other open items:
  - false clarifications on plans with no specialist (run 73);
  - the correction path for a genuine, non-defensible label dispute.

## 7. Observations for the auditor

1. **One question dominates the evidence.** Runs 34-99 all use the same hard question. Only
   four runs use another question. Fixes may be tuned to that question.
2. **Small live samples.** Batches of 3 to 6 runs. A 4 of 4 batch (77-80) fired none of the
   new events, so batch-to-batch changes may be noise.
3. **Deterministic normalizations accumulate.**
   - Review: `label_issue_outside_disputes_dropped`, `supported_assertions_truncated`,
     `assertion_outside_pending_dropped`.
   - Planning: `clarification_with_specialist`, `sentiment_numbers_normalized`.
   - Answer delivery: `answer_count_truncated`.

   Each comes from a captured failure. It is worth checking whether, together, they hide
   reviewer or model errors that should surface.
4. **Gate:** `..\Echo_UI\.venv-windows\Scripts\python.exe -B -m unittest discover -s tests`,
   run from `Agent_Echo/`. 308 pass, 4 skipped, on `count-overflow-truncation`; 304 on `main`.
   The four skipped M4 tests need the reverted priority 2 lines.
5. **Knowledge graph:** `graphify update .` is blocked from the assistant's shell by Windows
   Application Control. The git hook rebuilds `Final_Project/graphify-out/` on commit, merge
   and branch switch.
6. **Outside the repo:** `Practicum/echo_review_experiment_20261028/` holds three older
   copies of `Agent_Echo`, which are not current code. `Final_Project/.vscode/settings.json`
   (ignored by git) gained Pylance excludes on 2026-11-10.

## 8. Where to read first

1. `PROJECT_CONTEXT.md`, the sections from "Count overflow truncation" down to "Original and
   ZeroSugar consolidated".
2. `reports_gold/DEVIATIONS.md`, all sections.
3. `git diff v8-consolidated..count-overflow-truncation -- agents/` for the runtime changes.
4. `AGENT_ROLES.md` and `AGENTS_V8_DESIGN.md` for the intended contracts.
