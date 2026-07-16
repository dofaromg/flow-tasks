"""
test_tool_registry.py — Smoke tests for tool_registry.py
origin_signature: MrLiouWord
"""
from __future__ import annotations

import pytest

from tool_registry import ToolRegistry, ToolSpec, _make_builtin_registry


# ─── ToolSpec ─────────────────────────────────────────────────────────────────

class TestToolSpec:
    def test_schema_structure(self):
        def add(a: int, b: int) -> int:
            return a + b

        spec = ToolSpec("add", add, "Add two numbers", {"a": int, "b": int})
        schema = spec.schema()
        assert schema["name"] == "add"
        assert "a" in schema["parameters"]["properties"]
        assert "b" in schema["parameters"]["properties"]
        assert schema["parameters"]["properties"]["a"]["type"] == "integer"

    def test_validate_ok(self):
        spec = ToolSpec("echo", lambda m: m, "echo", {"message": str})
        assert spec.validate({"message": "hi"}) is None

    def test_validate_missing_param(self):
        spec = ToolSpec("add", lambda a, b: a + b, "", {"a": int, "b": int})
        err = spec.validate({"a": 1})
        assert err is not None
        assert "b" in err

    def test_validate_wrong_type(self):
        spec = ToolSpec("add", lambda a, b: a + b, "", {"a": int, "b": int})
        err = spec.validate({"a": "oops", "b": 2})
        assert err is not None

    def test_int_to_float_coercion_ok(self):
        spec = ToolSpec("f", lambda x: x, "", {"x": float})
        assert spec.validate({"x": 3}) is None  # int→float allowed


# ─── ToolRegistry ─────────────────────────────────────────────────────────────

class TestToolRegistryRegistration:
    def test_register_decorator(self):
        reg = ToolRegistry()

        @reg.register(description="Square a number", parameters={"n": int})
        def square(n: int) -> int:
            return n * n

        assert "square" in reg.list_tools()

    def test_register_infers_type_annotations(self):
        # NOTE: this test registers with explicit parameters dict because
        # `from __future__ import annotations` in this file makes all
        # annotations strings at runtime, not types.
        reg = ToolRegistry()

        @reg.register(description="Greeting", parameters={"name": str})
        def greet(name: str) -> str:
            return f"Hello, {name}"

        schema = reg.get_schema("greet")
        assert schema["parameters"]["properties"]["name"]["type"] == "string"

    def test_add_direct(self):
        reg = ToolRegistry()
        reg.add(lambda x: x, name="identity", description="identity", parameters={"x": str})
        assert "identity" in reg.list_tools()

    def test_remove_tool(self):
        reg = ToolRegistry()
        reg.add(lambda: None, name="tmp", description="", parameters={})
        assert reg.remove("tmp") is True
        assert "tmp" not in reg.list_tools()
        assert reg.remove("tmp") is False  # already gone

    def test_list_tools_sorted(self):
        reg = ToolRegistry()
        reg.add(lambda: None, name="z_tool", description="", parameters={})
        reg.add(lambda: None, name="a_tool", description="", parameters={})
        tools = reg.list_tools()
        assert tools == sorted(tools)


class TestToolRegistryCall:
    def setup_method(self):
        self.reg = _make_builtin_registry()

    def test_call_echo(self):
        result = self.reg.call("echo", {"message": "test"})
        assert result["ok"] is True
        assert result["output"] == "test"

    def test_call_add(self):
        result = self.reg.call("add", {"a": 3.0, "b": 4.0})
        assert result["ok"] is True
        assert result["output"] == pytest.approx(7.0)

    def test_call_now_ms(self):
        result = self.reg.call("now_ms", {})
        assert result["ok"] is True
        assert isinstance(result["output"], int)
        assert result["output"] > 0

    def test_call_unknown_tool(self):
        result = self.reg.call("nonexistent", {})
        assert result["ok"] is False
        assert "not registered" in (result["error"] or "")

    def test_call_validation_error(self):
        result = self.reg.call("add", {"a": "wrong", "b": 1.0})
        assert result["ok"] is False
        assert "validation error" in (result["error"] or "")

    def test_call_missing_param(self):
        result = self.reg.call("echo", {})
        assert result["ok"] is False

    def test_call_exception_captured(self):
        reg = ToolRegistry()

        @reg.register(description="Always fails", parameters={})
        def blowup() -> None:
            raise ValueError("boom")

        result = reg.call("blowup", {})
        assert result["ok"] is False
        assert "ValueError" in (result["error"] or "")

    def test_call_result_has_origin_signature(self):
        result = self.reg.call("echo", {"message": "hi"})
        assert result["origin_signature"] == "MrLiouWord"

    def test_call_result_has_elapsed_ms(self):
        result = self.reg.call("echo", {"message": "timing"})
        assert "elapsed_ms" in result
        assert result["elapsed_ms"] >= 0

    def test_call_log_appends(self):
        self.reg.call("echo", {"message": "log_test"})
        log = self.reg.call_log()
        assert any(r["tool"] == "echo" for r in log)


class TestToolRegistrySchemas:
    def test_all_schemas_returns_list(self):
        reg = _make_builtin_registry()
        schemas = reg.all_schemas()
        assert isinstance(schemas, list)
        assert len(schemas) >= 1

    def test_get_schema_unknown_returns_none(self):
        reg = ToolRegistry()
        assert reg.get_schema("unknown") is None
