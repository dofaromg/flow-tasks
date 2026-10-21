# MRL_MrLiouIR_Compiler
# origin_signature: MrLiouWord
# layer: MRL_Language
# canonical: MrLiouIR（MrLiou 中介語義層 / MRL 母體正式中介表示層）
# 兼容：MetaIR 為歷史名稱 / Adapter / alias，不再作 canonical 主體命名。
"""MrLiouIR 編譯器：ParseResult → SemanticIR → ContextIR → IntentIR → MrLiouIR。

MrLiouIR = MRL 母體正式中介表示層（非 generic meta layer）。
在結構之上推導語意角色(Semantic)、上下文關係(Context)、意圖(Intent)，再收斂為
穩定可重現的 MrLiouIR（每節點具確定性 node_id 與 content hash）。
確定性保證：相同輸入永遠產生相同 MrLiouIR（replay/verify 之根據）。
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

ORIGIN_SIGNATURE = "MrLiouWord"

# unit.kind → 語意角色
_SEMANTIC_ROLE = {
    "heading": "structure",
    "list_item": "enumeration",
    "paragraph": "narrative",
    "object": "container",
    "array": "sequence",
    "scalar": "datum",
    "def": "definition",
    "class": "definition",
    "import": "dependency",
    "assign": "binding",
    "control": "control_flow",
    "call": "invocation",
    "stmt": "statement",
    "line": "statement",
}

# 語意角色 → 意圖
_INTENT = {
    "structure": "organize",
    "enumeration": "enumerate",
    "narrative": "describe",
    "container": "hold",
    "sequence": "order",
    "datum": "store",
    "definition": "declare",
    "dependency": "require",
    "binding": "assign",
    "control_flow": "branch",
    "invocation": "execute",
    "statement": "evaluate",
}


def _node_id(index: int, content_hash: str) -> str:
    return f"n{index:04d}_{content_hash[:8]}"


def _content_hash(text: str, kind: str) -> str:
    return hashlib.sha256(f"{kind}|{text}".encode("utf-8")).hexdigest()


def _semantic_role(kind: str) -> str:
    if kind.startswith("particle:"):
        return "particle"
    return _SEMANTIC_ROLE.get(kind, "statement")


def compile_mrliouir(parse_result: Dict[str, Any]) -> Dict[str, Any]:
    """ParseResult → MrLiouIR（含 semantic/context/intent 三層收斂）。"""
    units: List[Dict[str, Any]] = parse_result.get("units", [])
    nodes: List[Dict[str, Any]] = []

    depth_to_id: Dict[int, str] = {}

    for i, u in enumerate(units):
        text = u.get("text", "")
        kind = u.get("kind", "statement")
        depth = int(u.get("depth", 0))
        chash = _content_hash(text, kind)
        nid = _node_id(i, chash)

        role = _semantic_role(kind)            # SemanticIR
        intent = _INTENT.get(role, "evaluate") if not role == "particle" else "particle_flow"  # IntentIR

        # ContextIR：parent = 最近的較淺節點
        parent = None
        for d in range(depth - 1, -1, -1):
            if d in depth_to_id:
                parent = depth_to_id[d]
                break
        depth_to_id[depth] = nid
        for d in list(depth_to_id.keys()):
            if d > depth:
                del depth_to_id[d]

        nodes.append({
            "node_id": nid,
            "index": i,
            "semantic": {"kind": kind, "role": role},
            "context": {"depth": depth, "parent": parent},
            "intent": intent,
            "content": text,
            "content_hash": chash,
        })

    mrliouir_hash = hashlib.sha256(
        "".join(n["node_id"] for n in nodes).encode("utf-8")
    ).hexdigest()

    return {
        "mrliouir_version": "1.0",
        "origin_signature": ORIGIN_SIGNATURE,
        "lang": parse_result.get("lang"),
        "source_checksum": parse_result.get("raw_checksum"),
        "node_count": len(nodes),
        "mrliouir_hash": mrliouir_hash,
        "nodes": nodes,
    }


# ── Compatibility alias layer（MetaIR 為歷史名稱，僅向後兼容，非 canonical）──
def compile_metair(parse_result: Dict[str, Any]) -> Dict[str, Any]:
    """[DEPRECATED alias] 等同 compile_mrliouir；額外鏡射舊鍵 metair_* 供兼容。"""
    out = dict(compile_mrliouir(parse_result))
    out["metair_version"] = out["mrliouir_version"]
    out["metair_hash"] = out["mrliouir_hash"]
    return out
