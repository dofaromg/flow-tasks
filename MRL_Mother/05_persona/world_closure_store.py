"""Append-only transactional version store for the MRL L4 WorldModule.

origin_signature: MrLiouWord
The existing JSON files remain readable mirrors. SQLite is the durable,
single-writer transaction log; no historical event is removed by rewind.
"""
from __future__ import annotations

import copy
from contextlib import closing
import hashlib
import json
import pathlib
import sqlite3
from typing import Any, Callable, List


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

    def __init__(self, data_dir: pathlib.Path, initial: dict | Callable[[], dict]) -> None:
        self.path = pathlib.Path(data_dir) / "world_events.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                existed = db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='events'"
                ).fetchone() is not None
                db.execute("""CREATE TABLE IF NOT EXISTS events (
                    version_index INTEGER PRIMARY KEY,
                    action TEXT NOT NULL,
                    detail_json TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL
                )""")
                if db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
                    if existed:
                        raise WorldClosureIntegrityError("Missing bootstrap in existing journal")
                    state = self._validate_snapshot(initial() if callable(initial) else initial)
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

    def _verified_events(self, db: sqlite3.Connection) -> List[dict]:
        rows = db.execute("SELECT * FROM events ORDER BY version_index").fetchall()
        if not rows:
            raise WorldClosureIntegrityError("Missing bootstrap")
        events = []
        expected_prev = ""
        for index, row in enumerate(rows):
            try:
                event = self._decode(row)
                self._validate_snapshot(event["snapshot"])
                valid = (event["version_index"] == index
                         and event["prev_hash"] == expected_prev
                         and event["event_hash"] == _event_hash(
                             index, event["action"], event["detail"],
                             event["snapshot"], expected_prev))
            except (ValueError, TypeError) as exc:
                raise WorldClosureIntegrityError(
                    "Invalid world event at version " + str(index)) from exc
            if not valid:
                raise WorldClosureIntegrityError(
                    "World history modified at version " + str(index))
            expected_prev = event["event_hash"]
            events.append(event)
        return events

    def verify_history(self) -> dict:
        with closing(self._connect()) as db:
            events = self._verified_events(db)
        return {"versions": len(events), "latest_version_index": len(events) - 1,
                "merkle_tip": events[-1]["event_hash"], "integrity": "PASS"}

    def current_snapshot(self) -> dict:
        with closing(self._connect()) as db:
            return copy.deepcopy(self._verified_events(db)[-1]["snapshot"])

    @property
    def version_index(self) -> int:
        with closing(self._connect()) as db:
            return self._verified_events(db)[-1]["version_index"]

    def load_version(self, index: int) -> dict:
        if not isinstance(index, int) or isinstance(index, bool) or index < 0:
            raise ValueError("Invalid version_index")
        with closing(self._connect()) as db:
            events = self._verified_events(db)
        if index >= len(events):
            raise KeyError("Unknown version_index: " + str(index))
        return copy.deepcopy(events[index]["snapshot"])

    def history(self) -> List[dict]:
        with closing(self._connect()) as db:
            return self._verified_events(db)

    def commit(self, action: str, detail: dict, mutate: Callable[[dict], None]) -> dict:
        # SQLite BEGIN IMMEDIATE serializes concurrent local writers.
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                latest = self._verified_events(db)[-1]
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
