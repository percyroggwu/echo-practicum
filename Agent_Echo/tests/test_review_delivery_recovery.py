"""Bounded review delivery and truncation recovery; scripted judgments are not accuracy evidence.

These checks cover what the application can enforce: the declared field bounds, a precise
rejection when finding_reviews arrives as text, and a shorter retry inside the existing
three attempts when the provider truncates the review. Model compliance is not guaranteed
and no test here claims analytical correctness.
"""

from copy import deepcopy
import json
import re
import unittest

from agents.validation import OutputTokenLimit, ValidationError, repair_feedback
from agents.content import public_blocks
from agents.zero_sugar import (ZeroSugarAgent, DIMENSIONS, RATING_RATIONALE_LIMIT,
                               FINDING_REASON_LIMIT, SUGGESTION_LIMIT, SUGGESTION_COUNT_LIMIT,
                               UNCERTAINTY_LIMIT, COMPACT_SUPPORT_RETRY)
from test_agents import live_fixture, tool_turn, completeness_turn
from test_review_contract_v2 import current_support, reviewer, visible
from test_review_stages import support_turn, SOURCE, SCOPE


class ScriptModel:
    """Records the instructions so the compact retry can be asserted, not assumed."""

    def __init__(self, completeness=(), support=None):
        self.completeness = list(completeness or [completeness_turn()])
        self.support = support
        self.calls, self.instructions, self.histories, self.submissions = [], [], [], []

    def respond(self, instructions, history, tools, require_tool=False):
        context = json.loads(history[0]['content'])
        self.calls.append((tools[0]['name'], deepcopy(context), deepcopy(tools)))
        self.instructions.append(instructions)
        self.histories.append(deepcopy(history))
        if tools[0]['name'] == 'submit_completeness_review':
            turn = self.completeness.pop(0)
            if isinstance(turn, BaseException):
                raise turn
            return live_fixture(turn, instructions, history, tools)
        if callable(self.support):
            submission = self.support(context)
            self.submissions.append(deepcopy(submission))
            return live_fixture(submission, instructions, history, tools)
        return live_fixture(support_turn(context), instructions, history, tools)


def current(context):
    """A current live submission: no legacy issues/repair_targets fields."""
    report = current_support(context)
    report.pop('numeric_reviews', None)
    report.pop('correction_reviews', None)
    return report


class BoundedFieldTests(unittest.TestCase):
    def base(self):
        return {'decision': 'accept',
                'ratings': {name: {'score': 3, 'rationale': 'Controlled review fixture.'} for name in DIMENSIONS},
                'uncertainty': 'Controlled fixture.', 'suggestions': []}

    def test_bounds_reject_only_the_field_that_exceeds_them(self):
        cases = (
            (lambda report: report['ratings']['Accuracy'].update(rationale='x' * (RATING_RATIONALE_LIMIT + 1)),
             'ratings.Accuracy.rationale', 'max_characters', RATING_RATIONALE_LIMIT),
            (lambda report: report.update(uncertainty='x' * (UNCERTAINTY_LIMIT + 1)),
             'uncertainty', 'max_characters', UNCERTAINTY_LIMIT),
            (lambda report: report.update(suggestions=['x' * (SUGGESTION_LIMIT + 1)]),
             'suggestions', 'max_characters', SUGGESTION_LIMIT),
            (lambda report: report.update(suggestions=['ok'] * (SUGGESTION_COUNT_LIMIT + 1)),
             'suggestions', 'expected_count', SUGGESTION_COUNT_LIMIT),
            (lambda report: report.update(finding_reviews=[{'finding_id': 'F1', 'decision': 'supported',
                                                            'reason': 'x' * (FINDING_REASON_LIMIT + 1)}]),
             'finding_reviews.F1.reason', 'max_characters', FINDING_REASON_LIMIT),
        )
        for mutate, field, bound, limit in cases:
            with self.subTest(field=field, limit=limit):
                report = self.base()
                mutate(report)
                with self.assertRaises(ValidationError) as caught:
                    ZeroSugarAgent.validate_review_bounds(report)
                self.assertEqual(caught.exception.details['validation_code'], 'review_text_limit')
                self.assertEqual(caught.exception.details['field'], field)
                self.assertEqual(caught.exception.details[bound], limit)

    def test_correction_citation_feedback_names_the_evidence_namespace_and_received_ids(self):
        error = ValidationError('correction_citations', 'corrections.citation_ids',
            'Use evidence citation IDs from the supplied sources.', item_index=0,
            received_citation_ids=['F4', 'F5'], received_citation_count=2,
            allowed_citation_ids=['survey:CMT1'], allowed_citation_count=1)
        feedback = repair_feedback(error)
        self.assertEqual(feedback['received_citation_ids'], ['F4', 'F5'])
        self.assertEqual(feedback['allowed_citation_ids'], ['survey:CMT1'])
        self.assertEqual(feedback['allowed_citation_count'], 1)
        self.assertIn('never finding IDs such as F4', feedback['correction'])
        self.assertIn('Received IDs', feedback['correction'])

    def test_simultaneous_finding_and_correction_errors_are_returned_on_the_first_retry(self):
        change = {'issue': 'Explain the limit.', 'kind': 'missing_deliverable', 'owner': 'Original',
                  'requested_change': 'State the actual coverage limit.', 'citation_ids': ['F4']}
        attempts = {'count': 0}

        def support(context):
            attempts['count'] += 1
            report = current_support(context, corrections=[change if attempts['count'] == 1 else
                {**change, 'citation_ids': ['survey:CMT1']}])
            report.pop('numeric_reviews', None)
            report.pop('correction_reviews', None)
            if attempts['count'] == 1 and report['finding_reviews']:
                report['finding_reviews'][0]['assertions'][0]['citation_ids'] = ['survey:OUTSIDE']
            return tool_turn('submit_review', report)

        model = ScriptModel(support=support)
        agent = reviewer(model)
        result = agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE])
        self.assertEqual(result.decision, 'revise')
        self.assertEqual(json.loads(model.submissions[0].calls[0].arguments)['corrections'][0]['citation_ids'], ['F4'])
        self.assertNotIn('F4', json.dumps(result.corrections), result.corrections)
        first = agent.diagnostics['rejected_attempts'][0]
        self.assertEqual(first['validation_code'], 'assertion_citations', first)
        self.assertIn('additional_errors', first, first)
        self.assertEqual(first['additional_errors'][0]['validation_code'], 'correction_citations')
        self.assertEqual(first['additional_errors'][0]['received_citation_ids'], ['F4'])
        self.assertEqual(first['additional_errors'][0]['allowed_citation_count'], 1)
        retry = next(item for item in model.histories[2] if item.get('type') == 'function_call_output')
        self.assertIn('corrections.citation_ids', retry['output'])
        self.assertIn('F4', retry['output'])
        self.assertIn('survey:CMT1', retry['output'])

    def test_saved_blocks_are_sent_once_with_a_current_draft_marker(self):
        available = {f'B{index}': {'kind': 'interpretations', 'value': {'text': f'Block {index}.'}}
                     for index in range(8)}
        saved = dict(list(available.items())[:4])
        combined = public_blocks(available, saved)
        self.assertEqual(len(combined), len(available))
        self.assertEqual(sum(item['currently_saved'] for item in combined), 4)
        duplicate_payload = {'reusable_blocks': public_blocks(available), 'current_draft': public_blocks(saved)}
        compact_payload = {'available_blocks': combined}
        self.assertLess(len(json.dumps(compact_payload)), len(json.dumps(duplicate_payload)))

    def test_bounds_accept_the_declared_limits_and_every_judgment_stays_required(self):
        report = self.base()
        report['ratings']['Accuracy']['rationale'] = 'x' * RATING_RATIONALE_LIMIT
        report['uncertainty'] = 'x' * UNCERTAINTY_LIMIT
        report['suggestions'] = ['x' * SUGGESTION_LIMIT] * SUGGESTION_COUNT_LIMIT
        ZeroSugarAgent.validate_review_bounds(report)
        # The live schema declares the same numbers the validator enforces.
        agent = ZeroSugarAgent(SCOPE, ScriptModel(), 'live')
        parameters = agent.tools[0]['parameters']['properties']
        self.assertEqual(parameters['ratings']['properties']['Accuracy']['properties']['rationale']['maxLength'],
                         RATING_RATIONALE_LIMIT)
        self.assertEqual(parameters['uncertainty']['maxLength'], UNCERTAINTY_LIMIT)
        self.assertEqual(parameters['suggestions']['maxItems'], SUGGESTION_COUNT_LIMIT)
        self.assertEqual(parameters['suggestions']['items']['maxLength'], SUGGESTION_LIMIT)
        self.assertEqual(parameters['finding_reviews']['items']['properties']['reason']['maxLength'],
                         FINDING_REASON_LIMIT)

    def test_live_submission_over_the_limit_is_rejected_then_recovered(self):
        attempts = {'count': 0}

        def assess(context):
            attempts['count'] += 1
            report = current(context)
            if attempts['count'] == 1:
                report['ratings']['Accuracy']['rationale'] = 'x' * (RATING_RATIONALE_LIMIT + 1)
            return tool_turn('submit_review', report)

        model = ScriptModel([visible()], assess)
        agent = reviewer(model)
        result = agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE])
        self.assertEqual(result.decision, 'accept')
        rejected = agent.diagnostics['rejected_attempts']
        self.assertEqual([entry['validation_code'] for entry in rejected], ['review_text_limit'])
        self.assertEqual(rejected[0]['field'], 'ratings.Accuracy.rationale')
        self.assertEqual(rejected[0]['actual_characters'], RATING_RATIONALE_LIMIT + 1)
        support_phase = [phase for phase in agent.diagnostics['review_phases'] if phase['phase'] == 'support'][0]
        self.assertEqual((support_phase['status'], support_phase['model_attempts']), ('completed', 2))

    def test_overlong_finding_is_not_retained_and_remains_editable_on_retry(self):
        def assess(context):
            report = current(context)
            allowed = model.calls[-1][2][0]['parameters']['properties']['finding_reviews']['properties']
            report['finding_reviews'] = {
                item['finding_id']: {key: value for key, value in item.items() if key != 'finding_id'}
                for item in report['finding_reviews'] if item['finding_id'] in allowed}
            if len(model.calls) == 2:
                report['finding_reviews']['F1']['reason'] = 'x' * (FINDING_REASON_LIMIT + 1)
            return tool_turn('submit_review', report)

        model = ScriptModel([visible()], assess)
        agent = reviewer(model)
        answer = 'First summary [survey:CMT1].\n\nSecond summary [survey:CMT1].'
        result = agent.review('Explain.', answer, [SOURCE])
        self.assertEqual(result.decision, 'accept')
        self.assertEqual(len(result.findings), 2)
        rejected = agent.diagnostics['rejected_attempts']
        self.assertEqual([entry['validation_code'] for entry in rejected], ['review_text_limit'])
        self.assertEqual(rejected[0]['retained_finding_ids'], ['F2'])
        self.assertEqual(rejected[0]['missing_finding_ids'], ['F1'])
        retry = model.calls[2][2][0]['parameters']['properties']['finding_reviews']
        self.assertEqual(retry['required'], ['F1'])

    def test_new_legacy_shaped_response_cannot_bypass_the_current_bounds(self):
        def assess(context):
            report = json.loads(support_turn(context).calls[0].arguments)
            if len(model.calls) == 2:
                report['ratings']['Accuracy']['rationale'] = 'x' * (RATING_RATIONALE_LIMIT + 1)
            return tool_turn('submit_review', report)

        model = ScriptModel([visible()], assess)
        agent = reviewer(model)
        result = agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE])
        self.assertEqual(result.decision, 'accept')
        self.assertEqual([entry['field'] for entry in agent.diagnostics['rejected_attempts']],
                         ['ratings.Accuracy.rationale'])

    def test_stored_review_keeps_the_limits_it_was_produced_under(self):
        model = ScriptModel()
        agent = reviewer(model)
        blocks = [{'finding_id': 'F1', 'text': 'Summary [survey:CMT1].',
                   'citation_ids': [SOURCE['citation_id']]}]
        stored = json.loads(support_turn({'findings': blocks, 'evidence': [SOURCE]}).calls[0].arguments)
        stored['ratings']['Accuracy']['rationale'] = 'y' * 900
        stored['finding_reviews'][0]['reason'] = 'x' * 600
        # Read a serialized historical report; do not ask a model to generate a new one.
        report = agent.validate(json.loads(json.dumps(stored)))
        findings = agent.validate_findings(report, blocks, [SOURCE], require_assertions=True)
        self.assertEqual(findings[0]['status'], 'supported')
        self.assertEqual(len(findings[0]['reason']), 600)
        self.assertEqual(model.calls, [])

    def test_empty_or_whitespace_fields_are_disallowed_by_schema_and_validator(self):
        agent = reviewer(ScriptModel())
        props = agent.tools[0]['parameters']['properties']
        for field, schema in (('uncertainty', props['uncertainty']),
                              ('rationale', props['ratings']['properties']['Accuracy']['properties']['rationale'])):
            for blank in ('', ' \t\n'):
                with self.subTest(field=field, blank=repr(blank)):
                    report = self.base()
                    if field == 'uncertainty':
                        report[field] = blank
                    else:
                        report['ratings']['Accuracy'][field] = blank
                    self.assertTrue(len(blank) < schema['minLength'] or re.search(schema['pattern'], blank) is None)
                    with self.assertRaises(ValidationError):
                        agent.validate_review_bounds(report)


class FormatRecoveryTests(unittest.TestCase):
    def test_finding_reviews_sent_as_text_is_rejected_and_never_treated_as_a_review(self):
        attempts = {'count': 0}

        def assess(context):
            attempts['count'] += 1
            report = current(context)
            if attempts['count'] == 1:
                report['finding_reviews'] = json.dumps(report['finding_reviews'])
            return tool_turn('submit_review', report)

        model = ScriptModel([visible()], assess)
        agent = reviewer(model)
        result = agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE])
        self.assertEqual(result.decision, 'accept')
        entry = agent.diagnostics['rejected_attempts'][0]
        self.assertEqual(entry['validation_code'], 'finding_reviews_type')
        self.assertEqual(entry['expected_type'], 'dict')
        self.assertEqual(entry['actual_type'], 'str')
        self.assertIn('not as text', entry['reason'])
        # The rejected delivery released nothing; the retry supplied the judgments.
        self.assertEqual(result.findings[0]['status'], 'supported')

    def test_repeated_text_delivery_still_fails_the_phase(self):
        def assess(context):
            report = current(context)
            report['finding_reviews'] = json.dumps(report['finding_reviews'])
            return tool_turn('submit_review', report)

        model = ScriptModel([visible()], assess)
        agent = reviewer(model)
        with self.assertRaises(RuntimeError):
            agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE])
        self.assertEqual([entry['validation_code'] for entry in agent.diagnostics['rejected_attempts']],
                         ['finding_reviews_type'] * 3)


class TruncationRetryTests(unittest.TestCase):
    def test_support_review_retries_shorter_inside_the_existing_attempts(self):
        attempts = {'count': 0}

        def assess(context):
            attempts['count'] += 1
            if attempts['count'] == 1:
                raise OutputTokenLimit('Model output token budget exhausted before completion.')
            return support_turn(context)

        model = ScriptModel([visible()], assess)
        agent = reviewer(model)
        result = agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE])
        self.assertEqual(result.decision, 'accept')
        support_phase = [phase for phase in agent.diagnostics['review_phases'] if phase['phase'] == 'support'][0]
        self.assertEqual((support_phase['status'], support_phase['model_attempts']), ('completed', 2))
        self.assertEqual(support_phase['truncated_attempts'], 1)
        self.assertNotIn(COMPACT_SUPPORT_RETRY, model.instructions[1])
        self.assertIn(COMPACT_SUPPORT_RETRY, model.instructions[2])

    def test_completeness_review_retries_shorter_inside_the_existing_attempts(self):
        model = ScriptModel([OutputTokenLimit('Model output token budget exhausted before completion.'),
                             visible()])
        agent = reviewer(model)
        result = agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE])
        self.assertEqual(result.decision, 'accept')
        completeness_phase = agent.diagnostics['review_phases'][0]
        self.assertEqual((completeness_phase['status'], completeness_phase['model_attempts'],
                          completeness_phase['truncated_attempts']), ('completed', 2, 1))
        self.assertIn('cut off by the output limit', model.instructions[1])

    def test_three_truncations_still_fail_the_phase(self):
        def assess(context):
            raise OutputTokenLimit('Model output token budget exhausted before completion.')

        model = ScriptModel([visible()], assess)
        agent = reviewer(model)
        with self.assertRaises(OutputTokenLimit):
            agent.review('Explain.', 'Summary [survey:CMT1].', [SOURCE])
        support_phase = [phase for phase in agent.diagnostics['review_phases'] if phase['phase'] == 'support'][0]
        self.assertEqual((support_phase['status'], support_phase['model_attempts'],
                          support_phase['truncated_attempts']), ('failed', 3, 2))

    def test_finding_text_is_supplied_once_but_the_warning_still_locates_its_finding(self):
        answer = 'Recognition rose by 41 percent [survey:CMT1].'

        def assess(context):
            return tool_turn('submit_review', current(context))

        model = ScriptModel([visible()], assess)
        agent = reviewer(model)
        agent.review('Explain.', answer, [SOURCE], claims=[{
            'finding_id': 'FINDING_1', 'text': answer, 'citation_ids': [SOURCE['citation_id']],
            'kind': 'narrative', 'review_warnings': ['quantity']}])
        payload = model.calls[1][1]
        self.assertEqual(payload['review_warnings'], [{'finding_id': 'FINDING_1',
                         'citation_ids': [SOURCE['citation_id']], 'signals': ['quantity']}])
        self.assertEqual(payload['findings'][0]['text'], answer)


if __name__ == '__main__':
    unittest.main()
