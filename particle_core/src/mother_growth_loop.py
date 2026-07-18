#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRLiou mother growth loop: absorb, version, verify, activate, rollback, reuse."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class MotherGrowthLoop:
    """Persist distilled memory seeds as an append-only, verifiable version chain."""

    SCHEMA_VERSION = "mrliou.mother-growth.v1"
    ORIGIN_SIGNATURE = "MrLiouWord"
    VOLATILE_FIELDS = {"created_at", "distilled_at", "exported_at", "updated_at"}

    def __init__(self, storage_path: str = "mother_memory") -> None:
        self.storage_path = Path(storage_path)
        self.seeds_path = self.storage_path / "seeds"
        self.active_path = self.storage_path / "active"
        self.journal_path = self.storage_path / "journal.jsonl"
        self.lock_path = self.storage_path / ".growth.lock"
        self.seeds_path.mkdir(parents=True, exist_ok=True)
        self.active_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _canonical_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def _hash(cls, value: Any) -> str:
        return hashlib.sha256(cls._canonical_json(value).encode("utf-8")).hexdigest()

    @classmethod
    def _semantic_value(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: cls._semantic_value(item)
                for key, item in value.items()
                if key not in cls.VOLATILE_FIELDS
            }
        if isinstance(value, list):
            return [cls._semantic_value(item) for item in value]
        return value

    @staticmethod
    def _safe_seed_id(seed_id: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", seed_id.strip()).strip("._")
        if not safe:
            raise ValueError("seed_id must contain at least one safe character")
        return safe

    @contextmanager
    def _lock(self, timeout_seconds: float = 10.0):
        deadline = time.time() + timeout_seconds
        descriptor: Optional[int] = None
        while descriptor is None:
            try:
                descriptor = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(descriptor, str(os.getpid()).encode("ascii"))
            except FileExistsError:
                if time.time() >= deadline:
                    raise TimeoutError(f"Timed out acquiring growth-loop lock: {self.lock_path}")
                time.sleep(0.05)
        try:
            yield
        finally:
            if descriptor is not None:
                os.close(descriptor)
            self.lock_path.unlink(missing_ok=True)

    def _atomic_write_json(self, path: Path, value: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _active_file(self, seed_id: str) -> Path:
        return self.active_path / f"{self._safe_seed_id(seed_id)}.json"

    def _seed_dir(self, seed_id: str) -> Path:
        return self.seeds_path / self._safe_seed_id(seed_id)

    def _version_file(self, seed_id: str, version: int) -> Path:
        return self._seed_dir(seed_id) / f"v{version:06d}.json"

    @staticmethod
    def _insight_text(item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("insight") or item.get("text") or "").strip()
        return str(item).strip()

    def _validate_seed(self, seed: Dict[str, Any]) -> None:
        if not isinstance(seed, dict):
            raise TypeError("memory_seed must be a mapping")
        if not isinstance(seed.get("seed_type"), str) or not seed["seed_type"].strip():
            raise ValueError("memory_seed.seed_type must be a non-empty string")
        insights = seed.get("insights")
        if not isinstance(insights, list):
            raise ValueError("memory_seed.insights must be a list")
        empty = [index for index, item in enumerate(insights) if not self._insight_text(item)]
        if empty:
            raise ValueError(f"memory_seed contains empty insight(s): {empty}")

    def _extract_seed(self, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(pipeline_result, dict):
            raise TypeError("pipeline_result must be a mapping")
        if pipeline_result.get("seed_type"):
            seed = pipeline_result
        else:
            seed = pipeline_result.get("views", {}).get("memory_seed")
        if not isinstance(seed, dict):
            raise ValueError("pipeline_result does not contain views.memory_seed")
        self._validate_seed(seed)
        return copy.deepcopy(seed)

    def _diff(self, previous: Optional[Dict[str, Any]], current: Dict[str, Any]) -> Dict[str, Any]:
        previous_items = {
            self._hash(self._insight_text(item)): self._insight_text(item)
            for item in (previous or {}).get("insights", [])
        }
        current_items = {
            self._hash(self._insight_text(item)): self._insight_text(item)
            for item in current.get("insights", [])
        }
        added_keys = sorted(set(current_items) - set(previous_items))
        removed_keys = sorted(set(previous_items) - set(current_items))
        return {
            "added_count": len(added_keys),
            "removed_count": len(removed_keys),
            "added": [current_items[key] for key in added_keys],
            "removed": [previous_items[key] for key in removed_keys],
        }

    def _last_event_hash(self) -> Optional[str]:
        if not self.journal_path.exists():
            return None
        lines = [line for line in self.journal_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            return None
        return json.loads(lines[-1]).get("event_hash")

    def _append_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "schema_version": self.SCHEMA_VERSION,
            "timestamp": self._now(),
            "origin_signature": self.ORIGIN_SIGNATURE,
            "previous_event_hash": self._last_event_hash(),
            **event,
        }
        record["event_hash"] = self._hash(record)
        with self.journal_path.open("a", encoding="utf-8") as journal:
            journal.write(self._canonical_json(record) + "\n")
            journal.flush()
            os.fsync(journal.fileno())
        return record

    def load_active(self, seed_id: str) -> Dict[str, Any]:
        pointer_path = self._active_file(seed_id)
        if not pointer_path.exists():
            raise FileNotFoundError(f"No active seed: {seed_id}")
        pointer = self._read_json(pointer_path)
        envelope = self._read_json(self.storage_path / pointer["path"])
        if envelope.get("content_hash") != pointer.get("content_hash"):
            raise ValueError(f"Active pointer hash mismatch: {seed_id}")
        return envelope

    def absorb_pipeline_result(
        self,
        pipeline_result: Dict[str, Any],
        seed_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate and commit one pipeline memory seed without deleting prior versions."""
        safe_id = self._safe_seed_id(seed_id)
        seed = self._extract_seed(pipeline_result)
        semantic_seed = self._semantic_value(seed)
        content_hash = self._hash(semantic_seed)

        with self._lock():
            active: Optional[Dict[str, Any]] = None
            pointer_path = self._active_file(safe_id)
            if pointer_path.exists():
                active = self.load_active(safe_id)
                if active["content_hash"] == content_hash:
                    event = self._append_event(
                        {
                            "event_type": "no_change",
                            "seed_id": safe_id,
                            "version": active["version"],
                            "content_hash": content_hash,
                        }
                    )
                    return {
                        "status": "unchanged",
                        "seed_id": safe_id,
                        "version": active["version"],
                        "content_hash": content_hash,
                        "event_hash": event["event_hash"],
                    }

            versions = sorted(self._seed_dir(safe_id).glob("v*.json"))
            version = len(versions) + 1
            parent_hash = active.get("content_hash") if active else None
            parent_version = active.get("version") if active else None
            change = self._diff(active.get("seed") if active else None, semantic_seed)
            envelope = {
                "schema_version": self.SCHEMA_VERSION,
                "origin_signature": self.ORIGIN_SIGNATURE,
                "seed_id": safe_id,
                "version": version,
                "created_at": self._now(),
                "content_hash": content_hash,
                "parent_hash": parent_hash,
                "parent_version": parent_version,
                "metadata": metadata or {},
                "diff": change,
                "seed": semantic_seed,
            }
            version_path = self._version_file(safe_id, version)
            self._atomic_write_json(version_path, envelope)
            reread = self._read_json(version_path)
            if self._hash(reread["seed"]) != reread["content_hash"]:
                raise ValueError(f"Written seed failed hash verification: {version_path}")

            relative_path = str(version_path.relative_to(self.storage_path)).replace("\\", "/")
            pointer = {
                "schema_version": self.SCHEMA_VERSION,
                "origin_signature": self.ORIGIN_SIGNATURE,
                "seed_id": safe_id,
                "version": version,
                "content_hash": content_hash,
                "path": relative_path,
                "updated_at": self._now(),
            }
            self._atomic_write_json(pointer_path, pointer)
            event = self._append_event(
                {
                    "event_type": "created" if active is None else "upgraded",
                    "seed_id": safe_id,
                    "version": version,
                    "content_hash": content_hash,
                    "parent_hash": parent_hash,
                    "diff": change,
                }
            )
            return {
                "status": "created" if active is None else "upgraded",
                "seed_id": safe_id,
                "version": version,
                "content_hash": content_hash,
                "parent_hash": parent_hash,
                "diff": change,
                "event_hash": event["event_hash"],
                "path": relative_path,
            }

    def process_and_absorb(
        self,
        extractor: Any,
        source: Any,
        seed_id: str,
        source_type: str = "auto",
        metadata: Optional[Dict[str, Any]] = None,
        trust_level: str = "medium",
    ) -> Dict[str, Any]:
        """Run ConversationExtractor and commit its memory_seed into the mother store."""
        pipeline_result = extractor.process_external_analysis_pipeline(
            source,
            source_type=source_type,
            metadata=metadata,
            trust_level=trust_level,
        )
        backfill = self.absorb_pipeline_result(pipeline_result, seed_id, metadata=metadata)
        mqm_export = self.export_active_for_mqm(seed_id)
        return {
            "pipeline_result": pipeline_result,
            "backfill": backfill,
            "mqm_export": mqm_export,
        }

    def export_active_for_mqm(
        self,
        seed_id: str,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export the verified active seed in MemoryQuickMounter structure format."""
        active = self.load_active(seed_id)
        target = (
            Path(output_path)
            if output_path
            else self.storage_path / "exports" / f"{self._safe_seed_id(seed_id)}.mqm.json"
        )
        payload = {
            "structure": {
                "mother_seed_id": active["seed_id"],
                "mother_seed_version": active["version"],
                "mother_seed_hash": active["content_hash"],
                "mother_insights": active["seed"].get("insights", []),
                "mother_source_count": active["seed"].get("source_count", 0),
            },
            "metadata": {
                "schema_version": self.SCHEMA_VERSION,
                "origin_signature": self.ORIGIN_SIGNATURE,
                "exported_at": self._now(),
                "source_version_path": str(
                    self._version_file(active["seed_id"], active["version"]).relative_to(
                        self.storage_path
                    )
                ).replace("\\", "/"),
            },
        }
        self._atomic_write_json(target, payload)
        return {
            "path": str(target),
            "seed_id": active["seed_id"],
            "version": active["version"],
            "content_hash": active["content_hash"],
        }

    def build_context(self, seed_id: str, max_insights: int = 20) -> Dict[str, Any]:
        """Return active verified insights for a downstream task."""
        active = self.load_active(seed_id)
        insights = active["seed"].get("insights", [])[:max_insights]
        return {
            "seed_id": active["seed_id"],
            "version": active["version"],
            "content_hash": active["content_hash"],
            "source_count": active["seed"].get("source_count", 0),
            "insights": insights,
        }

    def prepare_next_task(
        self,
        task: Dict[str, Any],
        seed_ids: Iterable[str],
        max_insights: int = 20,
    ) -> Dict[str, Any]:
        """Inject verified active memory into a copy of the next task payload."""
        prepared = copy.deepcopy(task)
        prepared["mother_context"] = [
            self.build_context(seed_id, max_insights=max_insights) for seed_id in seed_ids
        ]
        prepared["mother_context_verified_at"] = self._now()
        return prepared

    def rollback(self, seed_id: str, target_version: int) -> Dict[str, Any]:
        """Reactivate an existing immutable version; no version file is deleted."""
        safe_id = self._safe_seed_id(seed_id)
        with self._lock():
            target_path = self._version_file(safe_id, target_version)
            if not target_path.exists():
                raise FileNotFoundError(f"Unknown target version: {safe_id} v{target_version}")
            target = self._read_json(target_path)
            if self._hash(target["seed"]) != target["content_hash"]:
                raise ValueError(f"Target seed hash mismatch: {target_path}")
            relative_path = str(target_path.relative_to(self.storage_path)).replace("\\", "/")
            self._atomic_write_json(
                self._active_file(safe_id),
                {
                    "schema_version": self.SCHEMA_VERSION,
                    "origin_signature": self.ORIGIN_SIGNATURE,
                    "seed_id": safe_id,
                    "version": target_version,
                    "content_hash": target["content_hash"],
                    "path": relative_path,
                    "updated_at": self._now(),
                },
            )
            event = self._append_event(
                {
                    "event_type": "rollback",
                    "seed_id": safe_id,
                    "version": target_version,
                    "content_hash": target["content_hash"],
                }
            )
            return {
                "status": "rolled_back",
                "seed_id": safe_id,
                "version": target_version,
                "content_hash": target["content_hash"],
                "event_hash": event["event_hash"],
            }

    def verify_store(self, seed_id: Optional[str] = None) -> Dict[str, Any]:
        """Verify seed hashes, parent references, active pointers, and journal chain."""
        errors: List[str] = []
        checked_versions = 0
        seed_dirs = [self._seed_dir(seed_id)] if seed_id else sorted(self.seeds_path.glob("*"))
        for seed_dir in seed_dirs:
            if not seed_dir.exists():
                errors.append(f"Missing seed directory: {seed_dir}")
                continue
            known_hashes = set()
            for path in sorted(seed_dir.glob("v*.json")):
                envelope = self._read_json(path)
                checked_versions += 1
                actual_hash = self._hash(envelope.get("seed"))
                if actual_hash != envelope.get("content_hash"):
                    errors.append(f"Hash mismatch: {path}")
                parent_hash = envelope.get("parent_hash")
                if parent_hash and parent_hash not in known_hashes:
                    errors.append(f"Missing parent hash: {path}")
                known_hashes.add(envelope.get("content_hash"))
            pointer_path = self._active_file(seed_dir.name)
            if not pointer_path.exists():
                errors.append(f"Missing active pointer: {seed_dir.name}")
            else:
                try:
                    self.load_active(seed_dir.name)
                except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
                    errors.append(str(error))

        previous_hash: Optional[str] = None
        if self.journal_path.exists():
            for line_number, line in enumerate(self.journal_path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                event_hash = record.pop("event_hash", None)
                if record.get("previous_event_hash") != previous_hash:
                    errors.append(f"Journal parent mismatch at line {line_number}")
                if self._hash(record) != event_hash:
                    errors.append(f"Journal hash mismatch at line {line_number}")
                previous_hash = event_hash

        return {
            "status": "PASS" if not errors else "FAIL",
            "checked_versions": checked_versions,
            "errors": errors,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Absorb external data into versioned MRLiou mother memory")
    parser.add_argument("source", help="File, folder, repository path, or literal text")
    parser.add_argument("--seed-id", required=True)
    parser.add_argument("--source-type", default="auto")
    parser.add_argument("--storage", default="mother_memory")
    parser.add_argument("--trust-level", default="medium")
    args = parser.parse_args()

    from conversation_extractor import ConversationExtractor

    loop = MotherGrowthLoop(args.storage)
    result = loop.process_and_absorb(
        ConversationExtractor(),
        args.source,
        seed_id=args.seed_id,
        source_type=args.source_type,
        trust_level=args.trust_level,
    )
    verification = loop.verify_store(args.seed_id)
    print(
        json.dumps(
            {
                "result": result["backfill"],
                "mqm_export": result["mqm_export"],
                "verification": verification,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if verification["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
