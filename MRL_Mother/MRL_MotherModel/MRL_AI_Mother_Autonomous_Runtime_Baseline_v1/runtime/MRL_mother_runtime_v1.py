#!/usr/bin/env python3
"""Orchestrate local inference, memory, passport and evidence as one MRL loop."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from . import ORIGIN_SIGNATURE, RUNTIME_ID
from .MRL_evidence_ledger_v1 import MRLEvidenceLedger
from .MRL_local_model_adapter_v1 import MRLLocalModelAdapter
from .MRL_memory_vault_v1 import MRLMemoryVault
from .MRL_passport_registry_v1 import MRLPassportRegistry


class MRLMotherRuntime:
    """The autonomous baseline: local model -> memory -> passport -> evidence."""

    def __init__(self, config: dict[str, Any], data_dir: Path) -> None:
        self.config = config
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        model = config.get("local_model") or {}
        self.adapter = MRLLocalModelAdapter(
            backend=str(model.get("backend") or "ollama"),
            endpoint=str(model.get("endpoint") or "http://127.0.0.1:11434"),
            model=str(model.get("model") or "MRL_LOCAL_MODEL_NOT_CONFIGURED"),
            timeout_seconds=int(model.get("timeout_seconds") or 120),
        )
        self.memory = MRLMemoryVault(data_dir)
        self.evidence = MRLEvidenceLedger(data_dir)
        self.passports = MRLPassportRegistry(data_dir)

    @classmethod
    def from_file(cls, config_path: Path, data_dir: Path | None = None) -> "MRLMotherRuntime":
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("runtime config must be an object")
        resolved_data_dir = data_dir or Path(str(config.get("data_dir") or "./MRL_runtime_data"))
        return cls(config, resolved_data_dir)

    def health(self) -> dict[str, Any]:
        model_health = self.adapter.health()
        memory_health = self.memory.verify()
        evidence_health = self.evidence.verify()
        ready = bool(model_health["ready"] and memory_health["ok"] and evidence_health["ok"])
        return {
            "runtime_id": RUNTIME_ID,
            "ready": ready,
            "autonomy_gate": "PASS" if ready else "OPEN",
            "model": model_health,
            "memory": memory_health,
            "evidence": evidence_health,
            "external_model_required": False,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def run(
        self,
        *,
        prompt: str,
        world_id: str = "MRL_main",
        session_id: str | None = None,
        system_prompt: str = "You are the local MRL AI mother runtime.",
    ) -> dict[str, Any]:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        if not world_id.startswith("MRL_"):
            raise ValueError("world_id must use the MRL_ canonical prefix")
        session_id = session_id or f"MRL_session_{uuid.uuid4().hex}"
        input_record = self.memory.remember(
            world_id=world_id,
            session_id=session_id,
            role="user",
            content=prompt,
            metadata={"runtime_id": RUNTIME_ID},
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        try:
            inference = self.adapter.complete(messages)
        except Exception as exc:
            failure = self.evidence.record(
                event_type="MRL_LOCAL_INFERENCE",
                state="FAIL",
                subject_id=session_id,
                details={"error": f"{type(exc).__name__}: {exc}", "world_id": world_id},
            )
            raise RuntimeError(
                f"MRL_LOCAL_INFERENCE_FAILED evidence={failure['record_hash']}"
            ) from exc
        output_record = self.memory.remember(
            world_id=world_id,
            session_id=session_id,
            role="assistant",
            content=inference["text"],
            metadata={"model": inference["model"], "backend": inference["backend"]},
        )
        evidence = self.evidence.record(
            event_type="MRL_LOCAL_INFERENCE",
            state="PASS",
            subject_id=session_id,
            details={
                "world_id": world_id,
                "input_memory_hash": input_record["record_hash"],
                "output_memory_hash": output_record["record_hash"],
                "backend": inference["backend"],
                "model": inference["model"],
                "external_model_required": False,
            },
        )
        passport = self.passports.issue(
            canonical_id=f"MRL_output_{session_id.removeprefix('MRL_session_')}",
            source_identity=session_id,
            world_state="candidate",
            capabilities=["MRL_LOCAL_INFERENCE", "MRL_MEMORY_REPLAY"],
            evidence_refs=[evidence["record_hash"]],
            return_anchor=input_record["record_hash"],
            environment={
                "runtime_id": RUNTIME_ID,
                "backend": inference["backend"],
                "model": inference["model"],
            },
            rights={"state": "MRL_INTERNAL_RUNTIME_OUTPUT"},
        )
        return {
            "ok": True,
            "session_id": session_id,
            "world_id": world_id,
            "text": inference["text"],
            "model": inference["model"],
            "backend": inference["backend"],
            "memory": {
                "input": input_record["record_hash"],
                "output": output_record["record_hash"],
            },
            "evidence_ref": evidence["record_hash"],
            "passport": passport,
            "external_model_required": False,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def recall(self, *, world_id: str, session_id: str | None = None) -> dict[str, Any]:
        return {
            "world_id": world_id,
            "session_id": session_id,
            "records": self.memory.recall(world_id=world_id, session_id=session_id),
            "origin_signature": ORIGIN_SIGNATURE,
        }

