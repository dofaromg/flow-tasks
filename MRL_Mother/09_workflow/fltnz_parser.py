#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fltnz_parser.py — Bidirectional .fltnz ↔ .txt reversible chain parser
origin_signature: MrLiouWord
layer: L2 PARTICLE + L7 LOOP

Design principle: 怎麼過去，就怎麼回來 (the path forward is the path back)

Reversible chain
----------------
  txt  ──encode──▶  fltnz  ──expand──▶  map  ──pack──▶  flpkg  ──seal──▶  trace
  txt  ◀──decode──  fltnz  ◀──compact── map  ◀──unpack── flpkg  ◀──unseal── trace

Format spec (.fltnz)
--------------------
A .fltnz file is a UTF-8 JSON envelope with the following top-level keys:

  {
    "fltnz_version": "1.0",
    "origin_signature": "MrLiouWord",
    "encoding": "utf-8",
    "checksum": "<sha256 of raw text bytes>",
    "length": <original byte length>,
    "tokens": [ ... ]   // particle-token list
  }

Each token in the list is one of:
  { "t": "word",  "v": "<word>" }
  { "t": "ws",   "v": "<whitespace>" }
  { "t": "nl",   "v": "\\n" }
  { "t": "ref",  "v": <index> }   // back-reference to earlier token by index

Usage
-----
    python 09_workflow/fltnz_parser.py encode --src README.md --dst /tmp/readme.fltnz
    python 09_workflow/fltnz_parser.py decode --src /tmp/readme.fltnz --dst /tmp/readme_restored.txt
    python 09_workflow/fltnz_parser.py verify --src /tmp/readme.fltnz
    python 09_workflow/fltnz_parser.py pack   --src /tmp/readme.fltnz --dst /tmp/readme.flpkg
    python 09_workflow/fltnz_parser.py unpack --src /tmp/readme.flpkg --dst /tmp/readme_out.fltnz
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import time
from typing import Any, Dict, List, Optional, Tuple

FLTNZ_VERSION = "1.0"
ORIGIN_SIGNATURE = "MrLiouWord"

# ─── Tokeniser ───────────────────────────────────────────────────────────────

_TOKEN_RE = re.compile(r"(\n|\r\n|\r|[ \t]+|\S+)")


def _tokenise(text: str) -> List[Dict[str, Any]]:
    """Split *text* into a flat list of typed raw tokens (no back-refs yet)."""
    tokens: List[Dict[str, Any]] = []
    for m in _TOKEN_RE.finditer(text):
        val = m.group(0)
        if val in ("\n", "\r\n", "\r"):
            tokens.append({"t": "nl", "v": "\n"})
        elif val.strip() == "":
            tokens.append({"t": "ws", "v": val})
        else:
            tokens.append({"t": "word", "v": val})
    return tokens


def _compress_tokens(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Replace repeated tokens with back-references (position index)."""
    seen: Dict[str, int] = {}
    compressed: List[Dict[str, Any]] = []
    for i, tok in enumerate(raw):
        key = f"{tok['t']}:{tok['v']}"
        if key in seen and tok["t"] == "word":
            compressed.append({"t": "ref", "v": seen[key]})
        else:
            seen[key] = i
            compressed.append(tok)
    return compressed


def _decompress_tokens(tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Resolve back-references into their original token values."""
    resolved: List[Dict[str, Any]] = []
    for tok in tokens:
        if tok["t"] == "ref":
            idx = tok["v"]
            if idx < len(resolved):
                resolved.append(dict(resolved[idx]))
            else:
                raise ValueError(f"fltnz: back-reference {idx} out of range")
        else:
            resolved.append(tok)
    return resolved


def _tokens_to_text(tokens: List[Dict[str, Any]]) -> str:
    return "".join(t["v"] for t in tokens)


# ─── Checksum ────────────────────────────────────────────────────────────────

def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ─── Encode / Decode ─────────────────────────────────────────────────────────

def encode(text: str) -> Dict[str, Any]:
    """Convert plain *text* → .fltnz envelope dict."""
    raw_tokens = _tokenise(text)
    compressed = _compress_tokens(raw_tokens)
    return {
        "fltnz_version": FLTNZ_VERSION,
        "origin_signature": ORIGIN_SIGNATURE,
        "encoding": "utf-8",
        "checksum": _sha256_text(text),
        "length": len(text.encode("utf-8")),
        "tokens": compressed,
    }


def decode(envelope: Dict[str, Any]) -> str:
    """Convert .fltnz envelope dict → original plain text."""
    tokens = envelope.get("tokens", [])
    resolved = _decompress_tokens(tokens)
    text = _tokens_to_text(resolved)
    # Integrity check
    expected = envelope.get("checksum", "")
    if expected and _sha256_text(text) != expected:
        raise ValueError("fltnz: checksum mismatch — chain integrity violation")
    return text


# ─── Map layer ───────────────────────────────────────────────────────────────

def to_map(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expand a .fltnz envelope into a .map structure.

    The map layer groups tokens by type and adds positional metadata so
    downstream modules can navigate without decoding the full text.
    """
    resolved = _decompress_tokens(envelope.get("tokens", []))
    word_positions: Dict[str, List[int]] = {}
    for i, tok in enumerate(resolved):
        if tok["t"] == "word":
            word_positions.setdefault(tok["v"], []).append(i)

    return {
        "map_version": "1.0",
        "origin_signature": ORIGIN_SIGNATURE,
        "source_checksum": envelope.get("checksum"),
        "total_tokens": len(resolved),
        "word_count": sum(1 for t in resolved if t["t"] == "word"),
        "unique_words": len(word_positions),
        "word_positions": word_positions,
    }


def from_map(
    map_obj: Dict[str, Any], envelope: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compact a .map back to its originating .fltnz envelope.

    Since the map only stores positional metadata (not the token stream),
    the original envelope is required for lossless reconstruction.
    """
    if map_obj.get("source_checksum") != envelope.get("checksum"):
        raise ValueError("fltnz: map source_checksum does not match envelope checksum")
    return envelope


# ─── Pack / Unpack (.flpkg) ──────────────────────────────────────────────────

def pack(envelope: Dict[str, Any], label: str = "unnamed") -> Dict[str, Any]:
    """Seal a .fltnz envelope into a .flpkg bundle."""
    return {
        "flpkg_version": "1.0",
        "origin_signature": ORIGIN_SIGNATURE,
        "label": label,
        "created_at_ms": int(time.time() * 1000),
        "payload": envelope,
        "payload_type": "fltnz",
    }


def unpack(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the .fltnz envelope from a .flpkg bundle."""
    if bundle.get("payload_type") != "fltnz":
        raise ValueError("flpkg: payload_type is not 'fltnz'")
    return bundle["payload"]


# ─── Trace seal / unseal ─────────────────────────────────────────────────────

def seal(bundle: Dict[str, Any], event_type: str = "flpkg_seal") -> Dict[str, Any]:
    """
    Produce a trace record from a .flpkg bundle.

    The trace is the outermost wrapper in the chain and is compatible with
    the existing MerkleChain payload format (03_memory/merkle/memory_chain.py).
    """
    bundle_bytes = json.dumps(bundle, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return {
        "event_type": event_type,
        "origin_signature": ORIGIN_SIGNATURE,
        "layer": "L2",
        "sealed_at_ms": int(time.time() * 1000),
        "bundle_checksum": hashlib.sha256(bundle_bytes).hexdigest(),
        "bundle": bundle,
    }


def unseal(trace_record: Dict[str, Any]) -> Dict[str, Any]:
    """Recover the .flpkg bundle from a trace record and verify its checksum."""
    bundle = trace_record.get("bundle", {})
    bundle_bytes = json.dumps(bundle, ensure_ascii=False, sort_keys=True).encode("utf-8")
    computed = hashlib.sha256(bundle_bytes).hexdigest()
    if computed != trace_record.get("bundle_checksum", ""):
        raise ValueError("trace: bundle_checksum mismatch — chain integrity violation")
    return bundle


# ─── Full-chain helpers ───────────────────────────────────────────────────────

def text_to_trace(text: str, label: str = "unnamed") -> Dict[str, Any]:
    """txt → fltnz → flpkg → trace (full forward chain)."""
    return seal(pack(encode(text), label=label))


def trace_to_text(trace_record: Dict[str, Any]) -> str:
    """trace → flpkg → fltnz → txt (full reverse chain)."""
    return decode(unpack(unseal(trace_record)))


# ─── File I/O helpers ─────────────────────────────────────────────────────────

def _read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: pathlib.Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_encode(args: argparse.Namespace) -> None:
    text = _read_text(pathlib.Path(args.src))
    envelope = encode(text)
    dst = pathlib.Path(args.dst)
    _write_json(dst, envelope)
    print(f"✅ Encoded → {dst}")


def _cmd_decode(args: argparse.Namespace) -> None:
    envelope = _read_json(pathlib.Path(args.src))
    text = decode(envelope)
    dst = pathlib.Path(args.dst)
    _write_text(dst, text)
    print(f"✅ Decoded → {dst}")


def _cmd_verify(args: argparse.Namespace) -> None:
    envelope = _read_json(pathlib.Path(args.src))
    try:
        text = decode(envelope)
        print(f"✅ Checksum valid  (length={len(text)} chars)")
    except ValueError as exc:
        print(f"❌ Verification failed: {exc}")


def _cmd_pack(args: argparse.Namespace) -> None:
    envelope = _read_json(pathlib.Path(args.src))
    label = args.label or pathlib.Path(args.src).stem
    bundle = pack(envelope, label=label)
    dst = pathlib.Path(args.dst)
    _write_json(dst, bundle)
    print(f"✅ Packed → {dst}")


def _cmd_unpack(args: argparse.Namespace) -> None:
    bundle = _read_json(pathlib.Path(args.src))
    envelope = unpack(bundle)
    dst = pathlib.Path(args.dst)
    _write_json(dst, envelope)
    print(f"✅ Unpacked → {dst}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="fltnz — bidirectional txt↔fltnz↔map↔flpkg↔trace chain parser"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encode", help="txt → .fltnz")
    enc.add_argument("--src", required=True)
    enc.add_argument("--dst", required=True)

    dec = sub.add_parser("decode", help=".fltnz → txt")
    dec.add_argument("--src", required=True)
    dec.add_argument("--dst", required=True)

    ver = sub.add_parser("verify", help="Verify .fltnz checksum")
    ver.add_argument("--src", required=True)

    pk = sub.add_parser("pack", help=".fltnz → .flpkg")
    pk.add_argument("--src", required=True)
    pk.add_argument("--dst", required=True)
    pk.add_argument("--label", default="")

    up = sub.add_parser("unpack", help=".flpkg → .fltnz")
    up.add_argument("--src", required=True)
    up.add_argument("--dst", required=True)

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "encode": _cmd_encode,
        "decode": _cmd_decode,
        "verify": _cmd_verify,
        "pack":   _cmd_pack,
        "unpack": _cmd_unpack,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
