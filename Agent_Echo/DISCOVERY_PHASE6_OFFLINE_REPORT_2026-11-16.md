# Discovery Phase 6: tests and scoring (offline report)

Date: 2026-11-16. Scope: **T6.1, T6.2 and T6.3 only** of
[WORK_BREAKDOWN_DISCOVERY.md](WORK_BREAKDOWN_DISCOVERY.md). Starting branch:
`discovery-phases-0-5`, commit `661c9478f7d03bd53f845a0c0715d7280703ac81`.
Final-source offline regression: **487 tests, 483 passed, four skipped, zero
failures/errors**, exit 0. Gates 1-5 pass; gate 6 remains partly unverified.

All evaluation is offline. Scripted judgments test plumbing, schema checks,
withholding, routing and publication; they are **not analytical accuracy evidence**.
No live model, API, provider or connection-test calls are authorized or performed.
No runtime behavior, source databases, generated pack, gates or thresholds are changed.
The changes remain uncommitted. Previous state:
[phase 5 report](DISCOVERY_PHASE5_OFFLINE_REPORT_2026-11-16.md).

## Who did what

| Task | Subagent | Model and effort | Responsibility |
| --- | --- | --- | --- |
| T6.1 | `t61_tests` | `gpt-6.1-sol`, medium | Read existing test assertions, identify actual gaps, add unit and integration tests, supply the coverage mapping. |
| T6.2 | `t62_scorer` | `gpt-6.1-sol`, high | Implement the offline scorer, its contract tests and the gate report. |
| T6.3 | `t63_regression` | `gpt-6.1-sol`, medium | Inspect remaining role/plan fixtures and run the full offline suite last. |

The coordinator reviewed the new assertions and scorer implementation, requested
corrections to the assertion mapping, and owns the final report, status updates,
database verification and graph update. No Astra subagent was used. The available
model was used at the medium/high levels specified by the breakdown; Sonnet was
not an available subagent model.

## What was built

- **T6.1:** fifteen additional tests: eleven in `tests/test_discovery_phase6.py`,
  three in `tests/test_ui_followup.py`, and one in `tests/test_discovery_subject.py`.
  Existing tests were read before adding these cases.
- Dedicated A5/A6 follow-up checks cover matching records and exclusion of unrelated
  work/partners or records before the decision. An additional A2 test covers an
  observed result and a different beneficiary manager.
- The new integration checks cover the same-agent findings-to-decline reset,
  clarification with a changed replanned name and preserved quarter, a literal
  temporal comparison using a recorded plan, reviewed-answer byte identity,
  section tampering, and failure-artifact/manager-projection preservation.
- The runner's existing credential-file block also covers `connections.local.json`.
  Synthetic temporary fixtures remain inside `Agent_Echo/data/phase2_test_tmp/`.
- **T6.2:** `score_discovery.py` measures the current pool and summary across all
  60 managers, derives each plant's slot from the current rule, and binds gates
  2-4 and 6 to individual executed test IDs. Missing or skipped assertions remain
  `unverified`. Gate 5 accepts an explicitly supplied full regression log.
- The scorer reads published findings exclusively through
  `discovery_section.rendered`, never `candidate.findings` or the private runtime
  Discovery object. Listed source IDs measure visible evidence coverage; one-line
  findings without sources and semantic equivalence remain unverified.
- An optional existing gate-7 selection-only capture can be scored. It must have
  exactly one row per current manager, with the exact number of distinct permitted
  selection IDs. Its recall combines these choices with the current code slot.
  No selection-only capture was generated.
- Four small scorer tests cover current slots, recall/missed plants, invalid
  selection captures, and section-only evidence extraction.
- **T6.3:** aligned the remaining numeric and sentiment plan factories, the
  sentiment misroute overwrite, and the unused revision helper with current plan
  fields. Renamed the pacing test's obsolete "five roles" name; its existing
  dynamic role enumeration already included Discovery. Explicit five-role
  scenarios tied to the legacy database remain valid scoped fixtures. Deliberately
  incomplete negative plans remain rejection fixtures. No unintended global
  five-role assumption or complete fixture using the obsolete plan key set was
  left in the inspected tests; no assertions or budgets were relaxed.

## T6.1 item -> test that covers it

The existing modules in this table were inspected for their assertions, rather
than treated as coverage merely because of their filenames. Recorded plans and
scripted outputs establish execution contracts, not live planning/judgment quality.

| T6.1 item | Tests that cover it |
| --- | --- |
| Plan fields; Discovery on in-scope questions; other-team comparison rejection; beneficiary-only focus | Existing `test_discovery_phase4.py` team/routing tests and `test_ui_offline_discovery.py`; recorded plans exercise both rejection and beneficiary focus. |
| Exact, ambiguous, unknown and outside subjects; period resolution | Existing `test_discovery_subject.py` resolver tests. New `ResolveTests.test_every_supported_people_count_and_uppercase_accent_matching` checks successful groups of 2-5 and uppercase accented names. |
| Temporal comparison remains a team question | New `DiscoveryPhase6IntegrationTests.test_recorded_temporal_comparison_stays_team_scoped`; recorded plan, literal question and January-March dates. |
| Satisfaction slot and team summary | Existing `test_discovery_satisfaction.py`, `test_discovery_t23.py` and `test_discovery_t24.py`; scorer gate 1 additionally measures all 60 teams with current slots. |
| Selection validation, as-of filtering and balanced evidence | Existing `test_discovery_t25.py`, `test_discovery_prefilter.py`, `test_discovery_signals.py` and boundary tests. New `test_repeated_closure_rows_leave_room_for_independent_source_support` checks the eight-item cap under a flood of closure records. |
| Placeholders and leaks | Existing access tests, `test_discovery_t24.py`, and `DiscoveryAgentTests.test_team_question_selection_then_judgment` check masked external identities, partner-name redaction and recipient exceptions. |
| Top-five rule and section rendering | New `test_top_five_plus_five_and_overflow_are_checked_and_rendered`: 12 checked outputs yield 5 detailed, 5 one-line and 2 overflow findings. Existing `SectionTests` cover rendering. |
| Release check | New `test_release_rejects_tampered_section_and_keeps_reviewed_answer` compares UTF-8 answer bytes with the stored reviewed candidate and rejects a changed section. |
| Every Discovery status | Existing phase-3 agent tests plus new `test_no_candidates_costs_no_discovery_model_call`; new `test_pointer_and_provenance_for_every_status` covers rendered pointers and provenance for every status. |
| Three logical calls with network retries; shared schema retry | Existing phase-3 retry checks plus new `test_three_logical_calls_with_transport_and_shared_schema_retry`; verifies 3 logical calls, 4 raw attempts and a single shared schema retry. |
| Failed selection gives partial | Existing `DiscoveryAgentTests.test_failed_selection_reviews_the_satisfaction_slot_only` and selection-timeout test. |
| Budget check before schema retry | New `test_schema_retry_checks_available_budget_before_calling`; only the original attempt is spent. |
| DiscoveryTimeout and refunds without changing raw counters | Existing `BudgetTests` and phase-3 timeout tests; combined-retry test additionally checks raw attempts minus transport retries equals request-cost entries. |
| Pointer per status; discovery_section provenance; Original failure publication | New all-status pointer test and `test_original_failure_section_survives_artifact_and_manager_projection`; existing phase-4 failure publication test. |
| Section reset between questions | New `test_findings_then_declined_resets_section_in_same_agent` checks an actual findings-to-not_run transition without mutating the first result. |
| Subject clarification, unchanged resent question, chosen ID despite a different replanned name | Existing UI clarification transport tests and new `test_changed_replanned_name_applies_chosen_id_and_retains_period`. |
| Fixed discovery_v1 range | Existing access tests, `CommandLineTests.test_discovery_v1_rejects_a_missing_or_different_range`, and UI `test_other_or_missing_dates_rejected`. |
| FollowUpScope and each follow-up rule | Existing frozen-roster/anchor access tests and UI follow-up tests for A1/A3/A4, coverage and decision states; new `test_a2_observes_feedback_for_matching_person_work_and_partner`, `test_a5_matches_person_work_and_decision_date`, and `test_a6_matches_home_manager_partner_and_decision_date`. |

The broader gate-6 audit checklist has additional evidence requirements beyond
this T6.1 mapping. The scorer records those explicitly rather than declaring an
unqualified pass from the available tests.

## Scorer results

The foreground scorer exited **0**, with **828.95 s** elapsed. The coordinator
reviewed the generated JSON and its actual test transcript: **130 tests, zero
failures, zero errors, zero skips**. Sources:
`data/discovery_phase6_gate_report_final.json` (the reviewed measurement plus
final regression attachment), `data/discovery_phase6_gate_report.json` (initial
standalone scorer output),
`data/discovery_phase6_gate_report.tests.txt`, and
`data/discovery_phase6_scorer_results.txt`.

| Gate | Final result | Evidence and limits |
| --- | --- | --- |
| 1: pool and summary | Pass | All 60 managers; summary recall 78/78; hand-built positive person checks 8/8; P5 other-team contributors 5/5; automatic evidence retention 117/120 (97.5%, unchanged floor 95%); 275/275 malformed selections refused. |
| 2: code checks | Pass | Executed synthetic bad-ID, quote, subject, coverage and action-trigger assertions. |
| 3: subject and routing | Pass | Executed recorded-plan and resolver assertions, including groups of 2-5, accents/case, temporal comparison and clarification ID/period preservation. |
| 4: follow-up | Pass | Executed observed/not-yet, pending decision, complete/partial coverage, workload-topic and frozen-roster assertions. |
| 5: offline regression | Pass | Final-source full suite: 487 tests, 483 passed, four skipped, zero failures/errors, exit 0. The scorer attaches the actual log and its raw-byte SHA-256. Skips remain unverified. |
| 6: audit cases | Unverified in part | Mapped assertions passed; eight additional audit requirements have no complete dedicated evidence in this run. |

Gate 1 measured **47 current code-slot / 73 current selection-slot** automatic
plants. This split is an observed result, not a hard-coded acceptance condition
and not copied from the answer key's `Entry_Slot`. The three conditional
prefilter misses were `PL-M26-2`, `PL-M55-2` and `PL-M56-1`. No measured cap,
date, roster-scope, external-name or summary-order violation occurred. Five small
teams were evaluated by the whole-team rule. Separate conditional plant fixtures
do not imply that all M32 positives fit simultaneously into five selection slots.

Gate 6 remains conservative about these requirements:

1. Complete published-section external-name exclusion, beyond the individual
   masking and recipient cases tested.
2. Actual rendering of six manager-page agents and the declined Why card.
3. No Discovery rerun during actual correction rounds.
4. The complete work-reference variant contract, including a different record ID
   for the same work and foreign-reference edit rejection.
5. Export provenance, beyond the tested result/artifact/manager projection.
6. Independent report-reader matching of P1-P6 from the section.
7. Controlled equality of Original's closing turn and remaining calls/seconds
   against a no-Discovery workflow after refunds.
8. Actual workflow completion of Original's closing turn after its remaining
   post-Discovery budget is exhausted.

Some constituent checks already exist, but they do not prove the whole combined
requirement. These are missing evidence, not observed runtime failures. The
aggregate offline acceptance status therefore remains **unverified** even when
the executed regression suite passes. Gate 7 is **not_run**; no selection-only
report or optional workflow capture was supplied or created.

Reproduction from `Agent_Echo/`, using the system Python:

```powershell
$env:PYTHONPATH = '.venv/Lib/site-packages'
python -B -u score_discovery.py --output data/discovery_phase6_gate_report.json *> data/discovery_phase6_scorer_results.txt
# After the separate full offline runner has completed, a complete rerun can also use:
python -B -u score_discovery.py --regression-log data/discovery_phase6_unit_results.txt --output data/discovery_phase6_gate_report.json
```

For this delivery, the full regression log was attached using the scorer's
`regression_evidence()` helper to `data/discovery_phase6_gate_report_final.json`, preserving the original measurement and test
transcript instead of repeating the expensive all-team measurement. Its source
and raw-byte hash are explicit; a supplied log by itself does not authenticate
the command, freshness or source identity. The coordinator separately reviewed
the final runner command, final source changes, actual summary and raw-byte hash.
The report's `regression_attachment` records this handoff while retaining the
original 130-test execution and 828.95 s measurement metadata.

## Deviations

- The first scorer invocation did not provide a recoverable completed report.
  The final invocation runs Python in the shell foreground with stdout/stderr
  redirected to `data/discovery_phase6_scorer_results.txt`; progress is flushed per team.
- Creating the initially requested auxiliary coverage note at
  `C:\workspace\t61_coverage.md` failed with “Failed to create parent directories”.
  No retry or alternate file was created. The user authorized continuation and
  requested the coverage table directly in this report instead.
- An auxiliary read-only `Get-CimInstance Win32_Process` query was denied with
  “Access to a CIM resource was not available to the client.” It was not retried
  through another mechanism. The user authorized continuation without process inspection.
- A coordinator method-list query using `rg` failed because `rg` is unavailable.
  That query was not retried through another route.
- A read-only scoped `git diff --name-only` query included parent paths outside
  the `Final_Project` repository and failed. It was not retried through another
  route; the final repository status and database hashes are reported separately.
- The first full-suite invocation began before the final unused plan helper was
  aligned. It is preliminary evidence only; a separate final-source full run
  supplies the requested regression log. The extra run follows an actual source
  correction, rather than reusing the preliminary result as final verification.
- No broader runtime fix, live gate, independent audit, Phase 7 task or Git publication
  was added to the scope.

## Verification

- Focused T6.1 checks: `test_discovery_subject.py` **9 passed**,
  `test_discovery_phase6.py` **11 passed**, `test_ui_followup.py` **15 passed**.
- Small scorer contract checks: **4 passed**.
- Foreground scorer: **130 tests passed**, zero skips, with gates 1-4 passing;
  final gate-5 evidence is attached separately and gate 6 retains the limits above.
- **Final-source full offline suite:** `python -B tests/run_phase2_offline.py`,
  system Python with `PYTHONPATH=.venv/Lib/site-packages`, from `Agent_Echo/`.
  **487 tests, 483 passed, four skipped, zero failures/errors, exit 0**, in
  **713.145 s**. Log: `data/discovery_phase6_unit_results.txt`.
  Its SHA-256 is `2511dd27a42e818db95d9f0ff4ea82dd4c1faa2132bf01d11756104f807f2c8e`.
- The preliminary full run executed **487 tests, zero failures, four skips** in
  **710.684 s** (`data/discovery_phase6_unit_results_prefinal.txt`). It began
  before the final unused-helper adjustment and is not the final-source gate.
- **Coordinator review:** inspected each subagent's changes and final outputs;
  verified the two database hashes and unchanged branch/HEAD. `git diff --check`
  passes. This scoped coordination review is not the independent T6.4 audit.
- **Graph maintenance:** `graphify update .` completed from `Final_Project/`
  after code and status updates, exit 0, AST-only with no LLM calls: **4,402 nodes,
  11,732 edges, 214 communities**. `graph.json`, `graph.html` and
  `GRAPH_REPORT.md` were refreshed. Existing community labels were retained or
  renamed by hubs; no semantic relabeling or extraction was run.

## Changed files

- New: `score_discovery.py`, `tests/test_score_discovery.py`,
  `tests/test_discovery_phase6.py`, and this report.
- Edited: `tests/test_discovery_subject.py`, `tests/test_ui_followup.py`,
  `tests/run_phase2_offline.py`, `tests/test_workflow_repairs.py`,
  `tests/test_sentiment_workflow_repairs.py`, `tests/test_workflow.py`, and
  `tests/test_request_pacing.py`.
- Status updates: `PROJECT_CONTEXT.md`, `DOCUMENTATION_MAP.md`.
- Graph artifacts: `graphify-out/graph.json`, `graphify-out/graph.html`,
  `graphify-out/GRAPH_REPORT.md` and related local graph metadata/backups.
- Generated verification outputs live under `data/`; they are local evidence,
  separate from source-data databases and the generated data pack.
  They include the final gate JSON, initial scorer JSON/transcript/stdout log,
  canonical final suite log and preserved preliminary suite log.

## Database hashes

| Database | SHA-256 before | SHA-256 after |
| --- | --- | --- |
| `data/echo.db` | `95db1450b9d4129db0e1efb29c2d31e07adf894a9d2568900246b409dbc766f4` | `95db1450b9d4129db0e1efb29c2d31e07adf894a9d2568900246b409dbc766f4` |
| `data/echo_discovery_v1.db` | `b26494d63e2e46c840355ce69630b31fc684ee138b647584a2f3dc7620e03df4` | `b26494d63e2e46c840355ce69630b31fc684ee138b647584a2f3dc7620e03df4` |

Both match the supplied expected hashes. The branch remains `discovery-phases-0-5`
at `661c9478f7d03bd53f845a0c0715d7280703ac81`; changes are uncommitted.

## What remains

- **T6.4:** done; findings recorded in
  [DISCOVERY_T64_REVIEW_2026-11-16.md](DISCOVERY_T64_REVIEW_2026-11-16.md); R1-R7 fixed on 2026-11-16.
- **T6.5:** selection-only, workflow and benchmark live runs by the user; none was
  started here. Live results are recorded in
  [DISCOVERY_T65_LIVE_REPORT_2026-11-17.md](DISCOVERY_T65_LIVE_REPORT_2026-11-17.md).
  Tooling added on 2026-11-17, tested offline only
  ([test_discovery_t65_runners.py](tests/test_discovery_t65_runners.py)):
  - [run_discovery_selection.py](run_discovery_selection.py) runs the selection call alone for every team
    (the same instructions, summary, tool and checks as a team question, spaced by `--interval`) and writes
    the input for `score_discovery.py --selection-report`; `--resume` retries failed teams;
  - `run_agent.py original --database discovery_v1 --no-discovery` runs the same workflow with the
    subject check but without the Discovery step, for the plan's with/without comparison, and records
    `execution.discovery_disabled`.
- **Phase 7:** deferred documentation work. The compact context/map status updates
  requested for this delivery do not execute Phase 7.
