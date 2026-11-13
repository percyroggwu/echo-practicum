# Discovery: seven-role requirements review

Date: 2026-11-12. Design only. Reviewed plan: [v2](DISCOVERY_PLAN_v2_2026-11-11.md). Replacement: [scope and plan v3](DISCOVERY_SCOPE_AND_PLAN_v3_2026-11-12.md).

All seven requested agents used **`gpt-6-luna`, reasoning effort `medium`**. Their assignments were distinct. They examined the user's clarified objective: give value to people who indicate that work is unrecognized, and explain its impact on their own or another team. They were instructed not to preserve an arbitrary table limit, assume current rows were sufficient, implement changes or run evaluations.

## 1. Why the previous plan was insufficient

V2 specified automatic review, evidence controls and report reuse, but its actual population was accepted `OP_contributions`. It expressly excluded work not represented there. It did not define an employee-report source, an accountable response to that report, adequate completion/acceptance history, or measured beneficiary outcomes. Its scenario pack and data-construction quantities were not a concrete pilot scope.

The earlier table reviewer recommended one goals table and warned against precomputed analytical links. The parent adopted that as a selected design; subsequent reviewers challenged activation and source interpretation but did not require a complete record-construction blueprint for the broader worker-value promise. The parent then described one required table too categorically. No user instruction imposed that limit. V3 derives sources from the required facts and scenarios instead.

## 2. Product scope and value for people — reviewer 1

Ranked findings:

1. **P0:** A named employee report must enter review without an accepted contribution row.
2. **P0:** Source requirements must cover work, completion/acceptance, beneficiary and result, not just goal association.
3. **P0:** A finding is not a resolution; record acknowledgment, owner, disposition, follow-up and actual closure evidence.
4. **P1:** Routine work and work already within formal goals can deserve recognition.
5. **P1:** Sharing feedback, recognizing a person and completing a follow-up are different events.

Parent decision: make employee voice and an accountable response part of the core scope. A new employee portal is not required because correct collection is an explicit case assumption; employee-facing drafts/status extracts and recorded delivery remain distinguishable.

## 3. Source data and record construction — reviewer 2

Ranked findings:

1. **P0:** The source model is too thin; large existing row counts do not establish complete evidence for the new cases.
2. **P0:** Add an independent employee-report grain, task completion/milestone history and outcome observations.
3. **P1:** Preserve named beneficiary confirmation and dated recognition/sharing/action history.
4. **P1:** Candidate enumeration must unite reports and operational work and keep unmatched reports visible.
5. **P1:** Ordinary source foreign keys are legitimate; expected evaluation conclusions are what must stay hidden.

Parent decision: recommend six additional source relations for the selected pilot, extend existing feedback instead of duplicating it into another generic feedback table, and specify proposed record quantities. Six is the result of the chosen grains, not a maximum. A completion event relation covers multiple milestones without a separate deliverables master for this pilot.

## 4. Completion, goals and team impact — reviewer 3

Ranked findings:

1. **P0:** Delivered work, accepted work, achieved milestone and beneficiary impact are distinct.
2. **P0:** Final request snapshots cannot explain every reopening, changed commitment or accepted milestone.
3. **P0:** Before/after statements need metric definitions, units, windows, denominators and sources.
4. **P1:** Employee reporting can initiate investigation; independent confirmation supplies additional support.
5. **P1:** Distinguish association, goal attainment and attributed effect; the controlled scenario can record a causal mechanism when intended.

Parent decision: include task events and metric observations as required source types for the selected cases. Cherry calculates completion/time/quality/goal measures; Discovery interprets supported relationships; ZeroSugar independently checks the claims. Qualitative benefits remain valid without invented monetary values.

## 5. Agent architecture — reviewer 4

Ranked findings:

1. **P0:** Worker-reported and proactive leads must be independent entry paths.
2. **P0:** Choose evidence structure from scope rather than agent/table minimization.
3. **P0:** Provide a shared authorized projection separating sources, measures and interpretations.
4. **P1:** Preserve report origins when merging overlapping records into derived cases.
5. **P1:** Attribute benefit to home, partner or both teams, and distinguish group contributions from individual credit.

Parent decision: retain Discovery as the proposed specialist responsible for lead reconciliation and contribution-impact interpretation, but keep a matched existing-specialist baseline in evaluation. All employee reports receive a disposition; an exceptional-value filter cannot hide ordinary supported work.

## 6. Existing harness and case lifecycle — reviewer 5

Ranked findings:

1. **P0:** Broaden the manifest to reports, contributions and deliveries, not accepted contributions alone.
2. **P0:** Keep captured facts, derived cases, reviewed findings and manager decisions distinct.
3. **P0:** The reviewer needs independent scoped sources even if Vanilla never runs.
4. **P1:** Extend operation identity, role/repair enums, shared accounting and partial-release semantics throughout the existing harness.
5. **P1:** Do not treat v2's proposed three-call ceiling as validated capacity for a larger evidence pack.

Parent decision: keep the automatic hook before model planning and the existing composed-report two-phase review. Add separate analysis and action status, durable result reuse and a manager-approved local action ledger. Source analysis remains read-only; approved intent is not evidence of completed action.

## 7. Scenarios and evaluation — reviewer 6

Ranked findings:

1. **P0:** Freeze a finite roster, work window, baseline, cutoff and follow-up before generating data.
2. **P0:** Construct concrete source chains for home-team, cross-team and report-only work.
3. **P1:** Evaluate worker value and management response as well as source fidelity.
4. **P1:** Separate data improvements, specialist-role effects and proactive-workflow effects in comparisons.
5. **P1:** Keep expected answers private and existing M1-M4 gold unchanged.

Parent decision: use 18 pilot employees in three home-manager cohorts, two additional beneficiary teams and explicit 12/12/8-week windows. Include a record blueprint, eleven scenario families, contract checks and human adjudication. All figures are proposed construction targets, not generated or evaluated results.

## 8. Adversarial completeness auditor — reviewer 7

Ranked findings:

1. **P0:** A plan without intake and accountable closure does not deliver the promised worker value.
2. **P0:** Every promised impact needs a named source-record path.
3. **P1:** Scope must freeze people, time, denominator and follow-up, not just case names.
4. **P1:** Goal-aligned routine work must remain eligible.
5. **P1:** Analysis completion and follow-up closure require different meanings.

Parent decision: adopt a requirements-to-data-to-output-to-check matrix. Refine the suggested completion gate: unresolved claims or open human follow-ups do not make fully assessed analysis incomplete. Unassessed population or failed required review does. Never report a case as resolved solely because the analytical report completed.

## 9. Consolidation choices

- **Broadened:** employees' named reports, accepted and not-yet-accepted work, home-team value, completion history, observed results and manager response.
- **Added concretely:** proposed roster IDs, source windows, record targets, schema/grain map, case construction requirements, closure evidence and acceptance matrix.
- **Retained:** automatic review activation, model-independent source scope, existing harness, shared accounting, independent review, lineage, strict reuse and privacy.
- **Corrected:** normal factual links are not inherently analytical leakage. Keep the hidden judgment and expected relationship answers out of runtime, while retaining employee-supplied task references, acceptance records and measurement-to-goal links.
- **Not adopted:** a new employee portal, enterprise writeback, automatic external messages, a separate generic evidence platform, employee productivity ranking, or arbitrary schema/call limits chosen before evidence requirements.

The seventh reviewer also examined the v3 draft. Its final pass identified five residual gaps: deterministic population rules, employee receipt evidence, reports first received during follow-up, case-to-source reconciliation and avoiding attribution of seeded process improvements to Echo. The parent added explicit rules for all five. Employee response preparation remains separate from actual delivery, and open human actions remain separate from analysis coverage.

No reviewer or parent implemented runtime/data changes or ran application tests, builds, provider probes or live Echo evaluation. Existing unrelated work was preserved. The source checkout inspected was `ec4bc8a` with other local changes; those changes are not validated by this review.
