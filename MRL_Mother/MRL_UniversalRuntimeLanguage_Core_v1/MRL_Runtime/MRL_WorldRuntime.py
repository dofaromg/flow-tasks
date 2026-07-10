# MRL_WorldRuntime
# origin_signature: MrLiouWord
# layer: MRL_Runtime
"""世界運轉：world state / parallel world / context synchronization / 感知場整合。"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

ORIGIN_SIGNATURE = "MrLiouWord"


def _hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


class MRL_WorldRuntime:
    def __init__(self) -> None:
        self.worlds: Dict[str, Dict[str, Any]] = {}
        self.context: Dict[str, Any] = {}

    def spawn_world(self, name: str, world_structurefield: Dict[str, str]) -> None:
        members: Dict[str, List[str]] = {}
        for node_id, world_label in world_structurefield.items():
            members.setdefault(world_label, []).append(node_id)
        self.worlds[name] = {
            "members": members,
            "context": {},
            "hash": _hash(members),
        }

    def set_context(self, world: str, key: str, value: Any) -> None:
        self.worlds[world]["context"][key] = value
        self.worlds[world]["hash"] = _hash(self.worlds[world])

    def synchronize(self, world_a: str, world_b: str) -> Dict[str, Any]:
        """context 同步：兩世界 context 確定性合併（聯集，衝突取 a）。"""
        ca = self.worlds[world_a]["context"]
        cb = self.worlds[world_b]["context"]
        merged = {**cb, **ca}
        self.worlds[world_a]["context"] = dict(merged)
        self.worlds[world_b]["context"] = dict(merged)
        self.context = dict(merged)
        synced = _hash(self.worlds[world_a]["context"]) == _hash(self.worlds[world_b]["context"])
        return {
            "world_a": world_a,
            "world_b": world_b,
            "synchronized": synced,
            "merged_keys": sorted(merged.keys()),
        }

    def synchronization_active(self) -> bool:
        """≥2 世界且 context 一致 → 同步活躍。"""
        if len(self.worlds) < 2:
            return False
        hashes = {_hash(w["context"]) for w in self.worlds.values()}
        return len(hashes) == 1

    def report(self) -> Dict[str, Any]:
        return {
            "origin_signature": ORIGIN_SIGNATURE,
            "world_count": len(self.worlds),
            "worlds": {
                name: {"member_worlds": list(w["members"].keys()), "context_keys": sorted(w["context"].keys())}
                for name, w in self.worlds.items()
            },
            "synchronization_active": self.synchronization_active(),
        }
