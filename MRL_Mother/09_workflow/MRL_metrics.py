#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_metrics.py — In-Memory Telemetry Collector
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
layer: L6 REFLECT
group: Y=1 MotherCore

Industry capability: lightweight, zero-dependency, thread-safe telemetry that
                     mirrors the Counter / Histogram pattern used in Prometheus
                     and OpenTelemetry — but with no external packages.
MRL extension: every snapshot is stamped with origin_signature and exports
               the same envelope format used by other MRL modules.

Features
--------
- Per-subsystem call counts, error counts, and latency stats (min/max/avg)
- Thread-safe via a single lock (read-copy-under-lock)
- Global singleton shortcut functions (record / snapshot / reset)
- CLI: ``status`` prints a JSON snapshot; ``reset`` clears all stats

Usage (library)
---------------
    from MRL_metrics import MetricsCollector

    collector = MetricsCollector()
    collector.record("llm_gateway", latency_ms=120, ok=True)
    collector.record("eval_engine", latency_ms=8,   ok=False)
    print(collector.snapshot())

    # Global singleton shortcut
    from MRL_metrics import record, snapshot
    record("guardrail", latency_ms=2, ok=True)
    snap = snapshot()
    print(snap["subsystems"]["guardrail"]["avg_latency_ms"])

CLI
---
    python 09_workflow/MRL_metrics.py status
    python 09_workflow/MRL_metrics.py reset
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from typing import Any, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
PRODUCT_NAME = "MRL_AI_SYSTEM"
METRICS_VERSION = "1.0"


# ─── Per-subsystem stats ───────────────────────────────────────────────────────

class _SubsystemStats:
    """Accumulates call counts and latency for one subsystem."""

    __slots__ = (
        "call_count", "ok_count", "error_count",
        "total_latency_ms", "min_latency_ms", "max_latency_ms",
        "last_call_ms",
    )

    def __init__(self) -> None:
        self.call_count: int = 0
        self.ok_count: int = 0
        self.error_count: int = 0
        self.total_latency_ms: int = 0
        self.min_latency_ms: Optional[int] = None
        self.max_latency_ms: Optional[int] = None
        self.last_call_ms: int = 0

    def record(self, latency_ms: int, ok: bool) -> None:
        self.call_count += 1
        self.total_latency_ms += latency_ms
        if ok:
            self.ok_count += 1
        else:
            self.error_count += 1
        if self.min_latency_ms is None or latency_ms < self.min_latency_ms:
            self.min_latency_ms = latency_ms
        if self.max_latency_ms is None or latency_ms > self.max_latency_ms:
            self.max_latency_ms = latency_ms
        self.last_call_ms = int(time.time() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        avg = (self.total_latency_ms // self.call_count) if self.call_count else 0
        return {
            "call_count": self.call_count,
            "ok_count": self.ok_count,
            "error_count": self.error_count,
            "avg_latency_ms": avg,
            "min_latency_ms": self.min_latency_ms if self.min_latency_ms is not None else 0,
            "max_latency_ms": self.max_latency_ms if self.max_latency_ms is not None else 0,
            "total_latency_ms": self.total_latency_ms,
            "last_call_ms": self.last_call_ms,
        }


# ─── MetricsCollector ─────────────────────────────────────────────────────────

class MetricsCollector:
    """
    Thread-safe in-memory metrics collector.

    Records call counts, error rates, and latency statistics per named
    subsystem.  All operations are protected by a single threading.Lock so
    the collector is safe to use from multiple threads simultaneously.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stats: Dict[str, _SubsystemStats] = {}
        self._created_at_ms: int = int(time.time() * 1000)

    # ── Write ──────────────────────────────────────────────────────────────────

    def record(self, subsystem: str, latency_ms: int, *, ok: bool = True) -> None:
        """
        Record one call for *subsystem*.

        Parameters
        ----------
        subsystem  : Logical name of the component (e.g. "llm_gateway").
        latency_ms : Wall-clock duration of the call in milliseconds.
        ok         : True if the call succeeded, False if it errored.
        """
        with self._lock:
            if subsystem not in self._stats:
                self._stats[subsystem] = _SubsystemStats()
            self._stats[subsystem].record(latency_ms, ok)

    # ── Read ───────────────────────────────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        """Return a point-in-time snapshot of all collected metrics."""
        with self._lock:
            return {
                "origin_signature": ORIGIN_SIGNATURE,
                "product_name": PRODUCT_NAME,
                "metrics_version": METRICS_VERSION,
                "created_at_ms": self._created_at_ms,
                "snapshot_at_ms": int(time.time() * 1000),
                "subsystems": {k: v.to_dict() for k, v in sorted(self._stats.items())},
            }

    def subsystem_names(self) -> List[str]:
        """Return sorted list of tracked subsystem names."""
        with self._lock:
            return sorted(self._stats.keys())

    # ── Reset ──────────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Clear all collected metrics and reset the creation timestamp."""
        with self._lock:
            self._stats.clear()
            self._created_at_ms = int(time.time() * 1000)


# ── Global singleton ──────────────────────────────────────────────────────────

_default_collector: MetricsCollector = MetricsCollector()


def record(subsystem: str, latency_ms: int, *, ok: bool = True) -> None:
    """Record a call on the process-wide default collector."""
    _default_collector.record(subsystem, latency_ms, ok=ok)


def snapshot() -> Dict[str, Any]:
    """Return a snapshot from the process-wide default collector."""
    return _default_collector.snapshot()


def reset() -> None:
    """Reset the process-wide default collector."""
    _default_collector.reset()


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cmd_status(_args: argparse.Namespace) -> None:
    snap = snapshot()
    print(json.dumps(snap, ensure_ascii=False, indent=2))


def _cmd_reset(_args: argparse.Namespace) -> None:
    reset()
    print("Metrics reset.")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MetricsCollector — in-memory telemetry for MRL subsystems"
    )
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("status", help="Print current metrics snapshot as JSON")
    sub.add_parser("reset",  help="Clear all collected metrics")
    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    if args.cmd == "status":
        _cmd_status(args)
    elif args.cmd == "reset":
        _cmd_reset(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
