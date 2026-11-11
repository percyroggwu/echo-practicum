"""Check the annotation/scoring instrument, not model intelligence."""

import unittest
from review_cases import cases, score, corpus_identity


class ReviewCaseTests(unittest.TestCase):
    def test_fixed_case_set_has_clean_and_independently_varied_candidates(self):
        values = cases()
        self.assertEqual(len(values), 9)
        self.assertEqual(values[0]['expected_defects'], [])
        self.assertEqual(len({c['case_id'] for c in values}), 9)
        self.assertEqual(len(corpus_identity()), 64)

    def test_scorer_counts_false_objections_and_missed_defects(self):
        judgments = [{'case_id': c['case_id'], 'defect_ids': list(c['expected_defects'])} for c in cases()]
        self.assertTrue(score(judgments)['passes_controlled_threshold'])
        judgments[0]['defect_ids'] = ['denominator']
        judgments[1]['defect_ids'] = []
        result = score(judgments)
        self.assertEqual((result['false_positives'], result['false_negatives']), (1, 1))
        self.assertFalse(result['passes_controlled_threshold'])

    def test_partial_or_duplicate_case_coverage_is_rejected(self):
        judgments = [{'case_id': c['case_id'], 'defect_ids': c['expected_defects']} for c in cases()]
        with self.assertRaises(ValueError):
            score(judgments[:-1])
        judgments[-1] = judgments[0]
        with self.assertRaises(ValueError):
            score(judgments)
