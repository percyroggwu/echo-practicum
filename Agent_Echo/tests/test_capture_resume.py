"""Unrun regression fixtures for full capture and bounded live-phase resumption."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agents.capture import (capture_summary, checkpoint, checkpoint_progress, load_checkpoint, register_secret,
                            checkpoint_database_identity, database_identity)
from agents.data_access import ScopedData
from agents.execution_log import RunLog, logged_model
from agents.resume import resume_phase, resume_workflow
from agents.zero_sugar import ZeroSugarAgent
from test_agents import DATABASE, SequenceModel, tool_turn
from test_flow_improvements import plan
from fixtures import visible
from fixtures import support
from fixtures import PhaseModel, SCOPE


class Registry:
    def __init__(self, model):
        self.model, self.roles = model, []

    def profile_for(self, role):
        return 'fixture_profile'

    def get(self, role):
        self.roles.append(role)
        return logged_model(self.model, role, 'fixture_profile')


class CaptureResumeTests(unittest.TestCase):
    def test_old_workflow_code_is_rejected_before_any_model_request(self):
        registry = Registry(SequenceModel([]))
        saved = {'payload': {'mode': 'live'}, 'progress': {}, 'code_versions': {'old': 'baseline'}}
        with self.assertRaisesRegex(ValueError, 'matching live workflow code'):
            resume_workflow(saved, registry, DATABASE)
        self.assertEqual(registry.roles, [])

    def test_absent_capture_does_not_read_database_but_real_capture_stays_strict(self):
        with TemporaryDirectory() as folder:
            missing = Path(folder) / 'missing.db'
            self.assertIsNone(checkpoint_database_identity(missing))
            with self.assertRaises(FileNotFoundError):
                database_identity(missing)
            with RunLog(Path(folder)):
                with self.assertRaises(FileNotFoundError):
                    checkpoint_database_identity(missing)
                self.assertEqual(checkpoint_database_identity(DATABASE), database_identity(DATABASE))

    def test_full_capture_keeps_rejected_arguments_and_redacts_credentials(self):
        secret = 'fixture-private-api-credential-4829'
        register_secret(secret)
        arguments = {'unexpected': 'source text ' * 200, 'api_key': secret}
        with TemporaryDirectory() as folder:
            with RunLog(Path(folder)):
                model = logged_model(SequenceModel([tool_turn('submit_review', arguments)]), 'ZeroSugar', 'fixture_profile')
                model.respond('Review.', [{'role': 'user', 'content': 'Retained evidence.'}], [], True)
                path = Path(capture_summary()['exchanges'])
            text = path.read_text(encoding='utf-8')
        self.assertIn('source text ' * 200, text)
        self.assertNotIn(secret, text)
        self.assertIn('credential omitted', text)

    def test_checkpoint_roundtrip_preserves_inputs_and_detects_changed_payload(self):
        with TemporaryDirectory() as folder:
            with RunLog(Path(folder)):
                path = checkpoint('planning', 'Original', SCOPE.__dict__, {'question': 'Explain.', 'mode': 'live'})
                checkpoint_progress(path, status='failed')
            saved = load_checkpoint(path)
            self.assertEqual(saved['payload']['question'], 'Explain.')
            data = json.loads(Path(path).read_text(encoding='utf-8'))
            data['payload']['question'] = 'Changed.'
            Path(path).write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'payload has changed'):
                load_checkpoint(path)


    def test_source_changes_stop_resume_before_any_model_request(self):
        registry = Registry(SequenceModel([]))
        saved = {'scope': SCOPE.__dict__, 'kind': 'review', 'role': 'ZeroSugar',
                 'payload': {'mode': 'live', 'database_hash': 'different-source'}}
        with self.assertRaisesRegex(ValueError, 'database changed'):
            resume_phase(saved, registry, DATABASE)
        self.assertEqual(registry.roles, [])

    def test_planning_resume_stops_after_the_plan_without_analysis_or_delegation(self):
        registry = Registry(SequenceModel([plan(numbers=False)]))
        saved = {'scope': SCOPE.__dict__, 'kind': 'planning', 'role': 'Original',
            'run_id': 'parent', 'source_path': 'retained', 'code_versions': {},
            'payload': {'mode': 'live', 'profile': 'fixture_profile', 'question': 'Explain.'}}
        result = resume_phase(saved, registry, DATABASE)
        self.assertEqual(registry.roles, ['Original'])
        self.assertTrue(result.diagnostics['phase_only'])
        self.assertNotEqual(result.status, 'complete')



if __name__ == '__main__':
    unittest.main()
