"""Manager sign-in for the Echo manager app, kept apart from the rest of the backend.

app.py only needs two lines:
    from auth import install_auth
    install_auth(app, database)

What it adds:
- auth.db (next to this file): each manager's salted password hash, and the key that signs sessions.
  Echo never stores the passwords themselves.
- manager_passwords.csv (next to this file): the readable demo passwords, written once for the team.
  Both files are listed in Echo_UI/.gitignore, so they never reach GitHub.
- /api/auth/login, /api/auth/logout and /api/auth/me.
- A gate in front of every team endpoint: a signed-in manager can only read their own team.

Demo passwords are simple on purpose: first name in lowercase + the number in the manager ID
(M14 Noah Harris -> noah14). Change them for anything beyond the demo.

The Technical console (/console) stays open by design. Its requests carry an X-Echo-Console header,
which this gate lets through when nobody is signed in, so the console keeps working as before.
"""

from __future__ import annotations

import csv
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
AUTH_DB = HERE / "auth.db"
PASSWORD_LIST = HERE / "manager_passwords.csv"
COOKIE = "echo_session"
SESSION_SECONDS = 8 * 60 * 60  # signed in for 8 hours, or until logging out
MAX_TRIES = 5  # wrong passwords in a row before a short lock
LOCK_SECONDS = 5 * 60
ITERATIONS = 200_000  # PBKDF2-SHA256 rounds

router = APIRouter()
_failures: dict[str, tuple[int, float]] = {}  # manager ID -> (wrong tries, time of the first one)
_secret: bytes = b""


# ---------- storage ----------

def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(AUTH_DB)
    connection.execute("CREATE TABLE IF NOT EXISTS credentials (manager_id TEXT PRIMARY KEY, salt TEXT NOT NULL, hash TEXT NOT NULL)")
    connection.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    return connection


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS).hex()


def demo_password(manager_id: str, name: str) -> str:
    first = re.sub(r"[^a-z]", "", name.split()[0].lower()) if name.strip() else "manager"
    return first + re.sub(r"\D", "", manager_id)


def _setup(database) -> None:
    """Create the sign-in store once: hash every manager's demo password and write the readable list."""
    global _secret
    with _connect() as db:
        row = db.execute("SELECT value FROM meta WHERE key = 'secret'").fetchone()
        if row is None:
            db.execute("INSERT INTO meta VALUES ('secret', ?)", (secrets.token_hex(32),))
            row = db.execute("SELECT value FROM meta WHERE key = 'secret'").fetchone()
        _secret = bytes.fromhex(row[0])
        if db.execute("SELECT COUNT(*) FROM credentials").fetchone()[0]:
            return
        try:
            with database() as data:
                managers = [(r["Manager_ID"], r["Manager_Name"]) for r in data.execute("SELECT Manager_ID, Manager_Name FROM HR_managers ORDER BY Manager_ID")]
        except Exception:
            return  # Echo's database isn't built yet; try again on the next start
        listing = []
        for manager_id, name in managers:
            password = demo_password(manager_id, name)
            salt = secrets.token_hex(16)
            db.execute("INSERT INTO credentials VALUES (?, ?, ?)", (manager_id.upper(), salt, _hash(password, salt)))
            listing.append((manager_id, name, password))
    with PASSWORD_LIST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Manager_ID", "Manager_Name", "Password"])
        writer.writerows(listing)


def _check(manager_id: str, password: str) -> bool:
    with _connect() as db:
        row = db.execute("SELECT salt, hash FROM credentials WHERE manager_id = ?", (manager_id,)).fetchone()
    if row is None:
        _hash(password, "00" * 16)  # same work either way, so timing doesn't reveal which IDs exist
        return False
    return hmac.compare_digest(_hash(password, row[0]), row[1])


# ---------- sessions: "M14.<expiry>.<signature>", signed so they survive a backend restart ----------

def _sign(text: str) -> str:
    return hmac.new(_secret, text.encode(), hashlib.sha256).hexdigest()


def _token(manager_id: str) -> str:
    body = f"{manager_id}.{int(time.time()) + SESSION_SECONDS}"
    return f"{body}.{_sign(body)}"


def session_manager(request_cookie: str | None) -> str | None:
    if not request_cookie or not _secret:
        return None
    try:
        manager_id, expires, signature = request_cookie.split(".")
    except ValueError:
        return None
    if not hmac.compare_digest(signature, _sign(f"{manager_id}.{expires}")):
        return None
    if not expires.isdigit() or int(expires) < time.time():
        return None
    return manager_id


# ---------- endpoints ----------

class Login(BaseModel):
    manager_id: str
    password: str


@router.post("/api/auth/login")
def login(body: Login, response: Response):
    manager_id = body.manager_id.strip().upper()
    count, first = _failures.get(manager_id, (0, 0.0))
    if count >= MAX_TRIES and time.time() - first < LOCK_SECONDS:
        raise HTTPException(429, "Too many tries. Please wait a few minutes and try again.")
    if not _check(manager_id, body.password):
        if time.time() - first > LOCK_SECONDS:  # an old streak of wrong tries no longer counts
            count, first = 0, time.time()
        _failures[manager_id] = (count + 1, first)
        raise HTTPException(401, "Manager ID or password is incorrect.")
    _failures.pop(manager_id, None)
    response.set_cookie(COOKIE, _token(manager_id), max_age=SESSION_SECONDS, httponly=True, samesite="lax", path="/")
    return {"manager_id": manager_id}


@router.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/api/auth/me")
def me(request: Request):
    manager_id = session_manager(request.cookies.get(COOKIE))
    if manager_id is None:
        raise HTTPException(401, "Not signed in.")
    return {"manager_id": manager_id}


# ---------- the gate in front of team data ----------

TEAM_PATH = re.compile(r"^/api/(?:managers/(?P<team>[^/]+)/|manager/(?P<code>[^/]+)$)")


class AuthGate:
    """Plain ASGI middleware: checks who is signed in before a team's data is read."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") == "OPTIONS":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        method = scope.get("method", "GET")
        target = None
        body = b""
        match = TEAM_PATH.match(path)
        if match:
            target = match.group("team") or match.group("code")
        elif path == "/api/recordings":
            query = dict(part.split("=", 1) for part in scope.get("query_string", b"").decode().split("&") if "=" in part)
            target = query.get("manager_id")
        elif path == "/api/runs" and method == "POST":
            # Read the body once to see whose team the question is about, then hand it on unchanged.
            more = True
            while more:
                message = await receive()
                body += message.get("body", b"")
                more = message.get("more_body", False)
            try:
                target = json.loads(body or b"{}").get("manager_id")
            except ValueError:
                target = None

            async def replay():
                return {"type": "http.request", "body": body, "more_body": False}

            receive = replay
        if target is None:
            return await self.app(scope, receive, send)

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        cookies = dict(part.strip().split("=", 1) for part in headers.get("cookie", "").split(";") if "=" in part)
        signed_in = session_manager(cookies.get(COOKIE))
        if signed_in is None:
            if headers.get("x-echo-console") == "1":
                return await self.app(scope, receive, send)  # the Technical console stays open by design
            return await _deny(send, 401, "Please sign in.")
        if signed_in.upper() != str(target).strip().upper():
            return await _deny(send, 403, "You can only see your own team.")
        return await self.app(scope, receive, send)


async def _deny(send, status: int, detail: str):
    payload = json.dumps({"detail": detail}).encode()
    await send({"type": "http.response.start", "status": status, "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": payload})


def install_auth(app, database) -> None:
    _setup(database)
    app.include_router(router)
    app.add_middleware(AuthGate)
