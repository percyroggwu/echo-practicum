# Discovery Phase 2: offline implementation and acceptance report

> **Outdated numbers.** The figures below predate the thread-direction fix in `data_access.py` and the 5 + 5 pool rework (`strongest_signals` removed). Current results are in [DISCOVERY_PHASE3_OFFLINE_REPORT_2026-11-16.md](DISCOVERY_PHASE3_OFFLINE_REPORT_2026-11-16.md).

Date: 2026-11-16. Scope: T2.1-T2.6 of plan v10. **Implemented locally; acceptance is NOT passed.** No commit or live Echo/provider execution was made.

## Assignment and file ownership

Every task had its own subagent. T2.1 and T2.6 ran in parallel; T2.2, T2.3, T2.4 and T2.5 wrote `discovery_tools.py` sequentially. The coordinator reviewed results, repaired boundary issues, and personally ran the final suite and all-team audit.

| Task / subagent | Requested equivalent | Effort | Owned runtime file | Focused result |
| --- | --- | --- | --- | --- |
| T2.1 / t21_access | GPT-6.1 Terra | high | agents/data_access.py | 7 tests passed |
| T2.2 / t22_subject | GPT-6.1 Terra | low | agents/discovery_tools.py | 8 tests passed |
| T2.3 / t23_satisfaction | GPT-6.1 Terra | low | agents/discovery_tools.py | 2 tests passed |
| T2.4 / t24_signals | GPT-6.1 Sol | medium | agents/discovery_tools.py | 13 tests; 2 M32 acceptance failures retained |
| T2.5 / t25_prefilter | GPT-6.1 Sol | medium | agents/discovery_tools.py | 8 tests passed after work-selection repair |
| T2.6 / t26_precompute | GPT-6.1 Terra | low | agents/discovery_precompute.py | 2 tests passed |

Each agent also owned its separate task test file. No two writers edited the same file concurrently, including coordinator repairs.

## Implemented behavior

- Separate `DiscoveryScope` and read-only `DiscoveryData`: explicit fixed dates 2025-10-01..2026-06-30, active roster as of June 30, event/recorded cutoff, dated sharing, manager-ID team identity, and external-person placeholders. Legacy `AccessScope`/`ScopedData` behavior is preserved.
- `FollowUpScope` / `FollowUpData`: July-September only, frozen June roster and immutable snapshots of saved subjects, anchors and beneficiary teams. This is an access foundation; the HTTP follow-up endpoint is a later phase.
- Deterministic subject resolution, including direct clarification IDs, accent/case matching, unresolved/ambiguous clarification, outside-subject decline, beneficiary focus, and bounded period hints. Resolution reads no evidence.
- Latest pulse selection with previous-quarter delta and employee-ID tie breaks. Same-day observations use their complete recorded timestamp. Pulse values never enter the model pool.
- Versioned signals with two types from two source tables and the required qualifying type. Normal selection excludes the lowest ten; focus selection uses only the beneficiary's signals. Volume counts distinct qualifying/workload records rather than ordinary help-only record volume. Self-review matching is a deterministic token-overlap lead, not model judgment.
- Strict 8/10/25 TOTAL source-record caps, 300-character text excerpts, work references, closing recognition/attribution/outcome context, counted goal targets, source-balanced work selection using actual signal leads, self-review leads, and bounded team-pattern sample references. Linked source rows count toward the cap. Caps and omitted closing context are recorded.
- Separate post-import sidecar with dated visibility events, a separate anchor mapping, name mentions and quarter keys. One share produces one visibility event even if it has multiple anchors.

API entry points are `resolve_subject(data, plan, clarification=None)`, `lowest_satisfaction(data, n=10)`, `strongest_signals(data, n=5, focus_hint=None, period=None)`, `prefilter(data, resolution)`, and `build_discovery_index(source_db, index_db)`. `selection_audit` is internal; the returned model pool excludes selection reasons and pulse scores.

## Final verification run by the coordinator

Run from `Agent_Echo` with installed Python and the existing dependency directory:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) '.venv/Lib/site-packages'
python -B tests/run_phase2_offline.py
python -B tests/discovery_phase2_audit.py
```

- Full suite: **386 tests in 56.087 seconds; FAILED (failures=4, skipped=4); exit 1**. No errors. The four failures are the acceptance checks listed below, including two subtests within the P5 contributor test.
- All-team audit: **60 teams in 162.33 seconds; acceptance_pass=false; exit 1**.
- `python -B tests/run_phase2_offline.py --pattern test_agents.py`: **21 tests passed** (legacy data-access/agent regressions).
- `python -B tests/run_phase2_offline.py --pattern test_import_discovery_profile.py`: **10 tests passed**.
- Task test commands use the same runner with patterns `test_discovery_access.py`, `test_discovery_subject.py`, `test_discovery_satisfaction.py`, `test_discovery_signals.py`, `test_discovery_prefilter.py`, and `test_discovery_precompute.py`; exact focused outcomes are in the assignment table.
- Independent coordinator boundary tests: `python -B tests/run_phase2_offline.py --pattern test_discovery_phase2_boundaries.py`: **8 tests, 2 failing P5 contributor subtests**. Other checks include same-day pulse order, authorship-versus-mention discrimination, private-source rejection, frozen action inputs, recognition as-of/person identity, beneficiary self-review, and counted goal context.
- `git diff --check`: exit 0. `graphify update .`: exit 0, AST-only, no LLM needed.

Logs: `data/discovery_phase2_unit_results.txt` and `data/discovery_phase2_audit_results.txt`. Structured final metrics: `data/discovery_phase2_metrics.json` (`audit_scope=all_60`). The private answer key is read only by evaluation code; positive cases and decoys have separate denominators.

An initial unguarded legacy-test entry point was run before the credential guard was added; that entry point can load private configuration. It was rerun with the guard, and no credential contents were printed. Final verification hides project credential files and blocks their opening and network access. Early importer-test attempts also hit the Windows temporary-directory ACL issue; the test-only runner fixes that location/ACL issue, and the importer checks then passed.

## Recall and remaining acceptance failures

| Positive automatic slot | People reached | Listed source present in case |
| --- | --- | --- |
| Low satisfaction / whole team | 75/75 (100%) | 70/75 (93.3%) |
| Strong signals | 30/45 (66.7%) | 30/45 (66.7%) |
| Total | **105/120 (87.5%)** | **100/120 (83.3%)** |

The low-satisfaction denominator contains 41 actual satisfaction selections plus 34 plants included by the whole-team exception. All **17 small teams** use their entire active roster. All 60 automatic decoys are reported separately and do not inflate positive recall. A listed-source hit can include goal context; it is an evidence-selection diagnostic, not semantic proof of a contribution.

Strict row recall is **397/1,154 (34.4%)**. Many cases list more source rows than an eight-item cap can retain; this row ratio is not the 95% person-recall gate. The initial prefilter recovered only 44 listed rows; the work-level signal repair increased that to 397. Five selected plants still have no listed source within the cap. Ten answer-key source IDs have no quarter-index metadata and remain in the evidence denominator rather than being silently discarded.

Unmet acceptance:

1. M32's normal strong slot misses **E0107 and E0561**, and reaches only **1/2 automatic plants**. Under the current versioned generic rules, E0107 ranks 17th (6 types, volume 13) and E0561 ranks 19th (6 types, volume 12). The fifth selected candidate has 6 types and volume 32. They cannot be promoted by this fixed ranking/cap without changing the rules or signal/data distribution. No employee-specific selection rule was added.
2. The 95% automatic person recall gate fails: **15 strong-slot plants are missing**.
3. Plan gate 1's P5 other-manager check fails for **M31 (1/2 contributors)** and **M01 (0/2)**. M46 includes E0046 through its whole-team pool. M14 includes E0001 and both automatic plants through strong signals.
4. Five selected automatic cases still lack any listed source evidence inside the bounded pool.

Passing checks: M32's exact lowest-ten order; all 17 whole-team exceptions; zero external person-name/employee-ID, inactive-person, cap or as-of violations in all 60 normal pools; M32 controls E0815/E0776 absent; all three M16-focused helpers selected with eight M16 evidence items each; actual D1 recognition AND shared feedback and D3's E0970 corrective attribution survive an eight-record selection. D3's retention passes when selected, but D3 is still absent from the normal M32 pool because of the strong-slot miss. July shares/recognition do not rewrite June state.

## Demo pools and token sizes

M32, low satisfaction (ordered): `E2198, E0010, E1748, E2156, E1401, E1586, E0728, E2233, E1333, E1383`.

M32, strong signals (ordered): `E0970, E0058, E0350, E2293, E2047`.

M14, low satisfaction (ordered): `E1183, E1209, E0450, E0885, E1088, E1546, E1876, E0451, E1254, E0758`.

M14, strong signals (ordered): `E0334, E0135, E0001, E0491, E1412`.

Each pool contains 15 people and 120 source records. Pool-only serialized sizes:

| Manager | Characters | Estimated tokens |
| --- | --- | --- |
| M32 | 69,517 | 17,380 |
| M14 | 66,623 | 16,656 |

These are **characters/4 estimates**, rounded up, because a cached provider tokenizer was unavailable. They exclude the manager question, role instructions and output tokens. No vocabulary was downloaded.

## Changed files and generated outputs

Runtime:
- `agents/data_access.py`
- `agents/discovery_tools.py`
- `agents/discovery_precompute.py`

Verification:
- `tests/test_discovery_access.py`
- `tests/test_discovery_subject.py`
- `tests/test_discovery_satisfaction.py`
- `tests/test_discovery_signals.py`
- `tests/test_discovery_prefilter.py`
- `tests/test_discovery_precompute.py`
- `tests/test_discovery_phase2_boundaries.py`
- `tests/run_phase2_offline.py`
- `tests/discovery_phase2_audit.py`

Documentation: this report, `PROJECT_CONTEXT.md`, and `DOCUMENTATION_MAP.md`. Pre-existing changes in `AGENTS.md`, `import_data.py`, plan/breakdown files and `tests/test_import_discovery_profile.py` were preserved.

Generated: `data/echo_discovery_v1.index.db`, final metrics/logs listed above, and the AST graph assets under `graphify-out/`. Source databases were not modified:

| Database | SHA-256 before = after |
| --- | --- |
| data/echo.db | 95db1450b9d4129db0e1efb29c2d31e07adf894a9d2568900246b409dbc766f4 |
| data/echo_discovery_v1.db | b26494d63e2e46c840355ce69630b31fc684ee138b647584a2f3dc7620e03df4 |

Post-import command, separate from the importer:

```powershell
python -m agents.discovery_precompute --database data/echo_discovery_v1.db --output data/echo_discovery_v1.index.db
```

Sidecar: 87,672 visibility events (42,921 praised, 4,034 recognized, 40,717 shared), 87,672 anchor links, 147,102 mention rows and 845,594 quarter keys; SQLite integrity passed. No generated pack, legacy dataset or extension files were modified.

## Handoff status

Phase 2 has local implementation and reproducible measurements, but is **not accepted or ready to declare complete**. Reconcile the fixed ranking/slot budget with the observed signal distribution and the remaining bounded-evidence misses before the next phase. Model judgment, Original integration, backend/CLI transport guards, UI, action persistence and the follow-up HTTP endpoint remain later-phase work and were not executed or claimed here.
