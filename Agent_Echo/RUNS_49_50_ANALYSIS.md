# Runs 49/50: reasoning, protocol and system analysis, 2026-10-31

Read-only analysis of the saved artifacts, full provider exchanges, review snapshots and
matching implementation. No runtime change, model request, test execution or publication.
Historical artifacts and audits remain unchanged. This is an evidence-based case analysis,
not an independently annotated sentiment benchmark.

## Outcome and attribution boundary

Gemini 49 completed 20/20 provider calls in 475.500 seconds. It released ten finding
blocks from candidate two, with four withheld, and ended partial after candidate three's
support review exhausted three attempts. Luna 50 completed 13/13 calls in 342.046 seconds
and failed completeness review before any full review or release. Both use the same
question, authorized scope, database and a14973b runtime. There is no connection failure
or output truncation explaining these terminal outcomes.

Separate model judgment from malformed model/gateway output, deterministic safeguards,
confirmed implementation defects and recovery-policy limits. API success is not a valid
review. The captures establish what the gateway returned, not which upstream component
generated a malformed response.

## Findings

| ID | Observation | Attribution | Evidence / consequence |
| --- | --- | --- | --- |
| G1 | Candidate one's requested literal examples are absent | Generator omission | Completeness correctly requested positive and critical examples. Candidate two supplied them. |
| G2 | Original submitted three incompatible excerpt/source selections during repair | Model tool-argument error | Located errors at interpretations[0] and interpretations[2]; a later changed submission passed. The valid source catalog was supplied. The identical-submission shortcut did not end this run. |
| G3 | An assertion says CMT27502 is negative, is assessed contradicted, and is explained as confirmed negative | Reviewer reasoning contradiction | Candidate-two F10:A1's assessment conflicts with its reason and the retained classification. Structural validation cannot turn that explanation into semantic assurance. |
| G4 | F9's rationale says CMT27510 is missing although its assertion citation_ids include CMT27510 | Reviewer evidence-reading error | The reviewer misdescribes its own supplied source subset. This does not prove the entire pattern is supported: the check-in claim also has a real source-selection issue. |
| G5 | The reviewer requests all 13 comment labels while saying to exclude eligible CMT27511 | Reviewer correction error | CMT27511 exists and is classified mixed. The source list includes it. Original's third candidate did include it despite the bad instruction. |
| G6 | Candidate three swaps the saved labels for CMT27510 and CMT27512 | Generator fidelity error plus system handoff gap | Saved labels are positive/mixed; the narrative says mixed/positive. Counts stay 8/2/3, hiding the swap. This candidate was not released. |
| G7 | Two distinct repairs are linked to the negative-pattern obligation rather than separate positive/negative obligations | Model correction-identity error | Each of three support responses links both to C_a51013e9d2d475bf_F10_assertions, although the separate F9 obligation is supplied. This is not an exact duplicate that can simply be deduplicated. |
| G8 | Duplicate-correction feedback omits the repeated ID and conflicting positions | System diagnostic defect | content.resolve_corrections raises correction_duplicate without the offending ID or item indices; feedback is generic. The model repeats the association three times. |
| G9 | Correction-reference parsing aborts before independent finding entries are validated/retained | System recovery limitation | Each rejected response contains 16 finding-review entries and three corrections. resolve_corrections runs before normalize_finding_submission, so these entries never reach per-finding validation/cache. Their presence is not proof of validity or permission to release. |
| G10 | Six non-completeness rating rationales remain one character | Reviewer explanation failure | Both completed rounds preserve those raw API values. The application does not truncate them. The new policy avoids an additional submission rejection and retains partial support; it has not made the model explain its ratings. This was not the final protocol error. |
| L1 | Each completeness response contains two different review calls | Upstream tool-protocol violation; origin unresolved | The actual request has one tool, tool_choice=required and parallel_tool_calls=false. All three responses have distinct call IDs and arguments. The second calls itself accidental. That text is not authority to discard a competing call. |
| L2 | The proposed completeness review denies visible category counts, percentages and denominator | Reviewer reasoning error | The actual candidate table contains all five categories and Eligible_Comments=13. Trusted context identifies M14/Data Platforms as the authorized population. |
| L3 | The proposed completeness review says no literal examples or inline citations exist | Reviewer reasoning error | The candidate visibly includes positive/mixed/negative excerpts and bracketed citations. There is room to critique relevance or concision, not to assert their absence. |
| L4 | One distinct follow-up targets reviewers rather than explicitly the team | Generator instruction-following concern | There is a reasonable basis for questioning the second question's audience. Other versions of both questions are repeated. Do not dismiss this concern merely because the scope/example complaints are wrong. |
| S1 | The live proposals schema offers excerpt references that rendering forbids | Confirmed system contract inconsistency | content.live_answer_schema permits EX_/null for proposals; grounding.render_answer rejects every non-null proposal quote. Luna did submit proposal references. Its observed rejections first concern wrong sources, so this inconsistency is not proven to be their sole cause. |
| S2 | Only six explicit label objects are handed to Original although all 13 labels are retained | Confirmed information-delivery gap | delegate returns aggregate/examples, source text and narrative/claims, but not the retained sentiment report. The third Original input exposes label objects only for CMT27500/01/02/03/08/11. The seven remaining labels, including 10 and 12, are not transported as label records. |
| S3 | Luna's failure wrapper says no analysis was produced | Confirmed system presentation error | A full candidate, 13 labels, aggregates and source evidence exist; independent review did not complete. original.incomplete conflates absent verdict with absent analysis. |
| S4 | Gemini's wrapper says zero findings were released without specifying the failed phase/candidate | Confirmed system presentation ambiguity | Ten earlier-candidate blocks are published and correctly counted. The protocol-stop sentence imports zero from the failed latest phase without a clear boundary. Actual release gating did retain the older reviewed candidate. |
| S5 | Rephrased analysis, limits and follow-up blocks are repeated | Generator editing quality; no semantic deduplication guarantee | Gemini's released output repeats limits; Luna's candidate repeats themes and both question ideas. Explicit removal reasons do not themselves ensure good selection or consolidation. |

## The label handoff distinction

Both providers retained the same 13 individual labels: eight positive, two negative and
three mixed. This is agreement, not proof of semantic correctness. The exact positive
CMT27510 / mixed CMT27512 pair is in the stored report available to support review.
Original's last request, however, has only six explicitly labelled examples and the raw
comment texts. Asking it to reproduce the classifier's complete identity mapping through
prose therefore invites reconstruction of information already stored elsewhere.

Original remains responsible for falsely attributing the reconstructed mapping to the
classifier. The system is responsible for failing to deliver that mapping when requesting
its faithful display. A future repair should transport/render the existing records rather
than reclassify comments or enforce sentiment through wording rules.

## Correct checks versus missing recovery

Rejecting conflicting correction identities and two nonidentical review calls is a
defensible safeguard. Selecting one judgment automatically would change review meaning.
The confirmed defects are the inconsistent proposal contract, omitted label records,
nonlocalized correction feedback and inaccurate wrapper text. Retaining independently
validated pieces for a bounded retry is a recovery option; accepting an incomplete or
ambiguous verdict is not established as safe by these cases.

The valid source check and partial-release boundary worked: Gemini's newest label mapping
was not released, and Luna's incomplete review did not authorize publication. Neither
workflow triggered the quote-only fallback or an issue-linked low-score safety veto, so
these live runs do not validate those paths. Gemini's reported repair input tokens remain
22,252-26,595, above the 15,000 target.

## Priorities for a separately authorized correction

1. Deliver the retained per-comment label map with source/scope/rubric identity; use it
   directly for a requested display while keeping semantic classification provisional.
2. Make the proposals schema/feedback agree with the null-only quote rule. Keep literal
   examples in interpretations with their actual source identity.
3. Localize correction_duplicate with the repeated identity and both positions; validate
   independently checkable finding entries without granting release to an invalid review.
4. Specify bounded handling for multiple nonidentical review calls. Do not implement an
   instruction-in-rationale such as "ignore the other call" as an automatic selection rule.
5. Route explanation failures and false reviewer claims to reviewer reassessment. Repairing
   answer prose cannot supply a missing reviewer rationale. Preserve both phases and bounds.
6. Label wrapper counts by candidate/phase and distinguish generated-but-unverified work
   from absent analysis. Measure repair requests separately from reasoning correctness.

These are recommendations, not applied changes. Source code, budgets and provider settings
were not changed during this analysis.

## Evidence locations

- reports/apinex_prueba_gemini_49.json; run 20261031_073421_098f38a8bddd.
- reports/apinex_prueba_vanilla_50.json; run 20261031_074236_289203ec5f6b.
- reports/logs/details/<run_id>/exchanges.jsonl and each review checkpoint preserve the
  actual request, returned tool calls, candidate, evidence and rejected correction links.
- [content.py](agents/content.py): extract, resolve_corrections and live_answer_schema.
- [original.py](agents/original.py): delegate and incomplete.
- [zero_sugar.py](agents/zero_sugar.py): review_completeness and _review processing order.
- [grounding.py](agents/grounding.py): proposal_quote validation.
- [Observed pair record](DELIVERY_RELIABILITY_UPDATE.md#live-pair-gemini-49-and-luna-50-2026-10-31).

Private captures stay ignored locally. The reasoning examples above compare actual text,
stored labels and judgments; no historical result is rewritten or retroactively certified.
