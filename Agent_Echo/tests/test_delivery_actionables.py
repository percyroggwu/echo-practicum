"""System-side repair diagnostics for the Luna 40 and Gemini 39 delivery failures."""

import json
import unittest

from agents.validation import ValidationError, repair_feedback, safe_validation_details
from agents.zero_sugar import ZeroSugarAgent
from test_agents import live_fixture, tool_turn
from fixtures import support as current_review
from fixtures import reviewer, visible
from fixtures import SCOPE, SOURCE


class ReviewRepairActionableTests(unittest.TestCase):

    def test_refinement_feedback_names_the_id_and_offers_both_valid_lifecycle_encodings(self):
        correction_id = 'C_0123456789abcdef_support_1'
        state_error = ValidationError(
            'correction_refinement_state', f'correction_judgments.{correction_id}',
            'A linked refinement must explicitly preserve the active correction state.',
            correction_id=correction_id, mandatory=False, addressed=True,
            expected_mandatory=True, expected_addressed=False,
            mandatory_present=True, addressed_present=True)

        feedback = repair_feedback(state_error)
        self.assertEqual(feedback['correction_id'], correction_id)
        self.assertEqual(feedback['mandatory'], False)
        self.assertEqual(feedback['addressed'], True)
        self.assertIn('mandatory=false, addressed=true', feedback['correction'])
        self.assertIn('mandatory=true, addressed=false', feedback['correction'])
        self.assertIn('mandatory=true, addressed=true', feedback['correction'])
        self.assertIn('related_correction_id=null', feedback['correction'])

    def test_aggregate_feedback_includes_a_linked_state_error_without_raw_model_text(self):
        correction_id = 'C_0123456789abcdef_support_1'
        state_error = ValidationError(
            'correction_refinement_state', f'correction_judgments.{correction_id}',
            'A linked refinement must explicitly preserve the active correction state.',
            correction_id=correction_id, mandatory=False, addressed=True,
            mandatory_present=True, addressed_present=True)
        citation_error = ValidationError(
            'finding_citations', 'finding_reviews.F1.citation_ids',
            'Finding references are retained by code; do not change them.',
            finding_id='F1', allowed_citation_ids=[SOURCE['citation_id']],
            additional_errors=[safe_validation_details(state_error)])

        feedback = repair_feedback(citation_error)
        self.assertIn('finding_reviews.F1.citation_ids', feedback['correction'])
        self.assertIn(correction_id, feedback['correction'])
        self.assertIn('mandatory=true, addressed=false', feedback['correction'])
        self.assertNotIn('raw model text', json.dumps(feedback))



if __name__ == '__main__':
    unittest.main()
