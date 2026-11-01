# Runs 51/52: v7 implementation evidence, 2026-10-31

Exactly two authorized fresh full workflows ran after the 412-test local gate. Their
question, M14/Q3 scope, database identity, 29 runtime source hashes, retrieval and shared
limits match the frozen pre-live manifest. No code changed between or after these runs.
No additional live fixed-case evaluation or acceptance-hunting repeat ran. These are
case observations, not a general model accuracy benchmark.

| Result | Gemini 51 | Luna 52 |
| --- | --- | --- |
| Profile/model | apinex_gemini_test / free/gemini-3.8-flash | apinex_test / free/gpt-6-luna |
| Final status | partial / revise | partial; latest support review failed |
| Provider generation calls / successful | 19 / 18 | 16 / 15 |
| Elapsed seconds | 420.766 | 351.593 |
| Completed candidate reviews, both phases | 2 | 1 |
| Findings released / withheld in published candidate | 16 / 0 | 7 / 2 |
| Extra protocol calls | 0 | 1 |
| Output-limit events | 1, recovered | 1, recovered |
| Final blocking stage | Original answer validation | ZeroSugar support delivery |
| Final error | agent_turn_limit after removal-reason mismatches | review_protocol_error after correction state conflict |

Released means eligible under the existing partial-release controls, not full fulfillment
or independently established semantic truth. Both published an earlier fully reviewed
candidate while retaining newer unverified work. No network failure explains either stop.

## What the implementation demonstrably changed

All four saved review candidates contain a source-built table of 13 classifications.
Source-bound claim replay passes for each, including the failed latest Luna review's
candidate. IDs and labels match each run's retained classifier output. Gemini stored
8 positive / 2 negative / 3 mixed; Luna stored 9 / 2 / 2. In particular Luna labelled
CMT27512 positive whereas Gemini labelled it mixed. This is classifier disagreement,
not a renderer swapping saved labels; neither classification is human-certified here.

The three completed support reviews provide all seven structured explanations with
valid references and substantive observations. No explanation-only repair was needed.
This establishes delivery of the new explanation fields in these cases, not their
semantic accuracy. Final projected Completeness rationales can still originate from
the earlier completeness phase; raw support explanations and merged final ratings must
not be treated as identical assessments.

Luna exercised localized correction_duplicate feedback with the exact repeated identity
and indices 1/2. The one shared protocol exception was charged to the unchanged global
budget. Its fourth response fixed that duplicate by setting the new positive-quotation
issue's related ID to null. It then failed correction_refinement_state on
C_c3503eb728141ef5_visible_2: that correction was simultaneously linked as still pending
and marked mandatory=true/addressed=true. The last error is therefore NOT another
duplicate rejection. The earlier serial parser concealed this additional state error
until the duplicate link was repaired.

The failed latest Luna review retained 13 structurally validated finding entries, with
9 provisionally supported and 4 withheld. None was released from that incomplete review.
Seven blocks came from the earlier completed review. The wrapper names both candidates
and the failed phase, rather than suggesting that no analysis exists or that the whole
workflow published zero findings. A cached entry is not a completed atomic review.

## Model behavior that still fails

Gemini's first completeness response says only 12 comment rows are present and that the
denominator is absent. The captured answer has 13 rows and Eligible_Comments=13, plus a
denominator sentence. Its extra demand to verify source literalness belongs in support,
not visible-answer completeness. Its complaint about duplicated/extra questions is real.
The subsequent support review withdrew the false omissions and kept the question repair.
The next Original edit introduced further duplicated examples/questions rather than
consolidating them. More specific instructions did not guarantee effective editing.

Luna's first candidate really lacks literal examples. Its completeness and support models
also falsely describe the complete 13-row classification table as missing CMT27506/07/11.
One reason says 11 rows while claiming three of 13 are absent. The source-built table and
replay directly contradict those absence assertions. Requiring an anonymity declaration
is also different from the user's instruction not to identify respondents; the answer
already says labels are not based on numerical ratings.

Luna's second completeness assessment repeats the out-of-scope-team demand despite the
trusted authorization context. It also calls a source-extracted positive quotation a
paraphrase. That quotation is literal for CMT27500, although citing four comments on the
same item makes its attribution less clear. The critical literal example is still absent,
so that objection remains legitimate. The response also repeats patterns, limits and
the same question ideas. Do not dismiss real omissions because other objections are false.

The narrative about mixed comments cites CMT27510 and CMT27512 although Luna's retained
labels for both are positive. Canonical table fidelity does not certify arbitrary prose.
The two withheld first-candidate findings are the complete classification table (under
a false absence rationale) and a mixed-comment comparison with weak evidence. These
require separate assessment; a single supported/withheld count conceals the distinction.

## Remaining system limitations

Gemini's terminal Original repair submitted seven incompatible removal/reason lists.
The first two have 19 removals and 20 reasons, including a reason for an already removed
block. Later responses use 6 or 14 reasons against different removal lists. Python's
one-reason-per-removed-block check is correct, but its generic feedback does not name
the missing/extra IDs. The new localized correction-ID feedback does not fix this other
delivery field. Refining this contract/diagnostic remains necessary for reliable editing.

Correction-link parsing still reports duplicate identity before later lifecycle-state
checks. Independent finding validation/cache now survives that error, but independent
administrative errors are not all reported together. Luna repaired the first reported
error on its last permitted attempt, then encountered another already-present conflict.
More retry capacity alone did not solve the serial-feedback problem.

Structured explanations are mechanically evaluable, not proof that ZeroSugar reads
tables, scope or source quotations correctly. Known false objections can still appear in
published limitations and cause a source-faithful table to be withheld. Python did not
invent those objections; its current publication policy follows the model's judgments.

## Cost and measurement limits

Provider-reported totals, including the recovered truncated responses:

| Tokens | Gemini 51 | Luna 52 |
| --- | --- | --- |
| Input | 324,402 | 269,775 |
| Output | 29,437 | 26,001 |

Every logical request has available provider usage. These are provider counters, not a
price calculation or independent tokenizer measurement. Request records distinguish
protocol and ordinary work; the extra exception did not increase the 32-call/1000-second
global limits. Both stopped with unused global budget under their local phase/agent caps.

The nine-case instrument and scorer were verified locally, without provider calls. Its
zero-false-objection/zero-missed-defect threshold is specified but not established for
either provider. No claim of measured sentiment accuracy or general reviewer accuracy.

## Evidence and next implications

- reports/apinex_prueba_gemini_51.json; run 20261031_184919_4a532e3a56e9.
- reports/apinex_prueba_vanilla_52.json; run 20261031_185641_3fac4ea27b96.
- reports/live_pair_20261031_51_52.json freezes source/data/profile identity.
- reports/live_pair_20261031_51_52_verified_final.json includes terminal rejection events
  as well as retry events, candidate replay, counters and phase results.
- reports/logs/details/<run_id>/exchanges.jsonl preserves complete actual payloads.

The next engineering targets are removal/reason localization and joint administrative
validation. The next model-quality target is false absence/scope objections on fixed
candidates, with reviewer-only reassessment distinguished from answer rewriting. These
are newly observed follow-up needs, not implemented after the live pair. The v7 changes
improve reproducibility and deliverable review structure, but do not yet produce a fully
accepted answer in either of these two full workflows.
