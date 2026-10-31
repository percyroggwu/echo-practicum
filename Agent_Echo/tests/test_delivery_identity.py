import unittest
from copy import deepcopy
from agents.delivery_diagnostics import bind_corrections, repair_context, duplication, request_size
from agents.grounding import render_answer, FactCatalog


class DeliveryIdentityTests(unittest.TestCase):
    def test_explicit_challenge_preserves_disposition_and_is_bounded(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from agents.original import OriginalAgent
        from agents.zero_sugar import VerificationResult
        for decision in ('accept', 'revise'):
            agent = OriginalAgent.__new__(OriginalAgent)
            correction = {'correction_id': 'C1', 'issue': 'Controlled issue'}
            prior = VerificationResult('revise', {}, [], '', [], 'live',
                                       findings=[{'finding_id': 'F1'}], corrections=[correction])
            revised = VerificationResult(decision, {}, [], '', [], 'live', corrections=[] if decision == 'accept' else [correction])
            agent.active_candidate = SimpleNamespace(answer='Saved answer.', evidence=[], visualization={},
                diagnostics={}, claims=[], grounding={}, sentiment={})
            agent.last_verdict = prior
            agent.challenged_candidates = set()
            agent.active_reviewer = SimpleNamespace(review=Mock(return_value=revised), diagnostics={})
            agent.original_request = 'Question'
            agent.child_results = []
            result = agent.challenge_corrections(['C1'], ['F1'], 'Reconsider against this saved answer.')
            self.assertEqual(result['decision'], decision)
            self.assertEqual(result['corrections'], revised.corrections)
            args = agent.active_reviewer.review.call_args
            self.assertEqual(args.args[1], 'Saved answer.')
            self.assertEqual(args.kwargs['previous_corrections'], [correction])
            with self.assertRaises(ValueError):
                agent.challenge_corrections(['C1'], ['F1'], 'Repeat.')

    def test_old_issue_is_not_described_as_current_same_number(self):
        from agents.findings import unresolved_follow_up
        from agents.zero_sugar import VerificationResult
        issue = 'Finding F5 contains contradicted assertions.'
        verdict = VerificationResult('revise', {}, [issue], '', [], 'live', candidate_id='new',
            corrections=[{'issue': issue, 'origin_candidate_id': 'old', 'citation_ids': ['A'],
                          'assertion_assessments': [{'reason': 'The source supports only one observation.'}]}])
        message = unresolved_follow_up(verdict)[0]
        self.assertIn('Earlier-draft', message)
        self.assertNotIn('Finding F5', message)

    def test_reordered_and_removed_block_never_uses_successor_number(self):
        correction = {'origin_candidate_id': 'draft1', 'origin_finding_id': 'F2'}
        block = {'value': {'text': 'Supported theme.', 'citation_ids': ['A']}}
        bind_corrections([correction], [{'finding_id': 'F2', 'text': 'Supported theme. [A]', 'citation_ids': ['A']}], {'B': block}, 'draft1')
        self.assertEqual(correction['origin_block_id'], 'B')
        bind_corrections([correction], [{'finding_id': 'F2', 'text': 'Different theme.', 'citation_ids': ['A']}], {'OTHER': block}, 'draft2')
        self.assertEqual(correction['origin_block_id'], 'B')
        self.assertFalse(repair_context([correction], {})[0]['origin_block_still_saved'])
        self.assertTrue(repair_context([correction], {'B': block})[0]['origin_block_still_saved'])

    def test_ambiguous_block_does_not_get_guessed(self):
        c = {'origin_candidate_id': 'one', 'origin_finding_id': 'F1'}
        b = {'value': {'text': 'Theme.', 'citation_ids': ['A']}}
        bind_corrections([c], [{'finding_id': 'F1', 'text': 'Theme.', 'citation_ids': ['A']}], {'B': b, 'C': deepcopy(b)}, 'one')
        self.assertNotIn('origin_block_id', c)

    def test_duplication_is_measured_without_modifying_content(self):
        paragraph = 'A sufficiently long example paragraph explaining a repeated observation and its important qualifications.'
        text = paragraph + ' [A]\n\n' + paragraph + ' [B]'
        self.assertEqual(duplication(text)['pair_count'], 1)
        self.assertEqual(duplication(paragraph)['pair_count'], 0)
        self.assertEqual(request_size('é', [], [])['instructions']['utf8_bytes'], 4)

    def test_new_rendering_suppresses_exact_quote_and_old_replay_keeps_it(self):
        scope = {'manager_id': 'M14', 'start_date': '2026-07-01', 'end_date': '2026-09-30'}
        evidence = [{'citation_id': 'A', 'text': 'Support was helpful.', 'scope': scope}]
        payload = {'fact_ids': [], 'interpretations': [{'text': 'Example: "Support was helpful."', 'citation_ids': ['A'], 'quote': 'Support was helpful.'}], 'proposals': []}
        catalog = FactCatalog(evidence, scope)
        new, _ = render_answer(payload, catalog, 'Original')
        old, _ = render_answer(payload, catalog, 'Original', version='source-facts-v4')
        self.assertEqual(new.count('Support was helpful.'), 1)
        self.assertEqual(old.count('Support was helpful.'), 2)
        payload['interpretations'][0]['text'] = 'A positive illustration.'
        absent, _ = render_answer(payload, catalog, 'Original')
        self.assertEqual(absent.count('Support was helpful.'), 1)
