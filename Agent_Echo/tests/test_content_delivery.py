"""Mechanical draft edits and release boundaries; no model-quality assertions."""

from copy import deepcopy
import json
import unittest

from agents import OriginalAgent
from agents.content import block_catalog, draft_capacity, resolve_answer
from agents.grounding import FactCatalog, render_answer
from agents.model import ModelTurn
from agents.runtime import AgentRunError, RunBudget, Specialist
from agents.validation import OutputTokenLimit, ValidationError, repair_feedback, rejection_diagnostic
from test_agents import SequenceModel, tool_turn
from test_flow_improvements import plan
from test_review_contract_v2 import visible
from test_review_contract_v3 import support
from test_review_stages import PhaseModel, SCOPE, SOURCE


def item(text):
    return {'text': text, 'citation_ids': [SOURCE['citation_id']], 'quote': None}


def additions(texts, remove=(), reuse=()):
    return {'fact_ids': [], 'interpretations': [{**item(text), 'quote_ref': None} for text in texts],
            'proposals': [], 'remove_ids': list(remove), 'reuse_ids': list(reuse)}


def wire(texts, remove=(), reuse=()):
    value = additions(texts, remove, reuse)
    for i in value['interpretations']:
        i.pop('quote')
    return value


class ContentDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.evidence = [deepcopy(SOURCE)]
        self.previous = block_catalog({'fact_ids': [], 'interpretations': [item(f'Saved view {n}.') for n in range(12)],
                                       'proposals': []}, self.evidence, SCOPE.__dict__)

    def resolve(self, payload, previous=None, available=None):
        return resolve_answer(payload, self.evidence, SCOPE.__dict__,
                              self.previous if available is None else available,
                              self.previous if previous is None else previous)

    def test_remove_one_add_one_is_valid_even_when_the_draft_is_full(self):
        result = self.resolve(wire(['A revised view.'], remove=[next(iter(self.previous))]))
        self.assertEqual(len(result['interpretations']), 12)
        self.assertNotIn(item('Saved view 0.'), result['interpretations'])
        render_answer(result, FactCatalog(self.evidence, SCOPE.__dict__), 'Original')

    def test_duplicate_additions_do_not_consume_another_slot(self):
        result = self.resolve(wire(['Saved view 0.']))
        self.assertEqual(len(result['interpretations']), 12)

    def test_overflow_reports_the_resolved_count_and_editable_ids_without_source_text(self):
        previous = dict(list(self.previous.items())[:11])
        with self.assertRaises(ValidationError) as caught:
            self.resolve(wire([f'New view {n}.' for n in range(12)]), previous=previous)
        error = caught.exception
        self.assertEqual(error.details['retained_count'], 11)
        self.assertEqual(error.details['new_count'], 12)
        self.assertEqual(error.details['merged_count'], 23)
        self.assertEqual(error.details['excess'], 11)
        self.assertEqual(error.details['removable_block_ids'], list(previous))
        feedback = repair_feedback(error)
        self.assertIn('remove_ids', feedback['correction'])
        self.assertEqual(feedback['remaining_slots'], 1)
        saved = rejection_diagnostic(error, 'Original', 'submit_grounded_answer', 1, 1)
        self.assertEqual(saved['merged_count'], 23)
        self.assertNotIn('Saved view', json.dumps(saved))
        self.assertNotIn(SOURCE['text'], json.dumps(saved))

    def test_reused_blocks_are_included_in_capacity(self):
        extra = block_catalog({'interpretations': [item('Specialist view.')], 'proposals': [], 'fact_ids': []},
                              self.evidence, SCOPE.__dict__)
        with self.assertRaises(ValidationError) as caught:
            self.resolve(wire([], reuse=extra), available={**self.previous, **extra})
        self.assertEqual(caught.exception.details['merged_count'], 13)
        self.assertEqual(caught.exception.details['reused_count'], 1)
        self.assertEqual(caught.exception.details['reused_block_ids'], list(extra))

    def test_changed_source_invalidates_retained_content(self):
        self.evidence[0]['text'] = 'Changed source.'
        with self.assertRaises(ValidationError) as caught:
            self.resolve(wire([]))
        self.assertEqual(caught.exception.details['validation_code'], 'answer_block_binding')

    def test_informational_capacity_does_not_change_the_edit_semantics(self):
        self.assertEqual(draft_capacity(self.previous)['interpretations']['remaining_slots'], 0)
        result = self.resolve(wire(['Replacement.'], remove=list(self.previous)))
        self.assertEqual(len(result['interpretations']), 1)

    def specialist(self, turns):
        model = SequenceModel(turns)
        agent = Specialist('Original', 'Use the supplied evidence.', model, SCOPE, [], {}, 'live')
        agent.source_grounding = True
        agent.draft_question = 'Explain.'
        agent.draft_blocks = deepcopy(self.previous)
        agent.reusable_blocks = deepcopy(self.previous)
        return agent, model

    def test_a_scripted_replacement_repairs_overflow_within_two_turns(self):
        texts = [f'New view {n}.' for n in range(12)]
        agent, model = self.specialist([tool_turn('submit_grounded_answer', wire(texts)),
            tool_turn('submit_grounded_answer', wire(texts, remove=self.previous))])
        result = agent.run('Explain.', self.evidence)
        self.assertEqual(len(model.histories), 2)
        self.assertEqual(len(result.claims), 12)
        feedback = json.loads(model.histories[-1][-1]['output'])
        self.assertEqual(feedback['merged_count'], 24)
        self.assertEqual(set(feedback['removable_block_ids']), set(self.previous))

    def test_three_rejections_stop_without_publishing_an_unreviewed_answer(self):
        bad = tool_turn('submit_grounded_answer', wire(['Another view.']))
        agent, model = self.specialist([bad] * 7)
        with self.assertRaises(AgentRunError) as caught:
            agent.run('Explain.', self.evidence)
        self.assertEqual(len(model.histories), 3)
        self.assertEqual(caught.exception.result.failure['error_category'], 'answer_delivery_stalled')
        self.assertEqual(caught.exception.result.findings, [])
        self.assertEqual(caught.exception.result.claims, [])
        self.assertFalse(caught.exception.result.diagnostics['rejected_attempts'][-1]['feedback_retry_available'])

    def test_stalled_repair_releases_only_the_previous_completed_review(self):
        texts = [f'Original view {n}.' for n in range(12)]
        # No delegation is required: prepared scoped evidence is supplied by this workflow fixture.
        original = SequenceModel([plan(numbers=False), tool_turn('submit_grounded_answer', wire(texts)),
                                 *[tool_turn('submit_grounded_answer', wire(['A changed view.'])) for _ in range(3)]])
        def review(context):
            report = support(context)
            report['finding_reviews'][0]['decision'] = 'revise'
            report['finding_reviews'][0]['assertions'][0]['assessment'] = 'insufficient_evidence'
            return tool_turn('submit_review', report)
        reviewer = PhaseModel([visible()], review)
        agent = OriginalAgent(None, SCOPE, lambda role: original if role == 'Original' else reviewer, 'live')
        self.addCleanup(agent.close)
        # Inject only the evidence handoff, retaining the real coordinator/renderer/reviewer/release flow.
        from unittest.mock import patch
        from agents.zero_sugar import ZeroSugarAgent
        from agents.runtime import Specialist as Base
        run = Base.run
        def prepared(this, question, initial_evidence=(), context=(), diagnostics=None):
            return run(this, question, initial_evidence or self.evidence, context, diagnostics)
        def trusted_review(*args, **kwargs):
            kwargs['document_lookup'] = {SOURCE['citation_id']: SOURCE}
            return ZeroSugarAgent(*args, **kwargs)
        with patch.object(Base, 'run', prepared), patch('agents.original.ZeroSugarAgent', side_effect=trusted_review):
            result = agent.run('Explain.')
        self.assertEqual(result.status, 'partial')
        self.assertEqual(result.failure['error_category'], 'answer_delivery_stalled')
        self.assertEqual(result.verification['completed_reviews'], 1)
        self.assertEqual(result.verification['released_candidate_id'], result.verification['reviews'][0]['candidate_id'])
        self.assertEqual(len(result.findings), 12)
        self.assertEqual(sum(f['status'] == 'supported' for f in result.findings), 11)
        self.assertNotIn('A changed view', result.answer)

    def test_original_repair_retries_once_after_output_truncation_within_shared_budget(self):
        class TruncateThenAnswer:
            def __init__(self, truncate_twice=False):
                self.calls, self.truncate_twice = [], truncate_twice

            def respond(self, instructions, history, tools, require_tool=False):
                self.calls.append((instructions, deepcopy(history)))
                if len(self.calls) == 1 or self.truncate_twice:
                    raise OutputTokenLimit('Model output token budget exhausted before completion.')
                return tool_turn('submit_grounded_answer', {
                    'fact_ids': [],
                    'interpretations': [{'text': 'Recognition receives positive comments.',
                                         'citation_ids': [SOURCE['citation_id']], 'quote_ref': None}],
                    'proposals': [], 'reuse_ids': [], 'remove_ids': []})

        budget = RunBudget(model_limit=4, tool_limit=4, seconds=30)
        model = TruncateThenAnswer()
        agent = Specialist('Original', 'Prepare the answer.', model, SCOPE, [], {}, 'live', budget=budget)
        agent.source_grounding = True
        agent.repair_round = 1
        result = agent.run('Explain recognition.', [self.evidence[0]])
        self.assertIn('Recognition receives positive comments.', result.answer)
        self.assertEqual((len(model.calls), budget.models), (2, 2))
        self.assertIn('previous repair response was cut off', model.calls[1][0])
        self.assertIn('reuse_ids', model.calls[1][0])

    def test_second_original_repair_truncation_still_fails_after_two_budgeted_calls(self):
        class AlwaysTruncate:
            def __init__(self):
                self.calls = 0

            def respond(self, instructions, history, tools, require_tool=False):
                self.calls += 1
                raise OutputTokenLimit('Model output token budget exhausted before completion.')

        budget = RunBudget(model_limit=4, tool_limit=4, seconds=30)
        model = AlwaysTruncate()
        agent = Specialist('Original', 'Prepare the answer.', model, SCOPE, [], {}, 'live', budget=budget)
        agent.source_grounding = True
        agent.repair_round = 1
        with self.assertRaises(AgentRunError):
            agent.run('Explain recognition.', [self.evidence[0]])
        self.assertEqual((model.calls, budget.models), (2, 2))
