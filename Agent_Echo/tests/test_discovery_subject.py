import unittest
from types import SimpleNamespace
from agents.discovery_tools import resolve_subject, _key


class Data:
    def __init__(self):
        self.scope = SimpleNamespace(manager_id='M1', start_date='2025-10-01', end_date='2026-06-30')
        self.manager = {'Primary_Team': 'Home'}
        self.people = [{'Employee_ID': i, 'Employee_Name': n, 'Team_Display_Name': 'Home'} for i, n in [('E1', 'Tomás Ruiz'), ('E2', 'Isabel Garcia'), ('E3', 'Isabel Jones'), ('E4', 'Luis Perez')]]
    def roster(self): return self.people
    def resolve_person(self, value):
        matches = [p for p in self.people if _key(value) in (_key(p['Employee_ID']), _key(p['Employee_Name']))]
        return {'own_matches': matches, 'outside_match': _key(value) in ('outside person', 'e9')}
    def resolve_team(self, value):
        return [{'manager_id': mid, 'team': name, 'own_team': mid == 'M1'} for mid, name in [('M1', 'Home'), ('M2', 'Partner'), ('M3', 'Home')] if _key(value) in (_key(mid), _key(name))]
    def evidence(self): raise AssertionError('resolver must not read evidence')


class ResolveTests(unittest.TestCase):
    def setUp(self): self.data = Data()
    def run_plan(self, kind='team', names=None, **kw):
        return resolve_subject(self.data, {'subject_kind': kind, 'subject_names': names or [], **kw})
    def test_team_and_time(self):
        result = self.run_plan(period_hint='last quarter')
        self.assertEqual(result['subject']['kind'], 'team')
        self.assertEqual((result['period']['start'], result['period']['end']), ('2026-01-01', '2026-03-31'))
    def test_people_and_accent(self):
        self.assertEqual(self.run_plan('person', ['tomas'])['subject']['employee_ids'], ['E1'])
        self.assertEqual(self.run_plan('people', ['Tomás Ruiz', 'E4'])['subject']['employee_ids'], ['E1', 'E4'])
    def test_every_supported_people_count_and_uppercase_accent_matching(self):
        self.data.people.append({'Employee_ID': 'E5', 'Employee_Name': 'Fifth Person', 'Team_Display_Name': 'Home'})
        for count in range(2, 6):
            with self.subTest(count=count):
                ids = [f'E{i}' for i in range(1, count + 1)]
                result = self.run_plan('people', ids)
                self.assertEqual(result['status'], 'process')
                self.assertEqual(result['subject']['kind'], 'people')
                self.assertEqual(set(result['subject']['employee_ids']), set(ids))
        result = self.run_plan('person', ['TOMÁS RUIZ'])
        self.assertEqual((result['status'], result['subject']['employee_ids']), ('process', ['E1']))
    def test_ambiguous_and_unknown(self):
        r = self.run_plan('person', ['Isabel'])
        self.assertEqual(r['missing_field'], 'subject')
        self.assertEqual(len(r['clarification_candidates']), 2)
        self.assertEqual(self.run_plan('person', ['unknown'])['status'], 'clarification')
    def test_outside(self):
        for kind, names in [('person', ['outside person']), ('people', ['E1', 'E9']), ('team', ['Partner']), ('other_team', [])]:
            self.assertEqual(self.run_plan(kind, names)['reason_code'], 'subject_out_of_scope')
    def test_focus(self):
        result = self.run_plan(focus_hint='Partner')
        self.assertEqual(result['focus_hint']['manager_id'], 'M2')
        self.assertEqual(result['subject']['kind'], 'team')
    def test_clarification_choice(self):
        r = resolve_subject(self.data, {'subject_kind': 'person', 'subject_names': ['Changed name']}, {'employee_id': 'E2'})
        self.assertEqual(r['subject']['employee_ids'], ['E2'])
        r = resolve_subject(self.data, {'subject_kind': 'people', 'subject_names': ['E4', 'Isabel']}, {'employee_id': 'E3'})
        self.assertEqual(set(r['subject']['employee_ids']), {'E3', 'E4'})
        self.assertEqual(resolve_subject(self.data, {'subject_kind': 'person', 'subject_names': ['X']}, {'employee_id': 'E9'})['status'], 'declined')
    def test_ambiguous_teams_and_focus(self):
        self.assertEqual(self.run_plan('team', ['Home'])['status'], 'clarification')
        self.assertEqual(self.run_plan(focus_hint='Home')['missing_field'], 'focus_hint')
        self.assertEqual(self.run_plan(focus_hint={'manager_id': 'M2'})['focus_hint']['manager_id'], 'M2')
        r = resolve_subject(self.data, {'subject_kind': 'person', 'subject_names': ['Partner']}, {'employee_id': 'E2'})
        self.assertEqual(r['subject']['employee_ids'], ['E2'])

    def test_topic_focus_runs_the_whole_team(self):
        for topic in ('workload', 'Workload', 'after-hours load'):
            with self.subTest(topic=topic):
                result = self.run_plan(focus_hint=topic)
                self.assertEqual((result['status'], result['subject']['kind']), ('process', 'team'))
                self.assertNotIn('focus_hint', result)

    def test_limits_and_dates(self):
        self.assertEqual(self.run_plan('people', ['a', 'b', 'c', 'd', 'e', 'f'])['status'], 'clarification')
        for hint in ('2024-Q1', '2025-Q3', 'Q3 2026'):
            r = self.run_plan(period_hint=hint)
            with self.subTest(hint=hint):
                self.assertEqual((r['status'], r['reason_code']), ('declined', 'period_out_of_scope'))
                self.assertEqual(len(r['next_steps']), 2)
        r = self.run_plan(period_hint='2025-09-01 to 2025-12-31')
        self.assertTrue(r['period']['narrowed_from_hint'])

    def test_period_phrases(self):
        cases = {'Q2': ('2026-04-01', '2026-06-30'), 'q4': ('2025-10-01', '2025-12-31'),
                 'this year': ('2026-01-01', '2026-06-30'), '2026': ('2026-01-01', '2026-06-30'),
                 'last year': ('2025-10-01', '2025-12-31'), 'in June': ('2026-06-01', '2026-06-30'),
                 'november': ('2025-11-01', '2025-11-30'), 'H1 2026': ('2026-01-01', '2026-06-30'),
                 'the first half of 2026': ('2026-01-01', '2026-06-30'), 'last 6 months': ('2026-01-01', '2026-06-30'),
                 'past two quarters': ('2026-01-01', '2026-06-30'), 'since January': ('2026-01-01', '2026-06-30'),
                 'this quarter': ('2026-04-01', '2026-06-30')}
        for hint, expected in cases.items():
            with self.subTest(hint=hint):
                period = self.run_plan(period_hint=hint)['period']
                self.assertEqual((period['start'], period['end']), expected)
                self.assertFalse(period.get('hint_not_applied'))

    def test_unrecognized_period_keeps_the_window_and_says_so(self):
        for hint in ('recently', 'around the reorg'):
            with self.subTest(hint=hint):
                r = self.run_plan(period_hint=hint)
                self.assertEqual(r['status'], 'process')
                self.assertEqual((r['period']['start'], r['period']['end'], r['period']['hint_not_applied']),
                                 ('2025-10-01', '2026-06-30', True))


if __name__ == '__main__': unittest.main()
