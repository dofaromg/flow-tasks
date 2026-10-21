#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRL_host_guard.py — DL580 canonical host enforcement

origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
layer: L3 LAW
group: Y=1 MotherCore

Mainstream pattern note
-----------------------
This module enforces a production-standard *trust boundary*:
only the canonical host (DL580) is allowed to perform learning persistence
operations. All other nodes may treat external inputs as learning materials but
must not mutate internal knowledge stores.

The system recognises exactly two roles:

  NodeRole.MOTHER
      Fully trusted primary node.  May mutate internal knowledge stores,
      seal Merkle events, and persist learning.  Determined by three
      independent checks (hostname + CIDR + fingerprint file).

  NodeRole.MATERIAL
      Every other host.  Can read and participate in workflows but all
      external file data are treated as *materials* — they inform the
      MOTHER but cannot modify authoritative state.

Checks are performed using a defense-in-depth strategy:
  A) hostname allowlist (case-insensitive; also accepts Tailscale MagicDNS)
  B) IP/CIDR allowlist (for the local interface or primary outbound IP)
  C) host fingerprint file marker (operator provisioned)

CLI
---
    python 09_workflow/MRL_host_guard.py check
    python 09_workflow/MRL_host_guard.py status
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import platform
import socket
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Optional, Tuple

from MRL_utils import ORIGIN_SIGNATURE
PRODUCT_NAME = "MRL_AI_SYSTEM"
HOST_GUARD_VERSION = "1.0"


# ─── Node role ────────────────────────────────────────────────────────────────

class NodeRole(str, Enum):
    """Trust level of the running host."""
    MOTHER   = "MOTHER"    # canonical DL580 — full persistence rights
    MATERIAL = "MATERIAL"  # every other host — read-only / materials mode


# ─── Configuration ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HostGuardConfig:
    hostname_allowlist: List[str]
    cidr_allowlist: List[str]
    fingerprint_file: str
    fingerprint_value: str


DEFAULT_DL580_CONFIG = HostGuardConfig(
    hostname_allowlist=[
        # bare hostname (case-insensitive match)
        "win-pbvui7vk2a6",
        # Tailscale MagicDNS FQDN
        "win-pbvui7vk2a6.tail7de813.ts.net",
    ],
    cidr_allowlist=[
        "100.78.70.78/32",   # Tailscale IP
        "127.0.0.1/32",      # loopback
    ],
    fingerprint_file=r"D:\mrl\config\MRL_host_role.txt",
    fingerprint_value="MRL_DL580_CANONICAL_MOTHER",
)


def _norm_host(s: str) -> str:
    return (s or "").strip().lower().rstrip(".")


def _get_hostname_candidates() -> List[str]:
    cands = []
    try:
        cands.append(platform.node())
    except Exception:
        pass
    try:
        cands.append(socket.gethostname())
    except Exception:
        pass
    try:
        cands.append(socket.getfqdn())
    except Exception:
        pass
    out: List[str] = []
    seen = set()
    for c in cands:
        n = _norm_host(c)
        if n and n not in seen:
            out.append(n)
            seen.add(n)
    return out


def _read_fingerprint(path: str) -> Tuple[bool, str]:
    try:
        if not path:
            return False, "fingerprint_file not configured"
        if not os.path.exists(path):
            return False, f"fingerprint_file not found: {path}"
        raw = open(path, "r", encoding="utf-8", errors="replace").read().strip()
        return True, raw
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _get_ip_candidates() -> List[str]:
    ips: List[str] = []
    # Localhost always included
    ips.append("127.0.0.1")
    # Best-effort primary outbound IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
        finally:
            s.close()
    except Exception:
        pass
    # Dedup
    out: List[str] = []
    seen = set()
    for ip in ips:
        if ip and ip not in seen:
            out.append(ip)
            seen.add(ip)
    return out


def _ip_in_cidrs(ip: str, cidrs: Iterable[str]) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for c in cidrs:
        try:
            net = ipaddress.ip_network(c, strict=False)
        except ValueError:
            continue
        if ip_obj in net:
            return True
    return False


def is_dl580_canonical_host(cfg: HostGuardConfig = DEFAULT_DL580_CONFIG) -> Tuple[bool, str]:
    """Return (ok, reason). ok=True means this host is allowed to persist learning."""

    # A) hostname
    hostnames = _get_hostname_candidates()
    allow_hosts = {_norm_host(x) for x in (cfg.hostname_allowlist or [])}
    if allow_hosts and not any(h in allow_hosts for h in hostnames):
        return False, f"hostname not allowed: {hostnames}"

    # B) CIDR
    cidrs = list(cfg.cidr_allowlist or [])
    if cidrs:
        ips = _get_ip_candidates()
        if not any(_ip_in_cidrs(ip, cidrs) for ip in ips):
            return False, f"ip not allowed: {ips}"

    # C) fingerprint
    ok, fp = _read_fingerprint(cfg.fingerprint_file)
    if not ok:
        return False, f"fingerprint read failed: {fp}"
    if (fp or "").strip() != (cfg.fingerprint_value or "").strip():
        return False, "fingerprint mismatch"

    return True, "dl580 canonical host verified"


# ─── Node role helpers ────────────────────────────────────────────────────────

def get_node_role(cfg: HostGuardConfig = DEFAULT_DL580_CONFIG) -> NodeRole:
    """Return :class:`NodeRole.MOTHER` when running on the canonical DL580 host,
    otherwise :class:`NodeRole.MATERIAL`.

    This is the primary entrypoint for callers that need a simple role decision
    without inspecting the failure reason::

        from MRL_host_guard import get_node_role, NodeRole

        if get_node_role() is NodeRole.MOTHER:
            persist_learning(data)
        else:
            treat_as_material(data)
    """
    ok, _ = is_dl580_canonical_host(cfg)
    return NodeRole.MOTHER if ok else NodeRole.MATERIAL


def node_role_detail(cfg: HostGuardConfig = DEFAULT_DL580_CONFIG) -> dict:
    """Return a structured dict with role, verdict, and diagnostic info."""
    import time
    ok, reason = is_dl580_canonical_host(cfg)
    return {
        "role": (NodeRole.MOTHER if ok else NodeRole.MATERIAL).value,
        "verified": ok,
        "reason": reason,
        "hostnames": _get_hostname_candidates(),
        "ips": _get_ip_candidates(),
        "fingerprint_file": cfg.fingerprint_file,
        "origin_signature": ORIGIN_SIGNATURE,
        "product_name": PRODUCT_NAME,
        "checked_at_ms": int(time.time() * 1000),
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="MRL_host_guard",
        description="MRL canonical-host identity verification (DL580 MOTHER node).",
    )
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("check",  help="Exit 0 if this is the MOTHER host, else 1.")
    sub.add_parser("status", help="Print detailed role JSON and exit 0.")
    args = parser.parse_args(argv)

    detail = node_role_detail()
    if args.cmd == "check":
        if detail["verified"]:
            print(f"[MRL_host_guard] MOTHER: {detail['reason']}")
        else:
            print(f"[MRL_host_guard] MATERIAL: {detail['reason']}")
            raise SystemExit(1)
    elif args.cmd == "status":
        print(json.dumps(detail, ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
