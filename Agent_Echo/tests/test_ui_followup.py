"""T5.2 follow-up endpoint: actions built by code, no model. The answer key is read here only, never by runtime code."""
import csv
import json
import re
import sqlite3
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Echo_UI" / "backend"))

import app  # noqa: E402,F401  (mounts the router and puts Agent_Echo on sys.path)
import actions  # noqa: E402
from agents.data_access import DiscoveryData, DiscoveryScope, open_source  # noqa: E402

DB = ROOT / "Agent_Echo" / "data" / "echo_discovery_v1.db"
KEY = ROOT / "files_discovery_v1_private" / "QA_discovery_v1_answer_key.csv"
OTHER_WORK = {"type": "contribution", "id": "CON-OTHER-WORK"}  # work no source record anchors on


def parse_refs(text):
    return [dict(zip(("type", "id"), item.split(":"))) for item in text.split(";")]


class FollowUpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DB.exists() or not KEY.exists():
            raise unittest.SkipTest("Discovery database or answer key unavailable")
        with KEY.open(encoding="utf-8-sig", newline="") as stream:
            cls.cases = {r["Case_ID"]: r for r in csv.DictReader(stream)}
        cls.source = open_source(DB)

    @classmethod
    def tearDownClass(cls):
        cls.source.close()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.saved = (actions.DB_PATH, actions.RUNS_DIR, actions.DEMO_DECISION_DATE)
        actions.DB_PATH, actions.RUNS_DIR = root / "manager_actions.db", root / "runs"
        self.count = 0

    def tearDown(self):
        actions.DB_PATH, actions.RUNS_DIR, actions.DEMO_DECISION_DATE = self.saved
        self.tmp.cleanup()

    def team(self, manager_id):
        data = DiscoveryData(DB, DiscoveryScope("M32", "2025-10-01", "2026-06-30"))
        try:
            return data.team_manager(manager_id)["team"]
        finally:
            data.close()

    def build(self, case_id, kind_of_action, state="accepted", decided="2026-07-01", beneficiary=None, **decision):
        """Register one code-built action for a hand-built or automatic case and decide it. Returns (manager, key)."""
        case = self.cases[case_id]
        manager, refs = case["Manager_ID"], parse_refs(case["Work_Refs"])
        self.count += 1
        run, kind = f"run_{self.count}", case["Subject_Kind"]
        action = {"action_id": "ACT-1-1", "action_type": kind_of_action, "subject_kind": kind,
                  "subject_id": case["Employee_IDs"] if kind == "person" else manager,
                  "beneficiary_team": self.team(case["Beneficiary_Team"]),
                  "beneficiary_manager_id": beneficiary or case["Beneficiary_Team"],
                  "work_refs": refs + [OTHER_WORK], "recipient": None, "draft_text": "Draft."}
        path = actions.RUNS_DIR / run
        path.mkdir(parents=True)
        (path / "meta.json").write_text(json.dumps({"manager_id": manager}))
        (path / "artifact.json").write_text(json.dumps({"discovery": {"findings": [
            {"finding_id": "DISC-1", "work_refs": refs + [OTHER_WORK], "actions": [action]}]}}))
        actions.register_actions(manager, actions.RegisterRequest(run_id=run))
        key = f"{run}:ACT-1-1"
        if state != "proposed":
            decision = {"work_refs": refs, **decision} if state == "edited" else decision
            actions.DEMO_DECISION_DATE = decided
            actions.decide_action(manager, key, actions.DecisionRequest(state=state, **decision))
        return manager, key

    def follow(self, manager, key):
        return actions.follow_up_actions(manager)["results"][key]

    def rows(self, sql, *params):
        return self.source.execute(sql, params).fetchall()

    def test_p1_a1_and_a4_observed_and_p3_not_yet(self):
        for kind in ("A1", "A4"):
            manager, key = self.build("P1", kind, work_refs=None)
            result = self.follow(manager, key)
            self.assertEqual((result["status"], result["action_type"]), ("observed", kind), result)
            self.assertTrue(result["matched"])
            self.assertEqual(result["window"], {"start": "2026-07-01", "end": "2026-09-30"})
            self.assertEqual(result["coverage"]["quarters"], {"2026-Q3": "complete"})
            self.assertNotIn("Author_Name", json.dumps(result))  # ids only, no names or quotes
        manager, key = self.build("P3", "A2")
        result = self.follow(manager, key)
        self.assertEqual(result["status"], "not_yet", result)
        self.assertEqual(result["matched"], [])

    def test_a4_matches_the_beneficiary_manager_not_the_team_name(self):
        case = self.cases["P1"]
        real = case["Beneficiary_Team"]
        # Prefer a manager whose team has the same name; any other manager still proves the match is by ID.
        other = self.rows("""SELECT Manager_ID FROM HR_managers WHERE Manager_ID NOT IN (?, ?) ORDER BY
            Primary_Team = (SELECT Primary_Team FROM HR_managers WHERE Manager_ID=?) DESC, Manager_ID""",
                          real, case["Manager_ID"], real)[0][0]
        manager, key = self.build("P1", "A4", beneficiary=other)
        self.assertEqual(self.follow(manager, key)["status"], "not_yet")

    def test_empty_table_under_complete_coverage_is_not_yet(self):
        # P3 has no feedback row for its work in the window, and M32 declares the source complete.
        case = self.cases["P3"]
        self.assertEqual(self.rows("""SELECT 1 FROM HR_recognition_feedback WHERE Employee_ID=? AND Incident_ID=?
            AND substr(Interaction_At,1,10)>='2026-07-01'""", case["Employee_IDs"], "INC001840"), [])
        self.assertEqual(self.rows("""SELECT Coverage_Status FROM OP_source_coverage WHERE Home_Manager_ID='M32'
            AND Source_Table='HR_recognition_feedback' AND Quarter='2026-Q3'""")[0][0], "complete")
        manager, key = self.build("P3", "A2")
        self.assertEqual(self.follow(manager, key)["status"], "not_yet")

    def test_proposed_action_is_pending_decision(self):
        manager, key = self.build("P1", "A1", state="proposed")
        result = self.follow(manager, key)
        self.assertEqual((result["status"], result["matched"], result["window"], result["coverage"]),
                         ("pending_decision", [], None, None))

    def test_share_before_the_decision_does_not_close_a4(self):
        case = self.cases["P1"]
        shared = self.rows("""SELECT MIN(substr(Shared_With_Home_Manager_At,1,10)) FROM HR_recognition_feedback
            WHERE Employee_ID=? AND (Thread_ID='THR012784' OR Blocker_ID='BLK003068')
            AND substr(Shared_With_Home_Manager_At,1,10)>='2026-07-01'""",
                           case["Employee_IDs"])[0][0]
        self.assertIsNotNone(shared)
        later = self.rows("""SELECT MAX(substr(Shared_With_Home_Manager_At,1,10)) FROM HR_recognition_feedback
            WHERE Employee_ID=? AND (Thread_ID='THR012784' OR Blocker_ID='BLK003068')""", case["Employee_IDs"])[0][0]
        decided = (date.fromisoformat(later) + timedelta(days=1)).isoformat()  # after every share
        self.assertLessEqual(decided, "2026-09-30")
        manager, key = self.build("P1", "A4", decided=decided)
        result = self.follow(manager, key)
        self.assertEqual(result["status"], "not_yet", result)
        self.assertEqual(result["window"]["start"], decided)

    def test_recognition_for_other_work_does_not_close_a1(self):
        case = self.cases["P1"]
        self.assertTrue(self.rows("""SELECT 1 FROM HR_recognition_events WHERE Employee_ID=?
            AND substr(Recognized_At,1,10)>='2026-07-01'""", case["Employee_IDs"]))  # recognition exists, for the blocker
        manager, key = self.build("P1", "A1", state="edited", work_refs=[OTHER_WORK])
        result = self.follow(manager, key)
        self.assertEqual((result["status"], result["matched"]), ("not_yet", []), result)

    def test_partial_coverage_gives_unknown(self):
        self.assertEqual(self.rows("""SELECT Coverage_Status FROM OP_source_coverage WHERE Home_Manager_ID='M41'
            AND Source_Table='HR_recognition_feedback' AND Quarter='2026-Q3'""")[0][0], "partial")
        manager, key = self.build("PL-M41-1", "A4")
        result = self.follow(manager, key)
        self.assertEqual((result["status"], result["matched"]), ("unknown", []), result)
        self.assertEqual(result["coverage"]["quarters"], {"2026-Q3": "partial"})

    def test_a3_matches_only_workload(self):
        rows = self.rows("""SELECT Employee_ID, Topic_Code, One_On_One_ID FROM HR_one_on_ones WHERE Manager_ID='M32'
            AND substr(Meeting_Date,1,10) BETWEEN '2026-07-01' AND '2026-09-30'""")
        workload = {r[0]: [x[2] for x in rows if x[0] == r[0] and x[1] == "workload"] for r in rows}
        quiet = next(e for e, ids in workload.items() if not ids)
        busy = next(e for e, ids in workload.items() if ids)
        results = {}
        for employee in (quiet, busy):
            self.cases["A3-test"] = {"Manager_ID": "M32", "Subject_Kind": "person", "Employee_IDs": employee,
                                     "Beneficiary_Team": "M29", "Work_Refs": "blocker:BLK003068"}
            manager, key = self.build("A3-test", "A3")
            results[employee] = self.follow(manager, key)
        self.assertEqual(results[quiet]["status"], "not_yet", results[quiet])  # other topics do not count
        self.assertEqual((results[busy]["status"], results[busy]["matched"]), ("observed", workload[busy]))

    def test_a5_matches_person_work_and_decision_date(self):
        note = self.source.execute("""SELECT n.* FROM HR_review_notes n JOIN HR_employees e USING(Employee_ID)
            WHERE e.Pilot_Manager_ID='M32' AND n.Note_Date BETWEEN '2026-07-01' AND '2026-09-29'
            AND (n.Contribution_ID IS NOT NULL OR n.Thread_ID IS NOT NULL OR n.Blocker_ID IS NOT NULL OR n.Incident_ID IS NOT NULL)
            ORDER BY n.Note_Date DESC, n.Review_Note_ID LIMIT 1""").fetchone()
        self.assertIsNotNone(note)
        refs = [{"type": column.removesuffix("_ID").lower(), "id": note[column]}
                for column in ("Contribution_ID", "Thread_ID", "Blocker_ID", "Incident_ID") if note[column]]
        self.cases["A5-test"] = {"Manager_ID": "M32", "Subject_Kind": "person", "Employee_IDs": note["Employee_ID"],
                                 "Beneficiary_Team": "M29", "Work_Refs": ";".join(r["type"] + ":" + r["id"] for r in refs)}
        manager, key = self.build("A5-test", "A5")
        result = self.follow(manager, key)
        self.assertEqual((result["status"], result["coverage"]["source_table"]), ("observed", "HR_review_notes"))
        self.assertIn(note["Review_Note_ID"], result["matched"])
        # A different work anchor cannot be closed by this person's review note.
        manager, key = self.build("A5-test", "A5", state="edited", work_refs=[OTHER_WORK])
        self.assertEqual(self.follow(manager, key)["status"], "not_yet")
        # Choosing a decision after every matching note excludes all of them.
        anchors = " OR ".join(column + "=?" for column in ("Contribution_ID", "Thread_ID", "Blocker_ID", "Incident_ID"))
        last = self.rows("SELECT MAX(Note_Date) FROM HR_review_notes WHERE Employee_ID=? AND (" + anchors + ")",
                         note["Employee_ID"], *[note[column] for column in ("Contribution_ID", "Thread_ID", "Blocker_ID", "Incident_ID")])[0][0]
        later = (date.fromisoformat(last[:10]) + timedelta(days=1)).isoformat()
        self.assertLessEqual(later, "2026-09-30")
        manager, key = self.build("A5-test", "A5", decided=later)
        self.assertEqual(self.follow(manager, key)["status"], "not_yet")

    def test_a2_observes_feedback_for_matching_person_work_and_partner(self):
        feedback = self.source.execute("""SELECT f.* FROM HR_recognition_feedback f JOIN HR_employees e USING(Employee_ID)
            WHERE e.Pilot_Manager_ID='M32' AND f.Author_Manager_ID IS NOT NULL AND f.Author_Manager_ID <> 'M32'
            AND substr(f.Interaction_At,1,10) BETWEEN '2026-07-01' AND '2026-09-30'
            AND (f.Contribution_ID IS NOT NULL OR f.Thread_ID IS NOT NULL OR f.Blocker_ID IS NOT NULL OR f.Incident_ID IS NOT NULL)
            ORDER BY f.Interaction_ID LIMIT 1""").fetchone()
        self.assertIsNotNone(feedback)
        refs = [{"type": column.removesuffix("_ID").lower(), "id": feedback[column]}
                for column in ("Contribution_ID", "Thread_ID", "Blocker_ID", "Incident_ID") if feedback[column]]
        self.cases["A2-test"] = {"Manager_ID": "M32", "Subject_Kind": "person", "Employee_IDs": feedback["Employee_ID"],
                                 "Beneficiary_Team": feedback["Author_Manager_ID"],
                                 "Work_Refs": ";".join(r["type"] + ":" + r["id"] for r in refs)}
        manager, key = self.build("A2-test", "A2")
        result = self.follow(manager, key)
        self.assertEqual(result["status"], "observed")
        self.assertIn(feedback["Interaction_ID"], result["matched"])
        manager, key = self.build("A2-test", "A2", beneficiary="M32")
        self.assertEqual(self.follow(manager, key)["status"], "not_yet")
    def test_a6_matches_home_manager_partner_and_decision_date(self):
        plan = self.source.execute("""SELECT * FROM OP_team_plans WHERE Planning_Manager_ID='M32'
            AND Partner_Manager_ID <> 'M32' AND Plan_Date BETWEEN '2026-07-01' AND '2026-09-29'
            ORDER BY Plan_Date DESC, Team_Plan_ID LIMIT 1""").fetchone()
        self.assertIsNotNone(plan)
        self.cases["A6-test"] = {"Manager_ID": "M32", "Subject_Kind": "team", "Employee_IDs": "",
                                 "Beneficiary_Team": plan["Partner_Manager_ID"], "Work_Refs": "blocker:BLK003068"}
        manager, key = self.build("A6-test", "A6")
        result = self.follow(manager, key)
        expected = [r[0] for r in self.rows("""SELECT Team_Plan_ID FROM OP_team_plans WHERE Planning_Manager_ID=?
            AND Partner_Manager_ID=? AND Plan_Date BETWEEN '2026-07-01' AND '2026-09-30'""", manager, plan["Partner_Manager_ID"])]
        self.assertEqual(result["status"], "observed")
        self.assertEqual(set(result["matched"]), set(expected))
        self.assertIn(plan["Team_Plan_ID"], result["matched"])
        self.assertEqual(result["coverage"]["source_table"], "OP_team_plans")
        # The home team itself is never a partner match.
        manager, key = self.build("A6-test", "A6", beneficiary="M32")
        self.assertEqual(self.follow(manager, key)["status"], "not_yet")
        last = self.rows("SELECT MAX(Plan_Date) FROM OP_team_plans WHERE Planning_Manager_ID='M32' AND Partner_Manager_ID=?",
                         plan["Partner_Manager_ID"])[0][0]
        later = (date.fromisoformat(last[:10]) + timedelta(days=1)).isoformat()
        self.assertLessEqual(later, "2026-09-30")
        manager, key = self.build("A6-test", "A6", decided=later)
        self.assertEqual(self.follow(manager, key)["status"], "not_yet")

    def test_dismissed_is_not_checked(self):
        manager, key = self.build("P1", "A1", state="dismissed", reason="Not now")
        result = self.follow(manager, key)
        self.assertEqual((result["status"], result["reason"], result["matched"]), ("dismissed", "Not now", []))

    def test_edited_action_uses_the_last_version(self):
        manager, key = self.build("P1", "A1", state="edited", action_type="A5", decided="2026-07-15")
        result = self.follow(manager, key)
        self.assertEqual((result["action_type"], result["window"]["start"]), ("A5", "2026-07-15"))
        self.assertEqual(result["coverage"]["source_table"], "HR_review_notes")

    def test_no_work_refs_is_unknown_with_a_reason(self):
        manager, key = self.build("P1", "A1")
        with actions.connect() as db:
            db.execute("UPDATE action_versions SET work_refs='[]' WHERE action_key=? AND version=1", (key,))
        result = self.follow(manager, key)
        self.assertEqual(result["status"], "unknown")
        self.assertIn("no anchored work", result["reason"])

    def test_store_gains_the_beneficiary_column(self):
        manager, key = self.build("P1", "A4")
        self.assertEqual(actions.list_actions(manager)["actions"][0]["beneficiary_manager_id"], "M29")
        actions.DB_PATH = Path(self.tmp.name) / "old.db"  # a store file from T5.1 has no such column
        old = sqlite3.connect(actions.DB_PATH)
        old.executescript(re.sub(r",[^\n]*\n\s+beneficiary_manager_id TEXT[^\n]*", "", actions.SCHEMA))
        old.execute("INSERT INTO actions VALUES ('r:A','M32','r','A','F','person','E1','Team',NULL,'[]')")
        old.execute("INSERT INTO action_versions VALUES ('r:A',0,'proposed','A1','d','[]',NULL,NULL)")
        old.commit()
        old.close()
        self.assertIsNone(actions.list_actions("M32")["actions"][0]["beneficiary_manager_id"])


if __name__ == "__main__":
    unittest.main()
