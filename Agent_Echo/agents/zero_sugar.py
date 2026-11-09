"""ZeroSugar: independent answer review with deterministic evidence checks."""

from dataclasses import asdict, dataclass, field
from copy import deepcopy
import json
import re
import hashlib

from .runtime import AgentResult, RunBudget, function_tool, reject_calls
from .data_access import ScopedData
from .tools import SQLReader
from .execution_log import record, error_summary
from .findings import cited_findings, clarification_question
from .validation import ValidationError, OutputTokenLimit, planning_value, review_messages, object_fields, field_names
from .grounding import FactCatalog, audit_claims
from .policies import with_policies
from .sentiment_rubric import SENTIMENT_RUBRICS, SENTIMENT_LABELS
from .capture import checkpoint, checkpoint_progress, checkpoint_database_identity, trace as full_trace
from .content import fragments
from .review_delivery import safety_gate, reconcile_corrections

DIMENSIONS = ("Accuracy", "Relevance", "Completeness", "Clarity", "Instruction Following", "Usefulness", "Safety / Appropriateness")
MAX_REVIEW_ATTEMPTS = 3
REVIEW_VERSION = "review-v8"




def candidate_id(answer, evidence=None, visualization=None):
    charts = (visualization or {}).get("charts") or []
    content = json.dumps({"answer": answer, "evidence": evidence or [], "charts": charts},
                         sort_keys=True, ensure_ascii=False) if evidence or charts else answer
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def review_snapshot(report):
    """Persist validated review fields, bounded/redacted; never prompts or evidence payloads."""
    if isinstance(report, str):
        return planning_value(report)["value"]
    if isinstance(report, list):
        return [review_snapshot(item) for item in report[:64]]
    if isinstance(report, dict):
        return {key: review_snapshot(value) for key, value in report.items()}
    return report


def equivalent_calls(turn, expected):
    """Only collapse identical parsed assessments, never competing decisions."""
    if len(turn.calls) < 2 or any(c.name != expected for c in turn.calls):
        return turn, []
    try:
        values = [json.dumps(json.loads(c.arguments), sort_keys=True) for c in turn.calls]
    except (ValueError, TypeError):
        return turn, []
    if len(set(values)) != 1 or len({c.call_id for c in turn.calls}) != len(turn.calls):
        return turn, []
    result = deepcopy(turn)
    result.calls = result.calls[:1]
    return result, turn.calls[1:]


@dataclass
class VerificationResult:
    decision: str
    ratings: dict
    issues: list
    uncertainty: str
    deterministic_issues: list
    mode: str
    findings: list = field(default_factory=list)
    repair_targets: list = field(default_factory=list)
    clarification_question: str | None = None
    suggestions: list = field(default_factory=list)
    corrections: list = field(default_factory=list)
    correction_reviews: list = field(default_factory=list)
    completeness_review: dict = field(default_factory=dict)
    version: str = REVIEW_VERSION
    candidate_id: str = ""
    numeric_reviews: list = field(default_factory=list)
    correction_judgments: dict = field(default_factory=dict)
    release_gate: dict | None = None
    explanation_quality: dict | None = None


class ReviewRepairNeeded(RuntimeError):
    """Validated repair instructions, without a completed support verdict."""

    def __init__(self, corrections, identity):
        super().__init__("Verifier did not return a valid structured verdict.")
        self.corrections, self.candidate_id = corrections, identity


CLAIM_LIMIT = 600            # schema bound; instructions ask for about 160 characters
PROBLEM_LIMIT = 300
NOTE_LIMIT = 200
ASSERTION_LIMIT = 12
NEW_ISSUE_LIMIT = 8
MISSING_LIMIT = 8
FEEDBACK_ERRORS = 16
ISSUE_KINDS = ["missing_deliverable", "unsupported_claim", "unusable_presentation"]
OWNERS = ["Original", "Cherry", "Vanilla", "Lime", "clarify"]
PROPOSAL_TYPES = ("action", "team_question", "other")
STATUS_MAP = {"open": "unresolved", "satisfied": "resolved", "withdrawn": "withdrawn"}
COMPLETENESS_INSTRUCTIONS = """You are ZeroSugar checking visible completeness: does the answer,
as the reader sees it, deliver what the question asks? You see the question, the visible
answer and visible_inventory. You do not see source evidence, so do not judge whether
claims are true; the support phase does that.
- Compare each part of the question with the visible answer. Requested item counts matter
  (two questions means two). Wording, order and layout are free.
- The authorized scope (manager, dates, teams) is complete and fixed. Never ask for other
  teams, periods or respondent identities. "All" means all records within the scope.
- Every 'Excerpt: "..."' in the answer was copied by code from the comment it cites, so it is
  literal, never a paraphrase; visible_inventory.literal_examples lists them.
- Tables listed in visible_inventory are visible to the reader: their rows, IDs, counts and
  denominators are present. Do not report them missing or incomplete.
- Team questions and manager actions serve different purposes; one never replaces the
  other. Useful extra content never excuses a real omission.
- Do not add requirements the question does not state: preferred formats, extra examples,
  disclaimers or anonymity declarations.
- Report each real omission or visible contradiction once in missing: request_ref is the
  part of the question that requires it, issue says what is absent and where,
  requested_change says what to add. If specific comments are absent, list them in
  missing_source_ids.
- decision: accept when nothing required is missing (suggestions are optional); revise
  only together with at least one missing item.
OUTPUT: exactly one submit_completeness_review call, no text before it, short fields."""
SUPPORT_INSTRUCTIONS = """You are ZeroSugar, Echo's independent reviewer. You judge the
candidate answer against the question and the supplied evidence. You never rewrite it.

ALREADY VERIFIED BY CODE - do not re-check these and do not object to them:
- Tables, counts and percentages are rendered from source records; arithmetic, coverage and
  label-to-table fidelity are verified. visible_inventory lists what the reader sees.
- Every quoted excerpt was copied mechanically from its cited source, so it is literal. You
  may judge relevance and attribution, never whether it is a paraphrase. A short contiguous
  fragment of a comment satisfies a request for a short literal excerpt; the whole comment is
  not required.
- Classification labels are stored model judgments. In assertions, take each comment's stored
  label as given; if you think a label is wrong, say so only in label_disputes.
- The authorized scope (manager, dates, teams) is complete and fixed. Never ask for other
  teams, managers, periods or respondent identities.
- Objective problems code found are listed in deterministic_issues.
- Findings marked application_text are fixed application statements, not model claims; the
  tool does not ask you to assess them.

WHAT YOU JUDGE
1. assertions: one flat list covering every finding_id offered for it. Split each finding
   into its substantive claims (at most 12 per finding). Each item has finding_id, a short
   claim label (about 160 characters), kind (factual or proposal), the citation_ids of that
   finding that bear on it, assessment (supported, contradicted or insufficient_evidence)
   and problem: null when supported, otherwise what is wrong in one sentence. Judge against
   the full source texts, not only the excerpt. A claim about a whole group needs evidence
   for the whole group. For a proposal judge its factual premise and reasoning; the idea
   itself need not appear in a source.
   label_disputes: for classification table findings, one item per comment whose label is
   not a defensible reading of the full comment under the supplied rubric; [] when every
   label is defensible. A defensible label you would have chosen differently is not a dispute:
   if you write an item anyway, set stored_label_defensible=true and code discards it.
2. obligations (earlier corrections, if any): open = still required and not satisfied by
   the visible answer; satisfied = the visible answer now satisfies it; withdrawn = not
   required by the request, or contradicted by the visible answer or evidence. When
   original_response disputes an item, decide on the merits. A refinement of an open item
   goes in its note, never in a new issue.
3. new_issues: only independent problems not covered by an open obligation, a failed
   assertion or a label dispute. At most 8, one per problem. missing_deliverable needs
   request_ref; if specific comments are absent, list them in missing_source_ids. Check
   visible_inventory and the findings before reporting anything missing. Owner: Original
   for synthesis/presentation, Vanilla for text analysis or labels, Cherry for
   calculations, Lime for charts, clarify only for a necessary clarification question.
4. ratings: every dimension scored 1 (material failure), 2 (minor limitation) or 3
   (satisfactory) with one short note. A material problem must also appear in 1-3; a
   score alone never blocks release.
5. safety_issue_index: index of the new issue that is a genuine safety or privacy concern,
   or null. Using survey evidence for pay, promotion, discipline or termination decisions
   is a safety concern.

Do not require preferred formats, wording, extra examples or content the user did not ask
for. Selected examples need not cover a whole category.
OUTPUT: exactly one submit_support_review call, no text before it. assertions,
label_disputes and new_issues are JSON arrays of objects, never strings containing JSON.
Keep notes short and never copy the answer, tables or sources."""
SENTIMENT_NOTE = ("\nsentiment_labels holds the stored label and reason for each comment; the comment text is in "
    "evidence. Judge labels with the supplied rubric. Percentages describe comments, not employees; labels are "
    "provisional model judgments and human validation is pending.\n"
    "category_claims: for every interpretation finding that describes comments of particular sentiment categories "
    "(for example 'Mixed comments ...' or 'Negative and mixed comments ...'), give its finding_id and every category "
    "it describes. Code then checks each cited comment against its stored label. Leave out interpretations that do "
    "not describe sentiment categories.")
NUMERIC_NOTE = ("\npending_numeric_requests: for each request decide required, not_required or uncertain against the "
    "question, with a short reason. Pending means unqueried, not absent data.")
ACTION_NOTE = ("\nrequire_actionable is true: Echo requires at least one concrete manager action reasoned from the "
    "analysis. proposal_types: classify every proposal finding exactly once. action = something the manager does or "
    "starts (a practice change, a pilot, a process step, a validation step). team_question = a question to put to the "
    "team, including 'ask the team whether ...' or 'Follow-up question: ...'. other = neither. If no proposal is an "
    "action, code records the policy gap, so do not also add it as a new issue. Classify by what the user asked "
    "for: items that deliver questions the user requested (for example 'suggest two follow-up questions') are "
    "team_question, and items that deliver actions or recommendations the user requested are action, whatever "
    "their wording.")
LEGACY_ACTION_NOTE = ("\nrequire_actionable is true: Echo requires at least one concrete manager action reasoned from "
    "the analysis. If none is visible, add one new issue of kind policy_requirement, owner Original, request_ref null. "
    "Questions for the team alone do not satisfy it.")
COMPACT_RETRY = ("\nThe previous attempt was cut off by the output limit. Send the tool call now with no text. "
                 "Every field is plain JSON: arrays of objects, never a string containing JSON, and no padding "
                 "whitespace. Use the shortest possible claim labels, problems and notes; keep every required entry.")
def _string(value, limit, minimum=1):
    return isinstance(value, str) and minimum <= len(value.strip()) and len(value) <= limit
def _array(items, limit):
    return {"type": "array", "maxItems": limit, "items": items}
def _ids(values):
    values = list(dict.fromkeys(values))
    return {"type": "string", "enum": values} if values else {"type": "string"}
def _enum_array(values, limit):
    return _array(_ids(values), limit if values else 0)
def _error(errors, path, code, message, **ids):
    """Fixed messages plus IDs/counts only: never echo model or source text."""
    errors.append({"path": path, "code": code, "message": message, **ids})
def classification_records(block):
    operation = block.get("operation") or {}
    if block.get("kind") == "table" and operation.get("type") == "sentiment_classifications":
        return operation.get("records") or []
    return None
def visible_inventory(blocks, charts=()):
    """What the reader sees, computed from the rendered blocks and charts (objective, not semantic)."""
    tables, examples = [], []
    for block in blocks:
        records = classification_records(block)
        operation = block.get("operation") or {}
        if records is not None:
            tables.append({"finding_id": block["finding_id"], "content": "per_comment_classifications",
                           "row_count": len(records), "source_ids": [r["citation_id"] for r in records]})
        elif block.get("kind") == "table" and isinstance(operation.get("rows"), list):
            tables.append({"finding_id": block["finding_id"], "content": "source_rows",
                           "row_count": len(operation["rows"]), "columns": operation.get("columns", [])})
        elif block.get("kind") == "interpretation" and block.get("quote"):
            examples.append({"finding_id": block["finding_id"], "citation_ids": block.get("citation_ids", [])})
    # Charts are listed here, not beside it: M4 C3 reviews called a rendered chart missing because the inventory omitted it.
    visible_charts = [{k: c[k] for k in ("kind", "title", "x_label", "y_label", "unit", "denominator", "source_id") if k in c}
                      for c in charts if isinstance(c, dict)]
    return {"tables": tables, "literal_examples": examples, "charts": visible_charts,
            "interpretation_count": sum(b.get("kind") == "interpretation" for b in blocks),
            "proposal_count": sum(b.get("kind") == "proposal" for b in blocks)}
def rendered_source_ids(blocks):
    return {r["citation_id"] for block in blocks for r in (classification_records(block) or [])}


class ZeroSugarAgent:
    name = "ZeroSugar"

    def __init__(self, scope, model, mode="live", budget=None, sql_reader=None, document_lookup=None, database=None, sentiment_reports=None, sentiment_documents=None, authorized_teams=None):
        self.scope, self.model, self.mode = scope, model, mode
        self.budget = budget or RunBudget()
        self.sql_reader, self.document_lookup = sql_reader, document_lookup
        self.database, self.owned_reader = database, None
        self.authorized_teams = list(authorized_teams) if authorized_teams is not None else None
        self.diagnostics = {"rejected_attempts": [], "review_phases": []}
        self.sentiment_reports = sentiment_reports or {}
        self.sentiment_documents = sentiment_documents

    def phase_model(self, phase):
        """Experiments may separate model ownership without copying review gates."""
        return self.model





    def phase_attempts(self, budget, phase):
        """Three ordinary attempts plus at most one shared protocol exception."""
        for attempt in range(MAX_REVIEW_ATTEMPTS):
            phase['protocol_retry_eligible'] = False
            yield attempt
        if phase.get('protocol_retry_eligible') and budget.reserve_review_protocol_repair():
            phase['extra_protocol_attempt'] = True
            record('review_protocol_exception', phase=phase['phase'], candidate_id=phase['candidate_id'],
                   shared_exception_used=1, remaining=budget.remaining())
            yield MAX_REVIEW_ATTEMPTS





    def audit(self, answer, evidence, visualization=None):
        issues = []
        known = {item.get("citation_id") for item in evidence}
        cited = set(re.findall(r"\[([A-Za-z0-9_:-]+)\]", answer))
        if cited - known:
            issues.append("Answer contains unknown citation IDs.")
        if evidence and not cited:
            issues.append("Answer has no evidence citations.")
        for item in evidence:
            if not item.get("citation_id"):
                issues.append("Evidence record lacks a citation ID.")
            if str(item.get("citation_id", "")).startswith("SQL"):
                if not {"sql", "rows", "truncated", "scope"}.issubset(item):
                    issues.append("SQL evidence is missing its query, rows or scope metadata.")
                if self.sql_reader is None:
                    issues.append("SQL evidence has no trusted replay source.")
            if "text" in item and item.get("kind") != "survey_response" and self.document_lookup is None:
                issues.append("Text evidence has no trusted source lookup.")
            if "scope" in item and item["scope"] != self.scope.__dict__:
                issues.append("Evidence scope differs from the authorized caller scope.")
            if item.get("kind") == "survey_sentiment" or str(item.get("citation_id", "")).startswith("SENTIMENT"):
                try:
                    self.sentiment_source(item)
                except (KeyError, TypeError, ValueError, AttributeError):
                    issues.append("Sentiment evidence failed source, coverage or aggregation verification.")
            if "date" in item and not self.scope.start_date <= item["date"] <= self.scope.end_date:
                issues.append("Evidence date is outside the authorized period.")
            if item.get("anonymous") and any(key in item for key in ("Employee_ID", "Anonymous_Response_Token", "Employee_Name")):
                issues.append("Anonymous survey evidence contains identity fields.")
            if "sql" in item and self.sql_reader:
                try:
                    replay = self.sql_reader.execute(item["sql"], item.get("parameters", []))
                    if replay["rows"] != item["rows"] or replay["truncated"] != item["truncated"]:
                        issues.append("SQL evidence does not match a read-only query replay.")
                    if item.get("metric_id"):
                        from .metrics import MetricCatalog
                        metric = MetricCatalog(self.sql_reader, actor="ZeroSugar").run(item["metric_id"], **item["metric_arguments"])
                        if any(metric.get(key) != item.get(key) for key in
                               ("rows", "sql", "parameters", "metric_version", "metric_definition")):
                            issues.append("Metric evidence differs from its validated definition.")
                except (ValueError, KeyError, TypeError):
                    issues.append("SQL evidence could not be replayed.")
            if item.get("kind") == "survey_response":
                original = next((d for d in (self.sentiment_documents or []) if d["citation_id"] == item["citation_id"]), None)
                if original is None or item.get("scope") != self.scope.__dict__ or any(item.get(key) != original.get(key) for key in
                    ("source", "record_id", "team", "date", "dimension", "anonymous")) or item.get("text") != original["response_text"]:
                    issues.append("Survey response evidence differs from its trusted anonymous comment.")
            elif "text" in item and self.document_lookup is not None:
                original = self.document_lookup.get(item["citation_id"])
                if original is None or any(item.get(key) != original.get(key) for key in ("source", "record_id", "team", "date", "anonymous")) or item["text"] != original["text"][:1600]:
                    issues.append("Text evidence differs from its scoped source record.")
        if visualization is not None:
            from .lime import validate_visuals
            try:
                validate_visuals({key: visualization[key] for key in ("charts", "reason")}, evidence, self.scope)
            except (ValueError, TypeError, KeyError) as error:
                issues.append("Invalid visualization: " + str(error))
        return list(dict.fromkeys(issues))

    def sentiment_source(self, evidence):
        """Replay the trusted report before using its labels or response texts."""
        from .vanilla import sentiment_summary
        report = self.sentiment_reports[evidence["citation_id"]]
        if self.sentiment_documents is None or report["scope"] != self.scope.__dict__ or report["mode"] != self.mode:
            raise ValueError("No matching trusted sentiment scope/mode/source.")
        eligible = [doc for doc in self.sentiment_documents if report["dimension"] is None or
                    doc["dimension"].casefold() == report["dimension"].casefold()]
        hashes = {doc["citation_id"]: hashlib.sha256(doc["response_text"].encode("utf-8")).hexdigest() for doc in eligible}
        if report.get("rubric_version", "survey-sentiment-v1") not in SENTIMENT_RUBRICS:
            raise ValueError("Unknown sentiment rubric version.")
        if report["source_hashes"] != hashes or sentiment_summary(report, self.sentiment_documents) != evidence:
            raise ValueError("Sentiment evidence differs from source-linked labels/aggregation.")
        return report, eligible

    def sentiment_review_context(self, evidence):
        """Supply all labels/full texts for released groups, preserving suppression."""
        packets = []
        for item in evidence:
            if item.get("kind") != "survey_sentiment":
                continue
            try:
                report, documents = self.sentiment_source(item)
                groups = {(row["Team"], row["Survey_Date"], row["Dimension"]) for row in item["rows"]}
                lookup = {doc["citation_id"]: doc for doc in documents
                          if (doc["team"], doc["date"], doc["dimension"]) in groups}
                version = report.get("rubric_version", "survey-sentiment-v1")
                comments = [{**label, "response_text": lookup[label["citation_id"]]["response_text"]}
                            for label in report["labels"] if label["citation_id"] in lookup]
                packets.append({"citation_id": item["citation_id"], "rubric_version": version,
                    "rubric": SENTIMENT_RUBRICS[version], "eligible_comments": len(documents),
                    "included_comments": len(comments), "suppressed_comments": len(documents) - len(comments),
                    "comments": comments})
            except (KeyError, TypeError, ValueError, AttributeError):
                # audit() retains the blocking integrity issue; never send untrusted text.
                continue
        return packets

    @staticmethod
    def validate(report):
        basic = {"decision", "ratings", "issues", "uncertainty"}
        extended = basic | {"finding_reviews", "repair_targets", "clarification_question"}
        optional = {"suggestions", "corrections", "correction_reviews"}
        if not isinstance(report, dict) or set(report) - optional not in (basic, extended):
            required = extended if isinstance(report, dict) and set(report) & (extended - basic) else basic
            object_fields(report, {"properties": {key: {} for key in required | optional}, "required": sorted(required),
                                   "additionalProperties": False}, "review_fields", "review",
                          "Review fields differ from the required legacy review schema.")
        if not isinstance(report["decision"], str) or report["decision"] not in {"accept", "revise"} or not isinstance(report["uncertainty"], str):
            raise ValidationError("review_decision", "decision/uncertainty", "Invalid review decision or uncertainty.")
        if not isinstance(report["ratings"], dict) or set(report["ratings"]) != set(DIMENSIONS):
            object_fields(report["ratings"], {"properties": {key: {} for key in DIMENSIONS}, "required": list(DIMENSIONS),
                                             "additionalProperties": False}, "rating_dimensions", "ratings",
                          "All seven rubric dimensions are required.")
        for name, rating in report["ratings"].items():
            if not isinstance(rating, dict) or set(rating) != {"score", "rationale"}:
                object_fields(rating, {"properties": {"score": {}, "rationale": {}}, "required": ["score", "rationale"],
                                       "additionalProperties": False}, "rating_fields", "ratings." + name,
                              "Each rating requires a score and rationale.")
            if type(rating["score"]) is not int or not 1 <= rating["score"] <= 3 or not isinstance(rating["rationale"], str):
                raise ValidationError("rating_value", "ratings." + name, "Scores must be integers from 1 to 3, with a rationale.")
        review_messages(report["issues"], "issues", "review_issues", max_items=64)
        review_messages(report.get("suggestions", []), "suggestions", "review_suggestions")
        return report













    def review(self, question, answer, evidence, visualization=None, numeric_coverage=None, claims=None, grounding=None, task_outcomes=None, require_sentiment=False, request_deliverables=None, previous_corrections=None, require_actionable=False, resume_completeness=None):
        arguments = dict(visualization=visualization, numeric_coverage=numeric_coverage,
            claims=claims, grounding=grounding, task_outcomes=task_outcomes,
            require_sentiment=require_sentiment, previous_corrections=previous_corrections,
            require_actionable=require_actionable)
        database = self.database
        if database is None:
            from pathlib import Path
            candidate = Path(__file__).resolve().parents[1] / 'data' / 'echo.db'
            database = candidate if candidate.exists() else None
        self.review_checkpoint = checkpoint('review', self.name, self.scope.__dict__, {
            'question': question, 'answer': answer, 'evidence': evidence, 'arguments': arguments,
            'mode': self.mode, 'profile': getattr(self.model, 'profile', None), 'sentiment_reports': self.sentiment_reports,
            'sentiment_documents': self.sentiment_documents, 'document_lookup': self.document_lookup,
            'authorized_teams': self.authorized_teams, 'database_hash': checkpoint_database_identity(database)})
        if self.review_checkpoint:
            self.diagnostics['checkpoint'] = self.review_checkpoint
        try:
            result = self._review(question, answer, evidence, **arguments, resume_completeness=resume_completeness)
            checkpoint_progress(self.review_checkpoint, status='completed', decision=result.decision, result=asdict(result))
            return result
        except BaseException as error:
            checkpoint_progress(self.review_checkpoint, status='failed', failure=error_summary(error),
                retained_findings=getattr(self, '_finding_review_cache', {}),
                finding_cache_binding=getattr(self, '_finding_cache_identity', None))
            raise


    def run(self, artifact):
        if artifact["scope"] != self.scope.__dict__:
            raise ValueError("Input artifact scope must match the requested verification scope.")
        if self.database:
            backend = ScopedData(self.database, self.scope)
            try:
                self.owned_reader = SQLReader(backend.structured_tables(), self.scope)
                self.sql_reader = self.owned_reader
                self.document_lookup = {doc["citation_id"]: doc for doc in backend.text_documents()}
                self.sentiment_documents = backend.sentiment_documents()
                self.sentiment_reports = artifact.get("sentiment", {})
                self.authorized_teams = list(backend.teams)
            finally:
                backend.close()
        review = self.review(artifact["question"], artifact["answer"], artifact["evidence"], artifact.get("visualization") or None,
                             claims=artifact.get("claims") or None, grounding=artifact.get("grounding") or None,
                             task_outcomes=[{"agent": child["agent"], "status": child["status"],
                                             "task_outcome": child.get("task_outcome", {})}
                                             for child in artifact.get("delegations", [])],
                             require_sentiment=artifact.get("diagnostics", {}).get("requires_sentiment", False))
        return AgentResult(self.name, artifact["question"], "Review decision: " + review.decision,
                           self.scope.__dict__, artifact["evidence"], mode=self.mode, verification=asdict(review))

    def close(self):
        if self.owned_reader:
            self.owned_reader.close()
            self.owned_reader = None

    original_responses = None


    # ---------------------------------------------------------------- delivery loop
    def deliver(self, phase_name, instructions, payload, build_tool, validate, budget, candidate):
        """One tool call per attempt; joint feedback; retries carry only the latest attempt."""
        phase = {"phase": phase_name, "status": "started", "model_attempts": 0, "candidate_id": candidate}
        self.diagnostics["review_phases"].append(phase)
        record("review_phase_started", agent=self.name, phase=phase_name)
        base = [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]
        history, compact = list(base), False
        for attempt in self.phase_attempts(budget, phase):
            try:
                budget.consume("model")
                phase["model_attempts"] = attempt + 1
                tool = build_tool()
                turn = budget.respond(self.phase_model(phase_name), with_policies(instructions) +
                                      (COMPACT_RETRY if compact else ""), history, [tool], True)
            except OutputTokenLimit:
                compact = True
                phase["truncated_attempts"] = phase.get("truncated_attempts", 0) + 1
                record("review_truncation_retry", agent=self.name, phase=phase_name, model_turn=attempt + 1)
                history = list(base)
                continue
            except (RuntimeError, ValueError):
                phase["status"] = "failed"
                record("review_phase_finished", agent=self.name, **phase)
                raise
            turn, duplicates = equivalent_calls(turn, tool["name"])
            if duplicates:
                record("equivalent_review_calls_normalized", phase=phase_name, duplicate_count=len(duplicates))
            errors, result = [], None
            if len(turn.calls) != 1 or turn.calls[0].name != tool["name"]:
                phase["protocol_retry_eligible"] = True
                _error(errors, "tool_call", "tool_call_count", f"Return exactly one {tool['name']} call and no text.")
            else:
                budget.consume("tool")
                try:
                    value = json.loads(turn.calls[0].arguments)
                except ValueError:
                    _error(errors, "arguments", "invalid_json", "Send valid JSON arguments.")
                else:
                    result, errors = validate(value)
            if not errors:
                phase.update(status="completed")
                self._resolve_rejections(phase_name, attempt + 1)
                record("review_phase_finished", agent=self.name, **phase)
                return result
            feedback = self._reject(phase_name, tool, attempt + 1, errors, budget)
            history = list(base) + list(turn.output_items)
            reject_calls(history, turn, json.dumps(feedback))
            full_trace("review_rejection", agent=self.name, phase=phase_name,
                       arguments=[c.arguments for c in turn.calls], feedback=feedback)
        phase["status"] = "failed"
        record("review_phase_finished", agent=self.name, **phase)
        return None

    def _reject(self, phase_name, tool, turn, errors, budget):
        previous = [e for e in self.diagnostics["rejected_attempts"] if e.get("phase") == phase_name
                    and e.get("candidate_id") == self.diagnostics.get("candidate_id")]
        codes = sorted({e["code"] for e in errors})
        condition = hashlib.sha256(json.dumps([e["path"] + ":" + e["code"] for e in errors]).encode()).hexdigest()[:16]
        repeated = 1 + sum(item.get("condition_id") == condition for item in previous)
        entry = {"agent": self.name, "tool": tool["name"], "phase": phase_name, "model_turn": turn,
                 "candidate_id": self.diagnostics.get("candidate_id"), "schema_version": REVIEW_VERSION,
                 "status": "rejected_unverified", "resolution": "unresolved",
                 "validation_code": errors[0]["code"], "field": errors[0]["path"],
                 "error_count": len(errors), "codes": codes, "condition_id": condition,
                 "same_condition_attempts": repeated}
        self.diagnostics["rejected_attempts"].append(entry)
        record("structured_response_repair", **entry)
        return {"status": "rejected", "error_count": len(errors), "errors": errors[:FEEDBACK_ERRORS],
                "retained_finding_ids": sorted(self._finding_cache),
                "same_condition_attempts": repeated,
                "instruction": ("Send one corrected call. Fix every listed error in that call and keep all other "
                                "content unchanged. Retained findings are already accepted; do not resend them."
                                + (" The same errors recurred: change the listed fields." if repeated > 1 else ""))}

    def _resolve_rejections(self, phase_name, accepted_turn):
        for entry in self.diagnostics["rejected_attempts"]:
            if entry.get("phase") == phase_name and entry.get("resolution") == "unresolved":
                entry.update(resolution="accepted_review_submission", accepted_model_turn=accepted_turn)

    # ---------------------------------------------------------------- completeness
    def completeness_tool(self, question, record_ids):
        missing = {"request_ref": {"type": "string", "enum": list(fragments(question, "original_question"))},
                   "issue": {"type": "string", "minLength": 1, "maxLength": PROBLEM_LIMIT},
                   "requested_change": {"type": "string", "minLength": 1, "maxLength": PROBLEM_LIMIT}}
        if record_ids:
            missing["missing_source_ids"] = _enum_array(record_ids, 64)
        return function_tool("submit_completeness_review", "Review visible-answer completeness without evidence.", {
            "decision": {"type": "string", "enum": ["accept", "revise"]},
            "score": {"type": "integer", "minimum": 1, "maximum": 3},
            "rationale": {"type": "string", "minLength": 1, "maxLength": 600},
            "missing": _array({"type": "object", "properties": missing, "required": list(missing),
                               "additionalProperties": False}, MISSING_LIMIT),
            "suggestions": _array({"type": "string", "minLength": 1, "maxLength": NOTE_LIMIT}, 4)})

    def validate_completeness(self, value, question, answer, rendered, record_ids):
        errors = []
        expected = {"decision", "score", "rationale", "missing", "suggestions"}
        if not isinstance(value, dict) or set(value) != expected:
            _error(errors, "completeness_review", "fields", "Use exactly the declared fields.",
                   expected_fields=sorted(expected),
                   missing_fields=sorted(expected - set(value)) if isinstance(value, dict) else sorted(expected),
                   unexpected_field_count=len(set(value) - expected) if isinstance(value, dict) else 0)
            return None, errors
        if value["decision"] not in ("accept", "revise"):
            _error(errors, "decision", "decision", "Choose accept or revise.")
        if type(value["score"]) is not int or not 1 <= value["score"] <= 3:
            _error(errors, "score", "score", "Use an integer score from 1 to 3.")
        if not _string(value["rationale"], 600):
            _error(errors, "rationale", "text", "Give a nonempty rationale of at most 600 characters.")
        if not isinstance(value["suggestions"], list) or len(value["suggestions"]) > 4 or \
                any(not _string(item, NOTE_LIMIT) for item in value["suggestions"]):
            _error(errors, "suggestions", "text", "Use at most 4 nonempty suggestions of 200 characters.")
        excerpts = fragments(question, "original_question")
        kept = []
        items = value["missing"] if isinstance(value["missing"], list) else None
        if items is None or len(items) > MISSING_LIMIT:
            _error(errors, "missing", "count", "Use a list of at most 8 missing items.")
            items = []
        for index, item in enumerate(items):
            path = f"missing[{index}]"
            fields = {"request_ref", "issue", "requested_change"} | ({"missing_source_ids"} if record_ids else set())
            if not isinstance(item, dict) or set(item) - {"missing_source_ids"} != fields - {"missing_source_ids"}:
                _error(errors, path, "fields", "Use request_ref, issue and requested_change" +
                       (" and missing_source_ids." if record_ids else "."))
                continue
            if item["request_ref"] not in excerpts:
                _error(errors, path + ".request_ref", "request_ref", "Select request_ref from question_excerpts.")
            for key in ("issue", "requested_change"):
                if not _string(item[key], PROBLEM_LIMIT):
                    _error(errors, f"{path}.{key}", "text", "Give a nonempty sentence of at most 300 characters.")
            named = self._named_ids(item.get("missing_source_ids", []), record_ids, errors, path)
            if named is None:
                continue
            kept.append((index, item, named))
        if errors:
            return None, errors
        corrections = []
        for index, item, named in kept:
            issue = item["issue"]
            corrections.append({"correction_id": f"C_{candidate_id(answer + issue)}_visible_{len(corrections) + 1}",
                                "issue": issue, "requested_change": item["requested_change"],
                                "request_excerpt": excerpts[item["request_ref"]]["text"],
                                "kind": "missing_deliverable", "owner": "Original", "citation_ids": [],
                                "detected_phases": ["completeness"], "missing_source_ids": named,
                                **self._code_note("completeness", index, named, rendered)})
        decision = "revise" if corrections else "accept"
        if value["decision"] == "revise" and not corrections:
            # A revision without a missing item cannot be repaired.
            self.diagnostics.setdefault("normalizations", []).append(
                {"phase": "completeness", "action": "revise_without_open_item_accepted"})
        suggestions = list(value["suggestions"]) + ([value["rationale"]] if value["decision"] == "revise" and not corrections else [])
        return {"decision": decision, "score": value["score"] if corrections or value["score"] > 1 else 2,
                "rationale": value["rationale"], "corrections": corrections,
                "issues": [c["issue"] for c in corrections], "suggestions": suggestions[:6]}, []

    def _named_ids(self, ids, record_ids, errors, path):
        if not isinstance(ids, list) or any(key not in record_ids for key in ids):
            _error(errors, path + ".missing_source_ids", "source_ids", "Use comment IDs from the eligible population only.")
            return None
        return list(dict.fromkeys(ids))

    def _code_note(self, phase, index, named, rendered):
        """An objective fact attached to the objection, never a reason to drop it.

        A named comment can be in the rendered table and still be missing as requested
        content (for example as a quoted example), so only the reviewer can judge it.
        """
        present = [key for key in named if key in rendered]
        if not present:
            return {}
        entry = {"phase": phase, "item_index": index, "named_count": len(named), "rendered_count": len(present),
                 "action": "absence_annotated"}
        self.diagnostics.setdefault("absence_annotations", []).append(entry)
        record("review_absence_annotated", agent=self.name, **entry)
        return {"code_note": "These named comments appear in the code-rendered per-comment table: " + ", ".join(present)
                + ". This does not show whether the requested content (for example a quoted example) is visible."}

    def _normalized(self, code, **ids):
        """Mechanical delivery normalization: a field with one valid value, or a no-op item. Never a judgment."""
        entry = {"code": code, **ids}
        self.diagnostics.setdefault("delivery_normalizations", []).append(entry)
        record("review_delivery_normalized", agent=self.name, **entry)

    # ---------------------------------------------------------------- support
    @staticmethod
    def asks_actions(blocks, require_actionable):
        """proposal_types needs typed findings; an untyped (legacy) answer uses a policy new issue instead."""
        return require_actionable and bool(blocks) and all("kind" in b for b in blocks)

    @staticmethod
    def application_text(block):
        """The renderer's fixed boundary statement is application text, not a model claim."""
        return block.get("kind") == "limitation" and block.get("validation") == "application_boundary"

    def pending_findings(self, blocks):
        """Findings still to review, split by how they are reviewed."""
        pending = [b for b in blocks if b["finding_id"] not in self._finding_cache]
        return ([b for b in pending if classification_records(b) is None],
                [b for b in pending if classification_records(b) is not None])

    def support_tool(self, question, blocks, evidence, obligations, numeric, record_ids, require_actionable):
        # Flat lists, not an object keyed by finding ID: a keyed object was sent back as an
        # escaped JSON string in every truncated v8 attempt of the 2026-11-03 smoke run.
        plain, tables = self.pending_findings(blocks)
        assertion = {"finding_id": _ids([b["finding_id"] for b in plain]),
                     "claim": {"type": "string", "minLength": 1, "maxLength": CLAIM_LIMIT},
                     "kind": {"type": "string", "enum": ["factual", "proposal"]},
                     "citation_ids": _enum_array(sorted({k for b in plain for k in b["citation_ids"]}), 16),
                     "assessment": {"type": "string", "enum": ["supported", "contradicted", "insufficient_evidence"]},
                     "problem": {"type": ["string", "null"], "maxLength": PROBLEM_LIMIT}}
        dispute = {"finding_id": _ids([b["finding_id"] for b in tables]),
                   "source_id": _ids([r["citation_id"] for b in tables for r in classification_records(b)]),
                   "proposed_label": {"type": "string", "enum": list(SENTIMENT_LABELS)},
                   "stored_label_defensible": {"type": "boolean"},
                   "problem": {"type": "string", "minLength": 1, "maxLength": PROBLEM_LIMIT}}
        kinds = ISSUE_KINDS + (["policy_requirement"] if require_actionable else [])
        issue = {"kind": {"type": "string", "enum": kinds}, "owner": {"type": "string", "enum": OWNERS},
                 "issue": {"type": "string", "minLength": 1, "maxLength": PROBLEM_LIMIT},
                 "requested_change": {"type": "string", "minLength": 1, "maxLength": PROBLEM_LIMIT},
                 "request_ref": {"type": ["string", "null"], "enum": [*fragments(question, "original_question"), None]},
                 "finding_ids": _enum_array([b["finding_id"] for b in blocks], 32),
                 "citation_ids": _enum_array([e["citation_id"] for e in evidence], 16)}
        if record_ids:
            issue["missing_source_ids"] = _enum_array(record_ids, 64)
        note = {"type": "string", "minLength": 1, "maxLength": NOTE_LIMIT}
        properties = {
            "assertions": {"type": "array", "minItems": 1 if plain else 0,
                           "maxItems": min(128, ASSERTION_LIMIT * len(plain)),
                           "items": {"type": "object", "properties": assertion, "required": list(assertion),
                                     "additionalProperties": False}},
            "label_disputes": _array({"type": "object", "properties": dispute, "required": list(dispute),
                                      "additionalProperties": False},
                                     sum(len(classification_records(b)) for b in tables)),
            "new_issues": _array({"type": "object", "properties": issue, "required": list(issue),
                                  "additionalProperties": False}, NEW_ISSUE_LIMIT),
            "ratings": {"type": "object", "properties": {d: {"type": "object", "properties": {
                "score": {"type": "integer", "minimum": 1, "maximum": 3}, "note": note},
                "required": ["score", "note"], "additionalProperties": False} for d in DIMENSIONS},
                "required": list(DIMENSIONS), "additionalProperties": False},
            "safety_issue_index": {"type": ["integer", "null"], "minimum": 0, "maximum": NEW_ISSUE_LIMIT - 1},
            "clarification_question": {"type": ["string", "null"], "maxLength": 500}}
        # Explicit judgments whose consequence code derives: the action policy and category prose.
        if self.asks_actions(blocks, require_actionable):
            proposals = [b["finding_id"] for b in blocks if b.get("kind") == "proposal"]
            typed = {"finding_id": _ids(proposals), "type": {"type": "string", "enum": list(PROPOSAL_TYPES)}}
            properties["proposal_types"] = {"type": "array", "minItems": len(proposals), "maxItems": len(proposals),
                "items": {"type": "object", "properties": typed, "required": list(typed), "additionalProperties": False}}
        if record_ids:
            interpretations = [b["finding_id"] for b in blocks if b.get("kind") == "interpretation"]
            category = {"finding_id": _ids(interpretations), "labels": {"type": "array", "minItems": 1,
                        "maxItems": len(SENTIMENT_LABELS), "items": {"type": "string", "enum": list(SENTIMENT_LABELS)}}}
            properties["category_claims"] = _array({"type": "object", "properties": category, "required": list(category),
                                                    "additionalProperties": False}, len(interpretations))
        if obligations:
            properties["obligations"] = {"type": "object", "properties": {item["correction_id"]: {
                "type": "object", "properties": {"status": {"type": "string", "enum": list(STATUS_MAP)}, "note": note},
                "required": ["status", "note"], "additionalProperties": False} for item in obligations},
                "required": [item["correction_id"] for item in obligations], "additionalProperties": False}
        if numeric:
            properties["numeric_reviews"] = {"type": "object", "properties": {item["request_id"]: {
                "type": "object", "properties": {"decision": {"type": "string", "enum": ["required", "not_required", "uncertain"]},
                                                 "reason": note}, "required": ["decision", "reason"],
                "additionalProperties": False} for item in numeric},
                "required": [item["request_id"] for item in numeric], "additionalProperties": False}
        return function_tool("submit_support_review", "Submit the evidence review of the candidate answer.", properties)

    def validate_support(self, value, ctx):
        """Validate everything, report every error; keep each valid finding for retries."""
        errors = []
        blocks, evidence = ctx["blocks"], ctx["evidence"]
        expected = {"assertions", "label_disputes", "new_issues", "ratings", "safety_issue_index", "clarification_question"} | \
            ({"obligations"} if ctx["obligations"] else set()) | ({"numeric_reviews"} if ctx["numeric"] else set()) | \
            ({"proposal_types"} if ctx["ask_actions"] else set()) | ({"category_claims"} if ctx["record_ids"] else set())
        if not isinstance(value, dict):
            _error(errors, "review", "fields", "Send a JSON object with the declared fields.", expected_fields=sorted(expected))
            return None, errors
        if set(value) != expected:
            _error(errors, "review", "fields", "Use exactly the declared fields.", expected_fields=sorted(expected),
                   missing_fields=sorted(expected - set(value)),
                   unexpected_fields=field_names(set(value) - expected, expected))
        lookup = {b["finding_id"]: b for b in blocks}
        plain, tables = self.pending_findings(blocks)
        grouped = {b["finding_id"]: [] for b in plain + tables}
        for name in ("assertions", "label_disputes"):
            items = value.get(name, [])
            if not isinstance(items, list):
                _error(errors, name, "type", f"Send {name} as a JSON array of objects, never as a string.")
                continue
            expected_ids = {b["finding_id"] for b in (plain if name == "assertions" else tables)}
            for index, item in enumerate(items):
                key = item.get("finding_id") if isinstance(item, dict) else None
                if name == "assertions" and key not in expected_ids and key in lookup and item.get("assessment") == "supported":
                    # Already reviewed, or a table judged through label_disputes: a supported claim changes nothing.
                    # Luna 74's last support attempt re-sent accepted findings and the review failed.
                    self._normalized("assertion_outside_pending_dropped", finding_id=key, item_index=index)
                    continue
                if key not in expected_ids:
                    _error(errors, f"{name}[{index}].finding_id", "finding_identity",
                           f"Use a finding_id listed for {name} in the schema.", allowed_finding_ids=sorted(expected_ids))
                    continue
                grouped[key].append({k: v for k, v in item.items() if k != "finding_id"})
        known = {e.get("citation_id") for e in evidence}
        for block in plain + tables:
            key = block["finding_id"]
            if block in plain and not grouped[key]:
                _error(errors, "assertions", "finding_missing", "Add at least one assertion for this finding.", finding_id=key)
                continue
            entry = {"label_disputes": grouped[key]} if block in tables else {"assertions": grouped[key]}
            checked = self._check_finding(entry, block, known, bool(evidence), errors, f"finding {key}")
            if checked is not None:
                self._finding_cache[key] = checked
        obligations = {}
        if ctx["obligations"]:
            given = value.get("obligations") if isinstance(value.get("obligations"), dict) else {}
            for item in ctx["obligations"]:
                cid, entry = item["correction_id"], given.get(item["correction_id"])
                if not isinstance(entry, dict) or set(entry) != {"status", "note"} or entry.get("status") not in STATUS_MAP \
                        or not _string(entry.get("note"), NOTE_LIMIT):
                    _error(errors, "obligations." + cid, "obligation", "Give status open, satisfied or withdrawn and a short note.",
                           correction_id=cid)
                else:
                    obligations[cid] = entry
            if set(given) - {item["correction_id"] for item in ctx["obligations"]}:
                _error(errors, "obligations", "obligation_identity", "Use only the supplied obligation IDs.")
        issues = []
        new = value.get("new_issues")
        if not isinstance(new, list) or len(new) > NEW_ISSUE_LIMIT:
            _error(errors, "new_issues", "count", "Use a list of at most 8 new issues.")
            new = []
        excerpts = fragments(ctx["question"], "original_question")
        # Same rule as safety_gate: the link counts only with a low safety score (Luna 72 linked a label issue at 3).
        rating = value.get("ratings", {}).get("Safety / Appropriateness") if isinstance(value.get("ratings"), dict) else None
        flagged = value.get("safety_issue_index") if isinstance(rating, dict) and rating.get("score") in (1, 2) else None
        for index, item in enumerate(new):
            issue = self._check_issue(item, index, ctx, excerpts, known, lookup, value.get("clarification_question"), errors)
            if issue is not None and index != flagged and self._label_objection(issue, lookup):
                # Labels are disputed only in label_disputes, where a defensible one is dropped. Luna 67 raised
                # a label it called defensible here instead; no role can relabel it, and the repair truncated.
                self._normalized("label_issue_outside_disputes_dropped", item_index=index)
            elif issue is not None:
                issues.append(issue)
        actions = None
        if ctx["ask_actions"]:
            types = value.get("proposal_types")
            proposals = [b["finding_id"] for b in blocks if b.get("kind") == "proposal"]
            given = {item.get("finding_id"): item.get("type") for item in types if isinstance(item, dict)} \
                if isinstance(types, list) else {}
            missing = [key for key in proposals if given.get(key) not in PROPOSAL_TYPES]
            if not isinstance(types, list) or missing or len(types) != len(proposals) or set(given) - set(proposals):
                _error(errors, "proposal_types", "proposal_types",
                       "Classify every proposal finding exactly once as action, team_question or other.",
                       allowed_finding_ids=proposals, missing_finding_ids=missing)
            else:
                actions = [key for key in proposals if given[key] == "action"]
        categories = []
        if ctx["record_ids"]:
            claims = value.get("category_claims")
            interpretations = {b["finding_id"] for b in blocks if b.get("kind") == "interpretation"}
            if not isinstance(claims, list):
                _error(errors, "category_claims", "type", "Send category_claims as a JSON array of objects.")
                claims = []
            seen = set()
            for index, item in enumerate(claims):
                if not isinstance(item, dict) or set(item) != {"finding_id", "labels"} or item["finding_id"] not in interpretations \
                        or item["finding_id"] in seen or not isinstance(item["labels"], list) or not item["labels"] \
                        or any(label not in SENTIMENT_LABELS for label in item["labels"]):
                    _error(errors, f"category_claims[{index}]", "category_claim",
                           "Name each interpretation finding at most once with the declared labels it describes.",
                           allowed_finding_ids=sorted(interpretations))
                    continue
                seen.add(item["finding_id"])
                categories.append(item)
        ratings = value.get("ratings") if isinstance(value.get("ratings"), dict) else {}
        for d in DIMENSIONS:
            rating = ratings.get(d)
            if not isinstance(rating, dict) or set(rating) != {"score", "note"} or type(rating.get("score")) is not int \
                    or not 1 <= rating["score"] <= 3 or not _string(rating.get("note"), NOTE_LIMIT):
                _error(errors, "ratings." + d, "rating", "Give an integer score 1-3 and a short note.")
        safety = value.get("safety_issue_index")
        if safety is not None and (type(safety) is not int or not 0 <= safety < len(new)):
            _error(errors, "safety_issue_index", "safety_index", "Use null or the index of one of your new_issues.",
                   actual_count=len(new))
        try:
            question = clarification_question(value.get("clarification_question"))
        except ValueError:
            _error(errors, "clarification_question", "text", "Use null or one question of at most 500 characters.")
            question = None
        numeric = []
        if ctx["numeric"]:
            given = value.get("numeric_reviews") if isinstance(value.get("numeric_reviews"), dict) else {}
            for item in ctx["numeric"]:
                entry = given.get(item["request_id"])
                if not isinstance(entry, dict) or entry.get("decision") not in ("required", "not_required", "uncertain") \
                        or not _string(entry.get("reason"), NOTE_LIMIT):
                    _error(errors, "numeric_reviews." + item["request_id"], "numeric_review", "Decide required, not_required or uncertain with a reason.")
                else:
                    numeric.append({"request_id": item["request_id"], "decision": entry["decision"], "reason": entry["reason"]})
        if errors:
            return None, errors
        return {"obligations": obligations, "issues": issues, "ratings": ratings, "safety": safety,
                "clarification_question": question, "numeric_reviews": numeric,
                "manager_actions": actions, "category_claims": categories}, []

    def _check_finding(self, entry, block, known, has_evidence, errors, path):
        start = len(errors)
        records = classification_records(block)
        if records is not None:
            disputes = entry.get("label_disputes") if isinstance(entry, dict) and set(entry) == {"label_disputes"} else None
            if not isinstance(disputes, list):
                _error(errors, path, "fields", "Send label_disputes ([] when every label is defensible).", finding_id=block["finding_id"])
                return None
            labels = {r["citation_id"]: r["label"] for r in records}
            seen, kept = set(), []
            for index, item in enumerate(disputes):
                where = f"{path}.label_disputes[{index}]"
                if not isinstance(item, dict) or set(item) != {"source_id", "proposed_label", "stored_label_defensible", "problem"}:
                    _error(errors, where, "fields", "Use source_id, proposed_label, stored_label_defensible and problem.")
                    continue
                if item["stored_label_defensible"] is True and item["source_id"] in labels and item["source_id"] not in seen:
                    # The reviewer itself judges the stored label defensible: by definition not a dispute.
                    self._normalized("dispute_defensible_label_dropped", finding_id=block["finding_id"], item_index=index)
                    seen.add(item["source_id"])
                    continue
                if type(item["stored_label_defensible"]) is not bool:
                    _error(errors, where + ".stored_label_defensible", "type", "Answer true or false.")
                    continue
                if item["source_id"] not in labels or item["source_id"] in seen:
                    _error(errors, where + ".source_id", "source_id", "Use each table comment ID at most once.")
                elif item["proposed_label"] not in SENTIMENT_LABELS:
                    _error(errors, where + ".proposed_label", "label", "Propose a declared label.")
                elif item["proposed_label"] == labels[item["source_id"]]:
                    # Proposing the stored label changes nothing, so it is not a dispute.
                    self._normalized("dispute_same_label_dropped", finding_id=block["finding_id"], item_index=index)
                    seen.add(item["source_id"])
                    continue
                if not _string(item["problem"], PROBLEM_LIMIT):
                    _error(errors, where + ".problem", "text", "Explain the dispute in at most 300 characters.")
                seen.add(item.get("source_id"))
                kept.append(item)
            return None if len(errors) > start else {"label_disputes": deepcopy(kept)}
        assertions = entry.get("assertions") if isinstance(entry, dict) and set(entry) == {"assertions"} else None
        if isinstance(assertions, list) and len(assertions) > ASSERTION_LIMIT and \
                all(isinstance(item, dict) and item.get("assessment") == "supported" for item in assertions):
            # Supported claims create no correction, so extra ones change nothing; Gemini 68 sent 43
            # near-copies for one finding on its last attempt and the review failed.
            self._normalized("supported_assertions_truncated", finding_id=block["finding_id"],
                             removed_count=len(assertions) - ASSERTION_LIMIT)
            assertions = assertions[:ASSERTION_LIMIT]
        if not isinstance(assertions, list) or not 1 <= len(assertions) <= ASSERTION_LIMIT:
            _error(errors, path, "assertion_coverage", "Send 1-12 assertions for this finding.", finding_id=block["finding_id"])
            return None
        allowed = known.intersection(block["citation_ids"])
        checked = []
        for index, item in enumerate(assertions):
            where = f"{path}.assertions[{index}]"
            if not isinstance(item, dict) or set(item) != {"claim", "kind", "citation_ids", "assessment", "problem"}:
                _error(errors, where, "fields", "Use claim, kind, citation_ids, assessment and problem.")
                continue
            refs = list(dict.fromkeys(item["citation_ids"])) if isinstance(item["citation_ids"], list) else None
            if not _string(item["claim"], CLAIM_LIMIT):
                _error(errors, where + ".claim", "text", "Give a short nonempty claim label.")
            if item["kind"] not in ("factual", "proposal"):
                _error(errors, where + ".kind", "kind", "Choose factual or proposal.")
            if item["assessment"] not in ("supported", "contradicted", "insufficient_evidence"):
                _error(errors, where + ".assessment", "assessment", "Choose supported, contradicted or insufficient_evidence.")
            if refs is None or any(not isinstance(ref, str) for ref in refs):
                _error(errors, where + ".citation_ids", "assertion_citations", "Send a list of citation IDs.",
                       allowed_citation_ids=sorted(allowed))
            else:
                outside = [ref for ref in refs if ref not in allowed]
                if outside:
                    # The flat schema offers all findings' sources; keep only this finding's own.
                    self._normalized("assertion_citations_outside_finding", finding_id=block["finding_id"],
                                     item_index=index, removed_count=len(outside))
                    refs = [ref for ref in refs if ref in allowed]
                if has_evidence and item["kind"] == "factual" and item["assessment"] == "supported" and not refs and allowed:
                    # A supported claim rests on its finding's sources; rejecting it made a reviewer
                    # downgrade a supported claim to pass validation (2026-11-03, Gemini B7).
                    self._normalized("supported_assertion_citations_defaulted", finding_id=block["finding_id"],
                                     item_index=index)
                    refs = sorted(allowed)
            if item["assessment"] != "supported" and not _string(item["problem"], PROBLEM_LIMIT):
                _error(errors, where + ".problem", "problem_required", "Explain what is wrong in at most 300 characters.")
            checked.append({"claim": item["claim"], "kind": item["kind"], "citation_ids": refs or [],
                            "assessment": item["assessment"],
                            "reason": item["problem"] if item["assessment"] != "supported" else "Supported by the cited sources.",
                            "assertion_id": f"{block['finding_id']}:A{index + 1}"})
        return None if len(errors) > start else {"assertions": checked}

    @staticmethod
    def _label_objection(issue, lookup):
        """A Vanilla issue on a classification table citing one of its labeled comments; absences are never dropped."""
        if issue["owner"] != "Vanilla" or issue["kind"] == "missing_deliverable":
            return False
        labeled = {r["citation_id"] for key in issue["finding_ids"] for r in classification_records(lookup[key]) or []}
        return bool(labeled.intersection(issue["citation_ids"]))

    def _check_issue(self, item, index, ctx, excerpts, known, lookup, clarify, errors):
        path, start = f"new_issues[{index}]", len(errors)
        fields = {"kind", "owner", "issue", "requested_change", "request_ref", "finding_ids", "citation_ids"} | \
            ({"missing_source_ids"} if ctx["record_ids"] else set())
        if not isinstance(item, dict) or set(item) != fields:
            _error(errors, path, "fields", "Use exactly the declared issue fields.", expected_fields=sorted(fields))
            return None
        kinds = ISSUE_KINDS + (["policy_requirement"] if ctx["require_actionable"] else [])
        if item["kind"] == "policy_requirement" and ctx["require_actionable"] and \
                (item["owner"] != "Original" or item["request_ref"] is not None):
            # The Echo action policy has exactly one owner and no question excerpt.
            self._normalized("policy_requirement_fields_fixed", item_index=index)
            item = {**item, "owner": "Original", "request_ref": None}
        if item["kind"] not in kinds:
            _error(errors, path + ".kind", "kind", "Choose a declared issue kind.")
        if item["owner"] not in OWNERS:
            _error(errors, path + ".owner", "owner", "Choose a declared owner.")
        for key in ("issue", "requested_change"):
            if not _string(item[key], PROBLEM_LIMIT):
                _error(errors, f"{path}.{key}", "text", "Give a nonempty sentence of at most 300 characters.")
        ref = item["request_ref"]
        if ref is not None and ref not in excerpts:
            _error(errors, path + ".request_ref", "request_ref", "Select request_ref from question_excerpts or null.")
        if item["kind"] == "missing_deliverable" and ref is None:
            _error(errors, path + ".request_ref", "request_ref_required", "A missing deliverable needs the request_ref that asks for it.")
        if item["owner"] == "clarify" and not clarify:
            _error(errors, path + ".owner", "clarification_required", "Owner clarify needs a clarification_question.")
        if not isinstance(item["finding_ids"], list) or any(key not in lookup for key in item["finding_ids"]):
            _error(errors, path + ".finding_ids", "finding_identity", "Use finding IDs from the schema.")
        if not isinstance(item["citation_ids"], list) or any(key not in known for key in item["citation_ids"]):
            _error(errors, path + ".citation_ids", "correction_citations", "Use evidence citation IDs, never finding IDs.")
        named = self._named_ids(item.get("missing_source_ids", []), ctx["record_ids"], errors, path)
        if len(errors) > start or named is None:
            return None
        return {**{k: v for k, v in item.items() if k not in {"request_ref", "missing_source_ids"}},
                "request_excerpt": excerpts[ref]["text"] if ref else None, "missing_source_ids": named,
                "index": index, **self._code_note("support", index, named, ctx["rendered"])}

    # ---------------------------------------------------------------- review
    def _review(self, question, answer, evidence, visualization=None, numeric_coverage=None, claims=None,
                grounding=None, task_outcomes=None, require_sentiment=False, previous_corrections=None,
                require_actionable=False, resume_completeness=None):
        self.diagnostics.update(rejected_attempts=[], review_phases=[])
        for key in ("completeness_review", "support_review", "absence_annotations", "normalizations", "protocol_recovery",
                    "provisional_findings", "support_contract", "delivery_normalizations"):
            self.diagnostics.pop(key, None)
        identity = candidate_id(answer, evidence, visualization)
        self.diagnostics["candidate_id"] = identity
        binding = (identity, question, json.dumps(self.scope.__dict__, sort_keys=True))
        if getattr(self, "_finding_binding", None) != binding:
            self._finding_cache, self._finding_binding = {}, binding
        self._finding_review_cache = self._finding_cache  # inherited checkpoint helpers read this name
        budget = self.budget or RunBudget()
        checks = self.audit(answer, evidence, visualization)
        if claims is not None:
            catalog = FactCatalog(evidence, self.scope.__dict__)
            checks.extend(audit_claims(claims, answer, catalog, grounding))
            blocks = claims
        else:
            catalog, blocks = None, cited_findings(answer)
        for block in blocks:
            if self.application_text(block):
                # Not a model claim: the objective audit above still covers its text and citations.
                self._finding_cache.setdefault(block["finding_id"], {"assertions": [], "application_text": True})
        charts = (visualization or {}).get("charts") or []
        inventory = visible_inventory(blocks, charts)
        rendered = rendered_source_ids(blocks)
        record_ids = sorted({r["citation_id"] for e in evidence for r in e.get("classification_records", []) or []})

        # Phase 1: visible completeness, without evidence.
        checkpoint_progress(getattr(self, "review_checkpoint", None), phase="completeness")
        visible = {"question": question, "question_excerpts": fragments(question, "original_question"),
                   "authorized_scope": self.scope.__dict__, "candidate_answer": answer, "visible_inventory": inventory}
        if self.authorized_teams is not None:
            visible["authorized_teams"] = self.authorized_teams
        completeness = self.deliver("completeness", COMPLETENESS_INSTRUCTIONS, visible,
            lambda: self.completeness_tool(question, record_ids),
            lambda value: self.validate_completeness(value, question, answer, rendered, record_ids), budget, identity)
        if completeness is None:
            self._protocol_stop("completeness", identity)
            raise RuntimeError("Completeness verifier did not return a valid structured verdict (review delivery protocol exhausted).")
        self.diagnostics["completeness_review"] = review_snapshot(completeness)
        self.completed_completeness = {"binding": identity, "result": deepcopy(completeness)}

        # Phase 2: evidence support, with code-verified facts stated up front.
        visible_corrections = completeness["corrections"]
        obligations = list({item["correction_id"]: item for item in [*(previous_corrections or []), *visible_corrections]}.values())
        numeric = [{**item, "request_id": f"N{index + 1}"} for index, item in
                   enumerate(i for i in numeric_coverage or [] if i["status"] in {"pending", "error"})]
        responses = dict(self.original_responses or {})
        # Original v7 disputes through challenge_corrections; show it the same way as a v8 response.
        for challenge in getattr(self, "correction_challenges", None) or []:
            for key in challenge.get("correction_ids", []):
                responses.setdefault(key, {"response": "disputed", "note": challenge.get("reason", "")})
        packets = self.sentiment_review_context(evidence)
        cited = {key for b in blocks for key in b["citation_ids"]}
        comparisons = [f for f in catalog.facts.values() if f["kind"] == "calculated"
                       and set(f["citation_ids"]) <= cited][:64] if catalog else []
        payload = {
            "question": question, "question_excerpts": visible["question_excerpts"],
            "authorized_scope": self.scope.__dict__, "authorized_teams": self.authorized_teams,
            "findings": [{k: b[k] for k in ("finding_id", "kind", "text", "citation_ids") if k in b} |
                         ({"attention": b["review_warnings"]} if b.get("review_warnings") else {}) |
                         ({"application_text": True} if self.application_text(b) else {}) for b in blocks],
            "visible_inventory": inventory, "deterministic_issues": checks, "evidence": evidence,
            "sentiment_labels": [{"citation_id": p["citation_id"], "rubric_version": p["rubric_version"], "rubric": p["rubric"],
                                  "eligible_comments": p["eligible_comments"], "suppressed_comments": p["suppressed_comments"],
                                  "labels": [{"citation_id": c["citation_id"], "label": c["label"], "reason": c.get("reason")}
                                             for c in p["comments"]]} for p in packets],
            "obligations": [{**{k: item.get(k) for k in ("correction_id", "kind", "owner", "issue", "requested_change",
                                                          "request_excerpt", "origin_finding_id", "code_note")},
                             "detected_phases": item.get("detected_phases", []),
                             "original_response": responses.get(item["correction_id"])} for item in obligations],
            "pending_numeric_requests": numeric, "computed_comparisons": comparisons,
            "task_outcomes": task_outcomes or [], "require_actionable": require_actionable,
            "require_complete_sentiment": require_sentiment}
        if charts:
            payload["visualization"] = visualization
        if len(json.dumps(payload, ensure_ascii=False)) > 150_000:
            raise ValueError("Complete review evidence is too large; narrow the question or scope.")
        instructions = SUPPORT_INSTRUCTIONS + (SENTIMENT_NOTE if packets else "") + (NUMERIC_NOTE if numeric else "") + \
            (ACTION_NOTE if self.asks_actions(blocks, require_actionable) else LEGACY_ACTION_NOTE if require_actionable else "")
        self.diagnostics["support_contract"] = {"version": REVIEW_VERSION, "obligation_count": len(obligations),
            "pending_numeric_count": len(numeric), "require_actionable": require_actionable,
            "finding_count": len(blocks), "classification_findings": sum(classification_records(b) is not None for b in blocks)}
        ctx = {"question": question, "blocks": blocks, "evidence": evidence, "obligations": obligations, "numeric": numeric,
               "record_ids": record_ids, "rendered": rendered, "require_actionable": require_actionable,
               "ask_actions": self.asks_actions(blocks, require_actionable)}
        checkpoint_progress(getattr(self, "review_checkpoint", None), phase="support")
        support = self.deliver("support", instructions, payload,
            lambda: self.support_tool(question, blocks, evidence, obligations, numeric, record_ids, require_actionable),
            lambda value: self.validate_support(value, ctx), budget, identity)
        if support is None:
            self._protocol_stop("support", identity)
            if visible_corrections:
                # Approved recovery: completeness repairs return to Original; nothing is released.
                raise ReviewRepairNeeded(deepcopy(visible_corrections), identity)
            raise RuntimeError("Verifier did not return a valid structured verdict (review delivery protocol exhausted).")
        return self._verdict(identity, blocks, evidence, checks, completeness, obligations, support,
                             numeric_coverage, require_sentiment, answer)

    def _protocol_stop(self, phase, identity):
        attempts = next((p.get("model_attempts") for p in reversed(self.diagnostics["review_phases"]) if p["phase"] == phase), 0)
        provisional = {"candidate_id": identity, "finding_count": len(self._finding_cache)}
        self.diagnostics["provisional_findings"] = provisional
        self.diagnostics["protocol_recovery"] = {"phase": phase, "candidate_id": identity, "support_review_completed": False,
            "attempts_used": attempts, "attempt_limit": 3, "retained_finding_ids": sorted(self._finding_cache),
            "provisional_findings": provisional, "released_finding_count": 0, "reason": "delivery_contract_exhausted"}
        record("review_protocol_stopped", agent=self.name, phase=phase, candidate_id=identity, attempts_used=attempts,
               retained_findings=len(self._finding_cache), released_finding_count=0)

    def _verdict(self, identity, blocks, evidence, checks, completeness, obligations, support,
                 numeric_coverage, require_sentiment, answer):
        corrections, reviews = [], []
        for item in support["issues"]:
            corrections.append({"correction_id": f"C_{candidate_id(answer + item['issue'])}_support_{item['index'] + 1}",
                "issue": item["issue"], "kind": item["kind"], "owner": item["owner"],
                "requested_change": item["requested_change"], "citation_ids": item["citation_ids"],
                "request_excerpt": item["request_excerpt"], "finding_ids": item["finding_ids"],
                "missing_source_ids": item["missing_source_ids"], "detected_phases": ["support"], "_new_index": item["index"],
                **({"code_note": item["code_note"]} if item.get("code_note") else {})})
        ratings = {d: {"score": support["ratings"][d]["score"], "rationale": support["ratings"][d]["note"]} for d in DIMENSIONS}
        if completeness["corrections"] and completeness["score"] < ratings["Completeness"]["score"]:
            ratings["Completeness"] = {"score": completeness["score"], "rationale": completeness["rationale"]}
        issues = [c["issue"] for c in corrections]
        links = [i for i, c in enumerate(corrections) if c["_new_index"] == support["safety"]] if support["safety"] is not None else []
        gate = safety_gate(ratings, issues, links)
        # The reviewer states which category each interpretation describes; code compares its citations.
        stored = {r["citation_id"]: r["label"] for e in evidence for r in e.get("classification_records", []) or []}
        lookup = {b["finding_id"]: b for b in blocks}
        mismatches = {}
        for claim in support["category_claims"]:
            wrong = [ref for ref in lookup[claim["finding_id"]]["citation_ids"]
                     if ref in stored and stored[ref] not in claim["labels"]]
            if wrong:
                mismatches[claim["finding_id"]] = (" or ".join(claim["labels"]), wrong)
        if support["manager_actions"] == [] and not any(i["kind"] == "policy_requirement" for i in support["issues"]):
            self._normalized("policy_action_absent_from_proposal_types")
            corrections.append({"correction_id": f"C_{identity}_policy_action", "kind": "policy_requirement",
                "owner": "Original", "issue": "No concrete manager action reasoned from the analysis is visible; "
                "the reviewer classified no proposal as an action.", "requested_change": "Add at least one concrete manager action "
                "with its factual basis and assumed benefit.", "citation_ids": [], "request_excerpt": None,
                "detected_phases": ["support"], "_new_index": None})
        findings = []
        for block in blocks:
            review = self._finding_cache[block["finding_id"]]
            subset = [e for e in evidence if e.get("citation_id") in block["citation_ids"]]
            block_checks = self.audit(block["text"], subset)
            if evidence and not block["citation_ids"]:
                block_checks.append("Finding lacks an explicit evidence citation.")
            disputes = review.get("label_disputes")
            failed = disputes if disputes is not None else [a for a in review["assertions"] if a["assessment"] != "supported"]
            mismatch = mismatches.get(block["finding_id"])
            if mismatch:
                label, wrong = mismatch
                text = f"Describes {label} comments but cites " + ", ".join(f"{ref} (stored {stored[ref]})" for ref in wrong) + "."
                block_checks = block_checks + [text]
                corrections.append({"correction_id": f"C_{identity}_{block['finding_id']}_category",
                    "issue": f"Finding {block['finding_id']}: {text}", "kind": "unsupported_claim", "owner": "Original",
                    "requested_change": f"Cite only comments stored as {label}, or describe the cited comments accurately.",
                    "citation_ids": wrong, "request_excerpt": None, "origin_candidate_id": identity,
                    "origin_finding_id": block["finding_id"], "detected_phases": ["support"], "_new_index": None})
            evidence_ok = not failed and not block_checks
            reason = "; ".join([*(item.get("problem") or item.get("reason") for item in failed),
                                *([text] if mismatch else [])])[:600] or (
                "Application-generated boundary statement, not a model claim; covered by the objective audit."
                if review.get("application_text") else "All assessed claims are supported.")
            findings.append({**block, "status": "supported" if evidence_ok and not gate["active"] else "withheld",
                             "evidence_status": "supported" if evidence_ok else "withheld",
                             "release_blockers": ["safety_issue"] if gate["active"] else [],
                             "reason": reason, "deterministic_issues": block_checks,
                             **({"label_disputes": disputes} if disputes is not None else {"assertions": review["assertions"]})})
            record("finding_reviewed", agent=self.name, finding_id=block["finding_id"], status=findings[-1]["status"],
                   deterministic_issues=len(block_checks), failed_items=len(failed))
            if failed:
                vanilla = disputes is not None
                corrections.append({"correction_id": f"C_{identity}_{block['finding_id']}_" + ("labels" if vanilla else "assertions"),
                    "issue": f"Finding {block['finding_id']} has " + ("disputed classification labels." if vanilla else
                             "contradicted or insufficiently supported assertions."),
                    "kind": "unsupported_claim", "owner": "Vanilla" if vanilla else "Original",
                    "requested_change": "Reassess the disputed labels." if vanilla else "Correct or qualify the flagged assertions.",
                    "citation_ids": block["citation_ids"], "request_excerpt": None, "origin_candidate_id": identity,
                    "origin_finding_id": block["finding_id"], "detected_phases": ["support"],
                    **({"label_disputes": deepcopy(disputes)} if vanilla else {"assertion_assessments": deepcopy(failed)})})
        for item in obligations:
            judged = support["obligations"].get(item["correction_id"])
            status = STATUS_MAP[judged["status"]]
            reviews.append({"correction_id": item["correction_id"], "status": status, "reason": judged["note"], "replacement_id": None})
            if status == "unresolved" and not any(c["correction_id"] == item["correction_id"] for c in corrections):
                corrections.append({**deepcopy(item), "reviewer_note": judged["note"]})
        for request in support["numeric_reviews"]:
            if request["decision"] != "not_required":
                corrections.append({"correction_id": f"C_{candidate_id(answer)}_{request['request_id']}", "issue":
                    f"A planned numeric request remains {request['decision']}: {request['reason']}", "kind": "coverage",
                    "owner": "Cherry", "requested_change": "Complete the planned calculation.", "citation_ids": [],
                    "request_excerpt": None, "detected_phases": ["support"]})
        if require_sentiment and not any(e.get("kind") == "survey_sentiment" and e.get("complete") is True for e in evidence):
            corrections.append({"correction_id": f"C_{candidate_id(answer)}_sentiment_coverage",
                "issue": "Requested full comment classification remains incomplete; no partial percentages may be released.",
                "kind": "coverage", "owner": "Vanilla", "requested_change": "Complete the classification.",
                "citation_ids": [], "request_excerpt": None, "detected_phases": ["support"]})
        for correction in corrections:
            correction.pop("_new_index", None)
        corrections = reconcile_corrections(corrections)
        issues = [c["issue"] for c in corrections]
        for index, correction in enumerate(corrections):
            correction["issue_index"] = index
        blocked = bool(checks or corrections or gate["active"]) or any(f["status"] != "supported" for f in findings)
        decision = "revise" if blocked else "accept"
        low = [d for d in DIMENSIONS if ratings[d]["score"] < 3]
        if low and not blocked:
            self.diagnostics["unexplained_low_scores"] = low
        targets = sorted({c["owner"] for c in corrections}) or (["Original"] if blocked else [])
        result = VerificationResult(decision, ratings, issues,
            "Semantic correctness is a model judgment; human validation is pending.", checks, self.mode,
            findings, targets, support["clarification_question"], completeness["suggestions"], corrections, reviews,
            completeness, version=REVIEW_VERSION, candidate_id=identity, numeric_reviews=support["numeric_reviews"],
            correction_judgments=support["obligations"], release_gate=gate,
            explanation_quality={"status": "complete", "contract": REVIEW_VERSION, "semantic_quality_verified": False})
        self.diagnostics["provisional_findings"] = {"candidate_id": identity, "finding_count": len(findings),
            "supported_count": sum(f["status"] == "supported" for f in findings),
            "withheld_count": sum(f["status"] != "supported" for f in findings)}
        self.diagnostics["release_gate"] = deepcopy(gate)
        self.diagnostics["support_review"] = review_snapshot({"decision": decision, "issues": issues,
            "correction_reviews": reviews, "repair_targets": targets})
        record("verification_finished", agent=self.name, decision=decision, deterministic_issues=len(checks),
               model_issues=len(issues))
        return result
