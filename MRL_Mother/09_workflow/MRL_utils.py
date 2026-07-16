#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_utils.py — 母體共用工具集（L0 / Y=0 RootGate，去重蒸餾唯一真實來源）
origin_signature: MrLiouWord
layer: L0 ROOT
group: Y=0 RootGate

本模組是所有 MRL-prefixed 模組共用工具的唯一真實來源（Single Source of Truth）。
不得在其他模組重複定義這裡已定義的符號；應以 `from MRL_utils import ...` 引入。

依賴：Python stdlib only（hashlib, json, importlib）— 無外部套件、無循環匯入。
"""
from __future__ import annotations

import hashlib
import importlib
import json
from typing import Any, Dict, Optional

# ─── 母體源頭主權簽章 ─────────────────────────────────────────────────────────
ORIGIN_SIGNATURE: str = "MrLiouWord"


# ─── 安全動態匯入 ─────────────────────────────────────────────────────────────
def _try_import(module: str, attr: str) -> Any:
    """嘗試從 *module* 匯入 *attr*；失敗則靜默回傳 None。"""
    try:
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    except Exception:  # noqa: BLE001
        return None


# ─── LAW-0 簽章（Python 鏡像，與 09_workflow/signature.js 位元相容） ──────────
#   公式：T(e) = e'  ⟹  signature(e) = signature(e')
#   相容性：採 JS JSON.stringify 等價的 compact 序列化（無空白、保留 unicode、
#           維持插入順序），故 _sig_hash 與 signature.js 對同一物件一致。
# ─────────────────────────────────────────────────────────────────────────────

def _compact_json(obj: Dict[str, Any]) -> str:
    """等價 JS JSON.stringify(obj)：compact、ensure_ascii=False、插入序。"""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def embed_signature(obj: Dict[str, Any], sig: str = ORIGIN_SIGNATURE) -> Dict[str, Any]:
    """
    LAW-0 embedSignature：非破壞性地嵌入母體簽章。
    新增 _signature 與 _sig_hash = sha256(sig + ":" + compact_json(obj))。
    """
    if not isinstance(obj, dict):
        raise TypeError("embed_signature: obj must be a plain dict")
    base = _compact_json(obj)
    sig_hash = hashlib.sha256((sig + ":" + base).encode("utf-8")).hexdigest()
    return {**obj, "_signature": sig, "_sig_hash": sig_hash}


def extract_signature(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """LAW-0 extractSignature：讀出已嵌入的簽章資訊；無則 None。"""
    if not isinstance(obj, dict):
        return None
    sig = obj.get("_signature")
    if not sig:
        return None
    return {"signature": sig, "sig_hash": obj.get("_sig_hash")}


def verify_signature(
    obj: Dict[str, Any], expected_sig: str = ORIGIN_SIGNATURE
) -> bool:
    """
    LAW-0 verifySignature：剝除 _signature/_sig_hash 後重新雜湊比對。
    回傳 True iff 簽章欄位存在且雜湊吻合。
    """
    if not isinstance(obj, dict):
        return False
    stored_sig = obj.get("_signature")
    stored_hash = obj.get("_sig_hash")
    if not stored_sig or not stored_hash:
        return False
    if stored_sig != expected_sig:
        return False
    base_obj = {k: v for k, v in obj.items() if k not in ("_signature", "_sig_hash")}
    expected_hash = hashlib.sha256(
        (expected_sig + ":" + _compact_json(base_obj)).encode("utf-8")
    ).hexdigest()
    return expected_hash == stored_hash
