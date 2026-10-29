# Delivery reliability update - 2026-10-28

Scope approved by the user: A16, A11, A12, A14, corrected A1/A2, offline verification
and controlled live evaluation. A3-A10 and A13 remain separate follow-up work.
Five roles, both reviews, scope/privacy/source controls and canonical source-facts-v4
with historical replay remain required. No grouped review or automatic checkpoint
migration is included.

## A16: preserved baseline and checkpoint decision

Commit `219d7ff` preserves the local C1 implementation used by runs 35/36. Merge
`9d4caf2` also integrates the UI changes already published by the team, without changing
the preserved agent modules. Both commits are published on GitHub.

Git stores normalized file content. On Windows a checkout may change line endings,
which are included in checkpoint code fingerprints. The ignored private baseline at
`reports/baselines/pre_delivery_20261028/` therefore includes exact source bytes,
private reports/checkpoints, the database, and a manifest of their SHA-256 hashes.
Credentials and the virtual environment are not copied. Archives must remain private.

Existing checkpoints remain historical evidence. To continue an old workflow, use the
preserved exact implementation and its matching sources/configuration and credentials.
The updated implementation deliberately rejects those workflow checkpoints. Do not edit
fingerprints or bypass the matching-code/source/configuration checks. A successful
compatibility check does not promise that an interrupted model call will succeed.

## A11: baseline and triage

The authorized baseline suite reproduced 329 tests, 34 failures and 57 errors on
Python 3.12.10. Private detail: `reports/offline_suite_before_delivery_20261028.txt`.
These are failed checks, not 91 independent production bugs.

- Checkpoint-only database hashing is lazy when no capture is active. Actual captures
  and resume still fail on missing or changed sources.
- Scripted live fixtures translate canonical quote/request text to supplied EX_
  references and saved finding lists to application-keyed delivery. Their judgments
  are unchanged. Missing or invalid content stays invalid.
- Runtime doubles named Cherry expose the reader counter supplied by the real role.
- Historical replay and direct validator tests continue to use canonical stored data.

Offline and live results below will be recorded after execution. Passing offline tests
validates software behavior, not sentiment accuracy or independent semantic quality.

## A1/A2: resolved edits and bounded delivery repair

The additions contract is unchanged. Capacity is checked only after resolving actual
removals, reuse and exact duplicates; a static `12 - retained` schema cap is deliberately
not used. The live request exposes current capacity and overflow feedback includes the
retained/reused/submitted/unique-new/merged counts, excess, remaining slots and safe
BLOCK_ identifiers. The model chooses edits; code does not remove claims by meaning.
Canonical renderer validation and both reviews still apply.

After three consecutive structured-answer rejections of the same code/field, the
runtime stops with `answer_delivery_stalled`. It does not spend the remaining turns on
the same condition. The existing reviewed-candidate release path retains only eligible
findings from the last completed review; absent or integrity-failed reviews release
nothing. This partial stop is not counted as successful completion.

Nine offline delivery tests cover at-capacity replacement, deduplication, reused blocks,
source binding, precise minimized feedback, a two-turn scripted repair, safe stopping,
and partial release with the completed review's candidate ID. A saved run-36 replay
reproduced 11 retained + 12 new = 23; explicit replacement rendered successfully.
Private replay summary: `reports/delivery_replay_20261028.json`. No model was called
for this replay and no semantic acceptance was inferred.

## Fixed live case

`tests/evaluation_cases.json` now includes `recognition_checkin_delivery`, preserving
the exact run-35/36 question and M14 / 2026-07-01 through 2026-09-30 scope. Controlled
CLI runs retain 32 calls, 1000 seconds and the unchanged per-profile output settings.
Review criteria are for external inspection and are not added to the agents' question.
Each live run uses a new output artifact. Provider names identify configured profiles,
not independently verified upstream model provenance.

## Offline verification before live calls

The final full release gate passed **343 tests in 117.279 seconds**, Python 3.12.10,
with zero provider calls. Private output: `reports/release_gate_verified_20261028.txt`.
The quick gate passed all nine delivery regressions. The eight capture/resume checks
include rejecting different workflow code before any model request. Existing source,
scope, privacy, quote, arithmetic, correction and partial-release checks remain in the
full suite. UI builds and browser behavior were outside this change's scope.

The A1/A2 code and fixed evaluation case were committed separately from the earlier
fixture restoration and gate. Live outcomes below are independent evidence, not inferred
from offline acceptance.

## Live attempt 37: provider prerequisite, not delivery validation

The first controlled Gemini attempt used the exact fixed question, M14/Q3 2026,
32 calls and 1000 seconds. It failed during planning after 7.719 seconds with
HTTP 402: the configured APInex provider requires its daily check-in for free models.
There was one generation request and zero successful generation calls. No specialist,
classification, completeness review or support review ran. This does not test A1/A2 live.

Private artifact: `reports/apinex_prueba_gemini_37.json`; matching execution log:
`reports/logs/20261029_014607_21b4e0fa3e4e.jsonl`. The captured code fingerprints match the frozen corrected
implementation. A same-code workflow retry can use this artifact after the account
prerequisite is resolved, with a fresh output filename and preserved budget/lineage.
Old runs 35/36 still require their preserved exact baseline.

Computer Use was denied access to Chrome, so the daily check-in was handed to the
user. No account configuration, credential, provider setting or execution budget was
changed. Additional provider calls are pending that external prerequisite.
