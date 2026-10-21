#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRL_learning_ingest.py — Learning ingest pipeline (local/web/git)

origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
layer: L6 REFLECT
group: Y=5 FileIndexGovernance

Purpose
-------
Provide a production-usable ingest→normalise→chunk→index→seal pipeline so the
system can absorb external technical knowledge into its vector store while
keeping a tamper-evident manifest sealed in the MerkleChain.

Design principle: 怎麼過去，就怎麼回來
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import time
import urllib.request
import uuid
from typing import Any, Dict, Iterable, List, Optional, Tuple

from MRL_utils import ORIGIN_SIGNATURE
PRODUCT_NAME = "MRL_AI_SYSTEM"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DATA_ROOT = _REPO_ROOT / "data" / "learning"
_RAW_ROOT = _DATA_ROOT / "raw"
_MANIFEST_ROOT = _DATA_ROOT / "manifests"


def _ensure_paths() -> None:
    import sys

    for sub in [
        _REPO_ROOT / "03_memory" / "vector",
        _REPO_ROOT / "03_memory" / "merkle",
    ]:
        p = str(sub)
        if p not in sys.path:
            sys.path.insert(0, p)


_ensure_paths()


def _require_dl580_persistence() -> Tuple[bool, str]:
    try:
        from MRL_host_guard import is_dl580_canonical_host
    except Exception:  # noqa: BLE001
        return False, "MRL_host_guard unavailable"
    return is_dl580_canonical_host()


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_text(s: str) -> str:
    return _sha256_bytes(s.encode("utf-8"))


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_text_file(path: pathlib.Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp950", "big5", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _strip_html(html: str) -> str:
    html = re.sub(r"(?is)<script.*?>.*?</script>", "\n", html)
    html = re.sub(r"(?is)<style.*?>.*?</style>", "\n", html)
    html = re.sub(r"(?s)<[^>]+>", "\n", html)
    html = html.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


def _chunk_text(text: str, chunk_chars: int = 1400, overlap: int = 200) -> List[str]:
    t = re.sub(r"\r\n?", "\n", text).strip()
    if not t:
        return []
    if chunk_chars <= 0:
        return [t]
    if overlap < 0:
        overlap = 0
    if overlap >= chunk_chars:
        overlap = 0
    chunks: List[str] = []
    i = 0
    n = len(t)
    while i < n:
        j = min(n, i + chunk_chars)
        chunks.append(t[i:j])
        if j == n:
            break
        i = max(0, j - overlap)
    return chunks


def _chunk_hash(text: str) -> str:
    return _sha256_text(text.strip())


def _is_self_repo_path(p: pathlib.Path) -> bool:
    try:
        rp = p.resolve()
    except Exception:
        return False
    try:
        root = _REPO_ROOT.resolve()
    except Exception:
        root = _REPO_ROOT
    return root == rp or root in rp.parents


def _embed_text_simple(text: str, dim: int = 128) -> List[float]:
    """Deterministic, dependency-free embedding.

    This is not SOTA, but it enables production persistence/query without
    adding new dependencies. It can be replaced by a real embedder later.
    """
    if dim <= 0:
        dim = 128
    vec = [0.0] * dim
    for tok in re.findall(r"[A-Za-z0-9_]+|[^\s]", text.lower()):
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        idx = int.from_bytes(h[:2], "big") % dim
        sign = 1.0 if (h[2] & 1) else -1.0
        vec[idx] += sign
    norm = sum(x * x for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def _write_raw(source_type: str, source_id: str, text: str) -> pathlib.Path:
    date_dir = time.strftime("%Y-%m-%d", time.gmtime())
    out_dir = _RAW_ROOT / source_type / date_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{source_id}.txt"
    out_path.write_text(text, encoding="utf-8")
    return out_path


def _write_manifest(source_id: str, manifest: Dict[str, Any]) -> pathlib.Path:
    _MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = _MANIFEST_ROOT / f"{source_id}.json"
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, out_path)
    return out_path


def _seal_manifest_summary(source_id: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
    from memory_chain import MerkleChain

    chain = MerkleChain(_REPO_ROOT / "03_memory" / "_data" / "memory_chain")
    summary = {
        "type": "learning_ingest",
        "source_id": source_id,
        "source_type": manifest.get("source", {}).get("type"),
        "source_ref": manifest.get("source", {}).get("ref"),
        "content_sha256": manifest.get("content", {}).get("sha256"),
        "chunks": manifest.get("chunks", {}).get("count"),
        "vector_entries": manifest.get("vector", {}).get("count"),
        "manifest_sha256": _sha256_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True)),
        "created_at": manifest.get("created_at"),
        "origin_signature": ORIGIN_SIGNATURE,
        "product_name": PRODUCT_NAME,
    }
    entry = chain.commit(
        summary,
        tags=["learning", "ingest"],
        layer="L6",
        meta={"origin_signature": ORIGIN_SIGNATURE},
    )
    return {"merkle": entry.merkle, "entry_id": entry.entry_id}


def ingest_text(
    *,
    source_type: str,
    source_ref: str,
    text: str,
    label: str = "",
    chunk_chars: int = 1400,
    overlap: int = 200,
    store_raw: bool = True,
) -> Dict[str, Any]:
    ok_host, err_host = _require_dl580_persistence()
    if not ok_host:
        return {"ok": False, "error": f"DL580_ONLY: {err_host}"}
    from vector_store import VectorStore

    source_id = _sha256_text(f"{source_type}:{source_ref}:{_sha256_text(text)}")[:24]
    chunks = _chunk_text(text, chunk_chars=chunk_chars, overlap=overlap)
    created_at = _now_iso()
    raw_path = ""
    if store_raw:
        raw_path = str(_write_raw(source_type, source_id, text).relative_to(_REPO_ROOT))

    vs = VectorStore()
    vector_ids: List[str] = []
    chunk_hashes: List[str] = []
    deduped = 0
    for idx, ch in enumerate(chunks):
        chash = _chunk_hash(ch)
        chunk_hashes.append(chash)
        doc_id = f"learn:chunk:{chash}"
        if vs.get(doc_id) is not None:
            deduped += 1
            continue
        meta = {
            "type": "learning_chunk",
            "source_type": source_type,
            "source_ref": source_ref,
            "source_id": source_id,
            "chunk_index": idx,
            "chunk_hash": chash,
            "label": label,
            "created_at": created_at,
            "origin_signature": ORIGIN_SIGNATURE,
            "product_name": PRODUCT_NAME,
        }
        vs.add(doc_id, _embed_text_simple(ch), meta)
        vector_ids.append(doc_id)

    manifest: Dict[str, Any] = {
        "origin_signature": ORIGIN_SIGNATURE,
        "product_name": PRODUCT_NAME,
        "created_at": created_at,
        "source": {"type": source_type, "ref": source_ref, "id": source_id, "label": label},
        "content": {"sha256": _sha256_text(text), "chars": len(text)},
        "chunks": {"count": len(chunks), "chunk_chars": chunk_chars, "overlap": overlap},
        "composition": {
            "source_id": source_id,
            "chunk_hashes": chunk_hashes,
            "deduped": deduped,
        },
        "raw": {"stored": bool(raw_path), "path": raw_path},
        "vector": {
            "store": "03_memory/_data/vector_store.json",
            "count": len(vector_ids),
            "ids": vector_ids,
            "id_scheme": "learn:chunk:{sha256}",
        },
        "seal": {},
    }
    manifest_path = _write_manifest(source_id, manifest)
    seal = _seal_manifest_summary(source_id, manifest)
    manifest["seal"] = seal
    _write_manifest(source_id, manifest)
    return {
        "ok": True,
        "source_id": source_id,
        "manifest_path": str(manifest_path.relative_to(_REPO_ROOT)),
        "sealed": seal,
        "chunks": len(chunks),
        "vector_entries": len(vector_ids),
    }


def ingest_path(path: str, *, label: str = "", **kwargs: Any) -> Dict[str, Any]:
    ok_host, err_host = _require_dl580_persistence()
    if not ok_host:
        return {"ok": False, "error": f"DL580_ONLY: {err_host}"}
    p = pathlib.Path(path)
    if not p.exists():
        return {"ok": False, "error": f"path not found: {path}"}
    if _is_self_repo_path(p):
        return {"ok": False, "error": "SELF_REPO_BLOCKED"}
    if p.is_dir():
        # minimal safe scan: only small text-like files
        texts: List[Tuple[str, str]] = []
        for fp in sorted(p.rglob("*")):
            if not fp.is_file():
                continue
            if fp.name.startswith("."):
                continue
            if fp.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".tar", ".mp4", ".mov"}:
                continue
            try:
                txt = _read_text_file(fp)
            except Exception:
                continue
            texts.append((str(fp), txt))
        if not texts:
            return {"ok": False, "error": f"no ingestible files under: {path}"}
        combined = "\n\n".join([f"# FILE: {fp}\n{txt}" for fp, txt in texts])
        return ingest_text(source_type="local_path", source_ref=str(p.resolve()), text=combined, label=label, **kwargs)

    txt = _read_text_file(p)
    return ingest_text(source_type="local_path", source_ref=str(p.resolve()), text=txt, label=label, **kwargs)


def ingest_url(url: str, *, label: str = "", timeout_s: int = 15, **kwargs: Any) -> Dict[str, Any]:
    ok_host, err_host = _require_dl580_persistence()
    if not ok_host:
        return {"ok": False, "error": f"DL580_ONLY: {err_host}"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MRL_AI_SYSTEM/learning"})
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
            ctype = (resp.headers.get("Content-Type") or "").lower()
        text = raw.decode("utf-8", errors="replace")
        if "text/html" in ctype or "<html" in text.lower():
            text = _strip_html(text)
        return ingest_text(source_type="web_url", source_ref=url, text=text, label=label, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "source": {"type": "web_url", "ref": url}}


def query(q: str, *, k: int = 5) -> Dict[str, Any]:
    ok_host, err_host = _require_dl580_persistence()
    if not ok_host:
        return {"ok": False, "error": f"DL580_ONLY: {err_host}"}
    from vector_store import VectorStore

    if not q:
        return {"ok": False, "error": "q is required"}
    vs = VectorStore()
    hits = vs.query(_embed_text_simple(q), top_k=int(k))
    out = []
    for doc_id, score, meta in hits:
        safe_meta = dict(meta or {})
        safe_meta.pop("text", None)
        out.append({"id": doc_id, "score": score, "meta": safe_meta})
    return {"ok": True, "q": q, "k": int(k), "hits": out}


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MRL learning ingest pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    ip = sub.add_parser("ingest_path", help="Ingest a local file or directory")
    ip.add_argument("--path", required=True)
    ip.add_argument("--label", default="")
    ip.add_argument("--chunk-chars", type=int, default=1400)
    ip.add_argument("--overlap", type=int, default=200)
    ip.add_argument("--no-raw", action="store_true")

    iu = sub.add_parser("ingest_url", help="Ingest a web URL (HTML will be stripped)")
    iu.add_argument("--url", required=True)
    iu.add_argument("--label", default="")
    iu.add_argument("--chunk-chars", type=int, default=1400)
    iu.add_argument("--overlap", type=int, default=200)
    iu.add_argument("--timeout", type=int, default=15)
    iu.add_argument("--no-raw", action="store_true")

    q = sub.add_parser("query", help="Query learned chunks")
    q.add_argument("--q", required=True)
    q.add_argument("--k", type=int, default=5)

    return p


def main() -> None:
    args = _build_argparser().parse_args()
    if args.cmd == "ingest_path":
        res = ingest_path(
            args.path,
            label=args.label,
            chunk_chars=args.chunk_chars,
            overlap=args.overlap,
            store_raw=not args.no_raw,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "ingest_url":
        res = ingest_url(
            args.url,
            label=args.label,
            chunk_chars=args.chunk_chars,
            overlap=args.overlap,
            timeout_s=args.timeout,
            store_raw=not args.no_raw,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.cmd == "query":
        res = query(args.q, k=args.k)
        print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
