# MRL_RuntimeStructureField
# origin_signature: MrLiouWord
# layer: MRL_Runtime
# canonical: StructureField（結構場 / 高維動態運轉場）
# 兼容：RuntimeGraph / *Graph* 為歷史名稱 / Adapter / alias，不再作 canonical 主體命名。
"""RuntimeStructureField 建構：MrLiouIR → 高維運轉場（不再是 node+edge+path）。

StructureField 正式定義 = structure + field + state + flow + rhythm + collapse
  + runtime relation + world synchronization + replay/recovery → 高維文明運轉場。

build() 產出（確定性）：
    nodes / relations（節點與關係，取代舊 node/edge）
    replay_structurefield   依觀察序的 op 串列（可精確重播）
    restore_structurefield  checkpoint 標記點
    world_structurefield    node_id → world 標籤
另提供 to_mermaid / to_dot / to_json 之 MRL_StructureField_Visualization 輸出。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"


def build(mrliouir: Dict[str, Any], observation_order: List[str] | None = None) -> Dict[str, Any]:
    nodes = mrliouir.get("nodes", [])
    node_ids = [n["node_id"] for n in nodes]
    id_to_node = {n["node_id"]: n for n in nodes}

    relations: List[Tuple[str, str, str]] = []
    # 序列關係（執行流）
    for a, b in zip(node_ids, node_ids[1:]):
        relations.append((a, b, "seq"))
    # 上下文關係（parent → child）
    for n in nodes:
        parent = n["context"]["parent"]
        if parent:
            relations.append((parent, n["node_id"], "context"))

    order = observation_order or node_ids
    replay_structurefield = [
        {"step": i, "node_id": nid, "intent": id_to_node[nid]["intent"], "hash": id_to_node[nid]["content_hash"]}
        for i, nid in enumerate(order)
        if nid in id_to_node
    ]
    restore_structurefield = [
        step["node_id"]
        for step in replay_structurefield
        if id_to_node[step["node_id"]]["semantic"]["role"] == "definition" or step["step"] % 8 == 0
    ]
    world_structurefield = {
        n["node_id"]: ("core_world" if n["semantic"]["role"] == "definition" else "context_world")
        for n in nodes
    }

    structurefield = {
        "structurefield_version": "1.0",
        "origin_signature": ORIGIN_SIGNATURE,
        "node_count": len(node_ids),
        "relation_count": len(relations),
        "nodes": node_ids,
        "relations": relations,
        "replay_structurefield": replay_structurefield,
        "restore_structurefield": restore_structurefield,
        "world_structurefield": world_structurefield,
    }
    structurefield["structurefield_hash"] = hashlib.sha256(
        json.dumps([structurefield["nodes"], structurefield["relations"]], ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return structurefield


# ── MRL_StructureField_Visualization ──────────────────────────────────────────

def to_mermaid(structurefield: Dict[str, Any], max_nodes: int = 60) -> str:
    lines = ["graph TD"]
    shown = set(structurefield["nodes"][:max_nodes])
    for (src, dst, kind) in structurefield["relations"]:
        if src in shown and dst in shown:
            arrow = "-->" if kind == "seq" else "-.->"
            lines.append(f'    {src}{arrow}{dst}')
    if len(structurefield["nodes"]) > max_nodes:
        lines.append(f'    note["... {len(structurefield["nodes"]) - max_nodes} more nodes truncated"]')
    return "\n".join(lines)


def to_dot(structurefield: Dict[str, Any]) -> str:
    lines = ["digraph MRL_RuntimeStructureField {", '  rankdir=TB;']
    for (src, dst, kind) in structurefield["relations"]:
        style = "" if kind == "seq" else ' [style=dashed]'
        lines.append(f'  "{src}" -> "{dst}"{style};')
    lines.append("}")
    return "\n".join(lines)


def to_json(structurefield: Dict[str, Any]) -> str:
    return json.dumps(structurefield, ensure_ascii=False, indent=2)
