"""Independent coordinator regressions for Phase 2 trust and time boundaries."""

from types import SimpleNamespace
from pathlib import Path
import unittest

from agents.data_access import (DiscoveryData, DiscoveryScope, FollowUpData,
                                FollowUpScope, open_source)
from agents.discovery_tools import (lowest_satisfaction, signal_records, team_summary,
                                    prefilter, resolve_subject, selection_audit)


class Phase2BoundaryTests(unittest.TestCase):
    def test_authorship_alone_is_not_a_name_in_someone_elses_text(self):
        from test_discovery_signals import SyntheticData, row
        owner = row("OP_contributions", "C1", employee="E2")
        message = row("OP_collab_messages", "M1", Author_Employee_ID="E1",
                      Message_Text="I helped with the release", work_refs=owner["work_refs"])
        rows = {"OP_contributions": [owner], "OP_collab_messages": [message]}
        types = lambda: {lead["signal_type"] for lead in signal_records(SyntheticData(rows))["E1"]}
        self.assertNotIn("name_in_other_text", types())
        message["Author_Employee_ID"] = "E3"
        message["Mentioned_Employee_IDs"] = "E1"
        self.assertIn("name_in_other_text", types())
        message["Author_Employee_ID"] = "E1"
        self.assertNotIn("name_in_other_text", types())

    def test_p5_contributors_enter_their_own_manager_pools(self):
        database = Path(__file__).resolve().parents[1] / "data" / "echo_discovery_v1.db"
        if not database.exists():
            self.skipTest("Discovery database has not been imported")
        for manager, required in {"M46": {"E0046"}, "M31": {"E0051", "E0066"},
                                  "M01": {"E0074", "E0085"}}.items():
            with self.subTest(manager=manager):
                data = DiscoveryData(database, DiscoveryScope(manager, "2025-10-01", "2026-06-30"))
                try:
                    summary = team_summary(data)
                    available = {line["employee_id"] for line in summary["lines"]}
                    self.assertTrue(required <= available | set(summary["lowest"]) | set(summary["whole_team"]))
                    choices = sorted(required - set(summary["lowest"]) - set(summary["whole_team"]))
                    choices += [e for e in sorted(available) if e not in choices][:max(0, summary["selection_count"] - len(choices))]
                    selected = selection_audit(data, resolve_subject(data, {"subject_kind": "team"}), selected_employee_ids=choices if summary["selection_count"] else None)
                    self.assertTrue(required <= set(selected["selected"]),
                                    f"P5 own-team contributors reached: {len(required & set(selected['selected']))}/{len(required)}")
                finally:
                    data.close()

    def test_goal_measurement_keeps_its_target_in_a_separate_counted_item(self):
        from test_discovery_signals import SyntheticData, row
        from test_discovery_prefilter import resolution
        rows = {"OP_contributions": [row("OP_contributions", "C1", Team_Goal_ID="G1")],
                "OP_team_goals": [row("OP_team_goals", "G1", Team_Goal_ID="G1",
                    employee_ids=[], work_refs=[], Target_Value=90, Target_Direction="increase")],
                "OP_goal_outcomes": [row("OP_goal_outcomes", "O1", Team_Goal_ID="G1",
                    employee_ids=[], work_refs=[], Measured_Value=92)]}
        items = prefilter(SyntheticData(rows), resolution())["people"][0]["items"]
        target = next(i for i in items if i["record_id"] == "G1")
        outcome = next(i for i in items if i["record_id"] == "O1")
        self.assertEqual(target["details"]["Target_Value"], 90)
        self.assertEqual(outcome["details"]["Measured_Value"], 92)
        self.assertEqual(len(items), 3)

    def test_recognition_closing_state_uses_asof_and_the_same_employee(self):
        from test_discovery_signals import SyntheticData, row
        work = row("OP_contributions", "C1", date="2026-01-10")
        recognition = row("HR_recognition_events", "R1", date="2026-05-01",
                          work_refs=work["work_refs"])
        period = {"start": "2026-01-01", "end": "2026-03-31"}
        rows = {"OP_contributions": [work], "HR_recognition_events": [recognition]}
        types = lambda: {lead["signal_type"] for lead in
                         signal_records(SyntheticData(rows), period=period)["E1"]}
        self.assertNotIn("recognition_gap", types())
        recognition["Employee_ID"] = "E2"
        self.assertIn("recognition_gap", types())
        recognition["Employee_ID"] = "E1"
        recognition["event_date"] = recognition["recorded_date"] = "2026-07-01"
        self.assertIn("recognition_gap", types())

    def test_focus_keeps_a_resolved_beneficiary_self_review(self):
        from test_discovery_signals import SyntheticData, row

        class Data(SyntheticData):
            def resolve_team(self, value):
                return [{"manager_id": "M2"}] if value == "Partner" else []

        rows = {"OP_contributions": [row("OP_contributions", "C1")],
                "HR_self_review_items": [row("HR_self_review_items", "S1",
                    Team_Helped="Partner", Item_Text="Helped the partner recover its service", work_refs=[])]}
        self.assertEqual([r["employee_id"] for r in
                          team_summary(Data(rows), focus_hint={"manager_id": "M2"})["lines"]], ["E1"])

    def test_followup_snapshots_the_saved_action_subjects_and_references(self):
        database = Path(__file__).resolve().parents[1] / "data" / "echo_discovery_v1.db"
        if not database.exists():
            self.skipTest("Discovery database has not been imported")
        source = open_source(database)
        self.addCleanup(source.close)
        row = source.execute("""SELECT Contribution_ID, Thread_ID, Blocker_ID, Incident_ID
            FROM HR_recognition_feedback WHERE Employee_ID='E0010'
            AND substr(Interaction_At,1,10)<='2026-06-30'
            AND substr(Shared_With_Home_Manager_At,1,10)>='2026-07-01' LIMIT 1""").fetchone()
        self.assertIsNotNone(row)
        reference = next({"type": field.removesuffix("_ID").lower(), "id": row[field]}
                         for field in row.keys() if row[field])
        people, references = ["E0010"], [reference]
        data = FollowUpData(database, FollowUpScope("M32", "2026-07-01", "2026-09-30",
                                                   people, references))
        self.addCleanup(data.close)
        before = data.evidence()
        self.assertTrue(before["HR_recognition_feedback"])
        people[0] = "E0001"
        references[0]["id"] = "unrelated-work"
        self.assertEqual(data.evidence(), before)

    def test_private_paths_are_rejected_before_they_are_opened(self):
        scope = DiscoveryScope("M32", "2025-10-01", "2026-06-30")
        for path in (Path("../files_discovery_v1_private/answer.csv"),
                     Path(".env"), Path("connections.private.json")):
            with self.assertRaises(ValueError):
                DiscoveryData(path, scope)

    def test_latest_pulse_uses_time_within_the_same_day(self):
        class Data:
            scope = SimpleNamespace(start_date="2025-10-01", end_date="2026-06-30")

            def roster(self):
                return [{"Employee_ID": "E1"}]

            def evidence(self):
                return {"HR_employee_performance": [
                    {"Employee_ID": "E1", "Quarter": "2026-Q2", "Pulse_Score": 1,
                     "record_id": "Z-earlier", "Recorded_At": "2026-06-30T08:00:00",
                     "event_date": "2026-06-30T08:00:00", "recorded_date": "2026-06-30T08:00:00"},
                    {"Employee_ID": "E1", "Quarter": "2026-Q2", "Pulse_Score": 5,
                     "record_id": "A-later", "Recorded_At": "2026-06-30T18:00:00",
                     "event_date": "2026-06-30T18:00:00", "recorded_date": "2026-06-30T18:00:00"},
                ]}

        self.assertEqual(lowest_satisfaction(Data())[0]["pulse_score"], 5)
