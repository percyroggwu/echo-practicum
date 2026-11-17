"""T5.5: fixed discovery range, clarification transport and manager projection, called directly (no server, no models)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Echo_UI" / "backend"))

from fastapi import HTTPException  # noqa: E402

import app as ui  # noqa: E402

QUESTION = "What should I recognize Isabel for this quarter?"
# M02 has two Isabels on the roster at 2026-06-30 (E2191 Isabel Reed, E2346 Isabel Keller).
CLARIFICATION = {"name_as_written": "Isabel", "employee_id": "E2346"}


def request(**extra):
    body = {"manager_id": "M02", "start_date": ui.FIXED_START, "end_date": ui.FIXED_END,
            "question": QUESTION, "mode": "live", "profile": "p"}
    return ui.RunRequest(**{**body, **extra})


class ScopeClarificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        patches = [patch.object(ui, "RUNS", Path(self.tmp.name)), patch.object(ui, "DISCOVERY", True),
                   patch.object(ui, "DATABASE", ui.DATABASES["discovery_v1"]),
                   patch.object(ui.threading, "Thread"), patch.object(ui.subprocess, "Popen")]
        self.popen = [p.start() for p in patches][-1]
        self.addCleanup(patch.stopall)
        self.addCleanup(self.tmp.cleanup)

    def command(self):
        return self.popen.call_args.args[0]

    def test_discovery_command_uses_fixed_range(self):
        ui.start_run(request())
        command = self.command()
        self.assertEqual(command[command.index("--database") + 1], "discovery_v1")
        self.assertEqual((command[command.index("--start") + 1], command[command.index("--end") + 1]), ("2025-10-01", "2026-06-30"))
        self.assertNotIn("--clarification-employee", command)

    def test_other_or_missing_dates_rejected(self):
        for extra in ({"start_date": "2025-11-01"}, {"end_date": "2026-09-30"}):
            with self.assertRaises(HTTPException) as caught:
                ui.start_run(request(**extra))
            self.assertEqual(caught.exception.status_code, 422)
        with self.assertRaises(HTTPException) as caught:  # omitted dates fall back to the legacy defaults, which differ
            ui.start_run(ui.RunRequest(manager_id="M02", question=QUESTION, mode="live", profile="p"))
        self.assertEqual(caught.exception.status_code, 422)
        self.popen.assert_not_called()

    def test_legacy_unchanged(self):
        with patch.object(ui, "DISCOVERY", False), patch.object(ui, "DATABASE", ui.DATABASES["legacy"]):
            ui.start_run(request(start_date="2024-10-01", end_date="2026-09-30"))
        command = self.command()
        self.assertNotIn("--database", command)
        self.assertEqual(command[command.index("--end") + 1], "2026-09-30")

    def test_clarification_outside_roster_rejected(self):
        for employee in ("E0001", "E9999"):  # a real employee of another team, and an unknown one
            with self.assertRaises(HTTPException) as caught:
                ui.start_run(request(clarification={"name_as_written": "Isabel", "employee_id": employee}))
            self.assertEqual(caught.exception.status_code, 422)
        self.popen.assert_not_called()

    def test_valid_clarification_is_passed_with_question_unchanged(self):
        ui.start_run(request(clarification=CLARIFICATION))
        command = self.command()
        self.assertEqual(command[command.index("--question") + 1], QUESTION)
        self.assertEqual(command[command.index("--clarification-name") + 1], "Isabel")
        self.assertEqual(command[command.index("--clarification-employee") + 1], "E2346")

    def test_demo_mode_applies_the_clarification(self):
        scope = ui.AccessScope("M02", ui.FIXED_START, ui.FIXED_END)
        self.assertIn("stop", ui.offline._discovery(ui.DATABASE, scope, QUESTION, False))  # two Isabels: asks
        self.assertEqual(ui.offline._discovery(ui.DATABASE, scope, QUESTION, False, CLARIFICATION), {})  # resolved
        path = Path(self.tmp.name) / "run_demo"
        path.mkdir()
        with patch.object(ui.offline, "build", return_value=({"status": "complete"}, [])) as build:
            ui.offline_run("run_demo", path, request(mode="demo", clarification=CLARIFICATION))
        self.assertEqual(build.call_args.args[3], CLARIFICATION)

    def test_recording_key_tells_requests_apart(self):
        args = ("M02", ui.FIXED_START, ui.FIXED_END, QUESTION)
        self.assertNotEqual(ui.recording_key(*args), ui.recording_key(*args, "E2346"))
        self.assertNotEqual(ui.recording_key(*args, "E2191"), ui.recording_key(*args, "E2346"))

    def test_meta_reports_database_and_range(self):
        with patch.object(ui, "DATABASE_NAME", "discovery_v1"):
            meta = ui.meta()
        self.assertEqual((meta["database"], meta["fixed_range"]), ("discovery_v1", {"start": "2025-10-01", "end": "2026-06-30"}))

    def test_manager_view_projects_section_and_candidates_not_discovery(self):
        artifact = {"question": QUESTION, "status": "needs_clarification", "answer": "Clarification needed",
                    "discovery_section": {"present": False, "status": "not_run", "finding_ids": [], "rendered": ""},
                    "discovery": {"internal": "secret"},
                    "clarification_candidates": [{"employee_id": "E2191", "name": "Isabel Reed", "team": "T", "manager_id": "M02"}],
                    "diagnostics": {"clarification_basis": {"missing_field": "subject", "missing_detail": "Two Isabels",
                                                            "blocking_reason": "x", "request_excerpt": "Isabel"}}}
        run = ui.RUNS / "run_a"
        run.mkdir()
        (run / "meta.json").write_text(json.dumps({"id": "run_a", "state": "needs_clarification"}), encoding="utf-8")
        (run / "artifact.json").write_text(json.dumps(artifact), encoding="utf-8")
        shown = ui.get_run("run_a", view="manager")["artifact"]
        self.assertEqual(shown["discovery_section"], artifact["discovery_section"])
        self.assertEqual(shown["clarification_candidates"][0]["employee_id"], "E2191")
        self.assertEqual(shown["clarification_basis"]["missing_field"], "subject")
        self.assertNotIn("discovery", shown)
        self.assertNotIn("secret", json.dumps(shown))


if __name__ == "__main__":
    unittest.main()
