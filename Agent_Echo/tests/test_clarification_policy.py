"""Offline regressions for shared instructions and bounded clarification handling.

Scripted decisions exercise application behavior, not model reasoning quality.
"""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agents import AccessScope, CherryAgent, VanillaAgent, OriginalAgent, ZeroSugarAgent, LimeAgent
from agents.execution_log import RunLog
from agents.model import ModelTurn
from agents.policies import COMMON_POLICY
from agents.runtime import RunBudget, Specialist
from test_agents import live_fixture, tool_turn
from test_flow_improvements import ReviewModel
from test_workflow_repairs import GroundedSequenceModel, numeric_plan, requests

DATABASE = Path(__file__).resolve().parents[1] / "data" / "echo.db"
SCOPE = AccessScope("M14", "2026-01-01", "2026-09-30")
MEDIUM_QUESTION = (
    "I'm preparing for a team check-in. Has recognition improved over the first three quarters of 2026? "
    "How does that compare with how supported people feel by their managers? Show me a simple table of the "
    "results, explain the main changes, and tell me what I should be careful about when interpreting them.")


class ObservedModel:
    def __init__(self, turns=(), delegate=None):
        self.turns, self.delegate, self.calls = iter(turns), delegate, []

    def respond(self, instructions, history, tools, require_tool=False):
        self.calls.append((instructions, deepcopy(history), deepcopy(tools)))
        if self.delegate is not None:
            return self.delegate.respond(instructions, history, tools, require_tool)
        return live_fixture(next(self.turns), instructions, history, tools)


def planned(q=None, basis=None):
    return tool_turn("submit_plan", {"needs_numbers": False, "needs_text": False, "include_chart": False,
                                    "needs_sentiment": False,
                                    "clarification_question": q, "clarification_basis": basis, "metrics": []})


def missing(excerpt, field="metric"):
    return {"missing_field": field, "missing_detail": "Which recognition definition to use",
            "blocking_reason": "Different recognition definitions produce different counts.",
            "request_excerpt": excerpt}


class ClarificationPolicyTests(unittest.TestCase):
    def agent(self, model, limit=32):
        agent = OriginalAgent(DATABASE, SCOPE, lambda role: model, "live")
        agent.budget = RunBudget(model_limit=limit)
        self.addCleanup(agent.close)
        return agent

    def test_complete_plan_uses_one_call_without_an_extra_reviewer(self):
        model = ObservedModel([planned()])
        agent = self.agent(model)
        self.assertIsNone(agent.plan(MEDIUM_QUESTION)["clarification_question"])
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(agent.budget.models, 1)
        self.assertEqual(agent.specialists, {})

    def test_observed_false_clarification_is_reconsidered_with_the_whole_question(self):
        model = ObservedModel([planned("What would you like me to cover after 'tell me what'?",
                                       missing("tell me what", "task")), planned()])
        agent = self.agent(model)
        result = agent.plan(MEDIUM_QUESTION)
        self.assertIsNone(result["clarification_question"])
        self.assertEqual(len(model.calls), 2)
        for _, history, _ in model.calls:
            context = json.loads(history[0]["content"])
            self.assertEqual(context["question"], MEDIUM_QUESTION)
            self.assertEqual(context["scope"], SCOPE.__dict__)
            self.assertTrue(context["question_excerpts"])
        feedback = json.loads(model.calls[1][1][-1]["output"])
        self.assertEqual(feedback["validation_code"], "clarification_recheck")
        self.assertEqual(agent.specialists, {})


    def test_already_supplied_scope_fields_cannot_be_requested_again(self):
        for field in ("manager_id", "start_date", "end_date"):
            with self.subTest(field=field):
                turn = planned("Please provide the scope.", missing("Show recognition.", field))
                model = ObservedModel([turn, turn])
                agent = self.agent(model)
                with self.assertRaisesRegex(RuntimeError, "valid bounded analysis plan"):
                    agent.plan("Show recognition.")
                feedback = json.loads(model.calls[1][1][-1]["output"])
                self.assertEqual(feedback["validation_code"], "clarification_already_supplied")
                self.assertEqual(len(model.calls), 2)

    def test_a_scope_question_can_be_corrected_to_a_plan_without_asking_the_user(self):
        model = ObservedModel([planned("Which manager?", missing("Show recognition.", "manager_id")), planned()])
        self.assertIsNone(self.agent(model).plan("Show recognition.")["clarification_question"])
        self.assertEqual(len(model.calls), 2)

    def test_missing_justification_and_invented_request_excerpt_are_rejected(self):
        for basis, code in ((None, "clarification_reference"),
                            (missing("tell me what..."), "excerpt_reference"),
                            ({**missing("tell me what"), "blocking_reason": " "}, "clarification_basis_text")):
            with self.subTest(code=code):
                model = ObservedModel([planned("What do you mean?", basis), planned()])
                result = self.agent(model).plan(MEDIUM_QUESTION)
                self.assertIsNone(result["clarification_question"])
                feedback = json.loads(model.calls[1][1][-1]["output"])
                self.assertEqual(feedback["validation_code"], code)

    def test_unused_basis_is_normalized_without_an_extra_call(self):
        model = ObservedModel([planned(basis=missing("Show recognition.")), planned()])
        self.assertIsNone(self.agent(model).plan("Show recognition.")["clarification_basis"])
        self.assertEqual(len(model.calls), 1)

    def test_persistent_invalid_clarifications_fail_bounded_without_questioning_user(self):
        turn = planned("Which manager?", missing("Show recognition.", "manager_id"))
        model = ObservedModel([turn, turn])
        agent = self.agent(model)
        result = agent.run("Show recognition.")
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.clarification_questions, [])
        self.assertEqual(result.evidence, [])
        self.assertEqual(len(model.calls), 2)
        self.assertEqual(agent.specialists, {})

    def test_reconsideration_cannot_bypass_the_shared_budget(self):
        turn = planned("Which recognition definition?", missing("Check recognition."))
        model = ObservedModel([turn, turn])
        agent = self.agent(model, limit=1)
        with self.assertRaisesRegex(RuntimeError, "call budget exceeded"):
            agent.plan("Check recognition.")
        self.assertEqual(len(model.calls), 1)

    def test_late_clarification_is_rechecked_and_can_still_be_asked(self):
        # M3 Gemini P8/P9/P12/P13: attempt 1 invalid, clarification first asked on attempt 2.
        turn = planned("Which recognition definition?", missing("Check recognition."))
        model = ObservedModel([tool_turn("submit_plan", {}), turn, turn])
        result = self.agent(model).plan("Check recognition.")
        self.assertEqual(result["clarification_question"], "Which recognition definition?")
        self.assertEqual(len(model.calls), 3)
        self.assertEqual(json.loads(model.calls[2][1][-1]["output"])["validation_code"], "clarification_recheck")

    def test_error_after_the_recheck_can_be_corrected_once(self):
        # M3 apinex_test P12/P13: after the recheck the repeated clarification dropped request_ref.
        turn = planned("Which recognition definition?", missing("Check recognition."))
        broken = planned("Which recognition definition?", None)
        model = ObservedModel([turn, broken, turn])
        result = self.agent(model).plan("Check recognition.")
        self.assertEqual(result["clarification_question"], "Which recognition definition?")
        self.assertEqual(len(model.calls), 3)

    def test_recheck_adds_only_one_turn(self):
        turn = planned("Which recognition definition?", missing("Check recognition."))
        broken = planned("Which recognition definition?", None)
        model = ObservedModel([tool_turn("submit_plan", {}), turn, broken, turn])
        with self.assertRaisesRegex(RuntimeError, "valid bounded analysis plan"):
            self.agent(model).plan("Check recognition.")
        self.assertEqual(len(model.calls), 3)

    def test_clarification_on_a_plan_that_selects_a_specialist_is_dropped(self):
        # M3 Gemini P2/P8: the plan chose Cherry or Vanilla, then asked for topic names or a roster they retrieve.
        turn = planned("Which exact survey topic names should I use?", missing(MEDIUM_QUESTION[:34]))
        args = json.loads(turn.calls[0].arguments)
        args.update(needs_text=True)
        model = ObservedModel([tool_turn("submit_plan", args)])
        agent = self.agent(model)
        result = agent.plan(MEDIUM_QUESTION)
        self.assertEqual((result["clarification_question"], result["clarification_basis"]), (None, None))
        self.assertEqual(len(model.calls), 1)
        self.assertEqual([d.get("validation_code") for d in agent.planning_diagnostics], ["clarification_with_specialist"])

    def test_diagnostics_record_recheck_code_with_bounded_redaction(self):
        turn = planned("Which recognition definition?", missing("private@example.invalid recognition"))
        model = ObservedModel([turn, planned()])
        agent = self.agent(model)
        with TemporaryDirectory() as directory:
            with RunLog(directory) as log:
                agent.plan("private@example.invalid recognition")
                log.finish(0)
            raw = log.path.read_text(encoding="utf-8")
        self.assertIn("clarification_recheck", raw)
        self.assertNotIn("private@example.invalid", raw)
        event = next(json.loads(line) for line in raw.splitlines() if json.loads(line).get("event") == "structured_response_repair")
        self.assertEqual(event["received"]["clarification_basis"]["omitted_field_count"], 1)


class SharedCallPathTests(unittest.TestCase):
    def assert_policy(self, model):
        self.assertTrue(model.calls)
        for instructions, _, _ in model.calls:
            self.assertTrue(instructions.startswith(COMMON_POLICY))
            self.assertEqual(instructions.count("ECHO SHARED POLICY"), 1)


    def test_original_separate_planning_call_receives_policy(self):
        model = ObservedModel([planned()])
        agent = OriginalAgent(DATABASE, SCOPE, lambda role: model, "live")
        self.addCleanup(agent.close)
        agent.budget = RunBudget()
        agent.plan(MEDIUM_QUESTION)
        self.assert_policy(model)

    def test_vanilla_independent_classification_receives_policy(self):
        docs = [dict(citation_id=f"test:{i}", source="HR_survey_comments", team="A", date="2026-06-30",
                     dimension="Recognition", response_text="Controlled source example.") for i in range(6)]
        labels = [dict(citation_id=d["citation_id"], label="neutral", quote=d["response_text"],
                       reason="Controlled test label, not a human evaluation.") for d in docs]
        model = ObservedModel([tool_turn("submit_sentiment_batch", {"labels": labels})])
        agent = VanillaAgent(DATABASE, SCOPE, model, "live")
        self.addCleanup(agent.close)
        agent.sentiment_documents, agent.budget = docs, RunBudget()
        self.assertEqual(agent.analyze_sentiment("Recognition")["classified_comments"], 6)
        self.assert_policy(model)




if __name__ == "__main__":
    unittest.main()
