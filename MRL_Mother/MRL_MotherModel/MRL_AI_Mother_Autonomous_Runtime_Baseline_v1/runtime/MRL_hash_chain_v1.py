#!/usr/bin/env python3
"""Append-only SHA-256 chain used by MRL memory and evidence ledgers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from . import ORIGIN_SIGNATURE


class MRLHashChain:
    """Minimal append-only JSONL ledger with deterministic hash linkage."""

    def __init__(self, path: Path, ledger_id: str) -> None:
        self.path = path
        self.ledger_id = ledger_id
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self._lock = Lock()

    @staticmethod
    def _canonical(value: dict[str, Any]) -> bytes:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    def _records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                if not isinstance(item, dict):
                    raise ValueError(f"{self.ledger_id}: record must be an object")
                records.append(item)
        return records

    def _tail_record(self) -> dict[str, Any] | None:
        """Return the last non-empty record without parsing the entire file."""
        last_line: str | None = None
        with self.path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    last_line = line
        if last_line is None:
            return None
        item = json.loads(last_line)
        if not isinstance(item, dict):
            raise ValueError(f"{self.ledger_id}: tail record must be an object")
        return item

    def append(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Append payload with previous-hash linkage and return the sealed record."""
        with self._lock:
            tail = self._tail_record()
            previous_hash = tail["record_hash"] if tail is not None else "GENESIS"
            sequence = (tail["sequence"] + 1) if tail is not None else 1
            body = {
                "ledger_id": self.ledger_id,
                "sequence": sequence,
                "previous_hash": previous_hash,
                "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
                "origin_signature": ORIGIN_SIGNATURE,
            }
            record_hash = hashlib.sha256(self._canonical(body)).hexdigest()
            record = {**body, "record_hash": record_hash}
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            return record

    def verify(self) -> dict[str, Any]:
        """Verify sequence, previous hash and every record checksum."""
        previous_hash = "GENESIS"
        records = self._records()
        for expected_sequence, record in enumerate(records, start=1):
            if record.get("sequence") != expected_sequence:
                return {"ok": False, "reason": "sequence_mismatch", "sequence": expected_sequence}
            if record.get("previous_hash") != previous_hash:
                return {"ok": False, "reason": "previous_hash_mismatch", "sequence": expected_sequence}
            body = {key: value for key, value in record.items() if key != "record_hash"}
            expected_hash = hashlib.sha256(self._canonical(body)).hexdigest()
            if record.get("record_hash") != expected_hash:
                return {"ok": False, "reason": "record_hash_mismatch", "sequence": expected_sequence}
            previous_hash = expected_hash
        return {"ok": True, "records": len(records), "head": previous_hash}

    def read_all(self) -> list[dict[str, Any]]:
        """Return all records for audited replay."""
        return self._records()
