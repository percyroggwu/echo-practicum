"""T5.4: the offline demo's Discovery fixtures, called directly (no HTTP, no network, no model)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Echo_UI" / "backend"))

from agents.data_access import AccessScope  # noqa: E402
import actions  # noqa: E402
import offline  # noqa: E402

DISCOVERY_DB = ROOT / "Agent_Echo" / "data" / "echo_discovery_v1.db"
LEGACY_DB = ROOT / "Agent_Echo" / "data" / "echo.db"
RANGE = ("2025-10-01", "2026-06-30")
QUESTION = "Which contributions lack a recognition note?"


def build(question=QUESTION, database=DISCOVERY_DB, manager="M32"):
    return offline.build(database, AccessScope(manager, *RANGE), question)


class OfflineDiscoveryTests(unittest.TestCase):
    def test_m32_has_discovery_events_section_and_actions(self):
        artifact, log = build()
        started = [e for e in log if e["event"] == "agent_started" and e.get("agent") == "Discovery"]
        calls = [e["call"] for e in log if e["event"] == "agent_turn" and e.get("agent") == "Discovery"]
        self.assertEqual((len(started), calls), (1, ["selection", "judgment"]))
        self.assertTrue(any(e["event"] == "agent_finished" and e.get("agent") == "Discovery" for e in log))
        section, discovery = artifact["discovery_section"], artifact["discovery"]
        self.assertTrue(section["present"] and section["checked_by_code"] and not section["reviewed_by_zerosugar"])
        self.assertEqual((section["mode"], discovery["mode"]), ("offline-demo", "offline-demo"))
        self.assertIn("fixed rule, not by a model", section["note"])
        self.assertIn("fixed rule, not by a model", section["rendered"])
        self.assertIn("Checked by code; not reviewed by ZeroSugar", section["rendered"])
        ids = [a["action_id"] for f in discovery["findings"] for a in f["actions"]]
        self.assertTrue(ids)
        self.assertEqual(section["finding_ids"], [f["finding_id"] for f in discovery["findings"]])
        self.assertNotIn(section["rendered"], artifact["answer"])

    def test_actions_register(self):
        artifact, _ = build()
        with tempfile.TemporaryDirectory() as tmp:
            saved = actions.DB_PATH, actions.RUNS_DIR
            actions.DB_PATH, actions.RUNS_DIR = Path(tmp) / "manager_actions.db", Path(tmp) / "runs"
            try:
                run = actions.RUNS_DIR / "run_offline"
                run.mkdir(parents=True)
                (run / "meta.json").write_text(json.dumps({"manager_id": "M32"}))
                (run / "artifact.json").write_text(json.dumps(artifact))
                registered = actions.register_actions("M32", actions.RegisterRequest(run_id="run_offline"))["actions"]
            finally:
                actions.DB_PATH, actions.RUNS_DIR = saved
        expected = {a["action_id"] for f in artifact["discovery"]["findings"] for a in f["actions"]}
        self.assertEqual({a["source_action_id"] for a in registered}, expected)
        self.assertTrue(all(a["state"] == "proposed" for a in registered))

    def test_helped_team_is_a_focus_and_a_comparison_is_declined(self):
        helped = build("Who on my team helped Customer Renewals?")
        self.assertNotEqual((helped or ({},))[0].get("status"), "declined")
        compared, _ = build("How are we doing compared with Customer Renewals?")
        self.assertEqual(compared["status"], "declined")

    def test_out_of_scope_is_declined(self):
        artifact, log = build(f"How is the {other_team()} team doing?")
        self.assertEqual(artifact["status"], "declined")
        self.assertEqual(artifact["task_outcome"], {"status": "declined", "reason_code": "subject_out_of_scope"})
        self.assertEqual(artifact["verification"], {"decision": "declined", "drafts_checked": 0})
        self.assertEqual(set(artifact["guardrail"]), {"rule", "detail", "checked_by"})
        self.assertEqual(artifact["guardrail"]["checked_by"], "code")
        self.assertEqual(len(artifact["next_steps"]), 2)
        self.assertFalse(artifact["discovery_section"]["present"])
        self.assertFalse(any(e.get("agent") == "Discovery" for e in log))
        self.assertEqual(log[-1]["status"], "declined")

    def test_ambiguous_name_asks_for_clarification(self):
        import sqlite3
        db = sqlite3.connect(DISCOVERY_DB.as_uri() + "?mode=ro", uri=True)
        names = [r[0] for r in db.execute("SELECT Employee_Name FROM HR_employees WHERE Pilot_Manager_ID = 'M32'")]
        db.close()
        first = next(n.split()[0] for n in names if sum(m.split()[0] == n.split()[0] for m in names) > 1)
        artifact, log = build(f"What did {first} do for other teams?")
        self.assertEqual(artifact["status"], "needs_clarification")
        self.assertTrue(len(artifact["clarification_candidates"]) > 1)
        self.assertEqual(log[-1]["status"], "needs_clarification")

    def test_legacy_database_is_unchanged(self):
        artifact, log = build(database=LEGACY_DB, manager="M4")
        self.assertEqual(artifact["discovery_section"], offline.NOT_RUN)
        self.assertEqual(artifact["discovery"], {})
        self.assertFalse(any(e.get("agent") == "Discovery" for e in log))

    def test_no_answer_key_is_opened(self):
        source = Path(offline.__file__).read_text(encoding="utf-8").lower()
        self.assertNotIn("answer_key", source)
        self.assertNotIn(".csv", source)


def other_team():
    """A team name held by exactly one manager other than M32."""
    import sqlite3
    db = sqlite3.connect(DISCOVERY_DB.as_uri() + "?mode=ro", uri=True)
    try:
        return db.execute("""SELECT Primary_Team FROM HR_managers GROUP BY Primary_Team
                             HAVING COUNT(*) = 1 AND MAX(Manager_ID) <> 'M32' ORDER BY Primary_Team""").fetchone()[0]
    finally:
        db.close()


if __name__ == "__main__":
    unittest.main()
