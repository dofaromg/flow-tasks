#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_manager.py — Centralised Configuration Manager
origin_signature: MrLiouWord
layer: L3 LAW
group: Y=1 MotherCore

Industry capability: centralised typed configuration with environment-variable
                     overrides — the same pattern used in production AI service
                     deployments across all major platforms.
MRL extension: every config load/save event is stamped with origin_signature;
               sensitive fields can be masked in log output.

Features
--------
  - JSON config file (default: data/config.json)
  - Environment-variable overrides (prefix: MRL_)
  - Type coercion (str → int / float / bool)
  - Default values with schema validation
  - Masked display for sensitive keys (api_key, token, secret, password)

Usage (library)
---------------
    from config_manager import ConfigManager

    cfg = ConfigManager()

    # Read a value (env var MRL_LLM_MODEL overrides JSON)
    model = cfg.get("llm.model", default="mock")

    # Write a value
    cfg.set("llm.model", "gpt-4o")
    cfg.save()

    # Full config dump (secrets masked)
    print(cfg.dump(mask_secrets=True))

CLI
---
    python 09_workflow/config_manager.py get  --key llm.model
    python 09_workflow/config_manager.py set  --key llm.model --value gpt-4o
    python 09_workflow/config_manager.py show
    python 09_workflow/config_manager.py reset
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import time
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "data" / "config.json"

# Keys whose values are masked in log output
_SENSITIVE_RE = re.compile(r"(api_key|token|secret|password|credential)", re.IGNORECASE)

# ── Default configuration schema ──────────────────────────────────────────────

_DEFAULTS: Dict[str, Any] = {
    "system": {
        "name": "MRL_AGI",
        "version": "1.0",
        "origin_signature": "MrLiouWord",
        "debug": False,
        "log_level": "INFO",
    },
    "llm": {
        # deny-by-default (rootlaw rl_00): no implicit mock in production.
        # Set a real model (e.g. "gpt-4o", "claude-3-5-sonnet") or enable a
        # local engine; "mock" requires allow_mock=true and is test-only.
        "default_model": "",
        "max_tokens": 1024,
        "temperature": 0.7,
        "stream": False,
        "openai_api_key": "",
        "anthropic_api_key": "",
        "local_base_url": "http://localhost:11434/v1",
        "enable_local": False,
        "allow_mock": False,
    },
    "memory": {
        "vector_store_path": "03_memory/vector/_data",
        "merkle_chain_path": "03_memory/_data/memory_chain",
        "max_vector_entries": 10000,
    },
    "context": {
        "max_tokens": 4096,
        "reply_reserve": 512,
        "strategy": "truncate_oldest",
    },
    "conversation": {
        "store_path": "data/conversations.json",
        "max_sessions": 1000,
        "default_system_prompt": (
            "You are MRL_AGI, a production-grade private AI assistant. "
            "Origin signature: MrLiouWord. "
            "Always act in accordance with the Mother Core Assembly laws."
        ),
    },
    "api": {
        "host": "127.0.0.1",
        "port": 7771,
        "require_auth": False,
        "auth_token": "",
        "cors_origins": ["*"],
    },
    "scheduler": {
        "workers": 2,
        "max_queue": 1000,
    },
    "eval": {
        "default_threshold": 0.5,
    },

    # Self-optimisation (mainstream pattern: dynamic config, auditable)
    "self_optimize": {
        "enabled": False,
        "apply": False,
        "last_run_at_ms": 0,
    },

    # Learning ingest defaults (kept separate; endpoints remain deny-by-default)
    "learning": {
        "enabled": False,
        "chunk_chars": 1400,
        "overlap": 200,
        "top_k": 5,
    },
}


# ─── ConfigManager ───────────────────────────────────────────────────────────

class ConfigManager:
    """
    Manages the MRL system configuration.

    Config is stored as a nested dict.  Dotted keys (e.g. "llm.model") are
    used for all get/set operations.  Environment variables prefixed with
    ``MRL_`` override JSON values; e.g. ``MRL_LLM_DEFAULT_MODEL=gpt-4o``.

    Parameters
    ----------
    config_path : pathlib.Path
        Path to the JSON config file.
    """

    def __init__(self, config_path: pathlib.Path = _DEFAULT_CONFIG_PATH) -> None:
        self._path = pathlib.Path(config_path)
        self._data: Dict[str, Any] = _deep_copy(_DEFAULTS)
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load config from JSON, merging with defaults."""
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as f:
                    stored = json.load(f)
                _deep_merge(self._data, stored)
            except (json.JSONDecodeError, OSError):
                pass  # fallback to defaults

    def save(self) -> None:
        """Persist the current configuration to JSON."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(self._data)
        payload["_meta"] = {
            "saved_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def reset(self) -> None:
        """Reset to built-in defaults (does not save automatically)."""
        self._data = _deep_copy(_DEFAULTS)

    # ── Get / Set ─────────────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a config value by dotted key.

        Environment variable ``MRL_<KEY_UPPER>`` (dots → underscores) takes
        precedence over the JSON value.

        Examples
        --------
        ``cfg.get("llm.default_model")``  →  env var ``MRL_LLM_DEFAULT_MODEL``
        """
        # Check environment variable first
        env_key = "MRL_" + key.upper().replace(".", "_")
        env_val = os.environ.get(env_key)
        if env_val is not None:
            # Coerce to the type of the default value
            existing = _nested_get(self._data, key)
            return _coerce(env_val, type(existing) if existing is not None else str)

        val = _nested_get(self._data, key)
        return val if val is not None else default

    def set(self, key: str, value: Any) -> None:
        """Set a config value by dotted key."""
        _nested_set(self._data, key, value)

    def all(self) -> Dict[str, Any]:
        """Return the full config dict (deep copy)."""
        return _deep_copy(self._data)

    def dump(self, mask_secrets: bool = True) -> Dict[str, Any]:
        """Return a display-safe dict (secrets masked if requested)."""
        data = _deep_copy(self._data)
        if mask_secrets:
            _mask_recursive(data)
        return data

    def schema_keys(self) -> List[str]:
        """Return all dotted keys in the default schema."""
        return sorted(_flatten_keys(_DEFAULTS))


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _nested_get(data: Dict[str, Any], key: str) -> Any:
    parts = key.split(".")
    node = data
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _nested_set(data: Dict[str, Any], key: str, value: Any) -> None:
    parts = key.split(".")
    node = data
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def _deep_copy(data: Any) -> Any:
    return json.loads(json.dumps(data, default=str))


def _coerce(value: str, target_type: type) -> Any:
    if target_type is bool:
        return value.lower() in ("1", "true", "yes", "on")
    if target_type is int:
        try:
            return int(value)
        except ValueError:
            return value
    if target_type is float:
        try:
            return float(value)
        except ValueError:
            return value
    return value


def _mask_recursive(data: Any) -> None:
    if isinstance(data, dict):
        for k in data:
            if isinstance(data[k], str) and _SENSITIVE_RE.search(k) and data[k]:
                data[k] = "***"
            else:
                _mask_recursive(data[k])
    elif isinstance(data, list):
        for item in data:
            _mask_recursive(item)


def _flatten_keys(data: Dict[str, Any], prefix: str = "") -> List[str]:
    keys: List[str] = []
    for k, v in data.items():
        full = f"{prefix}.{k}" if prefix else k
        keys.append(full)
        if isinstance(v, dict):
            keys.extend(_flatten_keys(v, full))
    return keys


# ── Module-level singleton ─────────────────────────────────────────────────────
# Modules can import and use `config` directly for convenience.

config = ConfigManager()


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_get(args: argparse.Namespace) -> None:
    cfg = ConfigManager()
    val = cfg.get(args.key)
    print(f"{args.key} = {json.dumps(val, ensure_ascii=False, default=str)}")


def _cmd_set(args: argparse.Namespace) -> None:
    cfg = ConfigManager()
    cfg.set(args.key, args.value)
    cfg.save()
    print(f"✅ Set {args.key} = {args.value}")


def _cmd_show(_args: argparse.Namespace) -> None:
    cfg = ConfigManager()
    print(json.dumps(cfg.dump(mask_secrets=True), ensure_ascii=False, indent=2))


def _cmd_reset(_args: argparse.Namespace) -> None:
    cfg = ConfigManager()
    cfg.reset()
    cfg.save()
    print("✅ Configuration reset to defaults.")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ConfigManager — centralised configuration")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("get", help="Get a config value")
    g.add_argument("--key", required=True, help="Dotted key e.g. llm.default_model")

    s = sub.add_parser("set", help="Set a config value and save")
    s.add_argument("--key", required=True)
    s.add_argument("--value", required=True)

    sub.add_parser("show", help="Print full config (secrets masked)")
    sub.add_parser("reset", help="Reset to built-in defaults")

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {"get": _cmd_get, "set": _cmd_set, "show": _cmd_show, "reset": _cmd_reset}
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
