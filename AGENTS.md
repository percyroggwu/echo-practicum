# Echo project guidance

Current agents, 2026-11-04 (consolidated): one version of each agent. `agents/original.py`
(`OriginalAgent`, answer-edit-v2 delivery with the normalizing duplicate guard) and
`agents/zero_sugar.py` (`ZeroSugarAgent`, review-v8). The former `original_v8.py`,
`zero_sugar_v8.py`, `review_v7.py`, `run_agent_v8.py` and `measure_repair_delivery.py` were
removed; the v7 code they replaced is only in git history. Workflows cannot be resumed from a
checkpoint. Old-protocol scenario tests are archived, not run, in
`Agent_Echo/old_protocol_tests/`. See Agent_Echo/AGENTS_V8_DESIGN.md sections 9-12 and
Agent_Echo/GOLD_V1_RECORD.md.

Completed authorized v7 pair: the 412-test gate passed. Gemini 51 and Luna 52 both ended
partial; see Agent_Echo/RUNS_51_52_ANALYSIS.md. Exactly two fresh full workflows ran with
frozen source/data. No full acceptance, fixed-case provider benchmark, additional repeat,
post-pair runtime patch or Git publication. Preserve the captures and remaining failures.

Authorization, 2026-10-31: the user approved the corrected v7 plan, local tests and
exactly two new full workflows (Gemini/Luna). See Agent_Echo/UPDATE_2026-10-31_V7.md.
The single additional protocol attempt is shared per workflow and charged to unchanged
global budgets. Explanation repair uses remaining ordinary attempts. Preserve old replay,
strict checkpoint identities, five roles, both reviews and publication controls. No new
Git publication or extra API evaluation is implied.


Subsequent live authorization, 2026-10-31: the user requested one fresh Gemini and one
fresh Luna workflow. Runs 49/50 are completed and documented in
[the delivery record](Agent_Echo/DELIVERY_RELIABILITY_UPDATE.md#live-pair-gemini-49-and-luna-50-2026-10-31).
Gemini was partial; Luna failed at review delivery. Neither was fully accepted. This
authorization does not imply additional repeats, budget increases or runtime changes.

Current authorization, 2026-10-31: the user approved the revised audit delivery/review
update, offline tests and Git publication, explicitly without live calls. See
[the implemented contract](Agent_Echo/UPDATE_2026-10-31.md). New review-v6 uses an
issue-linked safety veto; old saved review gates retain their historical semantics.
New source-facts-v6 preserves v1-v5 replay. Both reviews, objective gates, five roles
and shared budgets remain. Keep quote-only fallback candidates unverified until review;
never infer semantic truth from assertion-alignment diagnostics. Preserve old checkpoints
and audits; do not bypass identity checks to resume them under changed code.

## Start with a small amount of context

Read this guidance and [Agent_Echo/PROJECT_CONTEXT.md](Agent_Echo/PROJECT_CONTEXT.md) once per chat when Echo work first becomes relevant, unless their contents are already available in the chat context. Reuse that orientation rather than repeating the reading chain for every question. Reread only relevant sections if the documents change or verification is needed, and follow only the links needed for the current request. This applies when opening `Final_Project` directly as well as when working from the parent Practicum workspace.

- Verify current code/configuration before changing behavior. Do not reread the entire repository for each question.
- Keep implemented behavior, observed results, proposals, and unresolved decisions distinct.
- When changing synthesis or presentation, preserve facts and provenance without freezing wording. Keep the role instructions, answer/replay contract and review schema aligned; distinguish mandatory corrections from optional suggestions, and retain compatibility for saved answer versions.
- Keep objective integrity checks separate from model judgment. Narrative digits, quantifiers and repairable presentation are not proof of false meaning. Current source-facts-v4 (and stored v3) sends those signals to ZeroSugar without making them deterministic failures; preserve v1/v2/v3 replay. Retain source/scope, quote-literalness, coverage and structured arithmetic checks. Do not add language-pattern rejection rules as substitutes for semantic review.
- Preserve the 2026-10-23 selected behavior: no mandatory per-question deliverable checklist; Original integrates specialist meaning with presentation autonomy, actual review corrections persist, and ZeroSugar separates visible-answer completeness from evidence support. Code retains citations by finding ID. New trace metadata must avoid copying questions or source text. Both reviews and source/scope controls remain required for acceptance.
- Preserve the existing five roles unless the user requests a role change. Echo is the overall system, not an additional agent.
- Preserve manager/date scoping, read-only data tools, citations, independent finding review, and withholding of unsupported output.
- Do not invent numbers, missing coverage, causal effects, benchmark results, or successful provider access. Demo and connection tests do not establish analytical quality.
- Use English for application code, prompts, project documentation, and manager-facing outputs. Explain work in the user's requested language.
- Credentials belong in the ignored local `.env` or approved process environment. Never read or print keys for orientation. Current non-secret model/endpoint settings and role assignments belong in `Agent_Echo/connections.json`.
- For code changes, use the checks documented in `Agent_Echo/TESTING_AND_RAG.md` as appropriate. Report what was actually run. Documentation-only changes need link/content review, not live API calls.
- Respect a user instruction to skip tests or live calls. The 2026-10-21 v3 update was authorized for code/documentation and GitHub publication without local tests or API calls; earlier test counts do not validate it. A future successful-answer claim requires inspecting the actual new run and completed review.
- The 2026-10-22 coordination update was initially authorized locally without tests or GitHub publication; the user subsequently authorized publication. Do not treat publication, earlier checks or run ten as validation of this update. Preserve historical artifacts and verify a fresh completed run before claiming that omission/repair behavior improved.

- The user authorized tests and GitHub publication for the 2026-10-23 selected update. Report offline test results separately from unverified live-model behavior; preserve run eleven and use a fresh output filename for any later live evaluation.

## Current review/data contract (2026-10-26)

- On 2026-10-30 the user authorized the system delivery follow-up, local tests and fresh Gemini/Luna workflows with connection retries. New answers use source-facts-v5 for exact inline quotation presentation only; preserve v1-v4 replay, existing model instructions/judgment rules, both reviews and all budgets. Assertion repairs retain assessments and origin identity; delivery measurements are observational. See Agent_Echo/DELIVERY_RELIABILITY_UPDATE.md for actual verification and live outcomes.

- On 2026-10-28 the user subsequently authorized the scoped audit delivery plan:
  A16/A11/A12/A14 and corrected A1/A2, local tests, publication and controlled live
  evaluation. The exact baseline is preserved privately; old workflow checkpoints
  require the matching old implementation. Keep identity checks strict. On 2026-10-29
  the user also authorized three A7/A6 review follow-up corrections, local verification
  and two fresh live runs with the same case and budgets. The user then authorized A19,
  A8, A18 and A17, a full local release gate and fresh Luna/Gemini runs 41/42. See the
  delivery update for actual outcomes; preserve their exact source/data identities.
  The user subsequently authorized A20-A22, local verification, fresh Gemini/Luna live
  runs and GitHub publication. The 365-test gate passed; Gemini 44 and Luna 45 completed
  four reviews each but both ended partial/revise. A20/A21's targeted cases were verified
  offline, not triggered live; A22's draft-cap stop was observed in both runs. See the
  latest dated sections in `Agent_Echo/DELIVERY_RELIABILITY_UPDATE.md` and
  `Agent_Echo/LIVE_TEST_HISTORY.md` for evidence and limits.
  A3-A5/A9-A10/A13,
  grouped review and reviewer-role changes remain deferred. See
  Agent_Echo/DELIVERY_RELIABILITY_UPDATE.md for actual results, not inherited test totals.

- On 2026-10-28 the user approved applying strengthened C1 and the shared reliability
  changes in Agent_Echo/C1_RELIABILITY_UPDATE.md to the main application, without C2/C4.
  New Original workflow checkpoints may continue pending coordinator/specialist/review
  work through release; the older no-Original/Vanilla retry restriction applies only to
  explicit legacy phase checkpoints. Preserve five roles, both reviews, source replay,
  scope/privacy controls and model judgment. The user explicitly requested no tests,
  builds or API calls. Static review is not functional or semantic validation.

- On 2026-10-27 the user approved correcting B after runs 27-29: review-v5 removes literal
  reconstruction and retains concise per-assertion judgments, source subsets, assigned
  assessment IDs and whole-finding withholding/repair. Do not replace semantic judgment
  with new wording rules. Existing source-facts replay, five roles and both phases remain.
- The user explicitly requested full local capture of inputs, schemas, model responses,
  arguments (including rejected ones), tool results/errors/feedback and phase checkpoints,
  excluding credentials. This supersedes prior minimization only for the separate ignored
  private detail files; short logs and manager projections remain minimized. Preserve
  parent artifacts, lineage, scope/source/profile identity and bounded retries. Legacy explicit phase-only review
  resumption must not call Original/Vanilla or automatically start a correction loop;
  new workflow continuation follows the 2026-10-28 contract above.
- The user explicitly requested no local tests/builds or agent/model calls during this
  update. Static review is permitted. New/changed fixtures are unrun; previous passing
  totals do not validate review-v5 or capture/resumption. Full runs 30-32 will be user-run.

- On 2026-10-27 the user selected assertion-level support review (option B). New live
  reviews use review-v4: every finding has explicit literal claim excerpts, factual/proposal
  kind, source subsets, assessments and reasons. Validate ordered textual coverage and
  references; any failed assertion withholds its whole finding and creates an Original
  repair. Do not infer semantic atomicity or truth from literal coverage. Novel proposals
  remain separate from their factual premises. Preserve v3 correction judgments, both
  phases, all five roles, old artifacts/replay, provider settings and execution budgets.
  322 offline checks and the frontend build passed; no live validation or publication.

- After run twenty-one, live review-v3 requests code-keyed mandatory/addressed booleans
  and reasons, not lifecycle statuses or replacement IDs. Code derives canonical states;
  required unaddressed omissions stay blocking. Preserve strict full coverage, both
  reviews and all objective gates. Legacy v2 submissions keep their conservative checks.
- After run twenty, ChatModel requests parallel_tool_calls=false for one required tool.
  Completeness rationale failures retain types/lengths only. Thirty-six focused checks
  passed; a saved-candidate completeness recheck completed in one live call with revise.
  This does not validate the full answer, support review or semantic correction quality.
- On 2026-10-27 ChatModel was corrected to preserve explicit strict tool flags. Three
  focused adapter checks and two minimal/synthetic APInex Luna calls passed, without
  employee data. This is transport evidence, not semantic or full-workflow validation;
  other Chat providers were not called. Preserve both reviews and correction lifecycle
  protections; alternative B remains deferred. See the current testing guide.
- After run eighteen, support-tool numeric_reviews/correction_reviews fields are requested
  only for trusted pending numeric tasks/correction obligations. Inactive fields become
  empty lists in code; no active judgment may be inferred or defaulted. Preserve full
  assessment coverage when tasks exist, contextual-schema diagnostics and all prior gates.
  This local update was not tested or published.
- The user-approved run-seventeen simplification uses shared survey-sentiment-v3 with
  general category definitions and contextual model judgment. Preserve historical v1/v2
  rubric identities and all full-context, traceability, privacy and review improvements.
  Do not add case-specific word/combination rules to force sentiment labels. Existing
  fixtures were aligned without running tests; this update remains local and unvalidated.
- The local run-sixteen follow-up shares versioned sentiment definitions between Vanilla
  and ZeroSugar, records new survey-sentiment-v2 reports and replays older unversioned
  reports as v1. New omission corrections retain exact request excerpts; factual repairs
  identify the claim and conflicting evidence. Original may challenge a correction and
  ZeroSugar independently reassesses it. Full response/label/reason input covers every
  privacy-released group; suppressed texts remain excluded. Coverage metadata contains
  counts/versions only. Preserve the existing input bounds, objective gates and budgets;
  never infer semantic correctness or zero indeterminate labels from full coverage.
  The user requested this update without tests or GitHub publication. Run sixteen is
  retained evidence for the preceding version, not validation of this follow-up.
- Treat supplied data by content, definitions and method; do not presume or automatically warn about synthetic origin. Preserve dataset history and objective source/scope/quote/arithmetic/privacy gates.
- New answers use source-facts-v4, preserving v1/v2/v3 rendering. New reviews use review-v3: one correction list, derived routing and states, and complete explicit obligation judgments. Keep legacy v2 withdrawal/consolidation checks. Never drop actual omissions because evidence exists off-screen.
- Original retains both internal analysis coordination and manager action proposals without mandatory per-question templates or another agent. Model judgment evaluates metric relevance; planned tasks are not automatically user requirements.
- Preserve phase diagnostics and source-version identity for partial release. Update UI projections/export descriptions alongside shared contracts. Runs twelve and thirteen are retained evidence, not validation of the new implementation.
- The local run-fifteen recovery update normalizes optional review annotations only, conservatively retains invalid closure of current corrections, and may hand validated repair instructions to Original after invalid support submissions within four total drafts (initial plus three revisions). Recovery remains available after any of the first three drafts. ZeroSugar retains three submission attempts per phase; shared call/time/tool/token budgets still take precedence. A repair handoff is not a completed review and cannot release findings. Both review stages remain required for acceptance. Completeness receives trusted scope/team context without source evidence; false omissions may be withdrawn against visible content. Keep these distinctions when maintaining diagnostics or release code.

## Maintain continuity

After a user-authorized change materially affects architecture, configuration, verified results, priorities, or pending decisions, update the relevant section of `Agent_Echo/PROJECT_CONTEXT.md` in the same task. Keep it compact and point to detailed sources rather than copying them.

Use [Agent_Echo/DOCUMENTATION_MAP.md](Agent_Echo/DOCUMENTATION_MAP.md) to find all operating guides, source contracts, dataset documentation and local historical notes. Update affected references together, checking links and obsolete commands. Preserve historical evidence and license notices rather than rewriting every file after each change.

This `AGENTS.md` guides the coding assistant; it is not an Echo runtime prompt. Echo's six shared model rules live in `Agent_Echo/agents/policies.py`, role-specific instructions in the five agent modules, and CLI behavior in `Agent_Echo/run_agent.py`. Keep responsibilities and deterministic controls in their existing modules; do not introduce a new policy agent or move role-specific logic into this guidance.

Record dates and evidence for observations. Do not turn a suggestion from a conversation into an approved implementation or replace detailed source documentation with an unsupported summary. Explain unresolved contradictions instead of silently choosing an older note.

This guidance and the context file support future chats; they do not automatically import every previous conversation or start background synchronization. Do not edit Codex's generated memory store as part of ordinary project documentation maintenance.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
