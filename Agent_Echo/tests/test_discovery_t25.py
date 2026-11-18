"""T2.5 bounded evidence pool, with recorded selections and synthetic facts only."""
import copy
import json
import unittest

from agents.discovery_tools import prefilter, selection_audit
from test_discovery_signals import SyntheticData, row


class Data(SyntheticData):
    def __init__(self, rows=None, size=15):
        super().__init__(rows or {})
        self.size = size

    def roster(self):
        return [{'Employee_ID': f'E{i}'} for i in range(1, self.size + 1)]

    def resolve_team(self, manager):
        return [{'manager_id': manager, 'team': 'Partner'}]


def resolved(data, kind='team', ids=None, focus=None):
    result = {'status': 'process', 'subject': {'kind': kind,
        'employee_ids': ids if ids is not None else [p['Employee_ID'] for p in data.roster()],
        'manager_id': 'M1'}, 'period': {'start': '2025-10-01', 'end': '2026-06-30', 'as_of': '2026-06-30'}}
    if focus:
        result['focus_hint'] = {'manager_id': focus}
    return result


def pulse_rows():
    return [row('HR_employee_performance', f'P{i}', employee=f'E{i}',
                Quarter='2026-Q2', Pulse_Score=i) for i in range(1, 16)]


class T25Tests(unittest.TestCase):
    def test_normal_explicit_five_plus_five_and_fallback(self):
        data = Data({'HR_employee_performance': pulse_rows()})
        request = resolved(data)
        chosen = ['E10', 'E6', 'E9', 'E8', 'E7']
        audit = selection_audit(data, request, chosen)
        self.assertEqual(audit, {'selected': ['E1', 'E2', 'E3', 'E4', 'E5'] + chosen,
            'lowest': ['E1', 'E2', 'E3', 'E4', 'E5'], 'selection': chosen, 'whole_team': []})
        pool = prefilter(data, request, chosen)
        self.assertEqual(len(pool['people']), 10)
        self.assertTrue(pool['caps_hit']['people'])
        fallback = prefilter(data, request)
        self.assertEqual([p['employee_id'] for p in fallback['people']], audit['lowest'])
        self.assertFalse(fallback['caps_hit']['people'])
        serialized = json.dumps(pool)
        for private in ('Pulse_Score', 'low_satisfaction', 'strongest', 'selection_reason'):
            self.assertNotIn(private, serialized)

    def test_selection_validation(self):
        data = Data({'HR_employee_performance': pulse_rows()})
        for selection in ([], ['E6'] * 5, ['E1', 'E6', 'E7', 'E8', 'E9'],
                          ['E6', 'E7', 'E8', 'E9', 'E99'], 'E6', [[], 'E7', 'E8', 'E9', 'E10']):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                prefilter(data, resolved(data), selection)

    def test_small_teams_all_ten_no_selection(self):
        for size in (1, 10):
            data = Data(size=size)
            self.assertEqual(len(prefilter(data, resolved(data))['people']), size)
            self.assertEqual(selection_audit(data, resolved(data))['whole_team'],
                             sorted(p['Employee_ID'] for p in data.roster()))
            with self.assertRaises(ValueError):
                prefilter(data, resolved(data), ['E1'])

    def test_named_people_have_no_selection(self):
        data = Data()
        for kind, ids in (('person', ['E12']), ('people', ['E7', 'E12'])):
            self.assertEqual(selection_audit(data, resolved(data, kind, ids))['selected'], ids)
            with self.assertRaises(ValueError):
                prefilter(data, resolved(data, kind, ids), ['E6'])

    def test_focus_small_and_large_has_no_satisfaction_slot(self):
        for size in (10, 11):
            data = Data({'HR_employee_performance': pulse_rows(), 'OP_contributions': [
                row('OP_contributions', f'C{i}', employee=f'E{i}') for i in range(1, size + 1)]})
            request = resolved(data, focus='M2')
            if size == 10:
                self.assertEqual(len(prefilter(data, request)['people']), 10)
                self.assertEqual(selection_audit(data, request)['lowest'], [])
            else:
                self.assertEqual(prefilter(data, request)['people'], [])
                chosen = [f'E{i}' for i in range(2, 12)]
                self.assertEqual(selection_audit(data, request, chosen)['selected'], chosen)
                with self.assertRaises(ValueError):
                    prefilter(data, request, chosen[:5])

    def test_item_caps_text_refs_details_and_immutability(self):
        records = {'OP_contributions': [row('OP_contributions', f'C{i}',
            Contribution_Summary='x' * 700, Status='done') for i in range(40)]}
        original = copy.deepcopy(records)
        data = Data(records)
        for kind, ids, cap in (('person', ['E1'], 25), ('people', ['E1', 'E2'], 10),
                               ('team', None, 8)):
            pool = prefilter(data, resolved(data, kind, ids))
            items = next(p['items'] for p in pool['people'] if p['employee_id'] == 'E1') if kind != 'team' else []
            if kind == 'team':
                small = Data(records, size=10)
                pool = prefilter(small, resolved(small))
                items = next(p['items'] for p in pool['people'] if p['employee_id'] == 'E1')
            self.assertEqual(len(items), cap)
            self.assertTrue(pool['caps_hit']['items'])
            self.assertTrue(all(len(i['text']) <= 300 and i['work_refs'] and i['details']['Status'] == 'done' for i in items))
        self.assertEqual(records, original)

    def test_workload_source_and_repetition_context_ignore_history(self):
        records = {'OP_contributions': [row('OP_contributions', f'C{i}', date='2026-06-01') for i in range(20)] +
            [row('OP_contributions', 'EARLIER', date='2025-12-01'),
             row('OP_contributions', 'HISTORY', date='2025-09-01')],
            'OP_activity_weekly': [row('OP_activity_weekly', 'A1', Week_Start='2026-06-01',
                Cross_Team_Hours=20, After_Hours_Minutes=600),
                row('OP_activity_weekly', 'OLD', date='2025-09-01', Cross_Team_Hours=9999)]}
        data = Data(records, size=10)
        person = next(p for p in prefilter(data, resolved(data))['people'] if p['employee_id'] == 'E1')
        self.assertLessEqual(len(person['items']), 8)
        activity = next(i for i in person['items'] if i['record_id'] == 'A1')
        self.assertEqual(activity['details']['After_Hours_Minutes'], 600)
        workload = person['context']['workload']['After_Hours_Minutes']
        self.assertEqual(workload['quarters'][0]['mean'], 600)
        self.assertEqual(workload['provenance']['record_count'], 1)
        quarters = person['context']['help_by_beneficiary'][0]['quarters']
        self.assertEqual([q['quarter'] for q in quarters], ['2025-Q4', '2026-Q2'])
        self.assertNotIn('HISTORY', json.dumps(person))

    def test_focus_evidence_then_linked_closure_and_target_patterns(self):
        target = row('OP_contributions', 'TARGET', beneficiary='M2')
        recognition = row('HR_recognition_events', 'CLOSED', beneficiary='M3',
                          work_refs=target['work_refs'], Citation_Text='Recognized')
        data = Data({'OP_contributions': [target, row('OP_contributions', 'OTHER', beneficiary='M3')],
                     'HR_recognition_events': [recognition]})
        pool = prefilter(data, resolved(data, focus='M2'))
        self.assertEqual(pool['people'][0]['items'][0]['record_id'], 'TARGET')
        self.assertIn('CLOSED', [i['record_id'] for i in pool['people'][0]['items']])
        self.assertTrue(all(p['beneficiary_manager_id'] == 'M2' for p in pool['team_pattern_leads']))


if __name__ == '__main__':
    unittest.main()
