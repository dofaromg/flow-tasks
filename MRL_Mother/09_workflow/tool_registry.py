#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tool_registry.py — Tool / Function-Calling Registry and Executor
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

Industry capability: structured tool / function calling (OpenAI-style).
MRL extension: every tool invocation is stamped with origin_signature and
               each call record can be sealed into the MerkleChain.

A *Tool* is a named, schema-declared callable that the agent runtime can
invoke by name, validate inputs against a JSON-Schema-like spec, execute,
and record the outcome.

Usage (library)
---------------
    from tool_registry import ToolRegistry

    registry = ToolRegistry()

    @registry.register(
        description="Add two integers",
        parameters={"a": int, "b": int},
    )
    def add(a: int, b: int) -> int:
        return a + b

    result = registry.call("add", {"a": 3, "b": 4})
    print(result["output"])   # 7

CLI
---
    python 09_workflow/tool_registry.py list
    python 09_workflow/tool_registry.py call --tool add --args '{"a":3,"b":4}'
"""

from __future__ import annotations

import argparse
import inspect
import json
import time
import traceback
from typing import Any, Callable, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"

# ─── Type helpers ─────────────────────────────────────────────────────────────

_PY_TO_JSON_TYPE: Dict[type, str] = {
    int: "integer",
    float: "number",
    str: "string",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _py_type_name(t: type) -> str:
    return _PY_TO_JSON_TYPE.get(t, "any")


# ─── ToolSpec ─────────────────────────────────────────────────────────────────

class ToolSpec:
    """Metadata + callable for a single registered tool."""

    def __init__(
        self,
        name: str,
        fn: Callable[..., Any],
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.fn = fn
        self.description = description
        # parameters: {param_name: type_or_spec}
        self._params: Dict[str, Any] = parameters or {}

    def schema(self) -> Dict[str, Any]:
        """Return an OpenAI-style function schema dict."""
        props: Dict[str, Any] = {}
        for param, spec in self._params.items():
            if isinstance(spec, type):
                props[param] = {"type": _py_type_name(spec)}
            elif isinstance(spec, dict):
                props[param] = spec
            else:
                props[param] = {"type": "any"}
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": list(self._params.keys()),
            },
        }

    def validate(self, kwargs: Dict[str, Any]) -> Optional[str]:
        """Return an error string if kwargs are invalid, else None."""
        for param, spec in self._params.items():
            if param not in kwargs:
                return f"missing required parameter: '{param}'"
            if isinstance(spec, type) and not isinstance(kwargs[param], spec):
                # Allow int→float coercion
                if spec is float and isinstance(kwargs[param], int):
                    continue
                return (
                    f"parameter '{param}' expected {spec.__name__}, "
                    f"got {type(kwargs[param]).__name__}"
                )
        return None


# ─── ToolRegistry ─────────────────────────────────────────────────────────────

class ToolRegistry:
    """
    Registry of callable tools with schema declaration, validation, and
    full call-record logging compatible with the MRL trace format.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}
        self._call_log: List[Dict[str, Any]] = []

    # ── Registration ──────────────────────────────────────────────────────────

    def register(
        self,
        *,
        name: Optional[str] = None,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator factory.  Usage::

            @registry.register(description="...", parameters={"x": int})
            def my_tool(x: int) -> int: ...
        """
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or fn.__name__
            desc = description or (inspect.getdoc(fn) or "")
            # If parameters not given explicitly, infer from type annotations
            params = parameters
            if params is None:
                hints = {
                    k: v
                    for k, v in (fn.__annotations__ or {}).items()
                    if k != "return"
                }
                params = hints if hints else {}
            self._tools[tool_name] = ToolSpec(tool_name, fn, desc, params)
            return fn
        return decorator

    def add(
        self,
        fn: Callable[..., Any],
        *,
        name: Optional[str] = None,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> "ToolRegistry":
        """Register a tool directly (non-decorator form)."""
        decorator = self.register(name=name, description=description, parameters=parameters)
        decorator(fn)
        return self

    def remove(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    # ── Query ─────────────────────────────────────────────────────────────────

    def list_tools(self) -> List[str]:
        return sorted(self._tools.keys())

    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        spec = self._tools.get(name)
        return spec.schema() if spec else None

    def all_schemas(self) -> List[Dict[str, Any]]:
        return [self._tools[n].schema() for n in sorted(self._tools)]

    # ── Execution ─────────────────────────────────────────────────────────────

    def call(
        self,
        name: str,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Invoke a registered tool by name.

        Returns::

            {
              "tool":             <name>,
              "input":            <kwargs>,
              "output":           <return value or None>,
              "error":            <error message or None>,
              "ok":               True | False,
              "elapsed_ms":       <int>,
              "called_at_ms":     <int>,
              "origin_signature": "MrLiouWord",
            }
        """
        kwargs = kwargs or {}
        called_at = int(time.time() * 1000)
        record: Dict[str, Any] = {
            "tool": name,
            "input": kwargs,
            "output": None,
            "error": None,
            "ok": False,
            "elapsed_ms": 0,
            "called_at_ms": called_at,
            "origin_signature": ORIGIN_SIGNATURE,
        }

        spec = self._tools.get(name)
        if spec is None:
            record["error"] = f"tool '{name}' not registered"
            self._call_log.append(record)
            return record

        err = spec.validate(kwargs)
        if err:
            record["error"] = f"validation error: {err}"
            self._call_log.append(record)
            return record

        t0 = time.time()
        try:
            output = spec.fn(**kwargs)
            record["output"] = output
            record["ok"] = True
        except Exception as exc:  # noqa: BLE001
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["traceback"] = traceback.format_exc()
        finally:
            record["elapsed_ms"] = int((time.time() - t0) * 1000)

        self._call_log.append(record)
        return record

    def call_log(self) -> List[Dict[str, Any]]:
        """Return all recorded call records (defensive copy)."""
        return list(self._call_log)


# ─── Built-in demo tools ──────────────────────────────────────────────────────

def _make_builtin_registry() -> ToolRegistry:
    reg = ToolRegistry()

    @reg.register(description="Return the current UTC timestamp in milliseconds.")
    def now_ms() -> int:
        return int(time.time() * 1000)

    @reg.register(
        description="Echo back the supplied message string.",
        parameters={"message": str},
    )
    def echo(message: str) -> str:
        return message

    @reg.register(
        description="Add two numbers.",
        parameters={"a": float, "b": float},
    )
    def add(a: float, b: float) -> float:
        return a + b

    return reg


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _cmd_list(_args: argparse.Namespace) -> None:
    reg = _make_builtin_registry()
    names = reg.list_tools()
    print(f"{len(names)} built-in tool(s):")
    for n in names:
        s = reg.get_schema(n)
        print(f"  {n} — {s['description']}")


def _cmd_call(args: argparse.Namespace) -> None:
    reg = _make_builtin_registry()
    kwargs = json.loads(args.args) if args.args else {}
    result = reg.call(args.tool, kwargs)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ToolRegistry — function-calling registry")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List built-in tools")

    c = sub.add_parser("call", help="Call a built-in tool")
    c.add_argument("--tool", required=True)
    c.add_argument("--args", default="", help="JSON kwargs string")

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    if args.cmd == "list":
        _cmd_list(args)
    elif args.cmd == "call":
        _cmd_call(args)


if __name__ == "__main__":
    main()
