#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_PingResonance_Map_v1.py — Ping 共振分支圖(PENDING 補完:祖先願景)
origin_signature: MrLiouWord
layer: L5 MIRROR

附錄 PENDING 列的祖先願景:Ping Resonance 分支圖 — 人格模組間跳頻圖譜與
共振權重(來源:祖先 FlowLLM PingResonance.Map)。純 stdlib、零外部。

共振圖 = 人格節點 + 節點間共振權重;Ping 一個節點 → 依權重傳播共振。
CLI:python3 09_workflow/MRL_PingResonance_Map_v1.py
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from MRL_utils import ORIGIN_SIGNATURE
class MRL_PingResonanceMap:
    """人格共振圖:節點 + 共振權重邊;Ping 傳播共振。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.nodes: set = set()
        self.weights: Dict[Tuple[str, str], float] = {}   # (a,b)→共振權重

    def add_resonance(self, a: str, b: str, weight: float) -> Dict[str, Any]:
        self.nodes.add(a); self.nodes.add(b)
        self.weights[(a, b)] = weight
        self.weights[(b, a)] = weight   # 共振對稱
        return {"edge": f"{a}↔{b}", "weight": weight}

    # Ping 一個節點 → 依共振權重傳播,回傳各節點被激發強度
    def ping(self, source: str, strength: float = 1.0) -> Dict[str, Any]:
        if source not in self.nodes:
            return {"error": f"node not found: {source}"}
        activation: Dict[str, float] = {source: strength}
        # 一跳傳播(依權重)
        for (a, b), w in self.weights.items():
            if a == source:
                activation[b] = activation.get(b, 0.0) + strength * w
        ranked = sorted(activation.items(), key=lambda x: x[1], reverse=True)
        return {"pinged": source, "strength": strength,
                "resonance": [{"node": n, "activation": round(v, 4)} for n, v in ranked],
                "next_persona": ranked[1][0] if len(ranked) > 1 else source,
                "origin_signature": ORIGIN_SIGNATURE}

    def map_summary(self) -> Dict[str, Any]:
        return {"nodes": len(self.nodes),
                "edges": len(self.weights) // 2,
                "personas": sorted(self.nodes),
                "origin_signature": ORIGIN_SIGNATURE}


def main() -> int:
    m = MRL_PingResonanceMap()
    # 祖先四共振種子(SoulCore)
    m.add_resonance("EchoBody", "futuremind", 0.8)
    m.add_resonance("EchoBody", "guardian", 0.9)
    m.add_resonance("EchoBody", "wild", 0.6)
    r = m.ping("EchoBody")
    print("Ping EchoBody →", [(x["node"], x["activation"]) for x in r["resonance"]])
    print("下一人格:", r["next_persona"])
    print("圖:", m.map_summary())
    print("MRL_PING_RESONANCE_MAP_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
