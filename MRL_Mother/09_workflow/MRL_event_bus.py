#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_event_bus.py — Lightweight Pub/Sub Event Bus
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
layer: L6 REFLECT
group: Y=1 MotherCore

Industry capability: decoupled publish/subscribe event system — the same
                     architectural pattern used by LangChain callbacks,
                     AutoGen events, and production AI observability stacks.
MRL extension: every emitted event is stamped with origin_signature and a
               monotonic event_id so events can be replayed or sealed into
               the MerkleChain.

Architecture
------------
  Publisher  — any module calls ``bus.emit(event_type, payload)``
  Subscriber — any module calls ``bus.subscribe(event_type, handler_fn)``
  EventBus   — thread-safe dispatcher; handlers called synchronously in the
               emitting thread by default (async_dispatch=True for background)

  Wildcard subscription:  subscribe("*", handler) receives ALL events.

Event envelope
--------------
    {
      "event_id":         str,            # UUID
      "event_type":       str,            # e.g. "guardrail.block"
      "payload":          dict,           # caller-supplied data
      "emitted_at_ms":    int,
      "origin_signature": "MrLiouWord",
      "layer":            "L6",
      "group":            "Y=1",
    }

Usage (library)
---------------
    from MRL_event_bus import EventBus

    bus = EventBus()

    @bus.subscribe("chat.complete")
    def on_chat(event):
        print(f"Chat done: {event['payload']}")

    bus.emit("chat.complete", {"tokens": 42, "model": "llama3"})

    # Process-wide singleton
    from MRL_event_bus import emit, subscribe
    subscribe("guardrail.block", lambda e: print("BLOCKED:", e))
    emit("guardrail.block", {"reason": "deny_terms"})

CLI
---
    python 09_workflow/MRL_event_bus.py demo
    python 09_workflow/MRL_event_bus.py stats
"""

from __future__ import annotations

import argparse
import json
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
PRODUCT_NAME = "MRL_AI_SYSTEM"
EVENT_BUS_VERSION = "1.0"

_LAYER = "L6"
_GROUP = "Y=1"

HandlerFn = Callable[[Dict[str, Any]], None]

_WILDCARD = "*"


# ─── EventBus ─────────────────────────────────────────────────────────────────

class EventBus:
    """
    Thread-safe publish/subscribe event bus.

    Parameters
    ----------
    async_dispatch : bool
        If True, each handler is invoked in a separate daemon thread so
        the emitting thread is not blocked.  If False (default), handlers
        run synchronously in the emitting thread.
    max_history    : int
        Number of recent events to keep in the ring buffer for replay
        and diagnostics (default 200, 0 = disabled).
    """

    def __init__(
        self,
        async_dispatch: bool = False,
        max_history: int = 200,
    ) -> None:
        self._async = async_dispatch
        self._max_history = max_history
        # event_type → list of handlers
        self._handlers: Dict[str, List[HandlerFn]] = {}
        self._lock = threading.Lock()
        self._history: List[Dict[str, Any]] = []
        self._emit_count: int = 0
        self._error_count: int = 0

    # ── Subscribe ─────────────────────────────────────────────────────────────

    def subscribe(
        self,
        event_type: str,
        handler: Optional[HandlerFn] = None,
    ) -> Any:
        """
        Register a handler for *event_type*.

        Can be used as a decorator::

            @bus.subscribe("chat.complete")
            def my_handler(event): ...

        Or called directly::

            bus.subscribe("chat.complete", my_handler)

        Use ``"*"`` to subscribe to all events.
        """
        def _register(fn: HandlerFn) -> HandlerFn:
            with self._lock:
                self._handlers.setdefault(event_type, []).append(fn)
            return fn

        if handler is not None:
            _register(handler)
            return handler
        return _register

    def unsubscribe(self, event_type: str, handler: HandlerFn) -> bool:
        """
        Remove a previously registered handler.

        Returns True if the handler was found and removed, False otherwise.
        """
        with self._lock:
            lst = self._handlers.get(event_type, [])
            try:
                lst.remove(handler)
                return True
            except ValueError:
                return False

    # ── Emit ──────────────────────────────────────────────────────────────────

    def emit(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Publish an event.

        Parameters
        ----------
        event_type : Dot-namespaced string, e.g. ``"guardrail.block"``.
        payload    : Arbitrary dict attached to the event.

        Returns
        -------
        The fully-formed event envelope dict.
        """
        event: Dict[str, Any] = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "payload": payload or {},
            "emitted_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
            "product_name": PRODUCT_NAME,
            "layer": _LAYER,
            "group": _GROUP,
        }

        with self._lock:
            self._emit_count += 1
            # Collect handlers: specific type + wildcard
            handlers = list(self._handlers.get(event_type, []))
            if event_type != _WILDCARD:
                handlers += list(self._handlers.get(_WILDCARD, []))
            # Store in ring buffer
            if self._max_history > 0:
                self._history.append(event)
                if len(self._history) > self._max_history:
                    self._history.pop(0)

        if handlers:
            if self._async:
                for h in handlers:
                    t = threading.Thread(
                        target=self._safe_call,
                        args=(h, event),
                        daemon=True,
                    )
                    t.start()
            else:
                for h in handlers:
                    self._safe_call(h, event)

        return event

    # ── Query ─────────────────────────────────────────────────────────────────

    def history(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return recent events, optionally filtered by *event_type*."""
        with self._lock:
            if event_type:
                return [e for e in self._history if e["event_type"] == event_type]
            return list(self._history)

    def stats(self) -> Dict[str, Any]:
        """Return bus statistics."""
        with self._lock:
            return {
                "emit_count": self._emit_count,
                "error_count": self._error_count,
                "subscriptions": {k: len(v) for k, v in self._handlers.items()},
                "history_size": len(self._history),
                "max_history": self._max_history,
                "async_dispatch": self._async,
                "origin_signature": ORIGIN_SIGNATURE,
                "product_name": PRODUCT_NAME,
                "layer": _LAYER,
                "group": _GROUP,
            }

    def clear_history(self) -> None:
        """Clear the event history ring buffer."""
        with self._lock:
            self._history.clear()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _safe_call(self, handler: HandlerFn, event: Dict[str, Any]) -> None:
        """Invoke *handler* and swallow exceptions so one bad handler cannot crash the bus."""
        try:
            handler(event)
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._error_count += 1
            # Log to stderr without importing logging (zero dependencies)
            import sys
            print(
                f"[MRL_event_bus] handler error in '{handler.__name__}' "
                f"for event '{event['event_type']}': {exc}",
                file=sys.stderr,
            )


# ── Process-wide singleton ────────────────────────────────────────────────────

_bus: Optional[EventBus] = None
_bus_lock = threading.Lock()


def get_bus() -> EventBus:
    """Return the process-wide EventBus singleton (lazy init)."""
    global _bus
    if _bus is None:
        with _bus_lock:
            if _bus is None:
                _bus = EventBus()
    return _bus


def emit(event_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Emit an event on the process-wide bus."""
    return get_bus().emit(event_type, payload)


def subscribe(
    event_type: str,
    handler: Optional[HandlerFn] = None,
) -> Any:
    """Subscribe a handler on the process-wide bus."""
    return get_bus().subscribe(event_type, handler)


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cmd_demo(_args: argparse.Namespace) -> None:
    bus = EventBus()
    received: List[str] = []

    @bus.subscribe("chat.complete")
    def on_chat(event: Dict[str, Any]) -> None:
        received.append(event["event_type"])
        print(f"  [handler: chat.complete] payload={event['payload']}")

    @bus.subscribe("*")
    def on_all(event: Dict[str, Any]) -> None:
        print(f"  [handler: *] event_type={event['event_type']}")

    print("Emitting 3 events…")
    bus.emit("chat.complete", {"tokens": 42, "model": "stub"})
    bus.emit("guardrail.block", {"reason": "deny_terms"})
    bus.emit("metrics.record", {"subsystem": "llm_gateway", "latency_ms": 120})

    print(f"\nStats: {json.dumps(bus.stats(), indent=2)}")
    print(f"History: {len(bus.history())} events")


def _cmd_stats(_args: argparse.Namespace) -> None:
    print(json.dumps(get_bus().stats(), indent=2, ensure_ascii=False))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MRL_event_bus — lightweight pub/sub event bus",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo",  help="Run interactive demo")
    sub.add_parser("stats", help="Print process-wide bus stats")
    return p


def main() -> None:
    args = _build_argparser().parse_args()
    dispatch = {"demo": _cmd_demo, "stats": _cmd_stats}
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
