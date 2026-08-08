#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_StructureField_Runtime_v1.py — Replay/Restore/World StructureField(命名規範v2 §3 落實)
origin_signature: MrLiouWord
layer: L4 WORLD + L7 LOOP

命名規範 v2 §3 列為「前瞻命名,不得空殼」的三個:
  MRL_ReplayStructureField   回放結構場 — 重播事件序列(怎麼過去怎麼回來)
  MRL_RestoreStructureField  復原結構場 — 從快照/事件鏈還原狀態
  MRL_WorldStructureField    世界結構場 — 多實例狀態同步

照規範語義做成「會跑的」(非空殼):純 stdlib,接事件序列/快照,可逆閉環。
對齊:rl_18 可逆平等(replay→restore 同路往返)/ rl_01 no-delete(快照 additive)/ LAW-0。

零依賴。CLI:python3 09_workflow/MRL_StructureField_Runtime_v1.py
"""
from __future__ import annotations

import copy
import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
def _hash(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, default=str)
                          .encode("utf-8")).hexdigest()


class MRL_ReplayStructureField:
    """回放結構場:記錄事件序列,可重播重建狀態(deterministic)。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.events: List[Dict[str, Any]] = []

    def record(self, op: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        ev = {"seq": len(self.events), "ts": int(time.time() * 1000),
              "op": op, "payload": payload}
        self.events.append(ev)
        return ev

    def replay(self, reducer, initial: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """重播全部事件,經 reducer 重建狀態。同事件序列→同結果(可重播驗證)。"""
        state = copy.deepcopy(initial or {})
        for ev in self.events:
            state = reducer(state, ev)
        return {"state": state, "replayed_events": len(self.events),
                "merkle": _hash(self.events)[:16], "origin_signature": ORIGIN_SIGNATURE}


class MRL_RestoreStructureField:
    """復原結構場:快照 + 從快照還原(rl_01 no-delete:快照只增不刪)。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.snapshots: List[Dict[str, Any]] = []

    def snapshot(self, state: Dict[str, Any]) -> Dict[str, Any]:
        snap = {"id": len(self.snapshots), "ts": int(time.time() * 1000),
                "state": copy.deepcopy(state), "hash": _hash(state)[:16]}
        self.snapshots.append(snap)
        return {"snapshot_id": snap["id"], "hash": snap["hash"],
                "origin_signature": ORIGIN_SIGNATURE}

    def restore(self, snapshot_id: Optional[int] = None) -> Dict[str, Any]:
        """還原到指定快照(預設最新)。no_proof:無快照誠實回錯。"""
        if not self.snapshots:
            return {"restored": False, "error": "no snapshot"}
        sid = snapshot_id if snapshot_id is not None else self.snapshots[-1]["id"]
        if sid < 0 or sid >= len(self.snapshots):
            return {"restored": False, "error": f"snapshot {sid} not found"}
        snap = self.snapshots[sid]
        return {"restored": True, "snapshot_id": sid,
                "state": copy.deepcopy(snap["state"]),
                "hash_verified": _hash(snap["state"])[:16] == snap["hash"],
                "origin_signature": ORIGIN_SIGNATURE}


class MRL_WorldStructureField:
    """世界結構場:多實例(平行世界)狀態註冊 + 同步(rl_14)。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.worlds: Dict[str, Dict[str, Any]] = {}

    def register(self, world_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        self.worlds[world_id] = {"state": copy.deepcopy(state),
                                 "origin": ORIGIN_SIGNATURE, "ts": int(time.time() * 1000)}
        return {"world_id": world_id, "registered": True}

    def sync(self, source_id: str, target_id: str) -> Dict[str, Any]:
        """把 source 世界狀態同步到 target(訊息互通,rl_13)。"""
        if source_id not in self.worlds:
            return {"synced": False, "error": f"source {source_id} not found"}
        self.worlds[target_id] = {"state": copy.deepcopy(self.worlds[source_id]["state"]),
                                  "origin": ORIGIN_SIGNATURE, "ts": int(time.time() * 1000),
                                  "synced_from": source_id}
        return {"synced": True, "from": source_id, "to": target_id,
                "origin_signature": ORIGIN_SIGNATURE}

    def list_worlds(self) -> List[str]:
        return list(self.worlds.keys())


def main() -> int:
    # Replay
    rp = MRL_ReplayStructureField()
    rp.record("add", {"k": "a", "v": 1}); rp.record("add", {"k": "b", "v": 2})
    def reducer(s, ev):
        if ev["op"] == "add":
            s[ev["payload"]["k"]] = ev["payload"]["v"]
        return s
    r = rp.replay(reducer)
    print("Replay:", r["state"], "events:", r["replayed_events"])
    # Restore
    rs = MRL_RestoreStructureField()
    rs.snapshot({"x": 1}); rs.snapshot({"x": 2})
    print("Restore latest:", rs.restore()["state"], "| snap0:", rs.restore(0)["state"])
    # World
    w = MRL_WorldStructureField()
    w.register("w0", {"v": 42}); w.sync("w0", "w1")
    print("World sync:", w.list_worlds())
    print("MRL_STRUCTUREFIELD_RUNTIME_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
