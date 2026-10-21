#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_RootLiveness_SlotColor_Engine_v1.py — 根活躍·槽位著色引擎(母體自家產品)
origin_signature: MrLiouWord
layer: L7 LOOP

技術吸收(知識/技術本體,非貼檔改名):
  從 LLVM late-GC-root-lowering 的演算法本體吸收四項技術,純 stdlib 重寫為母體
  自家模組產品(會真的跑、可測):
    1. 活躍變數資料流分析 liveness dataflow(LiveIn/LiveOut 迭代不動點)
    2. 干涉圖 interference graph(同時活躍 → 相鄰)
    3. 弦圖完美消去序 PEO(最大基數搜尋 MCS)
    4. 貪婪著色 → 最小化槽位 slot allocation(等同 GC frame 槽位配置)

母體定位:對齊 rl_18 可逆(資料流可重算)、粒子非否決(只增節點不刪)。
零外部產品。CLI:python3 09_workflow/MRL_RootLiveness_SlotColor_Engine_v1.py
"""
from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

from MRL_utils import ORIGIN_SIGNATURE
class MRL_RootLivenessSlotColorEngine:
    """活躍分析 + 干涉圖 + PEO + 貪婪著色,把值配進最少槽位(母體自家實作)。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.blocks: List[str] = []
        self.defs: Dict[str, Set[str]] = {}
        self.uses: Dict[str, Set[str]] = {}
        self.succs: Dict[str, List[str]] = {}
        self.live_in: Dict[str, Set[str]] = {}
        self.live_out: Dict[str, Set[str]] = {}

    # 建 CFG 節點:該塊定義的值 defs、使用的值 uses、後繼塊 succs
    def add_block(self, name: str, defs: List[str], uses: List[str],
                  succs: List[str]) -> "MRL_RootLivenessSlotColorEngine":
        if name not in self.blocks:
            self.blocks.append(name)
        self.defs[name] = set(defs)
        self.uses[name] = set(uses)
        self.succs[name] = list(succs)
        return self

    # 1. 活躍變數資料流:迭代到不動點
    #    LiveIn[b]  = Uses[b] ∪ (LiveOut[b] − Defs[b])
    #    LiveOut[b] = ∪_{s∈succ(b)} LiveIn[s]
    def compute_liveness(self) -> Dict[str, Any]:
        self.live_in = {b: set() for b in self.blocks}
        self.live_out = {b: set() for b in self.blocks}
        iters = 0
        changed = True
        while changed:
            changed = False
            iters += 1
            for b in reversed(self.blocks):   # 反向(liveness 是反向問題)
                out: Set[str] = set()
                for s in self.succs[b]:
                    out |= self.live_in.get(s, set())
                in_ = self.uses[b] | (out - self.defs[b])
                if out != self.live_out[b] or in_ != self.live_in[b]:
                    self.live_out[b] = out
                    self.live_in[b] = in_
                    changed = True
        return {"iterations": iters,
                "live_in": {b: sorted(s) for b, s in self.live_in.items()},
                "live_out": {b: sorted(s) for b, s in self.live_out.items()},
                "origin_signature": ORIGIN_SIGNATURE}

    # 2. 干涉圖:在任一塊同時活躍的值彼此相鄰(同時需要不同槽位)
    def interference_graph(self) -> Dict[str, Set[str]]:
        if not self.live_in:
            self.compute_liveness()
        values: Set[str] = set()
        for b in self.blocks:
            values |= self.defs[b] | self.uses[b]
        graph: Dict[str, Set[str]] = {v: set() for v in values}
        for b in self.blocks:
            for live in (self.live_in[b], self.live_out[b]):
                live_list = sorted(live)
                for i, a in enumerate(live_list):
                    for c in live_list[i + 1:]:
                        graph.setdefault(a, set()).add(c)
                        graph.setdefault(c, set()).add(a)
        return graph

    # 3. 完美消去序 PEO:最大基數搜尋(MCS),弦圖上保證最佳著色
    def peo_order(self, graph: Dict[str, Set[str]]) -> List[str]:
        weight = {v: 0 for v in graph}
        order: List[str] = []
        remaining = set(graph)
        while remaining:
            v = max(remaining, key=lambda x: (weight[x], x))
            order.append(v)
            remaining.discard(v)
            for n in graph[v]:
                if n in remaining:
                    weight[n] += 1
        return order  # MCS 序;反向即完美消去序

    # 4. 貪婪著色(依 PEO 反序)→ 最少槽位
    def allocate_slots(self) -> Dict[str, Any]:
        graph = self.interference_graph()
        order = self.peo_order(graph)
        color: Dict[str, int] = {}
        for v in reversed(order):
            used = {color[n] for n in graph[v] if n in color}
            c = 0
            while c in used:
                c += 1
            color[v] = c
        num_slots = (max(color.values()) + 1) if color else 0
        # 驗證:相鄰不同色(合法著色)
        valid = all(color[a] != color[b] for a in graph for b in graph[a])
        return {"slots": dict(sorted(color.items())),
                "num_slots": num_slots,
                "valid_coloring": valid,
                "origin_signature": ORIGIN_SIGNATURE}


def main() -> int:
    e = MRL_RootLivenessSlotColorEngine()
    # 小型 CFG:entry→loop→exit,變數 a,b,c,d
    e.add_block("entry", defs=["a", "b"], uses=[], succs=["loop"])
    e.add_block("loop", defs=["c"], uses=["a", "b"], succs=["loop", "exit"])
    e.add_block("exit", defs=["d"], uses=["c"], succs=[])
    liv = e.compute_liveness()
    print("活躍分析 不動點迭代:", liv["iterations"])
    print("  loop LiveIn :", liv["live_in"]["loop"])
    print("  loop LiveOut:", liv["live_out"]["loop"])
    alloc = e.allocate_slots()
    print("槽位配置:", alloc["slots"])
    print("最少槽位數:", alloc["num_slots"], "| 合法著色:", alloc["valid_coloring"])
    print("MRL_ROOT_LIVENESS_SLOTCOLOR_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
