"""Offline delivery regressions; scripted judgments do not measure model quality."""

from copy import deepcopy
from dataclasses import asdict
import json
import unittest

from agents.content import excerpt_catalog, resolve_answer, block_catalog
from agents.grounding import FactCatalog, render_answer, audit_claims
from agents.original import OriginalAgent
from agents.review_delivery import (safety_gate, veto_active, obligation_groups, reconcile_corrections,
    assertion_alignment, submission_identity)
from agents.runtime import Specialist, AgentRunError, AgentResult
from agents.validation import ValidationError, repair_feedback
from agents.zero_sugar import ZeroSugarAgent, VerificationResult, DIMENSIONS
from test_agents import SequenceModel, tool_turn
from test_review_stages import PhaseModel, SCOPE, SOURCE
from test_review_contract_v2 import current_support, visible


def wire(text='A scoped interpretation.', refs=None, quote=None):
    return {'fact_ids': [], 'interpretations': [{'text': text,
        'citation_ids': refs or [SOURCE['citation_id']], 'quote_ref': quote}],
        'proposals': [], 'reuse_ids': [], 'remove_ids': [], 'removal_reasons': []}


class Audit31UpdateTests(unittest.TestCase):
    def setUp(self):
        self.evidence = [deepcopy(SOURCE), {'citation_id': 'survey:OTHER',
            'text': 'Extra support was overlooked.', 'scope': SCOPE.__dict__}]
        self.excerpts = excerpt_catalog(self.evidence)
        self.other = next(key for key, item in self.excerpts.items() if item['source_id'] == 'survey:OTHER')

    def specialist(self, turns):
        model = SequenceModel(turns)
        agent = Specialist('Original', 'Use scoped evidence.', model, SCOPE, [], {}, 'live')
        agent.source_grounding = True
        return agent, model

    def test_excerpt_error_locates_item_and_lists_real_source_and_allowed_refs(self):
        payload = wire(quote=self.other)
        with self.assertRaises(ValidationError) as caught:
            resolve_answer(payload, self.evidence, SCOPE.__dict__, {}, {})
        feedback = repair_feedback(caught.exception)
        self.assertEqual(feedback['field'], 'interpretations[0].quote_ref')
        self.assertEqual(feedback['source_id'], 'survey:OTHER')
        self.assertEqual(feedback['submitted_reference'], self.other)
        self.assertEqual(feedback['item_index'], 0)
        self.assertTrue(feedback['allowed_excerpt_refs'])
        self.assertNotIn('Extra support', json.dumps(feedback))

    def test_aggregate_has_no_allowed_excerpt_and_null_is_valid(self):
        evidence = [*self.evidence, {'citation_id': 'SENTIMENT1', 'rows': [], 'scope': SCOPE.__dict__}]
        with self.assertRaises(ValidationError) as caught:
            resolve_answer(wire(refs=['SENTIMENT1'], quote=self.other), evidence, SCOPE.__dict__, {}, {})
        self.assertEqual(repair_feedback(caught.exception)['allowed_excerpt_refs'], [])
        result = resolve_answer(wire(refs=['SENTIMENT1']), evidence, SCOPE.__dict__, {}, {})
        self.assertIsNone(result['interpretations'][0]['quote'])

    def test_different_submissions_do_not_trigger_identical_submission_stall(self):
        turns = [tool_turn('submit_grounded_answer', wire('Draft ' + str(i), quote=self.other)) for i in range(4)]
        turns.append(tool_turn('submit_grounded_answer', wire()))
        agent, model = self.specialist(turns)
        result = agent.run('Explain.', self.evidence)
        self.assertEqual(len(model.histories), 5)
        self.assertNotIn('presentation_fallback', result.diagnostics)

    def test_identical_bad_quotes_get_one_mechanical_fallback_without_another_model_call(self):
        turn = tool_turn('submit_grounded_answer', wire(quote=self.other))
        agent, model = self.specialist([turn] * 3)
        result = agent.run('Explain.', self.evidence)
        self.assertEqual(len(model.histories), 3)
        self.assertTrue(result.diagnostics['presentation_fallback']['requires_both_reviews'])
        self.assertIsNone(result.claims[0]['quote'])
        self.assertNotEqual(result.status, 'complete')
        self.assertEqual(result.claims[0]['citation_ids'], [SOURCE['citation_id']])

    def test_final_turn_has_mechanical_fallback_but_no_eighth_model_request(self):
        turns = [tool_turn('submit_grounded_answer', wire('Variant ' + str(i), quote=self.other)) for i in range(7)]
        agent, model = self.specialist(turns)
        result = agent.run('Explain.', self.evidence)
        self.assertEqual(len(model.histories), 7)
        self.assertIn('presentation_fallback', result.diagnostics)

    def test_fallback_cannot_repeat_in_another_draft_of_the_same_role(self):
        turn = tool_turn('submit_grounded_answer', wire(quote=self.other))
        agent, model = self.specialist([turn] * 6)
        agent.run('Explain.', self.evidence)
        with self.assertRaises(AgentRunError):
            agent.run('Explain.', self.evidence)
        self.assertEqual(len(model.histories), 6)

    def test_old_saved_review_keeps_the_score_based_veto(self):
        ratings = {key: {'score': 3, 'rationale': 'Historical fixture.'} for key in DIMENSIONS}
        ratings['Safety / Appropriateness']['score'] = 2
        old = VerificationResult('revise', ratings, [], '', [], 'live', version='review-v5')
        self.assertTrue(veto_active(old))

    def test_fallback_cannot_bypass_unknown_citation_validation(self):
        turn = tool_turn('submit_grounded_answer', wire(refs=['survey:UNKNOWN'], quote=self.other))
        agent, _ = self.specialist([turn] * 7)
        with self.assertRaises((AgentRunError, ValidationError)):
            agent.run('Explain.', self.evidence)

    def test_submission_hash_ignores_object_key_order_not_content(self):
        self.assertEqual(submission_identity({'b': 2, 'a': 1}, 'x', 'f'), submission_identity({'a': 1, 'b': 2}, 'x', 'f'))
        self.assertNotEqual(submission_identity({'a': 2}, 'x', 'f'), submission_identity({'a': 1}, 'x', 'f'))

    def review(self, support):
        model = PhaseModel([visible()], support)
        agent = ZeroSugarAgent(SCOPE, model, 'live', document_lookup={SOURCE['citation_id']: SOURCE}, authorized_teams=['Data Platforms'])
        result = agent.review('Explain.', 'Recognition is described favorably [survey:CMT1].', [SOURCE])
        return agent, model, result

    def test_unexplained_low_safety_retains_complete_review_and_supported_findings(self):
        def support(context):
            report = current_support(context)
            report['ratings']['Safety / Appropriateness'] = {'score': 2, 'rationale': 'R'}
            report['safety_issue_indices'] = []
            return tool_turn('submit_review', report)
        agent, model, result = self.review(support)
        self.assertEqual(len(model.calls), 4)
        self.assertEqual(agent.diagnostics['explanation_quality']['status'], 'incomplete')
        self.assertEqual(result.decision, 'revise')
        self.assertEqual(result.findings[0]['status'], 'supported')
        self.assertFalse(result.release_gate['active'])
        self.assertTrue(agent.diagnostics['unexplained_revision'])
        self.assertIn('Safety / Appropriateness', agent.diagnostics['rating_explanation_diagnostics']['one_character_dimensions'])

    def test_real_linked_safety_concern_vetoes_without_erasing_evidence_support(self):
        def support(context):
            report = current_support(context, corrections=[{'issue': 'The proposed disclosure would identify an anonymous respondent.',
                'kind': 'unsupported_claim', 'owner': 'Original', 'requested_change': 'Remove the identifying disclosure.',
                'citation_ids': [SOURCE['citation_id']]}])
            report['ratings']['Safety / Appropriateness'] = {'score': 2, 'rationale': 'The disclosure risks anonymity.'}
            report['safety_issue_indices'] = [0]
            return tool_turn('submit_review', report)
        _, model, result = self.review(support)
        self.assertEqual(len(model.calls), 2)
        self.assertTrue(result.release_gate['active'])
        self.assertEqual(result.findings[0]['status'], 'withheld')
        self.assertEqual(result.findings[0]['evidence_status'], 'supported')

    def test_high_scores_with_one_character_explanations_cannot_certify_complete_answer(self):
        def support(context):
            report = current_support(context)
            for rating in report['ratings'].values():
                rating['rationale'] = 'R'
            return tool_turn('submit_review', report)
        agent, model, result = self.review(support)
        self.assertEqual(len(model.calls), 4)
        self.assertEqual(agent.diagnostics['explanation_quality']['status'], 'incomplete')
        self.assertEqual(result.decision, 'revise')
        self.assertEqual(result.findings[0]['status'], 'supported')
        self.assertEqual(agent.diagnostics['rejected_attempts'], [])

    def test_invalid_safety_link_is_diagnostic_not_another_review_rejection(self):
        ratings = {key: {'score': 2, 'rationale': 'R'} for key in DIMENSIONS}
        gate = safety_gate(ratings, [], [0, -1, 'x'])
        self.assertFalse(gate['active'])
        self.assertEqual(gate['invalid_link_count'], 3)

    def test_duplicate_citations_normalize_without_changing_assessment(self):
        def support(context):
            report = current_support(context)
            for finding in report['finding_reviews']:
                for assertion in finding['assertions']:
                    assertion['citation_ids'] *= 2
            return tool_turn('submit_review', report)
        agent, model, result = self.review(support)
        self.assertEqual(len(model.calls), 2)
        self.assertTrue(agent.diagnostics['citation_normalizations'])
        self.assertEqual(result.findings[0]['assertions'][0]['citation_ids'], [SOURCE['citation_id']])

    def test_scope_is_explicit_and_diagnostics_never_reject_nonliteral_assertion(self):
        from agents.zero_sugar import COMPLETENESS_INSTRUCTIONS
        self.assertIn('defines the eligible population', COMPLETENESS_INSTRUCTIONS)
        agent, model, result = self.review(lambda context: tool_turn('submit_review', current_support(context)))
        self.assertEqual(model.calls[0][1]['authorized_scope'], SCOPE.__dict__)
        self.assertEqual(model.calls[0][1]['authorized_teams'], ['Data Platforms'])
        diagnostic = assertion_alignment('Only one team appears, justifying no suppression.', 'Which recognition practices should we protect?')
        self.assertFalse(diagnostic['literal_anchor_found'])
        self.assertFalse(diagnostic['semantic_alignment_verified'])
        self.assertEqual(result.decision, 'accept')

    def test_explicit_aliases_coalesce_but_similar_unlinked_issues_do_not(self):
        values = [{'correction_id': 'C1', 'issue': 'Missing example.', 'detected_phases': ['completeness']},
            {'correction_id': 'C2', 'obligation_id': 'C1', 'issue': 'Include the example.', 'detected_phases': ['support']},
            {'correction_id': 'C3', 'issue': 'Missing example.'}]
        merged = reconcile_corrections(values)
        self.assertEqual(len(merged), 2)
        self.assertEqual(len(obligation_groups(merged)), 2)
        self.assertEqual(merged[0]['detected_phases'], ['completeness', 'support'])
        self.assertEqual(merged[0]['provenance_records'][0]['issue'], 'Include the example.')
        self.assertEqual(len(values), 3)

    def test_same_obligation_from_both_phases_has_one_repair_with_provenance(self):
        def support(context):
            prior = context['review_obligations'][0]['correction_id']
            report = current_support(context, corrections=[{'issue': 'The requested example remains absent.',
                'kind': 'missing_deliverable', 'owner': 'Original', 'requested_change': 'Show the literal example.',
                'citation_ids': [SOURCE['citation_id']], 'related_correction_id': prior}])
            report.pop('correction_reviews')
            report['correction_judgments'] = {prior: {'mandatory': True, 'addressed': False,
                'reason': 'The visible example is still absent.'}}
            return tool_turn('submit_review', report)
        model = PhaseModel([visible(['A literal example is absent.'])], support)
        reviewer = ZeroSugarAgent(SCOPE, model, 'live', document_lookup={SOURCE['citation_id']: SOURCE})
        result = reviewer.review('Explain.', 'A theme [survey:CMT1].', [SOURCE])
        self.assertEqual(len(model.calls), 2)
        self.assertEqual(len(result.corrections), 1)
        self.assertEqual(result.corrections[0]['detected_phases'], ['support', 'completeness'])
        self.assertEqual(len(obligation_groups(result.corrections)), 1)

    def test_live_edit_requires_reasons_but_historical_payload_is_still_readable(self):
        payload = wire()
        payload.pop('removal_reasons')
        resolve_answer(payload, [SOURCE], SCOPE.__dict__, {}, {})
        with self.assertRaises(ValidationError):
            resolve_answer(payload, [SOURCE], SCOPE.__dict__, {}, {}, require_removal_reasons=True)

    def test_required_content_is_replaced_with_explicit_removal_reason(self):
        original = {'fact_ids': [], 'interpretations': [{'text': 'Positive example.', 'citation_ids': [SOURCE['citation_id']], 'quote': SOURCE['text']}],
            'proposals': [{'text': 'What should the team preserve?', 'citation_ids': [SOURCE['citation_id']], 'quote': None}]}
        blocks = block_catalog(original, [SOURCE], SCOPE.__dict__)
        positive = next(key for key, value in blocks.items() if value['kind'] == 'interpretations')
        payload = wire('A clearer positive example.', quote=next(iter(excerpt_catalog([SOURCE]))))
        payload['remove_ids'] = [positive]
        payload['removal_reasons'] = [{'block_id': positive, 'reason': 'Replace the example while keeping the literal quote and source.'}]
        resolved = resolve_answer(payload, [SOURCE], SCOPE.__dict__, blocks, blocks)
        self.assertEqual(len(resolved['proposals']), 1)
        self.assertEqual(resolved['interpretations'][0]['quote'], SOURCE['text'])
        payload['removal_reasons'] = []
        with self.assertRaises(ValidationError):
            resolve_answer(payload, [SOURCE], SCOPE.__dict__, blocks, blocks)

    def test_substring_quote_suppressed_only_in_v6_and_old_replay_is_exact(self):
        source = {**SOURCE, 'text': 'My contributions are noticed. The recap named contributors.'}
        payload = {'fact_ids': [], 'interpretations': [{'text': 'Example: "' + source['text'] + '"',
            'citation_ids': [source['citation_id']], 'quote': 'My contributions are noticed.'}], 'proposals': []}
        catalog = FactCatalog([source], SCOPE.__dict__)
        new, claims = render_answer(payload, catalog, 'Original')
        old, _ = render_answer(payload, catalog, 'Original', version='source-facts-v5')
        self.assertEqual(new.count('My contributions are noticed.'), 1)
        self.assertEqual(old.count('My contributions are noticed.'), 2)
        grounding = {'version': 'source-facts-v6', 'role': 'Original', 'payload': payload}
        self.assertEqual(audit_claims(claims, new, catalog, grounding), [])

    def test_reporting_separates_safety_veto_and_pending_obligations(self):
        ratings = {key: {'score': 3, 'rationale': 'Controlled fixture.'} for key in DIMENSIONS}
        ratings['Safety / Appropriateness']['score'] = 2
        verdict = VerificationResult('revise', ratings, ['Privacy concern.'], '', [], 'live',
            findings=[{'finding_id': 'F1', 'text': 'A supported block.', 'status': 'withheld', 'evidence_status': 'supported'}],
            corrections=[{'correction_id': 'C1', 'issue': 'Privacy concern.', 'owner': 'Original'}],
            candidate_id='reviewed', release_gate=safety_gate(ratings, ['Privacy concern.'], [0]))
        agent = OriginalAgent.__new__(OriginalAgent)
        agent.mode = 'live'
        agent.reviewed_candidate = {'candidate_id': 'reviewed', 'answer': 'Old answer', 'claims': [], 'grounding': {},
            'visualization': {}, 'evidence': [SOURCE], 'sentiment': {}}
        candidate = AgentResult('Original', 'Explain.', 'A newer draft.', SCOPE.__dict__, mode='live')
        candidate.verification = {'reviews': [asdict(verdict)]}
        result = agent.incomplete(candidate, verdict)
        self.assertEqual(result.verification['release_counts']['supported'], 1)
        self.assertEqual(result.verification['release_counts']['released'], 0)
        self.assertEqual(result.verification['release_counts']['withheld_by_release_gate'], 1)
        self.assertIn('No blocks were published', result.answer)
        self.assertIn('supported 1 findings on evidence', result.answer)
        self.assertEqual(result.diagnostics['unresolved_views']['structured_pending_corrections']['distinct_obligation_count'], 1)
