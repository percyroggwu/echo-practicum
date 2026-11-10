"""Offline checks of the M3 planning casebook, its scoring and its runner; no model is called."""

from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
import io
import unittest

import gold_plans
import run_gold_plans
from test_agents import live_fixture, tool_turn


def plan_turn(numbers=False, text=False, sentiment=False, chart=False, metrics=(), question=None, basis=None):
    return tool_turn("submit_plan", {"needs_numbers": numbers, "needs_text": text, "needs_sentiment": sentiment,
                                     "include_chart": chart, "clarification_question": question,
                                     "clarification_basis": basis,
                                     "metrics": [{"metric": m, "dimension": d} for m, d in metrics]})


class ScriptedModel:
    def __init__(self, *turns):
        self.turns = iter(turns)

    def respond(self, instructions, history, tools, require_tool=False):
        return live_fixture(next(self.turns), instructions, history, tools)


class GoldPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = gold_plans.load()
        cls.cases = {c["id"]: c for c in cls.data["cases"]}

    def run_case(self, case_id, *turns):
        case = self.cases[case_id]
        return run_gold_plans.run_one(case, case.get("scope", self.data["default_scope"]), ScriptedModel(*turns))

    def test_casebook_has_the_required_cases(self):
        self.assertEqual(len(self.cases), 14)
        self.assertEqual({k for k, c in self.cases.items() if c.get("hard")}, {"P1", "P10", "P11"})
        self.assertEqual({k for k, c in self.cases.items() if c["expected"].get("clarify")}, {"P12", "P13"})
        self.assertIn("classify each comment", self.cases["P1"]["question"])

    def test_final_plan_passes_and_raw_plan_keeps_the_model_value(self):
        result = self.run_case("P4", plan_turn(numbers=True, chart=True,
                                               metrics=[("survey_trend", "manager support"), ("survey_trend", "Workload")]))
        self.assertEqual((result["status"], result["mismatches"], result["model_calls"]), ("completed", [], 1))
        self.assertIn('"manager support"', result["raw_calls"][0][0]["arguments"])

    def test_run_64_plan_fails_on_numbers_and_chart(self):
        result = self.run_case("P1", plan_turn(numbers=True, text=True, sentiment=True, chart=True,
                                               metrics=[("survey_trend", "Recognition")]))
        self.assertEqual(result["mismatches"], ["needs_numbers", "include_chart", "metrics"])

    def test_kept_clarification_uses_one_call_and_compares_only_clarify(self):
        question = self.cases["P12"]["question"]
        basis = {"missing_field": "task", "missing_detail": "What 'it' and the earlier meeting refer to",
                 "blocking_reason": "No permitted tool has the earlier meeting.", "request_excerpt": question}
        turn = plan_turn(question="What should I compare, and what was discussed?", basis=basis)
        result = self.run_case("P12", turn)
        self.assertEqual((result["status"], result["mismatches"], result["model_calls"]), ("completed", [], 1))

    def test_summary_applies_the_m3_rule(self):
        run = lambda case, miss, status="completed": {"case": case, "repeat": 1, "status": status, "mismatches": miss}
        passing = [run(c, []) for c in self.cases]
        self.assertEqual(gold_plans.summary(passing, self.data["cases"])["result"], "pass")
        one_hard = passing[:-1] + [run("P1", ["needs_numbers"])]
        self.assertEqual(gold_plans.summary(one_hard, self.data["cases"])["hard_cases_failed"], ["P1"])
        self.assertEqual(gold_plans.summary(one_hard, self.data["cases"])["result"], "fail")
        stopped = passing + [run("P2", None, "protocol_failure")]
        self.assertEqual(gold_plans.summary(stopped, self.data["cases"])["result"], "stopped (protocol failure)")

    def test_frozen_hash_ignores_line_endings_but_not_content(self):
        content = gold_plans.CASEBOOK.read_bytes().replace(b"\r\n", b"\n")
        with TemporaryDirectory() as folder:
            copy = Path(folder) / "casebook.json"
            copy.write_bytes(content.replace(b"\n", b"\r\n"))
            self.assertEqual(gold_plans.sha256(copy), gold_plans.PLANS_SHA256)
            copy.write_bytes(content.replace(b'"P14"', b'"P15"'))
            self.assertNotEqual(gold_plans.sha256(copy), gold_plans.PLANS_SHA256)

    def test_dry_run_reports_frozen_and_an_unfrozen_casebook_refuses_a_live_run(self):
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(run_gold_plans.main(["--profile", "apinex_test", "--dry-run"]), 0)
        self.assertIn("28 plans", out.getvalue())
        self.assertIn(": frozen.", out.getvalue())
        # run_gold_plans holds its own copy of PLANS_SHA256 (from-import), so patch it there.
        with mock.patch.object(run_gold_plans, "PLANS_SHA256", "0" * 64), self.assertRaises(SystemExit), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            run_gold_plans.main(["--profile", "apinex_test"])


if __name__ == "__main__":
    unittest.main()
