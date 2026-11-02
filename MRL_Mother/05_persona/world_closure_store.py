"""Append-only transactional version store for the MRL L4 WorldModule.

origin_signature: MrLiouWord
The existing JSON files remain readable mirrors. SQLite is the durable,
single-writer transaction log; no historical event is removed by rewind.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sqlite3
from typing import Any, Callable, Dict, List


class WorldClosureIntegrityError(RuntimeError):
    """The history cannot be trusted; refuse further writes."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _event_hash(version_index: int, action: str, detail: dict,
                snapshot: dict, prev_hash: str) -> str:
    payload = dict(version_index=version_index, action=action, detail=detail,
                   snapshot=snapshot, prev_hash=prev_hash)
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


class WorldClosureStore:
    """Version-indexed immutable events and complete world-state snapshots."""

    def __init__(self, data_dir: pathlib.Path, initial: dict) -> None:
        self.path = pathlib.Path(data_dir) / "world_events.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                version_index INTEGER PRIMARY KEY,
                action TEXT NOT NULL,
                detail_json TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                event_hash TEXT NOT NULL
            )""")
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
                    state = self._validate_snapshot(initial)
                    self._insert(db, 0, "bootstrap", {"origin_signature": "MrLiouWord"}, state, "")
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        self.verify_history()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
        db.execute("PRAGMA busy_timeout=30000")
        db.execute("PRAGMA synchronous=FULL")
        return db

    @staticmethod
    def _validate_snapshot(snapshot: dict) -> dict:
        if not isinstance(snapshot, dict) or set(snapshot) != {"nodes", "state", "globe"}:
            raise ValueError("World snapshot must have nodes, state, and globe")
        if any(not isinstance(snapshot[key], dict) for key in ("nodes", "state", "globe")):
            raise ValueError("World snapshot components must be dictionaries")
        return json.loads(_canonical(snapshot))

    @staticmethod
    def _insert(db: sqlite3.Connection, version_index: int, action: str,
                detail: dict, snapshot: dict, prev_hash: str) -> None:
        digest = _event_hash(version_index, action, detail, snapshot, prev_hash)
        db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
                   (version_index, action, _canonical(detail), _canonical(snapshot),
                    prev_hash, digest))

    @staticmethod
    def _decode(row: tuple) -> dict:
        index, action, detail, snapshot, prev_hash, digest = row
        return dict(version_index=index, action=action, detail=json.loads(detail),
                    snapshot=json.loads(snapshot), prev_hash=prev_hash, event_hash=digest)

    def verify_history(self) -> dict:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM events ORDER BY version_index").fetchall()
        if not rows:
            raise WorldClosureIntegrityError("Missing bootstrap")
        expected_prev = ""
        for index, row in enumerate(rows):
            event = self._decode(row)
            if event["version_index"] != index or event["prev_hash"] != expected_prev:
                raise WorldClosureIntegrityError("World history chain broken at version " + str(index))
            expected_hash = _event_hash(index, event["action"], event["detail"],
                                        event["snapshot"], expected_prev)
            if expected_hash != event["event_hash"]:
                raise WorldClosureIntegrityError("World event hash mismatch at version " + str(index))
            expected_prev = expected_hash
        return {"versions": len(rows), "latest_version_index": len(rows) - 1,
                "merkle_tip": expected_prev, "integrity": "PASS"}

    def current_snapshot(self) -> dict:
        with self._connect() as db:
            row = db.execute("SELECT snapshot_json FROM events ORDER BY version_index DESC LIMIT 1").fetchone()
        return copy.deepcopy(json.loads(row[0]))

    @property
    def version_index(self) -> int:
        with self._connect() as db:
            return db.execute("SELECT MAX(version_index) FROM events").fetchone()[0]

    def load_version(self, index: int) -> dict:
        if not isinstance(index, int) or isinstance(index, bool) or index < 0:
            raise ValueError("Invalid version_index")
        with self._connect() as db:
            row = db.execute("SELECT snapshot_json FROM events WHERE version_index = ?", (index,)).fetchone()
        if row is None:
            raise KeyError("Unknown version_index: " + str(index))
        return copy.deepcopy(json.loads(row[0]))

    def history(self) -> List[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM events ORDER BY version_index").fetchall()
        return [self._decode(row) for row in rows]

    def commit(self, action: str, detail: dict, mutate: Callable[[dict], None]) -> dict:
        # SQLite BEGIN IMMEDIATE serializes concurrent local writers.
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                rows = db.execute("SELECT * FROM events ORDER BY version_index").fetchall()
                expected_prev = ""
                for index, row in enumerate(rows):
                    event = self._decode(row)
                    if (event["version_index"] != index or event["prev_hash"] != expected_prev
                            or event["event_hash"] != _event_hash(index, event["action"],
                                                     event["detail"], event["snapshot"], expected_prev)):
                        raise WorldClosureIntegrityError("World history modified at version " + str(index))
                    expected_prev = event["event_hash"]
                latest = self._decode(rows[-1])
                snapshot = self._validate_snapshot(latest["snapshot"])
                mutate(snapshot)
                snapshot = self._validate_snapshot(snapshot)
                self._insert(db, latest["version_index"] + 1, action, detail,
                             snapshot, latest["event_hash"])
                db.execute("COMMIT")
                return snapshot
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def restore_version(self, index: int) -> dict:
        # Restoration is a NEW event, never deletion of historical records.
        def restore(snapshot: dict) -> None:
            snapshot.clear()
            snapshot.update(self.load_version(index))
        return self.commit("restore_version", {"target_version_index": index}, restore)
