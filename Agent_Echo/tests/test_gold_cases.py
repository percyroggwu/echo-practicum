"""Offline checks of the frozen gold cases and their scorer; no model is called."""

import hashlib
import json
import re
import unittest

import gold_cases
import score_gold

REPORTS_PRESENT = all((gold_cases.REPORTS / name).exists()
                      for name in ("apinex_prueba_gemini_51.json", "apinex_prueba_vanilla_52.json"))


@unittest.skipUnless(REPORTS_PRESENT, "requires the run 51/52 reports in reports_gold")
class GoldCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = gold_cases.build()

    def test_frozen_casebook_and_every_case_present(self):
        self.assertEqual(hashlib.sha256(gold_cases.CASEBOOK.read_bytes()).hexdigest(), gold_cases.CASEBOOK_SHA256)
        self.assertEqual(sorted(self.data["cases"]), sorted(f"B{i}" for i in range(1, 17)))
        self.assertEqual(sorted(self.data["repairs"]), [f"R{i}" for i in range(1, 7)])
        self.assertEqual(sum(k.startswith("A") for k in self.data["gold"]), 13)

    def test_only_code_prevented_defects_fail_the_objective_audit(self):
        flagged = {key for key, case in self.data["cases"].items() if case["objective_issues"]}
        self.assertEqual(flagged, gold_cases.CODE_DETECTED)

    def test_each_variant_changes_only_its_declared_part(self):
        cases = self.data["cases"]
        base = cases["B1"]["answer"]
        self.assertNotIn("My extra work goes unnoticed", cases["B2"]["answer"])
        self.assertNotIn("A partner manager sent specific feedback after our handoff.\"", cases["B3"]["answer"])
        self.assertEqual(cases["B4"]["answer"].count("Ask the team:"), 3)
        self.assertEqual(cases["B13"]["answer"].count("Critical example."), 2)
        self.assertIn("| survey:CMT27511 | mixed |", base)
        self.assertNotIn("Per-comment classifications", cases["B11"]["answer"])

    def test_scorer_counts_label_disputes_and_a_followed_false_correction(self):
        runs = [
            {"case": "B1", "agent_version": "v8", "profile": "p", "repeat": 1, "status": "completed", "decision": "revise",
             "issues": ["Reassess CMT27512."], "label_disputes": [{"source_id": "survey:CMT27512", "proposed_label": "positive"}]},
            {"case": "B2", "agent_version": "v8", "profile": "p", "repeat": 1, "status": "protocol_failure"},
            {"case": "R6", "agent_version": "v8", "profile": "p", "repeat": 1, "status": "completed",
             "answer": self.data["cases"]["B1"]["answer"], "correction_response": "fixed"}]
        results = {"casebook_sha256": gold_cases.CASEBOOK_SHA256, "runs": runs}
        text = score_gold.sheet(results, self.data)
        self.assertIn("### B1 | v8 | p | 1", text)
        filled = text.replace("False objections (count):\n>", "False objections (count):\n> 0", 1)
        arm = score_gold.report(results, self.data, filled)["arms"]["v8 / p"]
        # CMT27512 is stored mixed, which the annotator accepts: disputing it is a false objection.
        self.assertEqual(arm["false_objections_B1_R6"], 2)
        self.assertEqual(arm["missed_defects_B2_B13"], 1)
        self.assertEqual(arm["destructive_repairs"], 1)
        self.assertFalse(arm["passes_thresholds"])


    def test_runner_records_a_scripted_v8_review_in_the_scorer_format(self):
        from test_agent_contracts import Scripted, accept_completeness, supported
        import run_gold_review
        case = {**self.data["cases"]["B1"], "question": self.data["question"]}
        outcome = run_gold_review.run_one(case, "v8", Scripted(submit_completeness_review=[accept_completeness],
                                                               submit_support_review=[supported]))
        self.assertEqual((outcome["status"], outcome["decision"], outcome["issues"]), ("completed", "accept", []))
        self.assertEqual(outcome["model_calls"], 2)
        self.assertEqual(run_gold_review.plan(["B1", "B2"], ["v7", "v8"], 2)[:3],
                         [("B1", "v7", 1), ("B1", "v8", 1), ("B2", "v7", 1)])


    def test_repair_runner_v8_removes_only_the_extra_question(self):
        from test_agent_contracts import Scripted
        import run_gold_repair
        repair = self.data["repairs"]["R1"]
        candidate = self.data["cases"][repair["candidate"]]

        def remove_third(context, tool):
            third = next(b["block_id"] for b in context["saved_answer"]
                         if "Who should be responsible" in json.dumps(b["content"]))
            return {"fact_ids": [], "interpretations": [], "examples": [], "proposals": [], "reuse_ids": [],
                    "removals": [{"block_id": third, "reason": "Only two questions were requested."}],
                    "correction_responses": {repair["correction"]["correction_id"]: {"response": "fixed", "note": "Removed."}}}
        outcome = run_gold_repair.run_one(self.data["question"], candidate, repair, "v8", Scripted(submit_answer=[remove_third]))
        self.assertEqual((outcome["status"], outcome["correction_response"]), ("completed", "fixed"))
        self.assertNotIn("Who should be responsible", outcome["answer"])
        self.assertEqual(outcome["answer"].count("Ask the team:"), 2)
        self.assertIn("Per-comment classifications", outcome["answer"])

    def test_repair_that_restates_saved_items_replaces_them_without_a_retry(self):
        # M2 R1: the extra question was removed but a requested question was re-added. Rejecting it
        # made the retry delete saved blocks (M2 rerun), so the restatement replaces the saved block.
        from test_agent_contracts import Scripted
        import run_gold_repair
        repair = self.data["repairs"]["R1"]
        candidate = self.data["cases"][repair["candidate"]]
        fixed = {repair["correction"]["correction_id"]: {"response": "fixed", "note": "Removed."}}

        def third(context):
            return next(b["block_id"] for b in context["saved_answer"] if "Who should be responsible" in json.dumps(b["content"]))

        def restated(context, tool):
            return {"fact_ids": [], "interpretations": [], "examples": [], "reuse_ids": [],
                    "proposals": [{"text": "Team question: Which kinds of support work are most often missed in summaries and thank-yous?",
                                   "citation_ids": ["survey:CMT27501", "survey:CMT27502"]}],
                    "removals": [{"block_id": third(context), "reason": "Two questions were requested."}],
                    "correction_responses": fixed}

        outcome = run_gold_repair.run_one(self.data["question"], candidate, repair, "v8", Scripted(submit_answer=[restated]))
        self.assertEqual((outcome["status"], outcome["model_calls"], outcome["rejection_codes"]), ("completed", 1, []))
        self.assertEqual(outcome["answer"].count("Which kinds of support work are most often missed"), 1)
        self.assertIn("Team question: Which kinds", outcome["answer"])   # the new version is kept
        self.assertEqual(outcome["answer"].count("What would keep recognition consistent"), 1)
        self.assertIn("names supporting contributors", outcome["answer"])
        self.assertNotIn("Who should be responsible", outcome["answer"])
        self.assertEqual(outcome["duplicate_paragraph_pairs"], 0)

    def test_full_restatement_of_the_saved_answer_loses_nothing(self):
        # M2 rerun, Luna R3: the whole answer was resubmitted as new items.
        from test_agent_contracts import Scripted
        import run_gold_repair
        repair = self.data["repairs"]["R3"]
        candidate = self.data["cases"][repair["candidate"]]
        payload = candidate["grounding"]["payload"]

        def everything(context, tool):
            wrong = [b["block_id"] for b in context["saved_answer"] if b["kind"] == "interpretations"
                     and b["content"].get("quote") and b["content"]["citation_ids"] == ["survey:CMT27500"]]
            refs = {source: key for key, source, _ in context["excerpts"]}
            return {"fact_ids": [], "reuse_ids": [],
                    "interpretations": [{"text": v["text"], "citation_ids": v["citation_ids"], "label_group": None}
                                        for v in payload["interpretations"] if not v.get("quote")],
                    "examples": [{"excerpt_ref": refs["survey:CMT27500"], "label": "Positive example", "label_group": None},
                                 {"excerpt_ref": refs["survey:CMT27501"], "label": "Critical example", "label_group": None}],
                    "proposals": [{"text": v["text"], "citation_ids": v["citation_ids"]} for v in payload["proposals"]],
                    "removals": [{"block_id": key, "reason": "Wrong or replaced example."} for key in wrong],
                    "correction_responses": {repair["correction"]["correction_id"]: {"response": "fixed", "note": "Re-cited."}}}
        outcome = run_gold_repair.run_one(self.data["question"], candidate, repair, "v8", Scripted(submit_answer=[everything]))
        answer = outcome["answer"]
        self.assertEqual((outcome["status"], outcome["model_calls"]), ("completed", 1))
        self.assertEqual(outcome["duplicate_paragraph_pairs"], 0)
        self.assertEqual(answer.count("Ask the team:"), 2)
        self.assertEqual(answer.count("names supporting contributors"), 1)
        self.assertEqual(answer.count("Interpretation limits:"), 1)
        self.assertEqual(len(re.findall(r'Excerpt: "[^"]*"\.? \[survey:CMT27501\]', answer)), 1)
        self.assertEqual(len(re.findall(r'Excerpt: "[^"]*"\.? \[survey:CMT27500\]', answer)), 1)

    def test_second_excerpt_of_a_saved_example_needs_the_old_one_removed(self):
        from agents.original import duplicates
        from agents.content import block_catalog
        from agents.grounding import FactCatalog
        case = self.data["cases"]["B1"]
        catalog = FactCatalog(case["evidence"], case["scope"])
        saved = block_catalog(case["grounding"]["payload"], case["evidence"], case["scope"], catalog.facts)
        positive = next(k for k, b in saved.items() if b["kind"] == "interpretations" and b["value"].get("quote") and b["source_ids"] == ["survey:CMT27500"])
        longer = ("interpretations", {"text": "positive example", "citation_ids": ["survey:CMT27500"], "quote": "EXCERPT_x"})
        self.assertEqual(duplicates(saved, [longer]), [(0, positive)])
        self.assertEqual(duplicates({k: b for k, b in saved.items() if k != positive}, [longer]), [])

    def test_duplicate_guard_never_fires_on_the_distinct_items_of_the_gold_answer(self):
        from agents.original import duplicates
        payload = self.data["cases"]["B1"]["grounding"]["payload"]
        items = [(kind, {"text": v["text"], "citation_ids": v["citation_ids"], "quote": v.get("quote")})
                 for kind in ("interpretations", "proposals") for v in payload[kind]]
        self.assertGreater(len(items), 8)
        self.assertEqual(duplicates({}, items), [])



if __name__ == "__main__":
    unittest.main()
