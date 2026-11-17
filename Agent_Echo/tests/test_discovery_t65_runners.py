"""T6.5 tooling, offline: the --no-discovery switch and the gate 7 selection-only runner.

Scripted models only; the runner's live path is not exercised here.
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_agent
import run_discovery_selection as selection
from agents import AccessScope
from agents.original import OriginalAgent
from test_discovery_phase4 import DISCOVERY_DB, SCOPE, DiscoveryModel, PlanOverride, plan_args
from test_workflow_scenarios import QUESTION


class Failing(DiscoveryModel):
    def respond(self, instructions, history, tools, require_tool=False):
        self.log.append(('Discovery', tools[0]['name']))
        raise RuntimeError('Model request failed (HTTP 429).')


@unittest.skipUnless(DISCOVERY_DB.exists(), 'discovery_v1 database has not been imported')
class NoDiscoverySwitchTests(unittest.TestCase):
    def run_original(self, plan=None, enabled=True):
        log, models = [], {}
        discovery = DiscoveryModel(log)

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
