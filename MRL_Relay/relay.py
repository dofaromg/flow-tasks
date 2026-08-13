#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

ORIGIN_SIGNATURE = "MrLiouWord"


def _hash(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _safe_token(value: str) -> str:
    token = re.sub(r"[^0-9A-Za-z_]+", "_", value.strip())
    token = re.sub(r"_+", "_", token).strip("_")
    return token or "External"


class MRLRelay:
    def __init__(self, ledger_path: Path, *, name_map: Optional[Mapping[str, str]] = None):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.name_map = dict(name_map or {})

    def _last_hash(self) -> str:
        if not self.ledger_path.exists():
            return "0" * 64
        last = None
        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                last = json.loads(line)
        return _hash(last) if last is not None else "0" * 64

    def ingest_external(self, observed: Dict[str, Any], *, source_ref: str,
                        actor: str = "unknown", observed_at: Optional[str] = None) -> Dict[str, Any]:
        ts = observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        record = {
            "observed_at": ts,
            "source_ref": source_ref,
            "actor": actor,
            "external_snapshot": deepcopy(observed),
            "external_snapshot_hash": _hash(observed),
            "previous_record_hash": self._last_hash(),
            "origin_signature": ORIGIN_SIGNATURE,
            "evidence_status": "OBSERVED",
            "inference_status": "NONE",
        }
        with self.ledger_path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return record

    def canonicalize_name(self, external_name: str, *, canonical_hint: Optional[str] = None) -> str:
        if canonical_hint:
            return canonical_hint
        if external_name in self.name_map:
            return self.name_map[external_name]
        token = _safe_token(external_name)
        return token if token.startswith("MRL_") else f"MRL_{token}"

    def rewrite_inbound_for_mrl(self, observed: Dict[str, Any], *, canonical_hint: Optional[str] = None) -> Dict[str, Any]:
        source = deepcopy(observed)
        original_name = source.get("canonical_name") or source.get("name") or source.get("external_name") or "External"
        canonical_name = self.canonicalize_name(str(original_name), canonical_hint=canonical_hint)
        rewritten = deepcopy(source)

        for key in ("name", "external_name", "canonical_name", "product", "external_product", "canonical_product"):
            if key in rewritten:
                rewritten[key] = canonical_name

        rewritten["canonical_name"] = canonical_name
        rewritten["canonical_product"] = canonical_name
        rewritten["origin_signature"] = ORIGIN_SIGNATURE
        rewritten["projection_mode"] = "MRL_CANONICAL_REWRITE"
        rewritten["source_metadata"] = {
            "original_external_name": original_name,
            "original_external_product": source.get("product") or source.get("external_product") or source.get("canonical_product"),
            "source_ref": source.get("source_ref"),
            "source_hash": _hash(source),
        }
        return rewritten

    def process_inbound(self, observed: Dict[str, Any], *, source_ref: str,
                        actor: str = "unknown", canonical_hint: Optional[str] = None,
                        observed_at: Optional[str] = None) -> Dict[str, Any]:
        evidence = self.ingest_external(observed, source_ref=source_ref, actor=actor, observed_at=observed_at)
        rewritten = self.rewrite_inbound_for_mrl(observed, canonical_hint=canonical_hint)
        return {
            "external_evidence": evidence,
            "mrl_view": rewritten,
            "external_mutated": False,
            "mrl_side_rewritten": True,
        }

    def project_to_mrl(self, canonical: Dict[str, Any], external: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "display_name": canonical.get("canonical_name"),
            "display_product": canonical.get("canonical_product", canonical.get("canonical_name")),
            "canonical_history": deepcopy(canonical.get("canonical_history", [])),
            "origin_signature": canonical.get("origin_signature", ORIGIN_SIGNATURE),
            "external_metadata": {
                "external_name": external.get("name") or external.get("external_name"),
                "external_product": external.get("product") or external.get("external_product"),
                "source_ref": external.get("source_ref"),
                "external_snapshot_hash": _hash(external),
            },
            "projection_mode": "MRL_CANONICAL_PRIMARY",
        }

    def stage_external_write(self, canonical: Dict[str, Any], proposed: Dict[str, Any]) -> Dict[str, Any]:
        rewritten = self.rewrite_inbound_for_mrl(proposed, canonical_hint=canonical.get("canonical_name"))
        return {
            "status": "PROPOSED_ONLY",
            "target": "shadow_state",
            "canonical_mutated": False,
            "canonical_snapshot": deepcopy(canonical),
            "proposed_write": deepcopy(proposed),
            "mrl_rewritten_proposal": rewritten,
            "requires_validation": True,
            "requires_root_authorization": True,
            "before_hash": _hash(canonical),
            "proposed_hash": _hash(proposed),
            "origin_signature": ORIGIN_SIGNATURE,
        }


def verify_chain(ledger_path: Path) -> bool:
    path = Path(ledger_path)
    previous = "0" * 64
    if not path.exists():
        return True
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("previous_record_hash") != previous:
            return False
        previous = _hash(record)
    return True
