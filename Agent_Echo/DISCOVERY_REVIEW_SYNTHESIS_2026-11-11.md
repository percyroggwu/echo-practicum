# Discovery plan: five independent reviews and synthesis

Date: 2026-11-11. Design review only. No runtime, database, prompt, profile, test or gold changes.

Reviewed baseline: [Discovery brainstorm and plan, November 10](DISCOVERY_BRAINSTORM_AND_PLAN_2026-11-10.md), checkout `4f4c3ef`, and subsequent conversational steering: Discovery should proactively investigate when a manager begins a team/period review, independently of Original anticipating its relevance. Strong, correctly collected synthetic evidence remains an explicit case assumption.

Five requested subagents used **`gpt-6-luna`, reasoning effort `medium`**. Reviews A, B and C examined the entire plan independently and in parallel. The table-information and harness specialists then examined their respective areas. All returned analyses; none edited files or ran application evaluations.

This record condenses their ranked findings and records the parent agent's decisions. The replacement design is [Discovery plan v2](DISCOVERY_PLAN_v2_2026-11-11.md). The November 10 document remains historical.

## 1. Full review A: product value and analytical weaknesses

1. **P0: question-led activation defeats discovery.** The old plan puts Discovery behind an Original planning flag. Current `OriginalAgent.plan()` is question-driven. Replace that dependency with an application-defined review-start operation.
2. **P0: cross-question result reuse does not exist.** `OriginalAgent.run()` clears children and retained work for every fresh workflow. The semantic-search cache contains embeddings, not completed findings. Define a persisted report identity and invalidation rules.
3. **P0: the original comparison cannot answer the strongest alternative.** Echo versus Echo + Discovery tests an architectural addition, not whether the workflow is worth using instead of a prepared general-purpose assistant. Include a matched general-purpose workflow in the decision-quality evaluation and measure preparation effort.
4. **P1: review-start lacks an entry point and result flow.** Define the review operation, its status, reopening and subsequent question use in CLI and UI.
5. **P1: linked partner evidence needs an allowlist.** A contribution link does not authorize a whole beneficiary roster. Producer and reviewer need the same permitted context.
6. **P1: goal association and causal effect are distinct claims.** Sources can document a contribution and outcome without demonstrating a measured causal effect. Require precise interpretation.
7. **P1: one planted story is a demonstration, not a general quality estimate.** Include differently worded/layout variants of the main initiative and background records.
8. **P2: visibility dashboards distract from the main decision.** Defer broad hours/recognition views until one useful, cited contribution report works.

Parent disposition: accept all eight directions. The matched general-purpose arm is a planned evaluation requirement, not a claim that a ChatGPT product benchmark has been run.

## 2. Full review B: runtime, evidence and release invariants

1. **P0: remove the initial model-selected Discovery flag.** Trigger on a trusted manager/team/period review, not on Original's relevance prediction.
2. **P0: specify durable freshness and provenance.** Key a report to scope, cutoff, data, collection contract, rubric, code/tools and analysis configuration; an old checkpoint is not a reusable report.
3. **P1: do not parallelize the first runtime version.** `RunBudget` and coordinator/capture state are mutable, and current specialist dispatch is sequential. Use a bounded staged pass first.
4. **P1: distinguish an automatic review report from an ad-hoc answer.** The final answer's acceptance path is question-oriented today. Add a product task specification and explicit report lifecycle rather than fabricating a user question or bypassing review.
5. **P1: define the eligible population.** Search relevance is not exhaustive discovery. Enumerate authorized contributions deterministically and retrieve context for those records, recording what remains unprocessed.
6. **P1: preserve the beyond-scorecard focus.** Recognition states are context, not the main product.
7. **P1: make baseline tasks and evaluation claims comparable.** Freeze identical objectives, scope and evidence; label small-case success as controlled demonstration evidence.
8. **P2: avoid turning documented links into causal proof.** Keep source association and benefit interpretation distinct.

Parent disposition: accept. Use the existing composed-report approval route, with no extra mandatory producer-review cycle. Keep proactive execution independent of model selection while retaining current role responsibilities.

## 3. Full review C: coherence, scope and evaluation

1. **P0: activation, bounded coverage and reuse need one lifecycle.** A proactive trigger without a finite population and persistence can become an expensive repeat scan or a silently incomplete search.
2. **P0: narrow the product contract.** The central finding should explain what was done, who benefited, what documented goal/outcome it supported, why ordinary reporting underdescribes it and what review decision is warranted.
3. **P0: absence statements require a collection basis.** The controlled scenario may declare complete collection; legacy quarterly/capped records must keep their original meaning.
4. **P1: stage execution before pursuing concurrency.** Measure latency before redesigning shared budget and capture infrastructure.
5. **P1: minimize schema machinery.** Goals/ownership/provenance are useful; extra linkage/event systems must earn their place.
6. **P1: distinguish insufficient evidence from low relevance.** A numeric zero cannot mean both ordinary work and unknown comparison. Use explicit evidence state, then a separate contextual relevance judgment.
7. **P1: protect review independence.** Let the reviewer examine underlying sources and rubric, without treating the producer's internal scores as authoritative.
8. **P1: define human adjudication and disagreements.** Blind adjudicators to configuration and producer scores; report raw per-case results and resolve disagreements explicitly.
9. **P2: defer a broad UI rollout.** One report/card and consistent mode/status/citations are sufficient for the first demonstration.

Parent disposition: accept with one refinement. ZeroSugar necessarily sees the final candidate claim it reviews. Independence means reconstructing authorized source context and judging it independently; it does not mean hiding the claim itself. Internal producer score totals are unnecessary and omitted from v2.

## 4. Table-information specialist

1. **P0: make `OP_goals` the required new source table.** Project objectives are not the contributor's assigned formal goals.
2. **P0: remove mandatory input `OP_contribution_goal_links`.** Prefilled mappings can supply the very relationship Discovery is supposed to find. A missing link also proves nothing about beyond-goal work. Derived links belong in the report, with source citations.
3. **P1: represent assignment, ownership and time explicitly.** One row can represent one version of a formal goal assigned to one employee or team for a period. Preserve goal revisions and complete applicable goal coverage.
4. **P1: reuse strong source records.** Contributions, requests and named partner interactions can carry accepted work and beneficiary confirmation. Add an artifact table only if actual source requirements exceed those records.
5. **P1: keep deterministic status and quantitative grain separate from model interpretation.** Visibility is event/cutoff-based. Hours belong to requests and must not multiply through contribution/feedback joins.
6. **P1: expose an explicit safe dossier.** Include applicable home goals, linked beneficiary context, dated sources and coverage; exclude unrelated partner data and anonymous identity links.
7. **P2: version manifest/dictionary/import and validate complete scenario chains.** Expected findings and mappings stay outside runtime.

Parent disposition: accept the one-table design. Adapt the proposed owner key to the actual schema: there is no separately verified canonical teams table to reference. Use current canonical team names, validate them against the pilot roster, and avoid inventing a `Team_ID` foreign key or a new team master table. Use separate goal assignment tables only if repeated shared-goal assignments become a real requirement.

## 5. Harness specialist

1. **P0: use `OriginalAgent.workflow()` as the automatic entry seam.** `run()` already initializes state, budget and capture. Invoke Discovery inside the review-mode workflow before `plan(question)` so the model cannot skip the initial investigation.
2. **P0: compose first, review once through the existing route.** Seed Discovery evidence/results into the current handoff, let Original compose the report, then use existing completeness/support review and release. Do not review Discovery separately and then review the same initial report again by default.
3. **P0: enforce required work and partial results.** Required Discovery failure cannot produce a complete review report. Supported independently reviewed blocks may still be released as partial.
4. **P1: bound Discovery inside the existing shared budget.** Add phase guards/reserved capacity for synthesis and review; do not create an unaccounted second budget.
5. **P1: extend narrow existing integration points.** Add role registry, CLI/API operation kind, trusted review task, source lookup, repair owner, metadata and safe projections. Current reviewer construction can depend on Vanilla's documents; remove that dependency for Discovery-only evidence.
6. **P1: persist reviewed reports and deduplicate starts.** Match strict identities, distinguish complete from partial and prevent duplicate same-key subprocess work. Deepening creates a new version.
7. **P1: reuse completed artifacts, not workflow checkpoints.** Original v8 workflows intentionally cannot resume; keep that restriction.
8. **P1: extend the gold conventions without rewriting M1-M4.** Discovery needs its own case family/runner and thin scoring support, plus trigger/reuse/invalidation/partial/budget tests.

Parent disposition: accept. Artifact reuse is an application feature to implement, not a capability of current caches. Runtime concurrency, new orchestration frameworks and workflow resumption are excluded from the first version.

## 6. Parent decisions and rejected overreach

| Decision | v2 resolution |
| --- | --- |
| Who activates Discovery? | Trusted `team_review` operation, before model planning; Original may deepen later. |
| Does every message start discovery? | No. A valid same-identity completed report is reused; ad-hoc answers have their own task and review. |
| Run specialists concurrently? | Defer; automatic discovery does not require concurrent execution. |
| Required schema additions? | One `OP_goals` source table. Derived goal/contribution links live in report output. |
| How to prove source quality? | A versioned complete-collection scenario contract and coherent operational evidence. Do not make incomplete data the main demo. |
| Who approves a report? | Existing Original composition plus ZeroSugar completeness/support and release machinery. |
| What is cached? | A versioned released report with provenance/coverage/identity, not a free-standing model answer or a resumed workflow. |
| What is the first UI? | Existing review presentation plus a clear contribution card and freshness/coverage status. |
| How to assess value? | Matched data/rubric/task evaluation, source fidelity, useful findings and preparation effort. Agent count is not the outcome. |

All five reviews were used. Their agreement is design input, not empirical proof. Some implementation details remain proposed until the specified contract and offline checks exist. No application tests, builds, live Echo workflows, data generation or Git publication were performed during this review.
