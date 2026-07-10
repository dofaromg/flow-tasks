# MRL_UniversalParser_Core
# origin_signature: MrLiouWord
# layer: MRL_Language
"""通用解析核心：AnyLanguage → 結構化 ParseUnit 串列（確定性、可重現）。

支援語言：python / typescript / cpp / json / markdown / fltnz / flpkg / text。

輸出（確定性，供下游 MrLiouIR/Replay 使用）：

    {
      "lang": "<語言>",
      "raw_checksum": "<sha256 of raw text>",
      "units": [ {"kind": ..., "text": ..., "depth": int, "line": int}, ... ]
    }

深度說明（誠實邊界）：對 python/typescript/cpp 為「結構層級」解析（縮排/大括號深度 +
語句種類辨識），非完整語意編譯器；語意層由 MRL_MrLiouIR_Compiler 接續推導。
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List

ORIGIN_SIGNATURE = "MrLiouWord"

SUPPORTED_LANGS = (
    "python",
    "typescript",
    "cpp",
    "json",
    "markdown",
    "fltnz",
    "flpkg",
    "text",
)

_EXT_LANG = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "typescript",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".h": "cpp",
    ".json": "json",
    ".md": "markdown",
    ".markdown": "markdown",
    ".fltnz": "fltnz",
    ".flpkg": "flpkg",
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def detect_lang(filename: str) -> str:
    fn = filename.lower()
    for ext, lang in _EXT_LANG.items():
        if fn.endswith(ext):
            return lang
    return "text"


# ─── 各語言結構解析 ────────────────────────────────────────────────────────────

def _parse_markdown(text: str) -> List[Dict[str, Any]]:
    units: List[Dict[str, Any]] = []
    for i, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            units.append({"kind": "heading", "text": m.group(2), "depth": len(m.group(1)), "line": i})
        elif re.match(r"^[-*+]\s+", stripped):
            units.append({"kind": "list_item", "text": stripped[2:].strip(), "depth": 1, "line": i})
        else:
            units.append({"kind": "paragraph", "text": stripped, "depth": 0, "line": i})
    return units


def _parse_json(text: str) -> List[Dict[str, Any]]:
    obj = json.loads(text)
    units: List[Dict[str, Any]] = []

    def walk(node: Any, key: str, depth: int) -> None:
        if isinstance(node, dict):
            units.append({"kind": "object", "text": key, "depth": depth, "line": -1})
            for k in node:
                walk(node[k], str(k), depth + 1)
        elif isinstance(node, list):
            units.append({"kind": "array", "text": key, "depth": depth, "line": -1})
            for idx, item in enumerate(node):
                walk(item, f"{key}[{idx}]", depth + 1)
        else:
            units.append({"kind": "scalar", "text": f"{key}={node!r}", "depth": depth, "line": -1})

    walk(obj, "$", 0)
    return units


def _parse_braced(text: str, lang: str) -> List[Dict[str, Any]]:
    """python(縮排) / typescript,cpp(大括號) 的結構層級解析。"""
    units: List[Dict[str, Any]] = []
    brace_depth = 0
    for i, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        if lang == "python":
            indent = len(line) - len(line.lstrip(" "))
            depth = indent // 4
        else:
            depth = brace_depth
        kind = _statement_kind(stripped, lang)
        units.append({"kind": kind, "text": stripped, "depth": depth, "line": i})
        if lang in ("typescript", "cpp"):
            brace_depth += stripped.count("{") - stripped.count("}")
            if brace_depth < 0:
                brace_depth = 0
    return units


def _statement_kind(stripped: str, lang: str) -> str:
    if lang == "python":
        if stripped.startswith("def "):
            return "def"
        if stripped.startswith("class "):
            return "class"
        if stripped.startswith(("import ", "from ")):
            return "import"
        if re.match(r"^[A-Za-z_][\w\.]*\s*=", stripped):
            return "assign"
        if stripped.startswith(("return", "if ", "for ", "while ", "with ", "try", "except", "elif", "else")):
            return "control"
        if re.match(r"^[A-Za-z_][\w\.]*\s*\(", stripped):
            return "call"
        return "stmt"
    # typescript / cpp
    if re.match(r"^(export\s+)?(async\s+)?function\b", stripped) or "=>" in stripped:
        return "def"
    if re.match(r"^(export\s+)?(class|struct|namespace)\b", stripped):
        return "class"
    if stripped.startswith(("#include", "import ", "using ")):
        return "import"
    if re.match(r"^(const|let|var|int|float|double|auto|std::)\b", stripped):
        return "assign"
    if stripped.startswith(("return", "if", "for", "while", "switch", "else", "try", "catch")):
        return "control"
    return "stmt"


def _parse_fltnz(text: str) -> List[Dict[str, Any]]:
    """fltnz/flpkg envelope → 以 token 串列為 unit。"""
    env = json.loads(text)
    payload = env.get("payload", env)  # flpkg 外層含 payload
    tokens = payload.get("tokens", [])
    units: List[Dict[str, Any]] = []
    for i, tok in enumerate(tokens):
        units.append({"kind": f"particle:{tok.get('t')}", "text": str(tok.get("v")), "depth": 0, "line": i})
    return units


def _parse_text(text: str) -> List[Dict[str, Any]]:
    return [
        {"kind": "line", "text": line.strip(), "depth": 0, "line": i}
        for i, line in enumerate(text.splitlines())
        if line.strip()
    ]


_PARSERS = {
    "markdown": _parse_markdown,
    "json": _parse_json,
    "fltnz": _parse_fltnz,
    "flpkg": _parse_fltnz,
    "text": _parse_text,
}


def parse(source: str, lang: str = "text") -> Dict[str, Any]:
    """AnyLanguage 文字 → 結構化 ParseUnit 串列（確定性）。"""
    if lang not in SUPPORTED_LANGS:
        raise ValueError(f"unsupported lang: {lang!r}; supported={SUPPORTED_LANGS}")
    if lang in ("python", "typescript", "cpp"):
        units = _parse_braced(source, lang)
    else:
        units = _PARSERS[lang](source)
    return {
        "parser_version": "1.0",
        "origin_signature": ORIGIN_SIGNATURE,
        "lang": lang,
        "raw_checksum": _sha256(source),
        "unit_count": len(units),
        "units": units,
    }
