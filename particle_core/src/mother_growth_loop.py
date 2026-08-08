#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRL MotherGrowthLoop v1: absorb, version, verify, activate, rollback, reuse."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class MRL_MotherGrowthLoop_v1:
    """Persist distilled memory seeds as an append-only, verifiable version chain."""

    CANONICAL_SYSTEM_NAME = "MRL_MotherGrowthLoop_v1"
    LEGACY_SYSTEM_NAMES = ("MotherGrowthLoop", "mother_growth_loop")
    SCHEMA_VERSION = "mrliou.mother-growth.v1"
    ORIGIN_SIGNATURE = "MrLiouWord"
    VOLATILE_FIELDS = {"created_at", "distilled_at", "exported_at", "updated_at"}
    VERSION_PATTERN = re.compile(r"^v(?P<version>\d{6})\.json$")
    LOCK_STALE_SECONDS = 300.0

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
        if not isinstance(seed_id, str):
            raise TypeError("seed_id must be a string")
        original = seed_id.strip()
        canonical = original.lower()
        safe = re.sub(r"[^a-z0-9._-]+", "_", canonical).strip("._")
        if not safe:
            raise ValueError("seed_id must contain at least one safe character")
        if safe != canonical:
            suffix = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
            safe = f"{safe}-{suffix}"
        if len(safe) > 96:
            suffix = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
            safe = f"{safe[:79]}-{suffix}"
        return safe

    @staticmethod
    def _pid_is_running(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    def _recover_stale_lock(self) -> bool:
        """Remove a dead-owner lock without breaking a live long-running process."""
        try:
            payload = self._read_json(self.lock_path)
            pid = int(payload.get("pid", 0))
            if self._pid_is_running(pid):
                return False
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            try:
                age = time.time() - self.lock_path.stat().st_mtime
            except OSError:
                return True
            if age < self.LOCK_STALE_SECONDS:
                return False
        try:
            self.lock_path.unlink()
            return True
        except FileNotFoundError:
            return True
        except OSError:
            return False

    @contextmanager
    def _lock(self, timeout_seconds: float = 10.0):
        deadline = time.time() + timeout_seconds
        descriptor: Optional[int] = None
        while descriptor is None:
            try:
                descriptor = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                payload = self._canonical_json({"pid": os.getpid(), "created_at": self._now()})
                os.write(descriptor, payload.encode("utf-8"))
                os.fsync(descriptor)
            except FileExistsError:
                if self._recover_stale_lock():
                    continue
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

    def _write_immutable_json(self, path: Path, value: Dict[str, Any]) -> None:
        """Create a version file exactly once and refuse any overwrite."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as error:
            raise FileExistsError(f"Refusing to overwrite immutable seed version: {path}") from error
        try:
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _active_file(self, seed_id: str) -> Path:
        return self.active_path / f"{self._safe_seed_id(seed_id)}.json"

    def _seed_dir(self, seed_id: str) -> Path:
        return self.seeds_path / self._safe_seed_id(seed_id)

    def _version_file(self, seed_id: str, version: int) -> Path:
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise ValueError("version must be a positive integer")
        return self._seed_dir(seed_id) / f"v{version:06d}.json"

    def _version_files(self, seed_id: str) -> Dict[int, Path]:
        versions: Dict[int, Path] = {}
        seed_dir = self._seed_dir(seed_id)
        if not seed_dir.exists():
            return versions
        for path in seed_dir.glob("v*.json"):
            match = self.VERSION_PATTERN.fullmatch(path.name)
            if match:
                versions[int(match.group("version"))] = path
        return versions

    def _next_version(self, seed_id: str) -> int:
        versions = self._version_files(seed_id)
        return max(versions, default=0) + 1

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
        if not insights:
            raise ValueError("memory_seed.insights must not be empty")
        empty = [index for index, item in enumerate(insights) if not self._insight_text(item)]
        if empty:
            raise ValueError(f"memory_seed contains empty insight(s): {empty}")
        source_count = seed.get("source_count")
        if source_count is not None and (
            not isinstance(source_count, int) or isinstance(source_count, bool) or source_count < 0
        ):
            raise ValueError("memory_seed.source_count must be a non-negative integer")

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
        previous_by_text = {
            self._insight_text(item): item for item in (previous or {}).get("insights", [])
        }
        current_by_text = {
            self._insight_text(item): item for item in current.get("insights", [])
        }
        changed = []
        for text in sorted(set(previous_by_text) & set(current_by_text)):
            if self._hash(previous_by_text[text]) != self._hash(current_by_text[text]):
                changed.append(
                    {"insight": text, "before": previous_by_text[text], "after": current_by_text[text]}
                )
        previous_top = {key: value for key, value in (previous or {}).items() if key != "insights"}
        current_top = {key: value for key, value in current.items() if key != "insights"}
        top_level_changed = sorted(
            key
            for key in set(previous_top) | set(current_top)
            if previous_top.get(key) != current_top.get(key)
        )
        return {
            "added_count": len(added_keys),
            "removed_count": len(removed_keys),
            "added": [current_items[key] for key in added_keys],
            "removed": [previous_items[key] for key in removed_keys],
            "changed_count": len(changed),
            "changed": changed,
            "top_level_changed": top_level_changed,
        }

    def _last_event_hash(self) -> Optional[str]:
        records, errors = self._read_and_verify_journal()
        if errors:
            raise ValueError("Refusing to extend an invalid journal: " + "; ".join(errors))
        return records[-1].get("event_hash") if records else None

    def _append_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "system_name": self.CANONICAL_SYSTEM_NAME,
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

    def _read_and_verify_journal(self) -> tuple[List[Dict[str, Any]], List[str]]:
        records: List[Dict[str, Any]] = []
        errors: List[str] = []
        previous_hash: Optional[str] = None
        if not self.journal_path.exists():
            return records, errors
        try:
            lines = self.journal_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as error:
            return records, [f"Journal read failed: {error}"]
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                stored = json.loads(line)
                if not isinstance(stored, dict):
                    raise TypeError("event must be a JSON object")
            except (json.JSONDecodeError, TypeError) as error:
                errors.append(f"Journal parse failed at line {line_number}: {error}")
                continue
            record = dict(stored)
            event_hash = record.pop("event_hash", None)
            if record.get("previous_event_hash") != previous_hash:
                errors.append(f"Journal parent mismatch at line {line_number}")
            if self._hash(record) != event_hash:
                errors.append(f"Journal hash mismatch at line {line_number}")
            if not isinstance(event_hash, str):
                errors.append(f"Journal event hash missing at line {line_number}")
            else:
                previous_hash = event_hash
            records.append(stored)
        return records, errors

    def _validate_envelope(self, envelope: Dict[str, Any], seed_id: str, version: int) -> None:
        system_name = envelope.get("system_name")
        if system_name not in (None, self.CANONICAL_SYSTEM_NAME):
            raise ValueError(f"Seed system name mismatch: {seed_id} v{version}")
        if envelope.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError(f"Seed schema mismatch: {seed_id} v{version}")
        if envelope.get("origin_signature") != self.ORIGIN_SIGNATURE:
            raise ValueError(f"Seed origin signature mismatch: {seed_id} v{version}")
        if envelope.get("seed_id") != seed_id or envelope.get("version") != version:
            raise ValueError(f"Seed identity mismatch: {seed_id} v{version}")
        self._validate_seed(envelope.get("seed"))
        actual_hash = self._hash(envelope["seed"])
        if actual_hash != envelope.get("content_hash"):
            raise ValueError(f"Seed content hash mismatch: {seed_id} v{version}")

    def load_active(self, seed_id: str) -> Dict[str, Any]:
        safe_id = self._safe_seed_id(seed_id)
        pointer_path = self._active_file(safe_id)
        if not pointer_path.exists():
            raise FileNotFoundError(f"No active seed: {seed_id}")
        pointer = self._read_json(pointer_path)
        system_name = pointer.get("system_name")
        if system_name not in (None, self.CANONICAL_SYSTEM_NAME):
            raise ValueError(f"Active pointer system name mismatch: {safe_id}")
        if pointer.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError(f"Active pointer schema mismatch: {safe_id}")
        if pointer.get("origin_signature") != self.ORIGIN_SIGNATURE:
            raise ValueError(f"Active pointer origin signature mismatch: {safe_id}")
        if pointer.get("seed_id") != safe_id:
            raise ValueError(f"Active pointer seed identity mismatch: {safe_id}")
        version = pointer.get("version")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise ValueError(f"Active pointer version is invalid: {safe_id}")
        expected_path = self._version_file(safe_id, version)
        expected_relative = str(expected_path.relative_to(self.storage_path)).replace("\\", "/")
        if pointer.get("path") != expected_relative:
            raise ValueError(f"Active pointer path mismatch: {safe_id}")
        envelope = self._read_json(expected_path)
        self._validate_envelope(envelope, safe_id, version)
        if envelope.get("content_hash") != pointer.get("content_hash"):
            raise ValueError(f"Active pointer hash mismatch: {seed_id}")
        records, journal_errors = self._read_and_verify_journal()
        if journal_errors:
            raise ValueError("; ".join(journal_errors))
        activation_hash = pointer.get("activation_event_hash")
        matching = [record for record in records if record.get("event_hash") == activation_hash]
        if not matching:
            raise ValueError(f"Active pointer journal event missing: {safe_id}")
        event = matching[0]
        if (
            event.get("event_type") not in {"created", "upgraded", "rollback"}
            or event.get("seed_id") != safe_id
            or event.get("version") != version
            or event.get("content_hash") != envelope.get("content_hash")
            or event.get("version_path") != expected_relative
            or event.get("transaction_id") != pointer.get("transaction_id")
        ):
            raise ValueError(f"Active pointer journal event mismatch: {safe_id}")
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
                        "system_name": self.CANONICAL_SYSTEM_NAME,
                        "status": "unchanged",
                        "seed_id": safe_id,
                        "version": active["version"],
                        "content_hash": content_hash,
                        "event_hash": event["event_hash"],
                    }

            version = self._next_version(safe_id)
            parent_hash = active.get("content_hash") if active else None
            parent_version = active.get("version") if active else None
            change = self._diff(active.get("seed") if active else None, semantic_seed)
            envelope = {
                "system_name": self.CANONICAL_SYSTEM_NAME,
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
            self._write_immutable_json(version_path, envelope)
            reread = self._read_json(version_path)
            self._validate_envelope(reread, safe_id, version)

            relative_path = str(version_path.relative_to(self.storage_path)).replace("\\", "/")
            transaction_id = uuid.uuid4().hex
            event = self._append_event(
                {
                    "event_type": "created" if active is None else "upgraded",
                    "transaction_id": transaction_id,
                    "seed_id": safe_id,
                    "version": version,
                    "content_hash": content_hash,
                    "parent_hash": parent_hash,
                    "parent_version": parent_version,
                    "version_path": relative_path,
                    "diff": change,
                }
            )
            pointer = {
                "system_name": self.CANONICAL_SYSTEM_NAME,
                "schema_version": self.SCHEMA_VERSION,
                "origin_signature": self.ORIGIN_SIGNATURE,
                "seed_id": safe_id,
                "version": version,
                "content_hash": content_hash,
                "path": relative_path,
                "activation_event_hash": event["event_hash"],
                "transaction_id": transaction_id,
                "updated_at": self._now(),
            }
            self._atomic_write_json(pointer_path, pointer)
            return {
                "system_name": self.CANONICAL_SYSTEM_NAME,
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
                "system_name": self.CANONICAL_SYSTEM_NAME,
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
            "system_name": self.CANONICAL_SYSTEM_NAME,
            "path": str(target),
            "seed_id": active["seed_id"],
            "version": active["version"],
            "content_hash": active["content_hash"],
        }

    def build_context(self, seed_id: str, max_insights: int = 20) -> Dict[str, Any]:
        """Return active verified insights for a downstream task."""
        if not isinstance(max_insights, int) or isinstance(max_insights, bool) or max_insights < 1:
            raise ValueError("max_insights must be a positive integer")
        active = self.load_active(seed_id)
        insights = active["seed"].get("insights", [])[:max_insights]
        return {
            "system_name": self.CANONICAL_SYSTEM_NAME,
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
        if not isinstance(task, dict):
            raise TypeError("task must be a mapping")
        if isinstance(seed_ids, (str, bytes)):
            raise TypeError("seed_ids must be an iterable of seed identifiers, not a string")
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
            self._validate_envelope(target, safe_id, target_version)
            relative_path = str(target_path.relative_to(self.storage_path)).replace("\\", "/")
            transaction_id = uuid.uuid4().hex
            event = self._append_event(
                {
                    "event_type": "rollback",
                    "transaction_id": transaction_id,
                    "seed_id": safe_id,
                    "version": target_version,
                    "content_hash": target["content_hash"],
                    "version_path": relative_path,
                }
            )
            self._atomic_write_json(
                self._active_file(safe_id),
                {
                    "system_name": self.CANONICAL_SYSTEM_NAME,
                    "schema_version": self.SCHEMA_VERSION,
                    "origin_signature": self.ORIGIN_SIGNATURE,
                    "seed_id": safe_id,
                    "version": target_version,
                    "content_hash": target["content_hash"],
                    "path": relative_path,
                    "activation_event_hash": event["event_hash"],
                    "transaction_id": transaction_id,
                    "updated_at": self._now(),
                },
            )
            result = {
                "system_name": self.CANONICAL_SYSTEM_NAME,
                "status": "rolled_back",
                "seed_id": safe_id,
                "version": target_version,
                "content_hash": target["content_hash"],
                "event_hash": event["event_hash"],
            }
        result["mqm_export"] = self.export_active_for_mqm(safe_id)
        return result

    def verify_store(self, seed_id: Optional[str] = None) -> Dict[str, Any]:
        """Verify seed hashes, parent references, active pointers, and journal chain."""
        errors: List[str] = []
        checked_versions = 0
        records, journal_errors = self._read_and_verify_journal()
        errors.extend(journal_errors)
        seed_dirs = [self._seed_dir(seed_id)] if seed_id else sorted(self.seeds_path.glob("*"))
        for seed_dir in seed_dirs:
            if not seed_dir.exists():
                errors.append(f"Missing seed directory: {seed_dir}")
                continue
            versions = self._version_files(seed_dir.name)
            all_version_paths = sorted(seed_dir.glob("v*.json"))
            if len(versions) != len(all_version_paths):
                invalid = sorted(path.name for path in all_version_paths if not self.VERSION_PATTERN.fullmatch(path.name))
                errors.append(f"Invalid version filename(s) for {seed_dir.name}: {invalid}")
            if versions:
                expected_versions = set(range(1, max(versions) + 1))
                missing_versions = sorted(expected_versions - set(versions))
                if missing_versions:
                    errors.append(f"Version gap for {seed_dir.name}: {missing_versions}")
            envelopes: Dict[int, Dict[str, Any]] = {}
            for version, path in sorted(versions.items()):
                try:
                    envelope = self._read_json(path)
                    self._validate_envelope(envelope, seed_dir.name, version)
                except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
                    errors.append(f"Invalid seed version {path}: {error}")
                    continue
                checked_versions += 1
                envelopes[version] = envelope
            for version, envelope in sorted(envelopes.items()):
                parent_version = envelope.get("parent_version")
                parent_hash = envelope.get("parent_hash")
                if parent_version is None and parent_hash is None:
                    if version != 1:
                        errors.append(f"Missing parent reference: {seed_dir.name} v{version}")
                elif not isinstance(parent_version, int) or parent_version not in envelopes:
                    errors.append(f"Missing parent version: {seed_dir.name} v{version}")
                elif envelopes[parent_version].get("content_hash") != parent_hash:
                    errors.append(f"Parent hash mismatch: {seed_dir.name} v{version}")
                matching_events = [
                    event
                    for event in records
                    if event.get("event_type") in {"created", "upgraded"}
                    and event.get("seed_id") == seed_dir.name
                    and event.get("version") == version
                    and event.get("content_hash") == envelope.get("content_hash")
                ]
                if not matching_events:
                    errors.append(f"Journal coverage missing: {seed_dir.name} v{version}")
            pointer_path = self._active_file(seed_dir.name)
            if not pointer_path.exists():
                errors.append(f"Missing active pointer: {seed_dir.name}")
            else:
                try:
                    self.load_active(seed_dir.name)
                except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
                    errors.append(str(error))

        return {
            "system_name": self.CANONICAL_SYSTEM_NAME,
            "status": "PASS" if not errors else "FAIL",
            "checked_versions": checked_versions,
            "errors": errors,
        }


# Backward-compatible import for existing DL580 scripts. New code must use the
# canonical MRL name; the persisted schema stays stable so existing stores remain readable.
MotherGrowthLoop = MRL_MotherGrowthLoop_v1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Absorb external data into MRL_MotherGrowthLoop_v1 memory"
    )
    parser.add_argument("source", nargs="?", help="File, folder, repository path, or literal text")
    parser.add_argument("--seed-id", required=True)
    parser.add_argument("--source-type", default="auto")
    parser.add_argument("--storage", default="mother_memory")
    parser.add_argument("--trust-level", default="medium")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--verify-only", action="store_true")
    action.add_argument("--rollback-version", type=int)
    args = parser.parse_args()

    loop = MRL_MotherGrowthLoop_v1(args.storage)
    result: Dict[str, Any]
    mqm_export: Optional[Dict[str, Any]] = None
    if args.verify_only:
        result = {"status": "verification_only"}
    elif args.rollback_version is not None:
        result = loop.rollback(args.seed_id, args.rollback_version)
        mqm_export = result.get("mqm_export")
    else:
        if not args.source:
            parser.error("source is required unless --verify-only or --rollback-version is used")
        from conversation_extractor import ConversationExtractor

        absorbed = loop.process_and_absorb(
            ConversationExtractor(),
            args.source,
            seed_id=args.seed_id,
            source_type=args.source_type,
            trust_level=args.trust_level,
        )
        result = absorbed["backfill"]
        mqm_export = absorbed["mqm_export"]
    verification = loop.verify_store(args.seed_id)
    print(
        json.dumps(
            {
                "system_name": loop.CANONICAL_SYSTEM_NAME,
                "result": result,
                "mqm_export": mqm_export,
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
