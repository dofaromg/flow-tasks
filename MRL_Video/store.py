"""Transactional local queue, append-only version relationships and event chain."""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .model import VideoError, canonical, digest, validate

TERMINAL = {"SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"}


class Store:
    """A single-machine SQLite queue; one worker process owns a storage root."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / "MRL_video.sqlite3"
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, version_index INTEGER UNIQUE NOT NULL,
              parent_id TEXT REFERENCES jobs(id), request TEXT NOT NULL,
              request_sha256 TEXT NOT NULL, idempotency TEXT UNIQUE,
              state TEXT NOT NULL, phase TEXT NOT NULL, error TEXT,
              created_at TEXT NOT NULL, cancel_requested INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS events (
              seq INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL REFERENCES jobs(id),
              payload TEXT NOT NULL, previous_sha256 TEXT NOT NULL, sha256 TEXT NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def event(self, db, job_id: str, phase: str, detail: str = "") -> None:
        previous = db.execute("SELECT sha256 FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        prev = previous[0] if previous else "0" * 64
        payload = canonical({"job_id": job_id, "phase": phase, "detail": detail,
                             "observed_at": datetime.now(timezone.utc).isoformat()}).decode()
        sha = digest(prev.encode() + payload.encode())
        db.execute("INSERT INTO events(job_id,payload,previous_sha256,sha256) VALUES(?,?,?,?)",
                   (job_id, payload, prev, sha))

    def submit(self, request: dict, idempotency: str | None = None,
               parent_id: str | None = None) -> dict:
        request = validate(request)
        raw = canonical(request).decode()
        sha = digest(raw.encode())
        if idempotency is not None and (not isinstance(idempotency, str)
                                        or not 1 <= len(idempotency) <= 128):
            raise VideoError("Invalid idempotency key")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if idempotency:
                old = db.execute("SELECT * FROM jobs WHERE idempotency=?", (idempotency,)).fetchone()
                if old:
                    if old["request_sha256"] != sha or old["parent_id"] != parent_id:
                        raise VideoError("Idempotency key conflicts with another request")
                    return self.public(old)
            if parent_id and not db.execute("SELECT id FROM jobs WHERE id=?", (parent_id,)).fetchone():
                raise VideoError("Parent version unavailable")
            pending = db.execute("SELECT COUNT(*) FROM jobs WHERE state IN ('QUEUED','RUNNING')").fetchone()[0]
            if pending >= 32:
                raise VideoError("Queue capacity reached")
            index = db.execute("SELECT COALESCE(MAX(version_index),0)+1 FROM jobs").fetchone()[0]
            jid = "MRL_" + uuid.uuid4().hex
            db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                       (jid, index, parent_id, raw, sha, idempotency, "QUEUED", "QUEUED", None,
                        datetime.now(timezone.utc).isoformat(), 0))
            self.event(db, jid, "QUEUED")
        return self.get(jid)

    @staticmethod
    def public(row) -> dict:
        result = dict(row)
        result.pop("request", None)
        result.pop("idempotency", None)
        result["version_string"] = f"v1.{result['version_index']}"
        return result

    def get(self, jid: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
            if row is None:
                raise KeyError(jid)
            return self.public(row)

    def request(self, jid: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT request FROM jobs WHERE id=?", (jid,)).fetchone()
            if row is None:
                raise KeyError(jid)
            return json.loads(row[0])

    def list(self) -> list[dict]:
        with self.connect() as db:
            return [self.public(row) for row in db.execute(
                "SELECT * FROM jobs ORDER BY version_index DESC LIMIT 100")]

    def claim(self) -> str | None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT id FROM jobs WHERE state='QUEUED' ORDER BY version_index LIMIT 1").fetchone()
            if row is None:
                return None
            db.execute("UPDATE jobs SET state='RUNNING',phase='PREFLIGHT' WHERE id=?", (row[0],))
            self.event(db, row[0], "PREFLIGHT")
            return row[0]

    def update(self, jid: str, state: str, phase: str, error: str | None = None) -> None:
        if state not in TERMINAL | {"RUNNING"}:
            raise VideoError("Invalid state")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT state,cancel_requested FROM jobs WHERE id=?", (jid,)).fetchone()
            if old is None or old[0] != "RUNNING":
                raise VideoError("Job is not running")
            if state == "SUCCEEDED" and old[1]:
                state, phase = "CANCELLED", "CANCELLED"
            db.execute("UPDATE jobs SET state=?,phase=?,error=? WHERE id=?", (state, phase, error, jid))
            self.event(db, jid, phase, error or "")

    def cancel(self, jid: str) -> dict:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state FROM jobs WHERE id=?", (jid,)).fetchone()
            if row is None:
                raise KeyError(jid)
            if row[0] == "QUEUED":
                db.execute("UPDATE jobs SET state='CANCELLED',phase='CANCELLED',cancel_requested=1 WHERE id=?", (jid,))
                self.event(db, jid, "CANCELLED")
            elif row[0] == "RUNNING":
                db.execute("UPDATE jobs SET cancel_requested=1 WHERE id=?", (jid,))
                self.event(db, jid, "CANCEL_REQUESTED")
        return self.get(jid)

    def recover(self) -> None:
        """Interrupted work remains inspectable; never blindly replay external effects."""
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("SELECT id FROM jobs WHERE state='RUNNING'").fetchall()
            for row in rows:
                db.execute("UPDATE jobs SET state='INTERRUPTED',phase='INTERRUPTED' WHERE id=?", (row[0],))
                self.event(db, row[0], "INTERRUPTED")

    def verify_chain(self) -> bool:
        with self.connect() as db:
            prev = "0" * 64
            for row in db.execute("SELECT * FROM events ORDER BY seq"):
                if row["previous_sha256"] != prev or digest(prev.encode() + row["payload"].encode()) != row["sha256"]:
                    return False
                prev = row["sha256"]
        return True

    def history(self, jid: str) -> list[dict]:
        self.get(jid)
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM events WHERE job_id=? ORDER BY seq", (jid,))]

    def diff(self, left: str, right: str) -> dict:
        a, b = self.request(left), self.request(right)
        return {key: {"before": a.get(key), "after": b.get(key)}
                for key in sorted(a.keys() | b.keys()) if a.get(key) != b.get(key)}
