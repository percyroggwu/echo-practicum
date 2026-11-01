# Addendum E versus the runs 49/50 analysis, 2026-10-31

Read-only comparison of [Addendum E](AUDIT_2026-10-31.md#addendum-e---runs-49-50-the-duplicate-refinement-rejection-and-the-completeness-call-guard),
[the preceding analysis](RUNS_49_50_ANALYSIS.md), saved exchange/review artifacts and the
matching runtime. No new model call, test, runtime change, commit or publication. The
auditor's historical text is preserved rather than rewritten.

## Agreement and a necessary distinction

Both records identify the same immediate stops: Gemini's correction_duplicate rejection
and Luna's two-call completeness guard. Both establish successful transport, unused
workflow budget, older-candidate partial release in Gemini, no accepted Luna verdict,
generic correction-link feedback, short rating explanations, duplicate presentation and
misleading failed-phase text. Excerpt delivery recovered without A27; the low-score veto
was not exercised. There is no evidence here of general model superiority or general
semantic accuracy.

E.6/E.7 correctly emphasize that the provider did return developed reviews. Gemini's
rejected submissions include 16 finding-review entries; Luna's first call in each pair
contains a complete-looking revise review with three corrections. Saying merely that
the reviewer produced no valid verdict obscures the acceptance guard and recovery path.
These reviews are syntactically present, not independently established as semantically
correct. The original analysis already recorded their presence in G9/L1, but the later
conversational summary put too much explanatory weight on reviewer unreliability alone.
The immediate protocol stop and the incorrect judgments are separate problems.

## Material correction to E.4/E.6: two prior identities were available

E.6 says the F10 obligation was the previous round's pattern obligation and that the two
defects had only one legal refinement link. The stored candidate-two corrections and
the third-review input show otherwise:

| Existing identity | Origin candidate / finding | Stored failed assertions |
| --- | --- | --- |
| C_a51013e9d2d475bf_F9_assertions | a51013e9d2d475bf / F9 | Positive and mixed comments cluster around four practices |
| C_a51013e9d2d475bf_F10_assertions | a51013e9d2d475bf / F10 | CMT27502 classified negative; busy periods worsen the negative issue |

Both IDs were in the tool enum and review_obligations. The model also supplied a judgment
for each. It nevertheless linked the positive-pattern repair and the negative busy-period
repair to F10's identity on all three attempts. A same-issue refinement could use the
separate matching prior identity; a genuinely new issue could use null, as E.6 itself
acknowledges. Merely relinking without preserving the correct lifecycle judgments would
not suffice, but those judgments were available and mandatory/unaddressed for both IDs.

The claim that this run forced a repeated ID is therefore unsupported. Observation 50's
diagnostic defect remains confirmed. A broader one-obligation/multiple-defect design
question can still be investigated, but observation 51 and the proposed coalescing fix
cannot be justified by treating the two prior findings as one. Current F-numbers must not
be substituted for origin_candidate_id/origin_finding_id.

## Reconciliation is blocked, but moving the helper is not a ready-made fix

The duplicate guard does execute before reconciliation. However, raw submitted corrections
contain related_correction_id, not correction_id or obligation_id. The existing
reconcile_corrections helper groups on the latter two fields. Moving it unchanged ahead
of parsing/validation would not coalesce those raw objects. Its current behavior also
keeps the first main correction and attaches subsequent records as provenance; it is not
proof that two independent requested repairs remain fully active after a merge.

A33's localized ID/index feedback is supported. A34 needs an explicit identity and
multi-repair contract, source/lifecycle checks and coverage verification, rather than
merging every repeated link to make the submission pass. Independently validating and
retaining finding entries for repair can be evaluated without releasing an invalid review.

## Luna: the guard blocks progress, and first-call selection is a new policy

The captured provider requests have one available tool, tool_choice=required and
parallel_tool_calls=false. The raw responses have two distinct IDs and argument payloads;
they are not byte-identical duplicates introduced by Echo. The first carries three
corrections, score 1; the second has no corrections, score 2, and calls itself accidental.
The underlying model-versus-gateway origin remains unresolved.

Taking the first call would avoid this particular cardinality rejection. It does not
establish that the selected call is correct or that the full workflow would succeed.
The first proposed reviews deny category counts, percentages, a denominator, literal
examples and inline citations that are actually visible in the candidate. E.11 explicitly
does not evaluate that semantic disagreement. These evidence-reading mistakes remain
findings from the previous analysis, not contradictions disproved by the audit.

A32 changes which returned assessment becomes authoritative. It is a possible recovery
policy to specify and test, not an already-proven harmless duplicate normalization. A38
is a useful separation of call-protocol failure from a substantive review verdict.

## Rating and duplication measurements need stage labels

Direct artifact inspection finds seven one_character_dimensions in each of Gemini's
first two history records. The third history record has no such diagnostic: correction
parsing failed before the rating diagnostic stage. The three rejected raw third-round
submissions do contain seven one-character explanations. The exported completed verdicts
show six one-character fields because Completeness is later replaced by the substantive
completeness-phase rationale. E.3/E.8's 6/6/7 diagnostic count mixes those representations;
the raw explanations, recorded diagnostic and final projection must be kept separate.

The forcing rule did not change an observed verdict here: other issues already required
revise. Its existence is established by code/offline checks, not by a counterfactual
live result. Likewise, the 0.947 released duplication pair is confirmed. It measures
similarity, not semantic redundancy. The earlier implementation intentionally made this
metric observational. A36 would introduce a new release/consolidation policy; it is not
repairing a missing automatic gate that had already been authorized. The concrete repeated
limits paragraph can be consolidated without treating every high-overlap pair as false
or redundant. A near-cap output is a risk, not evidence that a hypothetical fourth attempt
would truncate; no truncation occurred in either run.

## Findings that E does not re-verify

E.11 excludes semantic grading and E.12 expressly does not re-verify the preceding
analysis's recommendations. Its silence does not invalidate the separately checked:

- CMT27502 assessment/reason contradiction and the citation-list misdescription.
- Incorrect instruction to exclude eligible CMT27511.
- Unreleased CMT27510/CMT27512 label swap and the six-example/thirteen-label delivery gap.
- Proposals schema permitting non-null quote selections while rendering forbids them.
- Luna's absent-analysis message despite a retained candidate and classifications.

These are different evidence checks from the audit's event/count reconstruction. Some are
literal consistency checks; sentiment truth and general reviewer accuracy remain ungraded.

## Resulting priorities

Use two separate verification tracks. Delivery checks should exercise exact correction
identity, localized errors, bounded handling of multiple calls, retained unverified work
and candidate-scoped reporting. Judgment checks should use fixed candidates and sources,
record correct versus false objections, and distinguish omissions from representation
preferences. Successful delivery alone cannot certify judgment, while incorrect judgment
alone does not explain why a received review never reaches validation.

No proposed change is implemented by this comparison. In particular A32, A34, a new
rationale rejection rule and automatic similarity-based release blocking require explicit
design decisions; they are not consequences of simply accepting the audit's measurements.
