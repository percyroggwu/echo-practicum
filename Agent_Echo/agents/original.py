"""Original: coordinator with mandatory verification and bounded revision."""

from dataclasses import asdict
from copy import deepcopy
import json
import hashlib

from .cherry import CherryAgent
from .vanilla import VanillaAgent
from .zero_sugar import ZeroSugarAgent, ReviewRepairNeeded, VerificationResult, candidate_id
from .lime import LimeAgent
from .runtime import RunBudget, Specialist, function_tool, AgentResult, AgentRunError, reject_calls
from .execution_log import record, error_summary, explain_failure
from .findings import safe_follow_up, clarification_question, unresolved_follow_up
from .policies import with_policies
from .validation import ValidationError, repair_feedback, planning_value
from .capture import (checkpoint, checkpoint_progress, checkpoint_database_identity, agent_snapshot, json_value,
                      trace as full_trace, exception_context)
from .grounding import FactCatalog
from .content import fragments, extract
from .delivery_diagnostics import bind_corrections, repair_context, duplication
from .review_delivery import veto_active, obligation_groups

MAX_DRAFTS = 4

INSTRUCTIONS = """You are Original, Echo's coordinator and owner of the final manager-facing
answer. Answer the user's complete request in clear English, using the authorized scope.
Choose the presentation and level of detail that make the answer useful; distinguish
observations, provisional interpretation, uncertainty and proposed human action.
Echo requires a complete analytical answer to fulfill the user's request and include at
least one concrete proposed action for manager consideration. Derive the action through
reasoning about the analysis: it may introduce an idea not requested in the question or
stated in the sources. Cite its factual basis and explain how it might address a problem,
sustain a strength or resolve uncertainty. When evidence is insufficient for an improvement
proposal, a justified validation or information-gathering step can be actionable. Make
assumptions and expected benefits explicit; do not present them as observed facts or
demonstrated effects. Your internal query/specialist plan is not this manager-facing action.
Preserve all requested content and item counts. Team questions invite the team's response;
they and action recommendations serve different purposes and do not replace each other.
Choose the presentation freely without inventing mandatory dates, owners or resources.
Assess review corrections against the complete question, visible answer and evidence.
Explain unjustified or contradictory repairs for ZeroSugar to reassess; never silently
drop a pending correction or approve yourself.

Delegate structured calculations to Cherry and text retrieval/interpretation to Vanilla.
Full comment sentiment classification and its counts/percentages belong to Vanilla's
analyze_survey_sentiment tool, not numerical survey ratings or selected search examples.
Delegate the relevant analytical question with the original context. Specialists supply
analysis and evidence; you integrate one final answer without repeating their work.
Use an adequate specialist interpretation as the basis for synthesis. Edit as needed for
integration and clarity while preserving its supported meaning, disagreements and limits.
An example existing in attached evidence is different from showing it to the reader.

Reuse completed evidence and classification progress. Correct incompatible routing after
a specialist decline; never resend an identical closed task or widen scope. Missing work,
failed execution and absent records are different. The manager ID is not an Employee_ID.
Use pending numeric coverage to request only unresolved calculations. Charts are selected
by Lime when planned; ZeroSugar independently reviews the complete candidate.

Finish through submit_grounded_answer. Select source facts for numeric tables/calculations,
interpret cited text or rows through interpretations, and place proposed follow-up in
proposals. Literal examples select quote_ref; other interpretations use quote_ref=null.
Keep citations, numerical units and denominators tied to supplied evidence. A source table
already displays its cells; interpretation should explain meaning rather than repeat them.
Each interpretation item should express one independently reviewable assertion with its
own supporting source subset. Separate materially different attributions or qualifications
instead of combining them into an apparently supported paragraph. Keep factual premises
separate from proposed ideas. The application assigns finding IDs; do not copy sources or
tables to create a second report for the reviewer. ZeroSugar may flag a compound or
omitted assertion; it does not reconstruct your answer or repeat the specialist analysis.
Sentiment percentages describe comments, not employees; labels remain provisional.
Use the supplied classifications and aggregates consistently. Preserve their stated
uncertainty without inventing explanations for category counts.
Selected examples are not the complete category population. Keep narrative group counts
consistent with the aggregate, and show requested literal examples through quote_ref selections.

When review identifies pending corrections, resolve them with retained evidence or request
missing/disputed specialist analysis. Preserve valid requested content, the proposed action
and supported meaning while allowing rephrasing and removing redundancy. Correct their
substance when evidence requires it. The whole revised answer is reviewed
again. Optional style suggestions do not require correction or another specialist call.
Explain unresolved work honestly when evidence or execution limits prevent completion.
"""


class OriginalAgent(Specialist):
    source_grounding = True
    def __init__(self, database, scope, model_factory, mode="live", retrieval="lexical", embedding_model=None, cache_root=None, connections=None, model_call_limit=32, run_seconds=300):
        self.database, self.model_factory = database, model_factory
        self.retrieval, self.embedding_model, self.cache_root = retrieval, embedding_model, cache_root
        self.specialists, self.child_results = {}, []
        self.connection_summary = connections or {}
        self.model_call_limit, self.run_seconds = model_call_limit, run_seconds
        definitions = [function_tool(name, description, {"question": {"type": "string"},
            **({"task_type": {"type": "string", "enum": ["numeric"] if name == "ask_cherry" else ["text", "sentiment"]}}
               if mode == "live" else {})}) for name, description in (
            ("ask_cherry", "Ask Cherry a bounded question about structured evidence and calculations."),
            ("ask_vanilla", "Ask Vanilla for relevant textual evidence and a cited interpretation."))]
        super().__init__("Original", INSTRUCTIONS, model_factory("Original"), scope, definitions,
            {"ask_cherry": lambda question, task_type=None: self.delegate("Cherry", question, task_type),
             "ask_vanilla": lambda question, task_type=None: self.delegate("Vanilla", question, task_type)}, mode)
        self.all_definitions = definitions
        self.allowed_delegations = {"Cherry", "Vanilla"}
        self.declined_requests = {}
        self.challenge_definition = function_tool('challenge_corrections',
            'Ask ZeroSugar to reconsider specific corrections against the saved draft before rewriting it.', {
                'correction_ids': {'type': 'array', 'minItems': 1, 'maxItems': 8, 'items': {'type': 'string'}},
                'finding_ids': {'type': 'array', 'maxItems': 32, 'items': {'type': 'string'}},
                'reason': {'type': 'string', 'minLength': 1, 'maxLength': 1000}})
        self.handlers['challenge_corrections'] = self.challenge_corrections

    def plan(self, question):
        point = checkpoint('planning', self.name, self.scope.__dict__, {
            'question': question, 'mode': self.mode, 'profile': getattr(self.model, 'profile', None),
            'database_hash': checkpoint_database_identity(self.database)})
        self.planning_checkpoint = point
        try:
            result = self._plan(question)
            checkpoint_progress(point, status='completed', result=result)
            return result
        except BaseException as error:
            checkpoint_progress(point, status='failed', failure=error_summary(error))
            raise

    def _plan(self, question):
        self.planning_diagnostics = []
        tools = [function_tool("submit_plan", "Choose only the specialists needed by this question.", {
            "needs_numbers": {"type": "boolean"}, "needs_text": {"type": "boolean"},
            "needs_sentiment": {"type": "boolean", "description": "Full comment sentiment classification by Vanilla, including its counts/percentages; not survey ratings."},
            "include_chart": {"type": "boolean"}, "clarification_question": {"type": ["string", "null"]},
            "clarification_basis": {"type": ["object", "null"], "properties": {
                "missing_field": {"type": "string", "enum": ["manager_id", "start_date", "end_date", "metric", "task", "other"]},
                "missing_detail": {"type": "string", "minLength": 1, "maxLength": 240},
                "blocking_reason": {"type": "string", "minLength": 1, "maxLength": 500},
                "request_ref": {"type": "string", "enum": list(fragments(question, 'original_question'))}},
                "required": ["missing_field", "missing_detail", "blocking_reason", "request_ref"],
                "additionalProperties": False,
                "description": "Null without a clarification. Otherwise identify the missing detail and select request_ref from question_excerpts."},
            "metrics": {"type": "array", "maxItems": 32, "items": {"type": "object", "properties": {
                "metric": {"type": "string", "enum": ["cross_team_contributions", "survey_trend"]},
                "dimension": {"type": ["string", "null"], "description":
                    "Exact survey topic for survey_trend; null for cross-team counts. Never a time grouping."}},
                "required": ["metric", "dimension"], "additionalProperties": False}},
        })]
        history = getattr(self, 'planning_history', None) or [{"role": "user", "content": json.dumps({
            "question": question, "scope": self.scope.__dict__, "question_excerpts": fragments(question, 'original_question')})}]
        self.planning_history = history
        reconsidered_clarification = False
        for attempt in range(1, 3):
            self.budget.consume("model")
            turn = self.budget.respond(self.model, with_policies("Plan Echo's scoped analysis. Return submit_plan only. Structured SQL counts need Cherry; "
                "full comment sentiment classification and its counts/percentages need Vanilla ONLY: set needs_sentiment=true, "
                "needs_text=true, needs_numbers=false and metrics=[] unless the user separately requests SQL/rating metrics. "
                "For Recognition comment percentages with literal examples, do not add Manager support, survey scores or Cherry. "
                "use Vanilla for requested narrative/source interpretation as well as sentiment classification. A structured SQL count alone does not need "
                "Vanilla. Requests to cite SQL results or explain survey-score limitations do not "
                "require text retrieval. Use Vanilla for actual narrative examples or qualitative interpretation. "
                "For example, a quarterly numeric Recognition survey trend with dates, response counts, mean "
                "scores and metric limitations needs Cherry only; it does not request comment sentiment. "
                "The backend already restricts the data to the supplied manager's roster and dates; those details "
                "do not need clarification. Charts are optional; request one only if asked for or useful to compare indicators. "
                "Return metrics as a list of ALL needed catalog requests. Include one survey_trend entry per exact "
                "dimension explicitly needed by the user's rating question. Never copy example dimensions or add unrequested metrics. Cross-team counts use "
                "cross_team_contributions with dimension=null. Use metrics=[] for custom SQL or no numeric work. "
                "The application prepares these metrics; Cherry keeps tools to complete additional calculations. "
                "All output is English. Use clarification_question=null and clarification_basis=null unless a necessary "
                "task detail prevents proceeding. Otherwise supply a concrete missing_detail, blocking_reason and exact "
                "request_excerpt after reading the COMPLETE request. Your proposed clarification will be returned once "
                "for reconsideration within the existing two-attempt planning limit. Remove it if the full request, "
                "scope or permitted tools already answer it; never ask for credentials, anonymous identities or wider access."), history, tools, True)
            history.extend(turn.output_items)
            if len(turn.calls) != 1 or turn.calls[0].name != "submit_plan":
                feedback = {"error": "Return exactly one submit_plan call."}
                self.record_planning_attempt(attempt, "rejected", {}, feedback,
                                             attempt < 2, "invalid_plan_call")
                reject_calls(history, turn, json.dumps(feedback))
                continue
            call = turn.calls[0]
            received = {}
            try:
                plan = json.loads(call.arguments)
                if isinstance(plan, dict):
                    received = {key: planning_value(plan[key]) for key in
                                ("clarification_question", "clarification_basis") if key in plan}
                if isinstance(plan, dict) and "metrics" not in plan and self.mode != "live":
                    # Read older scripted fixtures; live plans must use the current schema.
                    metric, dimension = plan.pop("metric", "none"), plan.pop("dimension", "")
                    plan["metrics"] = [] if metric == "none" else [{"metric": metric, "dimension": dimension or None}]
                if isinstance(plan, dict) and self.mode != "live":
                    plan.setdefault("clarification_basis", None)
                    plan.setdefault("needs_sentiment", False)
                if isinstance(plan, dict):
                    # Read old saved/fixture plans without retaining the retired checklist.
                    plan.pop("deliverables", None)
                if not isinstance(plan, dict) or set(plan) != {"needs_numbers", "needs_text", "needs_sentiment", "include_chart", "clarification_question", "clarification_basis", "metrics"}:
                    raise ValueError("Plan fields differ from the required schema.")
                if any(type(plan[k]) is not bool for k in ("needs_numbers", "needs_text", "needs_sentiment", "include_chart")):
                    raise ValueError("Plan flags must be booleans.")
                if plan["needs_sentiment"] and not plan["needs_text"]:
                    raise ValueError("Sentiment classification requires Vanilla (needs_text=true).")
                if plan["include_chart"] and not plan["needs_numbers"]:
                    raise ValueError("A chart requires numeric evidence.")
                if not isinstance(plan["metrics"], list) or len(plan["metrics"]) > 32:
                    raise ValueError("metrics must be a list of at most 32 catalog requests.")
                if plan["metrics"] and not plan["needs_numbers"]:
                    raise ValueError("A metric requires the numeric specialist.")
                for request in plan["metrics"]:
                    if not isinstance(request, dict) or set(request) != {"metric", "dimension"} \
                            or request["metric"] not in {"cross_team_contributions", "survey_trend"}:
                        raise ValueError("Invalid planned metric request.")
                    if request["metric"] == "survey_trend":
                        if not isinstance(request["dimension"], str) or not 1 <= len(request["dimension"].strip()) <= 100:
                            raise ValueError("A survey trend needs one exact dimension per request.")
                    elif request["dimension"] is not None:
                        raise ValueError("Cross-team counts require dimension=null.")
                q = clarification_question(plan["clarification_question"])
                plan["clarification_question"] = q
                if q is not None:
                    basis = plan['clarification_basis']
                    if not isinstance(basis, dict) or 'request_ref' not in basis or 'request_excerpt' in basis:
                        raise ValidationError('clarification_reference', 'clarification_basis.request_ref',
                            'Select request_ref from question_excerpts; Python extracts the original question fragment.')
                    basis['request_excerpt'] = extract(basis.pop('request_ref'), fragments(question, 'original_question'),
                                                       field='clarification_basis.request_ref')
                    self.validate_clarification_basis(plan["clarification_basis"], question)
                    if not reconsidered_clarification:
                        reconsidered_clarification = True
                        raise ValidationError("clarification_recheck", "clarification_basis",
                            "Before asking the user, reconsider the COMPLETE original question and supplied scope. "
                            "Check whether the allegedly missing detail is already present or can be obtained with "
                            "permitted tools. Return a corrected plan with both clarification fields null if so; "
                            "otherwise return a justified necessary clarification. Do not guess missing facts.")
                elif plan["clarification_basis"] is not None:
                    plan["clarification_basis"] = None
                    self.record_planning_attempt(attempt, "normalized", received,
                        {"correction": "No clarification question; unused clarification_basis normalized to null."},
                        False, "unused_clarification_basis")
                if any(r["metric"] == "survey_trend" for r in plan["metrics"]) and q is None:
                    self.budget.consume("tool")
                    dimensions = self.specialist("Cherry").reader.describe()["survey_dimensions"]
                    for request in plan["metrics"]:
                        if request["metric"] != "survey_trend":
                            continue
                        matches = [d for d in dimensions if d.casefold() == request["dimension"].strip().casefold()]
                        if dimensions and not matches:
                            raise ValueError("Unknown survey dimension. Choose the topic requested by the user from: " +
                                             ", ".join(dimensions) + ". A quarter is a time grouping, not a survey dimension.")
                        request["dimension"] = matches[0] if matches else request["dimension"].strip()
                plan["metrics"] = list({(r["metric"], r["dimension"]): r for r in plan["metrics"]}.values())
                record("workflow_plan", agent="Original", needs_numbers=plan["needs_numbers"],
                       needs_text=plan["needs_text"], needs_sentiment=plan["needs_sentiment"], include_chart=plan["include_chart"], needs_clarification=q is not None,
                       metric_count=len(plan["metrics"]))
                return plan
            except (ValueError, TypeError) as error:
                feedback = repair_feedback(error) if isinstance(error, ValidationError) else {"error": str(error)}
                self.record_planning_attempt(attempt, "rejected", received, feedback,
                                             attempt < 2, **error_summary(error))
                history.append({"type": "function_call_output", "call_id": call.call_id,
                                "output": json.dumps(feedback)})
        raise RuntimeError("Original did not return a valid bounded analysis plan.")

    def record_planning_attempt(self, attempt, status, received, feedback, feedback_sent,
                                validation_code=None, **details):
        """Keep the same sanitized planning diagnostic in JSONL and the result artifact."""
        entry = {"attempt": attempt, "status": status, "received": received,
                 "feedback": {key: planning_value(value) if isinstance(value, str) else value
                              for key, value in feedback.items()},
                 "feedback_retry_available": feedback_sent, **details}
        if validation_code is not None:
            entry["validation_code"] = validation_code
        self.planning_diagnostics.append(entry)
        record("structured_response_repair" if status == "rejected" else "planning_normalization",
               agent="Original", stage="planning", **entry)

    def validate_clarification_basis(self, basis, question):
        """Check observable contradictions; prompt reconsideration handles semantic ambiguity."""
        fields = {"missing_field", "missing_detail", "blocking_reason", "request_excerpt"}
        if not isinstance(basis, dict) or set(basis) != fields:
            raise ValidationError("clarification_basis_required", "clarification_basis",
                                  "Identify missing_field, missing_detail, blocking_reason and request_excerpt.")
        if not isinstance(basis["missing_field"], str) or basis["missing_field"] not in {
                "manager_id", "start_date", "end_date", "metric", "task", "other"}:
            raise ValidationError("clarification_field", "clarification_basis.missing_field",
                                  "Choose a field from the declared clarification schema.")
        for field, maximum in (("missing_detail", 240), ("blocking_reason", 500), ("request_excerpt", 400)):
            if not isinstance(basis[field], str) or not 1 <= len(basis[field].strip()) <= maximum or len(basis[field]) > maximum:
                raise ValidationError("clarification_basis_text", "clarification_basis." + field,
                                      "Clarification details must be nonempty bounded strings.")
        if basis["request_excerpt"] not in question:
            raise ValidationError("clarification_excerpt_not_literal", "clarification_basis.request_excerpt",
                                  "Quote the original request exactly; do not invent a truncated or altered request.")
        if basis["missing_field"] in self.scope.__dict__ and self.scope.__dict__[basis["missing_field"]]:
            raise ValidationError("clarification_already_supplied", "clarification_basis.missing_field",
                                  "The application already supplies this scope field. Use it; do not ask for it again.")

    def set_delegations(self, names):
        self.allowed_delegations = set(names)
        self.definitions = [tool for tool in self.all_definitions
            if {"ask_cherry": "Cherry", "ask_vanilla": "Vanilla"}[tool["name"]] in self.allowed_delegations]
        if getattr(self, 'last_verdict', None) and self.last_verdict.corrections:
            self.definitions.append(self.challenge_definition)

    def challenge_corrections(self, correction_ids, finding_ids, reason):
        candidate = getattr(self, 'active_candidate', None)
        previous = getattr(self, 'last_verdict', None)
        if candidate is None or previous is None:
            raise ValueError('A completed review of a saved draft is required before challenging it.')
        known = {item['correction_id'] for item in previous.corrections}
        known_findings = {item['finding_id'] for item in previous.findings}
        if (not isinstance(correction_ids, list) or not 1 <= len(correction_ids) <= 8 or
                any(not isinstance(key, str) or key not in known for key in correction_ids) or
                not isinstance(finding_ids, list) or any(not isinstance(key, str) or key not in known_findings for key in finding_ids) or
                not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 1000):
            raise ValueError('Challenge existing correction/finding IDs and give a bounded substantive counterargument.')
        identity = candidate_id(candidate.answer, candidate.evidence, candidate.visualization)
        if identity in self.challenged_candidates:
            raise ValueError('This candidate already used its bounded reconsideration; repair remaining justified issues.')
        verifier = self.active_reviewer
        if verifier is None:
            cherry, vanilla = self.specialists.get('Cherry'), self.specialists.get('Vanilla')
            verifier = ZeroSugarAgent(self.scope, self.model_factory('ZeroSugar'), self.mode, budget=self.budget,
                sql_reader=cherry.reader if cherry else None,
                document_lookup={doc['citation_id']: doc for doc in vanilla.searcher.documents} if vanilla else None,
                sentiment_reports=candidate.sentiment,
                sentiment_documents=vanilla.sentiment_documents if vanilla else None,
                authorized_teams=getattr(vanilla or cherry, 'authorized_teams', None))
            self.active_reviewer = verifier
        verifier.correction_challenges = [{'correction_ids': correction_ids, 'finding_ids': finding_ids, 'reason': reason}]
        resumed = getattr(self, 'resume_challenge_review_progress', {})
        verifier.resume_finding_cache = resumed
        if not resumed:
            for key in finding_ids:
                getattr(verifier, '_finding_review_cache', {}).pop(key, None)
        if resumed.get('status') == 'completed' and resumed.get('result'):
            reviewed = VerificationResult(**resumed['result'])
        else:
            reviewed = verifier.review(self.original_request, candidate.answer, candidate.evidence, candidate.visualization,
                numeric_coverage=candidate.diagnostics.get('numeric_coverage'), claims=candidate.claims,
                grounding=candidate.grounding,
                task_outcomes=[{'agent': child['agent'], 'status': child['status'], 'task_outcome': child.get('task_outcome', {})}
                               for child in self.child_results],
                require_sentiment=candidate.diagnostics.get('requires_sentiment', False),
                previous_corrections=previous.corrections, require_actionable=True,
                resume_completeness=resumed.get('completed_completeness') or getattr(verifier, 'completed_completeness', None))
        self.resume_challenge_review_progress = {}
        self.challenged_candidates.add(identity)
        self.challenge_result = {'candidate_id': identity, 'verdict': asdict(reviewed), 'diagnostics': deepcopy(verifier.diagnostics)}
        self.last_verdict = reviewed
        record('correction_challenge_completed', agent='Original', candidate_id=identity,
               correction_ids=correction_ids, decision=reviewed.decision)
        return {'candidate_id': identity, 'decision': reviewed.decision,
                'corrections': reviewed.corrections, 'correction_reviews': reviewed.correction_reviews,
                'note': 'ZeroSugar reconsidered this exact saved candidate. Changed content still requires independent review.'}

    def specialist(self, name):
        if name not in self.specialists:
            if name == "Cherry":
                child = CherryAgent(self.database, self.scope, self.model_factory(name), self.mode, budget=self.budget)
            else:
                child = VanillaAgent(self.database, self.scope, self.model_factory(name), self.mode,
                    retrieval=self.retrieval, embedding_model=self.embedding_model, cache_root=self.cache_root, budget=self.budget)
                child.workflow_reuse = True
            self.specialists[name] = child
        return self.specialists[name]

    def delegate(self, name, question, task_type=None):
        if name not in self.allowed_delegations:
            raise ValueError("This repair/plan does not require that specialist. Use the supplied evidence.")
        if self.mode == "live" and task_type not in ({"numeric"} if name == "Cherry" else {"text", "sentiment"}):
            raise ValueError("Delegation task_type must match the specialist: Cherry=numeric, Vanilla=text/sentiment.")
        declined_key = (name, question.strip(), task_type)
        if declined_key in getattr(self, "declined_requests", {}):
            return self.declined_requests[declined_key]
        try:
            child = self.specialist(name)
            prepared = []
            if name == "Cherry":
                child.required_metrics = self.planned_metrics
                if self.repair_round == 0:
                    for request in self.planned_metrics:
                        key = (request["metric"], request["dimension"])
                        if key not in self.prepared_metrics:
                            self.budget.consume("tool")
                            try:
                                self.prepared_metrics[key] = child.handlers["run_metric"](**request)
                            except (ValueError, TypeError) as error:
                                record("prepared_metric_failed", agent="Cherry", **error_summary(error))
                                continue
                            record("prepared_metric", agent="Cherry", metric_id=request["metric"], remaining=self.budget.remaining())
                prepared = list(self.prepared_metrics.values())
            previous = next((item for item in reversed(self.child_results) if item["agent"] == name), None)
            if previous and previous.get("scope") == self.scope.__dict__:
                # Context reuse within this workflow, not a claim that the new task is done.
                retained = {item["citation_id"]: item for item in previous.get("evidence", [])}
                retained.update({item["citation_id"]: item for item in prepared})
                prepared = list(retained.values())
            context = ([{"role": "user", "content": json.dumps({"original_request": self.original_request,
                        "note": "Use the original request as context for this bounded task and preserve your role and fixed scope. Return supported analysis and evidence in the existing format; Original owns final integration."})}]
                       if getattr(self, "original_request", None) else [])
            result = child.run(question, initial_evidence=prepared, context=context)
        except AgentRunError as error:
            result = error.result
            failure = result.failure or {}
            if failure.get("error_category") in {"provider_timeout", "provider_connection"} or (
                    isinstance(failure.get("http_status"), int) and failure['http_status'] >= 500):
                # Exhausted transport retries suspend the same task; the coordinator must not rephrase it.
                raise
            result.diagnostics["numeric_coverage"] = child.numeric_coverage(result.evidence) if name == "Cherry" else []
            self.child_results.append(asdict(result))
            return {"agent": name, "status": "failed", "error": "Specialist execution did not finish; see failure.stage. Retained evidence is available, not independently approved. Reuse it, resolve missing work and submit a candidate for review.",
                    "task_outcome": result.task_outcome,
                    "evidence": result.evidence, "failure": result.failure,
                    "numeric_coverage": child.numeric_coverage(result.evidence) if name == "Cherry" else []}
        if result.scope != self.scope.__dict__:
            raise ValidationError("specialist_scope_binding", "scope", "Specialist output differs from the authorized workflow scope.")
        self.reusable_blocks.update(child.draft_blocks)
        self.draft_texts.update(child.draft_texts)
        # Validate source identifiers/scope before code constructs the handoff.
        FactCatalog(result.evidence, self.scope.__dict__)
        self.child_results.append(asdict(result))
        response = {"agent": name, "status": result.status, "task_outcome": result.task_outcome,
                "answer": result.answer, "scope": result.scope, "evidence": result.evidence,
                "claims": result.claims,
                "sentiment_classifications": [{"citation_id": e['citation_id'],
                    "rubric_version": e['rubric_version'], "scope": e['scope'],
                    "classification_binding": e['classification_binding'],
                    "records": e['classification_records']} for e in result.evidence if 'classification_records' in e],
                "numeric_coverage": child.numeric_coverage(result.evidence) if name == "Cherry" else []}
        if result.status == "declined":
            self.declined_requests[declined_key] = response
            if result.task_outcome.get("reason_code") == "out_of_role":
                self.set_delegations({"Cherry", "Vanilla"})
        elif result.status == "incomplete":
            self.declined_requests[declined_key] = response
        return response

    def run(self, question):
        if getattr(self, 'resume_workflow_state', None) is not None:
            return self._execute_workflow(question)
        # A fresh workflow prevents artifacts from earlier questions entering the answer.
        self.close()
        self.specialists, self.child_results = {}, []
        self.original_request = question
        self.budget = RunBudget(model_limit=self.model_call_limit,
            tool_limit=48 + 2 * max(0, self.model_call_limit - 32), seconds=self.run_seconds)
        self.last_result, self.last_verdict = None, None
        self.reviewed_candidate = None
        self.review_history = []
        self.planned_metrics, self.prepared_metrics, self.repair_round = [], {}, 0
        self.coordinator_diagnostics = {}
        self.planning_diagnostics = []
        self.declined_requests = {}
        self.attempt_reviews, self.drafts = [], []
        self.active_stage, self.verification_diagnostics = "planning", {}
        self.active_reviewer, self.challenge_result = None, None
        self.challenged_candidates = set()
        self.workflow_state = {}
        self.reusable_blocks, self.draft_blocks = {}, {}
        self.draft_texts = {}
        profiles = {item.get('profile') for item in self.connection_summary.values()}
        self.workflow_checkpoint = checkpoint('workflow', self.name, self.scope.__dict__, {
            'question': question, 'mode': self.mode, 'profile': next(iter(profiles)) if len(profiles) == 1 else None,
            'connections': self.connection_summary, 'database_hash': checkpoint_database_identity(self.database),
            'model_call_limit': self.model_call_limit, 'run_seconds': self.run_seconds,
            'retrieval': self.retrieval, 'cache_root': str(self.cache_root) if self.cache_root else None,
            'embedding_profile': getattr(self.embedding_model, 'profile', None)})
        self.save_workflow('planning')
        return self._execute_workflow(question)

    def save_workflow(self, phase=None, state=None, status='started'):
        names = ('plan', 'context', 'evidence', 'candidates', 'reviews', 'coordinator_trace',
                 'prior_visuals', 'prior_fingerprint', 'targets', 'pending_corrections', 'attempt',
                 'candidate', 'verdict', 'chart_failure')
        if state is not None:
            self.workflow_state = {key: json_value(state[key]) for key in names if key in state}
        if phase is not None:
            self.workflow_state['phase'] = phase
        checkpoint_progress(getattr(self, 'workflow_checkpoint', None), status=status,
            state=self.workflow_state, budget=self.budget.snapshot(),
            coordinator=agent_snapshot(self), children={name: agent_snapshot(child) for name, child in self.specialists.items()},
            child_results=self.child_results, planning_history=getattr(self, 'planning_history', []),
            reviewed_candidate=self.reviewed_candidate, attempt_reviews=self.attempt_reviews,
            review_history=self.review_history, planned_metrics=self.planned_metrics,
            prepared_metrics=[{'key': list(key), 'result': value} for key, value in self.prepared_metrics.items()],
            declined_requests=[{'key': list(key), 'result': value} for key, value in self.declined_requests.items()],
            allowed_delegations=list(self.allowed_delegations),
            challenge_result=self.challenge_result, challenged_candidates=list(self.challenged_candidates),
            review_checkpoint=getattr(getattr(self, 'active_reviewer', None), 'review_checkpoint', None))

    def _execute_workflow(self, question):
        try:
            result = self.workflow(question)
            self.save_workflow(status='completed')
            return result
        except Exception as error:
            full_trace('workflow_exception', **exception_context(error))
            self.save_workflow(status='failed')
            candidate = self.last_result or AgentResult("Original", question, "", self.scope.__dict__, mode=self.mode)
            candidate.failure = error_summary(error)
            candidate.failure["stage"] = candidate.diagnostics.get("stage", self.active_stage) if self.active_stage == "coordination" else self.active_stage
            candidate.diagnostics["verification"] = self.verification_diagnostics
            candidate.diagnostics["review_history"] = self.review_history
            candidate.diagnostics["planning_attempts"] = self.planning_diagnostics
            candidate.delegations = self.child_results
            candidate.sentiment = {key: value for child in self.child_results for key, value in child.get("sentiment", {}).items()}
            candidate.connections = self.connection_summary
            candidate.verification = {"decision": "revise", "status": "failed" if self.active_stage == "verification" else
                                      "completed" if self.attempt_reviews else "not_run", "reviews": self.attempt_reviews,
                                      "drafts_checked": len(self.drafts), "rejected_drafts": self.drafts}
            record("workflow_failed", agent="Original", **candidate.failure, remaining=self.budget.remaining())
            return self.incomplete(candidate, self.last_verdict)

    def incomplete(self, candidate, verdict):
        latest = {"candidate_id": candidate_id(candidate.answer, candidate.evidence, candidate.visualization), "answer": candidate.answer,
                  "claims": candidate.claims, "grounding": candidate.grounding, "visualization": candidate.visualization}
        reviewed = getattr(self, "reviewed_candidate", None) if verdict else None
        candidate.verification["latest_candidate_id"] = latest["candidate_id"]
        candidate.verification["completed_reviews"] = len(candidate.verification.get("reviews", []))
        if reviewed:
            candidate.verification["released_candidate_id"] = reviewed["candidate_id"]
            candidate.verification["released_candidate"] = {key: reviewed[key] for key in
                                                            ("candidate_id", "answer", "claims", "grounding", "visualization")}
            candidate.evidence = deepcopy(reviewed["evidence"])
            candidate.sentiment = deepcopy(reviewed["sentiment"])
        if not reviewed or reviewed["candidate_id"] != latest["candidate_id"]:
            candidate.verification["unreviewed_candidate"] = latest
        candidate.findings = [{**finding, "finding_id": finding.get("finding_id", f"F{index + 1}")}
                              for index, finding in enumerate(verdict.findings)] if verdict else []
        targets = verdict.repair_targets if verdict else ["Original"]
        candidate.limitations = (unresolved_follow_up(verdict) if verdict else []) or ([
            "An analysis candidate was generated, but independent review did not complete; its conclusions remain unverified."
            if latest['answer'] else "No analysis candidate was generated; no conclusions were reviewed."] if not verdict else safe_follow_up(targets)) or ["The requested analysis could not be fully verified."]
        if candidate.failure:
            candidate.limitations.insert(0, explain_failure(candidate.failure))
        if candidate.diagnostics.get('verification', {}).get('explanation_quality', {}).get('status') == 'incomplete':
            candidate.limitations.insert(0, 'The model acting as ZeroSugar did not supply complete rating explanations. This is a reviewer limitation, not a request to rewrite supported analysis.')
        verification_diagnostics = candidate.diagnostics.get("verification", {})
        protocol_stop = verification_diagnostics.get("protocol_recovery", {}) if isinstance(verification_diagnostics, dict) else {}
        if protocol_stop and not protocol_stop.get("support_review_completed"):
            provisional = protocol_stop.get("provisional_findings") or {}
            finding_count = provisional.get("finding_count", protocol_stop.get("retained_findings", 0))
            detail = (f"The model acting as ZeroSugar did not complete its structured review after "
                      f"{protocol_stop.get('attempts_used', protocol_stop.get('attempt_limit', 3))} submission attempts. "
                      f"Echo retained provisional judgments for {finding_count} findings, but released "
                      f"{protocol_stop.get('released_finding_count', 0)} findings because no complete review passed validation.")
            if provisional:
                detail = (f"The model acting as ZeroSugar did not complete its structured review after "
                          f"{protocol_stop.get('attempts_used', protocol_stop.get('attempt_limit', 3))} submission attempts. "
                          f"It provisionally judged {finding_count} findings ({provisional.get('supported_count', 0)} supported, "
                          f"{provisional.get('withheld_count', 0)} withheld); Echo released "
                          f"{protocol_stop.get('released_finding_count', 0)} because no complete review passed validation.")
            candidate.limitations.insert(0, detail)
            candidate.limitations[0] = (
                f"{protocol_stop.get('phase', 'support').capitalize()} review for candidate {protocol_stop.get('candidate_id', latest['candidate_id'])} did not complete "
                f"after {protocol_stop.get('attempts_used', 3)} attempts. No findings from that incomplete review were authorized for publication. "
                + (f"The output below uses the earlier completed review of candidate {reviewed['candidate_id']}." if reviewed else
                   "The generated candidate remains unverified."))
            candidate.verification["protocol_stop"] = {
                "attempts_used": protocol_stop.get("attempts_used"),
                "attempt_limit": protocol_stop.get("attempt_limit"),
                "phase": protocol_stop.get('phase', 'support'),
                "candidate_id": protocol_stop.get('candidate_id', latest['candidate_id']),
                "provisional_findings": deepcopy(provisional),
                "released_finding_count": protocol_stop.get("released_finding_count", 0),
            }
        candidate.next_steps = ["Address the listed unresolved items using retained evidence where available, then review the complete revised answer."]
        supported = [f["text"] for f in candidate.findings if f["status"] == "supported"]
        evidence_supported = sum(f.get('evidence_status', f['status']) == 'supported' for f in candidate.findings)
        if verdict and (verdict.deterministic_issues or veto_active(verdict)):
            supported = []
            candidate.findings = [{**f, "status": "withheld"} for f in candidate.findings]
        released_ids = [f["finding_id"] for f in candidate.findings if f["status"] == "supported"]
        if verdict and evidence_supported and not released_ids:
            reason = ('an explicitly linked global safety concern blocked publication'
                if getattr(verdict, 'release_gate', None) and veto_active(verdict) else
                'a global release check blocked publication')
            candidate.limitations.insert(0, f'The completed review supported {evidence_supported} findings on evidence; none were published because {reason}.')
        if reviewed:
            candidate.verification['reviewed_candidate_id'] = reviewed['candidate_id']
            if not released_ids:
                candidate.verification['reviewed_candidate'] = candidate.verification.pop('released_candidate', None)
                candidate.verification['released_candidate_id'] = None
        candidate.verification["released_finding_ids"] = released_ids
        pending_corrections = candidate.diagnostics.get("pending_corrections", getattr(verdict, 'corrections', []) if verdict else [])
        if not isinstance(pending_corrections, list):
            pending_corrections = []
        candidate.diagnostics['pending_corrections'] = pending_corrections
        groups = obligation_groups(pending_corrections)
        candidate.diagnostics["unresolved_views"] = {
            "manager_facing_limitations": {"count": len(candidate.limitations), "items": deepcopy(candidate.limitations)},
            "structured_pending_corrections": {"count": len(pending_corrections),
                                               'distinct_obligation_count': len(groups), 'obligations': groups,
                                               "correction_ids": [item.get("correction_id") for item in pending_corrections
                                                                  if isinstance(item, dict)]},
            "relationship": "Limitations are deduplicated manager-facing messages; pending corrections are individual structured review records. They are different views, so their counts need not match.",
        }
        candidate.claims = [deepcopy(claim) for claim in reviewed["claims"] if claim["finding_id"] in released_ids] if reviewed else []
        # Partial wrappers are not a full renderer selection. The reviewed source
        # candidate retains its own replay contract separately from released blocks.
        candidate.grounding = {}
        if reviewed and reviewed["candidate_id"] != latest["candidate_id"]:
            candidate.limitations.insert(0, 'A newer draft remains unverified. ' + (
                'Published blocks and unresolved items refer to the earlier reviewed version.' if released_ids else
                'No blocks were published; unresolved items refer to the earlier reviewed version.'))
        question = verdict.clarification_question if verdict and "clarify" in targets and not verdict.deterministic_issues \
            and not veto_active(verdict) else None
        if question and not veto_active(verdict):
            candidate.status = "needs_clarification"
            candidate.clarification_questions = [question]
        else:
            candidate.status = "partial" if supported else "failed"
        candidate.answer = ("Partial analysis — independently supported findings:\n\n"+"\n\n".join(supported)) if supported else "No verified answer was produced in this run."
        if supported and any(f["status"] == "supported" and f.get("kind") in {"interpretation", "proposal"} for f in candidate.findings):
            candidate.answer += "\n\nInterpretations remain provisional. Proposed actions/questions are for manager review, not observed outcomes."
        candidate.answer += "\n\nUnresolved:\n" + "\n".join("- " + item for item in candidate.limitations)
        if question:
            candidate.answer += "\n\nClarification needed: " + question
        candidate.diagnostics["released_duplication"] = duplication(candidate.answer)
        candidate.diagnostics['request_costs'] = deepcopy(getattr(getattr(self, 'budget', None), 'request_costs', []))
        candidate.diagnostics['review_protocol_repairs_used'] = getattr(getattr(self, 'budget', None), 'review_protocol_repairs', 0)
        candidate.verification["release_counts"] = {'reviewed': len(candidate.findings),
            'supported': evidence_supported, 'released': len(released_ids),
            'withheld_by_assertion_or_evidence': len(candidate.findings) - evidence_supported,
            'withheld_by_release_gate': evidence_supported - len(released_ids)}
        candidate.verification['release_gate'] = deepcopy(getattr(verdict, 'release_gate', None))
        candidate.diagnostics['unresolved_views']['manager_facing_limitations'] = {
            'count': len(candidate.limitations), 'items': deepcopy(candidate.limitations)}
        candidate.answer += "\n\nNext step: " + candidate.next_steps[0]
        candidate.visualization = {"charts": [], "reason": "Charts withheld while the package requires review.", "mode": self.mode, "tool_trace": []}
        return candidate

    def workflow(self, question):
        if not isinstance(question, str) or not question.strip() or len(question) > 4000:
            raise ValueError("Question must contain 1 to 4,000 characters.")
        restored = getattr(self, 'resume_workflow_state', None) or {}
        self.resume_workflow_state = None
        plan = restored.get('plan') or self.plan(question)
        self.coordinator_diagnostics["planning_attempts"] = self.planning_diagnostics
        self.numeric_requested = plan["needs_numbers"] or plan["needs_sentiment"]
        self.planned_metrics = plan["metrics"]
        if "Cherry" in self.specialists:
            self.specialists["Cherry"].required_metrics = self.planned_metrics
        if plan["clarification_question"]:
            q = plan["clarification_question"]
            return AgentResult("Original", question, "Clarification needed: " + q, self.scope.__dict__,
                mode=self.mode, status="needs_clarification", clarification_questions=[q],
                verification={"decision": "needs_clarification", "reviews": [], "drafts_checked": 0},
                diagnostics={"clarification_basis": plan["clarification_basis"], "planning_reconsidered": True,
                             "planning_attempts": self.planning_diagnostics})
        self.set_delegations([name for name, needed in (("Cherry", plan["needs_numbers"]), ("Vanilla", plan["needs_text"])) if needed])
        for name, needed in (("Cherry", plan["needs_numbers"]), ("Vanilla", plan["needs_text"]), ("Lime", plan["include_chart"])):
            if not needed:
                record("role_skipped", agent=name, reason="not_needed_by_plan")
        context, evidence = [], []
        candidates, reviews, coordinator_trace = [], [], []
        prior_visuals, prior_fingerprint, targets = None, None, set()
        pending_corrections = []
        if restored:
            context, evidence = restored.get('context', []), restored.get('evidence', [])
            candidates, reviews = restored.get('candidates', []), restored.get('reviews', [])
            coordinator_trace = restored.get('coordinator_trace', [])
            prior_visuals, prior_fingerprint = restored.get('prior_visuals'), restored.get('prior_fingerprint')
            targets, pending_corrections = set(restored.get('targets', [])), restored.get('pending_corrections', [])
            candidate = AgentResult(**restored['candidate']) if restored.get('candidate') else None
            self.active_candidate = candidate
            self.set_delegations(getattr(self, 'restored_delegations', self.allowed_delegations))
        for attempt in range(restored.get('attempt', 0), MAX_DRAFTS):
            resume_phase = restored.get('phase') if attempt == restored.get('attempt', 0) else None
            self.repair_round = attempt
            if resume_phase in {'chart_planning', 'verification', 'reviewed'}:
                record('workflow_stage_reused', agent='Original', phase=resume_phase, draft_number=attempt + 1)
            elif attempt and targets == {"Lime"}:
                record("repair_reuse", agent="Original", reason="chart_only_repair")
            else:
                numeric_child = self.specialists.get("Cherry")
                pending_coverage = numeric_child.numeric_coverage(evidence) if numeric_child else [
                    {**request, "status": "pending", "citation_id": None} for request in self.planned_metrics]
                task_context = [{"role": "user", "content": json.dumps({
                    "numeric_coverage": pending_coverage, "pending_corrections": repair_context(pending_corrections, self.draft_blocks)})}]
                self.active_stage = "coordination"
                self.save_workflow('coordination', locals())
                candidate = super().run(question, initial_evidence=evidence, context=context + task_context,
                                        diagnostics=self.coordinator_diagnostics)
                coordinator_trace.extend(candidate.tool_trace)
            if resume_phase not in {'chart_planning', 'verification', 'reviewed'}:
                candidates.append(candidate.answer)
            self.drafts = candidates
            self.last_result = candidate
            self.active_candidate = candidate
            catalog = FactCatalog(candidate.evidence, self.scope.__dict__)
            canonical = {item["citation_id"]: item for child in self.child_results for item in child.get("evidence", [])}
            missing_sources = sorted(set(canonical) - set(catalog.sources))
            if missing_sources:
                raise ValidationError('evidence_handoff_coverage', 'evidence',
                    'The candidate packet must retain all authorized specialist evidence.', missing_source_ids=missing_sources)
            for key, source in catalog.sources.items():
                if key in canonical and source != canonical[key]:
                    raise ValidationError("evidence_handoff_binding", "evidence", "Candidate evidence differs from the retained specialist record.", source_id=key)
            referenced = {key for claim in candidate.claims or [] for key in claim.get("citation_ids", [])}
            if not referenced.issubset(catalog.sources):
                raise ValidationError("evidence_handoff_missing", "evidence", "Candidate references lack their retained source records.")
            record("evidence_handoff_bound", agent="Original", source_count=len(catalog.sources),
                   evidence_binding=hashlib.sha256(json.dumps(candidate.evidence, sort_keys=True).encode()).hexdigest()[:16])
            cherry = self.specialists.get("Cherry")
            vanilla = self.specialists.get("Vanilla")
            lookup = {doc["citation_id"]: doc for doc in vanilla.searcher.documents} if vanilla else None
            candidate.sentiment = {key: value for child in self.child_results
                                   for key, value in child.get("sentiment", {}).items()}
            verifier = ZeroSugarAgent(self.scope, self.model_factory("ZeroSugar"), self.mode,
                budget=self.budget, sql_reader=cherry.reader if cherry else None, document_lookup=lookup,
                sentiment_reports=candidate.sentiment,
                sentiment_documents=vanilla.sentiment_documents if vanilla else None,
                authorized_teams=getattr(vanilla or cherry, "authorized_teams", None))
            self.active_reviewer = verifier
            numeric_evidence = [item for item in candidate.evidence if item.get("producer") == "Cherry" and "sql" in item]
            fingerprint = hashlib.sha256(json.dumps(numeric_evidence, sort_keys=True).encode()).hexdigest()
            chart_failure = None
            if resume_phase in {'verification', 'reviewed'}:
                chart_failure = restored.get('chart_failure')
            elif plan["include_chart"]:
                if prior_visuals is not None and prior_fingerprint == fingerprint and ("Lime" not in targets or
                        (prior_visuals.get("task_outcome") or {}).get("status") == "declined"):
                    candidate.visualization = prior_visuals
                    record("repair_reuse", agent="Lime", reason="unchanged_numeric_evidence")
                else:
                    lime = LimeAgent(self.scope, self.model_factory("Lime"), self.mode, self.budget)
                    try:
                        self.active_stage = "chart_planning"
                        self.save_workflow('chart_planning', locals())
                        candidate.visualization = asdict(lime.plan(question, candidate.answer, candidate.evidence,
                                                  feedback=reviews[-1] if reviews else None))
                        prior_visuals, prior_fingerprint = candidate.visualization, fingerprint
                    except (RuntimeError, ValueError) as error:
                        chart_failure = error_summary(error)
                        chart_failure["stage"] = "chart_planning"
                        candidate.diagnostics["Lime"] = lime.diagnostics
                        record("chart_planning_failed", agent="Lime", **chart_failure)
                        candidate.visualization = {"charts": [], "reason": "The planned chart could not be completed.", "mode": self.mode, "tool_trace": []}
                if (candidate.visualization.get("task_outcome") or {}).get("status") == "declined":
                    chart_failure = {"error_category": "task_declined"}
            else:
                candidate.visualization = {"charts": [], "reason": "No chart needed by the analysis plan.", "mode": self.mode, "tool_trace": []}
            candidate.rag = {"specialist_runs": [child["rag"] for child in self.child_results if child.get("rag")],
                "note": "RAG is recorded only when Vanilla runs; numerical-only questions may use Cherry alone."}
            coverage = cherry.numeric_coverage(candidate.evidence) if cherry else [
                {**request, "status": "pending", "citation_id": None} for request in self.planned_metrics]
            candidate.diagnostics["numeric_coverage"] = coverage
            candidate.diagnostics["requires_sentiment"] = plan["needs_sentiment"]
            self.active_stage = "verification"
            self.save_workflow('verification', locals())
            self.verification_diagnostics = verifier.diagnostics
            self.review_history.append(verifier.diagnostics)
            candidate.diagnostics["review_history"] = self.review_history
            try:
                if resume_phase == 'reviewed':
                    verdict = VerificationResult(**restored['verdict'])
                elif self.challenge_result and self.challenge_result['candidate_id'] == candidate_id(candidate.answer, candidate.evidence, candidate.visualization):
                    verdict = VerificationResult(**self.challenge_result['verdict'])
                    verifier.diagnostics.update(self.challenge_result['diagnostics'])
                    record('review_reused', agent='ZeroSugar', candidate_id=verdict.candidate_id, reason='unchanged_challenged_candidate')
                else:
                    if self.challenge_result:
                        pending_corrections = self.challenge_result['verdict']['corrections']
                    review_progress = getattr(self, 'resume_review_progress', {})
                    verifier.resume_finding_cache = review_progress
                    verdict = verifier.review(question, candidate.answer, candidate.evidence, candidate.visualization,
                                          numeric_coverage=coverage, claims=candidate.claims or None,
                                          grounding=candidate.grounding or None,
                                          task_outcomes=[{"agent": c["agent"], "status": c["status"], "task_outcome": c.get("task_outcome", {})}
                                                         for c in self.child_results], require_sentiment=plan["needs_sentiment"],
                                          previous_corrections=pending_corrections, require_actionable=True,
                                          resume_completeness=review_progress.get('completed_completeness'))
                    self.resume_review_progress = {}
                self.challenge_result = None
            except ReviewRepairNeeded as error:
                if attempt + 1 >= MAX_DRAFTS or error.candidate_id != candidate_id(candidate.answer, candidate.evidence, candidate.visualization):
                    raise
                pending_corrections = deepcopy(error.corrections)
                candidate.diagnostics["pending_corrections"] = pending_corrections
                candidate.diagnostics["verification"] = verifier.diagnostics
                evidence = candidate.evidence
                targets = {item["owner"] for item in pending_corrections}
                self.set_delegations({"Cherry", "Vanilla"} if "Original" in targets else targets & {"Cherry", "Vanilla"})
                record("review_repair_requested", agent="Original", candidate_id=error.candidate_id,
                       correction_ids=[item["correction_id"] for item in pending_corrections],
                       support_review_completed=False, released_findings=0,
                       draft_number=attempt + 1, draft_limit=MAX_DRAFTS)
                context = [{"role": "assistant", "content": candidate.answer}, {"role": "user", "content":
                    "The support review did not complete. These are visible-answer repair instructions, not an approval. "
                    "Address the pending corrections or explain an unjustified observation against the visible draft. "
                    "Reuse retained evidence and show requested content to the reader. The complete revised answer "
                    "must pass both independent reviews before publication. The active pending corrections are supplied "
                    "in the coordination context; the retrieved evidence is supplied once as source evidence."}]
                continue
            bind_corrections(verdict.corrections, verdict.findings, self.draft_blocks, verdict.candidate_id)
            self.save_workflow('reviewed', locals())
            pending_numeric = [item for item in coverage if item["status"] in {"pending", "error"}]
            retired = [pending_numeric[int(item["request_id"][1:]) - 1] for item in verdict.numeric_reviews
                       if item["decision"] == "not_required"]
            if retired:
                self.planned_metrics = [request for request in self.planned_metrics if not any(
                    all(request.get(key) == item.get(key) for key in ("metric", "dimension")) for item in retired)]
                if cherry:
                    cherry.required_metrics = self.planned_metrics
                candidate.diagnostics["retired_numeric_requests"] = retired
            if chart_failure:
                verdict.decision = "revise"
                verdict.repair_targets = sorted(set(verdict.repair_targets) | {"Lime"})
                verdict.issues.append("The planned chart could not be completed.")
                verdict.corrections.append({"correction_id": f"C_{candidate_id(candidate.answer)}_chart",
                    "issue_index": len(verdict.issues) - 1, "issue": verdict.issues[-1], "kind": "coverage",
                    "owner": "Lime", "requested_change": verdict.issues[-1], "citation_ids": [], "request_excerpt": None})
                candidate.failure = chart_failure
            verifier.diagnostics["duplication"] = duplication(candidate.answer)
            reviews.append(asdict(verdict))
            candidate.diagnostics["verification"] = verifier.diagnostics
            candidate.diagnostics["review_phases"] = verifier.diagnostics.get("review_phases", [])
            self.last_verdict, self.attempt_reviews = verdict, reviews
            self.reviewed_candidate = deepcopy({"candidate_id": verdict.candidate_id, "answer": candidate.answer,
                                                "claims": candidate.claims, "grounding": candidate.grounding,
                                                "evidence": candidate.evidence, "sentiment": candidate.sentiment,
                                                "visualization": candidate.visualization})
            self.active_stage = "release"
            candidate.findings = verdict.findings
            candidate.diagnostics["pending_corrections"] = verdict.corrections
            if verdict.decision == "accept":
                candidate.verification = {"decision": "accept", "status": "completed", "reviews": reviews, "drafts_checked": len(candidates),
                                          "completed_reviews": len(reviews), "latest_candidate_id": verdict.candidate_id,
                                          "released_candidate_id": verdict.candidate_id}
                candidate.verification['release_gate'] = deepcopy(verdict.release_gate)
                candidate.verification['release_counts'] = {'reviewed': len(verdict.findings),
                    'supported': len(verdict.findings), 'released': len(verdict.findings),
                    'withheld_by_assertion_or_evidence': 0, 'withheld_by_release_gate': 0}
                candidate.delegations = self.child_results
                candidate.tool_trace = coordinator_trace
                candidate.connections = self.connection_summary
                latest_children = {c["agent"]: c for c in self.child_results}
                unresolved_child = any(c.get("status") == "incomplete" or
                    (c.get("status") == "failed" and not c.get("task_outcome", {}).get("evidence_retained")) or
                    (c.get("status") == "declined" and c.get("task_outcome", {}).get("reason_code") != "out_of_role")
                    for c in latest_children.values())
                if unresolved_child:
                    candidate.verification["decision"] = "revise"
                    verdict.repair_targets = [name for name, child in latest_children.items() if child.get("status") in {"failed", "incomplete", "declined"}]
                    candidate.failure = next((child.get("failure") for child in latest_children.values() if child.get("status") == "failed" and child.get("failure")), {})
                    return self.incomplete(candidate, verdict)
                recovered = [name for name, child in latest_children.items() if child.get("status") == "failed"]
                if recovered:
                    candidate.diagnostics["recovered_specialists"] = recovered
                    record("specialist_evidence_recovered", agents=recovered, review_status="completed")
                candidate.status = "complete"
                candidate.diagnostics['request_costs'] = deepcopy(self.budget.request_costs)
                candidate.diagnostics['review_protocol_repairs_used'] = self.budget.review_protocol_repairs
                return candidate
            evidence = candidate.evidence
            targets = set(verdict.repair_targets)
            pending_corrections = verdict.corrections
            if not targets:
                record('repair_stopped', agent='Original', reason='reviewer_explanation_incomplete',
                       draft_number=attempt + 1, next_draft_started=False)
                break
            if "clarify" in targets and verdict.clarification_question:
                record("repair_stopped", agent="Original", reason="clarification_required",
                       draft_number=attempt + 1, draft_limit=MAX_DRAFTS,
                       pending_corrections=len(pending_corrections), next_draft_started=False)
                break
            if targets == {"Lime"} and (candidate.visualization.get("task_outcome") or {}).get("status") == "declined":
                record("repair_stopped", agent="Original", reason="requested_specialist_declined",
                       draft_number=attempt + 1, draft_limit=MAX_DRAFTS,
                       pending_corrections=len(pending_corrections), next_draft_started=False)
                break
            if attempt + 1 >= MAX_DRAFTS:
                record("repair_stopped", agent="Original", reason="draft_limit_reached",
                       draft_number=attempt + 1, draft_limit=MAX_DRAFTS,
                       pending_corrections=len(pending_corrections), next_draft_started=False)
                break
            record("repair_requested", agent="Original", targets=sorted(targets),
                   supported_findings=sum(f["status"] == "supported" for f in verdict.findings),
                   draft_number=attempt + 1, next_draft_number=attempt + 2, draft_limit=MAX_DRAFTS)
            self.set_delegations({"Cherry", "Vanilla"} if "Original" in targets else targets & {"Cherry", "Vanilla"})
            context = [{"role": "user", "content": "The saved answer is supplied once through available_blocks. "
                 "Assess each correction against the question, saved blocks and evidence. "
                 "Repair justified mandatory issues; explain any unjustified requirement or contradictory repair "
                 "so ZeroSugar can independently withdraw or reassess it. Never change supported meaning merely to comply. "
                 "Preserve supported facts, meaning and sources, "
                 "Explain each removal in removal_reasons. If replacing requested content, supply its replacement "
                 "in this same submission. A repaired citation is not a reason to delete examples, questions or limits. "
                 "while allowing rephrasing, reordering, qualitative synthesis and removal of redundant presentation. "
                 "Reuse existing evidence; the revised candidate will be reviewed again. Answer in English. "
                 "The active pending corrections are supplied in the coordination context; the retrieved evidence "
                 "is supplied once as source evidence. The complete review verdict is not needed for this repair."}]
        # Rejected drafts are preserved in the local artifact, never released as findings.
        candidate.verification = {"decision": "revise", "status": "completed", "reviews": reviews, "drafts_checked": len(candidates), "rejected_drafts": candidates}
        candidate.delegations, candidate.tool_trace = self.child_results, coordinator_trace
        candidate.connections = self.connection_summary
        return self.incomplete(candidate, verdict)

    def close(self):
        for child in self.specialists.values():
            child.close()
        self.specialists = {}
