#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vector_store.py — In-Memory Vector Store with Cosine Similarity (RAG-ready)
origin_signature: MrLiouWord
layer: L6 REFLECT
group: Y=2 ParticleReversible

Industry capability: Retrieval-Augmented Generation (RAG)
MRL extension: every vector entry is stamped with origin_signature and can be
               sealed into the MerkleChain for tamper-evident retrieval.

Usage
-----
    from vector_store import VectorStore

    vs = VectorStore()
    vs.add("doc1", [0.1, 0.9, 0.3], {"source": "README.md"})
    hits = vs.query([0.1, 0.8, 0.3], top_k=3)

CLI
---
    python 03_memory/vector/vector_store.py add  --id doc1 --vec "0.1,0.9,0.3"
    python 03_memory/vector/vector_store.py query --vec "0.1,0.8,0.3" --k 3
    python 03_memory/vector/vector_store.py list
    python 03_memory/vector/vector_store.py delete --id doc1
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import time
from typing import Any, Dict, List, Optional, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"
STORE_VERSION = "1.0"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DEFAULT_STORE = _REPO_ROOT / "03_memory" / "_data" / "vector_store.json"


# ─── Math helpers ─────────────────────────────────────────────────────────────

def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(v: List[float]) -> float:
    return math.sqrt(_dot(v, v))


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Return cosine similarity in [-1, 1]; returns 0 for zero vectors."""
    na, nb = _norm(a), _norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return _dot(a, b) / (na * nb)


# ─── VectorStore ──────────────────────────────────────────────────────────────

class VectorStore:
    """
    Lightweight in-memory vector store backed by a JSON file.

    Each entry:
        {
          "id":               <str>,
          "vector":           [float, ...],
          "meta":             {any JSON},
          "added_at_ms":      <int>,
          "origin_signature": "MrLiouWord"
        }

    Supports:
    - add / upsert entries
    - cosine-similarity top-k query
    - delete by id
    - persist to / load from JSON file
    """

    def __init__(self, store_path: pathlib.Path = _DEFAULT_STORE) -> None:
        self._path = pathlib.Path(store_path)
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._path.exists():
            with self._path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            for e in data.get("entries", []):
                self._entries[e["id"]] = e

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "store_version": STORE_VERSION,
            "origin_signature": ORIGIN_SIGNATURE,
            "total": len(self._entries),
            "entries": list(self._entries.values()),
        }
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def add(
        self,
        doc_id: str,
        vector: List[float],
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add or update an entry. Returns the stored entry."""
        entry: Dict[str, Any] = {
            "id": doc_id,
            "vector": [float(v) for v in vector],
            "meta": meta or {},
            "added_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }
        self._entries[doc_id] = entry
        self._save()
        return entry

    def delete(self, doc_id: str) -> bool:
        """Remove an entry by id. Returns True if it existed."""
        if doc_id in self._entries:
            del self._entries[doc_id]
            self._save()
            return True
        return False

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self._entries.get(doc_id)

    def list_ids(self) -> List[str]:
        return sorted(self._entries.keys())

    # ── Query ─────────────────────────────────────────────────────────────────

    def query(
        self,
        query_vector: List[float],
        top_k: int = 5,
        min_score: float = -1.0,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Return the *top_k* nearest entries by cosine similarity.

        Returns a list of (doc_id, score, meta) tuples, sorted descending.
        """
        q = [float(v) for v in query_vector]
        scored: List[Tuple[str, float, Dict[str, Any]]] = []
        for entry in self._entries.values():
            score = _cosine_similarity(q, entry["vector"])
            if score >= min_score:
                scored.append((entry["id"], score, entry["meta"]))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def __len__(self) -> int:
        return len(self._entries)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _parse_vec(s: str) -> List[float]:
    return [float(x.strip()) for x in s.split(",")]


def _cmd_add(args: argparse.Namespace) -> None:
    vs = VectorStore()
    meta = json.loads(args.meta) if args.meta else {}
    entry = vs.add(args.id, _parse_vec(args.vec), meta)
    print(f"✅ Added '{entry['id']}'  dim={len(entry['vector'])}  total={len(vs)}")


def _cmd_query(args: argparse.Namespace) -> None:
    vs = VectorStore()
    hits = vs.query(_parse_vec(args.vec), top_k=args.k)
    if not hits:
        print("No results.")
        return
    print(f"Top-{args.k} results:")
    for doc_id, score, meta in hits:
        print(f"  [{score:.4f}]  {doc_id}  meta={meta}")


def _cmd_list(_args: argparse.Namespace) -> None:
    vs = VectorStore()
    ids = vs.list_ids()
    print(f"{len(ids)} entries:")
    for doc_id in ids:
        e = vs.get(doc_id)
        print(f"  {doc_id}  dim={len(e['vector'])}")


def _cmd_delete(args: argparse.Namespace) -> None:
    vs = VectorStore()
    removed = vs.delete(args.id)
    print(f"{'✅ Deleted' if removed else '❌ Not found'}  '{args.id}'")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="VectorStore — cosine-similarity vector index")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="Add / update a vector entry")
    a.add_argument("--id", required=True)
    a.add_argument("--vec", required=True, help="Comma-separated floats, e.g. 0.1,0.9,0.3")
    a.add_argument("--meta", default="", help="JSON metadata string")

    q = sub.add_parser("query", help="Top-k cosine similarity query")
    q.add_argument("--vec", required=True, help="Query vector, comma-separated floats")
    q.add_argument("--k", type=int, default=5)

    sub.add_parser("list", help="List all stored entry ids")

    d = sub.add_parser("delete", help="Delete an entry by id")
    d.add_argument("--id", required=True)

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "add":    _cmd_add,
        "query":  _cmd_query,
        "list":   _cmd_list,
        "delete": _cmd_delete,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
