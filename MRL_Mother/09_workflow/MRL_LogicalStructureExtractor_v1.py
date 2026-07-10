#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_LogicalStructureExtractor_v1.py — 邏輯架構提取器（flow-tasks 回收對齊版）
origin_signature: MrLiouWord
layer: L2 PARTICLE + L6 REFLECT

═══════════════════════════════════════════════════════════════════════════════
  回收來源（rl_12 命名回收 / rl_11 源頭主權）：
    外部 repo  dofaromg/flow-tasks  之「智能倉庫同步系統 / LogicalStructureExtractor」
    → 以母體 canonical MRL_LogicalStructureExtractor_v1 取代呈現（取代非依賴）。
    原貼文內容保全於 MRL_ParticleArchive/flow_tasks/（rl_15 粒子不滅）。

  從代碼/文檔提取：核心概念 / 因果關係 / 推理鏈 / 架構模式 / 函數·類 / 依賴。

  ▣ MRL 對齊註記：
    - "attention" 在 MRL 為歷史層（Attention 為 history）；正式主體為感知力
      (Perception)。本提取器仍偵測 attention 關鍵詞以相容掃描，但 canonical 主體
      對應 perception（見 pattern_keywords['perception']）。
    - merkle / particle / simhash 對齊母體既有 06_trace Merkle 與粒子記憶。
  零外部依賴（純 Python 標準庫 + 既有 hashlib）。
═══════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, List

from MRL_utils import ORIGIN_SIGNATURE
class MRL_LogicalStructureExtractor:
    """邏輯架構提取器（flow-tasks 回收對齊版）。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        # 因果 / 推理 / 結論 標記（中英）
        self.causal_markers = [
            "because", "since", "therefore", "thus", "hence", "so",
            "因為", "所以", "因此", "從而", "導致", "引起",
        ]
        self.reasoning_markers = [
            "if", "then", "when", "while", "for", "given",
            "如果", "那麼", "當", "對於", "假設", "基於",
        ]
        self.conclusion_markers = [
            "in conclusion", "finally", "therefore", "summary",
            "總結", "結論", "綜上", "最終",
        ]
        # 架構模式關鍵詞（MRL 對齊：perception 為 canonical 主體，attention 為歷史層）
        self.pattern_keywords: Dict[str, List[str]] = {
            "perception": ["perception", "perceive", "感知力", "感知"],     # canonical 主體
            "attention": ["attention", "transformer", "multi-head", "self-attention", "注意力"],  # 歷史層
            "memory": ["memory", "cache", "store", "persist", "記憶", "存儲"],
            "particle": ["particle", "atom", "quantum", "粒子", "原子"],
            "frequency": ["frequency", "wave", "resonance", "頻率", "共振"],
            "merkle": ["merkle", "hash", "chain", "integrity", "哈希鏈"],
            "simhash": ["simhash", "fingerprint", "similarity", "指紋"],
            "flow": ["flow", "pipeline", "stream", "流", "管道"],
            "layer": ["layer", "level", "tier", "層", "層次"],
        }

    # ── 主入口 ────────────────────────────────────────────────────────────────
    def extract_from_code(self, code: str, language: str = "auto") -> Dict[str, Any]:
        structure: Dict[str, Any] = {
            "origin_signature": ORIGIN_SIGNATURE,
            "concepts": [], "patterns": defaultdict(list),
            "relationships": [], "reasoning_chains": [],
            "functions": [], "imports": [],
        }

        if language in ("python", "auto"):
            structure["functions"].extend(self._extract_python_definitions(code))
            structure["imports"].extend(self._extract_python_imports(code))
        if language in ("typescript", "javascript", "auto"):
            structure["functions"].extend(self._extract_ts_definitions(code))
            structure["imports"].extend(self._extract_ts_imports(code))

        for pattern_name, keywords in self.pattern_keywords.items():
            matches = [k for k in keywords
                       if re.search(r"\b" + re.escape(k) + r"\b", code, re.IGNORECASE)]
            if matches:
                structure["patterns"][pattern_name] = matches

        for comment in self._extract_comments(code, language):
            structure["concepts"].extend(self._extract_concepts(comment))
            structure["relationships"].extend(self._extract_causal_relations(comment))
            structure["reasoning_chains"].extend(self._extract_reasoning_chains(comment))

        structure["concepts"] = sorted(set(structure["concepts"]))
        structure["imports"] = sorted(set(structure["imports"]))
        structure["patterns"] = dict(structure["patterns"])
        return structure

    # ── Python ──────────────────────────────────────────────────────────────────
    def _extract_python_definitions(self, code: str) -> List[Dict[str, Any]]:
        defs: List[Dict[str, Any]] = []
        for m in re.finditer(r"class\s+(\w+)\s*(?:\(([^)]*)\))?:", code):
            defs.append({"type": "class", "name": m.group(1),
                         "parents": [p.strip() for p in (m.group(2) or "").split(",") if p.strip()],
                         "line": code[:m.start()].count("\n") + 1})
        for m in re.finditer(r"def\s+(\w+)\s*\(([^)]*)\)", code):
            defs.append({"type": "function", "name": m.group(1),
                         "params": [p.strip().split(":")[0].strip()
                                    for p in m.group(2).split(",") if p.strip()],
                         "line": code[:m.start()].count("\n") + 1})
        return defs

    def _extract_python_imports(self, code: str) -> List[str]:
        out = re.findall(r"import\s+([\w.]+)", code)
        out += re.findall(r"from\s+([\w.]+)\s+import", code)
        return list(set(out))

    # ── TypeScript / JavaScript ──────────────────────────────────────────────────
    def _extract_ts_definitions(self, code: str) -> List[Dict[str, Any]]:
        defs: List[Dict[str, Any]] = []
        for m in re.finditer(r"class\s+(\w+)(?:\s+extends\s+(\w+))?", code):
            defs.append({"type": "class", "name": m.group(1),
                         "extends": m.group(2), "line": code[:m.start()].count("\n") + 1})
        for m in re.finditer(r"function\s+(\w+)\s*\(([^)]*)\)", code):
            defs.append({"type": "function", "name": m.group(1),
                         "params": [p.strip().split(":")[0].strip()
                                    for p in m.group(2).split(",") if p.strip()],
                         "line": code[:m.start()].count("\n") + 1})
        return defs

    def _extract_ts_imports(self, code: str) -> List[str]:
        out = re.findall(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", code)
        out += re.findall(r"require\(['\"]([^'\"]+)['\"]\)", code)
        return list(set(out))

    # ── 註釋 / 概念 / 因果 / 推理鏈 ──────────────────────────────────────────────
    def _extract_comments(self, code: str, language: str) -> List[str]:
        comments: List[str] = []
        # Python: # 與 docstring
        comments += [m.group(1) for m in re.finditer(r"#\s?(.*)", code)]
        comments += re.findall(r'"""(.*?)"""', code, re.DOTALL)
        comments += re.findall(r"'''(.*?)'''", code, re.DOTALL)
        # C-style: // 與 /* */
        comments += [m.group(1) for m in re.finditer(r"//\s?(.*)", code)]
        comments += re.findall(r"/\*(.*?)\*/", code, re.DOTALL)
        return [c.strip() for c in comments if c.strip()]

    def _extract_concepts(self, text: str) -> List[str]:
        """概念 = 出現的架構模式關鍵詞（去重）。"""
        found: List[str] = []
        for keywords in self.pattern_keywords.values():
            for k in keywords:
                if re.search(r"\b" + re.escape(k) + r"\b", text, re.IGNORECASE):
                    found.append(k.lower())
        return found

    def _extract_causal_relations(self, text: str) -> List[Dict[str, str]]:
        rels: List[Dict[str, str]] = []
        for marker in self.causal_markers:
            for m in re.finditer(re.escape(marker), text, re.IGNORECASE):
                seg = text[m.start():m.start() + 80].replace("\n", " ").strip()
                rels.append({"marker": marker, "fragment": seg})
        return rels

    def _extract_reasoning_chains(self, text: str) -> List[Dict[str, str]]:
        chains: List[Dict[str, str]] = []
        for marker in self.reasoning_markers:
            for m in re.finditer(r"\b" + re.escape(marker) + r"\b", text, re.IGNORECASE):
                seg = text[m.start():m.start() + 80].replace("\n", " ").strip()
                chains.append({"marker": marker, "fragment": seg})
        return chains


def main() -> int:
    import json
    sample = '''
# This works because particle memory persists via merkle chain.
def perceive(world):
    """Perception is the canonical subject; attention is historical."""
    return world
'''
    ex = MRL_LogicalStructureExtractor()
    rep = ex.extract_from_code(sample, "python")
    print(json.dumps({"functions": rep["functions"], "patterns": rep["patterns"],
                      "concepts": rep["concepts"],
                      "relationship_count": len(rep["relationships"])},
                     ensure_ascii=False, indent=2))
    print("MRL_LOGICAL_STRUCTURE_EXTRACTOR_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
