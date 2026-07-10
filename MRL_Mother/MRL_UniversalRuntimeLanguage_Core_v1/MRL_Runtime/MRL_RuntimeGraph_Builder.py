# MRL_RuntimeGraph_Builder — COMPATIBILITY ALIAS（歷史名稱，非 canonical）
# origin_signature: MrLiouWord
# canonical 已遷移至 MRL_RuntimeStructureField；本檔僅為向後兼容 alias，請勿新增主體邏輯。
"""[DEPRECATED] RuntimeGraph / *Graph* 為歷史名稱 / Adapter / alias。

正式 canonical = StructureField（見 MRL_RuntimeStructureField）。
本模組原樣轉出 build / 視覺化函式，並提供舊鍵鏡射 (graph_hash / replay_graph / ...) 供兼容。
"""
from __future__ import annotations

from typing import Any, Dict

from . import MRL_RuntimeStructureField as _sf
from .MRL_RuntimeStructureField import (  # noqa: F401
    ORIGIN_SIGNATURE,
    build as _build_structurefield,
)


def build(mrliouir: Dict[str, Any], observation_order=None) -> Dict[str, Any]:
    """[alias] 等同 MRL_RuntimeStructureField.build；額外鏡射舊 *graph* 鍵。"""
    sf = dict(_build_structurefield(mrliouir, observation_order))
    sf["graph_version"] = sf["structurefield_version"]
    sf["graph_hash"] = sf["structurefield_hash"]
    sf["edges"] = sf["relations"]
    sf["edge_count"] = sf["relation_count"]
    sf["replay_graph"] = sf["replay_structurefield"]
    sf["restore_graph"] = sf["restore_structurefield"]
    sf["world_graph"] = sf["world_structurefield"]
    return sf


def _normalize_legacy(obj: Dict[str, Any]) -> Dict[str, Any]:
    """接受 legacy graph 物件（可能只有 edges/graph_hash，如舊存檔 MRL_RuntimeGraph.json）
    → 補上 canonical 鍵（relations/structurefield_hash）供 StructureField viz 使用，避免 KeyError。"""
    o = dict(obj)
    if "relations" not in o and "edges" in o:
        o["relations"] = o["edges"]
    if "structurefield_hash" not in o and "graph_hash" in o:
        o["structurefield_hash"] = o["graph_hash"]
    o.setdefault("nodes", [])
    return o


def to_mermaid(graph: Dict[str, Any], max_nodes: int = 60) -> str:
    """[alias] 接受 canonical 或 legacy(edges) 物件；先正規化再委派 canonical to_mermaid。"""
    return _sf.to_mermaid(_normalize_legacy(graph), max_nodes)


def to_dot(graph: Dict[str, Any]) -> str:
    return _sf.to_dot(_normalize_legacy(graph))


def to_json(graph: Dict[str, Any]) -> str:
    return _sf.to_json(_normalize_legacy(graph))



__all__ = ["build", "to_mermaid", "to_dot", "to_json", "ORIGIN_SIGNATURE"]
