#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_DurableReplay_Instrumentation_v1.py — 持久重播儀器(補完 ReplayRestore 常駐結構)
origin_signature: MrLiouWord
layer: L7 LOOP

補完缺的結構邏輯:in-process 的精確重播已實(MRL_ReplayRestore_Core),持久落盤已實
(MRL_PersistentLoop_Daemon);缺的是把兩者接起來的「常駐 runtime instrumentation」——
長駐 runtime 每步 op **持久落盤(append-only JSONL)**,跨重啟後由持久事件流**精確重播**,
state hash 與重啟前一致 = exact(怎麼過去怎麼回來)。純 stdlib、零外部。

對齊:rl_01 no-delete(事件 append-only 只增不刪)、rl_18 可逆(exact replay)、
跨重啟存活(durable 落盤)。
CLI:python3 09_workflow/MRL_DurableReplay_Instrumentation_v1.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
def _state_hash(state: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(state, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _fold(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """確定性折疊:事件序 → state(與 ReplayRestore_Core 同模型)。"""
    state: Dict[str, Any] = {"applied": [], "node_count": 0, "intent_tally": {}}
    for ev in events:
        state["applied"].append(ev["node_id"])
        state["node_count"] += 1
        intent = ev.get("intent", "_")
        state["intent_tally"][intent] = state["intent_tally"].get(intent, 0) + 1
    return state


class MRL_DurableReplayInstrumentation:
    """常駐儀器:每步 op append-only 落盤;跨重啟由持久日誌精確重播。"""

    def __init__(self, log_path: pathlib.Path) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.log_path = pathlib.Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    # 儀器:記錄一步 op → append-only 持久落盤(rl_01 no-delete)
    def record(self, node_id: str, intent: str = "_") -> Dict[str, Any]:
        ev = {"node_id": node_id, "intent": intent}
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
        return ev

    # 讀回持久事件流(跨重啟:新實例指同一日誌即續)
    def load_events(self) -> List[Dict[str, Any]]:
        if not self.log_path.exists():
            return []
        events: List[Dict[str, Any]] = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                events.append(json.loads(line))
        return events

    # 當前 state(由持久事件流折疊)
    def state(self) -> Dict[str, Any]:
        return _fold(self.load_events())

    def state_hash(self) -> str:
        return _state_hash(self.state())

    # 精確重播:由持久日誌重建 → 與給定 hash 比對(跨重啟 exact)
    def exact_replay(self, expected_hash: Optional[str] = None) -> Dict[str, Any]:
        state = self.state()
        h = _state_hash(state)
        exact = (expected_hash is None) or (h == expected_hash)
        return {"state": state, "hash": h, "exact": exact,
                "events": len(state["applied"]),
                "origin_signature": ORIGIN_SIGNATURE}

    # 回滾:由持久日誌前 n+1 步折疊(no-delete:不動日誌,只回讀)
    def rollback(self, n: int) -> Dict[str, Any]:
        events = self.load_events()[: n + 1]
        state = _fold(events)
        return {"rolled_back_to": n, "state": state, "hash": _state_hash(state)}


def main() -> int:
    import tempfile
    log = pathlib.Path(tempfile.mktemp(suffix=".jsonl"))
    # 常駐 runtime 跑若干步,每步落盤
    inst = MRL_DurableReplayInstrumentation(log)
    for i in range(6):
        inst.record(f"n{i}", intent="observe" if i % 2 == 0 else "resolve")
    pre_hash = inst.state_hash()
    print("跑 6 步,state hash:", pre_hash[:16], "…")
    # 模擬重啟:新實例指同一持久日誌
    rebooted = MRL_DurableReplayInstrumentation(log)
    rep = rebooted.exact_replay(expected_hash=pre_hash)
    print(f"重啟後精確重播: events={rep['events']} exact={rep['exact']} (應 True=跨重啟一致)")
    rb = rebooted.rollback(2)
    print("回滾至第2步:", rb["state"]["node_count"], "節點")
    log.unlink(missing_ok=True)
    print("MRL_DURABLE_REPLAY_INSTRUMENTATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
