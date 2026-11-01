"""Deterministic delivery regressions, never a claim of model accuracy."""

from copy import deepcopy
import hashlib
import json
import unittest

from agents.content import resolve_corrections, live_answer_schema
from agents.grounding import FactCatalog, answer_schema, render_answer, audit_claims, GROUNDING_VERSIONS
from agents.model import ModelTurn
from agents.model import record_response_usage
from types import SimpleNamespace
from agents.review_v7 import equivalent_calls, explanation_errors
from agents.runtime import RunBudget
from agents.validation import ValidationError, repair_feedback
from agents.vanilla import sentiment_summary
from agents.zero_sugar import ZeroSugarAgent, DIMENSIONS
from test_agents import tool_turn, live_fixture
from test_review_stages import SCOPE, SOURCE, PhaseModel
from test_review_contract_v2 import visible, current_support


def classification_fixture(n=13):
    docs = [{'citation_id': f'survey:CMT{i}', 'source': 'HR_survey_comments', 'team': 'Data Platforms',
        'date': '2026-09-01', 'dimension': 'Recognition', 'response_text': f'Comment number {i}.'} for i in range(n)]
    labels = [{'citation_id': d['citation_id'], 'label': 'mixed' if i in (8, 11, 12) else 'negative' if i in (1, 2) else 'positive',
        'quote': d['response_text'], 'reason': 'Scripted label, not a semantic annotation.'} for i, d in enumerate(docs)]
    report = {'citation_id': 'SENTIMENT1', 'scope': SCOPE.__dict__, 'dimension': 'Recognition', 'mode': 'live',
        'rubric_version': 'survey-sentiment-v3', 'source_facts_version': 'source-facts-v7', 'labels': labels,
        'source_hashes': {d['citation_id']: hashlib.sha256(d['response_text'].encode()).hexdigest() for d in docs}}
    summary = sentiment_summary(report, docs)
    evidence = [summary, *[{'citation_id': d['citation_id'], 'text': d['response_text'], 'scope': SCOPE.__dict__} for d in docs]]
    return report, docs, evidence


class ReviewV7Tests(unittest.TestCase):
    def test_canonical_display_covers_all_thirteen_labels(self):
        _, _, evidence = classification_fixture()
        catalog = FactCatalog(evidence, SCOPE.__dict__)
        payload = catalog.bind_classification_display({'fact_ids': [], 'interpretations': [], 'proposals': []}, 'Original')
        text, claims = render_answer(payload, catalog, 'Original')
        self.assertIn('| survey:CMT10 | positive |', text)
        self.assertIn('| survey:CMT12 | mixed |', text)
        self.assertEqual(audit_claims(claims, text, catalog, {'version': 'source-facts-v7', 'role': 'Original', 'payload': payload}), [])

    def test_swapped_labels_with_identical_totals_fail_replay(self):
        _, _, evidence = classification_fixture()
        catalog = FactCatalog(evidence, SCOPE.__dict__)
        payload = catalog.bind_classification_display({'fact_ids': [], 'interpretations': [], 'proposals': []}, 'Original')
        text, claims = render_answer(payload, catalog, 'Original')
        changed_claims = deepcopy(claims)
        changed_claims[0]['text'] = changed_claims[0]['text'].replace('| survey:CMT10 | positive |', '| survey:CMT10 | mixed |').replace('| survey:CMT12 | mixed |', '| survey:CMT12 | positive |')
        changed = '\n\n'.join(c['text'] for c in changed_claims)
        self.assertTrue(audit_claims(changed_claims, changed, catalog, {'version': 'source-facts-v7', 'role': 'Original', 'payload': payload}))

    def test_binding_tampering_and_source_tampering_are_rejected(self):
        for kind in ('label', 'source'):
            _, _, evidence = classification_fixture()
            if kind == 'label':
                evidence[0]['classification_records'][0]['label'] = 'negative'
            else:
                evidence[1]['text'] = 'Changed source.'
            with self.assertRaises(ValidationError):
                FactCatalog(evidence, SCOPE.__dict__)

    def test_suppressed_group_has_no_label_records(self):
        _, _, evidence = classification_fixture(4)
        self.assertEqual(evidence[0]['classification_records'], [])

    def test_historical_summary_is_unchanged_without_new_marker(self):
        report, docs, _ = classification_fixture()
        report.pop('source_facts_version')
        self.assertNotIn('classification_records', sentiment_summary(report, docs))
        self.assertTrue({f'source-facts-v{i}' for i in range(1, 8)} <= GROUNDING_VERSIONS)

    def test_proposals_offer_null_only(self):
        schema = live_answer_schema(answer_schema('Original'), excerpts=['EX_example'])
        self.assertEqual(schema['proposals']['items']['properties']['quote_ref']['enum'], [None])
        self.assertEqual(schema['interpretations']['items']['properties']['quote_ref']['enum'], ['EX_example', None])

    def test_duplicate_feedback_names_id_and_both_items(self):
        identity = 'C_0123456789abcdef_F9_assertions'
        report = {'corrections': [{'request_ref': None, 'related_correction_id': identity} for _ in range(2)]}
        with self.assertRaises(ValidationError) as caught:
            resolve_corrections(report, 'Explain.', {}, [identity])
        feedback = repair_feedback(caught.exception)
        self.assertEqual((feedback['correction_id'], feedback['item_index'], feedback['conflicting_item_index']), (identity, 1, 0))

    def test_distinct_prior_ids_remain_legal(self):
        ids = ['C_0123456789abcdef_F9_assertions', 'C_0123456789abcdef_F10_assertions']
        links = {}
        resolve_corrections({'corrections': [{'request_ref': None, 'related_correction_id': i} for i in ids]}, 'Explain.', links, ids)
        self.assertEqual(list(links.values()), ids)

    def test_equivalent_calls_normalize_but_competing_decisions_do_not(self):
        a, b = tool_turn('submit_review', {'decision': 'accept'}, 'a'), tool_turn('submit_review', {'decision': 'accept'}, 'b')
        turn = ModelTurn(calls=a.calls + b.calls)
        self.assertEqual(len(equivalent_calls(turn, 'submit_review')[0].calls), 1)
        turn.calls[1].arguments = json.dumps({'decision': 'revise'})
        self.assertEqual(len(equivalent_calls(turn, 'submit_review')[0].calls), 2)

    def test_protocol_exception_is_shared_across_phases(self):
        budget = RunBudget()
        agent = ZeroSugarAgent(SCOPE, None, budget=budget)
        phase = {'phase': 'completeness', 'candidate_id': 'fixed'}
        attempts = []
        for attempt in agent.phase_attempts(budget, phase):
            attempts.append(attempt)
            phase['protocol_retry_eligible'] = True
        self.assertEqual(attempts, [0, 1, 2, 3])
        phase = {'phase': 'support', 'candidate_id': 'fixed'}
        attempts = []
        for attempt in agent.phase_attempts(budget, phase):
            attempts.append(attempt)
            phase['protocol_retry_eligible'] = True
        self.assertEqual(attempts, [0, 1, 2])
        self.assertEqual(budget.snapshot()['review_protocol_repairs'], 1)

    def test_no_exception_for_semantic_revision_or_exhausted_global_budget(self):
        agent = ZeroSugarAgent(SCOPE, None)
        phase = {'phase': 'support', 'candidate_id': 'fixed'}
        self.assertEqual(list(agent.phase_attempts(RunBudget(), phase)), [0, 1, 2])
        budget = RunBudget(model_limit=0)
        for _ in agent.phase_attempts(budget, phase):
            phase['protocol_retry_eligible'] = True
        self.assertEqual(budget.review_protocol_repairs, 0)

    def test_fourth_completeness_attempt_can_recover_without_fifth(self):
        a, b = visible(), visible(issues=['Controlled missing content.'])
        for c in b.calls:
            c.call_id = 'second'
        bad = ModelTurn(calls=a.calls + b.calls)
        model = PhaseModel([bad, bad, bad, visible()])
        budget = RunBudget()
        agent = ZeroSugarAgent(SCOPE, model, 'live', budget=budget, document_lookup={SOURCE['citation_id']: SOURCE})
        result = agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE])
        self.assertEqual(result.decision, 'accept')
        self.assertEqual(agent.diagnostics['review_phases'][0]['model_attempts'], 4)
        self.assertEqual(budget.models, 5)

    def test_explanation_fields_do_not_certify_semantics(self):
        explanations = {d: {'dimension': d, 'evidence_refs': ['candidate'], 'observation': 'A potentially incorrect explanation.'} for d in DIMENSIONS}
        self.assertEqual(explanation_errors(explanations, DIMENSIONS, ['candidate']), [])
        explanations['Accuracy']['evidence_refs'] = ['unknown']
        self.assertEqual(explanation_errors(explanations, DIMENSIONS, ['candidate']), ['Accuracy'])

    def test_explanation_repair_freezes_substantive_corrections(self):
        correction = {'issue': 'A controlled real correction.', 'kind': 'unsupported_claim', 'owner': 'Original',
            'requested_change': 'Repair the controlled claim.', 'citation_ids': [SOURCE['citation_id']]}
        def support(context):
            report = current_support(context, corrections=[correction])
            report['rating_explanations'] = {}
            return tool_turn('submit_review', report)
        model = PhaseModel([visible()], support)
        agent = ZeroSugarAgent(SCOPE, model, 'live', document_lookup={SOURCE['citation_id']: SOURCE})
        result = agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE])
        self.assertEqual(result.corrections[0]['issue'], correction['issue'])
        self.assertEqual(agent.diagnostics['explanation_quality']['status'], 'complete')
        self.assertEqual([c[0] for c in model.calls], ['submit_completeness_review', 'submit_review', 'submit_rating_explanations'])

    def test_competing_calls_stop_after_the_single_exception(self):
        a, b = visible(), visible(issues=['Controlled gap.'])
        b.calls[0].call_id = 'second'
        bad = ModelTurn(calls=a.calls + b.calls)
        budget = RunBudget()
        agent = ZeroSugarAgent(SCOPE, PhaseModel([bad] * 4), 'live', budget=budget)
        with self.assertRaisesRegex(RuntimeError, 'review delivery protocol exhausted'):
            agent.review('Explain.', 'A generated candidate.', [])
        self.assertEqual(budget.models, 4)
        self.assertEqual(agent.diagnostics['protocol_recovery']['phase'], 'completeness')
        self.assertFalse(agent.diagnostics['protocol_recovery']['support_review_completed'])

    def test_bad_explanations_exhaust_ordinary_attempts_without_losing_findings(self):
        def support(context):
            report = current_support(context)
            for rating in report['ratings'].values():
                rating['rationale'] = 'R'
            report['rating_explanations'] = {}
            return tool_turn('submit_review', report)
        budget = RunBudget()
        agent = ZeroSugarAgent(SCOPE, PhaseModel([visible()], support), 'live', budget=budget,
            document_lookup={SOURCE['citation_id']: SOURCE})
        result = agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE])
        self.assertEqual(result.decision, 'revise')
        self.assertEqual(result.repair_targets, [])
        self.assertEqual(result.findings[0]['status'], 'supported')
        self.assertEqual(result.explanation_quality['status'], 'incomplete')
        self.assertEqual(budget.models, 4)
        self.assertEqual(budget.review_protocol_repairs, 0)

    def test_request_cost_records_provider_tokens_without_request_text(self):
        class UsageModel:
            def respond(self, *args):
                record_response_usage(SimpleNamespace(usage=SimpleNamespace(prompt_tokens=10, completion_tokens=4, total_tokens=14)), 'fixture', 6000)
                return ModelTurn()
        budget = RunBudget()
        budget.consume('model')
        budget.respond(UsageModel(), 'PRIVATE TEXT', [], [], True)
        cost = budget.snapshot()['request_costs'][0]
        self.assertEqual(cost['provider_usage'][0]['input_tokens'], 10)
        self.assertNotIn('PRIVATE TEXT', json.dumps(cost))


if __name__ == '__main__':
    unittest.main()
