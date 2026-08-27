#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mrl_librarian.py — MRL System Librarian Worker
origin_signature: MrLiouWord
layer: L6 REFLECT + L7 LOOP

Indexes every tracked file in the repo using the T/X/Y/Z four-dimensional
coordinate system, then exposes search and query helpers so any module can
locate its peers without full-directory scans.

Dimensions
----------
T — Temporal state   : principle | spec | prototype | runnable | entry
X — Layer            : L0 | L1 | L2 | L3 | L4 | L5 | L6 | L7 | MetaEnv | Platform
Y — Core group       : 1=MotherCore | 2=ParticleReversible | 3=FlowAgent |
                       4=WorldModule | 5=FileIndex | 6=PersonaHistory
Z — Relation depth   : 0=standalone | 1=linked | 2=hub

Usage
-----
    python 09_workflow/mrl_librarian.py index   # rebuild index
    python 09_workflow/mrl_librarian.py search --layer L3
    python 09_workflow/mrl_librarian.py search --group 3
    python 09_workflow/mrl_librarian.py search --state runnable
    python 09_workflow/mrl_librarian.py query --path 03_memory/merkle/memory_chain.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import time
from typing import Any, Dict, List, Optional

# ─── Repository root (two levels up from this file) ──────────────────────────

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_INDEX_PATH = _REPO_ROOT / "data" / "librarian_index.json"

# ─── Static classification table ─────────────────────────────────────────────
# Maps directory prefix → (X layer, Y core-group, T default state)
_DIR_CLASSIFICATION: List[tuple[str, str, int, str]] = [
    ("00_rootlaw",    "L0",      1, "spec"),
    ("01_schema",     "L1",      1, "spec"),
    ("02_principles", "L3",      1, "spec"),
    ("03_memory",     "L6",      2, "runnable"),
    ("04_runtime",    "L7",      3, "runnable"),
    ("05_persona",    "L4",      4, "prototype"),
    ("06_trace",      "L6",      5, "runnable"),
    ("07_ingest",     "L2",      5, "spec"),
    ("08_sources",    "L0",      5, "spec"),
    ("09_workflow",   "L7",      3, "runnable"),
    ("data",          "MetaEnv", 5, "spec"),
    ("ui",            "Platform",6, "prototype"),
]

# Fine-grained overrides keyed on file path patterns (relative to repo root)
_PATH_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "00_rootlaw/rootlaw.yaml":           {"T": "spec",     "Y": 1, "Z": 2},
    "03_memory/merkle/memory_chain.py":  {"T": "runnable", "Y": 2, "Z": 1},
    "03_memory/vector/vector_store.py":  {"T": "runnable", "Y": 2, "Z": 1},
    "04_runtime/flowcore_loop.py":       {"T": "runnable", "Y": 3, "Z": 2},
    "04_runtime/runtime_manifest.yaml":  {"T": "spec",     "Y": 3, "Z": 2},
    "05_persona/world_module.py":        {"T": "prototype","Y": 4, "Z": 1},
    "09_workflow/api.js":                {"T": "runnable", "Y": 3, "Z": 2},
    "09_workflow/signature.js":          {"T": "runnable", "Y": 1, "Z": 1},
    "09_workflow/seed.js":               {"T": "runnable", "Y": 2, "Z": 1},
    "09_workflow/fltnz_parser.py":       {"X": "L2", "T": "runnable", "Y": 2, "Z": 2},
    "09_workflow/mrl_librarian.py":      {"T": "entry",    "Y": 5, "Z": 2},
    "09_workflow/MRL__Flowcore_Loop_2.py": {"T": "runnable","Y": 3, "Z": 2},
    "09_workflow/tool_registry.py":      {"T": "runnable", "Y": 3, "Z": 1},
    "09_workflow/prompt_template.py":    {"T": "runnable", "Y": 3, "Z": 1},
    "09_workflow/agent_planner.py":      {"T": "runnable", "Y": 3, "Z": 2},
    "09_workflow/eval_engine.py":        {"T": "runnable", "Y": 5, "Z": 1},
    "09_workflow/plugin_manager.py":     {"T": "runnable", "Y": 3, "Z": 1},
    "09_workflow/MRL_mother_assembly.py":    {"T": "entry",    "Y": 1, "Z": 2},
    "data/relations/module_relations.yaml": {"T": "spec",  "Y": 5, "Z": 2},
    "data/master/master_summary_v1.3.md":   {"T": "spec",  "Y": 1, "Z": 1},
}

# Directories and extensions to skip
_SKIP_DIRS = {".git", "__pycache__", "node_modules", "_data", "vector", "approvals"}
_SKIP_EXTS = {".pyc", ".pyo", ".log", ".jsonl"}


def _sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _classify(rel: pathlib.PurePosixPath) -> Dict[str, Any]:
    rel_str = rel.as_posix()

    # Fine-grained override wins
    if rel_str in _PATH_OVERRIDES:
        override = _PATH_OVERRIDES[rel_str]
        # X layer: use explicit override if present, otherwise derive from directory
        if "X" in override:
            x_layer = override["X"]
        else:
            x_layer = "L7"
            for prefix, xl, _y, _t in _DIR_CLASSIFICATION:
                if rel_str.startswith(prefix + "/") or rel_str == prefix:
                    x_layer = xl
                    break
        return {
            "X": x_layer,
            "Y": override.get("Y", 1),
            "T": override.get("T", "spec"),
            "Z": override.get("Z", 0),
        }

    for prefix, x_layer, y_group, t_state in _DIR_CLASSIFICATION:
        if rel_str.startswith(prefix + "/") or rel_str == prefix:
            return {"X": x_layer, "Y": y_group, "T": t_state, "Z": 0}

    return {"X": "L7", "Y": 1, "T": "spec", "Z": 0}


def build_index(repo_root: pathlib.Path = _REPO_ROOT) -> Dict[str, Any]:
    """Walk the repository and produce a TXYZ-indexed catalogue."""
    entries: List[Dict[str, Any]] = []
    ts = int(time.time() * 1000)

    for dirpath, dirnames, filenames in os.walk(repo_root):
        # Prune unwanted directories in-place
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]

        for fname in filenames:
            fpath = pathlib.Path(dirpath) / fname
            if fpath.suffix in _SKIP_EXTS:
                continue
            # .gitkeep placeholders are not worth indexing
            if fname == ".gitkeep":
                continue

            rel = fpath.relative_to(repo_root).as_posix()
            coords = _classify(pathlib.PurePosixPath(rel))

            entry: Dict[str, Any] = {
                "path": rel,
                "X": coords["X"],
                "Y": coords["Y"],
                "T": coords["T"],
                "Z": coords["Z"],
                "size_bytes": fpath.stat().st_size,
                "sha256": _sha256_file(fpath),
            }
            entries.append(entry)

    index = {
        "meta": {
            "version": "1.0",
            "origin_signature": "MrLiouWord",
            "generated_at_ms": ts,
            "repo_root": str(repo_root),
            "total_files": len(entries),
        },
        "entries": sorted(entries, key=lambda e: e["path"]),
    }
    return index


def save_index(index: Dict[str, Any], out_path: pathlib.Path = _INDEX_PATH) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def load_index(index_path: pathlib.Path = _INDEX_PATH) -> Optional[Dict[str, Any]]:
    if not index_path.exists():
        return None
    with index_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def search(
    index: Dict[str, Any],
    *,
    layer: Optional[str] = None,
    group: Optional[int] = None,
    state: Optional[str] = None,
    path_contains: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter index entries by one or more TXYZ dimensions."""
    results = index.get("entries", [])
    if layer:
        results = [e for e in results if e["X"] == layer]
    if group is not None:
        results = [e for e in results if e["Y"] == group]
    if state:
        results = [e for e in results if e["T"] == state]
    if path_contains:
        results = [e for e in results if path_contains in e["path"]]
    return results


def query_path(index: Dict[str, Any], rel_path: str) -> Optional[Dict[str, Any]]:
    """Return the single index entry for a given relative path, or None."""
    for e in index.get("entries", []):
        if e["path"] == rel_path:
            return e
    return None


# ─── rl_11 對外邊界稽核（Origin Boundary Guard 整合，additive）────────────────
#   特別標註：以下為 rl_11 源頭主權於 librarian 的 enforcement 掛點。
#   不改動既有索引行為；僅新增「外部殼名稽核」能力——掃描索引中非 MRL_ 前綴的
#   名稱（rl_16 不可顯化），並給出 rl_12 正名建議。守衛實作於
#   MRL_OriginBoundary_Guard_v1（rl_11/rl_12/rl_16/rl_17 + LAW-0 簽章）。
def boundary_audit(index: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """rl_11：稽核索引內所有檔名,標出外部殼(非 MRL_)並建議 canonical 正名。"""
    from MRL_OriginBoundary_Guard_v1 import scan_for_boundary_violations  # noqa: PLC0415
    idx = index if index is not None else load_index()
    if idx is None:
        return {"error": "no index; run: python mrl_librarian.py index"}
    # 只取檔名(basename)做顯化前綴判定;路徑分類由既有 TXYZ 索引負責
    names = [pathlib.PurePosixPath(e["path"]).name for e in idx.get("entries", [])]
    return scan_for_boundary_violations(names)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_index(_args: argparse.Namespace) -> None:
    print("Building librarian index …")
    idx = build_index()
    save_index(idx)
    print(f"✅ Index written → {_INDEX_PATH}  ({idx['meta']['total_files']} files)")


def _cmd_search(args: argparse.Namespace) -> None:
    idx = load_index()
    if idx is None:
        print("No index found. Run: python mrl_librarian.py index")
        return
    results = search(
        idx,
        layer=args.layer,
        group=args.group,
        state=args.state,
        path_contains=args.contains,
    )
    print(f"Found {len(results)} file(s):")
    for e in results:
        print(f"  [{e['X']}] [Y={e['Y']}] [T={e['T']}] [Z={e['Z']}]  {e['path']}")


def _cmd_query(args: argparse.Namespace) -> None:
    idx = load_index()
    if idx is None:
        print("No index found. Run: python mrl_librarian.py index")
        return
    entry = query_path(idx, args.path)
    if entry is None:
        print(f"Path not found in index: {args.path}")
    else:
        print(json.dumps(entry, ensure_ascii=False, indent=2))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MRL Librarian — TXYZ file index worker")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index", help="Rebuild the TXYZ index")

    sp = sub.add_parser("search", help="Search index by TXYZ dimensions")
    sp.add_argument("--layer", help="Filter by X layer (e.g. L3, L7, MetaEnv)")
    sp.add_argument("--group", type=int, help="Filter by Y core group (1–6)")
    sp.add_argument("--state", help="Filter by T state (principle/spec/prototype/runnable/entry)")
    sp.add_argument("--contains", help="Filter paths containing this substring")

    qp = sub.add_parser("query", help="Look up a single path in the index")
    qp.add_argument("--path", required=True, help="Relative path from repo root")

    # rl_11 對外邊界稽核
    sub.add_parser("boundary", help="rl_11 audit: flag external-shell names, suggest MRL_ reclaim")

    return p


def _cmd_boundary(_args: argparse.Namespace) -> None:
    rep = boundary_audit()
    print(json.dumps(rep, ensure_ascii=False, indent=2))


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    if args.cmd == "index":
        _cmd_index(args)
    elif args.cmd == "search":
        _cmd_search(args)
    elif args.cmd == "query":
        _cmd_query(args)
    elif args.cmd == "boundary":
        _cmd_boundary(args)


if __name__ == "__main__":
    main()
