"""
test_MRL_mcp_server.py — 母體 MCP 閘口驗收(rl_13 出口即入口 / rl_19 MCP 基座)
origin_signature: MrLiouWord
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))

from MRL_MCP_Server_v1 import MRL_MCPServer, TOOLS, PROTOCOL_VERSION  # noqa: E402
from MRL_Platform_Server import api_mcp  # noqa: E402


def _call(srv, method, params=None, rid=1):
    return srv.handle({"jsonrpc": "2.0", "id": rid, "method": method,
                       "params": params or {}})


class TestMCPProtocol:
    def test_initialize(self):
        srv = MRL_MCPServer()
        r = _call(srv, "initialize")
        assert r["result"]["protocolVersion"] == PROTOCOL_VERSION
        assert r["result"]["serverInfo"]["origin_signature"] == "MrLiouWord"

    def test_tools_list(self):
        srv = MRL_MCPServer()
        r = _call(srv, "tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        assert "mother_status" in names and "mother_chat" in names
        assert "dl580_run" in names and "law_engine_loop" in names

    def test_ping(self):
        srv = MRL_MCPServer()
        assert _call(srv, "ping")["result"] == {}

    def test_unknown_method_errors(self):
        srv = MRL_MCPServer()
        r = _call(srv, "no/such/method")
        assert r["error"]["code"] == -32601

    def test_initialized_notification_no_response(self):
        srv = MRL_MCPServer()
        # notification(無 id)不回應
        assert srv.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


class TestMCPToolCalls:
    def test_mother_status(self):
        srv = MRL_MCPServer()
        r = _call(srv, "tools/call", {"name": "mother_status", "arguments": {}})
        assert r["result"]["isError"] is False
        content = json.loads(r["result"]["content"][0]["text"])
        assert content["rootlaw_version"] >= 9
        assert content["origin_signature"] == "MrLiouWord"

    def test_law_engine_loop(self):
        srv = MRL_MCPServer()
        r = _call(srv, "tools/call", {"name": "law_engine_loop", "arguments": {}})
        content = json.loads(r["result"]["content"][0]["text"])
        assert content["verified"] is True
        assert content["token"] == "MRL_FLOWAGENT_LAWENGINE_LOOP_PASS"

    def test_chat_requires_message(self):
        srv = MRL_MCPServer()
        r = _call(srv, "tools/call", {"name": "mother_chat", "arguments": {}})
        content = json.loads(r["result"]["content"][0]["text"])
        assert "error" in content        # 無 message 誠實回錯,不偽造

    def test_unknown_tool(self):
        srv = MRL_MCPServer()
        r = _call(srv, "tools/call", {"name": "nope", "arguments": {}})
        content = json.loads(r["result"]["content"][0]["text"])
        assert "unknown tool" in content["error"]

    def test_result_carries_origin_signature(self):
        srv = MRL_MCPServer()
        r = _call(srv, "tools/call", {"name": "mother_status", "arguments": {}})
        content = json.loads(r["result"]["content"][0]["text"])
        assert content["origin_signature"] == "MrLiouWord"


class TestMCPHttpBridge:
    def test_http_bridge_initialize(self):
        r = api_mcp({"jsonrpc": "2.0", "id": 7, "method": "initialize", "params": {}})
        assert r["result"]["protocolVersion"] == PROTOCOL_VERSION
        assert r["result"]["serverInfo"]["origin_signature"] == "MrLiouWord"

    def test_http_bridge_tools_list(self):
        r = api_mcp({"jsonrpc": "2.0", "id": 8, "method": "tools/list", "params": {}})
        names = [t["name"] for t in r["result"]["tools"]]
        assert "mother_status" in names and "law_engine_loop" in names

    def test_http_bridge_accepts_notifications(self):
        r = api_mcp({"jsonrpc": "2.0", "method": "notifications/initialized"})
        assert r["result"]["notification"] is True
        assert r["result"]["origin_signature"] == "MrLiouWord"

    def test_http_bridge_rejects_missing_method(self):
        # Empty body (e.g. JSON parse error fallback from _body()) must return error, not a stub.
        r = api_mcp({})
        assert "error" in r
        assert r["error"]["code"] == -32600

    def test_http_bridge_rejects_null_method(self):
        # method:null must be rejected — non-empty string required.
        r = api_mcp({"jsonrpc": "2.0", "method": None})
        assert "error" in r
        assert r["error"]["code"] == -32600

    def test_http_bridge_rejects_empty_method(self):
        # method:"" must be rejected — non-empty string required.
        r = api_mcp({"jsonrpc": "2.0", "method": ""})
        assert "error" in r
        assert r["error"]["code"] == -32600

    def test_http_bridge_rejects_non_dict(self):
        r = api_mcp("not a dict")
        assert "error" in r
        assert r["error"]["code"] == -32600
