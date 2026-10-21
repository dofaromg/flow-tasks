#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_rate_limiter.py — Sliding-Window API Rate Limiter
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
layer: L3 LAW
group: Y=1 MotherCore

Industry capability: per-client sliding-window rate limiting — the same
                     pattern used by OpenAI, Anthropic, and major API
                     platforms to protect backend resources.
MRL extension: every throttle decision is stamped with origin_signature
               and can be integrated with MRL_metrics for observability.

Algorithm
---------
  Sliding-window counter:  for each client key (IP address or auth token)
  keep a deque of UTC timestamps for the last N requests.  On each new
  request, drop timestamps older than ``window_seconds``, then check
  whether the remaining count exceeds the configured limit.

  This avoids the "burst at window boundary" problem of fixed-window
  counters while remaining O(1) amortised per request.

Configuration (via config_manager)
-----------------------------------
  api.rate_limit_per_minute  (int)   — max requests per client per minute
                                        0 = disabled (default)
  api.rate_limit_window_s    (int)   — window size in seconds (default 60)
  api.rate_limit_by          (str)   — "ip" | "token" (default "ip")

Usage (library)
---------------
    from MRL_rate_limiter import RateLimiter

    limiter = RateLimiter(limit=60, window_seconds=60)
    allowed, info = limiter.check("192.168.1.1")
    if not allowed:
        # respond with HTTP 429
        print(info["retry_after_s"])

CLI
---
    python 09_workflow/MRL_rate_limiter.py demo
    python 09_workflow/MRL_rate_limiter.py status
"""

from __future__ import annotations

import argparse
import collections
import threading
import time
from typing import Any, Deque, Dict, Optional, Tuple

from MRL_utils import ORIGIN_SIGNATURE
PRODUCT_NAME = "MRL_AI_SYSTEM"
RATE_LIMITER_VERSION = "1.0"

# TXYZ metadata
_LAYER = "L3"
_GROUP = "Y=1"


# ─── RateLimiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Thread-safe sliding-window rate limiter.

    Parameters
    ----------
    limit          : Maximum requests allowed per *window_seconds*.
                     0 disables rate limiting.
    window_seconds : Size of the sliding window in seconds (default 60).
    """

    def __init__(self, limit: int = 0, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        # client_key → deque of request timestamps (float, monotonic)
        self._windows: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()
        self._total_allowed: int = 0
        self._total_throttled: int = 0

    # ── Core logic ────────────────────────────────────────────────────────────

    def check(self, client_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check whether *client_key* is within the rate limit.

        Returns
        -------
        (allowed, info)

        info keys:
          allowed         : bool
          client_key      : str
          current_count   : int  — requests in current window
          limit           : int
          window_seconds  : int
          retry_after_s   : float | None  — seconds until oldest request expires
          checked_at_ms   : int
          origin_signature: str
        """
        if self.limit <= 0:
            return True, self._info(client_key, True, 0, None)

        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            dq = self._windows.get(client_key)
            if dq is None:
                dq = collections.deque()
                self._windows[client_key] = dq

            # Evict timestamps outside the current window
            while dq and dq[0] <= cutoff:
                dq.popleft()

            count = len(dq)
            if count < self.limit:
                dq.append(now)
                self._total_allowed += 1
                return True, self._info(client_key, True, count + 1, None)
            else:
                # Compute how long until the oldest entry leaves the window
                retry_after: Optional[float] = None
                if dq:
                    retry_after = max(0.0, dq[0] + self.window_seconds - now)
                self._total_throttled += 1
                return False, self._info(client_key, False, count, retry_after)

    def reset(self, client_key: Optional[str] = None) -> None:
        """
        Clear rate-limit state.

        Parameters
        ----------
        client_key : If given, reset only that client; otherwise reset all.
        """
        with self._lock:
            if client_key is None:
                self._windows.clear()
                self._total_allowed = 0
                self._total_throttled = 0
            else:
                self._windows.pop(client_key, None)

    def stats(self) -> Dict[str, Any]:
        """Return aggregate statistics."""
        with self._lock:
            return {
                "limit": self.limit,
                "window_seconds": self.window_seconds,
                "active_clients": len(self._windows),
                "total_allowed": self._total_allowed,
                "total_throttled": self._total_throttled,
                "enabled": self.limit > 0,
                "origin_signature": ORIGIN_SIGNATURE,
                "product_name": PRODUCT_NAME,
                "layer": _LAYER,
                "group": _GROUP,
            }

    # ── Helper ────────────────────────────────────────────────────────────────

    def _info(
        self,
        client_key: str,
        allowed: bool,
        current_count: int,
        retry_after: Optional[float],
    ) -> Dict[str, Any]:
        return {
            "allowed": allowed,
            "client_key": client_key,
            "current_count": current_count,
            "limit": self.limit,
            "window_seconds": self.window_seconds,
            "retry_after_s": retry_after,
            "checked_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
            "product_name": PRODUCT_NAME,
        }


# ── Module-level singleton (configured from ConfigManager) ────────────────────

def _build_from_config() -> RateLimiter:
    """Instantiate a RateLimiter using config_manager settings."""
    try:
        import importlib
        import pathlib
        import sys
        _root = pathlib.Path(__file__).resolve().parent.parent
        _wf = str(_root / "09_workflow")
        if _wf not in sys.path:
            sys.path.insert(0, _wf)
        cfg_mod = importlib.import_module("config_manager")
        cfg = cfg_mod.ConfigManager()
        limit = int(cfg.get("api.rate_limit_per_minute", 0))
        window = int(cfg.get("api.rate_limit_window_s", 60))
        return RateLimiter(limit=limit, window_seconds=window)
    except Exception:  # noqa: BLE001
        return RateLimiter(limit=0)


# Lazy singleton — initialised on first import
_limiter: Optional[RateLimiter] = None
_limiter_lock = threading.Lock()


def get_limiter() -> RateLimiter:
    """Return the process-wide RateLimiter singleton (lazy init)."""
    global _limiter
    if _limiter is None:
        with _limiter_lock:
            if _limiter is None:
                _limiter = _build_from_config()
    return _limiter


def check(client_key: str) -> Tuple[bool, Dict[str, Any]]:
    """Convenience wrapper around the process-wide limiter."""
    return get_limiter().check(client_key)


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cmd_demo(_args: argparse.Namespace) -> None:
    limiter = RateLimiter(limit=5, window_seconds=10)
    print(f"Limit: {limiter.limit} req / {limiter.window_seconds}s\n")
    for i in range(8):
        allowed, info = limiter.check("demo-client")
        mark = "✅ ALLOW" if allowed else "🚫 THROTTLE"
        print(f"  Request {i + 1:2d}: {mark}  count={info['current_count']}"
              f"  retry_after={info['retry_after_s']}")
    print(f"\nStats: {limiter.stats()}")


def _cmd_status(_args: argparse.Namespace) -> None:
    import json
    print(json.dumps(get_limiter().stats(), indent=2))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MRL_rate_limiter — sliding-window API rate limiter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Config keys (data/config.json or MRL_ env vars):\n"
            "  api.rate_limit_per_minute  (int, 0=disabled)\n"
            "  api.rate_limit_window_s    (int, default 60)\n"
            "  api.rate_limit_by          (str, 'ip' | 'token')\n"
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo",   help="Run interactive demo (limit=5, window=10s)")
    sub.add_parser("status", help="Print current limiter stats from config")
    return p


def main() -> None:
    args = _build_argparser().parse_args()
    dispatch = {"demo": _cmd_demo, "status": _cmd_status}
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
