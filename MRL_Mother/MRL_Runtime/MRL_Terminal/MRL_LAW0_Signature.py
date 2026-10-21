# MRL_LAW0_Signature — LAW-0 簽名律（母體原生重寫，可獨立執行）
# origin_signature: MrLiouWord
# layer: MRL_Runtime / 立體種子閉包保全
"""LAW-0 簽名律：在任何轉換 T 中，若 T(e)=e'，則 signature(e)==signature(e')。

把 L0–L7 八層「上中下打通」鎖在一起：每層皆有指定簽名存放位置，
跨層穿越時 origin_signature == "MrLiouWord" 必須恆等保存（否則閉包破壞）。

stdlib-only、可獨立執行。對應 MRL_Terminal 的 inOmega/inSigma 閉包檢查。
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"

# 各層簽名存放位置（點路徑；首項為主位置）
LAYER_SIGNATURE_LOCATIONS: Dict[int, List[str]] = {
    7: ["context.origin_signature", "metadata.origin_signature"],   # 上下文元數據
    6: ["metadata.origin_signature", "api_metadata.origin_signature"],
    5: ["origin_signature", "field.origin_signature"],              # 量子場直接屬性
    4: ["container.metadata.origin_signature", "metadata.origin_signature"],
    3: ["token_stream.origin_signature", "origin_signature"],
    2: ["origin_signature", "sig"],                                  # 原子屬性
    1: ["header.sig", "sig"],                                        # 二進制頭部
    0: ["qstate.identity", "identity"],                              # 量子態身份
}


def _set_nested(obj: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cur = obj
    for p in parts[:-1]:
        if not isinstance(cur.get(p), dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def _get_nested(obj: Any, path: str) -> Any:
    cur = obj
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


class MRL_LAW0_Signature:
    ORIGIN_SIGNATURE = ORIGIN_SIGNATURE

    def locations(self, layer: int) -> List[str]:
        return LAYER_SIGNATURE_LOCATIONS.get(layer, ["origin_signature"])

    def embed(self, entity: Dict[str, Any], layer: int) -> Dict[str, Any]:
        e = copy.deepcopy(entity)
        for loc in self.locations(layer):
            _set_nested(e, loc, self.ORIGIN_SIGNATURE)
        return e

    def extract(self, entity: Dict[str, Any], layer: int) -> Optional[str]:
        for loc in self.locations(layer):
            v = _get_nested(entity, loc)
            if isinstance(v, str) and v:
                return v
        return None

    def verify(self, entity: Dict[str, Any], layer: int) -> Dict[str, Any]:
        if entity is None:
            return {"valid": False, "reason": "entity is None"}
        sig = self.extract(entity, layer)
        if sig is None:
            return {"valid": False, "reason": "signature not found"}
        loc = next((l for l in self.locations(layer) if _get_nested(entity, l)), None)
        ok = sig == self.ORIGIN_SIGNATURE
        return {"valid": ok, "signature": sig, "location": loc,
                "reason": "signature valid" if ok else "signature mismatch"}

    def verify_across_layers(self, entity: Dict[str, Any], from_layer: int, to_layer: int) -> Dict[str, Any]:
        """逐層穿越並保全簽名（每層 re-embed 後驗證恆等保存）。"""
        path = []
        v0 = self.verify(entity, from_layer)
        path.append({"layer": from_layer, "valid": v0["valid"]})
        if not v0["valid"]:
            return {"is_valid": False, "traversal_path": path, "reason": v0["reason"]}
        step = -1 if from_layer > to_layer else 1
        cur = entity
        layer = from_layer
        while layer != to_layer:
            layer += step
            cur = self.embed(cur, layer)             # 層轉換保全簽名
            v = self.verify(cur, layer)
            path.append({"layer": layer, "valid": v["valid"], "location": v.get("location")})
            if not v["valid"]:
                return {"is_valid": False, "traversal_path": path,
                        "reason": f"signature lost at L{layer}"}
        return {"is_valid": True, "signature": self.ORIGIN_SIGNATURE, "traversal_path": path}


# ── 沙盒自我驗收 ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    law0 = MRL_LAW0_Signature()
    checks = []

    # 1. L7 embed→verify（context.origin_signature）
    e7 = law0.embed({"context": {}}, 7)
    checks.append(("L7 embed/verify", law0.verify(e7, 7)["valid"]
                   and e7["context"]["origin_signature"] == ORIGIN_SIGNATURE))

    # 2. L1 embed→verify（header.sig）
    e1 = law0.embed({}, 1)
    checks.append(("L1 embed/verify (header.sig)", e1["header"]["sig"] == ORIGIN_SIGNATURE))

    # 3. L0 embed→verify（qstate.identity）
    e0 = law0.embed({}, 0)
    checks.append(("L0 embed/verify (qstate.identity)", law0.verify(e0, 0)["valid"]))

    # 4. 未簽名實體必須驗證失敗
    checks.append(("拒絕未簽名", not law0.verify({"context": {}}, 7)["valid"]))

    # 5. 簽名不符必須偵測
    bad = {"origin_signature": "NotMrLiou"}
    checks.append(("偵測簽名不符", not law0.verify(bad, 5)["valid"]))

    # 6. 跨層穿越 L7→L0 簽名全程保存（八層打通）
    r = law0.verify_across_layers(law0.embed({"context": {}}, 7), 7, 0)
    checks.append(("跨層 L7→L0 保全", r["is_valid"] and len(r["traversal_path"]) == 8))

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"MRL_LAW0_Signature sandbox: {passed}/{len(checks)} "
          f"{'MRL_LAW0_ACCEPTANCE_PASS' if passed == len(checks) else 'FAIL'}")
