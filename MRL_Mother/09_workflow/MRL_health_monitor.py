#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_health_monitor.py — Background System Health Monitor
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
layer: L6 REFLECT
group: Y=1 MotherCore

Industry capability: proactive health monitoring with background polling —
                     the same pattern used in production AI platforms to
                     detect backend degradation before it impacts users.
MRL extension: health events are emitted on MRL_event_bus and anomalies
               are recorded in MRL_metrics so dashboards show live status.

What it monitors
----------------
  llm_backend   — Polls Ollama (/api/tags) and llama.cpp (/v1/models)
                  to detect if the local LLM server is reachable.
  disk_space    — Checks the MerkleChain data directory for low disk.
  custom probes — Any callable registered via ``add_probe(name, fn)``.

Health status levels
--------------------
  "ok"      — all checks passing
  "warn"    — at least one probe returned a warning (not critical)
  "error"   — at least one probe failed

Usage (library)
---------------
    from MRL_health_monitor import HealthMonitor

    monitor = HealthMonitor(interval_s=30)
    monitor.start()

    status = monitor.current_status()
    print(status["overall"])   # "ok" | "warn" | "error"

    monitor.stop()

    # Process-wide singleton
    from MRL_health_monitor import get_monitor, current_status
    get_monitor().start()
    print(current_status()["overall"])

CLI
---
    python 09_workflow/MRL_health_monitor.py start   --interval 30
    python 09_workflow/MRL_health_monitor.py status
    python 09_workflow/MRL_health_monitor.py probe
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
PRODUCT_NAME = "MRL_AI_SYSTEM"
HEALTH_MONITOR_VERSION = "1.0"

_LAYER = "L6"
_GROUP = "Y=1"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Disk warning threshold: warn when free space < 500 MB
_DISK_WARN_BYTES = 500 * 1024 * 1024

ProbeResult = Dict[str, Any]  # {"name", "status", "message", "checked_at_ms"}


# ─── Built-in probes ──────────────────────────────────────────────────────────

def _probe_ollama() -> ProbeResult:
    """Check if Ollama server is reachable."""
    url = "http://127.0.0.1:11434/api/tags"
    try:
        req = urllib.request.Request(
            url, headers={"Accept": "application/json"}, method="GET"
        )
        with urllib.request.urlopen(req, timeout=3):
            pass
        return _result("ollama_backend", "ok", "Ollama reachable")
    except Exception as exc:  # noqa: BLE001
        return _result("ollama_backend", "warn", f"Ollama unreachable: {exc}")


def _probe_llamacpp() -> ProbeResult:
    """Check if llama.cpp HTTP server is reachable."""
    url = "http://127.0.0.1:8080/v1/models"
    try:
        req = urllib.request.Request(
            url, headers={"Accept": "application/json"}, method="GET"
        )
        with urllib.request.urlopen(req, timeout=3):
            pass
        return _result("llamacpp_backend", "ok", "llama.cpp reachable")
    except Exception as exc:  # noqa: BLE001
        return _result("llamacpp_backend", "warn", f"llama.cpp unreachable: {exc}")


def _probe_disk() -> ProbeResult:
    """Check disk space on the MerkleChain data directory."""
    data_dir = _REPO_ROOT / "03_memory" / "_data"
    try:
        path = str(data_dir) if data_dir.exists() else str(_REPO_ROOT)
        usage = shutil.disk_usage(path)
        free_mb = usage.free // (1024 * 1024)
        if usage.free < _DISK_WARN_BYTES:
            return _result(
                "disk_space",
                "warn",
                f"Low disk space: {free_mb} MB free on {path}",
            )
        return _result("disk_space", "ok", f"{free_mb} MB free on {path}")
    except Exception as exc:  # noqa: BLE001
        return _result("disk_space", "error", f"disk check failed: {exc}")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _result(name: str, status: str, message: str) -> ProbeResult:
    return {
        "name": name,
        "status": status,
        "message": message,
        "checked_at_ms": int(time.time() * 1000),
        "origin_signature": ORIGIN_SIGNATURE,
        "product_name": PRODUCT_NAME,
    }


def _overall(results: List[ProbeResult]) -> str:
    statuses = {r["status"] for r in results}
    if "error" in statuses:
        return "error"
    if "warn" in statuses:
        return "warn"
    return "ok"


# ─── HealthMonitor ────────────────────────────────────────────────────────────

class HealthMonitor:
    """
    Background health probe runner.

    Parameters
    ----------
    interval_s : int
        Seconds between full probe cycles (default 60).
    """

    def __init__(self, interval_s: int = 60) -> None:
        self.interval_s = interval_s
        self._probes: Dict[str, Callable[[], ProbeResult]] = {
            "ollama_backend": _probe_ollama,
            "llamacpp_backend": _probe_llamacpp,
            "disk_space": _probe_disk,
        }
        self._latest: Dict[str, ProbeResult] = {}
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        self._cycle_count: int = 0
        self._started_at_ms: int = 0

    # ── Probe management ──────────────────────────────────────────────────────

    def add_probe(self, name: str, fn: Callable[[], ProbeResult]) -> None:
        """Register a custom probe callable."""
        with self._lock:
            self._probes[name] = fn

    def remove_probe(self, name: str) -> bool:
        """Remove a probe by name. Returns True if it existed."""
        with self._lock:
            if name in self._probes:
                del self._probes[name]
                return True
            return False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background polling thread."""
        if self._running:
            return
        self._stop_event.clear()
        self._running = True
        self._started_at_ms = int(time.time() * 1000)
        # Run one probe cycle immediately before detaching to background
        self._run_cycle()
        self._thread = threading.Thread(
            target=self._loop,
            name="mrl-health-monitor",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        """Stop the background polling thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        self._running = False
        self._thread = None

    # ── Status ────────────────────────────────────────────────────────────────

    def probe_once(self) -> Dict[str, Any]:
        """
        Run a single full probe cycle synchronously and return the result.
        Does NOT require the monitor to be started.
        """
        self._run_cycle()
        return self.current_status()

    def current_status(self) -> Dict[str, Any]:
        """
        Return the most recent health status snapshot.

        Returns
        -------
        {
          "overall":        "ok" | "warn" | "error",
          "running":        bool,
          "cycle_count":    int,
          "interval_s":     int,
          "probes":         {name: ProbeResult},
          "started_at_ms":  int,
          "snapshot_at_ms": int,
          "origin_signature": "MrLiouWord",
        }
        """
        with self._lock:
            return {
                "overall": _overall(list(self._latest.values())) if self._latest else "ok",
                "running": self._running,
                "cycle_count": self._cycle_count,
                "interval_s": self.interval_s,
                "probes": dict(self._latest),
                "started_at_ms": self._started_at_ms,
                "snapshot_at_ms": int(time.time() * 1000),
                "origin_signature": ORIGIN_SIGNATURE,
                "product_name": PRODUCT_NAME,
                "layer": _LAYER,
                "group": _GROUP,
            }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _loop(self) -> None:
        while not self._stop_event.wait(timeout=self.interval_s):
            self._run_cycle()

    def _run_cycle(self) -> None:
        with self._lock:
            probes_snapshot = dict(self._probes)

        results: Dict[str, ProbeResult] = {}
        for name, fn in probes_snapshot.items():
            try:
                results[name] = fn()
            except Exception as exc:  # noqa: BLE001
                results[name] = _result(name, "error", f"probe raised: {exc}")

        with self._lock:
            self._latest.update(results)
            self._cycle_count += 1

        # Emit events and record metrics for any non-ok probes
        self._dispatch_events(results)
        self._record_metrics(results)

    def _dispatch_events(self, results: Dict[str, ProbeResult]) -> None:
        """Emit health events on MRL_event_bus if available."""
        try:
            import importlib
            _wf = str(_REPO_ROOT / "09_workflow")
            if _wf not in sys.path:
                sys.path.insert(0, _wf)
            bus_mod = importlib.import_module("MRL_event_bus")
            for name, r in results.items():
                if r["status"] != "ok":
                    bus_mod.emit(f"health.{r['status']}", {
                        "probe": name,
                        "message": r["message"],
                        "status": r["status"],
                    })
        except Exception:  # noqa: BLE001
            pass

    def _record_metrics(self, results: Dict[str, ProbeResult]) -> None:
        """Record probe errors in MRL_metrics if available."""
        try:
            import importlib
            _wf = str(_REPO_ROOT / "09_workflow")
            if _wf not in sys.path:
                sys.path.insert(0, _wf)
            metrics_mod = importlib.import_module("MRL_metrics")
            for name, r in results.items():
                ok = r["status"] == "ok"
                metrics_mod.record(f"health.{name}", latency_ms=0, ok=ok)
        except Exception:  # noqa: BLE001
            pass


# ── Process-wide singleton ────────────────────────────────────────────────────

_monitor: Optional[HealthMonitor] = None
_monitor_lock = threading.Lock()


def get_monitor(interval_s: int = 60) -> HealthMonitor:
    """Return the process-wide HealthMonitor singleton (lazy init)."""
    global _monitor
    if _monitor is None:
        with _monitor_lock:
            if _monitor is None:
                _monitor = HealthMonitor(interval_s=interval_s)
    return _monitor


def current_status() -> Dict[str, Any]:
    """Return the current health status from the process-wide monitor."""
    return get_monitor().current_status()


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cmd_probe(_args: argparse.Namespace) -> None:
    monitor = HealthMonitor()
    status = monitor.probe_once()
    print(json.dumps(status, indent=2, ensure_ascii=False))


def _cmd_status(_args: argparse.Namespace) -> None:
    print(json.dumps(current_status(), indent=2, ensure_ascii=False))


def _cmd_start(args: argparse.Namespace) -> None:
    interval = getattr(args, "interval", 30)
    monitor = get_monitor(interval_s=interval)
    monitor.start()
    print(f"[MRL_health_monitor] Started (interval={interval}s). Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(interval)
            status = monitor.current_status()
            print(
                f"  cycle={status['cycle_count']}  overall={status['overall']}  "
                + "  ".join(
                    f"{k}={v['status']}" for k, v in status["probes"].items()
                )
            )
    except KeyboardInterrupt:
        monitor.stop()
        print("\n[MRL_health_monitor] Stopped.")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MRL_health_monitor — background system health probe",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    st = sub.add_parser("start", help="Start continuous background monitoring")
    st.add_argument("--interval", type=int, default=30, help="Probe interval in seconds")

    sub.add_parser("status", help="Print current status from singleton")
    sub.add_parser("probe",  help="Run one probe cycle and print result")

    return p


def main() -> None:
    args = _build_argparser().parse_args()
    dispatch = {
        "start":  _cmd_start,
        "status": _cmd_status,
        "probe":  _cmd_probe,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
