# Freeze record (2026-11-06, M4 added 2026-11-07)

The frozen inputs of the priority 2 study, with hashes that can be checked from any clone. It
replaces the hashes in `audit final v8/NEXT_STEPS_PLAN_FINAL.md`, which `.gitignore` excludes.

## Hashes (SHA-256 of the committed blob, LF line endings)

| File | Commit | SHA-256 |
|---|---|---|
| `Agent_Echo/reports_gold/P2_DECISION_CRITERIA_v1.md` | `2907912` | `e6a8e73de701c7f5d63d2a8639006cebe665d28c0fd0cd3bd3edda7e0325b269` |
| `Agent_Echo/reports_gold/P2_DECISION_CRITERIA_v2.md` | `23e352d` | `250f4860906deda4d62eae018ce09742f03ec6ec6f2fe56d72c62416528948ef` |
| `Agent_Echo/reports_gold/GOLD_PLANS_v1.json` (M3) | `23e352d` | `54461062a4d5ee8fc89186eb26dac993e2a3be907a7b3e34ccbca22ecfb54fea` (= `PLANS_SHA256` in `gold_plans.py`) |
| `Agent_Echo/reports_gold/P2_DECISION_CRITERIA_v3.md` | `2692ab9` | `e426cbec896091749f248f2c14194f7af3d0aa3febdefe45488ab43d86769220` (supersedes v2; frozen 2026-11-07) |
| `Agent_Echo/reports_gold/M4_CASES_v1.json` (M4) | `2692ab9` | `aa1f4d2a9368647b2028c6647db1ce42a52cf9db178d22e20a477736394944f6` (= `M4_SHA256` in `gold_m4.py`) |
| `Agent_Echo/GOLD_CASEBOOK_v1.md` (M1, M2) | `fc8cd4a` | `2ed93543df6892ece395d031f04b6834a49999fca5c26f9b324129984ac31c3d` (see the note below) |

## How to verify

From the repository root, in Git Bash on Windows or a shell on Linux/macOS (the hash is of the
committed blob, so it does not depend on the checkout's line endings):

```bash
git show 23e352d:Agent_Echo/reports_gold/GOLD_PLANS_v1.json | sha256sum
```

Replace the commit and path for each row. Do not run `sha256sum` on the working file: with
`core.autocrlf=true` (this machine) the checkout has CRLF line endings and gives another hash
(for example `7889…` for `GOLD_PLANS_v1.json`, `2cb0…` for criteria v2). Do not pipe `git show`
through Windows PowerShell 5.1 either: it re-encodes the bytes.

`gold_plans.sha256()` and `gold_m4.sha256()` hash the working file with CRLF converted to LF, so they give the
committed value on any checkout.

## Note on GOLD_CASEBOOK_v1.md

`CASEBOOK_SHA256` in `gold_cases.py` is `24d84029…5197d3`, the hash of this machine's CRLF
working copy, not of the committed blob (`2ed93543…`). `gold_cases.py` hashes the raw bytes, so a
clone with LF line endings would refuse to build `cases.json`. M1 and M2 run on this machine and
are not affected. Fixed after the study (2026-11-08, branch `v8-followups`): `gold_cases.sha256()` hashes
the LF-normalized file, `CASEBOOK_SHA256` is `2ed93543…`, and `24d84029…` is still accepted as
`LEGACY_CASEBOOK_SHA256` for the `cases.json` and results that carry it.
