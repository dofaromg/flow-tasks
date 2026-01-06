from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .storage import Storage


@dataclass
class Entry:
    index: int
    prev_hash: Optional[str]
    content: str
    timestamp: str
    hash: str

    @classmethod
    def create(cls, index: int, prev_hash: Optional[str], content: str) -> "Entry":
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = f"{index}|{prev_hash or ''}|{content}|{timestamp}".encode()
        entry_hash = hashlib.sha256(payload).hexdigest()
        return cls(index=index, prev_hash=prev_hash, content=content, timestamp=timestamp, hash=entry_hash)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "prev_hash": self.prev_hash,
            "content": self.content,
            "timestamp": self.timestamp,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Entry":
        return cls(
            index=int(data["index"]),
            prev_hash=data.get("prev_hash") or None,
            content=data["content"],
            timestamp=data["timestamp"],
            hash=data["hash"],
        )


class Ledger:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def init(self, reset: bool = False) -> None:
        if reset:
            self.storage.reset()
        self.storage.ensure_structure()
        refs = self.storage.load_refs()
        if refs.get("length") is None:
            self.storage.save_refs({"head": None, "length": 0})

    def append(self, content: str) -> Entry:
        self.storage.ensure_structure()
        refs = self.storage.load_refs()
        prev_hash = refs.get("head")
        index = int(refs.get("length", 0)) + 1
        entry = Entry.create(index=index, prev_hash=prev_hash, content=content)
        self.storage.append_chain_entry(entry.to_dict())
        if prev_hash:
            self.storage.append_dag_edge({"from": prev_hash, "to": entry.hash})
        self.storage.save_refs({"head": entry.hash, "length": index})
        return entry

    def verify(self) -> Tuple[bool, str]:
        entries = [Entry.from_dict(e) for e in self.storage.load_chain_entries()]
        prev_hash = None
        for entry in entries:
            expected_hash = hashlib.sha256(
                f"{entry.index}|{prev_hash or ''}|{entry.content}|{entry.timestamp}".encode()
            ).hexdigest()
            if entry.prev_hash != prev_hash:
                return False, f"Entry {entry.index} prev_hash mismatch: {entry.prev_hash} != {prev_hash}"
            if entry.hash != expected_hash:
                return False, f"Entry {entry.index} hash mismatch"
            prev_hash = entry.hash

        refs = self.storage.load_refs()
        if refs.get("head") != prev_hash:
            return False, "Head reference does not match chain tip"
        if refs.get("length") != len(entries):
            return False, "Length reference does not match chain length"

        return True, f"Verified {len(entries)} entries"

    def snapshot(self, name: str) -> Dict[str, Any]:
        refs = self.storage.load_refs()
        snapshot_data = {
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "head": refs.get("head"),
            "length": refs.get("length", 0),
        }
        path = self.storage.write_snapshot(name, snapshot_data)
        snapshot_data["path"] = str(path)
        return snapshot_data

    def log(self, n: int) -> List[Dict[str, Any]]:
        entries = self.storage.tail_chain(n)
        return [Entry.from_dict(e).to_dict() for e in entries]

    def export_state(self) -> Dict[str, Any]:
        refs = self.storage.load_refs()
        entries = self.storage.load_chain_entries()
        return {
            "refs": refs,
            "entries": entries,
        }

    def compare_with_storage(self, other_storage: Storage) -> Tuple[bool, str]:
        """Compare current ledger against another storage (sandbox) for divergence.

        This enables lifecycle sandbox validation by checking that a sandbox copy
        is in lock-step with the primary ledger state.
        """

        primary_entries = self.storage.load_chain_entries()
        sandbox_entries = other_storage.load_chain_entries()

        min_len = min(len(primary_entries), len(sandbox_entries))
        for idx in range(min_len):
            if primary_entries[idx]["hash"] != sandbox_entries[idx]["hash"]:
                return False, (
                    f"Mismatch at entry {idx + 1}: "
                    f"primary {primary_entries[idx]['hash']} != sandbox {sandbox_entries[idx]['hash']}"
                )

        if len(primary_entries) != len(sandbox_entries):
            diff = len(primary_entries) - len(sandbox_entries)
            direction = "behind" if diff > 0 else "ahead"
            return (
                False,
                f"Sandbox ledger is {abs(diff)} entries {direction} "
                f"(primary length {len(primary_entries)}, sandbox length {len(sandbox_entries)})",
            )

        primary_refs = self.storage.load_refs()
        sandbox_refs = other_storage.load_refs()
        if primary_refs.get("head") != sandbox_refs.get("head"):
            return False, "Head references differ between primary and sandbox ledgers"

        return True, "Sandbox ledger matches primary state"
