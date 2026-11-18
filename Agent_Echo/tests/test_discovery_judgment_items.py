"""Offline contracts for the items Discovery's judgment call receives (synthetic data only)."""
import unittest

from agents.discovery_tools import _excerpt, _person_items
from test_discovery_signals import SyntheticData, row

PERSON = {'Employee_ID': 'E1', 'Employee_Name': 'Pat Doe'}


def story_rows():
    """One person, two unshared-praise work items for two partners, each linked to its own goal."""
    blocker = row('OP_dependency_blockers', 'BLK1', beneficiary='M2', date='2025-11-10',
                  work_refs=[{'type': 'blocker', 'id': 'BLK1'}], Blocked_Team_Goal_ID='G1',
                  Blocker_Description='Missing fields stop the feed.', Resolution_Note='Closed with help from Pat Doe.')
    work = row('OP_contributions', 'CON1', beneficiary='M3', date='2026-01-22', Team_Goal_ID='G2',
               Contribution_Summary='Pat Doe explained the review.', Evidence_Description='Accepted a short summary.')
    feedback = [row('HR_recognition_feedback', 'INT1', beneficiary='M2', date='2025-12-07', shared_as_of=False,
                    Record_Coverage='complete', work_refs=blocker['work_refs'], Message='Pat Doe followed through.'),
                row('HR_recognition_feedback', 'INT2', beneficiary='M3', date='2026-01-30', shared_as_of=False,
                    Record_Coverage='complete', work_refs=work['work_refs'], Message='Pat Doe, the review.')]
    goals, outcomes = [], []
    for number, month in (('1', '03'), ('2', '04')):
        goals.append(row('OP_team_goals', f'TGL{number}', beneficiary='M2' if number == '1' else 'M3', date=f'2026-{month}-01',
                         work_refs=[], Team_Goal_ID=f'G{number}', Goal_Text='Reach the target'))
        for k in range(2):
            outcomes.append(row('OP_goal_outcomes', f'GOC{number}{k}', beneficiary='M2' if number == '1' else 'M3',
                                date=f'2026-{month}-1{k + 1}', work_refs=[], Team_Goal_ID=f'G{number}',
                                Measurement_Note='Measured'))
    activity = row('OP_activity_weekly', 'AWK1', work_refs=[], beneficiary=None, Week_Start='2026-06-29', Cross_Team_Hours=2)
    review = row('HR_self_review_items', 'REV1', work_refs=[], beneficiary=None, Item_Text='Other team project')
    return {'OP_dependency_blockers': [blocker], 'OP_contributions': [work], 'HR_recognition_feedback': feedback,
            'OP_team_goals': goals, 'OP_goal_outcomes': outcomes, 'OP_activity_weekly': [activity],
            'HR_self_review_items': [review]}


class ExcerptTests(unittest.TestCase):
    def test_short_text_is_kept_whole(self):
        self.assertEqual(_excerpt('Thanks Pat Doe, all sorted now.', PERSON), 'Thanks Pat Doe, all sorted now.')
        text = 'Missing fields block the feed. Closed after 5 days. Notes from Pat Doe attached.'
        self.assertEqual(_excerpt(text, PERSON), text)

    def test_long_text_without_sentence_break_never_starts_or_ends_mid_word(self):
        text = 'Thanks Pat Doe ' + 'for the careful review of every renewal ' * 20
        out = _excerpt(text, PERSON, limit=100)
        self.assertTrue(out.startswith('Thanks Pat Doe'))
        self.assertLessEqual(len(out), 100)
        self.assertTrue(text.startswith(out[:-1]) and text[len(out)] == ' ')

    def test_late_name_starts_at_a_word_boundary(self):
        text = 'x' * 10 + ' ' + 'filler words ' * 30 + 'and Pat Doe resolved it.'
        out = _excerpt(text, PERSON, limit=100)
        self.assertIn('Pat Doe resolved', out)
        self.assertTrue(out[0].isalpha() and text[text.index(out) - 1] == ' ')


class PersonItemsTests(unittest.TestCase):
    def items(self, cap=8):
        rows = story_rows()
        return _person_items(SyntheticData(rows), 'E1', PERSON, rows, rows, cap)[0]

    def test_unshared_praise_and_work_for_both_partners_beat_a_second_goal(self):
        ids = [i['record_id'] for i in self.items()]
        self.assertTrue({'BLK1', 'CON1', 'INT1', 'INT2'} <= set(ids), ids)
        self.assertEqual(len(ids), 8)
        # Goal context stays in the payload, limited to one goal in the first round.
        self.assertTrue({'TGL2', 'GOC21'} <= set(ids[:6]), ids)
        self.assertEqual(sum(i.startswith(('TGL', 'GOC')) for i in ids[:6]), 2, ids)

    def test_workload_and_self_review_slots_are_kept(self):
        ids = [i['record_id'] for i in self.items()]
        self.assertTrue({'AWK1', 'REV1'} <= set(ids))

    def test_extra_goal_rows_fill_slots_only_when_nothing_else_is_left(self):
        rows = story_rows()
        ids = [i['record_id'] for i in _person_items(SyntheticData(rows), 'E1', PERSON, rows, rows, 12)[0]]
        self.assertEqual(len(ids), 12)
        self.assertTrue(all(ids.index(g) > ids.index('CON1') for g in ('TGL1', 'GOC10', 'GOC11', 'GOC20')), ids)

    def test_item_text_keeps_blocker_context(self):
        items = {i['record_id']: i for i in self.items()}
        self.assertIn('Missing fields stop the feed', items['BLK1']['text'])
        self.assertTrue(items['INT2']['text'].startswith('Pat Doe'))


if __name__ == '__main__':
    unittest.main()
