#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_cache.py — LRU + TTL In-Process Cache
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
layer: L6 REFLECT
group: Y=1 MotherCore

Industry capability: time-aware least-recently-used cache — the same pattern
                     used to memoize LLM completions, vector search results,
                     and template renders in production AI pipelines.
MRL extension: cache hits/misses are stamped with origin_signature and can
               be exported to MRL_metrics for observability.

Features
--------
  - LRU eviction when max_size is reached
  - Per-entry TTL (seconds); expired entries are treated as misses
  - Thread-safe via a single RLock
  - Generic typed API: any hashable key, any serialisable value
  - Zero external dependencies (pure stdlib: collections.OrderedDict)

Configuration (via config_manager)
-----------------------------------
  cache.default_ttl    (int)   — seconds before an entry expires (default 60)
  cache.default_size   (int)   — max entries per cache instance (default 1024)

Usage (library)
---------------
    from MRL_cache import Cache

    cache = Cache(max_size=256, ttl=60)

    # Basic get / set
    cache.set("key1", {"text": "Hello"})
    entry = cache.get("key1")          # returns value or None if expired/absent
    entry = cache.get("key1", default="fallback")

    # Decorator
    @cache.cached(key_fn=lambda prompt: prompt)
    def call_llm(prompt: str) -> str:
        ...

    # Global singleton helpers
    from MRL_cache import get_cache, cache_get, cache_set
    cache_set("llm", "prompt_hash", response_dict)
    hit = cache_get("llm", "prompt_hash")

CLI
---
    python 09_workflow/MRL_cache.py demo
    python 09_workflow/MRL_cache.py stats
"""

from __future__ import annotations

import argparse
import collections
import json
import threading
import time
from typing import Any, Callable, Dict, Hashable, Optional, Tuple, TypeVar

from MRL_utils import ORIGIN_SIGNATURE
PRODUCT_NAME = "MRL_AI_SYSTEM"
CACHE_VERSION = "1.0"

_LAYER = "L6"
_GROUP = "Y=1"

_VT = TypeVar("_VT")

_SENTINEL = object()  # distinguish "not found" from None values


# ─── _CacheEntry ──────────────────────────────────────────────────────────────

class _CacheEntry:
    __slots__ = ("value", "expires_at", "created_at_ms", "hits")

    def __init__(self, value: Any, ttl: float) -> None:
        self.value = value
        self.expires_at: float = time.monotonic() + ttl if ttl > 0 else float("inf")
        self.created_at_ms: int = int(time.time() * 1000)
        self.hits: int = 0

    def is_alive(self) -> bool:
        return time.monotonic() < self.expires_at


# ─── Cache ────────────────────────────────────────────────────────────────────

class Cache:
    """
    LRU + TTL cache.

    Parameters
    ----------
    max_size : int
        Maximum number of entries before LRU eviction.  0 = unlimited.
    ttl      : float
        Default time-to-live in seconds.  0 = entries never expire.
    """

    def __init__(self, max_size: int = 1024, ttl: float = 60.0) -> None:
        self.max_size = max_size
        self.ttl = ttl
        # OrderedDict preserves insertion order; we move-to-end on access
        self._store: collections.OrderedDict[Hashable, _CacheEntry] = (
            collections.OrderedDict()
        )
        self._lock = threading.RLock()
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0

    # ── Core API ──────────────────────────────────────────────────────────────

    def get(self, key: Hashable, default: Any = None) -> Any:
        """
        Retrieve a cached value.

        Returns *default* when the key is absent or the entry has expired.
        """
        with self._lock:
            entry = self._store.get(key, None)
            if entry is None or not entry.is_alive():
                if entry is not None:
                    del self._store[key]  # lazily remove expired
                self._misses += 1
                return default
            # Move to end (most recently used)
            self._store.move_to_end(key)
            entry.hits += 1
            self._hits += 1
            return entry.value

    def set(
        self,
        key: Hashable,
        value: Any,
        *,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Store *value* under *key*.

        Parameters
        ----------
        key   : Any hashable key.
        value : Value to cache (any type).
        ttl   : Override the default TTL for this entry only.
        """
        effective_ttl = ttl if ttl is not None else self.ttl
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = _CacheEntry(value, effective_ttl)
            # Evict LRU entries if over capacity
            if self.max_size > 0:
                while len(self._store) > self.max_size:
                    self._store.popitem(last=False)
                    self._evictions += 1

    def delete(self, key: Hashable) -> bool:
        """Remove an entry. Returns True if it existed."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            self._store.clear()

    def __contains__(self, key: Hashable) -> bool:
        return self.get(key, _SENTINEL) is not _SENTINEL

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)

    # ── Decorator ─────────────────────────────────────────────────────────────

    def cached(
        self,
        key_fn: Optional[Callable[..., Hashable]] = None,
        ttl: Optional[float] = None,
    ) -> Callable[[Callable[..., _VT]], Callable[..., _VT]]:
        """
        Method / function decorator.

        Parameters
        ----------
        key_fn : Callable that receives the same args as the wrapped function
                 and returns a hashable cache key.  Defaults to ``repr(args)``.
        ttl    : Per-call TTL override.

        Example
        -------
            @cache.cached(key_fn=lambda p, **_: p)
            def llm_call(prompt: str) -> dict: ...
        """
        def decorator(fn: Callable[..., _VT]) -> Callable[..., _VT]:
            def wrapper(*args: Any, **kwargs: Any) -> _VT:
                if key_fn is not None:
                    k = key_fn(*args, **kwargs)
                else:
                    k = repr(args) + repr(sorted(kwargs.items()))
                hit = self.get(k, _SENTINEL)
                if hit is not _SENTINEL:
                    return hit  # type: ignore[return-value]
                result = fn(*args, **kwargs)
                self.set(k, result, ttl=ttl)
                return result
            wrapper.__name__ = fn.__name__
            wrapper.__doc__ = fn.__doc__
            return wrapper
        return decorator

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Return cache performance statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total else 0.0
            # Count alive vs expired entries in store
            alive = sum(1 for e in self._store.values() if e.is_alive())
            return {
                "size": len(self._store),
                "alive": alive,
                "max_size": self.max_size,
                "default_ttl": self.ttl,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
                "evictions": self._evictions,
                "origin_signature": ORIGIN_SIGNATURE,
                "product_name": PRODUCT_NAME,
                "layer": _LAYER,
                "group": _GROUP,
            }


# ── Namespaced multi-cache store ──────────────────────────────────────────────

class CacheStore:
    """
    A registry of named Cache instances.

    Modules request their own namespace::

        from MRL_cache import get_cache
        c = get_cache("llm_gateway")
        c.set("prompt_abc", response)
    """

    def __init__(self, default_max_size: int = 1024, default_ttl: float = 60.0) -> None:
        self._caches: Dict[str, Cache] = {}
        self._lock = threading.Lock()
        self._default_max_size = default_max_size
        self._default_ttl = default_ttl

    def get_cache(
        self,
        namespace: str,
        *,
        max_size: Optional[int] = None,
        ttl: Optional[float] = None,
    ) -> Cache:
        """Return (or create) the Cache for *namespace*."""
        with self._lock:
            if namespace not in self._caches:
                self._caches[namespace] = Cache(
                    max_size=max_size if max_size is not None else self._default_max_size,
                    ttl=ttl if ttl is not None else self._default_ttl,
                )
            return self._caches[namespace]

    def stats_all(self) -> Dict[str, Any]:
        """Return stats for every namespace."""
        with self._lock:
            return {ns: c.stats() for ns, c in self._caches.items()}


# ── Module-level singleton helpers ────────────────────────────────────────────

def _build_store() -> CacheStore:
    """Build a CacheStore using config_manager settings if available."""
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
        ttl = float(cfg.get("cache.default_ttl", 60))
        size = int(cfg.get("cache.default_size", 1024))
        return CacheStore(default_max_size=size, default_ttl=ttl)
    except Exception:  # noqa: BLE001
        return CacheStore()


_store: Optional[CacheStore] = None
_store_lock = threading.Lock()


def _get_store() -> CacheStore:
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = _build_store()
    return _store


def get_cache(namespace: str = "default", **kwargs: Any) -> Cache:
    """Return the named cache from the process-wide store."""
    return _get_store().get_cache(namespace, **kwargs)


def cache_get(namespace: str, key: Hashable, default: Any = None) -> Any:
    """Get *key* from the *namespace* cache."""
    return get_cache(namespace).get(key, default)


def cache_set(namespace: str, key: Hashable, value: Any, **kwargs: Any) -> None:
    """Set *key* in the *namespace* cache."""
    get_cache(namespace).set(key, value, **kwargs)


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cmd_demo(_args: argparse.Namespace) -> None:
    c = Cache(max_size=5, ttl=2.0)
    print(f"Cache (max_size={c.max_size}, ttl={c.ttl}s)\n")

    for i in range(7):
        c.set(f"k{i}", f"value_{i}")
        print(f"  set k{i}  →  size={len(c)}")

    print(f"\nAfter 7 sets (max 5), size={len(c)}")
    print(f"  get k0 (should be evicted): {c.get('k0')}")
    print(f"  get k6 (should exist):     {c.get('k6')}")

    print("\nWaiting 3s for TTL expiry…")
    import time as _t
    _t.sleep(3)
    print(f"  get k6 after expiry: {c.get('k6')}")
    print(f"\nStats: {json.dumps(c.stats(), indent=2)}")


def _cmd_stats(_args: argparse.Namespace) -> None:
    print(json.dumps(_get_store().stats_all(), indent=2, ensure_ascii=False))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MRL_cache — LRU+TTL in-process cache",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo",  help="Run interactive demo")
    sub.add_parser("stats", help="Print stats for all cache namespaces")
    return p


def main() -> None:
    args = _build_argparser().parse_args()
    dispatch = {"demo": _cmd_demo, "stats": _cmd_stats}
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
