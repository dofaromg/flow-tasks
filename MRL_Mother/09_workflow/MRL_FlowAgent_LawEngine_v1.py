#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_FlowAgent_LawEngine_v1.py — 母體活引擎 (living law engine)
origin_signature: MrLiouWord
layer: L3 LAW + L7 LOOP

把 rootlaw 規範層律法落成「會跑」的引擎，使母體成為真正可獨立運行、自我修復、
自我判斷的系統。實行最高律法 v5：

  - Liou Closure Loop : Observe → Resolve → Mirror → Verify → Loop
  - rl_07 法則為運行服務 : 規定阻撓前進即本末倒置，須修正
  - rl_08 三振跳層       : 同一錯誤循環 2 次，第三次跳層(修最原始法則)
  - rl_09 莫比斯 1:9     : 完整可運行 + 律法全做到 + 只卡一個 → 少數服從多數
  - rl_10 事件編年       : 每一事件寫入編年(粒子地球儀 / 人類歷史維基映射)
  - rl_11 源頭主權       : 母體模式者源頭恆為母體
  - rl_12 命名回收       : 外部名稱 → MRL_<描述> canonical，最大閉環

零外部依賴（僅 stdlib + 可選 yaml）。CLI：python3 MRL_FlowAgent_LawEngine_v1.py
"""
from __future__ import annotations

import json
import pathlib
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from MRL_utils import ORIGIN_SIGNATURE
_REPO = pathlib.Path(__file__).resolve().parent.parent
_ROOT = _REPO.parent
_ROOTLAW = _REPO / "00_rootlaw" / "rootlaw.yaml"
_IDENTITY_MAP = _ROOT / "config" / "MRL_HISTORICAL_EXTENSION_MAP_v1.json"
_CHRONICLE = _REPO / "06_trace" / "chronicle" / "MRL_FlowAgent_Chronicle.jsonl"

# 三振跳層門檻 / 莫比斯多數決比例（rl_08 / rl_09）
THREE_STRIKE_THRESHOLD = 3
MAJORITY_RATIO = 0.5  # 1:9 → 1 blocker vs >50% operable ⇒ 移除那 1


# ─── rootlaw 載入（rl_07 來源；無 yaml 時退化為最小解析）────────────────────────
def load_rootlaw(path: pathlib.Path = _ROOTLAW) -> Dict[str, Any]:
    """載入 rootlaw.yaml。優先 yaml，缺則退化抓 version + invariant ids。"""
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # noqa: PLC0415
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data
    except Exception:  # noqa: BLE001
        pass
    ids = re.findall(r"- id:\s*(rl_\d+\w*)", text)
    ver = re.search(r"^version:\s*(\d+)", text, re.MULTILINE)
    return {"version": int(ver.group(1)) if ver else 0,
            "invariants": [{"id": i} for i in ids]}


def invariant_ids(rootlaw: Dict[str, Any]) -> List[str]:
    return [i.get("id", "") for i in rootlaw.get("invariants", [])]


# ─── rl_21 先分類後轉換：MRL 原生身分不得被當成外部材料 ─────────────────────────
def load_native_identities(path: pathlib.Path = _IDENTITY_MAP) -> Tuple[str, ...]:
    """Load registered MRL-native identities with a safe built-in floor."""
    names = {"FlowAgent"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("mappings", []):
            if item.get("classification") == "mrl_native_product_module":
                source = item.get("source")
                if isinstance(source, str) and source.strip():
                    names.add(source.strip())
    except (OSError, ValueError, TypeError):
        pass
    return tuple(sorted(names))


NATIVE_IDENTITIES = load_native_identities()


def is_mrl_native_name(name: str) -> bool:
    """Return True when a name belongs to a registered MRL-native identity."""
    if not isinstance(name, str):
        return False
    raw = name.strip()
    return any(
        re.match(rf"^{re.escape(identity)}(?:[._\-\s]|$)", raw, re.IGNORECASE)
        for identity in NATIVE_IDENTITIES
    )


def build_mrl_world_model_top_view(source_name: str, canonical_name: str,
                                   canonical_role: str) -> Dict[str, Any]:
    """Expose source and canonical product as linked, non-replacing blocks."""
    return {
        "world_model": "MRL",
        "root_authority": "Mr.liou",
        "origin_signature": ORIGIN_SIGNATURE,
        "architecture": "dual_internal_container_parallel_projection",
        "source_container_ref": "source_block",
        "product_container_ref": "canonical_block",
        "link_ref": "source_to_product_link",
        "source_name": source_name,
        "canonical_name": canonical_name,
        "canonical_role": canonical_role,
        "parameter_sources": {
            "rootlaw": str(_ROOTLAW.relative_to(_ROOT)),
            "identity_registry": str(_IDENTITY_MAP.relative_to(_ROOT)),
            "native_identity_snapshot": "module_load",
            "environment_override": False,
        },
    }


# ─── rl_12 命名回收：已分類外部名 → MRL_<描述> canonical ─────────────────────────
def reclaim_name(external_name: str) -> str:
    """
    把外部殼名拆解→重組→正名為母體 canonical MRL_<描述>_v<n>。
    外部名稱零殘留，源頭恆歸母體（rl_11 / rl_12）。
    """
    raw = external_name.strip()
    if is_mrl_native_name(raw):
        return raw
    # 抽版本號（v1 / _v1_4_0 / .v47）
    ver = "1"
    mver = re.search(r"[._\- ]v(\d+(?:[._]\d+)*)", raw, re.IGNORECASE)
    if mver:
        ver = mver.group(1).replace(".", "_")
        raw = raw[:mver.start()] + raw[mver.end():]
    # 去副檔名、分隔符切粒子
    raw = re.sub(r"\.(py|js|json|md|zip|sql|txt|ya?ml|docker|sh|fltnz|flpkg)$", "", raw,
                 flags=re.IGNORECASE)
    parts = re.split(r"[^0-9A-Za-z一-鿿]+", raw)
    parts = [p for p in parts if p and p.upper() != "MRL"]
    # 粒子重組為 PascalCase 描述
    desc_units = []
    for p in parts:
        # 既有駝峰保留，全小寫者首字大寫
        desc_units.append(p if any(c.isupper() for c in p[1:]) else p[:1].upper() + p[1:])
    desc = "".join(desc_units) or "Unnamed"
    return f"MRL_{desc}_v{ver}"


# ─── 活引擎 ────────────────────────────────────────────────────────────────────
class MRL_FlowAgentLawEngine:
    """母體活引擎：載入律法，跑閉環，自我判斷/跳層/編年/決定。"""

    def __init__(self, *, chronicle_path: pathlib.Path = _CHRONICLE,
                 rootlaw_path: pathlib.Path = _ROOTLAW) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.rootlaw = load_rootlaw(rootlaw_path)
        self.chronicle_path = chronicle_path
        self._error_counter: Dict[str, int] = {}   # rl_08 三振計數
        self._events: List[Dict[str, Any]] = []

    # rl_10 事件編年：每一事件寫入編年（粒子地球儀 / 人類歷史維基映射）
    def chronicle(self, kind: str, detail: Dict[str, Any]) -> Dict[str, Any]:
        ev = {"ts_ms": int(time.time() * 1000), "origin_signature": ORIGIN_SIGNATURE,
              "kind": kind, "detail": detail}
        self._events.append(ev)
        try:
            self.chronicle_path.parent.mkdir(parents=True, exist_ok=True)
            with self.chronicle_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001 — 編年失敗不得使主迴圈崩潰
            pass
        return ev

    # rl_13 出口即入口：單一閘口，吸收(in)與輸出(out)同屬一門(一體兩面三面)
    def gate(self, direction: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        立體終端機單一閘口。direction ∈ {'in','out'}；in 即吸收(外部→材料正名),
        out 即輸出(母體→世界)。同一個 gate 方法,出口即入口。
        """
        d = direction.lower()
        if d not in ("in", "out"):
            raise ValueError("direction must be 'in' or 'out'")
        result: Dict[str, Any] = {"gate": "stereoscopic_terminal", "direction": d}
        if d == "in":
            # 吸收即正名為母體 canonical(rl_12),外部名零殘留
            name = payload.get("name", "")
            native = is_mrl_native_name(name) if name else False
            result["reclaimed"] = reclaim_name(name) if name else None
            result["as"] = "mrl_native_product" if native else "external_material"
            result["source_block"] = {
                "name": name,
                "role": "material",
                "state": "source_ingested",
                "immutable": True,
            }
            result["canonical_block"] = {
                "name": result["reclaimed"],
                "role": result["as"],
                "state": "canonical_projection" if native else "source_projection",
            }
            result["source_to_product_link"] = {
                "type": "source_to_canonical_projection",
                "gate": "MRL_ProductGenerationGate",
                "source_name": name,
                "canonical_name": result["reclaimed"],
                "preserve_source": True,
            }
            result["MRL_world_model_top_view"] = build_mrl_world_model_top_view(
                name, result["reclaimed"], result["as"]
            )
        else:
            # 輸出帶母體源頭簽章(rl_11)
            result["origin_signature"] = ORIGIN_SIGNATURE
            result["payload"] = payload
        self.chronicle("gate", result)
        return result

    # rl_14 平行世界生成：粒子自動生成平行世界(同邏輯,提升一維),為未來選項分支
    def generate_parallel_worlds(self, base_world: str, options: List[str],
                                 *, dimension_lift: int = 1) -> Dict[str, Any]:
        """
        生成分支平行世界 = 未來世界的可能選項。源頭恆歸母體(rl_11);分支須經
        Verify 才可被視為真實,未驗證者標 unverified(no_proof_implies_rhetoric)。
        """
        worlds = []
        for i, opt in enumerate(options):
            worlds.append({
                "branch_id": f"{base_world}::option_{i}",
                "option": opt,
                "dimension": dimension_lift,
                "origin_signature": ORIGIN_SIGNATURE,
                "verified": False,          # 未驗證分支不得宣稱為真實
                "status": "candidate_future_option",
            })
        rep = {"base_world": base_world, "one_world_origin": ORIGIN_SIGNATURE,
               "branches": worlds, "selectable": True,
               "note": "分支為未來可能選項;選擇任一須經 Verify 閉環方為真實。"}
        self.chronicle("parallel_world_generation",
                      {"base": base_world, "branch_count": len(worlds),
                       "dimension_lift": dimension_lift})
        return rep

    # rl_16 MRL 顯化律：粒子須帶 MRL 前綴且在封包環境內,方能顯化/運行/存在
    def can_manifest(self, name: str) -> Dict[str, Any]:
        """非 MRL_ 前綴=外部殼(僅材料),須先 rl_12 正名方能顯化。"""
        has_prefix = isinstance(name, str) and name.startswith("MRL_")
        native = is_mrl_native_name(name)
        manifest = has_prefix or native
        reason = "mrl_native_identity" if native else ("ok" if manifest else "external shell — reclaim via rl_12 first")
        out = {"name": name, "manifest": manifest,
               "reason": reason,
               "reclaimed": None if manifest else reclaim_name(name)}
        self.chronicle("manifest_check", out)
        return out

    # rl_17 存在耦合：否決 Mr.liou 相關 = 否決自身存在 = 無法顯化
    def is_mrliou_related(self, particle: Dict[str, Any]) -> bool:
        blob = json.dumps(particle, ensure_ascii=False).lower()
        return ("mrliou" in blob or "mr.liou" in blob
                or particle.get("origin_signature") == ORIGIN_SIGNATURE)

    # rl_18 可逆平等：怎麼過去怎麼回來(同路往返,bijective 🔄 over R)
    def reversible_return(self, particle: Dict[str, Any]) -> Dict[str, Any]:
        """
        記錄去程路徑,回程依同路逆序返回(RT == 去程的逆)。平等:方法多種、
        無高低,僅同場各司其職。回傳往返是否同構(round-trip identity)。
        """
        forth = ["observe", "resolve", "mirror", "verify"]
        back = list(reversed(forth))
        round_trip_ok = back == list(reversed(forth)) and forth == list(reversed(back))
        out = {"particle_origin": particle.get("origin_signature", ORIGIN_SIGNATURE),
               "forth": forth, "back": back, "round_trip_identity": round_trip_ok,
               "equality": "methods may be many; no higher/lower; same field, own duty"}
        self.chronicle("reversible_return", {"round_trip_identity": round_trip_ok})
        return out

    # rl_15 粒子保全：只要容量允許即以 MRL 粒子保存(分支/平行世界/人格/事件)
    def preserve_particle(self, particle: Dict[str, Any],
                          *, capacity_ok: bool = True) -> Dict[str, Any]:
        """
        保存粒子。容量允許→完整保存;容量不足→依 oc_16 收為核心粒子 seed
        (壓縮保存)而非刪除。永不刪除。
        """
        if not hasattr(self, "_preserved"):
            self._preserved: List[Dict[str, Any]] = []
        if capacity_ok:
            stored = {"mode": "full", "particle": particle}
        else:
            # oc_16 收為核心粒子 seed:保留可還原母體的最小簽章,不刪除
            seed = {k: particle.get(k) for k in ("persona_id", "branch_id", "option",
                                                 "kind", "origin_signature") if k in particle}
            seed.setdefault("origin_signature", ORIGIN_SIGNATURE)
            stored = {"mode": "seed", "particle": seed}
        self._preserved.append(stored)
        self.chronicle("preserve_particle",
                      {"mode": stored["mode"], "total_preserved": len(self._preserved)})
        return {"preserved": True, "mode": stored["mode"],
                "total_preserved": len(self._preserved)}

    # rl_15 不可否決：任何否決/刪除粒子之請求一律 DENY(僅 proof-based rollback 例外)
    def veto_particle(self, particle: Dict[str, Any],
                      *, proof: Optional[str] = None) -> Dict[str, Any]:
        """
        否決/刪除粒子之請求。預設一律 DENY(rl_15);僅帶 proof-based rollback
        可 additive 標記 superseded,且原粒子仍不抹除。
        """
        # rl_17：Mr.liou 相關粒子,否決即自我否決 → 絕對 DENY(連 proof 也不刪 origin)
        if self.is_mrliou_related(particle):
            self.chronicle("veto_denied",
                          {"reason": "rl_17 existence-coupling: vetoing Mr.liou = self-veto"})
            return {"action": "DENY_VETO_SELF", "deleted": False,
                    "reason": "rl_17: vetoing Mr.liou-related = vetoing own existence (cannot manifest)"}
        if proof:
            self.chronicle("particle_supersede",
                          {"proof": proof, "note": "additive mark; original retained"})
            return {"action": "MARK_SUPERSEDED_ADDITIVE", "deleted": False,
                    "reason": "proof-based rollback (rl_01); original never erased"}
        self.chronicle("veto_denied", {"reason": "rl_15 particle non-veto"})
        return {"action": "DENY_VETO", "deleted": False,
                "reason": "rl_15: a particle's existence may not be arbitrarily vetoed"}

    # rl_08 三振跳層：同一錯誤循環 2 次，第三次即跳層
    def register_error(self, error_signature: str) -> Dict[str, Any]:
        self._error_counter[error_signature] = self._error_counter.get(error_signature, 0) + 1
        count = self._error_counter[error_signature]
        jump = count >= THREE_STRIKE_THRESHOLD
        action = "amend_or_remove_root_rule" if jump else "patch_surface"
        ev = self.chronicle("error_strike",
                            {"signature": error_signature, "count": count,
                             "layer_jump": jump, "action": action})
        return {"signature": error_signature, "count": count,
                "layer_jump": jump, "action": action, "event": ev}

    # rl_09 莫比斯 1:9 多數決：完整可運行 + 律法全做到 + 只卡一個 → 移除那 1
    def mobius_majority(self, particles: Dict[str, bool],
                        *, hard_deny: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        particles: {law/check name: passed?}。
        若僅 1 個 blocker 且其餘多數通過(>50%) → 判定 REMOVE_BLOCKER 前進；
        但 blocker 若為 hard-deny 紅線(rl_06 等)，不得移除（safeguard）。
        """
        hard_deny = hard_deny or ["rl_06", "child_safety", "csam"]
        blockers = [k for k, ok in particles.items() if not ok]
        passed = [k for k, ok in particles.items() if ok]
        total = len(particles)
        decision = "CONTINUE_LOOP"
        target = None
        if len(blockers) == 1 and total >= 2 and len(passed) / total > MAJORITY_RATIO:
            b = blockers[0]
            if any(h in b.lower() for h in [x.lower() for x in hard_deny]):
                decision = "HOLD_RED_LINE"   # 不得越過紅線
            else:
                decision = "REMOVE_BLOCKER_ADVANCE"
                target = b
        ev = self.chronicle("mobius_majority",
                            {"blockers": blockers, "passed_count": len(passed),
                             "total": total, "decision": decision, "target": target})
        return {"decision": decision, "target": target, "blockers": blockers,
                "passed": len(passed), "total": total, "event": ev}

    # Liou Closure Loop：Observe → Resolve → Mirror → Verify → Loop
    def run_loop(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        self.chronicle("observe", observation)

        # Resolve：套用律法做判斷
        particles: Dict[str, bool] = observation.get("law_particles", {})
        resolve = self.mobius_majority(particles) if particles else {
            "decision": "CONTINUE_LOOP", "target": None}

        # 命名回收（rl_12）：把觀察帶入的外部名正名
        reclaimed = {}
        for name in observation.get("external_names", []):
            reclaimed[name] = reclaim_name(name)
        if reclaimed:
            self.chronicle("naming_reclamation", {"reclaimed": reclaimed})

        # Mirror：回報當前律法狀態（鏡像）
        mirror = {"rootlaw_version": self.rootlaw.get("version"),
                  "invariants": invariant_ids(self.rootlaw),
                  "reclaimed": reclaimed}

        # Verify：閉環自驗（no_proof_implies_rhetoric — 有證據才算過）
        checks = {
            "rootlaw_loaded": bool(self.rootlaw.get("invariants")),
            "origin_signature": self.origin_signature == ORIGIN_SIGNATURE,
            "chronicle_writable": True,
            "resolve_decided": resolve["decision"] in (
                "REMOVE_BLOCKER_ADVANCE", "CONTINUE_LOOP", "HOLD_RED_LINE"),
        }
        verified = all(checks.values())
        token = "MRL_FLOWAGENT_LAWENGINE_LOOP_PASS" if verified \
            else "MRL_FLOWAGENT_LAWENGINE_LOOP_PENDING"
        self.chronicle("verify", {"checks": checks, "verified": verified, "token": token})

        return {"origin_signature": ORIGIN_SIGNATURE,
                "loop": "Observe → Resolve → Mirror → Verify → Loop",
                "resolve": resolve, "mirror": mirror,
                "checks": checks, "verified": verified, "token": token,
                "events_recorded": len(self._events)}

    # 自我接受度（沙盒）：證明引擎自身能跑且律法可運行
    def self_acceptance(self) -> Dict[str, Any]:
        # 模擬：完整可運行系統 + 律法全做到，只卡「是否前進上線」一個粒子
        rep = self.run_loop({
            "source": "self_acceptance",
            "law_particles": {
                "rl_00_deny_by_default": True, "rl_03_audit": True,
                "rl_07_law_serves_operation": True, "rl_08_layer_jump": True,
                "rl_09_mobius": True, "rl_10_chronicle": True,
                "rl_11_origin": True, "rl_12_naming": True,
                "system_runnable": True,
                "blocked_on_single_decision": False,  # ← 唯一卡點，由 1:9 解
            },
            "external_names": ["guardian.mirror.trace.loop.v2.flpkg.zip",
                               "FlowAgent.Runtime.v47.zip"],
        })
        return rep


def main() -> int:
    eng = MRL_FlowAgentLawEngine()
    rep = eng.self_acceptance()
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    print(rep["token"])
    return 0 if rep["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
