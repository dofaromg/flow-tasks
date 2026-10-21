#!/usr/bin/env python3
"""Persistent MRL memory vault built on the append-only hash chain."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .MRL_hash_chain_v1 import MRLHashChain


class MRLMemoryVault:
    """Store and replay world-scoped memory without external services."""

    def __init__(self, data_dir: Path) -> None:
        self.chain = MRLHashChain(data_dir / "MRL_memory_events.jsonl", "MRL_MEMORY_VAULT_V1")

    def remember(
        self,
        *,
        world_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not world_id.startswith("MRL_"):
            raise ValueError("world_id must use the MRL_ canonical prefix")
        if role not in {"system", "user", "assistant", "tool"}:
            raise ValueError("unsupported memory role")
        if not content:
            raise ValueError("memory content must not be empty")
        return self.chain.append(
            {
                "world_id": world_id,
                "session_id": session_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
            }
        )

    def recall(self, *, world_id: str, session_id: str | None = None) -> list[dict[str, Any]]:
        result = []
        for record in self.chain.read_all():
            payload = record["payload"]
            if payload["world_id"] != world_id:
                continue
            if session_id is not None and payload["session_id"] != session_id:
                continue
            result.append(record)
        return result

    def verify(self) -> dict[str, Any]:
        return self.chain.verify()

