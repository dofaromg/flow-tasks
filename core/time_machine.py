"""Version views over the existing FlowCoreLoop trace; no second history store.

origin_signature: MrLiouWord
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
import sys
from pathlib import Path
from types import MappingProxyType


_WORKFLOW = str(Path(__file__).resolve().parents[1] / "MRL_Mother/09_workflow")
if _WORKFLOW not in sys.path:
    sys.path.insert(0, _WORKFLOW)
from MRL_utils import ORIGIN_SIGNATURE


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class TimeMachine:
    """Append snapshots and branches to the existing Tracer Merkle timeline.

    Mounts are detached immutable data views, never writable filesystem mounts.
    Use a branch handle's commit() to append a descendant snapshot.
    """

    def __init__(self, tracer):
        self.tracer = tracer
        root = Path(__file__).resolve().parents[1]
        seal = json.loads((root / "core/law.seal.json").read_text(encoding="utf-8"))
        hashes = []
        for leaf in seal["leaves"]:
            actual = hashlib.sha256((root / leaf["path"]).read_bytes()).hexdigest()
            if actual != leaf["sha256"]:
                raise ValueError("root_law_tampered")
            hashes.append(actual)
        self.law_seal = seal
        if hashlib.sha256("".join(hashes).encode()).hexdigest() != seal["merkle_root"]:
            raise ValueError("root_law_seal_mismatch")

    def _events(self):
        path = Path(self.tracer.trace_path)
        if not path.exists():
            return []
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        previous = "0" * 64
        for event in events:
            body = {k: v for k, v in event.items() if k != "merkle_root"}
            leaf = hashlib.sha256(_json(body).encode()).hexdigest()
            root = hashlib.sha256((previous + leaf).encode()).hexdigest()
            if root != event["merkle_root"]:
                raise ValueError("trace_merkle_mismatch")
            previous = root
        if previous != self.tracer._state["merkle_root"]:
            raise ValueError("trace_head_mismatch")
        return events

    def _versions(self):
        return [e["payload"] for e in self._events() if e["event_type"] == "timemachine_version"]

    def _load(self, version):
        matches = [v for v in self._versions() if version in
                   (v["version_id"], v["version_index"], v["version_string"])]
        if len(matches) != 1:
            raise KeyError("version_not_found_or_ambiguous")
        return copy.deepcopy(matches[0])

    def loadVersion(self, version):
        """Load by exact ID, integer index, or unique version string."""
        with self.tracer._lock:
            return _freeze(self._load(version))

    mountVersion = loadVersion

    def saveVersion(self, snapshot, version_string, *, branch_id=None, parent=None):
        """Append a JSON snapshot; an existing branch requires its current parent."""
        if not isinstance(version_string, str) or not re.fullmatch(r"v\d+\.\d+", version_string):
            raise ValueError("expected_vMM.HH_or_vMajor.Minor")
        # Validate JSON before emitting any trace or changing state.
        snapshot = json.loads(json.dumps(snapshot, ensure_ascii=False, allow_nan=False))
        with self.tracer._lock:
            versions = self._versions()
            if any(v["version_string"] == version_string for v in versions):
                raise ValueError("duplicate_version_string")
            if branch_id is not None:
                branches = [e["payload"] for e in self._events() if e["event_type"] == "timemachine_branch"]
                branch = next((b for b in branches if b["branch_id"] == branch_id), None)
                if branch is None:
                    raise KeyError("unknown_branch")
                tips = [v for v in versions if v["branch_id"] == branch_id]
                expected = tips[-1]["version_id"] if tips else branch["parent_version_id"]
                if parent != expected:
                    raise ValueError("stale_branch_parent")
            elif versions:
                raise PermissionError("branch_required_for_write")
            if parent is not None:
                parent = self._load(parent)["version_id"]
            if not any(e["event_type"] == "timemachine_law_seal" for e in self._events()):
                root = Path(__file__).resolve().parents[1]
                self.tracer.emit("timemachine_law_seal", dict(
                    seal=self.law_seal,
                    documents={leaf["path"]: (root / leaf["path"]).read_text(encoding="utf-8")
                               for leaf in self.law_seal["leaves"]},
                    origin_signature=ORIGIN_SIGNATURE))
            index = len(versions) + 1
            record = dict(version_id=uuid.uuid4().hex, version_index=index,
                          timestamp=index, version_string=version_string,
                          parent_version_id=parent, branch_id=branch_id,
                          origin_signature=ORIGIN_SIGNATURE, law_merkle_root=self.law_seal["merkle_root"],
                          snapshot=snapshot)
            self.tracer.emit("timemachine_version", record)
            return _freeze(record)

    def branchFrom(self, version_id):
        """Create an append-only branch rooted in an existing immutable version."""
        with self.tracer._lock:
            parent = self._load(version_id)
            branch_id = uuid.uuid4().hex
            self.tracer.emit("timemachine_branch", dict(
                branch_id=branch_id, parent_version_id=parent["version_id"],
                origin_signature=ORIGIN_SIGNATURE))
            return VersionBranch(self, branch_id, parent["version_id"])

    def diffVersions(self, v1, v2):
        """Return exact snapshot differences using JSON-pointer paths."""
        with self.tracer._lock:
            before, after = self._load(v1)["snapshot"], self._load(v2)["snapshot"]
        changes = []

        def walk(a, b, path):
            if isinstance(a, dict) and isinstance(b, dict):
                for key in sorted(a.keys() | b.keys()):
                    child = path + "/" + key.replace("~", "~0").replace("/", "~1")
                    if key not in a:
                        changes.append(dict(op="add", path=child, after=b[key]))
                    elif key not in b:
                        changes.append(dict(op="remove", path=child, before=a[key]))
                    else:
                        walk(a[key], b[key], child)
            elif type(a) is not type(b) or a != b:
                changes.append(dict(op="replace", path=path, before=a, after=b))

        walk(before, after, "")
        return changes

    def queryAt(self, timestamp):
        """Legacy wall-clock query: all original trace events up to ts (ISO)."""
        from datetime import datetime
        target = datetime.fromisoformat(timestamp)
        with self.tracer._lock:
            return _freeze([e for e in self._events() if datetime.fromisoformat(e["ts"]) <= target])

    def importLegacy(self, record, version_string):
        """Preserve complete legacy timestamp/coordinates in a new snapshot."""
        return self.saveVersion({"legacy_record": copy.deepcopy(record)}, version_string)

    def memoryWindow(self):
        """Reconstruct 64 traces and the last 16 checkpoints without rewriting history."""
        with self.tracer._lock:
            events = self._events()
        checkpoints = []
        world = None
        for i, event in enumerate(events, 1):
            if event["event_type"] == "timemachine_version":
                world = event["payload"]["snapshot"]
            if i % 16 == 0:
                checkpoints.append(dict(
                    tick=event["tick"], merkle_root=event["merkle_root"],
                    world_hash=hashlib.sha256(_json(world).encode()).hexdigest(),
                    origin_signature=ORIGIN_SIGNATURE))
        return _freeze(dict(ring=events[-64:], checkpoints=checkpoints[-16:]))


class VersionBranch:
    """Writable descendant handle; the source mount remains immutable."""

    def __init__(self, machine, branch_id, parent):
        self.machine, self.branch_id, self.parent = machine, branch_id, parent

    def commit(self, snapshot, version_string):
        version = self.machine.saveVersion(snapshot, version_string,
                                           branch_id=self.branch_id, parent=self.parent)
        self.parent = version["version_id"]
        return version
