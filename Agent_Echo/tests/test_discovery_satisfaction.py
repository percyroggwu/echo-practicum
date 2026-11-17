import unittest
from pathlib import Path
from types import SimpleNamespace

from agents.data_access import DiscoveryData, DiscoveryScope
from agents.discovery_tools import lowest_satisfaction


class SyntheticData:
    scope = SimpleNamespace(start_date='2025-10-01', end_date='2026-06-30')
    def roster(self):
        return [{'Employee_ID': x} for x in ('E1', 'E2', 'E3', 'E4')]
    def evidence(self):
        def row(person, quarter, score, recorded, event=None):
            return {'Employee_ID': person, 'Quarter': quarter, 'Pulse_Score': score,
                    'recorded_date': recorded, 'event_date': event or recorded}
        return {'HR_employee_performance': [
            row('E1', '2026-Q1', 5, '2026-03-20'), row('E1', '2026-Q2', 2, '2026-06-20'),
            row('E2', '2026-Q1', 4, '2026-03-20'), row('E2', '2026-Q2', 2, '2026-06-20'),
            row('E3', '2025-Q4', 5, '2025-12-20'), row('E3', '2026-Q2', 2, '2026-06-20'),
            row('E4', '2026-Q1', 5, '2026-03-20'), row('E4', '2026-Q2', 2, '2026-06-20'),
            row('E1', '2026-Q2', 1, '2026-07-01', '2026-06-30'),
            row('E1', '2026-Q3', 1, '2026-06-20'),
            row('E9', '2026-Q2', 1, '2026-06-20'),
            row('E2', '2026-Q2', 1, '2026-06-20', '2026-07-01'),
        ]}


class SatisfactionTests(unittest.TestCase):
    def test_ties_missing_previous_dates_and_inactive(self):
        rows = lowest_satisfaction(SyntheticData())
        self.assertEqual([r['employee_id'] for r in rows], ['E1', 'E4', 'E2', 'E3'])
        self.assertEqual([r['change'] for r in rows], [-3, -3, -2, None])
        self.assertIsNone(rows[-1]['previous_score'])
        self.assertEqual(len(lowest_satisfaction(SyntheticData(), 2)), 2)

    def test_m32_real_data(self):
        db = Path(__file__).resolve().parents[1] / 'data' / 'echo_discovery_v1.db'
        data = DiscoveryData(db, DiscoveryScope('M32', '2025-10-01', '2026-06-30'))
        try:
            self.assertEqual([r['employee_id'] for r in lowest_satisfaction(data)],
                             ['E2198', 'E0010', 'E1748', 'E2156', 'E1401'])
        finally:
            data.close()


if __name__ == '__main__':
    unittest.main()
