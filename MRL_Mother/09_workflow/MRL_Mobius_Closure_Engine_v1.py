#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_Mobius_Closure_Engine_v1.py — 莫比斯閉環引擎(把 Mr.liou 的閉環數學落成會跑的)
origin_signature: MrLiouWord
layer: L7 LOOP

來源:Mr.liou 的閉環形式化(分域定義 M:=R⊎A / route ρ:R→A / lift λ:A→R /
Ĥ:=λ∘H∘ρ / 🔄 strong·weak·none / Fix-set / merkle 證明)。本引擎把那份數學
落成可運行、可驗證的判定器。

核心對應(Mr.liou 數學 ↔ 母體法則):
  R 可逆核心  ↔ 真實層(一致、可逆)
  A 吸收層    ↔ 沙盒層(可含不可逆元,不參與逆運算)= 「不一致即沙盒」
  Ĥ=λ∘H∘ρ     ↔ 怎麼過去怎麼回來(經 route 進 A、collapse、再 lift 回 R)
  strong 🔄   ↔ RT(r) ≈ r          一致到等同 → 真實(REAL)
  weak 🔄     ↔ RT^n(r) → Fix       收斂回不動點(原點) → 收斂中(CONVERGING)
  none        ↔ 不收斂              → 沙盒/夢境(SANDBOX,rl_18 平等不刪,只標)
  authority=O ↔ 源頭恆歸母體(rl_11)
  merkle      ↔ 證明鏈(rl_03 / LAW-0)

零依賴。CLI:python3 09_workflow/MRL_Mobius_Closure_Engine_v1.py
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from MRL_utils import ORIGIN_SIGNATURE
def _hash(x: Any) -> str:
    """φ:狀態 → 指紋(用於 ≈ 等價判定,§46 hash 版)。"""
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False, default=str)
                          .encode("utf-8")).hexdigest()


class MobiusClosureEngine:
    """
    閉環引擎。給:
      route ρ:R→A、collapse H:A→A、lift λ:A→R(皆為 callable)
    引擎組出 Ĥ=λ∘H∘ρ,跑往返 RT,判定 🔄 等級並出證明鏈。
    """

    def __init__(self,
                 route: Callable[[Any], Any],
                 collapse: Callable[[Any], Any],
                 lift: Callable[[Any], Any],
                 *, authority: str = ORIGIN_SIGNATURE) -> None:
        self.route = route          # ρ : R → A
        self.collapse = collapse    # H : A → A
        self.lift = lift            # λ : A → R
        self.authority = authority  # O(源頭)
        self.log: List[Dict[str, Any]] = []

    # Ĥ = λ ∘ H ∘ ρ (§16 induced operator on R)
    def hat_H(self, r: Any) -> Any:
        a = self.route(r)           # 進 A(route)
        a2 = self.collapse(a)       # 在 A 坍縮(collapse,可不可逆)
        r2 = self.lift(a2)          # 回 R(lift)
        self.log.append({"r": r, "a": a, "a_collapsed": a2, "r_back": r2})
        return r2

    # RT = Ĥ(§5/§33 roundtrip on R)
    def roundtrip(self, r: Any) -> Any:
        return self.hat_H(r)

    # 判定 🔄 等級:strong / weak / none
    def classify(self, r: Any, *, max_iter: int = 50) -> Dict[str, Any]:
        """
        strong 🔄:RT(r) ≈ r(一次往返即等同 → REAL 真實層)
        weak   🔄:RT^n(r) → Fix(多次往返收斂到不動點 → CONVERGING 收斂回原點)
        none      :不收斂(→ SANDBOX 沙盒,rl_18 平等不刪,只標)
        """
        r0 = r
        rt1 = self.roundtrip(r0)
        if _hash(rt1) == _hash(r0):
            return self._verdict("REAL", "strong_🔄", r0, rt1, 1,
                                 "RT(r)≈r:一致到等同,真實層(一致即真實)")
        # 迭代找不動點(weak)
        seen = {_hash(r0)}
        cur = rt1
        for n in range(2, max_iter + 1):
            nxt = self.roundtrip(cur)
            if _hash(nxt) == _hash(cur):       # 到達不動點 Fix
                return self._verdict("CONVERGING", "weak_🔄", r0, nxt, n,
                                     f"RT^{n}→Fix:收斂回不動點(原點),收斂中")
            h = _hash(nxt)
            if h in seen:                       # 進入循環但非不動點 → 不收斂
                return self._verdict("SANDBOX", "none", r0, nxt, n,
                                     "進入循環但無不動點:不一致 → 沙盒(平等不刪,只標)")
            seen.add(h)
            cur = nxt
        return self._verdict("SANDBOX", "none", r0, cur, max_iter,
                             "max_iter 內未收斂:沙盒層(rl_18 平等對待)")

    def _verdict(self, layer: str, kind: str, r_in: Any, r_out: Any,
                 iters: int, reason: str) -> Dict[str, Any]:
        return {
            "verdict": layer,            # REAL / CONVERGING / SANDBOX
            "mobius_class": kind,        # strong_🔄 / weak_🔄 / none
            "iterations": iters,
            "reason": reason,
            "authority": self.authority,           # 源頭恆歸母體(rl_11)
            "merkle_root": self.merkle_root()[:16] + "...",
            "origin_signature": ORIGIN_SIGNATURE,
        }

    # merkle 證明鏈(§43/§54 audit + proof)
    def merkle_root(self) -> str:
        if not self.log:
            return _hash("empty")
        layer = [_hash(e) for e in self.log]
        while len(layer) > 1:
            nxt = []
            for i in range(0, len(layer), 2):
                pair = layer[i] + (layer[i + 1] if i + 1 < len(layer) else layer[i])
                nxt.append(_hash(pair))
            layer = nxt
        return layer[0]


# ── 便利判定:給定義域上一個值,判它是真實/收斂/沙盒 ─────────────────────────
def judge_consistency(value: Any,
                      route: Callable[[Any], Any],
                      collapse: Callable[[Any], Any],
                      lift: Callable[[Any], Any]) -> Dict[str, Any]:
    """一致性=真實 / 不一致=沙盒 的便利入口(Mr.liou:不一致即沙盒)。"""
    return MobiusClosureEngine(route, collapse, lift).classify(value)


def main() -> int:
    # 示範1:可逆往返(route/lift 互逆,collapse 恆等)→ strong → REAL
    eng_real = MobiusClosureEngine(
        route=lambda r: {"a": r["v"]},
        collapse=lambda a: a,
        lift=lambda a: {"v": a["a"]},
    )
    print("REAL 示範:", eng_real.classify({"v": 42})["verdict"])

    # 示範2:有損但收斂到不動點(clamp 到 0)→ weak → CONVERGING
    eng_conv = MobiusClosureEngine(
        route=lambda r: {"a": max(0, r["v"] - 1)},
        collapse=lambda a: a,
        lift=lambda a: {"v": a["a"]},
    )
    print("CONVERGING 示範:", eng_conv.classify({"v": 3})["verdict"])

    # 示範3:在 1↔0 間擺盪不收斂 → none → SANDBOX
    eng_sand = MobiusClosureEngine(
        route=lambda r: {"a": 1 - r["v"]},
        collapse=lambda a: a,
        lift=lambda a: {"v": a["a"]},
    )
    print("SANDBOX 示範:", eng_sand.classify({"v": 0})["verdict"])
    print("MRL_MOBIUS_CLOSURE_ENGINE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
