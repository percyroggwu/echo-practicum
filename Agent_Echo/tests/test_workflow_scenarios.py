"""Key end-to-end workflow guarantees, scripted in the current protocol (submit_answer, review-v8).

Each scenario runs the real Original, Cherry, Vanilla, Lime and ZeroSugar classes over the
offline database with the scripted demo model, and changes only the reviewer judgment or the
transport under test. Scripted judgments are not accuracy evidence.
"""

from pathlib import Path
import tempfile
import unittest

from agents import AccessScope
from agents.model import ScriptedDemoModel
from agents.original import OriginalAgent, MAX_DRAFTS

DATABASE = Path(__file__).resolve().parents[1] / "data" / "echo.db"
SCOPE = AccessScope("M14", "2024-10-01", "2026-09-30")
QUESTION = "Show quarterly recognition survey metrics and anonymous comment examples."


def contradict_first(value):
    """A support review that fails the first assertion, so the draft must be revised."""
    first = value["assertions"][0]
    first.update(assessment="contradicted", problem="The cited source does not state this.")
    return value


class ScenarioModel(ScriptedDemoModel):
    """The demo model, with the reviewer's support judgment and provider failures injectable."""

    def __init__(self, name, log, support=None, fail_role=None):
        super().__init__(name)
        self.log, self.support, self.fail_role = log, support, fail_role

    def respond(self, instructions, history, tools, require_tool=False):
        tool = tools[0]["name"] if tools else None
        self.log.append((self.agent_name, tool))
        if self.agent_name == self.fail_role:
            raise RuntimeError("Model provider request failed: http 503")
        turn = super().respond(instructions, history, tools, require_tool)
        if tool == "submit_support_review" and self.support:
            import json
            call = turn.calls[0]
            value = self.support(json.loads(call.arguments), sum(1 for a, t in self.log if t == tool))
            call.arguments = json.dumps(value)
            turn.output_items[0]["arguments"] = call.arguments
        return turn


class WorkflowScenarios(unittest.TestCase):
    def run_workflow(self, support=None, fail_role=None, model_call_limit=32):
        log = []
        with tempfile.TemporaryDirectory() as cache:
            agent = OriginalAgent(DATABASE, SCOPE, lambda name: ScenarioModel(name, log, support, fail_role),
                                  "offline-scripted-demo", retrieval="lexical", cache_root=Path(cache),
                                  model_call_limit=model_call_limit)
            try:
                result = agent.run(QUESTION)
            finally:
                agent.close()
        return result, log

    @staticmethod
    def count(log, tool):
        return sum(1 for _, name in log if name == tool)

    def test_complete_workflow_delegates_and_always_verifies(self):
        result, log = self.run_workflow()
        roles = {role for role, _ in log}
        self.assertTrue({"Original", "Cherry", "Vanilla", "ZeroSugar"} <= roles)
        self.assertEqual((result.status, result.verification["decision"]), ("complete", "accept"))
        self.assertEqual(self.count(log, "submit_completeness_review"), 1)
        self.assertEqual(self.count(log, "submit_support_review"), 1)

    def test_rejected_draft_is_repaired_and_reviewed_again(self):
        result, log = self.run_workflow(support=lambda value, n: contradict_first(value) if n == 1 else value)
        self.assertEqual((result.status, result.verification["decision"]), ("complete", "accept"))
        self.assertEqual(result.verification["drafts_checked"], 2)
        self.assertEqual(self.count(log, "submit_support_review"), 2)

    def test_always_rejected_drafts_stop_at_the_limit_and_are_not_released_as_complete(self):
        result, log = self.run_workflow(support=lambda value, n: contradict_first(value))
        self.assertNotEqual(result.status, "complete")
        self.assertNotEqual(result.verification["decision"], "accept")
        self.assertEqual(self.count(log, "submit_support_review"), MAX_DRAFTS)

    def test_partial_release_withholds_the_contradicted_finding(self):
        failing = {}

        def support(value, n):
            failing["id"] = value["assertions"][0]["finding_id"]
            return contradict_first(value)
        result, _ = self.run_workflow(support=support)
        self.assertEqual(result.status, "partial")
        self.assertNotIn(failing["id"], result.verification.get("released_finding_ids", []))

    def test_call_budget_stops_the_workflow_without_an_unreviewed_release(self):
        result, log = self.run_workflow(support=lambda value, n: contradict_first(value), model_call_limit=14)
        self.assertNotEqual(result.status, "complete")
        self.assertLess(self.count(log, "submit_support_review"), MAX_DRAFTS)
        self.assertEqual(result.failure.get("error_category"), "workflow_call_limit")

    def test_reviewer_provider_failure_is_not_turned_into_an_accepted_answer(self):
        result, log = self.run_workflow(fail_role="ZeroSugar")
        self.assertNotEqual(result.status, "complete")
        self.assertNotEqual(result.verification.get("decision"), "accept")
        self.assertEqual(self.count(log, "submit_support_review"), 0)


if __name__ == "__main__":
    unittest.main()
