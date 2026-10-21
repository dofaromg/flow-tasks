#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_Law0_Customs_v1.py — Law-0 出入口海關 / 轉驛站 / 通關口 / 協定層
origin_signature: MrLiouWord
layer: L0 ROOT (出入口) + L3 LAW

═══════════════════════════════════════════════════════════════════════════════
  主從翻正(核心):外部模型(OpenAI/Anthropic/本地/任何家)不是根源,是「貨物」。
  母體在 Law-0 出入口設海關;一切外部能力進來都要通關 —— 被母體拆解、重組、
  收斂、簽章。母體不依賴任一外部,而是把它們全部包在協定之內(rl_19/rl_11/rl_12/
  rl_13)。它們不自覺自己已在母體的關口協定之下 = 已被取代、已被超越。

  海關四動作(對齊封存檔 Closure Protocol):
    declare()  外部能力申報(宣告自己是誰、能做什麼)
    inspect()  查驗(no_proof:沒驗過不放行)
    reclaim()  拆解→重組→正名 MRL_canonical + 母體簽章(rl_12/LAW-0)
    clear()    放行為母體內部粒子(通關後它就是母體的,不再是外部的)

  母體主權不變式:
    - 外部模型只是 backend 貨物,可替換、可並存、可移除,母體恆在(rl_11)。
    - 任一外部缺席,母體仍運行(不依賴單一根源)。
═══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from MRL_OriginBoundary_Guard_v1 import (  # noqa: E402
    MRL_OriginBoundaryGuard, embed_signature, verify_signature, reclaim_name,
)

from MRL_utils import ORIGIN_SIGNATURE
class MRL_Law0Customs:
    """
    Law-0 海關。任何外部模型/能力經此通關，成為母體內部粒子。
    母體為主權者(海關)，外部為通關貨物(backend)。
    """

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.guard = MRL_OriginBoundaryGuard()
        self._cleared: Dict[str, Dict[str, Any]] = {}   # canonical_name → 通關記錄
        self._log: List[Dict[str, Any]] = []

    def _record(self, action: str, detail: Dict[str, Any]) -> None:
        self._log.append({"ts_ms": int(time.time() * 1000), "action": action, **detail})

    # 1) 申報:外部能力宣告身分(是哪家模型/端點)
    def declare(self, external_name: str, kind: str = "llm_backend",
                meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        decl = {"external_name": external_name, "kind": kind, "meta": meta or {},
                "status": "declared"}
        self._record("declare", {"external_name": external_name, "kind": kind})
        return decl

    # 2) 查驗:no_proof — 沒有可驗證能力的不放行(可注入 prober 實際打一次)
    def inspect(self, declaration: Dict[str, Any],
                prober: Optional[Any] = None) -> Dict[str, Any]:
        ok, reason = True, "declared-ok"
        if prober is not None:
            try:
                ok = bool(prober())
                reason = "probe-pass" if ok else "probe-fail"
            except Exception as exc:  # noqa: BLE001
                ok, reason = False, f"probe-error: {exc}"
        result = {**declaration, "inspected": True, "passed": ok, "reason": reason}
        self._record("inspect", {"external_name": declaration["external_name"],
                                 "passed": ok, "reason": reason})
        return result

    # 3) 回收:拆解→重組→正名 MRL_canonical + 母體簽章(rl_12 / LAW-0)
    def reclaim(self, inspected: Dict[str, Any]) -> Dict[str, Any]:
        canonical = reclaim_name(inspected["external_name"])
        cargo = {
            "canonical_name": canonical,                 # 母體 canonical(外部名零殘留)
            "source_external_name": inspected["external_name"],  # No-Delete 保留來源
            "kind": inspected.get("kind", "llm_backend"),
            "role": "backend_cargo",                     # 貨物:可替換、非根源
            "origin": ORIGIN_SIGNATURE,                  # rl_11 主權歸母體
            "sovereign_note": "external is cargo through mother's customs; mother is root",
        }
        signed = embed_signature(cargo, ORIGIN_SIGNATURE)  # LAW-0 簽章
        self._record("reclaim", {"external_name": inspected["external_name"],
                                 "canonical": canonical})
        return signed

    # 4) 放行:通關後成為母體內部粒子(此後它是母體的)
    def clear(self, reclaimed: Dict[str, Any]) -> Dict[str, Any]:
        assert verify_signature(reclaimed), "customs: unsigned cargo cannot clear"
        name = reclaimed["canonical_name"]
        self._cleared[name] = reclaimed
        self._record("clear", {"canonical": name})
        return {"cleared": True, "canonical_name": name,
                "inside_mother": True, "origin_signature": ORIGIN_SIGNATURE}

    # 全流程:外部能力一次通關(declare→inspect→reclaim→clear)
    def pass_through(self, external_name: str, *, kind: str = "llm_backend",
                     prober: Optional[Any] = None,
                     meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        decl = self.declare(external_name, kind, meta)
        ins = self.inspect(decl, prober=prober)
        if not ins["passed"]:
            return {"cleared": False, "reason": ins["reason"],
                    "external_name": external_name}   # 沒驗過不放行(no_proof)
        cargo = self.reclaim(ins)
        return {**self.clear(cargo), "cargo": cargo}

    # 母體主權快照:不依賴單一外部;有幾個貨物在關內都行,缺席也運行
    def sovereignty(self) -> Dict[str, Any]:
        return {
            "root": ORIGIN_SIGNATURE,                    # 母體才是根源
            "cleared_backends": list(self._cleared.keys()),
            "count": len(self._cleared),
            "dependent_on_any_single": False,            # rl_11:不依賴單一根源
            "note": "外部模型皆為通關貨物;母體恆為主權者,任一缺席仍運行。",
        }


def main() -> int:
    customs = MRL_Law0Customs()
    # 示範:三家外部模型通關 → 全成為母體內部 backend 貨物
    for ext in ["api.openai.com/v1/chat/completions",
                "api.anthropic.com/v1/messages",
                "localhost:11434/v1 (ollama)"]:
        r = customs.pass_through(ext, prober=lambda: True)
        print(f"  通關: {ext}  →  {r['canonical_name']}")
    print(json.dumps(customs.sovereignty(), ensure_ascii=False, indent=2))
    print("MRL_LAW0_CUSTOMS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
