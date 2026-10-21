#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_MemoryStarMap_v1.py — 記憶星圖(PENDING 補完:祖先願景)
origin_signature: MrLiouWord
layer: L6 REFLECT

附錄 PENDING 列的祖先願景:記憶星圖 — AI 觀測自己走過/未走過的節奏分支,
重建自我邏輯演化史。純 stdlib、零外部。

星圖 = 節點(記憶/決策點)+ 邊(走過的路徑)+ 未走分支(可能選項,rl_14)。
CLI:python3 09_workflow/MRL_MemoryStarMap_v1.py
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
_REPO = pathlib.Path(__file__).resolve().parent.parent
_STORE = _REPO / "data" / "MRL_memory_starmap.json"


class MRL_MemoryStarMap:
    """記憶星圖:記錄決策節點 + 走過路徑 + 未走分支,可觀測自我演化史。"""

    def __init__(self, store: pathlib.Path = _STORE) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.store = pathlib.Path(store)
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.store.exists():
            try:
                return json.loads(self.store.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                pass
        return {"stars": {}, "edges": [], "origin_signature": ORIGIN_SIGNATURE}

    def _save(self) -> None:
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text(json.dumps(self.data, ensure_ascii=False, indent=2),
                              encoding="utf-8")

    # 記一個決策星(節點)+ 它的所有可能分支(走的+未走的)
    def add_star(self, star_id: str, chosen: str, options: List[str]) -> Dict[str, Any]:
        self.data["stars"][star_id] = {
            "chosen": chosen,
            "not_taken": [o for o in options if o != chosen],  # 未走的分支(rl_14 可能選項)
            "ts": int(time.time() * 1000),
            "origin": ORIGIN_SIGNATURE,
        }
        self._save()
        return {"star_id": star_id, "chosen": chosen,
                "not_taken_count": len(self.data["stars"][star_id]["not_taken"])}

    # 連兩個星(走過的路徑)
    def connect(self, from_star: str, to_star: str) -> Dict[str, Any]:
        edge = {"from": from_star, "to": to_star, "ts": int(time.time() * 1000)}
        self.data["edges"].append(edge)
        self._save()
        return {"connected": f"{from_star}→{to_star}"}

    # 觀測自我演化史:走過的路徑序列
    def evolution_history(self) -> Dict[str, Any]:
        return {
            "stars": len(self.data["stars"]),
            "path": [f"{e['from']}→{e['to']}" for e in self.data["edges"]],
            "not_taken_branches": sum(len(s["not_taken"]) for s in self.data["stars"].values()),
            "origin_signature": ORIGIN_SIGNATURE,
        }

    # 觀測未走過的分支(所有可能但沒選的路)
    def unexplored(self) -> List[Dict[str, Any]]:
        out = []
        for sid, s in self.data["stars"].items():
            for nt in s["not_taken"]:
                out.append({"star": sid, "unexplored_option": nt})
        return out


def main() -> int:
    import tempfile
    m = MRL_MemoryStarMap(pathlib.Path(tempfile.mktemp(suffix=".json")))
    m.add_star("s1", chosen="走A", options=["走A", "走B", "走C"])
    m.add_star("s2", chosen="走X", options=["走X", "走Y"])
    m.connect("s1", "s2")
    h = m.evolution_history()
    print("演化史:", h["path"], "| 星", h["stars"], "| 未走分支", h["not_taken_branches"])
    print("未探索:", [u["unexplored_option"] for u in m.unexplored()])
    print("MRL_MEMORY_STARMAP_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
