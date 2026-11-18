"""T6.5 tooling, offline: the --no-discovery switch and the gate 7 selection-only runner.

Scripted models only; the runner's live path is not exercised here.
"""
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import run_agent
import run_discovery_selection as selection
from agents import AccessScope
from agents.data_access import DiscoveryScope
from agents.discovery_section import SEPARATE_NOTE
from agents.discovery_tools import _period
from agents.findings import safe_follow_up
from agents.original import OriginalAgent
from agents.tools import SQLReader
from test_discovery_phase4 import DISCOVERY_DB, SCOPE, DiscoveryModel, PlanOverride, plan_args
from test_workflow_scenarios import QUESTION


class Failing(DiscoveryModel):
    def respond(self, instructions, history, tools, require_tool=False):
        self.log.append(('Discovery', tools[0]['name']))
        raise RuntimeError('Model request failed (HTTP 429).')


class ThreadRecording(DiscoveryModel):
    def respond(self, instructions, history, tools, require_tool=False):
        self.threads = getattr(self, 'threads', []) + [threading.current_thread().name]
        return super().respond(instructions, history, tools, require_tool)


class Broken(DiscoveryModel):
    """A defect, not a provider failure: it escapes DiscoveryAgent's own handling."""
    def respond(self, instructions, history, tools, require_tool=False):
        raise KeyError('defect')


class RoundFixUnitTests(unittest.TestCase):
    def test_a_declined_specialist_gets_its_own_limitation(self):
        self.assertEqual(safe_follow_up(['Cherry'], {'Cherry'}),
                         ['The numeric specialist declined its task, so that part of the request was not analyzed.'])
        self.assertEqual(safe_follow_up(['Cherry']), ['The numerical calculation or its population still requires correction.'])

    def test_ordinal_quarter_phrases_are_read(self):
        scope = DiscoveryScope('M14', '2025-10-01', '2026-06-30')
        for hint in ('the second quarter of 2026', 'Q2 of 2026', '2nd quarter 2026', 'second quarter',
                     'Q2 2026 (April 1 to June 30, 2026)', 'April 1 to June 30, 2026', 'between April 2026 and June 2026'):
            with self.subTest(hint=hint):
                period = _period(scope, hint)
                self.assertEqual((period['start'], period['end']), ('2026-04-01', '2026-06-30'))
                self.assertNotIn('hint_not_applied', period)
        self.assertEqual(_period(scope, 'fourth quarter of 2025')['end'], '2025-12-31')

    def test_cherry_schema_defines_the_beneficiary_team(self):
        notes = ' '.join(SQLReader.describe(SimpleNamespace(schema={}, survey_dimensions=[], scope=SCOPE))['notes'])
        self.assertIn('Beneficiary_Team is the team the work was for', notes)


@unittest.skipUnless(DISCOVERY_DB.exists(), 'discovery_v1 database has not been imported')
class NoDiscoverySwitchTests(unittest.TestCase):
    def run_original(self, plan=None, enabled=True, discovery=None):
        log, models = [], {}
        discovery = discovery or DiscoveryModel(log)
        discovery.log = log

        def factory(name):
            if name == 'Discovery':
                return discovery
            models.setdefault(name, PlanOverride(name, log, plan or plan_args()))
            models[name].histories = []
            return models[name]
        cache = tempfile.TemporaryDirectory()
        self.addCleanup(cache.cleanup)
        agent = OriginalAgent(DISCOVERY_DB, SCOPE, factory, 'offline-scripted-demo', retrieval='lexical',
                              cache_root=Path(cache.name), discovery_enabled=enabled)
        self.addCleanup(agent.close)
        self.models = models
        return agent.run(QUESTION), log, agent

    def test_disabled_run_makes_no_discovery_call_and_keeps_the_section_not_run(self):
        result, log, agent = self.run_original(enabled=False)
        self.assertEqual([tool for role, tool in log if role == 'Discovery'], [])
        self.assertEqual((result.discovery, result.discovery_section['status']), ({}, 'not_run'))
        self.assertFalse(result.discovery_section['present'])
        self.assertNotIn('Discovery', agent.planned_roles)
        self.assertEqual(agent.budget.refunded_models, 0)

    def test_disabled_run_keeps_the_subject_check(self):
        result, log, _ = self.run_original(plan_args(period_hint='2024-Q1'), enabled=False)
        self.assertEqual((result.status, result.task_outcome['reason_code']), ('declined', 'period_out_of_scope'))

    def test_specialists_get_the_resolved_person_not_only_the_name_as_written(self):
        # "Avery" is unique in M32's roster; the specialists must see the full identity to filter by ID.
        result, _, agent = self.run_original(plan_args(subject_kind='person', subject_names=['Avery']))
        self.assertEqual(agent.resolved_people, [{'employee_id': 'E0032', 'employee_name': 'Avery Adams'}])
        seen = ' '.join(self.models['Cherry'].histories)
        self.assertIn('E0032', seen)
        self.assertIn('resolved_people', seen)

    def test_team_question_passes_no_resolved_people(self):
        _, _, agent = self.run_original()
        self.assertEqual(agent.resolved_people, [])
        self.assertNotIn('resolved_people', ' '.join(self.models['Cherry'].histories))

    def test_question_period_narrows_the_scope_of_every_role(self):
        # T6.5 hard runs: "the second quarter of 2026" was not read, so Vanilla classified three survey waves.
        result, _, agent = self.run_original(plan_args(period_hint='the second quarter of 2026'))
        self.assertEqual((result.scope['start_date'], result.scope['end_date']), ('2026-04-01', '2026-06-30'))
        self.assertEqual({c['scope']['start_date'] for c in result.delegations}, {'2026-04-01'})
        self.assertEqual((result.discovery['period']['start'], result.discovery['period']['end']), ('2026-04-01', '2026-06-30'))
        self.assertEqual(agent.full_scope, SCOPE)

    def test_survey_metric_plan_with_a_period_rebuilds_cherry_on_the_narrowed_scope(self):
        # Live run 2026-11-18: planning built Cherry on the full window to read survey dimensions, so every
        # ask_cherry after narrowing failed specialist_scope_binding until the call limit.
        metrics = [{'metric': 'cross_team_contributions', 'dimension': None}, {'metric': 'survey_trend', 'dimension': 'Recognition'}]
        result, _, agent = self.run_original(plan_args(period_hint='Q2 2026 (April 1 to June 30, 2026)', metrics=metrics))
        self.assertEqual((result.scope['start_date'], result.scope['end_date']), ('2026-04-01', '2026-06-30'))
        self.assertEqual(agent.specialists['Cherry'].scope, agent.scope)
        cherry = [c for c in result.delegations if c['agent'] == 'Cherry']
        self.assertTrue(cherry and all(c['scope']['start_date'] == '2026-04-01' for c in cherry))
        self.assertNotIn('specialist_scope_binding', json.dumps(result.tool_trace))

    def test_discovery_runs_beside_original_and_refunds_only_its_own_calls(self):
        model = ThreadRecording([])
        result, _, agent = self.run_original(discovery=model)
        self.assertEqual(set(model.threads), {'echo-discovery'})
        self.assertEqual(result.discovery['usage']['calls'], 2)
        self.assertEqual(agent.budget.refunded_models, 2)
        # In parallel, Discovery's time is not taken from Original's clock, so nothing is paused.
        self.assertEqual(agent.budget.paused_seconds, 0.0)
        self.assertIn(SEPARATE_NOTE, result.discovery_section['rendered'])

    def test_a_question_without_a_period_keeps_the_callers_window(self):
        result, _, agent = self.run_original()
        self.assertEqual((result.scope['start_date'], result.scope['end_date']), (SCOPE.start_date, SCOPE.end_date))
        self.assertIs(agent.scope, SCOPE)

    def test_section_has_no_separate_note_without_findings(self):
        result, _, _ = self.run_original(discovery=DiscoveryModel([], findings=False))
        self.assertNotIn(SEPARATE_NOTE, result.discovery_section['rendered'])

    def test_unexpected_discovery_error_keeps_originals_answer_and_names_the_stage(self):
        result, _, _ = self.run_original(discovery=Broken([]))
        self.assertEqual(result.failure['stage'], 'discovery')
        self.assertNotEqual(result.status, 'complete')
        self.assertTrue(result.answer)
        self.assertEqual(result.discovery_section['status'], 'not_run')

    def test_cli_accepts_the_switch_only_for_a_new_original_run_on_discovery_v1(self):
        common = ['--manager', 'M14', '--question', 'How is my team doing?', '--no-discovery']
        for argv in (['original', *common],
                     ['vanilla', *common, '--database', 'discovery_v1', '--start', '2025-10-01', '--end', '2026-06-30']):
            with self.subTest(argv=argv), self.assertRaises(SystemExit), patch('sys.stderr'):
                run_agent.main(argv)


@unittest.skipUnless(DISCOVERY_DB.exists(), 'discovery_v1 database has not been imported')
class SelectionRunnerTests(unittest.TestCase):
    def test_selection_row_uses_the_real_summary_and_checks(self):
        log = []
        row = selection.select_team(DISCOVERY_DB, 'M32', DiscoveryModel(log), 'How is my team doing?', 120)
        self.assertEqual(log, [('Discovery', 'submit_selection')])
        self.assertEqual((row['status'], row['calls'], len(row['selected_employee_ids'])), ('done', 1, row['selection_count']))
        self.assertGreater(row['selection_count'], 0)

    def test_provider_failure_is_recorded_not_raised_and_left_out_of_the_scorer_input(self):
        row = selection.select_team(DISCOVERY_DB, 'M32', Failing([]), 'How is my team doing?', 120)
        self.assertEqual((row['status'], row['failure'], row['selected_employee_ids']), ('failed', '_ProviderFailure', []))
        report = selection.summarize({'M32': row}, 'gw_azure', 'q')
        self.assertEqual((report['teams'], report['failed']), ([], ['M32']))

    def test_selection_ids_fit_the_scorer_contract(self):
        # The scorer requires exactly selection_count distinct summary IDs outside the code slot.
        from agents.data_access import DiscoveryData, DiscoveryScope, DISCOVERY_RANGE
        from agents.discovery_tools import team_summary
        row = selection.select_team(DISCOVERY_DB, 'M14', DiscoveryModel([]), 'How is my team doing?', 120)
        data = DiscoveryData(DISCOVERY_DB, DiscoveryScope('M14', *DISCOVERY_RANGE))
        try:
            summary = team_summary(data)
        finally:
            data.close()
        chosen = row['selected_employee_ids']
        self.assertEqual(len(set(chosen)), summary['selection_count'])
        self.assertTrue(set(chosen) <= {line['employee_id'] for line in summary['lines']})
        self.assertFalse(set(chosen) & set(summary['lowest']))

    def test_dry_run_makes_no_call(self):
        with patch.object(selection, 'ModelRegistry', side_effect=AssertionError('no registry in a dry run')), \
                patch('builtins.print') as shown:
            self.assertEqual(selection.main(['--profile', 'gw_azure', '--output', 'unused.json',
                                             '--managers', 'M14,M32', '--dry-run']), 0)
        self.assertIn('need a selection call', shown.call_args[0][0])


if __name__ == '__main__':
    unittest.main()
