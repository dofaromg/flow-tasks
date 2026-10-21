"""MRL橋接轉譯中心: lossless sidecar labels and Möbius boundary receipts.

origin_signature: MrLiouWord
Labels describe processing affiliation; payload authorship remains separate.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import sys
from pathlib import Path
from threading import RLock
from uuid import UUID, uuid4

CENTER = "MRL橋接轉譯中心"
SCHEMA = "MRL.BridgeTranslationCenter.v1"
_MODULE_LOADED_AT = datetime.now(timezone.utc).isoformat()
_MODULE_SHA256_LF = sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
_centers = {}
_centers_lock = RLock()


def canonical(value):
    """Serialize metadata deterministically; never coerce unsupported payloads."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


class TranslationCenter:
    """Process-local serialized ledger; optional append-only file on owner storage.

    One writer owns each ledger file. A corrupted ledger prevents initialization.
    With no ledger path, recent receipts are explicitly memory-only (bounded).
    """

    def __init__(self, ledger_path=None):
        self.path = Path(ledger_path) if ledger_path else None
        self.records = deque(maxlen=1024)
        self._lock = RLock()
        self._sequence = 0
        self._previous = "GENESIS"
        if self.path and self.path.exists():
            with self.path.open("r", encoding="utf-8") as ledger:
                for line in ledger:
                    record = json.loads(line)
                    digest = record.pop("record_sha256")
                    if (record["sequence"] != self._sequence
                            or record["previous_sha256"] != self._previous
                            or sha256(canonical(record).encode()).hexdigest() != digest):
                        raise ValueError("MRL bridge ledger integrity failure")
                    record["record_sha256"] = digest
                    self.records.append(record)
                    self._previous = digest
                    self._sequence += 1

    @classmethod
    def from_environment(cls, component):
        """Use separate ledger per component/process; no credential discovery."""
        root = os.environ.get("MRL_TRANSLATION_LEDGER_DIR")
        key = (root, component, os.getpid())
        with _centers_lock:
            if key not in _centers:
                _centers[key] = cls(Path(root) / f"{component}-{os.getpid()}.jsonl" if root else None)
            return _centers[key]

    def label(self, payload, *, source_ref, destination_ref,
              direction="mrl_to_external", trace_id=None, parent_ref=None,
              producer_persona=None, payload_origin_signature=None,
              status="observed", http_status=None, peer_trace_id=None):
        """Append a sidecar receipt without altering or retaining payload content.

        bytes hashes cover exact bytes; other values cover canonical JSON. MRL
        origin_signature signs this receipt, never an external payload's origin.
        """
        if direction not in {"mrl_to_external", "external_to_mrl", "internal"}:
            raise ValueError("invalid MRL bridge direction")
        raw = payload if isinstance(payload, bytes) else canonical(payload).encode()
        with self._lock:
            record = {
                "schema": SCHEMA, "bridge_center": CENTER,
                "mrl_affiliation": "MRL", "canonical_authority": "Mr.liou",
                "origin_signature": "MrLiouWord",
                "payload_origin_signature": payload_origin_signature,
                "producer_persona": producer_persona,
                "trace_id": trace_id or str(uuid4()), "event_id": str(uuid4()),
                "peer_trace_id": self.parse_peer_trace_id(peer_trace_id),
                "peer_trace_trust": "unverified",
                "runtime_evidence": {
                    "process_id": os.getpid(), "executable": sys.executable,
                    "module_path": str(Path(__file__).resolve()),
                    "module_sha256_lf": _MODULE_SHA256_LF,
                    "module_loaded_at": _MODULE_LOADED_AT,
                },
                "parent_ref": parent_ref, "source_ref": source_ref,
                "destination_ref": destination_ref, "direction": direction,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload_sha256": sha256(raw).hexdigest(),
                "hash_scope": "bytes" if isinstance(payload, bytes) else "canonical-json",
                "payload_size": len(raw), "status": status, "http_status": http_status,
                "storage": "append-only-file" if self.path else "memory-only",
                "sequence": self._sequence, "previous_sha256": self._previous,
            }
            record["record_sha256"] = sha256(canonical(record).encode()).hexdigest()
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as handle:
                    handle.write(canonical(record) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
            self.records.append(record)
            self._sequence += 1
            self._previous = record["record_sha256"]
            return dict(record)

    def envelope(self, payload, **context):
        """Return original payload plus separate labels (no renaming/re-signing)."""
        return {"payload": payload, "mrl_bridge": self.label(payload, **context)}

    @staticmethod
    def parse_peer_trace_id(value):
        """Retain a peer correlation UUID without accepting its authority claims."""
        try:
            return str(UUID(value)) if isinstance(value, str) else None
        except ValueError:
            return None

    @staticmethod
    def headers(record):
        """ASCII HTTP metadata; Chinese canonical name remains in the sidecar."""
        return {"X-MRL-Affiliation": "MRL",
                "X-MRL-Bridge-Center": "MRL-Bridge-Translation-Center-v1",
                "X-MRL-Trace-Id": record["trace_id"],
                "X-MRL-Event-Id": record["event_id"]}

