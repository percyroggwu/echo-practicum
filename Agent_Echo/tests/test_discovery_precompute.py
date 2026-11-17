import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

from agents.discovery_precompute import build_discovery_index


class DiscoveryPrecomputeTests(unittest.TestCase):
    def test_dated_visibility_and_mentions(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.db'
            output = Path(directory) / 'index.db'
            with closing(sqlite3.connect(source)) as db:
                db.executescript('''
                    CREATE TABLE HR_employees (Employee_ID TEXT PRIMARY KEY, Employee_Name TEXT);
                    INSERT INTO HR_employees VALUES ('E1', 'José Smith');
                    CREATE TABLE HR_recognition_feedback (Interaction_ID TEXT PRIMARY KEY, Employee_ID TEXT,
                      Contribution_ID TEXT, Thread_ID TEXT, Blocker_ID TEXT, Incident_ID TEXT,
                      Interaction_At TEXT, Shared_With_Home_Manager_At TEXT, Share_Recorded_At TEXT, Message TEXT, Recorded_At TEXT);
                    INSERT INTO HR_recognition_feedback VALUES ('F1','E1','C1','T1',NULL,NULL,
                      '2026-06-15','2026-07-01','2026-07-02','JOSE SMITH helped','2026-06-15');
                    INSERT INTO HR_recognition_feedback VALUES ('F2','E1','C2',NULL,NULL,NULL,
                      '2026-06-20',NULL,NULL,'Jose Smith helped','2026-07-05');
                    CREATE TABLE HR_recognition_events (Recognition_ID TEXT PRIMARY KEY, Employee_ID TEXT,
                      Contribution_ID TEXT, Thread_ID TEXT, Blocker_ID TEXT, Incident_ID TEXT, Recognized_At TEXT, Citation_Text TEXT);
                    INSERT INTO HR_recognition_events VALUES ('R1','E1','C1',NULL,NULL,NULL,'2026-07-03','Jose Smith');
                    CREATE TABLE OP_collab_messages (Message_ID TEXT PRIMARY KEY, Sent_At TEXT, Message_Text TEXT, Mentioned_Employee_IDs TEXT);
                    INSERT INTO OP_collab_messages VALUES ('M1','2026-06-10','Jose Smithson; josé smith','E1');
                    CREATE TABLE OP_meeting_mentions (Mention_ID TEXT PRIMARY KEY, Meeting_Date TEXT, Note_Text TEXT, Mentioned_Employee_ID TEXT);
                    CREATE TABLE HR_self_review_items (Item_ID TEXT PRIMARY KEY, Submitted_Date TEXT, Item_Text TEXT);
                    INSERT INTO HR_self_review_items VALUES ('S1','2025-12-01','JOSE SMITH contributed');
                    CREATE TABLE HR_employee_performance (Performance_ID TEXT PRIMARY KEY, Quarter TEXT, Recorded_At TEXT);
                    INSERT INTO HR_employee_performance VALUES ('P1','2026-Q2','2026-07-10');
                    CREATE TABLE OP_team_plans (Team_Plan_ID TEXT PRIMARY KEY, Plan_Date TEXT, Item_Text TEXT);
                    CREATE TABLE HR_review_notes (Review_Note_ID TEXT PRIMARY KEY, Note_Date TEXT, Note_Text TEXT);
                ''')
                db.commit()
            build_discovery_index(source, output)
            with closing(sqlite3.connect(output)) as db:
                june = db.execute("SELECT event_type FROM visibility_events WHERE event_date <= '2026-06-30' AND recorded_date <= '2026-06-30'").fetchall()
                self.assertEqual(june, [('praised',)])
                self.assertEqual(db.execute("SELECT event_date, recorded_date FROM name_mentions WHERE source_id='F2'").fetchone(), ('2026-06-20', '2026-07-05'))
                self.assertEqual(db.execute("SELECT quarter, event_date, recorded_date FROM quarter_keys WHERE source_id='P1'").fetchone(), ('2026-Q2', '2026-07-10', '2026-07-10'))
                self.assertEqual(db.execute("SELECT count(*) FROM visibility_events WHERE event_type='shared'").fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT count(*) FROM visibility_event_anchors WHERE event_type='shared'").fetchone()[0], 2)
                self.assertEqual(db.execute("SELECT event_date, recorded_date FROM visibility_events WHERE event_type='shared'").fetchone(), ('2026-07-01', '2026-07-02'))
                self.assertEqual(db.execute("SELECT match_type FROM name_mentions WHERE source_id='M1' ORDER BY match_type").fetchall(), [('id',), ('name',)])
                self.assertEqual(db.execute("SELECT quarter FROM name_mentions WHERE source_id='S1'").fetchone(), ('2025-Q4',))
            with self.assertRaises(ValueError):
                build_discovery_index(source, source)

    def test_real_database_structure(self):
        source = Path(__file__).resolve().parents[1] / 'data' / 'echo_discovery_v1.db'
        if not source.exists():
            self.skipTest('Discovery database not present')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'index.db'
            build_discovery_index(source, output)
            with closing(sqlite3.connect(output)) as db:
                for table in ('visibility_events', 'name_mentions', 'quarter_keys'):
                    self.assertGreater(db.execute(f'SELECT count(*) FROM {table}').fetchone()[0], 0)
                    self.assertEqual(db.execute(f'SELECT count(*) FROM {table} WHERE event_date IS NULL OR recorded_date IS NULL OR quarter IS NULL').fetchone()[0], 0)
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')


if __name__ == '__main__':
    unittest.main()


