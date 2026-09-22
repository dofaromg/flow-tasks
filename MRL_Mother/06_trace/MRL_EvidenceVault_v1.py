#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_EvidenceVault_v1.py
Append-only evidence preservation for MRL canonical history.
origin_signature: MrLiouWord

Purpose:
- Preserve observed external state without overwriting canonical history.
- Record before/after hashes, source, actor, timestamp, and provenance.
- Treat external changes as append-only evidence records.
- Keep canonical MRL identity/history independent from external presentation.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

ORIGIN_SIGNATURE = "MrLiouWord"
SCHEMA_VERSION = "1.0.0"


def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(_canonical_json(obj)).hexdigest()


@dataclass(frozen=True)
class EvidenceRecord:
    record_id: str
    observed_at: str
    source_type: str
    source_name: str
    source_ref: str
    actor: str
    canonical_name: str
    external_name: str
    event_type: str
    before_hash: str
    after_hash: str
    payload_hash: str
    previous_record_hash: str
    origin_signature: str = ORIGIN_SIGNATURE
    schema_version: str = SCHEMA_VERSION
    evidence_status: str = "OBSERVED"
    inference_status: str = "NONE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def record_hash(self) -> str:
        return sha256_obj(self.to_dict())


class MRL_EvidenceVault:
    """Append-only JSONL ledger. Existing history is never rewritten by this class."""

    def __init__(self, ledger_path: Path) -> None:
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.ledger_path.exists():
            return "0" * 64
        last = ""
        with self.ledger_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    last = line
        if not last:
            return "0" * 64
        obj = json.loads(last)
        return sha256_obj(obj)

    def append(self, *, source_type: str, source_name: str, source_ref: str,
               actor: str, canonical_name: str, external_name: str,
               event_type: str, before: Optional[Any], after: Optional[Any],
               payload: Optional[Any] = None,
               observed_at: Optional[str] = None) -> EvidenceRecord:
        ts = observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        before_hash = sha256_obj(before) if before is not None else "0" * 64
        after_hash = sha256_obj(after) if after is not None else "0" * 64
        payload_hash = sha256_obj(payload) if payload is not None else "0" * 64
        previous_record_hash = self._last_hash()
        record_seed = {
            "observed_at": ts,
            "source_type": source_type,
            "source_name": source_name,
            "source_ref": source_ref,
            "actor": actor,
            "canonical_name": canonical_name,
            "external_name": external_name,
            "event_type": event_type,
            "before_hash": before_hash,
            "after_hash": after_hash,
            "payload_hash": payload_hash,
            "previous_record_hash": previous_record_hash,
            "origin_signature": ORIGIN_SIGNATURE,
        }
        record_id = sha256_obj(record_seed)
        record = EvidenceRecord(
            record_id=record_id,
            observed_at=ts,
            source_type=source_type,
            source_name=source_name,
            source_ref=source_ref,
            actor=actor,
            canonical_name=canonical_name,
            external_name=external_name,
            event_type=event_type,
            before_hash=before_hash,
            after_hash=after_hash,
            payload_hash=payload_hash,
            previous_record_hash=previous_record_hash,
        )
        with self.ledger_path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return record


def verify_ledger(ledger_path: Path) -> Dict[str, Any]:
    path = Path(ledger_path)
    previous = "0" * 64
    count = 0
    if not path.exists():
        return {"valid": True, "records": 0, "last_hash": previous}
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("previous_record_hash") != previous:
                return {"valid": False, "records": count, "line": line_no,
                        "reason": "previous_record_hash mismatch"}
            previous = sha256_obj(obj)
            count += 1
    return {"valid": True, "records": count, "last_hash": previous}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger")
    args = parser.parse_args()
    print(json.dumps(verify_ledger(Path(args.ledger)), ensure_ascii=False, indent=2))
