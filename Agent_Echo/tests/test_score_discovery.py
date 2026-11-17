"""Scorer contracts: current slots, strict capture validation and section-only reads."""
import unittest

from score_discovery import current_slots, score_artifact, score_selection


class DiscoveryScorerTests(unittest.TestCase):
    def measured(self):
        return {"teams": {"M01": {"selection_count": 1, "summary_ids": ["E2", "E3"], "code_slot": ["E1"]},
                          "M02": {"selection_count": 0, "summary_ids": [], "code_slot": ["E4"]}},
                "plants": [{"manager_id": "M01", "case_id": "PL-1", "employee_ids": ["E2"], "origin": "automatic"},
                           {"manager_id": "M02", "case_id": "PL-2", "employee_ids": ["E4"], "origin": "automatic"}]}

    def test_current_slots_do_not_consult_answer_key_labels(self):
        summary = {"lowest": ["E1"], "whole_team": []}
        self.assertEqual(current_slots(summary, ["E1", "E2"]), {"E1": "satisfaction", "E2": "selection"})
        summary["whole_team"] = ["E1", "E2"]
        self.assertEqual(current_slots(summary, ["E1", "E2"]), {"E1": "whole_team", "E2": "whole_team"})

    def test_selection_capture_measures_code_and_selected_slots_and_misses(self):
        capture = {"teams": [{"manager_id": "M01", "selected_employee_ids": ["E2"]},
                             {"manager_id": "M02", "selected_employee_ids": []}]}
        self.assertEqual(score_selection(capture, self.measured())["automatic_recall"], 1)
        capture["teams"][0]["selected_employee_ids"] = ["E3"]
        result = score_selection(capture, self.measured())
        self.assertEqual((result["status"], result["automatic_recall"]), ("fail", .5))
        self.assertEqual(result["teams"]["M01"]["missed_plants"], ["PL-1"])

    def test_bad_selection_capture_is_refused(self):
        valid = [{"manager_id": "M01", "selected_employee_ids": ["E2"]},
                 {"manager_id": "M02", "selected_employee_ids": []}]
        invalid = [valid[:1], valid + valid[:1], [*valid, {"manager_id": "M99"}]]
        invalid += [[{"manager_id": "M01", "selected_employee_ids": ids}, valid[1]]
                    for ids in ([], ["E2", "E2"], ["E9"], ["E1"], "E2")]
        for rows in invalid:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                score_selection({"teams": rows}, self.measured())

    def test_findings_are_read_only_from_the_published_section(self):
        cases = [{"Manager_ID": "M01", "Case_ID": "P1", "Kind": "case", "Evidence_IDs": "SOURCE-1"}]
        artifact = {"candidate": {"findings": [{"text": "SOURCE-1"}]},
                    "discovery": {"findings": [{"evidence_ids": ["SOURCE-1"]}]}}
        self.assertEqual(score_artifact(artifact, cases, "M01")["status"], "unverified")
        artifact["discovery_section"] = {"rendered": "Sources: SOURCE-10", "finding_ids": ["DISC-1"]}
        self.assertFalse(score_artifact(artifact, cases, "M01")["cases"][0]["observed_in_section"])
        artifact["discovery_section"]["rendered"] = "Sources: SOURCE-1"
        self.assertTrue(score_artifact(artifact, cases, "M01")["cases"][0]["observed_in_section"])


if __name__ == "__main__":
    unittest.main()
