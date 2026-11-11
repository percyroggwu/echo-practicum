# Prompt audit: v7 vs current (2026-11-04)

Purpose: find general rules that were lost when the v8 prompts were rewritten from scratch,
without restoring v7 wholesale. v7 prompts were extracted from `main` before consolidation;
current prompts are in `agents/original.py`, `agents/zero_sugar.py` and `agents/policies.py`
(`COMMON_POLICY`, prepended to every prompt by `with_policies`, unchanged between versions).

Status legend:
- **kept**: the rule exists in the current prompt or in `COMMON_POLICY`, same meaning.
- **moved to code**: code now enforces it, so the prompt no longer needs it.
- **removed on purpose**: tailored to the test question, tied to the v7 tool contract, or linked to a known v7 error.
- **lost, valuable**: general rule with no replacement; evidence that its absence matters.
- **lost, harmless**: no replacement, but no evidence it is needed.

Section 6 lists the changes; all were applied on 2026-11-04 (see PROJECT_CONTEXT.md).

## 1. Planning prompt (`PLANNING_INSTRUCTIONS`)

Planning was never measured: M1 measured the reviewer, M2 the repair, and offline tests script the plan.
Runs 57, 59, 61, 64, 65 and 66 are the only evidence.

| v7 rule | Status | Evidence / reason | Recommended general wording |
|---|---|---|---|
| Sentiment-only request → `needs_sentiment=true, needs_text=true, needs_numbers=false, metrics=[]` unless SQL/rating metrics are separately requested | **lost, valuable** | Run 64: the plan added numbers and a chart to a sentiment question; Lime then failed and the call budget ran out | "A request about comment sentiment or comment examples does not need numbers: needs_numbers=false and metrics=[] unless the user also asks for survey ratings or other calculations." |
| "A structured SQL count alone does not need Vanilla"; "citing SQL results or explaining survey-score limitations does not require text retrieval" | **lost, valuable** (moderate) | No live failure seen yet in the opposite direction, but it is the mirror of the rule above and costs one line | "A numeric request alone does not need text: needs_text=false unless the user asks for comments, examples or their interpretation." |
| Worked example: quarterly Recognition trend with counts and means needs Cherry only | **removed on purpose** | Names the test dimension; the general rule above covers it | none |
| "For Recognition comment percentages with literal examples, do not add Manager support, survey scores or Cherry" | **removed on purpose** | Tailored to the gold question | none |
| Backend already restricts manager, roster and dates; no clarification needed | **kept** | "The application fixes the manager, dates and team roster" | none |
| Chart only if asked or useful to compare indicators | **kept**, but too loose | "clearly useful" lets the model add a chart; run 62 and 64 unrequested charts failed in Lime. Code now normalizes a chart without numbers | "include_chart: only if the user asks for a chart or graph." |
| One survey_trend per exact dimension; never copy example dimensions; cross-team uses dimension=null; [] for custom SQL | **kept** | Same meaning | none |
| "The application prepares these metrics; Cherry keeps tools for additional calculations" | **lost, harmless** | Internal detail; no evidence it changes plans | none |
| Clarification: "Remove it if the full request, scope or permitted tools already answer it" | **weakened** | Current text says "cannot be obtained with the permitted tools", but runs 65/66 asked the manager for the comments and then for the topic, both obtainable from Vanilla or stated in the question | "The comments, survey topics, ratings and team roster are available through the specialists; never ask the manager for them. Ask only when the question itself is ambiguous about what to analyze." |
| "Never ask for credentials, anonymous identities or wider access" | **kept** | Same meaning | none |

## 2. Original answer prompt (`INSTRUCTIONS`)

| v7 rule | Status | Evidence / reason | Recommended general wording |
|---|---|---|---|
| Delegation: calculations to Cherry, text and full sentiment classification to Vanilla | **kept** | JOB step 1 | none |
| At least one manager action, may be a new idea, cite basis, state benefit as assumption | **kept** | "THE ANSWER MUST CONTAIN" | none |
| "When evidence is insufficient, a justified validation or information-gathering step can be actionable" | **lost, valuable** (small) | Without it, a thin-evidence answer may invent a practice change instead of a validation step; matches the reviewer's ACTION_NOTE, which already lists "a validation step" as an action | Add to the action bullet: "When evidence is thin, a validation or information-gathering step is a valid action." |
| "Your internal plan is not this manager-facing action" | **lost, harmless** | v8 contract separates proposals from planning; no confusion observed | none |
| Preserve item counts; team questions and actions do not replace each other | **kept** | Same meaning | none |
| "Do not invent mandatory dates, owners or resources" | **lost, harmless** | Covered by "never invent numbers ... or people"; not seen in runs | none |
| Assess corrections against the question, answer and evidence; dispute unjustified ones | **kept** | correction_responses: fixed/disputed | none |
| "Explain unjustified repairs for ZeroSugar to reassess; never silently drop a pending correction" | **moved to code** | Code requires one correction_response per open correction | none |
| "An example existing in attached evidence is different from showing it to the reader" | **moved to code** | Examples are inserted by code from excerpt_ref | none |
| Reuse completed evidence; never resend an identical closed task | **kept** + code | `declined_requests` cache; COMMON_POLICY 6 | none |
| "Missing work, failed execution and absent records are different" | **kept** | COMMON_POLICY 2 | none |
| "The manager ID is not an Employee_ID" | **lost, harmless** | The ID never reaches SQL written by Original; Cherry uses catalog metrics | none |
| "Use pending numeric coverage to request only unresolved calculations" | **lost, harmless** | Reviewer NUMERIC_NOTE and repair flow handle it | none |
| submit_grounded_answer field mechanics (quote_ref, finding IDs) | **removed on purpose** | v7 delivery contract; replaced by answer-edit-v2 | none |
| One reviewable assertion per interpretation; separate attributions and premises | **kept** | "One idea per item", "one reviewable claim per item" | none |
| "Do not copy sources or tables to create a second report for the reviewer" | **kept** | "Do not restate their numbers in prose" | none |
| Percentages describe comments, not employees; labels provisional | **kept** | RULES | none |
| "Selected examples are not the whole category; keep narrative group counts consistent with the aggregate" | **lost, valuable** (small) | The reviewer still judges "a claim about a whole group needs evidence for the whole group"; telling Original the same prevents a repair round | Add to interpretations: "Describe a category through its aggregate; selected examples do not represent the whole category." |
| "Preserve their stated uncertainty without inventing explanations for category counts" | **lost, valuable** (small) | Same family of reviewer objection (unsupported causal reason for a count) | "Do not invent reasons for why a category is large or small." |
| "Optional style suggestions do not require correction or another specialist call" | **lost, harmless** | v8 reviewer has no suggestions field; only corrections reach Original | none |
| "Explain unresolved work honestly when evidence or execution limits prevent completion" | **kept** | COMMON_POLICY 6 | none |

## 3. ZeroSugar completeness (`COMPLETENESS_INSTRUCTIONS`)

| v7 rule | Status | Evidence / reason | Recommended general wording |
|---|---|---|---|
| Scope fixed; "all eligible" never means outside scope | **kept** | "All means all records within the scope" | none |
| "Do not infer omitted teams from an authorized team name" | **kept** (merged) | "Never ask for other teams" | none |
| "A quarter can contain records from one survey date; that alone is not missing coverage" | **lost, harmless** for now | Specific to quarterly numeric tables; no completeness objection of this type in M1 or runs 55-66. Re-add only if it reappears | (if needed) "A period with few survey dates is not missing coverage." |
| "A visible table denominator satisfies the request without a preferred n/N format" | **kept** (generalized) | "Do not add preferred formats"; tables in visible_inventory have their denominators | none |
| Item counts, purpose, flexible wording | **kept** | Same meaning | none |
| "An explanation of unavailable evidence can satisfy a conditional request" | **lost, valuable** (small) | General rule; without it the reviewer may demand content the data cannot provide and loop until the draft limit | "If the answer explains that requested evidence is unavailable, that satisfies the request; do not ask for it again." |
| "Material stored off-screen cannot satisfy requested visible content" | **moved to code** | visible_inventory is built from the rendered answer | none |
| Missing content vs visible contradiction, with location | **kept** | "missing or visible contradiction ... where" | none |
| "Number of cited examples need not equal the aggregate count" | **kept** (support) | "Selected examples need not cover a whole category" | none |
| Visible charts can satisfy a chart request | **lost, harmless** | visible_charts is in the payload; no objection seen | none |
| Do not add origin warnings or unrequested examples | **kept** | "Do not add requirements ... disclaimers" | none |
| "Echo's action policy is assessed in support, not invented as a user request here" | **lost, valuable** (small) | Without it, completeness may report a missing action as a user omission with an invented request_ref | "Echo's own action requirement is checked later; do not report it here." |
| English output; question language is not a reason to reject English | **kept** | COMMON_POLICY / RULES | none |

## 4. ZeroSugar support (`SUPPORT_INSTRUCTIONS` + notes)

| v7 rule | Status | Evidence / reason | Recommended general wording |
|---|---|---|---|
| Seven 1-3 dimensions; isolated score is not a veto | **kept** | "a score alone never blocks release" | none |
| Judge against full sources, not only the excerpt | **kept** | Same | none |
| Proposals: judge premises and reasoning; the idea need not be in a source; a benefit is not an observed effect | **kept** | Same | none |
| "Do not accept sentiment prevalence from top-k passages" | **moved to code** | Prevalence can only come from the full classification table; code checks coverage | none |
| "Missing recognition notes do not prove that no recognition happened" | **kept** (general) | COMMON_POLICY 2: "None proves zero activity" | none |
| No anonymous identification; no invented facts; causal claims need evidence | **kept** | COMMON_POLICY 1, 3 | none |
| Human validation pending; reject claims of validated accuracy or employee prevalence | **kept** | SENTIMENT_NOTE | none |
| "Do not apply a newer rubric retroactively to an older classification" | **lost, harmless** | Single rubric version in use (survey-sentiment-v3) | none |
| "Findings and actions support human review, not pay, promotion, discipline or termination" | **lost, valuable** | Safety boundary of the whole product; nothing else in the reviewer prompt names it, and safety_issue_index has no criterion | "An action that uses survey evidence for pay, promotion, discipline or termination decisions is a safety issue." |
| Lime chart review: indicator matches the question and answer; title, axes, units, denominators; no counts/percentages confusion, no hidden missing values, no causal implication | **lost, valuable** | `visualization` is sent to the reviewer, but no current instruction says how to judge it. Low urgency while charts are rare | Add a CHART_NOTE sent only when charts exist: "visualization holds Lime's chart. Check that it shows what the question asks, with correct units and denominators, and that it does not confuse counts with percentages or imply causation." |
| "Accept an honest no-chart explanation when evidence cannot support a chart" | **lost, valuable** | Run 62/64: an unrequested chart failed and blocked completion. Code fix is approved separately; the prompt side belongs in the same CHART_NOTE | Part of the CHART_NOTE: "If no chart was requested, its absence is never a problem." |
| Review task_outcomes: a decline requires reassignment; not proof of absent data | **lost, valuable** (small) | `task_outcomes` is still in the payload with no instruction | "task_outcomes lists each specialist task. A declined or failed task is not evidence that data is absent." |
| Literal copying proves provenance, not meaning | **kept** | COMMON_POLICY 1 | none |
| require_actionable policy; questions alone do not satisfy it | **kept** | ACTION_NOTE / LEGACY_ACTION_NOTE | none |
| Controlled tables and provisional-label disclosures are legitimate | **kept** (stronger) | "ALREADY VERIFIED BY CODE" block. Run 60 still hallucinated a negative value in a code table: a prompt problem, not a lost rule | (open item, not part of this audit) |
| review_warnings for source-facts-v3/v4; computed_comparisons | **removed on purpose** | Old formats; arithmetic is code-verified | none |
| correction_judgments mandatory/addressed per key | **removed on purpose** | Replaced by obligations open/satisfied/withdrawn | none |
| Withdraw unjustified or redundant inherited corrections; no duplicate repairs | **kept** | obligations "withdrawn"; "A refinement goes in its note" | none |
| pending_numeric_requests decisions | **kept** | NUMERIC_NOTE | none |
| "Review the complete revised package for regressions" | **lost, harmless** | Every draft gets a full fresh support review | none |
| "Data origin is not a reason to require or remove a caveat" | **kept** | COMMON_POLICY 1 | none |
| "'Ask the team:' still introduces a question" | **kept** (stronger) | ACTION_NOTE classifies proposals explicitly | none |
| Field limits, JSON-not-string, no text before the call | **kept** | OUTPUT line; schema enforces limits | none |

## 5. Summary

| Prompt | v7 rules | kept / moved to code | removed on purpose | lost, valuable | lost, harmless |
|---|---|---|---|---|---|
| Planning | 10 | 4 | 2 | 3 (one weakened) | 1 |
| Original | 21 | 12 | 1 | 3 | 5 |
| Completeness | 13 | 9 | 0 | 2 | 2 |
| Support | 23 | 15 | 2 | 4 | 2 |

Only the planning losses have live evidence (runs 64, 65, 66). The other valuable rules are
short additions with no observed failure yet; they should be added as single lines in the
current style, not by restoring v7 paragraphs.

What must **not** come back, because it caused the old errors:
- long, overlapping paragraphs (v7 support prompt: about 170 lines), which raised protocol failures and duplicated objections;
- question-specific rules (Recognition, Manager support), which would overfit the gold question;
- v7 field mechanics (quote_ref, correction_judgments, review_warnings), which belong to retired contracts.

## 6. Recommended changes (applied 2026-11-04, priority 1 and 2)

Priority 1, with live evidence (together with the three approved fixes):
1. Planning: sentiment-only means no numbers; numeric-only means no text; chart only if asked; never ask the manager for data the specialists can retrieve.

Priority 2, one line each, no observed failure yet:
2. Original: validation step is a valid action; describe categories through aggregates; no invented reasons for counts.
3. Completeness: explained unavailable evidence satisfies the request; the action requirement is checked later.
4. Support: task_outcomes line; CHART_NOTE sent only when a chart exists.

Adopted separately, not priority 2: the safety rule (pay, promotion, discipline, termination), a product boundary (relabelled 2026-11-05; see reports_gold/P2_DECISION_CRITERIA_v1.md).

Priority 2 changes need a fresh M1 reviewer measurement before adoption, because they change reviewer behavior.
