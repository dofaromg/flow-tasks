#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api_gateway.py — REST API Gateway
origin_signature: MrLiouWord
layer: L7 LOOP  (Platform tier)
group: Y=1 MotherCore

Industry capability: HTTP REST API gateway that exposes all MRL_AGI
                     capabilities to external clients — the same pattern used
                     by OpenAI, Anthropic, and Google to serve their AI APIs.
MRL extension: every request is wrapped in an MRL trace record stamped with
               origin_signature; responses include the request_id for auditability.

Endpoints
---------
  GET  /health                       — health check + subsystem status
  POST /chat                         — single-turn or multi-turn chat completion
  POST /chat/stream                  — SSE streaming chat completion
  GET  /sessions                     — list conversation sessions
  POST /sessions                     — create a new session
  GET  /sessions/{id}                — get session history
  DELETE /sessions/{id}              — delete a session
  POST /agent/run                    — run an agent task
  POST /eval                         — evaluate an output string
  POST /seal                         — seal text through the reversible chain
  GET  /tools                        — list registered tools
  POST /tools/{name}                 — call a tool by name
  GET  /templates                    — list prompt templates
  POST /templates                    — add / update a template
  POST /templates/{id}/render        — render a template
  GET  /config                       — get full config (secrets masked)
  POST /config                       — set a config key
  GET  /metrics                      — MRL_metrics telemetry snapshot
  POST /guard                        — run guardrail check on text
  POST /export/{sid}                 — export session as Markdown

Security
--------
  If ``require_auth`` is True in config, all requests must include:
    Authorization: Bearer <auth_token>
  Rate limiting:
    Configure api.rate_limit_per_minute (0 = disabled) in config.

CORS
----
  All responses include Access-Control-* headers.
  Allowed origins configured via api.cors_origins (default ["*"]).

  Learning endpoints follow mainstream production patterns:
  - deny-by-default feature flag (learning.enabled)
  - requires auth (api.require_auth=true) to prevent data exfiltration

  Learning endpoints follow mainstream production patterns:
  - deny-by-default feature flag (learning.enabled)
  - requires auth (api.require_auth=true) to prevent data exfiltration

Usage
-----
    python 09_workflow/api_gateway.py serve
    python 09_workflow/api_gateway.py serve --host 0.0.0.0 --port 7771
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

ORIGIN_SIGNATURE = "MrLiouWord"
GATEWAY_VERSION = "1.0"
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── Ensure module search paths ────────────────────────────────────────────────

def _ensure_paths() -> None:
    for sub in [
        _REPO_ROOT / "09_workflow",
        _REPO_ROOT / "03_memory" / "merkle",
        _REPO_ROOT / "03_memory" / "vector",
        _REPO_ROOT / "05_persona",
    ]:
        p = str(sub)
        if p not in sys.path:
            sys.path.insert(0, p)

_ensure_paths()


def _try_import(module: str, attr: str) -> Any:
    try:
        import importlib
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    except Exception:  # noqa: BLE001
        return None


# ─── Gateway state ────────────────────────────────────────────────────────────

class _GatewayState:
    """Singleton that holds the booted MotherAssembly and config."""

    def __init__(self) -> None:
        self.assembly: Any = None
        self.cfg: Any = None
        self._booted = False

    def boot(self) -> Dict[str, Any]:
        if self._booted:
            return {"already_booted": True}

        # Config
        ConfigManager = _try_import("config_manager", "ConfigManager")
        if ConfigManager:
            self.cfg = ConfigManager()

        # MotherAssembly
        MotherAssembly = _try_import("mother_assembly", "MotherAssembly")
        if MotherAssembly:
            self.assembly = MotherAssembly()
            report = self.assembly.boot()
        else:
            report = {"error": "MotherAssembly unavailable"}

        self._booted = True
        return report

    @property
    def require_auth(self) -> bool:
        if self.cfg:
            return bool(self.cfg.get("api.require_auth", False))
        return False

    @property
    def auth_token(self) -> str:
        if self.cfg:
            return str(self.cfg.get("api.auth_token", ""))
        return ""


_STATE = _GatewayState()


# ─── CORS helpers ─────────────────────────────────────────────────────────────

def _cors_origins() -> List[str]:
    """Return the list of allowed CORS origins from config."""
    if _STATE.cfg:
        val = _STATE.cfg.get("api.cors_origins", ["*"])
        if isinstance(val, list):
            return val
        return [str(val)]
    return ["*"]


def _add_cors_headers(handler: "BaseHTTPRequestHandler") -> None:
    """Add Access-Control-* headers to the response."""
    origins = _cors_origins()
    raw_origin = handler.headers.get("Origin", "")
    # Sanitise: strip CR/LF to prevent HTTP response-splitting injection
    origin = raw_origin.replace("\r", "").replace("\n", "").strip()
    if "*" in origins:
        handler.send_header("Access-Control-Allow-Origin", "*")
    elif origin and origin in origins:
        handler.send_header("Access-Control-Allow-Origin", origin)
    handler.send_header(
        "Access-Control-Allow-Methods",
        "GET, POST, DELETE, OPTIONS",
    )
    handler.send_header(
        "Access-Control-Allow-Headers",
        "Content-Type, Authorization, X-Request-Id",
    )
    handler.send_header("Access-Control-Max-Age", "86400")


# ─── Rate-limit helper ────────────────────────────────────────────────────────

def _get_client_key(handler: "BaseHTTPRequestHandler") -> str:
    """Derive a client key for rate limiting (IP or auth token)."""
    by = "ip"
    if _STATE.cfg:
        by = str(_STATE.cfg.get("api.rate_limit_by", "ip"))
    if by == "token":
        auth = handler.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
    # Fallback to IP
    return handler.client_address[0]


def _check_rate_limit(handler: "BaseHTTPRequestHandler", request_id: str) -> bool:
    """Return True if the request is allowed; send 429 and return False if throttled."""
    RateLimiter = _try_import("MRL_rate_limiter", "get_limiter")
    if RateLimiter is None:
        return True
    limiter = RateLimiter()
    key = _get_client_key(handler)
    allowed, info = limiter.check(key)
    if not allowed:
        retry_after = info.get("retry_after_s") or 60
        body: Dict[str, Any] = {
            "error": "Too Many Requests",
            "retry_after_s": retry_after,
            "limit": info.get("limit"),
            "window_seconds": info.get("window_seconds"),
        }
        encoded = json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
        handler.send_response(429)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(encoded)))
        handler.send_header("Retry-After", str(int(retry_after) + 1))
        handler.send_header("X-Request-Id", request_id)
        _add_cors_headers(handler)
        handler.end_headers()
        handler.wfile.write(encoded)
        return False
    return True


# ─── JSON helpers ─────────────────────────────────────────────────────────────

def _json_response(
    handler: "BaseHTTPRequestHandler",
    status: int,
    body: Any,
    request_id: str = "",
) -> None:
    if isinstance(body, dict) and request_id:
        body["request_id"] = request_id
        body["origin_signature"] = ORIGIN_SIGNATURE
    encoded = json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.send_header("X-Request-Id", request_id)
    _add_cors_headers(handler)
    handler.end_headers()
    handler.wfile.write(encoded)


def _read_json_body(handler: "BaseHTTPRequestHandler") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}, None
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON: {exc}"


def _check_auth(handler: "BaseHTTPRequestHandler") -> bool:
    if not _STATE.require_auth:
        return True
    auth = handler.headers.get("Authorization", "")
    expected = f"Bearer {_STATE.auth_token}"
    return auth == expected


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("1", "true", "yes", "on"):
            return True
        if normalized in ("0", "false", "no", "off"):
            return False
        return default
    return default


def _chat_error_status(error_msg: str) -> int:
    msg = error_msg.lower()
    if msg.startswith("llm error"):
        # 上游 LLM/adapter 失敗（含依賴缺失）一律 502，避免錯誤訊息內
        # 恰含 "required" 等字樣而誤判為 400 使用者錯誤
        return 502
    if "session not found" in msg:
        return 404
    if "required" in msg or "invalid" in msg:
        return 400
    if "unavailable" in msg or "not booted" in msg:
        return 503
    return 502


def _require_learning_enabled() -> Tuple[bool, str]:
    if _STATE.cfg is None:
        return False, "ConfigManager unavailable"
    enabled = bool(_STATE.cfg.get("learning.enabled", False))
    if not enabled:
        return False, "Learning endpoints disabled"
    require_auth = bool(_STATE.cfg.get("api.require_auth", False))
    if not require_auth:
        return False, "Learning requires api.require_auth=true"
    OnlyHost = _try_import("MRL_host_guard", "is_dl580_canonical_host")
    if OnlyHost is None:
        return False, "Host guard unavailable"
    ok_host, err_host = OnlyHost()
    if not ok_host:
        return False, f"DL580_ONLY: {err_host}"
    return True, ""


# ─── Request handler ──────────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt: str, *args: Any) -> None:
        # Suppress default noisy access log
        pass

    def _request_id(self) -> str:
        return str(uuid.uuid4())

    def _trace_id(self) -> str:
        return str(uuid.uuid4())

    # ── CORS preflight ────────────────────────────────────────────────────────

    def do_OPTIONS(self) -> None:
        rid = self._request_id()
        self.send_response(204)
        _add_cors_headers(self)
        self.send_header("Content-Length", "0")
        self.send_header("X-Request-Id", rid)
        self.end_headers()

    # ── Auth gate ─────────────────────────────────────────────────────────────

    def _require_auth(self, request_id: str) -> bool:
        if not _check_auth(self):
            _json_response(self, 401, {"error": "Unauthorized"}, request_id)
            return False
        return True

    # ── Routing ───────────────────────────────────────────────────────────────

    def do_GET(self) -> None:
        rid = self._request_id()
        if not self._require_auth(rid):
            return
        if not _check_rate_limit(self, rid):
            return
        path = urlparse(self.path).path.rstrip("/")
        routes: Dict[str, Any] = {
            "/health":     self._get_health,
            "/sessions":   self._get_sessions,
            "/tools":      self._get_tools,
            "/templates":  self._get_templates,
            "/config":     self._get_config,
            "/metrics":    self._get_metrics,
        }
        # Dynamic route: /sessions/{id}
        if path.startswith("/sessions/"):
            self._get_session(path.split("/sessions/")[1], rid)
            return
        fn = routes.get(path)
        if fn:
            fn(rid)
        else:
            _json_response(self, 404, {"error": f"Not found: {path}"}, rid)

    def do_POST(self) -> None:
        rid = self._request_id()
        if not self._require_auth(rid):
            return
        if not _check_rate_limit(self, rid):
            return
        path = urlparse(self.path).path.rstrip("/")
        body, err = _read_json_body(self)
        if err:
            _json_response(self, 400, {"error": err}, rid)
            return

        routes: Dict[str, Any] = {
            "/chat":       lambda: self._post_chat(body, rid),
            "/chat/stream": lambda: self._post_chat_stream(body, rid),
            "/sessions":   lambda: self._post_sessions(body, rid),
            "/agent/run":  lambda: self._post_agent_run(body, rid),
            "/eval":       lambda: self._post_eval(body, rid),
            "/seal":       lambda: self._post_seal(body, rid),
            "/learn/ingest_path": lambda: self._post_learn_ingest_path(body, rid),
            "/learn/ingest_url":  lambda: self._post_learn_ingest_url(body, rid),
            "/learn/query":       lambda: self._post_learn_query(body, rid),
            "/templates":  lambda: self._post_templates(body, rid),
            "/config":     lambda: self._post_config(body, rid),
            "/guard":      lambda: self._post_guard(body, rid),
        }
        # Dynamic: /templates/{id}/render
        if path.startswith("/templates/") and path.endswith("/render"):
            tid = path.split("/templates/")[1].split("/render")[0]
            self._post_template_render(tid, body, rid)
            return
        # Dynamic: /tools/{name}
        if path.startswith("/tools/"):
            tname = path.split("/tools/")[1]
            self._post_tool_call(tname, body, rid)
            return
        # Dynamic: /export/{sid}
        if path.startswith("/export/"):
            sid = path.split("/export/")[1]
            self._post_export(sid, rid)
            return

        fn = routes.get(path)
        if fn:
            fn()
        else:
            _json_response(self, 404, {"error": f"Not found: {path}"}, rid)

    def do_DELETE(self) -> None:
        rid = self._request_id()
        if not self._require_auth(rid):
            return
        if not _check_rate_limit(self, rid):
            return
        path = urlparse(self.path).path.rstrip("/")
        if path.startswith("/sessions/"):
            self._delete_session(path.split("/sessions/")[1], rid)
        else:
            _json_response(self, 404, {"error": f"Not found: {path}"}, rid)

    # ── GET handlers ──────────────────────────────────────────────────────────

    def _get_health(self, rid: str) -> None:
        if _STATE.assembly:
            status = _STATE.assembly.status()
        else:
            status = {"booted": False}
        _json_response(self, 200, {"status": "ok", "gateway_version": GATEWAY_VERSION, **status}, rid)

    def _get_sessions(self, rid: str) -> None:
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        if ConvMgr is None:
            _json_response(self, 503, {"error": "ConversationManager unavailable"}, rid)
            return
        mgr = ConvMgr()
        _json_response(self, 200, {"sessions": mgr.list_sessions()}, rid)

    def _get_session(self, session_id: str, rid: str) -> None:
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        if ConvMgr is None:
            _json_response(self, 503, {"error": "ConversationManager unavailable"}, rid)
            return
        mgr = ConvMgr()
        try:
            history = mgr.get_history(session_id)
            _json_response(self, 200, {"session_id": session_id, "messages": history}, rid)
        except KeyError:
            _json_response(self, 404, {"error": f"Session not found: {session_id}"}, rid)

    def _get_tools(self, rid: str) -> None:
        if _STATE.assembly and _STATE.assembly.tool_registry:
            schemas = _STATE.assembly.tool_registry.all_schemas()
            _json_response(self, 200, {"tools": schemas}, rid)
        else:
            _json_response(self, 503, {"error": "ToolRegistry unavailable"}, rid)

    def _get_templates(self, rid: str) -> None:
        if _STATE.assembly and _STATE.assembly.template_registry:
            ids = _STATE.assembly.template_registry.list_ids()
            _json_response(self, 200, {"templates": ids}, rid)
        else:
            _json_response(self, 503, {"error": "TemplateRegistry unavailable"}, rid)

    def _get_config(self, rid: str) -> None:
        if _STATE.cfg:
            _json_response(self, 200, {"config": _STATE.cfg.dump(mask_secrets=True)}, rid)
        else:
            _json_response(self, 503, {"error": "ConfigManager unavailable"}, rid)

    def _get_metrics(self, rid: str) -> None:
        """Return the current MRL_metrics snapshot."""
        metrics_snapshot = _try_import("MRL_metrics", "snapshot")
        if metrics_snapshot:
            _json_response(self, 200, {"metrics": metrics_snapshot()}, rid)
        else:
            _json_response(self, 503, {"error": "MRL_metrics unavailable"}, rid)

    # ── POST handlers ─────────────────────────────────────────────────────────

    def _post_chat(self, body: Dict[str, Any], rid: str) -> None:
        """
        Single-turn or session-based chat completion via MotherAssembly.chat()
        (session/model resolution lives there; the LLMGateway is called inside).

        Request body:
          message    : str  (required) — user message
          session_id : str  (optional) — continue an existing session
          model      : str  (optional) — LLM model name (default from config)
          system     : str  (optional) — system prompt (new sessions only)
          temperature: float (optional, 0~2)
        """
        trace_id = self._trace_id()
        message = body.get("message", "")
        if not message:
            _json_response(
                self,
                400,
                {
                    "error": "'message' is required",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        if _STATE.assembly is None:
            _json_response(
                self,
                503,
                {
                    "error": "MRL runtime unavailable (MotherAssembly not booted)",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        requested_model = str(body.get("model") or "").strip() or None
        cfg_default_model = (
            str(_STATE.cfg.get("llm.default_model", "")) if _STATE.cfg else ""
        ).strip() or None
        allow_mock = _coerce_bool(
            _STATE.cfg.get("llm.allow_mock", False) if _STATE.cfg else False,
            default=False,
        )

        if requested_model is None:
            if cfg_default_model is None:
                _json_response(
                    self,
                    400,
                    {
                        "error": "'model' is required unless llm.default_model is configured",
                        "engine": "mrl_runtime",
                        "runtime_origin": "local_mother_assembly",
                        "trace_id": trace_id,
                    },
                    rid,
                )
                return
            requested_model = cfg_default_model

        if requested_model.startswith("mock") and not allow_mock:
            _json_response(
                self,
                403,
                {
                    "error": "MockAdapter is test-only. Set llm.allow_mock=true to enable.",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        session_id = body.get("session_id")
        system_prompt = body.get("system", "")
        try:
            max_tokens = int(body.get("max_tokens", 1024))
        except (TypeError, ValueError):
            _json_response(
                self,
                400,
                {
                    "error": "'max_tokens' must be an integer",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return
        if max_tokens <= 0:
            _json_response(
                self,
                400,
                {
                    "error": "'max_tokens' must be > 0",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        try:
            temperature = float(body.get("temperature", 0.7))
        except (TypeError, ValueError):
            _json_response(
                self,
                400,
                {
                    "error": "'temperature' must be a number",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return
        temperature_in_range = MIN_TEMPERATURE <= temperature <= MAX_TEMPERATURE
        if not temperature_in_range:
            _json_response(
                self,
                400,
                {
                    "error": f"'temperature' must be between {MIN_TEMPERATURE} and {MAX_TEMPERATURE}",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        try:
            result = _STATE.assembly.chat(
                message,
                session_id=session_id or None,
                model=requested_model,
                system_prompt=system_prompt or None,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as exc:  # noqa: BLE001
            debug_mode = _coerce_bool(
                _STATE.cfg.get("system.debug", False) if _STATE.cfg else False,
                default=False,
            )
            _json_response(
                self,
                500,
                {
                    "error": "MRL runtime error",
                    "error_type": type(exc).__name__,
                    **({"error_detail": str(exc)} if debug_mode else {}),
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        if isinstance(result, dict) and result.get("error"):
            err = str(result.get("error", "MRL runtime error"))
            _json_response(
                self,
                _chat_error_status(err),
                {
                    **result,
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        _json_response(
            self,
            200,
            {
                **(result if isinstance(result, dict) else {"result": result}),
                "engine": "mrl_runtime",
                "runtime_origin": "local_mother_assembly",
                "trace_id": trace_id,
            },
            rid,
        )

    def _post_sessions(self, body: Dict[str, Any], rid: str) -> None:
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        if ConvMgr is None:
            _json_response(self, 503, {"error": "ConversationManager unavailable"}, rid)
            return
        mgr = ConvMgr()
        system = body.get("system_prompt", "")
        label = body.get("label", "")
        sid = mgr.new_session(system_prompt=system, label=label)
        _json_response(self, 201, {"session_id": sid, "label": label}, rid)

    def _delete_session(self, session_id: str, rid: str) -> None:
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        if ConvMgr is None:
            _json_response(self, 503, {"error": "ConversationManager unavailable"}, rid)
            return
        mgr = ConvMgr()
        ok = mgr.delete_session(session_id)
        if ok:
            _json_response(self, 200, {"deleted": session_id}, rid)
        else:
            _json_response(self, 404, {"error": f"Session not found: {session_id}"}, rid)

    def _post_agent_run(self, body: Dict[str, Any], rid: str) -> None:
        trace_id = self._trace_id()
        goal = body.get("goal", "")
        if not goal:
            _json_response(
                self,
                400,
                {
                    "error": "'goal' is required",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return
        if _STATE.assembly is None:
            _json_response(
                self,
                503,
                {
                    "error": "MotherAssembly unavailable",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        # This endpoint is the product-grade task orchestrator entry.
        # For now we run synchronously but return a formal task envelope.
        task_id = str(uuid.uuid4())
        started_ms = int(time.time() * 1000)
        try:
            status = "RUNNING"
            result = _STATE.assembly.run_agent(goal)
            if isinstance(result, dict) and result.get("error"):
                status = "FAILED"
            elif isinstance(result, dict) and result.get("finished") is False:
                # planner 用盡 max_steps 未完成目標：不誤標 DONE（review PR#77）
                status = "INCOMPLETE"
            else:
                status = "DONE"
            ended_ms = int(time.time() * 1000)
            _json_response(
                self,
                502 if status == "FAILED" else 200,
                {
                    "task_id": task_id,
                    "status": status,
                    "result": result,
                    "error_trace": result.get("error") if isinstance(result, dict) else None,
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                    "started_at_ms": started_ms,
                    "ended_at_ms": ended_ms,
                    "elapsed_ms": ended_ms - started_ms,
                },
                rid,
            )
        except Exception as exc:  # noqa: BLE001
            ended_ms = int(time.time() * 1000)
            debug_mode = _coerce_bool(
                _STATE.cfg.get("system.debug", False) if _STATE.cfg else False,
                default=False,
            )
            _json_response(
                self,
                500,
                {
                    "task_id": task_id,
                    "status": "FAILED",
                    "result": None,
                    "error_trace": {
                        # 細節僅在 system.debug 開啟時回傳，避免洩漏內部資訊（review PR#77）
                        "error": str(exc) if debug_mode else "MRL runtime error",
                        "error_type": type(exc).__name__,
                    },
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                    "started_at_ms": started_ms,
                    "ended_at_ms": ended_ms,
                    "elapsed_ms": ended_ms - started_ms,
                },
                rid,
            )

    def _post_eval(self, body: Dict[str, Any], rid: str) -> None:
        output = body.get("output", "")
        if not output:
            _json_response(self, 400, {"error": "'output' is required"}, rid)
            return
        keywords = body.get("keywords", [])
        if _STATE.assembly:
            result = _STATE.assembly.evaluate(output, keywords=keywords)
            _json_response(self, 200, result, rid)
        else:
            _json_response(self, 503, {"error": "MotherAssembly unavailable"}, rid)

    def _post_seal(self, body: Dict[str, Any], rid: str) -> None:
        text = body.get("text", "")
        label = body.get("label", "api")
        if not text:
            _json_response(self, 400, {"error": "'text' is required"}, rid)
            return
        if _STATE.assembly:
            trace = _STATE.assembly.seal_text(text, label=label)
            _json_response(self, 200, trace, rid)
        else:
            _json_response(self, 503, {"error": "MotherAssembly unavailable"}, rid)

    def _post_learn_ingest_path(self, body: Dict[str, Any], rid: str) -> None:
        ok, err = _require_learning_enabled()
        if not ok:
            _json_response(self, 403, {"error": err}, rid)
            return
        Learner = _try_import("MRL_learning_ingest", "ingest_path")
        if Learner is None:
            _json_response(self, 503, {"error": "Learning ingest unavailable"}, rid)
            return
        path = str(body.get("path") or "").strip()
        if not path:
            _json_response(self, 400, {"error": "path is required"}, rid)
            return
        label = str(body.get("label") or "")
        chunk_chars = int(body.get("chunk_chars") or 1400)
        overlap = int(body.get("overlap") or 200)
        store_raw = bool(body.get("store_raw", True))
        res = Learner(path, label=label, chunk_chars=chunk_chars, overlap=overlap, store_raw=store_raw)
        status = 200 if res.get("ok") else 400
        _json_response(self, status, res, rid)

    def _post_learn_ingest_url(self, body: Dict[str, Any], rid: str) -> None:
        ok, err = _require_learning_enabled()
        if not ok:
            _json_response(self, 403, {"error": err}, rid)
            return
        Learner = _try_import("MRL_learning_ingest", "ingest_url")
        if Learner is None:
            _json_response(self, 503, {"error": "Learning ingest unavailable"}, rid)
            return
        url = str(body.get("url") or "").strip()
        if not url:
            _json_response(self, 400, {"error": "url is required"}, rid)
            return
        label = str(body.get("label") or "")
        chunk_chars = int(body.get("chunk_chars") or 1400)
        overlap = int(body.get("overlap") or 200)
        store_raw = bool(body.get("store_raw", True))
        timeout_s = int(body.get("timeout_s") or 15)
        res = Learner(url, label=label, chunk_chars=chunk_chars, overlap=overlap, store_raw=store_raw, timeout_s=timeout_s)
        status = 200 if res.get("ok") else 400
        _json_response(self, status, res, rid)

    def _post_learn_query(self, body: Dict[str, Any], rid: str) -> None:
        ok, err = _require_learning_enabled()
        if not ok:
            _json_response(self, 403, {"error": err}, rid)
            return
        Learner = _try_import("MRL_learning_ingest", "query")
        if Learner is None:
            _json_response(self, 503, {"error": "Learning query unavailable"}, rid)
            return
        q = str(body.get("q") or "").strip()
        if not q:
            _json_response(self, 400, {"error": "q is required"}, rid)
            return
        k = int(body.get("k") or 5)
        res = Learner(q, k=k)
        status = 200 if res.get("ok") else 400
        _json_response(self, status, res, rid)

    def _post_tool_call(self, tool_name: str, body: Dict[str, Any], rid: str) -> None:
        if _STATE.assembly and _STATE.assembly.tool_registry:
            result = _STATE.assembly.tool_registry.call(tool_name, body)
            _json_response(self, 200, result, rid)
        else:
            _json_response(self, 503, {"error": "ToolRegistry unavailable"}, rid)

    def _post_templates(self, body: Dict[str, Any], rid: str) -> None:
        tid = body.get("id", "")
        text = body.get("text", "")
        desc = body.get("description", "")
        if not tid or not text:
            _json_response(self, 400, {"error": "'id' and 'text' are required"}, rid)
            return
        if _STATE.assembly and _STATE.assembly.template_registry:
            t = _STATE.assembly.template_registry.add(tid, text, desc)
            _json_response(self, 201, t.to_dict(), rid)
        else:
            _json_response(self, 503, {"error": "TemplateRegistry unavailable"}, rid)

    def _post_template_render(self, tid: str, body: Dict[str, Any], rid: str) -> None:
        variables = body.get("variables", {})
        if _STATE.assembly and _STATE.assembly.template_registry:
            try:
                rec = _STATE.assembly.template_registry.render_record(tid, variables)
                _json_response(self, 200, rec, rid)
            except KeyError as exc:
                _json_response(self, 404, {"error": str(exc)}, rid)
        else:
            _json_response(self, 503, {"error": "TemplateRegistry unavailable"}, rid)

    def _post_config(self, body: Dict[str, Any], rid: str) -> None:
        key = body.get("key", "")
        value = body.get("value")
        if not key:
            _json_response(self, 400, {"error": "'key' is required"}, rid)
            return
        if _STATE.cfg:
            _STATE.cfg.set(key, value)
            _STATE.cfg.save()
            _json_response(self, 200, {"key": key, "value": value}, rid)
        else:
            _json_response(self, 503, {"error": "ConfigManager unavailable"}, rid)

    def _post_guard(self, body: Dict[str, Any], rid: str) -> None:
        """
        Run guardrail checks on arbitrary text.

        Request body:
          text    : str   (required) — text to check
          stage   : str   (optional) — "input" | "output" (default "input")
          policy  : str   (optional) — "standard" | "strict" | "permissive"
        """
        text = body.get("text", "")
        if not text:
            _json_response(self, 400, {"error": "'text' is required"}, rid)
            return
        stage = body.get("stage", "input")
        policy = body.get("policy", "standard")

        InputGuardrail = _try_import("guardrail", "InputGuardrail")
        OutputGuardrail = _try_import("guardrail", "OutputGuardrail")

        if stage == "output" and OutputGuardrail:
            g = OutputGuardrail(policy)
            ok, violations = g.check(text)
        elif InputGuardrail:
            g = InputGuardrail(policy)
            ok, violations = g.check(text)
        else:
            _json_response(self, 503, {"error": "Guardrail unavailable"}, rid)
            return

        _json_response(self, 200, {
            "ok": ok,
            "stage": stage,
            "policy": policy,
            "violations": violations,
        }, rid)

    def _post_export(self, session_id: str, rid: str) -> None:
        """
        Export a conversation session as Markdown.

        URL: POST /export/{session_id}
        Response: plain Markdown text in the JSON field "markdown".
        """
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        if ConvMgr is None:
            _json_response(self, 503, {"error": "ConversationManager unavailable"}, rid)
            return
        mgr = ConvMgr()
        md = mgr.export_markdown(session_id)
        if not md:
            _json_response(self, 404, {"error": f"Session not found: {session_id}"}, rid)
            return
        _json_response(self, 200, {"session_id": session_id, "markdown": md}, rid)

    def _post_chat_stream(self, body: Dict[str, Any], rid: str) -> None:
        """
        Streaming chat completion via Server-Sent Events (SSE).

        Request body:
          message    : str  (required)
          model      : str  (optional)
          system     : str  (optional)
          max_tokens : int  (optional, default 1024)

        Note: this endpoint does not support session continuity.  Use
        POST /chat for persisted, session-aware conversations.

        Response: text/event-stream
          data: {"chunk": "<token_text>"}\n\n
          ...
          data: [DONE]\n\n
        """
        message = body.get("message", "")
        if not message:
            _json_response(self, 400, {"error": "'message' is required"}, rid)
            return

        # deny-by-default (rootlaw rl_00): no implicit "mock".
        model = body.get("model") or (
            _STATE.cfg.get("llm.default_model", "") if _STATE.cfg else ""
        )
        allow_mock = bool(_STATE.cfg.get("llm.allow_mock", False)) if _STATE.cfg else False
        if not model:
            _json_response(
                self, 400,
                {"error": "'model' is required unless llm.default_model is configured",
                 "engine": "mrl_runtime", "trace_id": rid},
                rid,
            )
            return
        if model.startswith("mock") and not allow_mock:
            _json_response(
                self, 403,
                {"error": "MockAdapter is test-only. Set llm.allow_mock=true to enable.",
                 "engine": "mrl_runtime", "trace_id": rid},
                rid,
            )
            return
        system = body.get("system", "")
        if not system and _STATE.cfg:
            system = _STATE.cfg.get(
                "conversation.default_system_prompt",
                "You are MRL_AGI, a helpful AI assistant.",
            )

        messages: List[Dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        LLMGateway = _try_import("llm_gateway", "LLMGateway")
        max_tokens = int(body.get("max_tokens", 1024))

        # Send SSE response headers
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("X-Request-Id", rid)
        _add_cors_headers(self)
        self.end_headers()

        def _send_chunk(data: str) -> None:
            line = f"data: {data}\n\n"
            self.wfile.write(line.encode("utf-8"))
            self.wfile.flush()

        try:
            if LLMGateway:
                gw = LLMGateway(model=model if model != "mock" else None)
                for chunk in gw.stream_chat(messages, max_tokens=max_tokens):
                    payload = json.dumps({"chunk": chunk}, ensure_ascii=False)
                    _send_chunk(payload)
            else:
                # No gateway available → honest error, never a fabricated echo
                # (rootlaw: no_proof_implies_rhetoric).
                payload = json.dumps(
                    {"error": "LLM gateway unavailable; cannot stream without a real engine",
                     "engine": "mrl_runtime"},
                    ensure_ascii=False,
                )
                _send_chunk(payload)
            _send_chunk("[DONE]")
        except BrokenPipeError:
            pass  # client disconnected — normal for SSE


# ─── Server entry point ───────────────────────────────────────────────────────

def serve(host: str = "127.0.0.1", port: int = 7771) -> None:
    """Boot the MotherAssembly and start the HTTP server."""
    print(f"[MRL_AGI API] Booting MotherAssembly…")
    boot_report = _STATE.boot()
    ok_count = sum(1 for v in boot_report.get("subsystems", {}).values() if v == "ok")
    total = len(boot_report.get("subsystems", {}))
    print(f"[MRL_AGI API] Subsystems online: {ok_count}/{total}")
    print(f"[MRL_AGI API] Listening on http://{host}:{port}")
    print(f"[MRL_AGI API] origin_signature: {ORIGIN_SIGNATURE}")
    print(f"[MRL_AGI API] Press Ctrl+C to stop.\n")

    server = ThreadingHTTPServer((host, port), _Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[MRL_AGI API] Shutting down.")
        server.shutdown()


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="api_gateway — MRL_AGI REST API gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Endpoints:
  GET  /health
  POST /chat              {"message": "...", "session_id": "...", "model": "..."}
  GET  /sessions
  POST /sessions          {"system_prompt": "...", "label": "..."}
  GET  /sessions/{id}
  DELETE /sessions/{id}
  POST /agent/run         {"goal": "..."}
  POST /eval              {"output": "...", "keywords": [...]}
  POST /seal              {"text": "...", "label": "..."}
  POST /learn/ingest_path  {"path": "...", "label": "..."}
  POST /learn/ingest_url   {"url": "...", "label": "..."}
  POST /learn/query        {"q": "...", "k": 5}
  GET  /tools
  POST /tools/{name}      {<kwargs>}
  GET  /templates
  POST /templates         {"id": "...", "text": "...", "description": "..."}
  POST /templates/{id}/render  {"variables": {...}}
  GET  /config
  POST /config            {"key": "...", "value": ...}
""",
    )
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7771)
    return p


def main() -> None:
    args = _build_argparser().parse_args()
    serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
