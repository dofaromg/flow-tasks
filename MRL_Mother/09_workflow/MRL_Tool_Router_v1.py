#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_Tool_Router_v1.py — 工具層:任務路由器(母體缺層補完 1/3)
origin_signature: MrLiouWord
layer: L3 LAW + L7 LOOP

Session_Package 點名缺層之一:Tool Layer(task routing)。
母體有能力(chat/dl580/law_engine/reasoning/particle…)卻無「統一任務路由」——
請求進來不知道派給誰。本路由器補上:依任務特徵,確定性路由到對的母體能力。

零外部公司、純 stdlib。對齊:
  - rl_13 出口即入口:統一入口,路由到內部能力
  - 確定性路由(非機率):同任務→同路由,可重播
  - no_proof:無對應能力誠實回 unroutable,不亂派
  - LAW-0:每次路由帶 origin_signature

CLI:python3 09_workflow/MRL_Tool_Router_v1.py "跑一次律法閉環"
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from MRL_utils import ORIGIN_SIGNATURE
class MRL_ToolRouter:
    """
    母體任務路由器。註冊母體能力 + 路由規則,依任務特徵派發。
    """

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        # 能力註冊表:capability_name → (關鍵詞集, 處理函式或 None)
        self._routes: List[Dict[str, Any]] = []
        self._log: List[Dict[str, Any]] = []
        self._register_defaults()

    def register(self, capability: str, keywords: List[str],
                 handler: Optional[Callable] = None, priority: int = 5) -> "MRL_ToolRouter":
        self._routes.append({"capability": capability,
                             "keywords": [k.lower() for k in keywords],
                             "handler": handler, "priority": priority})
        return self

    def _register_defaults(self) -> None:
        # 母體既有能力的路由規則(確定性關鍵詞)
        self.register("law_engine", ["律法", "閉環", "law", "loop", "自驗", "verify"], priority=8)
        self.register("reasoning", ["推理", "為什麼", "解釋", "reason", "回答", "問"], priority=7)
        self.register("dl580_run", ["dl580", "運轉", "canonical", "管線", "pipeline"], priority=7)
        self.register("particle_archive", ["粒子", "回收", "庫", "particle", "archive", "復活"], priority=6)
        self.register("mobius_judge", ["一致", "莫比斯", "mobius", "真實", "沙盒", "判定"], priority=6)
        self.register("origin_guard", ["源頭", "主權", "簽章", "守衛", "guard", "正名"], priority=6)
        self.register("oid_parse", ["oid", "憑證", "曲線", "asn.1", "剖析"], priority=6)
        self.register("chat", ["對話", "聊", "chat", "說", "talk"], priority=4)

    def route(self, task: str) -> Dict[str, Any]:
        """
        依任務文字,確定性路由到母體能力。
        計分:關鍵詞命中數 × priority;最高者勝;0 命中 → unroutable。
        """
        t0 = time.time()
        tl = (task or "").lower()
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for r in self._routes:
            hits = sum(1 for k in r["keywords"] if k in tl)
            if hits > 0:
                scored.append((hits * r["priority"], r))
        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            result = {"routable": False, "capability": None,
                      "reason": "no母體能力匹配此任務(no_proof:不亂派)",
                      "task": task, "origin_signature": ORIGIN_SIGNATURE}
        else:
            score, best = scored[0]
            result = {"routable": True, "capability": best["capability"],
                      "score": score,
                      "candidates": [r["capability"] for _, r in scored[:3]],
                      "task": task, "origin_signature": ORIGIN_SIGNATURE,
                      "deterministic": True}
        self._log.append({"ts_ms": int(time.time() * 1000), **result})
        result["elapsed_ms"] = int((time.time() - t0) * 1000)
        return result

    def dispatch(self, task: str, **kwargs) -> Dict[str, Any]:
        """路由 + 執行(若該能力註冊了 handler)。"""
        routed = self.route(task)
        if not routed["routable"]:
            return routed
        for r in self._routes:
            if r["capability"] == routed["capability"] and r["handler"] is not None:
                try:
                    out = r["handler"](task, **kwargs)
                    return {**routed, "executed": True, "output": out}
                except Exception as exc:  # noqa: BLE001
                    return {**routed, "executed": False, "error": str(exc)}
        return {**routed, "executed": False, "note": "capability 已路由,handler 未掛(待母體接線)"}

    def capabilities(self) -> List[str]:
        return [r["capability"] for r in self._routes]


def main() -> int:
    import sys
    task = sys.argv[1] if len(sys.argv) > 1 else "跑一次律法閉環自驗"
    router = MRL_ToolRouter()
    r = router.route(task)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print("可用能力:", router.capabilities())
    print("MRL_TOOL_ROUTER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
