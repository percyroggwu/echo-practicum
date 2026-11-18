"""T5.1 manager_actions store: synthetic run fixture in a temp folder, no workflow, no network."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Echo_UI" / "backend"))

from fastapi import HTTPException  # noqa: E402

import app as ui  # noqa: E402,F401  (the app must import and mount the router)
import actions  # noqa: E402

REFS = [{"type": "thread", "id": "T1"}, {"type": "contribution", "id": "C1"}]
ACTIONS = [
    {"action_id": "ACT-1-1", "action_type": "A1", "subject_kind": "person", "subject_id": "E1", "beneficiary_team": "Partner",
     "work_refs": REFS, "recipient": None, "draft_text": "Recognize E1."},
    {"action_id": "ACT-1-2", "action_type": "A2", "subject_kind": "person", "subject_id": "E1", "beneficiary_team": "Partner",
     "work_refs": REFS, "recipient": {"manager_id": "M2", "name": "Pat"}, "draft_text": "Ask Pat."},
]


class Reply:
    def __init__(self, status, body):
        self.status_code, self.body = status, body

    def json(self):
        return self.body


class DirectClient:
    """Calls the route handlers directly: TestClient needs a socketpair, which the offline runner blocks."""

    def call(self, method, url, body=None):
        parts = url.split("/")  # "", api, managers, id, actions[, action_id]
        try:
            if method == "POST":
                result = actions.register_actions(parts[3], actions.RegisterRequest(**body))
            elif method == "GET":
                result = actions.list_actions(parts[3])
            else:
                result = actions.decide_action(parts[3], "/".join(parts[5:]), actions.DecisionRequest(**body))
        except HTTPException as error:
            return Reply(error.status_code, {})
        except ValueError:  # pydantic validation, the 422 FastAPI would return
            return Reply(422, {})
        return Reply(200, result)

    def post(self, url, json):
        return self.call("POST", url, json)

    def get(self, url):
        return self.call("GET", url)

    def patch(self, url, json):
        return self.call("PATCH", url, json)


class ActionsStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.saved = (actions.DB_PATH, actions.RUNS_DIR)
        actions.DB_PATH, actions.RUNS_DIR = root / "manager_actions.db", root / "runs"
        for run_id, manager in (("run_a", "M1"), ("run_b", "M9")):
            path = actions.RUNS_DIR / run_id
            path.mkdir(parents=True)
            (path / "meta.json").write_text(json.dumps({"manager_id": manager}))
            (path / "artifact.json").write_text(json.dumps({"discovery": {"findings": [
                {"finding_id": "DISC-1", "work_refs": REFS, "actions": ACTIONS}]}}))
        self.client = DirectClient()
        self.key = "run_a:ACT-1-1"
        self.url = f"/api/managers/M1/actions/{self.key}"

    def tearDown(self):
        actions.DB_PATH, actions.RUNS_DIR = self.saved
        self.tmp.cleanup()

    def register(self, **extra):
        return self.client.post("/api/managers/M1/actions", json={"run_id": "run_a", **extra})

    def test_router_mounted(self):
        self.assertIn("/api/managers/{manager_id}/actions", ui.app.openapi()["paths"])

    def test_post_proposes_and_is_idempotent(self):
        first = self.register().json()["actions"]
        self.assertEqual([a["state"] for a in first], ["proposed", "proposed"])
        self.client.patch(self.url, json={"state": "accepted"})
        self.register()
        listed = self.client.get("/api/managers/M1/actions").json()["actions"]
        self.assertEqual(len(listed), 2)
        self.assertEqual(listed[0]["state"], "accepted")  # repost did not reset the decision

    def test_decisions_persist_across_connections(self):
        self.register()
        self.client.patch(self.url, json={"state": "dismissed", "reason": "Not now"})
        with actions.connect() as db:  # a fresh connection stands in for a restart
            rows = db.execute("SELECT state, reason, decided_on FROM action_versions WHERE action_key = ? ORDER BY version",
                              (self.key,)).fetchall()
        self.assertEqual([r["state"] for r in rows], ["proposed", "dismissed"])
        self.assertEqual((rows[1]["reason"], rows[1]["decided_on"]), ("Not now", actions.DEMO_DECISION_DATE))

    def test_dismiss_requires_reason(self):
        self.register()
        for body in ({"state": "dismissed"}, {"state": "dismissed", "reason": "  "}):
            self.assertEqual(self.client.patch(self.url, json=body).status_code, 422)
        self.assertEqual(self.client.patch(self.url, json={"state": "bogus"}).status_code, 422)

    def test_edit_work_refs(self):
        self.register()
        foreign = self.client.patch(self.url, json={"state": "edited", "work_refs": REFS[:1] + [{"type": "thread", "id": "X"}]})
        self.assertEqual(foreign.status_code, 422)
        ok = self.client.patch(self.url, json={"state": "edited", "work_refs": REFS[:1], "action_type": "A5", "draft_text": "New"})
        self.assertEqual(ok.status_code, 200)
        current = ok.json()["current"]
        self.assertEqual((current["work_refs"], current["action_type"], current["draft_text"]), (REFS[:1], "A5", "New"))

    def test_other_manager_run_and_actions_rejected(self):
        self.assertEqual(self.client.post("/api/managers/M1/actions", json={"run_id": "run_b"}).status_code, 403)
        self.assertEqual(self.client.post("/api/managers/M1/actions", json={"run_id": "../x"}).status_code, 422)
        self.assertEqual(self.client.get("/api/managers/bad id/actions").status_code, 422)
        self.register()
        self.assertEqual(self.client.patch(f"/api/managers/M9/actions/{self.key}", json={"state": "accepted"}).status_code, 404)
        self.assertEqual(self.client.get("/api/managers/M9/actions").json()["actions"], [])

    def test_history_kept(self):
        self.register(action_ids=["ACT-1-1"])
        self.client.patch(self.url, json={"state": "accepted"})
        self.client.patch(self.url, json={"state": "edited", "draft_text": "Changed"})
        versions = self.client.get("/api/managers/M1/actions").json()["actions"][0]["versions"]
        self.assertEqual([(v["version"], v["state"]) for v in versions], [(0, "proposed"), (1, "accepted"), (2, "edited")])
        self.assertEqual(versions[0]["draft_text"], "Recognize E1.")


if __name__ == "__main__":
    unittest.main()
