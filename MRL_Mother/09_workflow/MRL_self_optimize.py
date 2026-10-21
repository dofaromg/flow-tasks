#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRL_self_optimize.py — Self optimisation and growth (config-level)

origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
layer: L6 REFLECT
group: Y=1 MotherCore

Mainstream production pattern
-----------------------------
This module implements *self optimisation* in the mainstream, production-safe
way: the system adapts by tuning configuration (feature flags, concurrency,
chunking parameters) based on environment signals (CPU/RAM/disk), rather than
rewriting source code.

All changes are:
  - gated to the canonical host (DL580)
  - persisted via ConfigManager (data/config.json)
  - sealed into MerkleChain for auditability and rollback proofs
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import time
from typing import Any, Dict, Tuple

from MRL_utils import ORIGIN_SIGNATURE
PRODUCT_NAME = "MRL_AI_SYSTEM"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _ensure_paths() -> None:
    import sys

    for sub in [
        _REPO_ROOT / "09_workflow",
        _REPO_ROOT / "03_memory" / "merkle",
    ]:
        p = str(sub)
        if p not in sys.path:
            sys.path.insert(0, p)


_ensure_paths()


def _require_dl580() -> Tuple[bool, str]:
    try:
        from MRL_host_guard import is_dl580_canonical_host
    except Exception:  # noqa: BLE001
        return False, "MRL_host_guard unavailable"
    return is_dl580_canonical_host()


def sense_environment() -> Dict[str, Any]:
    cpu = os.cpu_count() or 1
    disk = shutil.disk_usage(str(_REPO_ROOT))
    env: Dict[str, Any] = {
        "cpu_count": int(cpu),
        "disk_total_bytes": int(disk.total),
        "disk_free_bytes": int(disk.free),
        "disk_used_bytes": int(disk.used),
    }

    # Best-effort memory detection without extra dependencies
    mem_total = None
    try:
        if hasattr(os, "sysconf"):
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            mem_total = int(pages) * int(page_size)
    except Exception:
        pass
    if mem_total is not None:
        env["mem_total_bytes"] = mem_total

    return env


def _recommend(env: Dict[str, Any]) -> Dict[str, Any]:
    cpu = int(env.get("cpu_count") or 1)
    mem = int(env.get("mem_total_bytes") or 0)

    # workers: keep conservative; mainstream default is small and scales with CPU
    workers = max(1, min(8, cpu))

    # chunking: increase modestly with memory
    chunk_chars = 1200
    overlap = 180
    if mem >= 8 * 1024**3:
        chunk_chars = 1600
        overlap = 220
    if mem >= 16 * 1024**3:
        chunk_chars = 2000
        overlap = 260

    top_k = 5
    if cpu >= 8:
        top_k = 8

    return {
        "scheduler.workers": workers,
        "learning.chunk_chars": chunk_chars,
        "learning.overlap": overlap,
        "learning.top_k": top_k,
    }


def _seal_change(env: Dict[str, Any], changes: Dict[str, Any]) -> Dict[str, Any]:
    from memory_chain import MerkleChain

    chain = MerkleChain(_REPO_ROOT / "03_memory" / "_data" / "memory_chain")
    payload = {
        "type": "self_optimize",
        "env": env,
        "changes": changes,
        "origin_signature": ORIGIN_SIGNATURE,
        "product_name": PRODUCT_NAME,
        "ts_ms": int(time.time() * 1000),
    }
    entry = chain.commit(payload, tags=["self_optimize"], layer="L6", meta={"origin_signature": ORIGIN_SIGNATURE})
    return {"entry_id": entry.entry_id, "merkle": entry.merkle}


def run(apply: bool) -> Dict[str, Any]:
    ok, err = _require_dl580()
    if not ok:
        return {"ok": False, "error": f"DL580_ONLY: {err}"}

    from config_manager import ConfigManager

    cfg = ConfigManager()
    if not bool(cfg.get("self_optimize.enabled", False)):
        return {"ok": False, "error": "self_optimize.enabled=false"}

    env = sense_environment()
    rec = _recommend(env)

    result: Dict[str, Any] = {
        "ok": True,
        "apply": bool(apply),
        "recommended": rec,
        "sealed": {},
    }

    if apply and bool(cfg.get("self_optimize.apply", False)):
        for k, v in rec.items():
            cfg.set(k, v)
        cfg.set("self_optimize.last_run_at_ms", int(time.time() * 1000))
        cfg.save()
        result["applied"] = True
    else:
        result["applied"] = False

    result["sealed"] = _seal_change(env, {"applied": result["applied"], "recommended": rec})
    return result


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MRL self optimisation (config-level)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sense", help="Print environment signals")

    r = sub.add_parser("run", help="Recommend and optionally apply config changes")
    r.add_argument("--apply", action="store_true")
    return p


def main() -> None:
    args = _build_argparser().parse_args()
    if args.cmd == "sense":
        ok, err = _require_dl580()
        if not ok:
            print(json.dumps({"ok": False, "error": f"DL580_ONLY: {err}"}, ensure_ascii=False, indent=2))
            return
        print(json.dumps({"ok": True, "env": sense_environment()}, ensure_ascii=False, indent=2))
        return
    if args.cmd == "run":
        print(json.dumps(run(apply=bool(args.apply)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

