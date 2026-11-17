"""Selection summary table: rare hidden-work facts lead, volume trails, no team names (synthetic data only)."""
from types import SimpleNamespace
import unittest

from agents.discovery import SUMMARY_COLUMNS, summary_table
from agents.discovery_tools import team_summary


class Data:
    scope = SimpleNamespace(manager_id='M1', start_date='2025-10-01', end_date='2026-06-30')
    manager = {'Primary_Team': 'Home'}

    def __init__(self, rows):
        self.rows = rows

    def roster(self):
        return [{'Employee_ID': f'E{i:04}', 'Employee_Name': f'Person {i}'} for i in range(12)]

    def evidence(self):
        return self.rows

    def resolve_team(self, value):
        return [{'manager_id': value, 'team': f'Zebra {value}'}] if str(value).startswith('M') else []


def row(table, key, employee, beneficiary='M2', **extra):
    result = dict(source=table, record_id=key, event_date='2026-06-01', recorded_date='2026-06-01',
                  quarter='2026-Q2', employee_ids=[employee], Employee_ID=employee,
                  beneficiary_manager_id=beneficiary, work_refs=[{'type': 'contribution', 'id': key}])
    result.update(extra)
    return result


class SelectionSummaryTests(unittest.TestCase):
    def setUp(self):
        rows = {
            # E0001: informal thread plus partner praise never shared, for M2.
            'OP_collab_threads': [row('OP_collab_threads', 'T1', 'E0001')],
            'HR_recognition_feedback': [
                row('HR_recognition_feedback', 'F1', 'E0001'),
                row('HR_recognition_feedback', 'F2', 'E0001'),
                # E0002: praise shared. E0003: unshared praise for two different partner teams.
                row('HR_recognition_feedback', 'F3', 'E0002', shared_as_of='2026-06-02'),
                row('HR_recognition_feedback', 'F4', 'E0003', beneficiary='M2'),
                row('HR_recognition_feedback', 'F5', 'E0003', beneficiary='M3')],
            'OP_contributions': [row('OP_contributions', f'C{i}', 'E0004', beneficiary=f'M{2 + i % 2}') for i in range(6)]}
        self.table = summary_table(team_summary(Data(rows))['lines'])
        lines = self.table.splitlines()
        self.columns = lines[0].split('|')
        self.lines = lines
        self.people = {r.split('|')[0]: dict(zip(self.columns, r.split('|'))) for r in lines[1:]}

    def test_header_is_the_declared_columns_and_ids_are_first_in_order(self):
        self.assertEqual(tuple(self.columns), SUMMARY_COLUMNS)
        self.assertEqual(self.columns[0], 'employee_id')
        self.assertEqual(list(self.people), sorted(self.people))
        self.assertEqual(len(self.people), 12)

    def test_unshared_praise_is_counted_per_partner_team_and_in_total(self):
        self.assertEqual(self.people['E0001']['threads_without_request'], '1')
        self.assertEqual(self.people['E0001']['partner_teams_praise_not_shared'], '1')
        self.assertEqual(self.people['E0001']['partner_feedback_not_shared'], '2')
        self.assertEqual(self.people['E0002']['partner_teams_praise_not_shared'], '0')
        self.assertEqual(self.people['E0002']['partner_feedback_not_shared'], '0')
        self.assertEqual(self.people['E0003']['partner_teams_praise_not_shared'], '2')
        self.assertEqual(self.people['E0003']['threads_without_request'], '0')

    def test_volume_columns_follow_the_hidden_work_facts(self):
        order = {name: i for i, name in enumerate(self.columns)}
        for fact in ('threads_without_request', 'partner_teams_praise_not_shared', 'blockers_resolved'):
            for volume in ('help_records', 'partner_teams', 'quarters_with_help'):
                self.assertLess(order[fact], order[volume])
        self.assertEqual(self.people['E0004']['help_records'], '6')
        self.assertEqual(self.people['E0004']['partner_teams'], '2')

    def test_no_team_names_or_forbidden_words_in_the_table(self):
        for forbidden in ('zebra', 'person', 'help_by_team', 'pulse', 'satisfaction', 'score', 'weight',
                          'strength', 'source_text'):
            self.assertNotIn(forbidden, self.table.lower())

    def test_every_row_has_one_value_per_column(self):
        for line in self.lines:
            self.assertEqual(len(line.split('|')), len(SUMMARY_COLUMNS))


if __name__ == '__main__':
    unittest.main()
