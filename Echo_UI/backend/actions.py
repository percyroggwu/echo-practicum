"""T5.1 manager_actions store: Discovery actions with decisions kept as versions.

Synthetic data only. The endpoints have no authentication (see README).
"""
import json
import re
import sqlite3
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import followup

DB_PATH = Path(__file__).resolve().parents[1] / "cache" / "manager_actions.db"  # tests point this to a temp file
RUNS_DIR = Path(__file__).resolve().parents[1] / "runs"                          # tests point this to a temp folder
DEMO_DECISION_DATE = "2026-07-01"  # the demo simulates "today"
MANAGER_ID = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
RUN_ID = re.compile(r"^[A-Za-z0-9_]{1,80}$")

router = APIRouter()

SCHEMA = """
CREATE TABLE IF NOT EXISTS actions (
    action_key TEXT PRIMARY KEY,          -- "<run_id>:<ACT-n-k>"; Discovery ids repeat across runs
    manager_id TEXT NOT NULL, run_id TEXT NOT NULL, source_action_id TEXT NOT NULL,
    finding_id TEXT NOT NULL, subject_kind TEXT, subject_id TEXT, beneficiary_team TEXT, recipient TEXT,
    allowed_refs TEXT NOT NULL,           -- JSON: the finding's work_refs, the only refs an edit may add
    beneficiary_manager_id TEXT           -- team names repeat across managers, so follow-up needs the ID
);
CREATE TABLE IF NOT EXISTS action_versions (
    action_key TEXT NOT NULL REFERENCES actions(action_key), version INTEGER NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('proposed','accepted','edited','dismissed')),
    action_type TEXT NOT NULL, draft_text TEXT NOT NULL, work_refs TEXT NOT NULL,
    reason TEXT, decided_on TEXT, PRIMARY KEY (action_key, version)
);
"""


class Store(sqlite3.Connection):
    """`with` commits and also closes (the stock connection leaves the file open, which locks it on Windows)."""

    def __exit__(self, *error):
        try:
            return super().__exit__(*error)
        finally:
            self.close()


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, factory=Store)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    if "beneficiary_manager_id" not in {r["name"] for r in db.execute("PRAGMA table_info(actions)")}:
        db.execute("ALTER TABLE actions ADD COLUMN beneficiary_manager_id TEXT")  # store file from before T5.2
    return db


def check_manager(manager_id):
    if not MANAGER_ID.match(manager_id):
        raise HTTPException(422, "Invalid manager ID.")
    return manager_id.upper()


def ref_key(ref):
    return (ref["type"], ref["id"])


class RegisterRequest(BaseModel):
    run_id: str
    action_ids: Optional[list[str]] = None


class WorkRef(BaseModel):
    type: Literal["contribution", "thread", "blocker", "incident"]
    id: str = Field(min_length=1, max_length=200)


class DecisionRequest(BaseModel):
    state: Literal["accepted", "edited", "dismissed"]
    reason: Optional[str] = Field(default=None, max_length=1000)
    draft_text: Optional[str] = Field(default=None, max_length=5000)
    action_type: Optional[Literal["A1", "A2", "A3", "A4", "A5", "A6"]] = None
    work_refs: Optional[list[WorkRef]] = None


def read_action(db, manager_id, action_key):
    head = db.execute("SELECT * FROM actions WHERE action_key = ? AND manager_id = ?", (action_key, manager_id)).fetchone()
    if not head:
        raise HTTPException(404, "Unknown action.")
    versions = [{"version": v["version"], "state": v["state"], "action_type": v["action_type"], "draft_text": v["draft_text"],
                 "work_refs": json.loads(v["work_refs"]), "reason": v["reason"], "decided_on": v["decided_on"]}
                for v in db.execute("SELECT * FROM action_versions WHERE action_key = ? ORDER BY version", (action_key,))]
    current = versions[-1]
    return {"action_id": head["action_key"], "source_action_id": head["source_action_id"], "run_id": head["run_id"],
            "finding_id": head["finding_id"], "subject_kind": head["subject_kind"], "subject_id": head["subject_id"],
            "beneficiary_team": head["beneficiary_team"], "beneficiary_manager_id": head["beneficiary_manager_id"], "recipient": json.loads(head["recipient"]) if head["recipient"] else None,
            "allowed_work_refs": json.loads(head["allowed_refs"]), "state": current["state"], "current": current, "versions": versions}


@router.post("/api/managers/{manager_id}/actions")
def register_actions(manager_id: str, request: RegisterRequest):
    manager_id = check_manager(manager_id)
    if not RUN_ID.match(request.run_id):
        raise HTTPException(422, "Invalid run ID.")
    path = RUNS_DIR / request.run_id
    try:
        meta = json.loads((path / "meta.json").read_text(encoding="utf-8-sig"))
        artifact = json.loads((path / "artifact.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise HTTPException(404, "Unknown run.")
    if str(meta.get("manager_id", "")).upper() != manager_id:
        raise HTTPException(403, "This run belongs to another manager.")
    found = [(f, a) for f in (artifact.get("discovery") or {}).get("findings", []) for a in f.get("actions", [])]
    wanted = set(request.action_ids) if request.action_ids is not None else None
    if wanted is not None and not wanted <= {a["action_id"] for _, a in found}:
        raise HTTPException(422, "Unknown action ID for this run.")
    keys = []
    with connect() as db:
        for finding, action in found:
            if wanted is not None and action["action_id"] not in wanted:
                continue
            key = f"{request.run_id}:{action['action_id']}"
            keys.append(key)
            if db.execute("SELECT 1 FROM actions WHERE action_key = ?", (key,)).fetchone():
                continue  # idempotent: never reset an existing decision
            refs = json.dumps(action.get("work_refs", finding.get("work_refs", [])))
            db.execute("INSERT INTO actions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (key, manager_id, request.run_id, action["action_id"], finding["finding_id"], action.get("subject_kind"),
                        action.get("subject_id"), action.get("beneficiary_team"),
                        json.dumps(action["recipient"]) if action.get("recipient") else None, refs,
                        action.get("beneficiary_manager_id")))
            db.execute("INSERT INTO action_versions VALUES (?,0,'proposed',?,?,?,NULL,NULL)",
                       (key, action["action_type"], action.get("draft_text", ""), refs))
        return {"actions": [read_action(db, manager_id, key) for key in keys]}


@router.get("/api/managers/{manager_id}/actions")
def list_actions(manager_id: str):
    manager_id = check_manager(manager_id)
    with connect() as db:
        keys = [r["action_key"] for r in db.execute("SELECT action_key FROM actions WHERE manager_id = ? ORDER BY rowid", (manager_id,))]
        return {"actions": [read_action(db, manager_id, key) for key in keys]}


@router.get("/api/managers/{manager_id}/actions/follow-up")
def follow_up_actions(manager_id: str):
    """{results: {action_id: Result}} for every saved action of the manager (shapes in followup.py)."""
    manager_id = check_manager(manager_id)
    return {"results": {a["action_id"]: followup.follow_up(a, manager_id) for a in list_actions(manager_id)["actions"]}}


@router.patch("/api/managers/{manager_id}/actions/{action_id}")
def decide_action(manager_id: str, action_id: str, request: DecisionRequest):
    manager_id = check_manager(manager_id)
    reason = (request.reason or "").strip()
    if request.state == "dismissed" and not reason:
        raise HTTPException(422, "A reason is required to dismiss an action.")
    edits = (request.draft_text, request.action_type, request.work_refs)
    if request.state != "edited" and any(e is not None for e in edits):
        raise HTTPException(422, "Only an edited decision may change the draft, type or references.")
    if request.state == "edited" and all(e is None for e in edits):
        raise HTTPException(422, "An edit must change the draft, the type or the references.")
    if request.draft_text is not None and not request.draft_text.strip():
        raise HTTPException(422, "The draft cannot be empty.")
    with connect() as db:
        action = read_action(db, manager_id, action_id)
        previous = action["current"]
        refs = previous["work_refs"]
        if request.work_refs is not None:
            refs = [r.model_dump() for r in request.work_refs]
            allowed = {ref_key(r) for r in action["allowed_work_refs"]}
            if any(ref_key(r) not in allowed for r in refs):
                raise HTTPException(422, "A work reference must come from the same finding.")
        db.execute("INSERT INTO action_versions VALUES (?,?,?,?,?,?,?,?)",
                   (action_id, previous["version"] + 1, request.state, request.action_type or previous["action_type"],
                    request.draft_text if request.draft_text is not None else previous["draft_text"],
                    json.dumps(refs), reason or None, DEMO_DECISION_DATE))
        return read_action(db, manager_id, action_id)
