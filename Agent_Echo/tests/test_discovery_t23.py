import unittest
from pathlib import Path
from types import SimpleNamespace

from agents.data_access import DiscoveryData, DiscoveryScope
from agents.discovery_tools import lowest_satisfaction


class SatisfactionSelectionTests(unittest.TestCase):
    def test_default_limit_and_deterministic_ties(self):
        class Data:
            scope = SimpleNamespace(start_date='2025-10-01', end_date='2026-06-30')

            def roster(self):
                return [{'Employee_ID': person} for person in ('E6', 'E5', 'E4', 'E3', 'E2', 'E1')]

            def evidence(self):
                rows = []
                for person, previous, current in [('E1', 5, 2), ('E2', 5, 2), ('E3', 4, 2),
                                                  ('E4', None, 2), ('E5', 5, 3), ('E6', 5, 1)]:
                    for quarter, score, date in [('2026-Q1', previous, '2026-03-20'),
                                                 ('2026-Q2', current, '2026-06-20')]:
                        if score is not None:
                            rows.append({'Employee_ID': person, 'Quarter': quarter, 'Pulse_Score': score,
                                         'recorded_date': date, 'event_date': date})
                return {'HR_employee_performance': rows}

        data = Data()
        self.assertEqual([r['employee_id'] for r in lowest_satisfaction(data)],
                         ['E6', 'E1', 'E2', 'E3', 'E4'])
        self.assertEqual(len(lowest_satisfaction(data, 6)), 6)
        self.assertEqual(lowest_satisfaction(data, 0), [])

    def test_fixed_team_selections(self):
        db = Path(__file__).resolve().parents[1] / 'data' / 'echo_discovery_v1.db'
        for manager, expected in [
            ('M32', ['E2198', 'E0010', 'E1748', 'E2156', 'E1401']),
            ('M14', ['E1183', 'E1209', 'E0450', 'E0885', 'E1088']),
        ]:
            with self.subTest(manager=manager):
                data = DiscoveryData(db, DiscoveryScope(manager, '2025-10-01', '2026-06-30'))
                try:
                    self.assertEqual([r['employee_id'] for r in lowest_satisfaction(data)], expected)
                finally:
                    data.close()


if __name__ == '__main__':
    unittest.main()
