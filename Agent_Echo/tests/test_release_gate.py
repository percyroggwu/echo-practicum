"""Release failure is propagated; the gate never calls a provider."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import check_release


class ReleaseGateTests(unittest.TestCase):
    def test_schema_smoke_uses_the_current_reference_contract(self):
        check_release.schema_smoke()

    def test_a_failed_suite_blocks_the_release(self):
        with patch.object(check_release.compileall, 'compile_dir', return_value=True), \
                patch.object(check_release.compileall, 'compile_file', return_value=True), \
                patch.object(check_release, 'schema_smoke'), \
                patch.object(check_release.subprocess, 'run', return_value=SimpleNamespace(returncode=1)) as run:
            self.assertEqual(check_release.main([]), 1)
            self.assertIn('unittest', run.call_args.args[0])

    def test_syntax_failure_prevents_running_the_suite(self):
        with patch.object(check_release.compileall, 'compile_dir', return_value=False), \
                patch.object(check_release.subprocess, 'run') as run:
            self.assertEqual(check_release.main([]), 1)
            run.assert_not_called()
