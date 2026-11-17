"""Phase 4 offline checks: Original's subject check, the Discovery step and the released section.

Every role is scripted (the demo model for Original, Cherry, Vanilla, Lime and ZeroSugar; a scripted
Discovery). Scripted judgments are not accuracy evidence.
"""
import json
from pathlib import Path
import tempfile
import unittest

from agents import AccessScope
from agents.model import ModelTurn, ToolCall
from agents.original import OriginalAgent
from test_agents import tool_turn
from test_workflow_scenarios import ScenarioModel, QUESTION

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_DB = ROOT / 'data' / 'echo_discovery_v1.db'
LEGACY_DB = ROOT / 'data' / 'echo.db'
SCOPE = AccessScope('M32', '2025-10-01', '2026-06-30')


def plan_args(**subject):
    base = {'needs_numbers': True, 'needs_text': True, 'needs_sentiment': False, 'include_chart': False,
            'clarification_question': None, 'clarification_basis': None,
            'metrics': [{'metric': 'cross_team_contributions', 'dimension': None}],
            'subject_kind': 'team', 'subject_names': [], 'period_hint': None, 'focus_hint': None}
    base.update(subject)
    return base


class DiscoveryModel:
    """Selects the first IDs of the summary table, then reports one finding built from the pool."""

    def __init__(self, log, fail=False, findings=True):
        self.log, self.fail, self.findings, self.histories = log, fail, findings, []

    def respond(self, instructions, history, tools, require_tool=False):
        name = tools[0]['name']
        self.log.append(('Discovery', name))
        self.histories.append(json.dumps(history))
        if self.fail:
            raise RuntimeError('Model request failed (HTTP 400). The provider rejected the request.')
        payload = json.loads(history[0]['content'])
        if name == 'submit_selection':
            rows = payload['summary'].splitlines()[1:]
            value = {'selected_employee_ids': [r.split('|')[0] for r in rows][:payload['count']]}
        else:
            value = {'findings': [], 'rejected': []}
            for person in payload['people'] if self.findings else []:
                item = next((i for i in person['items'] if i['source'] != 'HR_recognition_feedback' and i.get('text')
                             and i.get('beneficiary_manager_id') not in (None, payload['home_manager_id'])), None)
                if item:
                    value['findings'].append({'kind': 'person', 'employee_ids': [person['employee_id']],
                        'beneficiary_manager_id': item['beneficiary_manager_id'], 'work_summary': 'Helped another team.',
                        'why_it_matters': 'The help is recorded in the partner team\'s work.', 'visibility_state': 'no_feedback',
                        'recognition_state': 'unknown', 'evidence_ids': [item['record_id']],
                        'quotes': [{'source_id': item['record_id'], 'text': item['text'][:40]}], 'action_types': ['A5']})
                    break
        return ModelTurn(calls=[ToolCall('discovery-call', name, json.dumps(value))])


class PlanOverride(ScenarioModel):
    """The demo model for Original, with the plan replaced by a fixed one."""

    def __init__(self, name, log, plan, fail_role=None):
        super().__init__(name, log, fail_role=fail_role)
        self.plan = plan

    def respond(self, instructions, history, tools, require_tool=False):
        if self.agent_name == 'Original' and tools and tools[0]['name'] == 'submit_plan':
            self.log.append(('Original', 'submit_plan'))
            self.histories.append(json.dumps(history))
            return tool_turn('submit_plan', self.plan)
        self.histories.append(json.dumps(history))
        return super().respond(instructions, history, tools, require_tool)


@unittest.skipUnless(DISCOVERY_DB.exists(), 'discovery_v1 database has not been imported')
class OriginalDiscoveryTests(unittest.TestCase):
    def workflow(self, plan=None, discovery=None, fail_role=None, runs=None, database=DISCOVERY_DB, scope=SCOPE):
        log, models = [], {}
        discovery = discovery or DiscoveryModel(log)
        discovery.log = log

        def factory(name):
            if name == 'Discovery':
                return discovery
            models.setdefault(name, PlanOverride(name, log, plan or plan_args(), fail_role))
            models[name].histories = getattr(models[name], 'histories', [])
            return models[name]
        cache = tempfile.TemporaryDirectory()
        self.addCleanup(cache.cleanup)
        agent = OriginalAgent(database, scope, factory, 'offline-scripted-demo', retrieval='lexical', cache_root=Path(cache.name))
        self.addCleanup(agent.close)
        results = [agent.run(QUESTION, *args) for args in (runs or [()])]
        return results, log, models, agent, discovery

    def test_team_question_runs_discovery_once_and_appends_the_section_after_review(self):
        (result,), log, models, agent, discovery = self.workflow()
        calls = [tool for role, tool in log if role == 'Discovery']
        self.assertEqual(calls, ['submit_selection', 'submit_findings'])
        self.assertEqual(result.discovery['status'], 'findings')
        section = result.discovery_section
        self.assertTrue(section['present'])
        self.assertFalse(section['reviewed_by_zerosugar'])
        self.assertEqual(section['finding_ids'], ['DISC-1'])
        self.assertNotIn(section['rendered'], result.answer)
        self.assertNotIn('DISC-', result.answer)
        # Discovery is not a delegation: no child result, no handoff entry, not in ZeroSugar's input.
        self.assertNotIn('Discovery', {c['agent'] for c in result.delegations})
        self.assertIn('Discovery', agent.planned_roles)
        finding = result.discovery['findings'][0]
        for role in ('Original', 'ZeroSugar'):
            seen = ' '.join(models[role].histories)
            self.assertNotIn('DISC-', seen)
            self.assertNotIn('Checked by code', seen)
            self.assertNotIn('submit_findings', seen)
            self.assertNotIn(json.dumps(finding['work_summary'])[1:-1] + '"', seen)
        # Refunded: Original's budget is what it would be without Discovery.
        self.assertEqual(agent.budget.refunded_models, 2)
        self.assertEqual(agent.budget.remaining()['model_calls'],
                         agent.budget.model_limit - (agent.budget.models - 2))

    def test_out_of_scope_subject_is_declined_before_any_evidence_is_read(self):
        (result,), log, _, _, _ = self.workflow(plan=plan_args(subject_kind='other_team', subject_names=['Customer Renewals']))
        self.assertEqual(result.status, 'declined')
        self.assertEqual(result.task_outcome, {'status': 'declined', 'reason_code': 'subject_out_of_scope'})
        self.assertEqual(result.verification, {'decision': 'declined', 'drafts_checked': 0})
        self.assertEqual(result.guardrail['checked_by'], 'code')
        self.assertEqual(result.guardrail['detail'], 'Customer Renewals')
        self.assertEqual(len(result.next_steps), 2)
        self.assertEqual({role for role, _ in log}, {'Original'})  # Only planning ran.
        self.assertEqual(result.discovery_section['status'], 'not_run')

    def test_comparison_with_another_team_is_declined_and_beneficiary_focus_is_processed(self):
        (declined,), *_ = self.workflow(plan=plan_args(subject_kind='team', subject_names=['Customer Renewals']))
        self.assertEqual(declined.status, 'declined')
        (focused,), log, _, _, discovery = self.workflow(plan=plan_args(focus_hint='M17'))
        self.assertNotEqual(focused.status, 'declined')
        self.assertTrue(focused.discovery_section['present'])
        self.assertIn('"focus_hint": {"manager_id": "M17"', discovery.histories[-1].replace('\\"', '"'))
        # An unknown name and a name two managers share (M17, M49) both ask which team is meant.
        for hint in ('Infrastructure', 'Campaign Operations'):
            (unclear,), *_ = self.workflow(plan=plan_args(focus_hint=hint))
            self.assertEqual(unclear.status, 'needs_clarification')
            self.assertEqual(unclear.diagnostics['clarification_basis']['missing_field'], 'subject')

    def test_unresolved_name_gets_a_clarification_and_the_chosen_id_is_applied(self):
        plan = plan_args(subject_kind='person', subject_names=['Zzyzx'])
        (clarify, chosen), log, *_ = self.workflow(plan=plan, runs=[(), ({'name_as_written': 'Zzyzx', 'employee_id': 'E0010'},)])
        self.assertEqual(clarify.status, 'needs_clarification')
        self.assertEqual(clarify.diagnostics['clarification_basis']['missing_field'], 'subject')
        self.assertIsInstance(clarify.clarification_candidates, list)
        self.assertEqual(clarify.discovery_section['status'], 'not_run')
        # The second run resends the original question; the chosen ID wins without name matching.
        self.assertEqual(chosen.discovery['subject']['employee_ids'], ['E0010'])
        self.assertEqual(chosen.discovery['coverage']['selection'], 'not_needed')
        self.assertEqual([t for r, t in log if r == 'Discovery'], ['submit_findings'])

    def test_a_second_question_never_carries_the_first_section(self):
        (first, second), *_ = self.workflow(runs=[(), ()])
        self.assertTrue(first.discovery_section['present'])
        self.assertTrue(second.discovery_section['present'])
        self.assertIsNot(first.discovery_section, second.discovery_section)

    def test_section_is_published_when_original_fails(self):
        (result,), log, *_ = self.workflow(fail_role='ZeroSugar')
        self.assertNotEqual(result.status, 'complete')
        self.assertTrue(result.discovery_section['present'])
        self.assertEqual(result.discovery_section['status'], 'findings')

    def test_discovery_provider_failure_still_yields_originals_answer(self):
        (result,), log, _, agent, _ = self.workflow(discovery=DiscoveryModel([], fail=True))
        self.assertEqual(result.discovery['status'], 'failed_provider')
        self.assertIn('Discovery could not complete the analysis.', result.discovery_section['rendered'])
        self.assertTrue(result.answer)
        # A failed selection still leaves the 5 satisfaction people, so judgment runs too; both calls are refunded.
        self.assertEqual(agent.budget.refunded_models, 2)

    def test_discovery_v1_requires_the_fixed_range(self):
        with self.assertRaisesRegex(ValueError, 'fixed range'):
            OriginalAgent(DISCOVERY_DB, AccessScope('M32', '2025-10-01', '2026-03-31'), lambda name: None, 'offline-scripted-demo')

    def test_legacy_database_never_runs_discovery(self):
        legacy = AccessScope('M14', '2024-10-01', '2026-09-30')
        (result,), log, *_ = self.workflow(database=LEGACY_DB, scope=legacy)
        self.assertNotIn('Discovery', {role for role, _ in log})
        self.assertEqual(result.discovery_section, {'present': False, 'status': 'not_run', 'finding_ids': [],
                                                    'reviewed_by_zerosugar': False, 'checked_by_code': True, 'rendered': ''})


class CommandLineTests(unittest.TestCase):
    def test_discovery_v1_rejects_a_missing_or_different_range(self):
        import run_agent
        for dates in ([], ['--start', '2025-10-01'], ['--start', '2025-10-01', '--end', '2026-09-30']):
            with self.subTest(dates=dates), self.assertRaises(SystemExit):
                run_agent.main(['original', '--manager', 'M32', '--database', 'discovery_v1', '--question', 'Who helped?', *dates])

    @unittest.skipUnless(DISCOVERY_DB.exists(), 'discovery_v1 database has not been imported')
    def test_demo_run_records_discovery_in_the_report(self):
        import run_agent
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'demo.json'
            run_agent.main(['original', '--demo', '--manager', 'M32', '--database', 'discovery_v1', '--start', '2025-10-01',
                            '--end', '2026-06-30', '--charts-dir', folder, '--output', str(output)])
            report = json.loads(output.read_text(encoding='utf-8'))
        self.assertTrue(report['execution']['discovery_applied'])
        self.assertEqual(report['discovery_section']['status'], 'no_findings')  # The demo model never invents findings.
        self.assertEqual(report['discovery']['usage']['calls'], 2)
        self.assertNotIn('section', report['discovery'])

    def test_clarification_needs_original_and_a_question(self):
        import run_agent
        with self.assertRaises(SystemExit):
            run_agent.main(['cherry', '--manager', 'M32', '--clarification-name', 'Isabel', '--clarification-employee', 'E0010'])


if __name__ == '__main__':
    unittest.main()
