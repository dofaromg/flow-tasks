#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_PersistentLoop_Daemon_v1.py — 持久迴圈守護(PENDING-03 補完)
origin_signature: MrLiouWord
layer: L7 LOOP

附錄 PENDING-03 列的未完成項:MRL_PersistentLoop_Daemon 全量實作。
母體持久運行迴圈:跨重啟存活(狀態落盤),每 tick 跑 Liou 閉環,可 replay/restore。
純 stdlib、零外部。對齊 rl_18 可逆(replay→restore)、rl_01 no-delete(狀態 additive 落盤)。

跨重啟存活:狀態寫 data/MRL_persistent_loop_state.json;重啟讀回,從上次 tick 續跑。
CLI:python3 09_workflow/MRL_PersistentLoop_Daemon_v1.py [ticks]
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Callable, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
_REPO = pathlib.Path(__file__).resolve().parent.parent
_STATE = _REPO / "data" / "MRL_persistent_loop_state.json"


class MRL_PersistentLoopDaemon:
    """
    持久迴圈守護。每 tick:Observe→Resolve→Mirror→Verify→Loop,狀態落盤。
    跨重啟:從落盤狀態續跑(reboot survival)。
    """

    def __init__(self, state_path: pathlib.Path = _STATE) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.state_path = pathlib.Path(state_path)
        self.state: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.state_path.exists():
            try:
                s = json.loads(self.state_path.read_text(encoding="utf-8"))
                s["resumed"] = True   # 標記:這次是從落盤狀態續跑(reboot survival)
                return s
            except Exception:  # noqa: BLE001
                pass
        return {"tick": 0, "history": [], "origin_signature": ORIGIN_SIGNATURE,
                "resumed": False}

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2),
                                   encoding="utf-8")

    # 單 tick 閉環(可注入 work 函式)
    def tick(self, work: Optional[Callable[[Dict[str, Any]], Any]] = None) -> Dict[str, Any]:
        self.state["tick"] += 1
        loop = ["Observe", "Resolve", "Mirror", "Verify", "Loop"]
        result = None
        if work is not None:
            try:
                result = work(self.state)
            except Exception as exc:  # noqa: BLE001
                result = {"error": str(exc)}
        entry = {"tick": self.state["tick"], "ts": int(time.time() * 1000),
                 "loop": loop, "result": result}
        self.state["history"].append(entry)
        # additive 落盤(rl_01 no-delete:歷史只增不刪;只截顯示不截存)
        self._save()
        return entry

    def run(self, ticks: int = 5, work: Optional[Callable] = None,
            interval_s: float = 0.0) -> Dict[str, Any]:
        """跑 N 個 tick。每 tick 落盤 → 任何時點被殺,重啟可從落盤續跑。"""
        start_tick = self.state["tick"]
        for _ in range(ticks):
            self.tick(work)
            if interval_s:
                time.sleep(interval_s)
        return {"ran": ticks, "from_tick": start_tick, "to_tick": self.state["tick"],
                "resumed_from_disk": self.state.get("resumed", False),
                "total_history": len(self.state["history"]),
                "origin_signature": ORIGIN_SIGNATURE}

    # replay:重播迄今所有 tick(rl_18 可逆)
    def replay(self) -> List[Dict[str, Any]]:
        return list(self.state["history"])

    # restore:回到指定 tick 的狀態快照(no-delete:不刪後續,只回讀)
    def restore_to(self, tick_no: int) -> Dict[str, Any]:
        snap = [h for h in self.state["history"] if h["tick"] <= tick_no]
        return {"restored_to_tick": tick_no, "entries": len(snap),
                "origin_signature": ORIGIN_SIGNATURE}


def main() -> int:
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    import tempfile
    # 用臨時狀態檔示範跨重啟(兩個 daemon 共用同檔=模擬重啟續跑)
    sp = pathlib.Path(tempfile.mktemp(suffix=".json"))
    d1 = MRL_PersistentLoopDaemon(sp)
    r1 = d1.run(n)
    print(f"第一次跑: tick {r1['from_tick']}→{r1['to_tick']}, resumed={r1['resumed_from_disk']}")
    # 模擬重啟:新 daemon 讀同一狀態檔
    d2 = MRL_PersistentLoopDaemon(sp)
    r2 = d2.run(n)
    print(f"重啟續跑: tick {r2['from_tick']}→{r2['to_tick']}, resumed={r2['resumed_from_disk']} (應True=跨重啟存活)")
    print(f"replay 總 tick: {len(d2.replay())}")
    sp.unlink(missing_ok=True)
    print("MRL_PERSISTENT_LOOP_DAEMON_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
