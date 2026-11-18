"""Factual team selection contracts; expectations never enter runtime inputs."""
import csv
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

from agents.data_access import DiscoveryData, DiscoveryScope
from agents.discovery_tools import team_summary


class Data:
    scope = SimpleNamespace(manager_id='M1', start_date='2025-10-01', end_date='2026-06-30')
    manager = {'Primary_Team': 'Home'}

    def __init__(self, rows=None, size=12):
        self.rows, self.size = rows or {}, size

    def roster(self):
        return [{'Employee_ID': f'E{i:04}', 'Employee_Name': f'Person {i}'} for i in range(self.size)]

    def evidence(self):
        return self.rows

    def resolve_team(self, value):
        return [{'manager_id': m, 'team': 'Partner'} for m in ('M2', 'M3') if value in (m, 'Partner')]


def row(table, key, employee='E0000', **extra):
    result = dict(source=table, record_id=key, event_date='2026-06-01', recorded_date='2026-06-01',
                  quarter='2026-Q2', employee_ids=[employee], Employee_ID=employee,
                  beneficiary_manager_id='M2', work_refs=[{'type': 'contribution', 'id': key}])
    result.update(extra)
    return result


class TeamSummaryTests(unittest.TestCase):
    def test_id_order_exclusion_and_plain_facts(self):
        rows = {'HR_employee_performance': [row('HR_employee_performance', f'P{i}', f'E{i:04}', Quarter='2026-Q2', Pulse_Score=1.234+i) for i in range(5)],
                'OP_contributions': [row('OP_contributions', 'C', 'E0007', Contribution_Summary='PRIVATE TEXT External Person', Team_Goal_ID='G')]}
        result = team_summary(Data(rows))
        self.assertEqual(result['lowest'], [f'E{i:04}' for i in range(5)])
        self.assertEqual([l['employee_id'] for l in result['lines']], [f'E{i:04}' for i in range(5,12)])
        self.assertEqual(result['selection_count'], 5)
        line = result['lines'][2]
        self.assertEqual(line['beneficiaries'][0]['contribution'], 1)
        serialized = json.dumps(result['lines'])
        for forbidden in ('1.234', 'Pulse', 'score', 'satisfaction', 'weight', 'PRIVATE TEXT', 'External Person', 'G"'):
            self.assertNotIn(forbidden, serialized)

    def test_small_normal_team_skips_evidence_and_summary(self):
        data = Data(size=10)
        data.evidence = lambda: self.fail('Small team needs no selection evidence')
        result = team_summary(data)
        self.assertEqual(result['lines'], [])
        self.assertEqual(len(result['whole_team']), 10)
        self.assertEqual(result['selection_count'], 0)

    def test_focus_eligible_only_target_only_and_threshold(self):
        rows = {'OP_contributions': [row('OP_contributions', f'C{i}', f'E{i:04}') for i in range(11)]}
        rows['OP_contributions'].append(row('OP_contributions', 'Elsewhere', 'E0000', beneficiary_manager_id='M3'))
        data = Data(rows)
        result = team_summary(data, {'manager_id': 'M2'})
        self.assertEqual(len(result['lines']), 11)
        self.assertEqual(result['selection_count'], 10)
        self.assertEqual(result['lowest'], [])
        self.assertEqual(result['lines'][0]['help_records'], 1)
        self.assertTrue(all(b['manager_id'] == 'M2' for l in result['lines'] for b in l['beneficiaries']))
        rows['OP_contributions'] = rows['OP_contributions'][:10]
        result = team_summary(data, {'manager_id': 'M2'})
        self.assertEqual(len(result['lines']), 10)
        self.assertEqual(len(result['whole_team']), 10)
        self.assertEqual(result['selection_count'], 0)

    def test_counts_deduplicate_signal_types_and_filter_future(self):
        rows = {'OP_contributions': [row('OP_contributions', 'C', Team_Goal_ID='G')],
                'OP_collab_threads': [row('OP_collab_threads', 'T', Work_Request_ID=None)],
                'HR_recognition_feedback': [row('HR_recognition_feedback', 'F', shared_as_of=False), row('HR_recognition_feedback', 'Ffuture', recorded_date='2026-07-01')],
                'HR_self_review_items': [row('HR_self_review_items', 'S', Item_Text='Started independent recovery exercise', Claimed_Goal_ID=None)]}
        line = team_summary(Data(rows))['lines'][0]
        facts = line['beneficiaries'][0]
        self.assertEqual(line['help_records'], 3)
        self.assertEqual(facts['informal_threads'], 1)
        self.assertEqual(facts['partner_feedback'], 1)
        self.assertEqual(facts['shared_feedback'], 0)
        self.assertEqual(line['self_review_unmatched_initiative'], 1)

    def test_all_team_gate_and_privacy(self):
        root = Path(__file__).resolve().parents[1]
        db = root / 'data' / 'echo_discovery_v1.db'
        if not db.exists():
            self.skipTest('Discovery database unavailable')
        with (root.parent / 'files_discovery_v1_private' / 'QA_discovery_v1_answer_key.csv').open(encoding='utf-8-sig', newline='') as stream:
            cases = list(csv.DictReader(stream))
        missing, checked, privacy, p5, p6, focused_missing = 0, 0, 0, 0, 0, 0
        for manager in sorted({c['Manager_ID'] for c in cases}):
            data = DiscoveryData(db, DiscoveryScope(manager, '2025-10-01', '2026-06-30'))
            try:
                result = team_summary(data)
                lines = {l['employee_id']: l for l in result['lines']}
                encoded = json.dumps(result['lines'], ensure_ascii=False)
                # Whole words only: team names such as "Resource Planning" are not a leak.
                privacy += bool(re.search(r'\b(?:Pulse_Score|pulse_score|satisfaction|signal_types|weight|strength|source|Item_Text|Message_Text)\b', encoded))
                for case in cases:
                    if case['Manager_ID'] != manager or case['Kind'] != 'case':
                        continue
                    employees = set(filter(None, re.split(r'[;|]', case['Employee_IDs'])))
                    target = {t['manager_id'] for t in data.resolve_team(case['Beneficiary_Team'])}
                    for employee in employees - set(result['lowest']) - set(result['whole_team']):
                        checked += 1
                        line = lines.get(employee, {})
                        missing += not any(b['help_records'] and b['manager_id'] in target for b in line.get('beneficiaries', []))
                    if case['Case_ID'] == 'P5':
                        p5 += sum(lines[e]['self_review_cross_team'] + lines[e]['self_review_unmatched_initiative'] for e in employees if e in lines)
                    if case['Case_ID'] == 'P6':
                        p6 += sum(b['other_text_mentions'] for e in employees if e in lines for b in lines[e]['beneficiaries'])
                    if case['Case_ID'] == 'P4':
                        targets = data.resolve_team(case['Beneficiary_Team'])
                        for target_team in targets:
                            focused = team_summary(data, {'manager_id': target_team['manager_id']})
                            focused_missing += len(employees - {l['employee_id'] for l in focused['lines']})
                if manager in ('M14', 'M32'):
                    print(f'Summary {manager} estimated_tokens={(len(encoded)+3)//4}')
            finally:
                data.close()
        print(f'Summary gate checked={checked} missing={missing} privacy={privacy} p5={p5} p6={p6} focused_missing={focused_missing}')
        self.assertEqual((missing, privacy, focused_missing), (0, 0, 0))
        self.assertGreater(p5, 0)
        self.assertGreater(p6, 0)
