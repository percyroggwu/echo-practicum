"""Offline prefilter contracts: strict record caps and closing evidence."""
import copy
import json
import unittest
from pathlib import Path
import csv

from agents.discovery_tools import prefilter, _person_items
from test_discovery_signals import SyntheticData, row
from agents.data_access import DiscoveryData, DiscoveryScope
from agents.discovery_tools import _signal_rows


def resolution(kind='person', ids=None):
    return {'status': 'process', 'subject': {'kind': kind, 'employee_ids': ids or ['E1'],
            'manager_id': 'M1', 'team': 'Own team'},
            'period': {'start': '2025-10-01', 'end': '2026-06-30', 'as_of': '2026-06-30'}}


class PrefilterTests(unittest.TestCase):
    def test_invalid_subject_reads_no_evidence(self):
        data = SyntheticData({})
        data.evidence = lambda: self.fail('Read evidence for invalid scope')
        for payload in ({'status': 'declined'}, {'status': 'clarification'}, resolution(ids=['E99'])):
            with self.assertRaises(ValueError):
                prefilter(data, payload)
        payload = resolution()
        payload['subject']['manager_id'] = 'M2'
        with self.assertRaises(ValueError):
            prefilter(data, payload)

    def test_caps_reached_and_input_not_mutated(self):
        rows = {'OP_contributions': [row('OP_contributions', f'C{i}', Contribution_Summary='x' * 700)
                                     for i in range(30)]}
        # The team case has no recorded selection, so its pool is the satisfaction slot (E1 here).
        rows['HR_employee_performance'] = [row('HR_employee_performance', 'P1', Pulse_Score=1, Quarter='2026-Q2')]
        before = copy.deepcopy(rows)
        for kind, ids, cap in [('person', ['E1'], 25), ('people', ['E1', 'E2'], 10),
                               ('team', [f'E{i}' for i in range(1, 16)], 8)]:
            pool = prefilter(SyntheticData(rows), resolution(kind, ids))
            self.assertEqual(len(pool['people'][0]['items']), cap)
            self.assertTrue(pool['caps_hit']['items'])
            self.assertTrue(all(len(item['text']) <= 300 for p in pool['people'] for item in p['items']))
            self.assertNotIn('Pulse_Score', json.dumps(pool))
        self.assertEqual(rows, before)

    def test_closing_state_uses_cutoff_despite_narrow_work_period(self):
        work = row('OP_contributions', 'C1', date='2026-01-10')
        recognition = row('HR_recognition_events', 'R1', date='2026-05-01',
                          work_refs=work['work_refs'], Citation_Text='Already recognized')
        data = SyntheticData({'OP_contributions': [work], 'HR_recognition_events': [recognition]})
        payload = resolution()
        payload['period']['end'] = '2026-03-31'
        pool = prefilter(data, payload)
        self.assertEqual(pool['people'][0]['items'][0]['record_id'], 'R1')
        self.assertEqual(pool['people'][0]['items'][1]['closing_context']['recognition_state'], 'recorded')

    def test_contradicting_shared_and_record_holder_rows_survive_direct_selection(self):
        work = row('OP_contributions', 'C1')
        shared = row('HR_recognition_feedback', 'F1', shared_as_of=True,
                     Employee_ID='E2', work_refs=work['work_refs'], Message='E1 helped; E2 holds the record')
        rows = {'OP_contributions': [work], 'HR_recognition_feedback': [shared]}
        data = SyntheticData(rows)
        items, _, _ = _person_items(data, 'E1', {'Employee_ID': 'E1'}, rows, rows, 8)
        self.assertEqual(items[0]['record_id'], 'F1')
        self.assertEqual(items[0]['details']['Employee_ID'], 'E2')
        self.assertTrue(items[0]['details']['shared_as_of'])

    def test_excerpt_preserves_late_relevant_sentence(self):
        text = ('Unrelated opening. ' * 40) + 'E1 actually resolved the incident.'
        data = SyntheticData({'OP_meeting_mentions': [row('OP_meeting_mentions', 'N1', Note_Text=text)]})
        item = prefilter(data, resolution())['people'][0]['items'][0]
        self.assertIn('E1 actually resolved', item['text'])

    def test_focus_and_pattern_samples_stay_within_bounded_pool(self):
        rows = {'OP_contributions': [row('OP_contributions', 'C1', beneficiary='M2'),
                                    row('OP_contributions', 'C2', beneficiary='M3')]}
        payload = resolution('team', [f'E{i}' for i in range(1, 16)])
        payload['focus_hint'] = {'manager_id': 'M2'}
        pool = prefilter(SyntheticData(rows), payload)
        self.assertEqual(pool['people'][0]['items'][0]['beneficiary_manager_id'], 'M2')
        self.assertTrue(all(p['beneficiary_manager_id'] == 'M2' for p in pool['team_pattern_leads']))
        ids = {i['record_id'] for p in pool['people'] for i in p['items']}
        self.assertTrue(all(s['record_id'] in ids for p in pool['team_pattern_leads'] for s in p['samples']))

    def test_qualifying_work_survives_many_ordinary_formal_goal_records(self):
        ordinary = [row('OP_contributions', f'FORMAL{i}', Work_Request_ID=f'W{i}',
                        Team_Goal_ID=f'G{i}', Contribution_Summary='Ordinary assigned delivery') for i in range(30)]
        hidden = row('OP_contributions', 'HIDDEN', Contribution_Summary='Helped another team informally')
        feedback = row('HR_recognition_feedback', 'THANKS', work_refs=hidden['work_refs'],
                       shared_as_of=False, Record_Coverage='complete', Message='The helper unblocked our release')
        review = row('HR_self_review_items', 'REVIEW', work_refs=[], Item_Text='Created independent prototype service')
        rows = {'OP_contributions': ordinary + [hidden], 'HR_recognition_feedback': [feedback],
                'HR_self_review_items': [review]}
        before = copy.deepcopy(rows)
        data = SyntheticData(rows)
        items, _, _ = _person_items(data, 'E1', {'Employee_ID': 'E1'}, rows, rows, 8)
        self.assertTrue({'HIDDEN', 'THANKS', 'REVIEW'} <= {i['record_id'] for i in items})
        self.assertEqual(len(items), 8)
        self.assertEqual(rows, before)

    def test_pack_decoy_contradictions_in_eight_record_helper(self):
        root = Path(__file__).resolve().parents[1]
        with (root.parent / 'files_discovery_v1_private' / 'QA_discovery_v1_answer_key.csv').open(encoding='utf-8-sig') as stream:
            cases = {r['Case_ID']: r for r in csv.DictReader(stream)}
        data = DiscoveryData(root / 'data/echo_discovery_v1.db', DiscoveryScope('M32', '2025-10-01', '2026-06-30'))
        try:
            roster = {p['Employee_ID']: p for p in data.roster()}
            rows = _signal_rows(data)
            rows['OP_source_coverage'] = data.evidence()['OP_source_coverage']
            for case_id in ('D1', 'D3'):
                case = cases[case_id]
                employee = case['Employee_IDs'].split(';')[0]
                items, _, _ = _person_items(data, employee, roster[employee], rows, rows, 8)
                with self.subTest(case=case_id):
                    expected = set(case['Evidence_IDs'].split(';'))
                    story_items = [i for i in items if i['record_id'] in expected]
                    self.assertTrue(story_items)
                    if case_id == 'D1':
                        self.assertTrue(any(i['source'] == 'HR_recognition_events' for i in story_items))
                        self.assertTrue(any(i['details'].get('shared_as_of') for i in story_items))
                    else:
                        real_name = roster['E0970']['Employee_Name']
                        self.assertTrue(any(real_name in i['text'] for i in story_items))
        finally:
            data.close()


if __name__ == '__main__':
    unittest.main()
