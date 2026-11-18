"""T6.1 gaps found by reading earlier tests; scripted models and read-only sources."""
import copy
from dataclasses import asdict
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from agents.discovery import DiscoveryAgent
from agents.discovery_section import NOT_RUN, pointer, provenance, render
from agents.runtime import RunBudget
from agents.discovery_tools import _person_items
from test_discovery_phase3 import FakeData, Scripted, judgment_for, team_resolution, transient
from test_discovery_signals import SyntheticData, row
import test_discovery_phase4 as phase4
from test_discovery_phase4 import plan_args


SELECT = {'selected_employee_ids': ['E05', 'E06', 'E07', 'E08', 'E09']}


class DiscoveryPhase6Tests(unittest.TestCase):
    def test_repeated_closure_rows_leave_room_for_independent_source_support(self):
        work = row('OP_contributions', 'WORK')
        rows = {'OP_contributions': [work], 'HR_recognition_events': [
            row('HR_recognition_events', f'R{i:02}', work_refs=work['work_refs']) for i in range(20)],
            'OP_collab_threads': [row('OP_collab_threads', 'THREAD', work_refs=work['work_refs'])]}
        items, capped, _ = _person_items(SyntheticData(rows), 'E1', {'Employee_ID': 'E1'}, rows, rows, 8)
        self.assertEqual(len(items), 8)
        self.assertTrue(capped)
        self.assertTrue({'HR_recognition_events', 'OP_contributions', 'OP_collab_threads'} <= {i['source'] for i in items})

    def test_no_candidates_costs_no_discovery_model_call(self):
        data = FakeData()
        data.people = data.people[:2]
        data.evidence = lambda: {}
        model, budget = Scripted(), RunBudget(seconds=300)
        result = DiscoveryAgent(data, model, budget).run('Who helped?', team_resolution(data))
        self.assertEqual(result['status'], 'no_candidates')
        self.assertEqual((model.requests, result['usage']['calls'], budget.models), ([], 0, 0))
        self.assertEqual(result['coverage']['people_reviewed'], 2)

    def test_schema_retry_checks_available_budget_before_calling(self):
        data, budget = FakeData(), RunBudget(seconds=300)
        model = Scripted({'selected_employee_ids': ['BAD']})
        remaining = budget.remaining
        def available():
            snapshot = remaining()
            if model.requests:
                snapshot['model_calls'] = 0
            return snapshot
        with patch.object(budget, 'remaining', side_effect=available):
            result = DiscoveryAgent(data, model, budget).run('Who helped?', team_resolution(data))
        self.assertEqual(result['status'], 'failed_budget')
        self.assertEqual((len(model.requests), result['usage']['calls'], result['usage']['schema_retries']), (1, 1, 1))
        self.assertEqual((budget.models, budget.refunded_models), (1, 1))

    def test_three_logical_calls_with_transport_and_shared_schema_retry(self):
        data, budget = FakeData(), RunBudget(seconds=300)
        model = Scripted(transient(), {'selected_employee_ids': ['BAD']}, SELECT, {'findings': 'bad'})
        with patch('agents.runtime.time.sleep'), patch('agents.runtime.record') as events:
            result = DiscoveryAgent(data, model, budget).run('Who helped?', team_resolution(data))
        retries = [c for c in events.call_args_list if c.args[0] == 'request_transport_retry']
        self.assertEqual(result['status'], 'failed_provider')
        self.assertEqual((result['usage']['calls'], result['usage']['schema_retries'], len(model.requests)), (3, 1, 4))
        self.assertEqual((budget.models, budget.refunded_models, len(retries)), (4, 4, 1))
        self.assertEqual(budget.models - len(retries), len(budget.request_costs))
        self.assertEqual(budget.remaining()['model_calls'], budget.model_limit)

    def test_top_five_plus_five_and_overflow_are_checked_and_rendered(self):
        data, budget = FakeData(), RunBudget(seconds=300)
        # Twelve valid outputs exercise the cardinality rule independently of model quality.
        findings = [judgment_for('E07')([])['findings'][0] for _ in range(12)]
        result = DiscoveryAgent(data, Scripted(SELECT, {'findings': findings, 'rejected': []}), budget).run(
            'Who helped?', team_resolution(data))
        self.assertEqual((len(result['findings']), len(result['more_findings']['listed']), result['more_findings']['not_listed']), (5, 5, 2))
        self.assertTrue(all(f['actions'] for f in result['findings']))
        self.assertTrue(all('actions' not in f for f in result['more_findings']['listed']))
        self.assertEqual(result['section']['finding_ids'], [f'DISC-{i}' for i in range(1, 11)])
        self.assertIn('Discovery found 10 findings', result['section']['rendered'])
        self.assertIn('2 more findings are not listed.', result['section']['rendered'])

    def test_pointer_and_provenance_for_every_status(self):
        data = FakeData()
        checked = DiscoveryAgent(data, Scripted(SELECT, judgment_for('E07')), RunBudget(seconds=300)).run(
            'Who helped?', team_resolution(data))
        expected = {'findings': 'Discovery found 1 finding about contributions to other teams.',
                    'partial': 'Discovery found 1 finding about contributions to other teams.',
                    'no_candidates': 'No hidden-contribution findings in the selected evidence.',
                    'no_findings': 'No hidden-contribution findings in the selected evidence.',
                    'all_withheld': 'Discovery could not produce verifiable findings.',
                    'failed_budget': 'Discovery could not complete the analysis.',
                    'failed_provider': 'Discovery could not complete the analysis.'}
        for status, line in expected.items():
            with self.subTest(status=status):
                result = copy.deepcopy(checked)
                result['status'] = status
                if status not in ('findings', 'partial'):
                    result['findings'] = []
                ids = ['DISC-1'] if result['findings'] else []
                text = render(result, {'E07': 'Person 7'})
                section = provenance(result, text)
                self.assertEqual(pointer(status, len(ids)), line)
                self.assertEqual(text.splitlines()[1], line)
                self.assertEqual(section, {'present': True, 'status': status, 'finding_ids': ids,
                                          'reviewed_by_zerosugar': False, 'checked_by_code': True, 'rendered': text})
        self.assertEqual(NOT_RUN['finding_ids'], [])


class DiscoveryPhase6IntegrationTests(unittest.TestCase):
    workflow = phase4.OriginalDiscoveryTests.workflow

    def test_recorded_temporal_comparison_stays_team_scoped(self):
        question = 'How are we doing compared with last quarter?'
        (_,), _, _, agent, _ = self.workflow(plan=plan_args(period_hint='last quarter'))
        result = agent.run(question)
        self.assertEqual(agent.original_request, question)
        self.assertNotEqual(result.status, 'declined')
        self.assertEqual(result.discovery['subject']['kind'], 'team')
        self.assertEqual((result.discovery['period']['start'], result.discovery['period']['end']),
                         ('2026-01-01', '2026-03-31'))
        self.assertTrue(result.discovery_section['present'])

    def test_original_failure_section_survives_artifact_and_manager_projection(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'Echo_UI' / 'backend'))
        import app as ui
        (result,), _, _, _, _ = self.workflow(fail_role='ZeroSugar')
        self.assertNotEqual(result.status, 'complete')
        self.assertTrue(result.discovery_section['present'])
        with tempfile.TemporaryDirectory() as folder, patch.object(ui, 'RUNS', Path(folder)):
            run = ui.RUNS / 'run_failure'
            run.mkdir()
            (run / 'meta.json').write_text(json.dumps({'id': 'run_failure', 'state': result.status,
                                                      'manager_id': 'M32'}), encoding='utf-8')
            (run / 'artifact.json').write_text(json.dumps(asdict(result)), encoding='utf-8')
            stored = json.loads((run / 'artifact.json').read_text(encoding='utf-8'))
            shown = ui.get_run('run_failure', view='manager')['artifact']
        self.assertEqual(stored['discovery_section'], result.discovery_section)
        self.assertEqual(shown['discovery_section'], result.discovery_section)
        self.assertFalse(shown['discovery_section']['reviewed_by_zerosugar'])
        self.assertTrue(shown['discovery_section']['checked_by_code'])
        self.assertFalse({'internal', 'usage', 'quotes'} & set(shown.get('discovery') or {}))  # allow-listed view only
        self.assertNotIn(result.discovery_section['rendered'], shown['answer'])

    def test_findings_then_declined_resets_section_in_same_agent(self):
        (first,), _, models, agent, _ = self.workflow()
        self.assertTrue(first.discovery_section['present'])
        models['Original'].plan = plan_args(subject_kind='other_team', subject_names=['Customer Renewals'])
        second = agent.run('How does my team compare with Customer Renewals?')
        self.assertEqual(second.status, 'declined')
        self.assertEqual(second.discovery_section, NOT_RUN)
        self.assertEqual(second.discovery, {})
        self.assertTrue(first.discovery_section['present'])

    def test_changed_replanned_name_applies_chosen_id_and_retains_period(self):
        question = 'What should I recognize Isabel for this quarter?'
        (first,), _, models, agent, _ = self.workflow(plan=plan_args(subject_kind='person', subject_names=['Unknown']))
        self.assertEqual(first.diagnostics['clarification_basis']['missing_field'], 'subject')
        models['Original'].plan = plan_args(subject_kind='person', subject_names=['Different planner name'], period_hint='this quarter')
        result = agent.run(question, {'name_as_written': 'Isabel', 'employee_id': 'E0010'})
        self.assertEqual(result.discovery['subject']['employee_ids'], ['E0010'])
        self.assertEqual((result.discovery['period']['start'], result.discovery['period']['end']), ('2026-04-01', '2026-06-30'))
        self.assertEqual(agent.original_request, question)
        self.assertEqual(result.discovery['coverage']['selection'], 'not_needed')

    def test_release_rejects_tampered_section_and_keeps_reviewed_answer(self):
        (result,), _, _, agent, _ = self.workflow()
        before = result.answer.encode('utf-8')
        self.assertEqual(before, agent.reviewed_candidate['answer'].encode('utf-8'))
        agent.attach_discovery(result)
        self.assertEqual(result.answer.encode('utf-8'), before)
        self.assertEqual(result.discovery_section, agent.discovery['section'])
        agent.discovery['section']['rendered'] += '\nTampered'
        with self.assertRaisesRegex(ValueError, 'differs from its checked result'):
            agent.attach_discovery(result)


if __name__ == '__main__':
    unittest.main()
