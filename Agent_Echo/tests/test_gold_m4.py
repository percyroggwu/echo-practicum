"""Offline checks of the M4 group C cases and runner; no model is called."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from unittest import mock
import io
import json
import unittest

from agents import zero_sugar
from gold_cases import FactCatalog, audit_claims, prepared_reviewer
import gold_m4
import run_gold_m4


class NoModel:
    def respond(self, instructions, history, tools, require_tool=False):
        raise AssertionError("no model call is expected")


@unittest.skipUnless(gold_m4.GOLD_CASES.exists(), "requires reports_gold/cases.json (python gold_cases.py)")
class GoldM4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = gold_m4.build()
        cls.o1 = cls.data["repair_case"]["O1"]

    def test_saved_cases_are_the_built_cases_and_pass_the_objective_audit(self):
        saved = json.loads(gold_m4.OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(saved, json.loads(json.dumps(self.data)))
        for key, case in self.data["review_cases"].items():
            agent = prepared_reviewer(case, gold_m4.DATABASE)
            try:
                issues = agent.audit(case["answer"], case["evidence"], case["visualization"])
                issues += audit_claims(case["claims"], case["answer"], FactCatalog(case["evidence"], case["scope"]),
                                       case["grounding"])
            finally:
                agent.close()
            self.assertEqual(issues, [], key)
        self.assertNotIn("Proposed action:", self.o1["candidate"]["answer"])

    def test_without_arm_removes_exactly_its_line_and_restores_it(self):
        before = {case: getattr(m, name) for case, (m, name, _) in gold_m4.LINES.items()}
        for case, (module, name, text) in gold_m4.LINES.items():
            with gold_m4.patched(case, "without"):
                self.assertEqual(getattr(module, name), "" if text is None else before[case].replace(text, ""))
                without = gold_m4.prompt_sha256(case)
            with gold_m4.patched(case, "with"):
                self.assertEqual(getattr(module, name), before[case])
                self.assertNotEqual(gold_m4.prompt_sha256(case), without)
        self.assertEqual({case: getattr(m, name) for case, (m, name, _) in gold_m4.LINES.items()}, before)

    def test_a_missing_line_is_refused_in_both_arms(self):
        for arm in run_gold_m4.ARMS:
            with mock.patch.object(zero_sugar, "CHART_NOTE", ""), self.assertRaises(ValueError):
                gold_m4.patched("C3", arm)
            text = gold_m4.LINES["C1"][2]
            reduced = zero_sugar.COMPLETENESS_INSTRUCTIONS.replace(text, "")
            with mock.patch.object(zero_sugar, "COMPLETENESS_INSTRUCTIONS", reduced), self.assertRaises(ValueError):
                gold_m4.patched("C1", arm)

    def test_each_line_reaches_its_review_prompt_only_in_the_with_arm(self):
        for case_id in gold_m4.REVIEW_CASES:
            module, name, text = gold_m4.LINES[case_id]
            line = (text or getattr(module, name)).strip("\n- ")
            phase = "completeness" if case_id == "C1" else "support"
            for arm, present in (("with", True), ("without", False)):
                sent = {}
                def deliver(agent, phase_name, instructions, *args):
                    sent[phase_name] = instructions
                    if phase_name == "completeness":
                        return {"corrections": []}
                    raise RuntimeError("scripted stop")
                with mock.patch.object(zero_sugar.ZeroSugarAgent, "deliver", deliver), gold_m4.patched(case_id, arm):
                    run_gold_m4.review_one(self.data["review_cases"][case_id], NoModel())
                self.assertEqual(line in sent[phase], present, (case_id, arm))

    def test_repair_checks_read_citations_from_the_payload(self):
        candidate = self.o1["candidate"]
        payload = deepcopy(candidate["grounding"]["payload"])
        payload["proposals"].append({"text": "Proposed action: ask the team.", "citation_ids": ["survey:CMT27508"]})
        answer = candidate["answer"] + "\n\nProposed action: ask the team. [survey:CMT27508]"
        checks = run_gold_m4.repair_checks(answer, payload, candidate)
        self.assertEqual((len(checks["added_proposals"]), checks["cites_motivating_findings"]), (1, False))
        self.assertEqual(checks["candidate_lines_missing"], [])
        payload["proposals"][-1]["citation_ids"].append("survey:CMT27501")
        self.assertTrue(run_gold_m4.repair_checks(answer, payload, candidate)["cites_motivating_findings"])
        lines = candidate["answer"].splitlines()
        edited = "\n".join(lines[:-1] + [lines[-1] + " [survey:CMT27501]"])
        self.assertEqual(run_gold_m4.repair_checks(edited, payload, candidate)["candidate_lines_missing"], [])
        self.assertEqual(run_gold_m4.repair_checks("\n".join(lines[1:]), None, candidate)["candidate_lines_missing"],
                         [lines[0]])

    def test_sheet_lists_every_run(self):
        runs = [{"kind": "review", "case": "C1", "arm": arm, "repeat": 1, "status": "completed", "decision": "accept",
                 "issues": [], "prompt_sha256": "a" * 64} for arm in run_gold_m4.ARMS]
        runs.append({"kind": "repair", "case": "O1", "arm": "with", "repeat": 1, "status": "completed",
                     "correction_response": "fixed", "added_proposals": [{"text": "x", "citation_ids": ["SENTIMENT1"]}],
                     "cites_motivating_findings": True, "candidate_lines_missing": []})
        text = run_gold_m4.sheet({"profile": "p", "run_id": "r", "cases_sha256": "0" * 64, "arm_order": "with first",
                                  "runs": runs}, self.data)
        for header in ("## C1 with the line", "## C1 without the line", "## O1 repeat 1", "Diagnostic only",
                       "repeats neither B6 team question"):
            self.assertIn(header, text)

    def test_arm_order_dry_run_and_refusal_without_a_frozen_hash(self):
        self.assertEqual([s[2] for s in run_gold_m4.steps(2)[:2]], ["with", "without"])
        self.assertEqual([s[2] for s in run_gold_m4.steps(2, without_first=True)[:2]], ["without", "with"])
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(run_gold_m4.main(["--profile", "apinex_test", "--dry-run", "--without-first"]), 0)
        self.assertIn("8 runs", out.getvalue())
        self.assertIn("without first", out.getvalue())
        self.assertIn(": frozen.", out.getvalue())
        # run_gold_m4 holds its own copy of M4_SHA256 (from-import), so patch it there.
        with mock.patch.object(run_gold_m4, "M4_SHA256", "0" * 64), self.assertRaises(SystemExit), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            run_gold_m4.main(["--profile", "apinex_test"])


if __name__ == "__main__":
    unittest.main()
