#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_runtime_config.py — Runtime Configuration & Adapter Control
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=1 MotherCore

Production runtime configuration that enforces:
  1. MockAdapter is ONLY allowed in test/dev mode
  2. Production must use LocalAdapter or cloud adapters (OpenAI/Anthropic)
  3. All responses include runtime_origin, trace_id, and engine metadata

Usage (library)
---------------
    from MRL_runtime_config import RuntimeMode, get_production_adapter

    # Check if we're in production
    if RuntimeMode.is_production():
        adapter = get_production_adapter(config)
    else:
        adapter = MockAdapter()  # Only in test mode

CLI
---
    python 09_workflow/MRL_runtime_config.py check
    python 09_workflow/MRL_runtime_config.py list-adapters
"""

from __future__ import annotations

import argparse
import json
import os
from enum import Enum
from typing import Any, Dict, Optional

ORIGIN_SIGNATURE = "MrLiouWord"


# ─── RuntimeMode ──────────────────────────────────────────────────────────────

class RuntimeMode(str, Enum):
    """Runtime environment mode."""
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TEST = "test"

    @classmethod
    def current(cls) -> "RuntimeMode":
        """
        Determine current runtime mode from environment.

        Environment variable: MRL_RUNTIME_MODE
        Default: development
        """
        mode = os.environ.get("MRL_RUNTIME_MODE", "development").lower()
        if mode in ("prod", "production"):
            return cls.PRODUCTION
        elif mode in ("test", "testing"):
            return cls.TEST
        else:
            return cls.DEVELOPMENT

    @classmethod
    def is_production(cls) -> bool:
        """Check if we're running in production mode."""
        return cls.current() == cls.PRODUCTION

    @classmethod
    def is_test(cls) -> bool:
        """Check if we're running in test mode."""
        return cls.current() == cls.TEST


# ─── RuntimeConfig ────────────────────────────────────────────────────────────

class RuntimeConfig:
    """
    Production runtime configuration enforcer.

    Ensures:
      - MockAdapter is prohibited in production
      - All responses include trace metadata
      - Runtime origin is properly tracked
    """

    def __init__(self, mode: Optional[RuntimeMode] = None) -> None:
        self.mode = mode or RuntimeMode.current()
        self._allowed_adapters = self._get_allowed_adapters()

    def _get_allowed_adapters(self) -> Dict[str, bool]:
        """Return which adapters are allowed in current mode."""
        if self.mode == RuntimeMode.PRODUCTION:
            return {
                "mock": False,       # PROHIBITED in production
                "openai": True,
                "anthropic": True,
                "local": True,       # DL580 local models
            }
        elif self.mode == RuntimeMode.TEST:
            return {
                "mock": True,        # Allowed for testing
                "openai": False,     # Avoid API costs in tests
                "anthropic": False,
                "local": True,       # Local models OK for tests
            }
        else:  # DEVELOPMENT
            return {
                "mock": True,
                "openai": True,
                "anthropic": True,
                "local": True,
            }

    def is_adapter_allowed(self, adapter_name: str) -> bool:
        """Check if an adapter is allowed in current runtime mode."""
        return self._allowed_adapters.get(adapter_name.lower(), False)

    def validate_adapter(self, adapter_name: str) -> None:
        """
        Validate that an adapter is allowed in current mode.

        Raises
        ------
        RuntimeError if adapter is prohibited in current mode.
        """
        if not self.is_adapter_allowed(adapter_name):
            raise RuntimeError(
                f"Adapter '{adapter_name}' is PROHIBITED in {self.mode.value} mode. "
                f"Allowed adapters: {[k for k, v in self._allowed_adapters.items() if v]}"
            )

    def validate_model(self, model: str) -> None:
        """
        Validate that a model string corresponds to an allowed adapter.

        Raises
        ------
        RuntimeError if model uses a prohibited adapter.
        """
        if model.startswith("mock"):
            self.validate_adapter("mock")
        elif model.startswith("gpt"):
            self.validate_adapter("openai")
        elif model.startswith("claude"):
            self.validate_adapter("anthropic")
        # Local models typically use actual model names
        # No validation needed as local is usually allowed

    def enrich_response(
        self,
        response: Dict[str, Any],
        adapter_name: str,
        model: str,
    ) -> Dict[str, Any]:
        """
        Enrich a response with runtime metadata.

        Adds:
          - runtime_mode: current mode
          - runtime_origin: where the model is running
          - engine: adapter type
          - model: model name
          - origin_signature: MrLiouWord
        """
        response["runtime_mode"] = self.mode.value
        response["runtime_origin"] = self._get_runtime_origin(adapter_name)
        response["engine"] = adapter_name
        response["model"] = model
        response["origin_signature"] = ORIGIN_SIGNATURE
        return response

    def _get_runtime_origin(self, adapter_name: str) -> str:
        """Determine where the runtime is executing."""
        if adapter_name == "local":
            return os.environ.get("MRL_LOCAL_RUNTIME", "DL580_localhost")
        elif adapter_name == "mock":
            return "mock_runtime"
        elif adapter_name in ("openai", "anthropic"):
            return f"{adapter_name}_cloud"
        return "unknown"


# ─── Adapter factory ─────────────────────────────────────────────────────────

def get_production_adapter(config: Any) -> Any:
    """
    Get a production-ready adapter from config.

    Priority order:
      1. Local adapter (DL580) if configured
      2. OpenAI adapter if API key present
      3. Anthropic adapter if API key present
      4. Raise error (no production adapter available)

    Parameters
    ----------
    config : ConfigManager instance with llm.* settings

    Returns
    -------
    LLMAdapter instance

    Raises
    ------
    RuntimeError if no production adapter can be configured
    """
    from llm_adapter import LocalAdapter, OpenAIAdapter, AnthropicAdapter

    runtime_cfg = RuntimeConfig()
    runtime_cfg.validate_adapter("mock")  # This will raise if we're in production

    # Try local adapter first (DL580)
    local_url = config.get("llm.local_base_url", "http://localhost:11434/v1")
    if local_url and runtime_cfg.is_adapter_allowed("local"):
        try:
            adapter = LocalAdapter(base_url=local_url, api_key="local")
            return adapter
        except Exception:
            pass  # Try next option

    # Try OpenAI
    openai_key = config.get("llm.openai_api_key", "")
    if openai_key and runtime_cfg.is_adapter_allowed("openai"):
        return OpenAIAdapter(api_key=openai_key)

    # Try Anthropic
    anthropic_key = config.get("llm.anthropic_api_key", "")
    if anthropic_key and runtime_cfg.is_adapter_allowed("anthropic"):
        from llm_adapter import AnthropicAdapter
        return AnthropicAdapter(api_key=anthropic_key)

    raise RuntimeError(
        f"No production adapter available in {runtime_cfg.mode.value} mode. "
        "Please configure llm.local_base_url, llm.openai_api_key, or llm.anthropic_api_key."
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_check(_args: argparse.Namespace) -> None:
    """Check current runtime configuration."""
    cfg = RuntimeConfig()
    print(f"Runtime mode: {cfg.mode.value}")
    print(f"Environment: {os.environ.get('MRL_RUNTIME_MODE', '(not set, using default)')}")
    print("\nAllowed adapters:")
    for adapter, allowed in cfg._allowed_adapters.items():
        status = "✓ ALLOWED" if allowed else "✗ PROHIBITED"
        print(f"  {adapter:12s} {status}")
    print(f"\nOrigin signature: {ORIGIN_SIGNATURE}")


def _cmd_list_adapters(_args: argparse.Namespace) -> None:
    """List adapter availability in all modes."""
    modes = [RuntimeMode.PRODUCTION, RuntimeMode.DEVELOPMENT, RuntimeMode.TEST]

    for mode in modes:
        cfg = RuntimeConfig(mode=mode)
        print(f"\n=== {mode.value.upper()} ===")
        for adapter, allowed in cfg._allowed_adapters.items():
            status = "✓" if allowed else "✗"
            print(f"  {status} {adapter}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MRL_runtime_config — Runtime configuration and adapter control"
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="Check current runtime configuration")
    sub.add_parser("list-adapters", help="List adapter availability in all modes")
    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "check": _cmd_check,
        "list-adapters": _cmd_list_adapters,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()