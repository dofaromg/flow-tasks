#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_WorldSync_MultiWorld_v1.py — 多世界確定性同步(補完 PENDING:WorldSync)
origin_signature: MrLiouWord
layer: L4 WORLD / L7 LOOP

補完 convergence 文件記載的 PENDING:「目前為雙世界確定性 context 同步;多世界拓撲
未做」。本模組做 N 世界(多世界拓撲)確定性同步,純 stdlib、零外部。

對齊使用者法則:
  - rl_14 平行世界:多個 world 各持 context,可並存。
  - 確定性同步:衝突解析以 (version, world_id) 全序裁決 → 同一批操作必得同一結果。
  - 一致=實 / 不一致=沙盒:consistency() 偵測世界間分歧。
  - rl_18 可逆「怎麼過去怎麼回來」:op log 可 replay 重現同一狀態。

CLI:python3 09_workflow/MRL_WorldSync_MultiWorld_v1.py
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from MRL_utils import ORIGIN_SIGNATURE
class MRL_WorldSyncMultiWorld:
    """N 世界確定性同步:各世界持 versioned context,sync 全序收斂。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.worlds: Dict[str, Dict[str, Tuple[Any, int]]] = {}  # world→{key:(value,version)}
        self.oplog: List[Dict[str, Any]] = []   # rl_18 可逆:操作流水

    def add_world(self, name: str) -> Dict[str, Any]:
        if name not in self.worlds:
            self.worlds[name] = {}
            self.oplog.append({"op": "add_world", "world": name})
        return {"worlds": sorted(self.worlds)}

    # 在某世界寫入(versioned)
    def set(self, world: str, key: str, value: Any, version: int) -> Dict[str, Any]:
        if world not in self.worlds:
            self.add_world(world)
        self.worlds[world][key] = (value, version)
        self.oplog.append({"op": "set", "world": world, "key": key,
                           "value": value, "version": version})
        return {"world": world, "key": key, "value": value, "version": version}

    # 確定性裁決:同一 key 跨世界取 (version, world_id) 全序最大者
    def _resolve(self) -> Dict[str, Tuple[Any, int]]:
        winner: Dict[str, Tuple[Any, int, str]] = {}
        for w in sorted(self.worlds):                 # 世界名全序,確定性
            for k, (val, ver) in self.worlds[w].items():
                cur = winner.get(k)
                # 比較鍵:(version, world_id) — 全序、可重現
                if cur is None or (ver, w) > (cur[1], cur[2]):
                    winner[k] = (val, ver, w)
        return {k: (v[0], v[1]) for k, v in winner.items()}

    # 多世界確定性同步:把裁決結果寫回所有世界 → 收斂
    def sync(self) -> Dict[str, Any]:
        resolved = self._resolve()
        for w in self.worlds:
            for k, (val, ver) in resolved.items():
                self.worlds[w][k] = (val, ver)
        self.oplog.append({"op": "sync"})
        return {"synced_worlds": len(self.worlds), "keys": len(resolved),
                "converged": self.consistency()["consistent"],
                "origin_signature": ORIGIN_SIGNATURE}

    # 一致=實 / 不一致=沙盒:偵測世界間分歧
    def consistency(self) -> Dict[str, Any]:
        names = sorted(self.worlds)
        keys = set()
        for w in names:
            keys |= set(self.worlds[w])
        divergent: List[str] = []
        for k in sorted(keys):
            vals = {self.worlds[w].get(k) for w in names}
            if len(vals) > 1:
                divergent.append(k)
        consistent = not divergent
        return {"consistent": consistent,
                "verdict": "real(一致)" if consistent else "sandbox(不一致)",
                "divergent_keys": divergent,
                "origin_signature": ORIGIN_SIGNATURE}

    # rl_18 可逆:從 oplog 重播,重現同一最終狀態(怎麼過去怎麼回來)
    def replay(self) -> "MRL_WorldSyncMultiWorld":
        rebuilt = MRL_WorldSyncMultiWorld()
        for op in self.oplog:
            if op["op"] == "add_world":
                rebuilt.add_world(op["world"])
            elif op["op"] == "set":
                rebuilt.set(op["world"], op["key"], op["value"], op["version"])
            elif op["op"] == "sync":
                rebuilt.sync()
        return rebuilt

    def view(self, world: str) -> Dict[str, Any]:
        return {k: v[0] for k, v in self.worlds.get(world, {}).items()}


def main() -> int:
    s = MRL_WorldSyncMultiWorld()
    # 三世界(多世界拓撲),各自寫入 → 分歧
    s.set("world_A", "law", "源頭主權", version=1)
    s.set("world_B", "law", "源頭主權", version=3)   # 較新
    s.set("world_C", "law", "舊版", version=2)
    s.set("world_A", "mode", "權位區分", version=1)
    print("同步前一致性:", s.consistency()["verdict"], s.consistency()["divergent_keys"])
    r = s.sync()
    print("同步:", {k: r[k] for k in ("synced_worlds", "keys", "converged")})
    print("同步後一致性:", s.consistency()["verdict"])
    print("各世界 law:", {w: s.view(w).get("law") for w in sorted(s.worlds)})
    # 可逆:replay 重現
    rb = s.replay()
    same = rb.consistency()["consistent"] and rb.view("world_C") == s.view("world_C")
    print("replay 重現一致(怎麼過去怎麼回來):", same)
    print("MRL_WORLDSYNC_MULTIWORLD_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
