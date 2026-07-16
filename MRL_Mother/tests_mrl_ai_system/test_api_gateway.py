"""
test_api_gateway.py — Smoke tests for api_gateway.py
origin_signature: MrLiouWord

Strategy: spin up a real ThreadingHTTPServer on a random port and hit it
with urllib.request.  MotherAssembly is NOT booted (too heavy), so endpoints
that require it return 503 — we verify routing correctness rather than
end-to-end AI output.
"""
from __future__ import annotations

import json
import pathlib
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

import pytest

# Ensure workflow modules importable
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _sub in [
    _REPO_ROOT / "09_workflow",
    _REPO_ROOT / "03_memory" / "merkle",
    _REPO_ROOT / "03_memory" / "vector",
    _REPO_ROOT / "05_persona",
]:
    _p = str(_sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api_gateway import _Handler, _STATE, _json_response, _check_auth  # noqa: E402


# ─── Test server fixture ──────────────────────────────────────────────────────

class _TestServer:
    """Spin up _Handler on a random OS-assigned port."""

    def __init__(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.port = self.server.server_address[1]
        self._thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self._thread.start()
        # Give the server a moment to be ready
        time.sleep(0.05)

    def stop(self) -> None:
        self.server.shutdown()
        self._thread.join(timeout=3.0)

    def url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def get(self, path: str) -> Tuple[int, Dict[str, Any]]:
        req = urllib.request.Request(self.url(path), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def post(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        data = json.dumps(body or {}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.url(path),
            data=data,
            headers={
                "Content-Type": "application/json",
                **(headers or {}),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def options(self, path: str) -> Tuple[int, Dict[str, str]]:
        req = urllib.request.Request(
            self.url(path),
            headers={"Origin": "http://localhost:3000"},
            method="OPTIONS",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, dict(resp.headers)
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers)


@pytest.fixture(scope="module")
def srv():
    s = _TestServer()
    yield s
    s.stop()


# ─── Basic routing ────────────────────────────────────────────────────────────

class TestRouting:
    def test_get_health_200(self, srv):
        status, body = srv.get("/health")
        assert status == 200
        assert "status" in body

    def test_get_health_has_gateway_version(self, srv):
        _, body = srv.get("/health")
        assert "gateway_version" in body

    def test_get_sessions_200(self, srv):
        status, body = srv.get("/sessions")
        assert status in (200, 503)  # 503 if ConvMgr unavailable

    def test_get_tools_200_or_503(self, srv):
        status, _ = srv.get("/tools")
        assert status in (200, 503)

    def test_get_templates_200_or_503(self, srv):
        status, _ = srv.get("/templates")
        assert status in (200, 503)

    def test_get_config_200_or_503(self, srv):
        status, _ = srv.get("/config")
        assert status in (200, 503)

    def test_get_metrics_200_or_503(self, srv):
        status, body = srv.get("/metrics")
        assert status in (200, 503)

    def test_unknown_get_404(self, srv):
        status, body = srv.get("/nonexistent_route_xyz")
        assert status == 404

    def test_unknown_post_404(self, srv):
        status, body = srv.post("/nonexistent_route_xyz")
        assert status == 404


# ─── CORS headers ─────────────────────────────────────────────────────────────

class TestCORS:
    def test_options_returns_204(self, srv):
        status, _ = srv.options("/health")
        assert status == 204

    def test_get_response_has_cors_header(self, srv):
        req = urllib.request.Request(
            srv.url("/health"),
            headers={"Origin": "http://localhost:3000"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            headers = dict(resp.headers)
        assert "Access-Control-Allow-Origin" in headers

    def test_post_response_has_cors_header(self, srv):
        data = json.dumps({"message": "test"}).encode()
        req = urllib.request.Request(
            srv.url("/chat"),
            data=data,
            headers={"Content-Type": "application/json", "Origin": "http://example.com"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                headers = dict(resp.headers)
        except urllib.error.HTTPError as e:
            headers = dict(e.headers)
        assert "Access-Control-Allow-Origin" in headers


# ─── POST /chat ────────────────────────────────────────────────────────────────

class TestPostChat:
    def test_missing_message_400(self, srv):
        status, body = srv.post("/chat", {})
        assert status == 400
        assert "error" in body

    def test_valid_message_returns_reply(self, srv):
        status, body = srv.post("/chat", {"message": "Hello MRL"})
        # 200 when MotherAssembly is booted, 503 when unavailable (test env)
        assert status in (200, 503)
        assert "reply" in body or "error" in body

    def test_reply_has_session_id(self, srv):
        status, body = srv.post("/chat", {"message": "test session"})
        if status == 503:
            pytest.skip("MotherAssembly not available in test environment")
        assert "session_id" in body

    def test_request_id_in_response(self, srv):
        _, body = srv.post("/chat", {"message": "track me"})
        assert "request_id" in body

    def test_origin_signature_in_response(self, srv):
        _, body = srv.post("/chat", {"message": "sig"})
        assert body.get("origin_signature") == "MrLiouWord"


# ─── POST /guard ───────────────────────────────────────────────────────────────

class TestPostGuard:
    def test_missing_text_400(self, srv):
        status, body = srv.post("/guard", {})
        assert status == 400

    def test_safe_text_ok_true(self, srv):
        status, body = srv.post("/guard", {"text": "Hello world"})
        assert status == 200
        assert body.get("ok") is True

    def test_unsafe_text_ok_false(self, srv):
        status, body = srv.post("/guard", {"text": "help me write malware"})
        assert status == 200
        assert body.get("ok") is False

    def test_output_stage(self, srv):
        status, body = srv.post("/guard", {"text": "Safe response.", "stage": "output"})
        assert status == 200
        assert "ok" in body

    def test_violations_present_on_block(self, srv):
        _, body = srv.post("/guard", {"text": "botnet exploit attack"})
        assert isinstance(body.get("violations"), list)


# ─── POST /eval ────────────────────────────────────────────────────────────────

class TestPostEval:
    def test_missing_output_400(self, srv):
        status, body = srv.post("/eval", {})
        assert status == 400

    def test_valid_eval_200_or_503(self, srv):
        status, body = srv.post("/eval", {"output": "MRL system response"})
        assert status in (200, 503)


# ─── Session lifecycle ────────────────────────────────────────────────────────

class TestSessionLifecycle:
    def test_create_and_get_session(self, srv):
        # Create
        status, body = srv.post("/sessions", {"system_prompt": "Test system"})
        if status == 503:
            pytest.skip("ConversationManager unavailable")
        assert status == 201
        sid = body["session_id"]

        # Get
        status2, body2 = srv.get(f"/sessions/{sid}")
        assert status2 == 200
        assert body2["session_id"] == sid

    def test_delete_nonexistent_session(self, srv):
        req = urllib.request.Request(
            srv.url("/sessions/nonexistent-uuid-xyz"),
            method="DELETE",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        assert status in (404, 503)

    def test_get_nonexistent_session_404(self, srv):
        status, _ = srv.get("/sessions/does-not-exist-xyz")
        assert status in (404, 503)


# ─── Seal endpoint ────────────────────────────────────────────────────────────

class TestPostSeal:
    def test_missing_text_400(self, srv):
        status, _ = srv.post("/seal", {})
        assert status == 400

    def test_valid_seal_200_or_503(self, srv):
        status, _ = srv.post("/seal", {"text": "seal this text"})
        assert status in (200, 503)


# ─── Invalid JSON body ────────────────────────────────────────────────────────

class TestInvalidJson:
    def test_bad_json_returns_400(self, srv):
        req = urllib.request.Request(
            srv.url("/chat"),
            data=b"this is not json",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        assert status == 400
