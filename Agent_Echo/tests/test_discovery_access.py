"""Offline checks for Discovery's separate, time-bounded data access."""
import unittest
import sqlite3
from unittest.mock import patch
from pathlib import Path

from agents.data_access import (AccessScope, ScopedData, DiscoveryScope, DiscoveryData,
                                FollowUpScope, FollowUpData)

DB = Path(__file__).resolve().parents[1] / 'data' / 'echo_discovery_v1.db'


class FrozenRosterBoundaryTests(unittest.TestCase):
    def test_termination_on_as_of_date_is_included(self):
        connection = sqlite3.connect(':memory:')
        connection.row_factory = sqlite3.Row
        connection.execute('CREATE TABLE HR_managers (Manager_ID TEXT, Manager_Name TEXT, Primary_Team TEXT)')
        connection.execute("INSERT INTO HR_managers VALUES ('M1', 'Manager', 'Team')")
        connection.execute('CREATE TABLE HR_employees (Employee_ID TEXT, Employee_Name TEXT, Team_Display_Name TEXT, Pilot_Manager_ID TEXT, Hire_Date TEXT, Termination_Date TEXT, Department TEXT, Job_Title TEXT, Job_Level TEXT)')
        connection.executemany('INSERT INTO HR_employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', [
            ('E1', 'One Person', 'Team', 'M1', '2020-01-01', '2026-06-30', 'D', 'Role', 'L'),
            ('E2', 'Two Person', 'Team', 'M1', '2020-01-01', '2026-06-29', 'D', 'Role', 'L'),
            ('E3', 'Three Person', 'Team', 'M1', '2026-07-01', None, 'D', 'Role', 'L'),
        ])
        with patch('agents.data_access.open_source', return_value=connection):
            scoped = DiscoveryData('ignored', DiscoveryScope('M1', '2025-10-01', '2026-06-30'))
            self.assertEqual([p['Employee_ID'] for p in scoped.roster()], ['E1'])
            scoped.close()


class LaterStateProjectionTests(unittest.TestCase):
    def test_july_resolution_and_completion_are_not_visible_in_june(self):
        blocker = {'Blocker_ID': 'BLK1', 'Raised_At': '2026-06-20T10:00:00',
                   'Resolved_By_Employee_ID': 'E1', 'Resolved_At': '2026-07-02T10:00:00',
                   'Days_Blocked': 12, 'Resolution_Note': 'Resolved', 'Blocked_Manager_ID': 'M2'}
        request = {'Work_Request_ID': 'WR1', 'Request_Date': '2026-06-10',
                   'Assigned_Employee_ID': 'E1', 'Requested_By_Manager_ID': 'M2',
                   'Completion_Date': '2026-07-02', 'Status': 'Completed',
                   'Actual_Hours': 7, 'Rework_Hours': 2}

        class Source:
            def execute(self, sql, params=()):
                if sql.startswith('SELECT * FROM OP_dependency_blockers'):
                    return iter([blocker])
                if sql.startswith('SELECT * FROM OP_work_requests'):
                    return iter([request])
                return iter([])

        data = DiscoveryData.__new__(DiscoveryData)
        data.scope = DiscoveryScope('M1', '2025-10-01', '2026-06-30')
        data._source = Source()
        data._own = {'E1'}
        data._roster = [{'Employee_ID': 'E1', 'Employee_Name': 'Own Person'}]
        data._managers = []
        data.sanitize = lambda value: value
        projected = data._project('OP_dependency_blockers', blocker, 'Raised_At', {'E1'})
        for field in ('Resolved_By_Employee_ID', 'Resolved_At', 'Days_Blocked', 'Resolution_Note'):
            self.assertIsNone(projected[field])
        self.assertEqual(projected['employee_ids'], [])
        rows = data.evidence()
        self.assertEqual(rows['OP_dependency_blockers'], [])
        work = rows['OP_work_requests'][0]
        for field in ('Completion_Date', 'Status', 'Actual_Hours', 'Rework_Hours'):
            self.assertIsNone(work[field])


@unittest.skipUnless(DB.exists(), 'discovery_v1 database has not been imported')
class DiscoveryAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = DiscoveryData(DB, DiscoveryScope('M32', '2025-10-01', '2026-06-30'))
        cls.rows = cls.data.evidence()

    @classmethod
    def tearDownClass(cls):
        cls.data.close()

    def test_fixed_range_and_legacy_scope(self):
        for dates in ((None, '2026-06-30'), ('2025-10-01', None),
                      ('2025-10-02', '2026-06-30'), ('2025-10-01', '2026-09-30')):
            with self.assertRaises(ValueError):
                DiscoveryScope('M32', *dates)
        self.assertEqual(AccessScope('M32').end_date, '2026-09-30')
        legacy = ScopedData(DB, AccessScope('M32'))
        self.assertTrue(legacy.structured_tables()['employees'][1])
        legacy.close()

    def test_frozen_active_roster_and_subject_resolution(self):
        roster = self.data.roster()
        self.assertTrue(roster)
        self.assertTrue(all(p['Pilot_Manager_ID'] == 'M32' and p['Hire_Date'] <= '2026-06-30'
                            and (not p['Termination_Date'] or p['Termination_Date'] >= '2026-06-30') for p in roster))
        self.assertIn('E0970', {p['Employee_ID'] for p in roster})
        outside = self.data.resolve_person('E0001')
        self.assertTrue(outside['outside_match'])
        self.assertEqual(outside['own_matches'], [])
        self.assertTrue(self.data.resolve_person('E0970')['own_matches'])
        self.assertGreaterEqual(len(self.data.resolve_team('Data Platforms')), 2)

    def test_dates_recorded_cutoff_and_mention_in_other_record(self):
        for rows in self.rows.values():
            for row in rows:
                if 'event_date' not in row:
                    self.assertNotEqual(row.get('Quarter'), '2026-Q3')
                    continue
                self.assertLessEqual(row['event_date'][:10], '2026-06-30')
                self.assertGreaterEqual(row['event_date'][:10], '2025-10-01')
                self.assertLessEqual(row['recorded_date'][:10], '2026-06-30')
        feedback = self.rows['HR_recognition_feedback']
        self.assertTrue(any('E0970' in r['employee_ids'] and r['Employee_ID'] != 'E0970' for r in feedback))

    def test_thread_beneficiary_is_the_requesting_team(self):
        source = sqlite3.connect(DB)
        requesting = dict(source.execute('SELECT Thread_ID, Requesting_Manager_ID FROM OP_collab_threads'))
        source.close()
        rows = self.rows['OP_collab_threads'] + self.rows['OP_collab_messages']
        thread = lambda row: row.get('Thread_ID') or row['record_id']
        self.assertTrue(any(requesting[thread(r)] == 'M32' for r in rows))  # M32 also asks other teams
        for row in rows:
            self.assertEqual(row['beneficiary_manager_id'], requesting[thread(row)])

    def test_sharing_and_external_privacy(self):
        feedback = self.rows['HR_recognition_feedback']
        self.assertTrue(feedback)
        self.assertTrue(all('Shared_With_Home_Manager' not in r for r in feedback))
        late = self.data._source.execute("""SELECT Interaction_ID FROM HR_recognition_feedback
            WHERE Employee_ID='E0010' AND substr(Interaction_At,1,10)<='2026-06-30'
            AND substr(Share_Recorded_At,1,10)>'2026-06-30' LIMIT 1""").fetchone()
        self.assertIsNotNone(late)
        self.assertFalse(next(r for r in feedback if r['Interaction_ID'] == late[0])['shared_as_of'])
        external = next(p for p in self.data._people if p['Employee_ID'] == 'E0001')
        for rows in self.rows.values():
            for row in rows:
                text = str(row)
                self.assertNotIn(external['Employee_ID'], text)
                self.assertNotIn(external['Employee_Name'], text)

    def test_followup_freezes_roster_and_saved_anchors(self):
        with self.assertRaises(ValueError):
            FollowUpData(DB, FollowUpScope('M32', '2026-07-01', '2026-09-30', ('E0001',), ()))
        with self.assertRaises(ValueError):
            FollowUpScope('M32', '2026-06-30', '2026-09-30', ('E0010',), ())
        ref = next(r['work_refs'][0] for r in self.rows['HR_recognition_feedback']
                   if r['Employee_ID'] == 'E0010' and r['work_refs'])
        followup = FollowUpData(DB, FollowUpScope('M32', '2026-07-01', '2026-09-30', ('E0010',), (ref,)))
        rows = followup.evidence()
        followup.close()
        for table, items in rows.items():
            for row in items:
                if 'employee_ids' in row:
                    self.assertEqual(row['employee_ids'], ['E0010'])
                    if table != 'HR_one_on_ones':
                        self.assertIn(ref, row['work_refs'])


if __name__ == '__main__':
    unittest.main()
