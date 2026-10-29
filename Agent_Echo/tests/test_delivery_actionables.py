"""System-side repair diagnostics for the Luna 40 and Gemini 39 delivery failures."""

import json
import unittest

from agents.validation import ValidationError, repair_feedback, safe_validation_details
from agents.zero_sugar import ZeroSugarAgent
from test_agents import live_fixture, tool_turn
from test_review_contract_v3 import support as current_review
from test_review_contract_v2 import reviewer, visible
from test_review_stages import SCOPE, SOURCE


class ReviewRepairActionableTests(unittest.TestCase):
    def test_finding_normalization_reports_independent_errors_together(self):
        agent = ZeroSugarAgent(SCOPE, object(), 'live')
        blocks = [
            {'finding_id': 'F1', 'citation_ids': [SOURCE['citation_id']]},
            {'finding_id': 'F2', 'citation_ids': [SOURCE['citation_id']]},
        ]
        reviews = {
            key: {'decision': 'supported', 'reason': 'Controlled fixture.', 'assertions': [],
                  'citation_ids': [f'survey:WRONG{index}']}
            for index, key in enumerate(('F1', 'F2'), 1)
        }
        with self.assertRaises(ValidationError) as caught:
            agent.normalize_finding_submission({'finding_reviews': reviews}, blocks, [SOURCE], cache={})

        error = caught.exception
        self.assertEqual(error.details['validation_code'], 'finding_citations')
        self.assertEqual(error.details['finding_id'], 'F1')
        self.assertEqual(error.details['additional_errors'][0]['finding_id'], 'F2')
        feedback = repair_feedback(error)
        self.assertIn('finding_reviews.F1.citation_ids', feedback['correction'])
        self.assertIn('finding_reviews.F2.citation_ids', feedback['correction'])
        self.assertIn(SOURCE['citation_id'], feedback['correction'])
        self.assertNotIn('WRONG', json.dumps(feedback))

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

    def test_live_review_combines_citation_and_refinement_state_feedback(self):
        from copy import deepcopy

        correction_id = 'C_0123456789abcdef_support_1'
        prior = [{'correction_id': correction_id, 'issue': 'Include the requested explanation.',
                  'kind': 'missing_deliverable', 'owner': 'Original',
                  'requested_change': 'Include the requested explanation.',
                  'request_excerpt': 'Explain.', 'citation_ids': []}]
        attempts = {'count': 0}

        class CapturingScriptModel:
            def __init__(self):
                self.histories = []

            def respond(self, instructions, history, tools, require_tool=False):
                self.histories.append(deepcopy(history))
                context = json.loads(history[0]['content'])
                if tools[0]['name'] == 'submit_completeness_review':
                    return live_fixture(visible(), instructions, history, tools)
                attempts['count'] += 1
                report = current_review(context, {
                    correction_id: {'mandatory': attempts['count'] != 1,
                                    'addressed': False if attempts['count'] != 1 else True,
                                    'reason': 'Controlled lifecycle judgment.'}})
                report['decision'] = 'revise'
                report['corrections'] = [{
                    'issue': 'Retain the pending explanation.', 'kind': 'missing_deliverable',
                    'owner': 'Original', 'requested_change': 'Keep the required explanation pending.',
                    'request_excerpt': 'Explain.', 'citation_ids': [],
                    'related_correction_id': correction_id}]
                if attempts['count'] == 1 and report['finding_reviews']:
                    report['finding_reviews'][0]['citation_ids'] = ['survey:WRONG']
                turn = tool_turn('submit_review', report)
                return live_fixture(turn, instructions, history, tools)

        model = CapturingScriptModel()
        agent = reviewer(model)
        result = agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE], previous_corrections=prior)
        self.assertEqual(result.decision, 'revise')
        first = agent.diagnostics['rejected_attempts'][0]
        self.assertEqual(first['validation_code'], 'finding_citations')
        self.assertEqual(first['additional_errors'][0]['validation_code'], 'correction_refinement_state')
        self.assertEqual(first['additional_errors'][0]['correction_id'], correction_id)
        feedback = json.loads(next(item['output'] for item in model.histories[2]
                                   if item.get('type') == 'function_call_output'))
        self.assertIn('survey:CMT1', feedback['correction'])
        self.assertIn(correction_id, feedback['correction'])
        self.assertIn('mandatory=true, addressed=false', feedback['correction'])
        self.assertIn('related_correction_id=null', feedback['correction'])


if __name__ == '__main__':
    unittest.main()
