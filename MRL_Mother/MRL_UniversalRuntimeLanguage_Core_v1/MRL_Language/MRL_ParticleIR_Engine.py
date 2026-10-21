# MRL_ParticleIR_Engine
# origin_signature: MrLiouWord
# layer: MRL_Language (L2 PARTICLE)
"""ParticleIR 引擎：粒子語言層 .fltnz / .flpkg 的可逆鏈與粒子運算。

復用既有 09_workflow/fltnz_parser.py（不重建另一套可逆鏈），於其上增加粒子運算：
  jump      — 確定性可逆重排（保存 permutation 以還原）
  rhythm    — token 節奏度量（word/ws/nl 的節律統計）
  collapse  — 粒子塌縮（沿用 fltnz ref-compression；expand 為其逆）
  perception/persona/world mapping — 粒子標註對映

可逆原則：怎麼過去，就怎麼回來（path forward == path back）。
"""

from __future__ import annotations

import importlib.util
import pathlib
from typing import Any, Dict, List, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"


def _load_fltnz():
    """以檔案路徑載入 09_workflow/fltnz_parser.py（套件名以數字開頭無法 import）。"""
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "09_workflow" / "fltnz_parser.py"
        if cand.exists():
            spec = importlib.util.spec_from_file_location("mrl_fltnz_parser", cand)
            mod = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError("無法定位 09_workflow/fltnz_parser.py（ParticleIR 可逆鏈後端）")


_fltnz = _load_fltnz()


# ─── 可逆鏈（封裝 fltnz 全鏈 txt↔fltnz↔flpkg↔trace） ───────────────────────────

def to_particles(text: str, label: str = "particle") -> Dict[str, Any]:
    """txt → fltnz → flpkg → trace（前向全鏈）。"""
    return _fltnz.text_to_trace(text, label=label)


def from_particles(trace: Dict[str, Any]) -> str:
    """trace → flpkg → fltnz → txt（反向全鏈，含 checksum 驗證）。"""
    return _fltnz.trace_to_text(trace)


def encode(text: str) -> Dict[str, Any]:
    return _fltnz.encode(text)


def decode(envelope: Dict[str, Any]) -> str:
    return _fltnz.decode(envelope)


# ─── 粒子運算 ──────────────────────────────────────────────────────────────────

def collapse(text: str) -> Dict[str, Any]:
    """粒子塌縮：以 fltnz ref-compression 表達（重複 word → back-ref）。"""
    return _fltnz.encode(text)  # encode 內已做 _compress_tokens


def expand(envelope: Dict[str, Any]) -> str:
    """塌縮之逆：還原回原文。"""
    return _fltnz.decode(envelope)


def rhythm(text: str) -> Dict[str, Any]:
    """token 節奏度量：word / ws / nl 的數量與節律比。"""
    env = _fltnz.encode(text)
    resolved = _fltnz._decompress_tokens(env["tokens"])  # 還原 ref 後計數
    counts = {"word": 0, "ws": 0, "nl": 0}
    for t in resolved:
        counts[t["t"]] = counts.get(t["t"], 0) + 1
    total = max(1, sum(counts.values()))
    return {
        "counts": counts,
        "cadence": {k: round(v / total, 4) for k, v in counts.items()},
        "total_particles": total,
    }


def jump(text: str, permutation: List[int] | None = None) -> Tuple[List[Dict[str, Any]], List[int]]:
    """確定性可逆重排：回傳 (重排後 token 串列, permutation)。

    無指定 permutation 時採確定性反轉（reverse），便於測試其可逆性。
    """
    env = _fltnz.encode(text)
    tokens = _fltnz._decompress_tokens(env["tokens"])
    n = len(tokens)
    if permutation is None:
        permutation = list(range(n - 1, -1, -1))
    if sorted(permutation) != list(range(n)):
        raise ValueError("jump: permutation 必須為 0..n-1 的排列")
    jumped = [tokens[p] for p in permutation]
    return jumped, permutation


def unjump(jumped: List[Dict[str, Any]], permutation: List[int]) -> str:
    """jump 之逆：還原原文。"""
    n = len(jumped)
    original = [None] * n
    for new_pos, orig_pos in enumerate(permutation):
        original[orig_pos] = jumped[new_pos]
    return "".join(t["v"] for t in original)  # type: ignore[index]


def map_particles(mrliouir: Dict[str, Any]) -> Dict[str, Any]:
    """perception / persona / world 粒子對映（確定性標註）。"""
    mapping: Dict[str, List[str]] = {"perception": [], "persona": [], "world": []}
    for node in mrliouir.get("nodes", []):
        role = node["semantic"]["role"]
        nid = node["node_id"]
        if role in ("definition", "invocation", "control_flow"):
            mapping["world"].append(nid)
        elif role in ("narrative", "structure", "enumeration"):
            mapping["persona"].append(nid)
        mapping["perception"].append(nid)  # 全節點皆進入感知場
    return {
        "origin_signature": ORIGIN_SIGNATURE,
        "perception_count": len(mapping["perception"]),
        "persona_count": len(mapping["persona"]),
        "world_count": len(mapping["world"]),
        "mapping": mapping,
    }
