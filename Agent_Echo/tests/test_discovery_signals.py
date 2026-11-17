"""Offline signal contracts and explicit data-pack acceptance gates."""
import csv
from pathlib import Path
from types import SimpleNamespace
import unittest

from agents.data_access import DiscoveryData, DiscoveryScope
from agents.discovery_tools import signal_records, team_summary, workload_baseline


class SyntheticData:
    scope = SimpleNamespace(manager_id='M1', start_date='2025-10-01', end_date='2026-06-30')
    manager = {'Primary_Team': 'Own team'}
    def __init__(self, rows):
        self.rows = rows
    def roster(self):
        return [{'Employee_ID': f'E{i}'} for i in range(1, 16)]
    def evidence(self):
        return self.rows
    def resolve_team(self, value):
        return [{'manager_id': value, 'team': 'Partner'}] if value else []


def row(table, key, employee='E1', date='2026-06-01', beneficiary='M2', **fields):
    result = {'source': table, 'record_id': key, 'event_date': date, 'recorded_date': date,
              'quarter': f'{date[:4]}-Q{(int(date[5:7])-1)//3+1}', 'employee_ids': [employee],
              'Employee_ID': employee, 'beneficiary_manager_id': beneficiary,
              'work_refs': [{'type': 'contribution', 'id': key}]}
    result.update(fields)
    return result


def valid_rows(employee='E1', beneficiary='M2'):
    return {'OP_contributions': [row('OP_contributions', 'C' + employee, employee, beneficiary=beneficiary)],
            'OP_incident_handoffs': [row('OP_incident_handoffs', 'I' + employee, employee, beneficiary=beneficiary)]}


class SignalContractTests(unittest.TestCase):
    def test_summary_keeps_facts_without_independence_threshold(self):
        summary = team_summary(SyntheticData({'OP_contributions': [row('OP_contributions', 'C1')]}))
        line = next(line for line in summary['lines'] if line['employee_id'] == 'E1')
        self.assertEqual(line['beneficiaries'][0]['contribution'], 1)

    def test_formal_work_is_factual_not_a_coded_rejection(self):
        rows = valid_rows()
        rows['OP_contributions'][0]['Work_Request_ID'] = 'W1'
        line = next(x for x in team_summary(SyntheticData(rows))['lines'] if x['employee_id'] == 'E1')
        self.assertEqual(line['beneficiaries'][0]['contribution'], 1)
        self.assertEqual(line['beneficiaries'][0]['incident_handoff'], 1)

    def test_event_recorded_dates_and_roster(self):
        for changes in ({'event_date': '2026-07-01'}, {'recorded_date': '2026-07-01'},
                        {'employee_ids': ['E99'], 'Employee_ID': 'E99'}):
            rows = valid_rows()
            rows['OP_incident_handoffs'][0].update(changes)
            lines = team_summary(SyntheticData(rows))['lines']
            line = next(x for x in lines if x['employee_id'] == 'E1')
            self.assertEqual(sum(b['incident_handoff'] for b in line['beneficiaries']), 0)
            self.assertNotIn('E99', [x['employee_id'] for x in lines])

    def test_focus_uses_target_only_and_ignores_lowest_exclusion(self):
        rows = valid_rows()
        rows['HR_employee_performance'] = [row('HR_employee_performance', 'P1',
            Quarter='2026-Q2', Pulse_Score=1)]
        data = SyntheticData(rows)
        self.assertNotIn('E1', [x['employee_id'] for x in team_summary(data)['lines']])
        focused = team_summary(data, focus_hint={'manager_id': 'M2'})
        self.assertEqual(focused['whole_team'], ['E1'])
        self.assertEqual(focused['selection_count'], 0)
        self.assertFalse(team_summary(data, focus_hint={'manager_id': 'M3'})['lines'])
        for leads in signal_records(data, {'manager_id': 'M2'}).values():
            self.assertTrue(all(r['beneficiary_manager_id'] == 'M2' for r in leads))

    def test_name_in_text_requires_work_owned_by_someone_else(self):
        rows = valid_rows()
        rows['HR_recognition_feedback'] = [row('HR_recognition_feedback', 'F1',
            Author_Employee_ID='[Other colleague]', shared_as_of=True)]
        leads = signal_records(SyntheticData(rows))['E1']
        self.assertNotIn('name_in_other_text', {r['signal_type'] for r in leads})
        rows['HR_recognition_feedback'][0]['Employee_ID'] = 'E2'
        self.assertIn('name_in_other_text', {r['signal_type'] for r in signal_records(SyntheticData(rows))['E1']})

    def test_repetition_and_workload_stay_in_analysis_period(self):
        rows = valid_rows()
        rows['OP_contributions'].append(row('OP_contributions', 'C0', date='2025-09-01'))
        self.assertNotIn('repetition', {r['signal_type'] for r in signal_records(SyntheticData(rows))['E1']})
        rows['OP_contributions'].append(row('OP_contributions', 'C2', date='2025-12-01'))
        self.assertIn('repetition', {r['signal_type'] for r in signal_records(SyntheticData(rows))['E1']})
        rows['OP_activity_weekly'] = [row('OP_activity_weekly', 'A0', date='2025-09-01',
            Cross_Team_Hours=999, After_Hours_Minutes=999)]
        self.assertEqual(workload_baseline(SyntheticData(rows))['Cross_Team_Hours']['median'], 0)

    def test_shared_state_is_as_of_and_never_legacy_flag(self):
        rows = {'HR_recognition_feedback': [row('HR_recognition_feedback', 'F1',
            shared_as_of=False, Shared_With_Home_Manager='Yes')]}
        self.assertIn('visibility_gap', {r['signal_type'] for r in signal_records(SyntheticData(rows))['E1']})

    def test_self_review_matches_existing_goal_and_does_not_guess_empty_team(self):
        review = row('HR_self_review_items', 'S1', Item_Text='Built the monthly reporting automation',
                     Team_Helped=None, Claimed_Goal_ID=None)
        goal = row('HR_goals', 'G1', Goal_Text='Build monthly reporting automation')
        rows = {'HR_self_review_items': [review], 'HR_goals': [goal]}
        self.assertNotIn('self_review', {r['signal_type'] for r in signal_records(SyntheticData(rows))['E1']})
        review['Item_Text'] = 'Started an unassigned disaster recovery exercise'
        self.assertIn('self_review', {r['signal_type'] for r in signal_records(SyntheticData(rows))['E1']})
        review['Claimed_Goal_ID'] = 'G1'
        self.assertNotIn('self_review', {r['signal_type'] for r in signal_records(SyntheticData(rows))['E1']})

    def test_stable_id_order_and_selection_count(self):
        rows = valid_rows('E2')
        for table, items in valid_rows('E1').items():
            rows[table].extend(items)
        summary = team_summary(SyntheticData(rows))
        ids = [r['employee_id'] for r in summary['lines']]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(summary['selection_count'], 5)
        self.assertEqual(len(ids), 15)


class SignalDataPackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.data = {m: DiscoveryData(cls.root / 'data' / 'echo_discovery_v1.db',
            DiscoveryScope(m, '2025-10-01', '2026-06-30')) for m in ('M32', 'M14')}
    @classmethod
    def tearDownClass(cls):
        for data in cls.data.values():
            data.close()

    def test_m32_focus_retains_every_named_helper(self):
        focused = team_summary(self.data['M32'], focus_hint={'manager_id': 'M16'})
        lines = focused['lines']
        self.assertTrue({'E1401', 'E1586', 'E0561'} <= {r['employee_id'] for r in lines})
        self.assertTrue(all(b['manager_id'] == 'M16' and b['help_records'] > 0
                            for line in lines for b in line['beneficiaries']))

    def test_normal_handbuilt_summary_gate(self):
        expected = {'M32': {'E0728', 'E1586', 'E0561', 'E0970'}, 'M14': {'E0001'}}
        for manager, employees in expected.items():
            with self.subTest(manager=manager):
                lines = team_summary(self.data[manager])['lines']
                self.assertTrue(employees <= {line['employee_id'] for line in lines})
                lookup = {line['employee_id']: line for line in lines}
                if manager == 'M32':
                    self.assertGreater(sum(b['other_text_mentions'] for b in lookup['E0970']['beneficiaries']), 0)
                else:
                    self.assertGreater(lookup['E0001']['self_review_cross_team'] + lookup['E0001']['self_review_unmatched_initiative'], 0)

    def test_automatic_summary_gate_uses_current_code_slot(self):
        # Private expectations stay in evaluation code and never enter runtime prompts.
        key = self.root.parent / 'files_discovery_v1_private' / 'QA_discovery_v1_answer_key.csv'
        with key.open(encoding='utf-8-sig', newline='') as stream:
            cases = list(csv.DictReader(stream))
        for manager, data in self.data.items():
            summary = team_summary(data)
            code = set(summary['lowest']) | set(summary['whole_team'])
            expected = {employee for case in cases if case['Manager_ID'] == manager
                        and case['Origin'] == 'automatic' and case['Kind'] == 'case'
                        for employee in case['Employee_IDs'].split(';') if employee} - code
            lines = {r['employee_id']: r for r in summary['lines']}
            self.assertTrue(expected <= set(lines))
            self.assertTrue(all(sum(b['help_records'] for b in lines[e]['beneficiaries']) > 0 for e in expected))


if __name__ == '__main__':
    unittest.main()
