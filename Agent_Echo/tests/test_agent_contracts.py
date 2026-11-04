"""Offline delivery checks for Original v8 and ZeroSugar v8; scripted judgments are not accuracy evidence."""

import json
import unittest

from agents.grounding import FactCatalog, render_answer, GROUNDING_VERSION
from agents.content import excerpt_catalog
from agents.original import OriginalAgent, PLANNING_INSTRUCTIONS, INSTRUCTIONS
from agents.runtime import RunBudget, Specialist
from agents.zero_sugar import DIMENSIONS
from agents.zero_sugar import ZeroSugarAgent, SUPPORT_INSTRUCTIONS, COMPLETENESS_INSTRUCTIONS
from test_agents import DATABASE, tool_turn
from fixtures import SCOPE
from fixtures import classification_fixture

QUESTION = ("Classify every eligible Recognition comment, show counts and percentages, include one literal "
            "critical example, and propose one manager action.")


class Scripted:
    """Returns one scripted argument object per call, built from the request it receives."""

    def __init__(self, **queues):
        self.queues = {name: list(items) for name, items in queues.items()}
        self.calls = []

    def respond(self, instructions, history, tools, require_tool=False):
        name = tools[-1]["name"]
        self.calls.append({"name": name, "history": history, "tool": tools[-1], "instructions": instructions})
        context = next(json.loads(h["content"].split("\n", 1)[1]) for h in history
                       if isinstance(h.get("content"), str) and h["content"].startswith("WORKSPACE")) \
            if name == "submit_answer" else json.loads(history[0]["content"])
        return tool_turn(name, self.queues[name].pop(0)(context, tools[-1]), identifier=f"call-{len(self.calls)}")


def accept_completeness(context, tool):
    return {"decision": "accept", "score": 3, "rationale": "Every requested part is visible.", "missing": [], "suggestions": []}


def pending(tool, name):
    """Finding IDs the support tool still asks for under assertions or label_disputes."""
    return tool["parameters"]["properties"][name]["items"]["properties"]["finding_id"].get("enum", [])


def supported(context, tool, **changes):
    properties = tool["parameters"]["properties"]
    blocks = {f["finding_id"]: f for f in context["findings"]}
    assertions = [{"finding_id": key, "claim": "Main claim of " + key,
                   "kind": "proposal" if blocks[key].get("kind") == "proposal" else "factual",
                   "citation_ids": blocks[key]["citation_ids"][:1], "assessment": "supported", "problem": None}
                  for key in pending(tool, "assertions")]
    value = {"assertions": assertions, "label_disputes": [], "new_issues": [], "safety_issue_index": None,
             "clarification_question": None,
             "ratings": {d: {"score": 3, "note": "Satisfactory."} for d in DIMENSIONS}}
    if "obligations" in properties:
        value["obligations"] = {key: {"status": "satisfied", "note": "Visible now."} for key in properties["obligations"]["properties"]}
    if "proposal_types" in properties:
        ids = properties["proposal_types"]["items"]["properties"]["finding_id"].get("enum", [])
        value["proposal_types"] = [{"finding_id": key, "type": "action"} for key in ids]
    if "category_claims" in properties:
        value["category_claims"] = []
    value.update(changes)
    return value


def candidate(evidence):
    catalog = FactCatalog(evidence, SCOPE.__dict__)
    payload = catalog.bind_classification_display({"fact_ids": [], "interpretations": [
        {"text": "Most comments describe recognition favorably.", "citation_ids": ["SENTIMENT1"], "quote": None}],
        "proposals": [{"text": "Review recognition practices with the team.", "citation_ids": ["SENTIMENT1"], "quote": None}]},
        "Original")
    text, claims = render_answer(payload, catalog, "Original")
    return text, claims, {"version": GROUNDING_VERSION, "payload": payload, "role": "Original"}


def reviewer(model, report, docs, evidence):
    return ZeroSugarAgent(SCOPE, model, "live", budget=RunBudget(), sentiment_reports={"SENTIMENT1": report},
                            sentiment_documents=docs, document_lookup={e["citation_id"]: e for e in evidence[1:]},
                            authorized_teams=["Data Platforms"])


class ZeroSugarContractTests(unittest.TestCase):
    def setUp(self):
        self.report, self.docs, self.evidence = classification_fixture()
        self.answer, self.claims, self.grounding = candidate(self.evidence)

    def review(self, model, **kwargs):
        agent = reviewer(model, self.report, self.docs, self.evidence)
        result = agent.review(QUESTION, self.answer, self.evidence, claims=self.claims, grounding=self.grounding, **kwargs)
        return agent, result

    def test_absence_naming_rendered_comments_is_annotated_never_dropped(self):
        # Smoke run 2026-11-03: the named IDs meant "quote these comments", so a table row cannot settle it.
        def absence(context, tool):
            return {"decision": "revise", "score": 2, "rationale": "A critical example is missing.", "suggestions": [], "missing": [{
                "request_ref": next(iter(context["question_excerpts"])), "issue": "No critical excerpt is shown.",
                "requested_change": "Quote a critical comment.", "missing_source_ids": ["survey:CMT1", "survey:CMT2"]}]}
        model = Scripted(submit_completeness_review=[absence], submit_support_review=[
            lambda context, tool: supported(context, tool, obligations={key: {"status": "open", "note": "No critical quote."}
                for key in tool["parameters"]["properties"]["obligations"]["properties"]})])
        agent, result = self.review(model)
        self.assertEqual(result.decision, "revise")
        self.assertEqual(len(agent.diagnostics["absence_annotations"]), 1)
        sent = json.loads(model.calls[1]["history"][0]["content"])["obligations"][0]
        self.assertIn("survey:CMT1, survey:CMT2", sent["code_note"])
        self.assertEqual(result.corrections[0]["missing_source_ids"], ["survey:CMT1", "survey:CMT2"])
        self.assertEqual(model.calls[0]["history"][0]["content"].count("per_comment_classifications"), 1)

    def test_support_schema_is_flat_and_a_stringified_list_is_rejected(self):
        def stringified(context, tool):
            value = supported(context, tool)
            value["assertions"] = json.dumps(value["assertions"])
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[stringified, supported])
        agent, result = self.review(model)
        properties = model.calls[1]["tool"]["parameters"]["properties"]
        self.assertNotIn("findings", properties)
        self.assertEqual(properties["assertions"]["type"], "array")
        self.assertIn("type", agent.diagnostics["rejected_attempts"][0]["codes"])
        self.assertEqual(result.decision, "accept")

    def test_all_errors_reported_together_and_retry_sends_only_latest_attempt(self):
        def broken(context, tool):
            value = supported(context, tool)
            first, second = value["assertions"][0]["finding_id"], value["assertions"][1]["finding_id"]
            value["assertions"] = [a for a in value["assertions"] if a["finding_id"] != first]
            value["assertions"][0].update(assessment="insufficient_evidence", problem=None)
            self.assertEqual(value["assertions"][0]["finding_id"], second)
            value["safety_issue_index"] = 3
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[broken, supported])
        agent, result = self.review(model)
        rejection = agent.diagnostics["rejected_attempts"][0]
        self.assertEqual(set(rejection["codes"]), {"finding_missing", "problem_required", "safety_index"})
        self.assertEqual(rejection["resolution"], "accepted_review_submission")
        retry = model.calls[2]
        self.assertEqual(len(retry["history"]), 3)
        self.assertEqual(len(pending(retry["tool"], "assertions")), 2)
        self.assertEqual(pending(retry["tool"], "label_disputes"), [])
        self.assertEqual(result.decision, "accept")

    def test_label_dispute_withholds_only_the_table_and_routes_to_vanilla(self):
        def dispute(context, tool):
            value = supported(context, tool)
            value["label_disputes"] = [{"finding_id": pending(tool, "label_disputes")[0], "source_id": "survey:CMT8",
                                        "proposed_label": "positive", "stored_label_defensible": False,
                                        "problem": "The comment states no current criticism."}]
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[dispute])
        _, result = self.review(model)
        withheld = [f for f in result.findings if f["status"] != "supported"]
        self.assertEqual([f["kind"] for f in withheld], ["table"])
        self.assertEqual(result.decision, "revise")
        self.assertEqual([c["owner"] for c in result.corrections], ["Vanilla"])

    def test_obligations_take_one_status_and_see_original_disputes(self):
        prior = [{"correction_id": "C_0123456789abcdef_visible_1", "kind": "missing_deliverable", "owner": "Original",
                  "issue": "Team questions are missing.", "requested_change": "Add two team questions.",
                  "request_excerpt": None, "citation_ids": []}]
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[
            lambda context, tool: supported(context, tool, obligations={prior[0]["correction_id"]: {
                "status": "open", "note": "Still absent from the visible answer."}})])
        agent = reviewer(model, self.report, self.docs, self.evidence)
        agent.original_responses = {prior[0]["correction_id"]: {"response": "disputed", "note": "The question asked for none."}}
        result = agent.review(QUESTION, self.answer, self.evidence, claims=self.claims, grounding=self.grounding,
                              previous_corrections=prior)
        sent = json.loads(model.calls[1]["history"][0]["content"])["obligations"][0]
        self.assertEqual(sent["original_response"]["response"], "disputed")
        self.assertEqual(result.correction_reviews[0]["status"], "unresolved")
        self.assertEqual(result.corrections[0]["reviewer_note"], "Still absent from the visible answer.")
        self.assertEqual(result.decision, "revise")

    def test_mechanical_delivery_slips_are_normalized_instead_of_rejected(self):
        # Smoke run 2026-11-03: these four slips exhausted the support attempts of B2 and B15.
        def slips(context, tool):
            value = supported(context, tool)
            interpretation = next(a for a in value["assertions"] if a["finding_id"] == "F2")
            interpretation["citation_ids"] = ["SENTIMENT1", "survey:CMT3"]   # CMT3 belongs to no finding here
            value["label_disputes"] = [{"finding_id": pending(tool, "label_disputes")[0], "source_id": "survey:CMT8",
                                        "proposed_label": "mixed", "stored_label_defensible": False, "problem": "Mixed fits the comment."}]
            value["new_issues"] = [{"kind": "policy_requirement", "owner": "Cherry",
                                    "request_ref": next(iter(context["question_excerpts"])), "issue": "No action.",
                                    "requested_change": "Add one action.", "finding_ids": [], "citation_ids": [],
                                    "missing_source_ids": []}]
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[slips])
        agent, result = self.review(model, require_actionable=True)
        self.assertEqual(agent.diagnostics["rejected_attempts"], [])
        self.assertEqual({n["code"] for n in agent.diagnostics["delivery_normalizations"]},
                         {"assertion_citations_outside_finding", "dispute_same_label_dropped", "policy_requirement_fields_fixed"})
        boundary = next(f for f in result.findings if f["kind"] == "limitation")
        self.assertNotIn(boundary["finding_id"], pending(model.calls[1]["tool"], "assertions"))
        self.assertEqual(boundary["status"], "supported")
        self.assertEqual(next(f for f in result.findings if f["kind"] == "table")["label_disputes"], [])
        policy = next(c for c in result.corrections if c["kind"] == "policy_requirement")
        self.assertEqual((policy["owner"], policy["request_excerpt"]), ("Original", None))
        self.assertEqual(result.decision, "revise")

    def test_empty_manager_action_list_records_the_policy_gap_in_code(self):
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[
            lambda context, tool: supported(context, tool, proposal_types=[
                {"finding_id": key, "type": "team_question"} for key in
                tool["parameters"]["properties"]["proposal_types"]["items"]["properties"]["finding_id"]["enum"]])])
        _, result = self.review(model, require_actionable=True)
        policy = [c for c in result.corrections if c["kind"] == "policy_requirement"]
        self.assertEqual([(c["owner"], c["request_excerpt"]) for c in policy], [("Original", None)])
        self.assertEqual(result.decision, "revise")

    def test_untyped_answer_never_gets_a_code_derived_policy_correction(self):
        # Without rendered claims there are no proposal findings, so an empty list would mean nothing.
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[supported])
        agent = reviewer(model, self.report, self.docs, self.evidence)
        result = agent.review(QUESTION, "Most comments describe recognition favorably. [SENTIMENT1]", self.evidence,
                              require_actionable=True)
        self.assertNotIn("proposal_types", model.calls[1]["tool"]["parameters"]["properties"])
        self.assertIn("add one new issue of kind policy_requirement", model.calls[1]["instructions"])
        self.assertFalse(any(c["correction_id"].endswith("_policy_action") for c in result.corrections))

    def test_listed_action_satisfies_the_policy_without_a_correction(self):
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[supported])
        _, result = self.review(model, require_actionable=True)
        self.assertEqual(result.decision, "accept")

    def test_category_claim_is_checked_against_stored_labels(self):
        # B7/B15 pattern: prose about mixed comments that cites a comment stored as positive.
        catalog = FactCatalog(self.evidence, SCOPE.__dict__)
        payload = catalog.bind_classification_display({"fact_ids": [], "interpretations": [
            {"text": "Mixed comments combine support with gaps.", "citation_ids": ["survey:CMT8", "survey:CMT3"], "quote": None}],
            "proposals": [{"text": "Review recognition practices with the team.", "citation_ids": ["SENTIMENT1"], "quote": None}]},
            "Original")
        answer, claims = render_answer(payload, catalog, "Original")
        grounding = {"version": GROUNDING_VERSION, "payload": payload, "role": "Original"}
        prose = next(c for c in claims if c["kind"] == "interpretation")["finding_id"]
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[
            lambda context, tool: supported(context, tool, category_claims=[{"finding_id": prose, "labels": ["mixed"]}])])
        result = reviewer(model, self.report, self.docs, self.evidence).review(
            QUESTION, answer, self.evidence, claims=claims, grounding=grounding)
        finding = next(f for f in result.findings if f["finding_id"] == prose)
        self.assertEqual(finding["status"], "withheld")
        self.assertIn("survey:CMT3 (stored positive)", finding["deterministic_issues"][-1])
        self.assertEqual(next(c for c in result.corrections if c["correction_id"].endswith("_category"))["citation_ids"],
                         ["survey:CMT3"])

    def test_category_claim_with_several_labels_accepts_comments_of_each(self):
        # Luna/Gemini B15 F4: one paragraph about negative and mixed comments.
        catalog = FactCatalog(self.evidence, SCOPE.__dict__)
        payload = catalog.bind_classification_display({"fact_ids": [], "interpretations": [
            {"text": "Negative and mixed comments share one gap.", "citation_ids": ["survey:CMT1", "survey:CMT8"], "quote": None}],
            "proposals": [{"text": "Review recognition practices with the team.", "citation_ids": ["SENTIMENT1"], "quote": None}]},
            "Original")
        answer, claims = render_answer(payload, catalog, "Original")
        grounding = {"version": GROUNDING_VERSION, "payload": payload, "role": "Original"}
        prose = next(c for c in claims if c["kind"] == "interpretation")["finding_id"]
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[
            lambda context, tool: supported(context, tool, category_claims=[{"finding_id": prose, "labels": ["negative", "mixed"]}])])
        result = reviewer(model, self.report, self.docs, self.evidence).review(
            QUESTION, answer, self.evidence, claims=claims, grounding=grounding)
        self.assertEqual(result.decision, "accept")

    def test_supported_factual_claim_without_citations_gets_its_finding_sources(self):
        def uncited(context, tool):
            value = supported(context, tool)
            factual = next(a for a in value["assertions"] if a["kind"] == "factual")
            factual["citation_ids"] = []
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[uncited])
        agent, result = self.review(model)
        self.assertEqual(agent.diagnostics["rejected_attempts"], [])
        self.assertIn("supported_assertion_citations_defaulted", {n["code"] for n in agent.diagnostics["delivery_normalizations"]})
        self.assertEqual(result.decision, "accept")

    def test_dispute_marked_defensible_is_dropped(self):
        def defensible(context, tool):
            value = supported(context, tool)
            value["label_disputes"] = [{"finding_id": pending(tool, "label_disputes")[0], "source_id": "survey:CMT12",
                                        "proposed_label": "positive", "stored_label_defensible": True,
                                        "problem": "Mixed is defensible; positive is also possible."}]
            return value
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[defensible])
        agent, result = self.review(model)
        self.assertEqual(result.decision, "accept")
        self.assertIn("dispute_defensible_label_dropped", {n["code"] for n in agent.diagnostics["delivery_normalizations"]})

    def test_production_original_reviews_with_v8(self):
        # A fresh interpreter: test_agents pins the review-v7 fixtures for the older workflow tests.
        import subprocess, sys
        from pathlib import Path
        code = ("from agents.original import OriginalAgent; from agents.zero_sugar import ZeroSugarAgent; "
                "import run_agent; assert OriginalAgent.reviewer_class is ZeroSugarAgent; "
                "assert run_agent.ZeroSugarAgent is ZeroSugarAgent; "
                "from agents.original import OriginalAgent; assert run_agent.OriginalAgent is OriginalAgent")
        subprocess.run([sys.executable, "-B", "-c", code], cwd=Path(__file__).resolve().parents[1], check=True)

    def test_original_v7_challenge_reaches_v8_as_a_dispute(self):
        prior = [{"correction_id": "C_0123456789abcdef_visible_1", "kind": "missing_deliverable", "owner": "Original",
                  "issue": "Team questions are missing.", "requested_change": "Add two team questions.",
                  "request_excerpt": None, "citation_ids": []}]
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[supported])
        agent = reviewer(model, self.report, self.docs, self.evidence)
        agent.correction_challenges = [{"correction_ids": [prior[0]["correction_id"]], "finding_ids": [],
                                        "reason": "Two questions are already visible."}]
        agent.review(QUESTION, self.answer, self.evidence, claims=self.claims, grounding=self.grounding,
                     previous_corrections=prior)
        sent = json.loads(model.calls[1]["history"][0]["content"])["obligations"][0]
        self.assertEqual(sent["original_response"], {"response": "disputed", "note": "Two questions are already visible."})

    def test_low_score_without_item_is_recorded_not_a_revision(self):
        model = Scripted(submit_completeness_review=[accept_completeness], submit_support_review=[
            lambda context, tool: supported(context, tool, ratings={d: {"score": 2 if d == "Clarity" else 3, "note": "Fine."}
                                                                    for d in DIMENSIONS})])
        agent, result = self.review(model)
        self.assertEqual(result.decision, "accept")
        self.assertEqual(agent.diagnostics["unexplained_low_scores"], ["Clarity"])


def original_agent(model):
    agent = OriginalAgent(DATABASE, SCOPE, lambda name: model, "live")
    agent.budget = RunBudget()
    agent.set_delegations([])
    agent.numeric_requested = False
    agent.reusable_blocks, agent.draft_blocks, agent.draft_texts = {}, {}, {}
    return agent


def answer(context, tool, **changes):
    critical = next(ref for ref, source, _ in context["excerpts"] if source == "survey:CMT1")
    value = {"fact_ids": [], "interpretations": [], "reuse_ids": [], "removals": [],
             "examples": [{"excerpt_ref": critical, "label": "Critical example", "label_group": "negative"}],
             "proposals": [{"text": "Discuss uneven recognition with the team.", "citation_ids": ["SENTIMENT1"]}]}
    if "correction_responses" in tool["parameters"]["properties"]:
        value["correction_responses"] = {key: {"response": "fixed", "note": "Added."}
                                         for key in tool["parameters"]["properties"]["correction_responses"]["properties"]}
    value.update(changes)
    return value


class OriginalContractTests(unittest.TestCase):
    def setUp(self):
        self.report, self.docs, self.evidence = classification_fixture()

    def test_example_citation_is_derived_from_its_excerpt_and_replays_in_review(self):
        model = Scripted(submit_answer=[answer], submit_completeness_review=[accept_completeness],
                         submit_support_review=[supported])
        agent = original_agent(model)
        result = Specialist.run(agent, QUESTION, initial_evidence=self.evidence)
        example = next(c for c in result.claims if c.get("quote"))
        self.assertEqual((example["quote"], example["citation_ids"]), ("Comment number 1.", ["survey:CMT1"]))
        self.assertTrue(any(c["kind"] == "table" and c["operation"].get("type") == "sentiment_classifications"
                            for c in result.claims))
        verdict = reviewer(model, self.report, self.docs, self.evidence).review(
            QUESTION, result.answer, result.evidence, claims=result.claims, grounding=result.grounding)
        self.assertEqual(verdict.deterministic_issues, [])
        self.assertEqual(verdict.decision, "accept")

    def test_every_delivery_error_is_reported_once_and_retry_drops_older_attempts(self):
        def broken(context, tool):
            return answer(context, tool, removals=[{"block_id": "BLOCK_0000000000000000", "reason": "Old."}],
                          interpretations=[{"text": "Positive comments.", "citation_ids": ["survey:CMT1"], "label_group": "positive"},
                                           {"text": "Unknown.", "citation_ids": ["survey:NOPE"], "label_group": None}])
        model = Scripted(submit_answer=[broken, broken, answer])
        agent = original_agent(model)
        Specialist.run(agent, QUESTION, initial_evidence=self.evidence)
        rejection = agent.last_result.diagnostics["rejected_attempts"][0]
        self.assertEqual(set(rejection["codes"]), {"removal_unknown", "label_group_mismatch", "source_unknown"})
        self.assertEqual(len(model.calls), 3)
        # question + retained evidence + workspace + the latest rejected call and its feedback
        self.assertEqual(len(model.calls[2]["history"]), 5)

    def test_label_group_without_cited_comments_is_normalized_without_a_retry(self):
        # Run 64 spent five retries on label_group_sources; label_group is validation-only, so it is dropped.
        def aggregate_group(context, tool):
            return answer(context, tool, interpretations=[
                {"text": "Negative comments are a minority.", "citation_ids": ["SENTIMENT1"], "label_group": "negative"}])
        model = Scripted(submit_answer=[aggregate_group])
        agent = original_agent(model)
        Specialist.run(agent, QUESTION, initial_evidence=self.evidence)
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(agent.last_result.diagnostics.get("rejected_attempts", []), [])

    def test_only_a_requested_chart_blocks_completion(self):
        from types import SimpleNamespace
        agent = original_agent(Scripted())
        failure = {"error_category": "task_declined"}
        candidate = SimpleNamespace(visualization={"charts": [], "tool_trace": []})
        self.assertIsNone(agent.chart_blocks("Summarize recognition comments.", candidate, failure))
        self.assertIn("No chart was requested", candidate.visualization["reason"])
        self.assertEqual(agent.chart_blocks("Show a chart of recognition scores.", candidate, failure), failure)

    def test_repair_answers_each_open_correction_and_keeps_disputes(self):
        def silent(context, tool):
            value = answer(context, tool)
            value.pop("correction_responses")
            return value
        disputed = lambda context, tool: answer(context, tool, correction_responses={
            "C_0123456789abcdef_visible_1": {"response": "disputed", "note": "The question asks for one action only."}})
        model = Scripted(submit_answer=[silent, disputed])
        agent = original_agent(model)
        agent.open_corrections = [{"correction_id": "C_0123456789abcdef_visible_1", "owner": "Original",
                                   "kind": "missing_deliverable", "issue": "A second action is missing.",
                                   "requested_change": "Add a second action."}]
        Specialist.run(agent, QUESTION, initial_evidence=self.evidence)
        self.assertEqual(agent.last_result.diagnostics["rejected_attempts"][0]["codes"], ["fields"])
        self.assertEqual(agent.correction_responses["C_0123456789abcdef_visible_1"]["response"], "disputed")

    def test_prompts_do_not_name_the_single_test_case(self):
        for text in (PLANNING_INSTRUCTIONS, INSTRUCTIONS, SUPPORT_INSTRUCTIONS, COMPLETENESS_INSTRUCTIONS):
            self.assertNotIn("Recognition", text)


if __name__ == "__main__":
    unittest.main()
