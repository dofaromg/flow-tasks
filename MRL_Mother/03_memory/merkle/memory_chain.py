#!/usr/bin/env python3
"""
FlowAgent Memory Chain (Merkle)
- Immutable append-only log
- Each entry links to previous merkle (prev)
- Supports verify() + rollback()

Design principle: "怎麼過去，就怎麼回來"
"""

from __future__ import annotations

import json
import time
import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_json(obj: Any) -> str:
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(data)


@dataclass
class ChainEntry:
    # core identity
    entry_id: str
    timestamp_ms: int

    # payload
    payload: Dict[str, Any]  # event/action content, already structured

    # chain
    prev: str
    merkle: str

    # optional tags / layer for your L0-L7 worldview
    tags: List[str]
    layer: str
    meta: Dict[str, Any]


class MerkleChain:
    """
    Append-only Merkle chain stored as JSONL + head pointer.
    Default data dir is local runtime data, not tracked by git.
    """

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.entries_file = self.data_dir / "entries.jsonl"
        self.head_file = self.data_dir / "head.txt"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.head = self._load_head()

    def _load_head(self) -> str:
        if self.head_file.exists():
            return self.head_file.read_text(encoding="utf-8").strip()
        return "0" * 64

    def _save_head(self, merkle: str) -> None:
        self.head_file.write_text(merkle, encoding="utf-8")
        self.head = merkle

    def commit(
        self,
        payload: Dict[str, Any],
        *,
        entry_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        layer: str = "L7",
        meta: Optional[Dict[str, Any]] = None,
    ) -> ChainEntry:
        import uuid

        eid = entry_id or str(uuid.uuid4())
        ts = int(time.time() * 1000)
        prev = self.head

        # Merkle input must be deterministic
        merkle_input = {
            "entry_id": eid,
            "timestamp_ms": ts,
            "payload": payload,
            "prev": prev,
        }
        merkle = _sha256_json(merkle_input)

        entry = ChainEntry(
            entry_id=eid,
            timestamp_ms=ts,
            payload=payload,
            prev=prev,
            merkle=merkle,
            tags=tags or [],
            layer=layer,
            meta=meta or {},
        )

        with self.entries_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

        self._save_head(merkle)
        return entry

    def read_all(self) -> List[Dict[str, Any]]:
        if not self.entries_file.exists():
            return []
        items: List[Dict[str, Any]] = []
        with self.entries_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items

    def verify(self) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        entries = self.read_all()
        if not entries:
            return True, []

        # sort by timestamp
        entries.sort(key=lambda x: x["timestamp_ms"])
        prev = "0" * 64

        for e in entries:
            if e["prev"] != prev:
                errors.append(f"Chain broken at entry_id={e.get('entry_id')}: expected prev={prev}, got {e.get('prev')}")

            merkle_input = {
                "entry_id": e["entry_id"],
                "timestamp_ms": e["timestamp_ms"],
                "payload": e["payload"],
                "prev": e["prev"],
            }
            computed = _sha256_json(merkle_input)
            if computed != e["merkle"]:
                errors.append(f"Merkle mismatch at entry_id={e.get('entry_id')}: computed={computed}, stored={e.get('merkle')}")

            prev = e["merkle"]

        return len(errors) == 0, errors

    def rollback(self, target_merkle: str) -> bool:
        """
        Truncate the chain up to target_merkle (inclusive).
        """
        entries = self.read_all()
        if not entries:
            return False

        kept: List[Dict[str, Any]] = []
        found = False
        for e in entries:
            kept.append(e)
            if e.get("merkle") == target_merkle:
                found = True
                break
        if not found:
            return False

        with self.entries_file.open("w", encoding="utf-8") as f:
            for e in kept:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

        self._save_head(target_merkle)
        return True
