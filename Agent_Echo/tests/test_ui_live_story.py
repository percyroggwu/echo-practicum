"""Live answer card: story fields come only from Echo's own evidence (no database, no model, no network)."""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Echo_UI" / "backend"))

import app  # noqa: E402  (puts Agent_Echo on sys.path)
import offline  # noqa: E402
import presenter  # noqa: E402
from agents.data_access import AccessScope  # noqa: E402

DISCOVERY_DB = ROOT / "Agent_Echo" / "data" / "echo_discovery_v1.db"
SECRET = "QUOTED-COMMENT-TEXT"

CROSS = {"Total_Contributions": 174, "With_Manager_Recognition": 30, "Without_Manager_Recognition": 144, "With_Partner_Feedback": 60,
         "Without_Any_Feedback": 104, "Praise_Reached_Manager": 60, "No_Praise": 104, "Praise_Not_Passed_On": 0,
         "Praised_Not_Recognized": 40, "Unnoticed_Contributions": 104, "Total_Hours": 1500.0, "Unnoticed_Hours": 1183.0,
         "Unnoticed_People": 31, "Top3_Unnoticed_Share_Percent": 20.5, "Own_Team_Contributions": 27, "Own_Team_Recognized_Percent": 18.6}


def finding(number, name, employee, team, **extra):
    return {"finding_id": f"DISC-{number}", "kind": "person", "employee_ids": [employee], "employee_names": [name],
            "beneficiary_team": team, "work_summary": f"{name} rebuilt the renewal forecast.", "why_it_matters": "Renewals depended on it.",
            "visibility_state": "shared", "recognition_state": "not_recognized", "contribution_id": f"C{number}00",
            "contribution_date": "2026-05-12", "evidence_ids": [f"EV{number}"], "work_refs": [{"type": "contribution", "id": f"C{number}00"}],
            "quotes": [{"source_id": "EX1", "text": SECRET}],
            "actions": [{"action_id": f"ACT-{number}-1", "action_type": "A1", "subject_kind": "person", "subject_id": employee,
                         "beneficiary_team": team, "beneficiary_manager_id": "M9", "work_refs": [], "recipient": None,
                         "draft_text": f"Recognition note for {name}."},
                        {"action_id": f"ACT-{number}-2", "action_type": "A2", "subject_id": employee, "beneficiary_team": team,
                         "recipient": {"manager_id": "M9", "name": "Pat Lee"}, "draft_text": "Please share feedback."}], **extra}


def artifact():
    return {
        "question": "How much cross-team work goes unnoticed?", "answer": "Text.", "status": "complete", "mode": "live",
        "scope": {"manager_id": "M14", "start_date": "2026-04-01", "end_date": "2026-06-30"},
        "evidence": [{"citation_id": "SQL1", "metric_id": "cross_team_contributions", "metric_version": 2, "rows": [CROSS]},
                     {"citation_id": "SQL2", "metric_id": "survey_trend", "metric_version": 2, "metric_arguments": {"dimension": "Recognition"},
                      "rows": [{"Team": "Customer Success", "Survey_Date": "2026-03-31", "Responses": 8, "Mean_Score": 3.4, "Favorable_Percent": 62.5},
                               {"Team": "Customer Success", "Survey_Date": "2026-06-30", "Responses": 9, "Mean_Score": 3.9, "Favorable_Percent": 72.22}]}],
        "delegations": [], "next_steps": [],
        "findings": [{"finding_id": "F1", "text": "t", "citation_ids": ["SQL1", "SQL2", "SENT1"], "status": "supported"}],
        "sentiment": {"SENT1": {"rows": [{"Team": "Customer Success", "Survey_Date": "2026-06-30", "Dimension": "Recognition",
                                          "Eligible_Comments": 9, "positive_count": 5, "positive_percent": 55.56,
                                          "negative_count": 2, "negative_percent": 22.22}], "examples": [{"citation_id": "X", "label": SECRET}]}},
        "discovery": {"status": "findings", "period": {"start": "2025-10-01", "end": "2026-06-30"}, "coverage": {"people_reviewed": 8},
                      "subject": {"team": "Customer Success"}, "internal": {"note": SECRET}, "usage": {"calls": 2},
                      "findings": [finding(1, "Ivan Torres", "E1", "Customer Renewals"), finding(2, "Mia Cho", "E2", "Billing",
                                                                                               visibility_state="no_feedback")]},
    }


class LiveStoryTests(unittest.TestCase):
    def test_full_story(self):
        story = presenter.live_story(artifact())
        self.assertEqual(story["story_source"], "echo")
        self.assertEqual(story["headline"], "104 of 174 pieces of help your team gave other teams went unnoticed in Q2 2026.")
        self.assertEqual([t["value"] for t in story["tiles"]], ["104", "1,183 h", "$53k", "40"])
        self.assertEqual(story["tiles"][1]["label"], "of unnoticed work, about 2.3 people's quarter")
        self.assertEqual(story["journey"], {"quarter": "Q2 2026", "steps": [
            {"label": "Helped another team", "value": 174}, {"label": "Praised by that team", "value": 60},
            {"label": "Praise reached you", "value": 60}, {"label": "Recognized by a manager", "value": 30}]})
        triangle = story["triangle"]
        self.assertEqual((triangle["work"]["value"], triangle["feedback"]["value"], triangle["voice"]["value"], triangle["agreement"]),
                         ("174", "17%", "72%", "conflict"))
        self.assertIn("Discovery found Ivan Torres' help to Customer Renewals, not yet recognized.", triangle["note"])
        self.assertEqual(story["impact"][-1], "Discovery found Ivan Torres' help to Customer Renewals, not yet recognized.")
        self.assertTrue(any("$53k" in line for line in story["impact"]) and any("17%" in line and "19%" in line for line in story["impact"]))
        self.assertEqual(story["voice"], {"topic": "Recognition", "responses": 9, "positive": 56, "negative": 22})
        self.assertEqual([w["baseline"] for w in story["watch"]], ["17%", "60%", "72%"])
        self.assertEqual(story["examples"][0], {"employee_id": "E1", "name": "Ivan Torres", "team_helped": "Customer Renewals",
                                                "outcome": "Ivan Torres rebuilt the renewal forecast.", "date": "2026-05-12",
                                                "contribution_id": "C100", "praise_reached_you": True})
        self.assertFalse(story["examples"][1]["praise_reached_you"])
        recognize = [a for a in story["actions"] if a["kind"] == "recognize"]
        self.assertEqual([(a["discovery_action_id"], a["example_id"], a["person"]["id"]) for a in recognize],
                         [("ACT-1-1", "C100", "E1"), ("ACT-2-1", "C200", "E2")])
        self.assertTrue(any(a["kind"] == "plan" for a in story["actions"]))
        self.assertEqual(len(story["next_steps"]), 2)
        self.assertEqual(story["meaning"], [
            "Of 174 pieces of help to other teams in Q2 2026, 30 were recognized by a manager, 40 were praised and the praise "
            "reached you but were not recognized, 0 were praised without the praise reaching you, and 104 got no feedback at all.",
            "The unnoticed work took 1,183 hours across 31 people; the 3 people with the most unnoticed work did 20% of it.",
            "The Recognition survey was 72% favorable on 2026-06-30."])
        self.assertNotIn(SECRET, json.dumps(story))

    def test_unsupported_evidence_is_ignored(self):
        live = artifact()
        live["findings"][0]["status"] = "unsupported"
        story = presenter.live_story(live)
        self.assertFalse({"headline", "tiles", "journey", "triangle", "impact", "watch", "voice"} & set(story))
        self.assertIn("examples", story)  # Discovery is code-checked, not tied to metric findings
        live["findings"][0] = {**live["findings"][0], "status": "supported", "citation_ids": ["SQL2"]}
        story = presenter.live_story(live)
        self.assertNotIn("tiles", story)

    def test_missing_metric_omits_tiles(self):
        live = artifact()
        live["evidence"] = live["evidence"][1:]
        story = presenter.live_story(live)
        self.assertFalse({"headline", "tiles", "journey", "triangle", "watch", "next_steps"} & set(story))
        self.assertTrue(story["examples"] and story["actions"] and story["voice"])
        live["discovery"] = {}
        live["sentiment"] = {}
        self.assertEqual(presenter.live_story(live), {})

    def test_metric_version_one_and_missing_survey(self):
        live = artifact()
        live["evidence"][0]["metric_version"] = 1
        self.assertNotIn("tiles", presenter.live_story(live))
        live = artifact()
        del live["evidence"][1]
        story = presenter.live_story(live)
        self.assertNotIn("triangle", story)
        self.assertEqual(len(story["tiles"]), 4)

    def test_template_steps_replace_echo_repair_note_and_range_label(self):
        live = artifact()
        live["next_steps"] = ["Address the listed unresolved items using retained evidence where available."]
        live["scope"]["start_date"] = "2025-10-01"
        story = presenter.live_story(live)
        self.assertTrue(story["next_steps"][0].startswith("Start with the 40 pieces of praised work"))
        self.assertTrue(story["headline"].endswith("between 2025-10-01 and 2026-06-30."))
        self.assertEqual(story["journey"]["quarter"], "2025-10-01 to 2026-06-30")

    def test_manager_view_has_no_quotes_or_comment_text(self):
        view = app.without_comment_text(artifact())
        self.assertEqual(view["story_source"], "echo")
        self.assertEqual(view["headline"][:6], "104 of")
        discovery = view["discovery"]
        self.assertEqual(set(discovery), {"status", "period", "coverage", "findings"})
        first = discovery["findings"][0]
        self.assertEqual(set(first), {"finding_id", "kind", "employee_ids", "employee_names", "beneficiary_team", "work_summary",
                                     "why_it_matters", "visibility_state", "recognition_state", "contribution_id", "contribution_date",
                                     "evidence_ids", "actions"})
        self.assertEqual(first["employee_names"], ["Ivan Torres"])
        self.assertEqual(set(first["actions"][1]), {"action_id", "action_type", "subject_id", "beneficiary_team", "recipient", "draft_text"})
        self.assertEqual(first["actions"][1]["recipient"], {"manager_id": "M9", "name": "Pat Lee"})
        text = json.dumps(view)
        for banned in (SECRET, "quotes", "internal", "usage", "work_refs"):
            self.assertNotIn(banned, text)

    def test_offline_and_headline_artifacts_are_not_rebuilt(self):
        live = artifact()
        live["headline"] = "Existing."
        self.assertEqual(app.without_comment_text(live)["headline"], "Existing.")
        self.assertNotIn("story_source", app.without_comment_text(live))
        live = artifact()
        live["mode"] = "offline-demo"
        self.assertNotIn("headline", app.without_comment_text(live))
        self.assertNotIn("discovery", app.without_comment_text({**deepcopy(artifact()), "discovery": {"internal": "x"}}))


class SuggestedPromptTests(unittest.TestCase):
    def test_meta_lists_five_prompts(self):
        prompts = app.meta()["suggested_prompts"]
        self.assertEqual(len(prompts), 5)
        self.assertTrue(all(set(p) == {"label", "prompt"} and p["label"] != p["prompt"] for p in prompts))

    def test_each_prompt_uses_its_labels_handler(self):
        for p in offline.SUGGESTED_PROMPTS:
            handler = offline.supported(p["label"])
            self.assertIsNotNone(handler, p["label"])
            self.assertIs(offline.supported(p["prompt"]), handler)
            self.assertFalse(offline.guarded(p["prompt"]))
        self.assertNotEqual(app.recording_key("M14", "a", "b", offline.SUGGESTED_PROMPTS[0]["prompt"]),
                            app.recording_key("M14", "a", "b", offline.SUGGESTED_PROMPTS[0]["label"]))

    @unittest.skipUnless(DISCOVERY_DB.is_file(), "discovery database not built")
    def test_date_in_prompt_is_not_a_teammate_name(self):
        # M03 has teammates named June; "June 30, 2026" in the full prompt must not ask who is meant.
        built = offline.build(DISCOVERY_DB, AccessScope("M03", "2025-10-01", "2026-06-30"), offline.SUGGESTED_PROMPTS[0]["prompt"])
        self.assertEqual(built[0]["status"], "complete")

    @unittest.skipUnless(DISCOVERY_DB.is_file(), "discovery database not built")
    def test_demo_answers_a_full_prompt_and_discovery_carries_code_filled_fields(self):
        scope = AccessScope("M14", "2025-10-01", "2026-06-30")
        artifact_, _ = offline.build(DISCOVERY_DB, scope, offline.SUGGESTED_PROMPTS[4]["prompt"])
        self.assertEqual(artifact_["status"], "complete")
        self.assertIn("headline", artifact_)
        for f in artifact_["discovery"]["findings"]:
            self.assertEqual(len(f["employee_names"]), len(f["employee_ids"]))
            self.assertTrue(all(f["employee_names"]))
            self.assertIn("contribution_id", f)
            self.assertIn("contribution_date", f)
            if f["contribution_id"]:
                self.assertRegex(f["contribution_date"], r"^\d{4}-\d{2}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
