#!/usr/bin/env python3
"""MRL Universal Passport registry for runtime worlds and generated outputs."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from . import ORIGIN_SIGNATURE

_CANONICAL_ID = re.compile(r"^MRL_[A-Za-z0-9_.:/-]+$")


class MRLPassportRegistry:
    """Create immutable passport versions while retaining their origin chain."""

    def __init__(self, data_dir: Path) -> None:
        self.directory = data_dir / "passports"
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _hash(payload: dict[str, Any]) -> str:
        encoded = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def issue(
        self,
        *,
        canonical_id: str,
        source_identity: str,
        world_state: str,
        capabilities: list[str],
        evidence_refs: list[str],
        return_anchor: str,
        environment: dict[str, Any],
        rights: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not _CANONICAL_ID.fullmatch(canonical_id):
            raise ValueError("canonical_id must be a valid MRL_ identity")
        if not source_identity:
            raise ValueError("source_identity is required and must not be overwritten")
        if world_state not in {"source", "candidate", "canonical", "product", "archived"}:
            raise ValueError("unsupported world_state")
        previous = self.latest(canonical_id)
        body = {
            "schema": "MRL_Universal_Passport_v1",
            "canonical_id": canonical_id,
            "source_identity": source_identity,
            "world_state": world_state,
            "capabilities": sorted(set(capabilities)),
            "evidence_refs": evidence_refs,
            "return_anchor": return_anchor,
            "environment": environment,
            "rights": rights or {"state": "UNRESOLVED"},
            "previous_passport_hash": previous["passport_hash"] if previous else "GENESIS",
            "version": (previous["version"] + 1) if previous else 1,
            "origin_signature": ORIGIN_SIGNATURE,
        }
        passport = {**body, "passport_hash": self._hash(body)}
        path = self.directory / f"{self._safe_name(canonical_id)}.jsonl"
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(passport, ensure_ascii=False, sort_keys=True) + "\n")
        return passport

    @staticmethod
    def _safe_name(canonical_id: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", canonical_id)

    def latest(self, canonical_id: str) -> dict[str, Any] | None:
        path = self.directory / f"{self._safe_name(canonical_id)}.jsonl"
        if not path.exists():
            return None
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return json.loads(lines[-1]) if lines else None

    def verify(self, canonical_id: str) -> dict[str, Any]:
        path = self.directory / f"{self._safe_name(canonical_id)}.jsonl"
        if not path.exists():
            return {"ok": False, "reason": "passport_not_found"}
        previous_hash = "GENESIS"
        count = 0
        for count, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            passport = json.loads(line)
            if passport.get("version") != count:
                return {"ok": False, "reason": "version_mismatch", "version": count}
            if passport.get("previous_passport_hash") != previous_hash:
                return {"ok": False, "reason": "previous_hash_mismatch", "version": count}
            body = {key: value for key, value in passport.items() if key != "passport_hash"}
            expected_hash = self._hash(body)
            if passport.get("passport_hash") != expected_hash:
                return {"ok": False, "reason": "passport_hash_mismatch", "version": count}
            previous_hash = expected_hash
        return {"ok": True, "versions": count, "head": previous_hash}

