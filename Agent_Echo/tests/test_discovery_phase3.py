"""Phase 3 offline checks: budget refund and timeout, the Discovery class, code checks, section, profile.

Models are scripted fakes; no provider is contacted.
"""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch

from agents.connections import ModelRegistry
from agents.data_access import DiscoveryData, DiscoveryScope
from agents.discovery import DiscoveryAgent, CALL_CAP
from agents.discovery_checks import SchemaFailure, check_selection, check_finding, pool_index, action_allowed
from agents.discovery_section import pointer, render, provenance, NOT_RUN
from agents.discovery_tools import resolve_subject, team_summary, prefilter
from agents.model import ModelTurn, ToolCall, send_request
from agents.request_pacing import DiscoveryTimeout, check_request_deadline, request_deadline, call_deadline
from agents.runtime import RunBudget

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'echo_discovery_v1.db'


def transient():
    error = RuntimeError('Model request timed out while waiting for the provider.')
    error.transient_transport = True
    return error


class Scripted:
    """Returns one scripted tool call (or raises) per request, in order."""

    def __init__(self, *steps):
        self.steps, self.requests = list(steps), []

    def respond(self, instructions, history, tools, require_tool=False):
        self.requests.append({'instructions': instructions, 'history': copy.deepcopy(history), 'tool': tools[0]['name']})
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        if callable(step):
            step = step(history)
        return ModelTurn('', [ToolCall('call', tools[0]['name'], json.dumps(step))])


class BudgetTests(unittest.TestCase):
    def test_refund_restores_remaining_without_changing_raw_counters(self):
        budget = RunBudget(model_limit=4, seconds=100)
        budget.consume('model')
        budget.consume('model')
        budget.refund(2, 30)
        self.assertEqual((budget.models, budget.refunded_models), (2, 2))
        self.assertEqual(budget.remaining()['model_calls'], 4)
        self.assertGreater(budget.remaining()['seconds'], 100)
        snapshot = budget.snapshot()
        self.assertEqual((snapshot['models'], snapshot['refunded_models'], snapshot['paused_seconds']), (2, 2, 30))
        for _ in range(4):  # Original's closing turn at exhaustion still completes after refunds.
            budget.consume('model')
        with self.assertRaises(RuntimeError):
            budget.consume('model')

    def test_paused_seconds_extend_the_effective_deadline(self):
        budget = RunBudget(seconds=0.01)
        time.sleep(0.02)
        with self.assertRaises(RuntimeError):
            budget.consume('model')
        budget.refund(0, 5)
        budget.consume('model')

    def test_hung_request_ends_at_the_call_deadline_and_is_counted_once(self):
        budget = RunBudget(seconds=300)
        model = Scripted(transient())
        with patch('agents.runtime.record') as events:
            budget.consume('model')
            with self.assertRaises(DiscoveryTimeout):
                budget.respond(model, 'i', [], [{'name': 't'}], True, call_deadline=time.monotonic() + 10)
        self.assertEqual((budget.models, len(budget.request_costs)), (1, 1))
        self.assertNotIn('request_transport_retry', [c.args[0] for c in events.call_args_list])

    def test_retry_inside_discovery_uses_only_the_time_left(self):
        budget = RunBudget(seconds=300)
        model = Scripted(transient(), {'ok': True})
        with patch('agents.runtime.time.sleep'), patch('agents.runtime.record') as events:
            budget.consume('model')
            budget.respond(model, 'i', [], [{'name': 't'}], True, call_deadline=time.monotonic() + 100)
        retries = [c for c in events.call_args_list if c.args[0] == 'request_transport_retry']
        self.assertEqual((budget.models, len(budget.request_costs), len(retries)), (2, 1, 1))
        self.assertEqual(budget.models - len(retries), len(budget.request_costs))

    def test_run_level_timeout_outside_discovery_is_still_runtime_error(self):
        token = request_deadline.set(time.monotonic() - 1)
        try:
            with self.assertRaises(RuntimeError) as caught:
                check_request_deadline()
            self.assertNotIsInstance(caught.exception, DiscoveryTimeout)
            inner = call_deadline.set(time.monotonic() - 1)
            with self.assertRaises(DiscoveryTimeout):
                check_request_deadline()
            call_deadline.reset(inner)
        finally:
            request_deadline.reset(token)

    def test_per_request_timeout_only_for_a_call_deadline(self):
        seen = []

        class Model:
            request_pacer, rate_limit_retries, request_count, request_timeout = None, 0, 0, 135

        def create(**options):
            seen.append(options.get('timeout'))
            return 'ok'
        send_request(Model(), 'responses', create, {})
        token, inner = request_deadline.set(time.monotonic() + 120), call_deadline.set(time.monotonic() + 120)
        try:
            send_request(Model(), 'responses', create, {})
        finally:
            call_deadline.reset(inner)
            request_deadline.reset(token)
        self.assertIsNone(seen[0])
        self.assertTrue(115 < seen[1] <= 120)


class ProfileTests(unittest.TestCase):
    def test_discovery_profile_is_derived_without_retries_or_pacing(self):
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, folder)
        config = folder / 'connections.json'  # A copy, so no private configuration is consulted.
        shutil.copyfile(ROOT / 'connections.json', config)
        registry = ModelRegistry(config, env_file=None)
        name = registry.profile_for('Discovery')
        profile = registry.config['profiles'][name]
        base = registry.config['profiles'][registry.profile_for('Original')]
        self.assertEqual((profile['timeout_seconds'], profile['max_retries']), (135, 0))
        self.assertNotIn('request_interval_seconds', profile)
        self.assertEqual((profile['model'], profile['endpoint'], profile['provider']), (base['model'], base['endpoint'], base['provider']))
        self.assertIn('Discovery', registry.describe())


def pool_item(record, employee, source='OP_collab_threads', beneficiary='M2', text='Helped the partner team close the export issue quickly.', **details):
    return {'source': source, 'record_id': record, 'event_date': '2026-05-01', 'recorded_date': '2026-05-01',
            'beneficiary_manager_id': beneficiary, 'work_refs': [{'type': 'thread', 'id': record}], 'text': text,
            'closing_context': {'recognition_state': details.pop('recognition', 'no_recognition_event_recorded'),
                                'absence_coverage': details.pop('coverage', 'complete')},
            'details': details}


def finding(**overrides):
    base = {'kind': 'person', 'employee_ids': ['E1'], 'beneficiary_manager_id': 'M2',
            'work_summary': 'Closed the export issue.', 'why_it_matters': 'The partner goal was met.',
            'visibility_state': 'no_feedback', 'recognition_state': 'not_recognized', 'evidence_ids': ['T1'],
            'quotes': [{'source_id': 'T1', 'text': 'close the export issue'}], 'action_types': ['A1']}
    base.update(overrides)
    return base


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.pool = {'people': [
            {'employee_id': 'E1', 'items': [pool_item('T1', 'E1'), pool_item('F1', 'E1', 'HR_recognition_feedback', shared_as_of=False),
                                            pool_item('U1', 'E1', coverage='unknown')], 'context': {}},
            {'employee_id': 'E2', 'items': [pool_item('T2', 'E2', beneficiary='M1')], 'context': {}}],
            'team_pattern_leads': []}
        self.index = pool_index(self.pool)

    def check(self, **overrides):
        return check_finding(finding(**overrides), self.pool, self.index, 'M1')

    def test_valid_finding_passes(self):
        self.assertIsNone(self.check())

    def test_synthetic_bad_outputs_are_withheld(self):
        cases = {'unknown_evidence_id': dict(evidence_ids=['FAKE'], quotes=[]),
                 'quote_not_in_source': dict(quotes=[{'source_id': 'T1', 'text': 'an invented quotation here'}]),
                 'person_not_in_pool': dict(employee_ids=['E9']),
                 'evidence_not_for_subject': dict(evidence_ids=['T2'], quotes=[]),
                 'own_team_help': dict(beneficiary_manager_id='M1'),
                 'not_recognized_under_unknown_coverage': dict(evidence_ids=['U1'], quotes=[]),
                 'visibility_not_supported': dict(visibility_state='praise_not_shared'),
                 'kind_mismatch': dict(kind='team_pattern')}
        for expected, overrides in cases.items():
            with self.subTest(check=expected):
                self.assertEqual(self.check(**overrides), expected)

    def test_action_triggers(self):
        good = finding()
        self.assertTrue(action_allowed('A1', good, self.pool, self.index))
        self.assertTrue(action_allowed('A2', good, self.pool, self.index))
        self.assertFalse(action_allowed('A4', good, self.pool, self.index))
        self.assertFalse(action_allowed('A6', good, self.pool, self.index))
        self.assertFalse(action_allowed('A3', good, self.pool, self.index))
        self.assertFalse(action_allowed('A1', finding(recognition_state='recognized'), self.pool, self.index))

    def test_bad_selections_are_refused(self):
        summary = {'lowest': ['E0'], 'lines': [{'employee_id': e} for e in ('E1', 'E2', 'E3')], 'selection_count': 2}
        self.assertEqual(check_selection(summary, ['E1', 'E2']), ['E1', 'E2'])
        for ids in (['E1', 'E9'], ['E1', 'E1'], ['E0', 'E1'], ['E1'], ['E1', 'E2', 'E3'], 'E1', [1, 2]):
            with self.subTest(ids=ids), self.assertRaises(SchemaFailure):
                check_selection(summary, ids)


class SectionTests(unittest.TestCase):
    def result(self, status, findings=(), listed=()):
        return {'status': status, 'findings': list(findings), 'more_findings': {'listed': list(listed), 'not_listed': 0},
                'period': {'start': '2025-10-01', 'end': '2026-06-30', 'as_of': '2026-06-30', 'narrowed_from_hint': False},
                'coverage': {'team_size': 20, 'people_reviewed': 10, 'selection': 'done', 'caps_hit': []},
                'internal': {'withheld': []}}

    def test_pointer_counts_shown_findings_and_none_without_findings(self):
        one = {'finding_id': 'DISC-1', 'kind': 'person', 'employee_ids': ['E1'], 'beneficiary_team': 'Partner',
               'work_summary': 'w', 'why_it_matters': 'y', 'recognition_state': 'unknown', 'visibility_state': 'no_feedback',
               'evidence_ids': ['T1'], 'quotes': [], 'actions': []}
        result = self.result('findings', [one], [{'finding_id': 'DISC-2', 'employee_id': 'E2', 'beneficiary_team': 'Partner'}])
        text = render(result, {'E1': 'Ana', 'E2': 'Bo'})
        self.assertIn('Discovery found 2 findings about contributions to other teams.', text)
        self.assertEqual(text, render(result, {'E1': 'Ana', 'E2': 'Bo'}))
        self.assertEqual(provenance(result, text)['finding_ids'], ['DISC-1', 'DISC-2'])
        for status in ('no_candidates', 'no_findings'):
            self.assertNotRegex(pointer(status, 0), r'\d')
        self.assertEqual(NOT_RUN['status'], 'not_run')
        self.assertFalse(provenance(result, text)['reviewed_by_zerosugar'])


class FakeData:
    """A 12-person team; E00-E04 are the least satisfied. Each person helped M2 once."""

    def __init__(self):
        self.scope = DiscoveryScope('M1', '2025-10-01', '2026-06-30')
        self.manager = {'Manager_ID': 'M1', 'Primary_Team': 'Home'}
        self.people = [{'Employee_ID': f'E{i:02}', 'Employee_Name': f'Person {i}'} for i in range(12)]

    def roster(self):
        return [dict(p) for p in self.people]

    def evidence(self):
        rows = {'HR_employee_performance': [
            {'source': 'HR_employee_performance', 'record_id': f'P{i}', 'Employee_ID': f'E{i:02}', 'Quarter': '2026-Q2',
             'Pulse_Score': 1 if i < 5 else 4, 'event_date': '2026-06-01', 'recorded_date': '2026-06-01'} for i in range(12)]}
        rows['OP_collab_threads'] = [
            {'source': 'OP_collab_threads', 'record_id': f'T{i:02}', 'Employee_ID': f'E{i:02}', 'employee_ids': [f'E{i:02}'],
             'event_date': '2026-05-01', 'recorded_date': '2026-05-01', 'quarter': '2026-Q2', 'beneficiary_manager_id': 'M2',
             'work_refs': [{'type': 'thread', 'id': f'T{i:02}'}], 'Topic': f'Helped the partner team close the export issue {i}.'}
            for i in range(12)]
        return rows

    def resolve_team(self, value):
        return [{'manager_id': m, 'team': t, 'own_team': m == 'M1'} for m, t in (('M1', 'Home'), ('M2', 'Partner')) if value in (m, t)]

    def team_manager(self, manager_id):
        return {'manager_id': 'M2', 'manager_name': 'Pat Partner', 'team': 'Partner'} if manager_id == 'M2' else None

    def sanitize(self, value):
        return value.replace('Pat Partner', '[Partner manager]') if isinstance(value, str) else value


def team_resolution(data):
    return resolve_subject_like(data, 'team', [p['Employee_ID'] for p in data.roster()])


def resolve_subject_like(data, kind, ids):
    return {'status': 'process', 'subject': {'kind': kind, 'employee_ids': ids, 'manager_id': 'M1', 'team': 'Home'},
            'period': {'start': '2025-10-01', 'end': '2026-06-30', 'as_of': '2026-06-30', 'narrowed_from_hint': False}}


def judgment_for(employee):
    record = 'T' + employee[1:]
    return lambda history: {'findings': [{
        'kind': 'person', 'employee_ids': [employee], 'beneficiary_manager_id': 'M2',
        'work_summary': 'Closed the export issue for Pat Partner.', 'why_it_matters': 'The partner team could continue.',
        'visibility_state': 'no_feedback', 'recognition_state': 'unknown', 'evidence_ids': [record],
        'quotes': [{'source_id': record, 'text': 'close the export issue'}], 'action_types': ['A1', 'A2', 'A6']}],
        'rejected': [{'employee_id': 'E00', 'reason': 'no_hidden_work'}]}


class DiscoveryAgentTests(unittest.TestCase):
    def run_agent(self, *steps, budget=None, resolution=None):
        data = FakeData()
        budget = budget or RunBudget(model_limit=10, seconds=300)
        model = Scripted(*steps)
        result = DiscoveryAgent(data, model, budget).run('Who helped other teams?', resolution or team_resolution(data))
        return result, model, budget

    def test_team_question_selection_then_judgment(self):
        result, model, budget = self.run_agent({'selected_employee_ids': ['E05', 'E06', 'E07', 'E08', 'E09']}, judgment_for('E07'))
        self.assertEqual([r['tool'] for r in model.requests], ['submit_selection', 'submit_findings'])
        selection_prompt = model.requests[0]['history'][0]['content']
        self.assertNotIn('Pulse', selection_prompt)
        self.assertNotIn('E00', selection_prompt)  # The satisfaction slot is not offered for selection.
        self.assertEqual(result['status'], 'findings')
        self.assertEqual((result['coverage']['people_reviewed'], result['coverage']['selection']), (10, 'done'))
        self.assertEqual(result['internal']['pool']['entered_by'], {'low_satisfaction': 5, 'selection': 5, 'whole_team': 0})
        found = result['findings'][0]
        self.assertEqual([a['action_type'] for a in found['actions']], ['A1', 'A2'])
        self.assertEqual(result['internal']['withheld'], [{'finding_id': 'DISC-1', 'check': 'action_trigger_mismatch', 'action_type': 'A6'}])
        self.assertEqual(found['work_refs'], [{'type': 'thread', 'id': 'T07'}])
        self.assertNotIn('Pat Partner', found['work_summary'])  # Redacted outside the recipient field.
        self.assertEqual(result['internal']['redactions'], 1)
        section = result['section']
        self.assertIn('Discovery found 1 finding about contributions to other teams.', section['rendered'])
        recipient_lines = [l for l in section['rendered'].splitlines() if 'Pat Partner' in l]
        self.assertTrue(recipient_lines and all('Pat Partner' in l and ('To:' in l or l.strip().startswith('Hi Pat Partner')) for l in recipient_lines))
        self.assertEqual((result['usage']['calls'], result['usage']['selection_calls']), (2, 1))
        self.assertEqual((budget.models, budget.refunded_models), (2, 2))
        self.assertEqual(budget.remaining()['model_calls'], 10)

    def test_shared_schema_retry_and_three_call_cap(self):
        result, model, budget = self.run_agent({'selected_employee_ids': ['E00']}, {'selected_employee_ids': ['E05', 'E06', 'E07', 'E08', 'E09']},
                                               {'findings': 'bad'})
        self.assertEqual(result['status'], 'failed_provider')
        self.assertEqual((result['usage']['calls'], result['usage']['schema_retries']), (CALL_CAP, 1))
        self.assertEqual(budget.remaining()['model_calls'], 10)

    def test_failed_selection_reviews_the_satisfaction_slot_only(self):
        result, model, _ = self.run_agent(RuntimeError('provider down'), judgment_for('E01'))
        self.assertEqual(result['coverage'], {'team_size': 12, 'people_reviewed': 5, 'selection': 'failed', 'caps_hit': []})
        self.assertEqual(result['status'], 'partial')

    def test_selection_timeout_still_judges_and_refunds(self):
        result, _, budget = self.run_agent(DiscoveryTimeout('deadline'), judgment_for('E01'))
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(budget.remaining()['model_calls'], 10)

    def test_named_people_make_no_selection_call(self):
        data = FakeData()
        result, model, _ = self.run_agent(judgment_for('E07'), resolution=resolve_subject_like(data, 'person', ['E07']))
        self.assertEqual([r['tool'] for r in model.requests], ['submit_findings'])
        self.assertEqual(result['coverage']['selection'], 'not_needed')

    def test_no_budget_left_spends_no_call(self):
        budget = RunBudget(model_limit=1, seconds=300)
        budget.consume('model')
        result, model, _ = self.run_agent(budget=budget)
        self.assertEqual(result['status'], 'failed_budget')
        self.assertEqual((model.requests, budget.models), ([], 1))

    def test_judgment_timeout_gives_failed_budget_and_full_refund(self):
        result, _, budget = self.run_agent({'selected_employee_ids': ['E05', 'E06', 'E07', 'E08', 'E09']}, DiscoveryTimeout('deadline'))
        self.assertEqual(result['status'], 'failed_budget')
        self.assertEqual(budget.remaining()['model_calls'], 10)
        self.assertIn('Discovery could not complete the analysis.', result['section']['rendered'])

    def test_all_withheld_and_no_findings(self):
        bad = lambda h: {'findings': [dict(judgment_for('E07')(h)['findings'][0], evidence_ids=['FAKE'], quotes=[])], 'rejected': []}
        result, _, _ = self.run_agent({'selected_employee_ids': ['E05', 'E06', 'E07', 'E08', 'E09']}, bad)
        self.assertEqual((result['status'], result['section']['finding_ids']), ('all_withheld', []))
        result, _, _ = self.run_agent({'selected_employee_ids': ['E05', 'E06', 'E07', 'E08', 'E09']}, {'findings': [], 'rejected': []})
        self.assertEqual(result['status'], 'no_findings')
        self.assertIn('No hidden-contribution findings in the selected evidence.', result['section']['rendered'])


@unittest.skipUnless(DB.exists(), 'discovery_v1 database has not been imported')
class RealDataTests(unittest.TestCase):
    def test_m32_team_question_runs_end_to_end_with_recorded_outputs(self):
        data = DiscoveryData(DB, DiscoveryScope('M32', '2025-10-01', '2026-06-30'))
        try:
            resolution = resolve_subject(data, {'subject_kind': 'team'})
            summary = team_summary(data)
            chosen = [line['employee_id'] for line in summary['lines']][:5]
            pool = prefilter(data, resolution, chosen)
            person = next(p for p in pool['people'] if any(i['source'] != 'HR_recognition_feedback' and i.get('text')
                                                           and i.get('beneficiary_manager_id') not in (None, 'M32') for i in p['items']))
            item = next(i for i in person['items'] if i['source'] != 'HR_recognition_feedback' and i.get('text')
                        and i.get('beneficiary_manager_id') not in (None, 'M32'))
            output = {'findings': [{'kind': 'person', 'employee_ids': [person['employee_id']],
                'beneficiary_manager_id': item['beneficiary_manager_id'], 'work_summary': 'Helped another team.',
                'why_it_matters': 'Recorded cross-team work.', 'visibility_state': 'no_feedback', 'recognition_state': 'unknown',
                'evidence_ids': [item['record_id']], 'quotes': [{'source_id': item['record_id'], 'text': item['text'][:40]}],
                'action_types': ['A5']}], 'rejected': []}
            budget = RunBudget(model_limit=32, seconds=300)
            model = Scripted({'selected_employee_ids': chosen}, output)
            result = DiscoveryAgent(data, model, budget).run('Who on my team helped other teams?', resolution)
            self.assertEqual(result['status'], 'findings')
            self.assertEqual(result['coverage']['people_reviewed'], 10)
            self.assertEqual(result['findings'][0]['actions'][0]['action_type'], 'A5')
            self.assertEqual(budget.remaining()['model_calls'], 32)
            selection, payload = (r['history'][0]['content'] for r in model.requests)
            self.assertNotIn('pulse', (selection + payload).casefold())
            # Characters/4 estimate against plan section 4: selection about 3-4k, judgment about 12-13k tokens.
            self.assertLess(len(selection), 4 * 5000)
            self.assertLess(len(payload), 4 * 15000)
        finally:
            data.close()


if __name__ == '__main__':
    unittest.main()
