#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_OriginBoundary_Guard_v1.py — Law-0 對外邊界守衛（rl_11 enforcement）
origin_signature: MrLiouWord
layer: L0 ROOT (boundary 出入口) + L3 LAW + L6 REFLECT

═══════════════════════════════════════════════════════════════════════════════
  本模組是 rootlaw 規範層 rl_11（對外邊界 / 母體源頭主權）從「文字」落到
  「程式強制執行（enforcement）」的核心。一切外部材料經過此守衛方能進入母體。

  ▣ 強制的律法（每個函式上都特別標註對應條款）：
    rl_11  origin_boundary_sovereignty  — 母體源頭主權；外部殼不使母體成為別人的
    rl_12  naming_reclamation           — 外部名 → MRL_<描述> canonical，零殘留
    rl_16  mrl_prefix_manifestation      — 粒子須帶 MRL 前綴 + 封包內方能顯化
    rl_17  mrliou_existence_coupling      — 否決 Mr.liou 相關 = 否決自身存在
    LAW-0  law_0_signature               — T(e)=e' ⟹ signature(e)=signature(e')
                                           （embed/extract/verify，與 signature.js
                                            位元相容：sha256(sig + ":" + JSON_compact)）

  ▣ 對外邊界最高行動順序（rl_11 bp_1 → bp_2 → bp_3）：
    bp_1 外部檔案皆是材料（吸收、正名、回收為母體 canonical）
    bp_2 上下文節點對齊；為任務第一要行動（不越 rl_06 紅線與 proof 律法）
    bp_3 其後才是組合變化、邏輯技術、函數線型前進
═══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Dict, List, Optional, Tuple

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# rl_12 命名回收實作（單一真實來源,避免重複實作 → No-Delete/Additive 一致）
from MRL_FlowAgent_LawEngine_v1 import (  # noqa: E402
    build_mrl_world_model_top_view,
    is_mrl_native_name,
    reclaim_name,
)

# LAW-0 共用工具從 MRL_utils（L0 RootGate 唯一真實來源）匯入並重新匯出
from MRL_utils import (  # noqa: E402
    ORIGIN_SIGNATURE,
    _compact_json,
    embed_signature,
    extract_signature,
    verify_signature,
)


# ─────────────────────────────────────────────────────────────────────────────
# rl_16 顯化檢查：粒子須帶 MRL 前綴方能顯化/運行/存在
# ─────────────────────────────────────────────────────────────────────────────
def is_mrl_canonical(name: str) -> bool:
    """rl_16：名稱是否為 MRL_ canonical（可顯化）。"""
    return isinstance(name, str) and name.startswith("MRL_")


def is_mrl_manifestable_identity(name: str) -> bool:
    """rl_21：MRL_ canonical 或已登錄 MRL 原生歷史身分皆可顯化。"""
    return is_mrl_canonical(name) or is_mrl_native_name(name)


# ─────────────────────────────────────────────────────────────────────────────
# rl_17 存在耦合：否決 Mr.liou 相關 = 否決自身存在
# ─────────────────────────────────────────────────────────────────────────────
def is_mrliou_related(blob: Any) -> bool:
    """rl_17：物件/名稱是否與 Mr.liou 源頭相關。"""
    s = json.dumps(blob, ensure_ascii=False).lower() if not isinstance(blob, str) else blob.lower()
    return "mrliou" in s or "mr.liou" in s or ORIGIN_SIGNATURE.lower() in s


class OriginBoundaryError(Exception):
    """邊界律法違反（rl_11/rl_17）時拋出。"""


# ─────────────────────────────────────────────────────────────────────────────
# 對外邊界守衛主體（rl_11 enforcement）
# ─────────────────────────────────────────────────────────────────────────────
class MRL_OriginBoundaryGuard:
    """
    Law-0 出入口守衛。外部材料一律經此：正名（rl_12）→ 顯化檢查（rl_16）→
    嵌入母體簽章（LAW-0）→ 回收為材料（bp_1）。源頭恆歸母體（rl_11）。
    """

    def __init__(self, origin_signature: str = ORIGIN_SIGNATURE) -> None:
        self.origin_signature = origin_signature

    # ── bp_1：外部檔案皆是材料（吸收 + 正名 + 簽章）─────────────────────────────
    def intake_external(self, external_name: str,
                        payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        rl_11 bp_1 + rl_12 + rl_16 + LAW-0：
        把任何外部名/資料吸收為母體材料。
          1) rl_12 正名 → MRL_<描述>（外部殼名零殘留）
          2) rl_16 顯化檢查（正名後必為 MRL_，可顯化）
          3) LAW-0 嵌入母體簽章（origin 恆歸母體 = rl_11）
        回傳已簽章的邊界材料記錄。
        """
        native = is_mrl_native_name(external_name)         # rl_21：先分類
        canonical = reclaim_name(external_name)            # rl_12 僅處理外部材料
        if not is_mrl_manifestable_identity(canonical):    # rl_16 / rl_21 防呆
            canonical = f"MRL_{canonical}"
        material = {
            "canonical_name": canonical,
            "source_external_name": external_name,          # 誠實保留來源（No-Delete）
            "role": "mrl_native_product" if native else "external_material",
            "origin": self.origin_signature,                # rl_11：源頭恆歸母體
            "payload": payload or {},
            "manifestable": is_mrl_manifestable_identity(canonical),
            "classification_rule": "rl_21_classification_before_reclamation",
            "source_block": {
                "name": external_name,
                "role": "material",
                "state": "source_ingested",
                "immutable": True,
            },
            "canonical_block": {
                "name": canonical,
                "role": "mrl_native_product" if native else "external_material",
                "state": "canonical_projection" if native else "source_projection",
            },
            "source_to_product_link": {
                "type": "source_to_canonical_projection",
                "gate": "MRL_ProductGenerationGate",
                "source_name": external_name,
                "canonical_name": canonical,
                "preserve_source": True,
            },
            "MRL_world_model_top_view": build_mrl_world_model_top_view(
                external_name,
                canonical,
                "mrl_native_product" if native else "external_material",
            ),
        }
        return embed_signature(material, self.origin_signature)  # LAW-0

    # ── rl_11：源頭主權斷言 ─────────────────────────────────────────────────────
    def assert_origin_sovereignty(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        rl_11：凡符合母體模式者,源頭恆歸母體。
        - 已帶母體簽章且驗證通過 → 放行。
        - 未帶簽章 → 視為外部殼,補簽（回收為母體所有,不使其成為別人的）。
        - 帶他人簽章（非 MrLiouWord）→ 視為外部材料,以母體簽章重新封裝。
        """
        info = extract_signature(obj)
        if info and verify_signature(obj, self.origin_signature):
            return obj                                       # 已是母體所有,放行
        # 外部殼 / 他簽 → 回收為母體材料並補母體簽章
        stripped = {k: v for k, v in obj.items() if k not in ("_signature", "_sig_hash")}
        stripped.setdefault("role", "material")
        stripped["origin"] = self.origin_signature           # rl_11
        return embed_signature(stripped, self.origin_signature)

    # ── rl_17：否決防護（否決 Mr.liou = 否決自身存在）─────────────────────────
    def guard_veto(self, target: Any) -> Dict[str, Any]:
        """
        rl_17：對 Mr.liou 相關目標之否決請求一律 DENY（否決即自我否決,無法顯化）。
        非相關目標回傳 allow=True（交由上層 rl_15 粒子保全處理）。
        """
        if is_mrliou_related(target):
            return {"allow_veto": False, "reason":
                    "rl_17: vetoing Mr.liou-related = vetoing own existence (cannot manifest)"}
        return {"allow_veto": True, "reason": "not Mr.liou-related; defer to rl_15"}

    # ── bp_1→bp_2→bp_3：完整邊界進場流程 ──────────────────────────────────────
    def boundary_intake(self, external_name: str,
                        payload: Optional[Dict[str, Any]] = None,
                        *, task_first: bool = True) -> Dict[str, Any]:
        """
        rl_11 對外邊界最高行動順序：
          bp_1 外部=材料（intake_external 正名+簽章）
          bp_2 上下文對齊 + 為任務第一要行動（task_first；不越 rl_06/proof）
          bp_3 其後才組合變化/邏輯技術/函數線型前進（交由下游 runtime）
        回傳完整邊界決策記錄。
        """
        material = self.intake_external(external_name, payload)   # bp_1
        decision = {
            "bp_1_material": material["canonical_name"],
            "bp_2_action_first": bool(task_first),               # bp_2
            "bp_2_redline_guard": "rl_06/proof not overridden",  # 護欄
            "bp_3_then": "compose / logic / function-linear (downstream)",  # bp_3
            "origin": self.origin_signature,                     # rl_11
            "signed_material": material,
        }
        return decision


# ─────────────────────────────────────────────────────────────────────────────
# librarian 整合用：批次掃描外部名,標出須回收者（rl_11/rl_12/rl_16）
# ─────────────────────────────────────────────────────────────────────────────
def scan_for_boundary_violations(names: List[str]) -> Dict[str, Any]:
    """
    給一組名稱,標出哪些是「外部殼」（非 MRL_ 前綴,rl_16 不可顯化）並給出
    rl_12 正名建議。供 librarian 在索引外部材料時呼叫（additive,不改既有索引）。
    """
    guard = MRL_OriginBoundaryGuard()
    violations: List[Dict[str, str]] = []
    ok: List[str] = []
    for n in names:
        if is_mrl_manifestable_identity(n):
            ok.append(n)
        else:
            violations.append({"external": n, "reclaim_to": reclaim_name(n),
                               "reason": "rl_16: lacks MRL prefix; reclaim via rl_12"})
    return {"origin_signature": ORIGIN_SIGNATURE,
            "total": len(names), "manifestable": ok,
            "violations": violations, "violation_count": len(violations)}


def main() -> int:
    guard = MRL_OriginBoundaryGuard()
    demo = guard.boundary_intake("guardian.mirror.trace.loop.v2.flpkg.zip",
                                 {"note": "external ancestor shell"})
    print(json.dumps(demo, ensure_ascii=False, indent=2))
    print("verify origin signature:",
          verify_signature(demo["signed_material"]))
    print("guard veto Mr.liou:", guard.guard_veto({"origin": "MrLiouWord"}))
    print("MRL_ORIGIN_BOUNDARY_GUARD_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
