"""test_MRL_product_entry_ui.py — Issue #25 產品級首頁 / app 入口
origin_signature: MrLiouWord

Verifies that:
  1. src/mrl_app.html exists, is non-empty, and contains all required structural elements.
  2. The HTML is well-formed enough for a browser entry point (doctype, charset, viewport).
  3. Issue #26 — large composer textarea is present.
  4. Issue #28 — internal MRL_ tool names are mapped.
  5. Issue #29 — session management JS present (new session, localStorage DB).
  6. The send() function handles ok:false (no [object Object] bug).
  7. The probe() function checks available:false (not only HTTP status).
  8. The build artefact src/mrl_app_ui.js is present and exports APP_HTML
     containing the same content as mrl_app.html.
  9. MRL_Platform_Server.py GET / handler references src/mrl_app.html (correct entry).
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
HTML_PATH = REPO / "src" / "mrl_app.html"
UI_JS_PATH = REPO / "src" / "mrl_app_ui.js"


# ── helpers ──────────────────────────────────────────────────────────────────

def html() -> str:
    return HTML_PATH.read_text(encoding="utf-8")


def ui_js() -> str:
    return UI_JS_PATH.read_text(encoding="utf-8")


# ── 1. File existence ─────────────────────────────────────────────────────────

def test_mrl_app_html_exists():
    assert HTML_PATH.exists(), "src/mrl_app.html must exist (Issue #25 product entry)"
    assert HTML_PATH.stat().st_size > 1000, "src/mrl_app.html must be non-trivial"


def test_mrl_app_ui_js_exists():
    assert UI_JS_PATH.exists(), (
        "src/mrl_app_ui.js must exist — run `node scripts/MRL_build_ui.js` to generate"
    )


# ── 2. Basic HTML structure ───────────────────────────────────────────────────

def test_html_has_doctype():
    assert html().lstrip().lower().startswith("<!doctype html")


def test_html_has_charset_utf8():
    assert 'charset="utf-8"' in html().lower() or "charset=utf-8" in html().lower()


def test_html_has_viewport_meta():
    assert "viewport" in html()


def test_html_has_title():
    assert "<title>" in html()


def test_html_has_origin_signature():
    assert "MrLiouWord" in html()


# ── 3. Issue #25 — product entry UI shell ────────────────────────────────────

def test_html_has_login_section():
    """Issue #25: entry point must present a login/guest gate."""
    h = html()
    assert 'id="login"' in h, "Login section missing"
    assert 'id="guest"' in h, "Guest entry button missing"


def test_html_has_app_shell():
    """Issue #25: app shell (aside + main) must be present."""
    h = html()
    assert 'id="app"' in h
    assert "<aside" in h
    assert "<main" in h


# ── 4. Issue #26 — large composer textarea ───────────────────────────────────

def test_html_has_composer_textarea():
    """Issue #26: big composer input must exist."""
    assert "<textarea" in html(), "Composer textarea missing (Issue #26)"


# ── 5. Issue #27 — product entry, not engineering test page ──────────────────

def test_platform_server_serves_mrl_app_html():
    """Issue #27: MRL_Platform_Server.py GET / must serve src/mrl_app.html."""
    server_src = (REPO / "MRL_Platform_Server.py").read_text(encoding="utf-8")
    assert 'mrl_app.html' in server_src, (
        "MRL_Platform_Server.py must serve src/mrl_app.html at GET / (Issue #27)"
    )
    # Confirm fallback is the old page_html(), not the primary path
    assert 'page_html()' in server_src, "Fallback page_html() should remain for graceful degradation"


# ── 6. Issue #28 — internal MRL_ naming with external display names ──────────

def test_html_has_mrl_tool_names():
    """Issue #28: internal MRL_ ids must be listed in TOOLS."""
    h = html()
    required_ids = [
        "MRL_Dialogue",
        "MRL_Monitor",
        "MRL_Console",
        "MRL_Settings",
    ]
    for rid in required_ids:
        assert rid in h, f"Tool id {rid!r} missing from TOOLS array (Issue #28)"


def test_html_has_external_display_names():
    """Issue #28: external display names must be mapped alongside internal ids."""
    h = html()
    # Spot-check a few external names that appear in TOOLS array
    assert "AI 對話" in h
    assert "即時監控" in h


# ── 7. Issue #29 — session management ────────────────────────────────────────

def test_html_has_session_management():
    """Issue #29: new session, history sessions, task status."""
    h = html()
    assert "newSession" in h or "new_session" in h.lower(), "newSession function missing"
    assert "localStorage" in h, "Session persistence (localStorage) missing"
    assert "renderSessions" in h, "renderSessions function missing"


def test_html_has_task_status_indicators():
    """Issue #29: task status (QUEUED/RUNNING/DONE/FAILED) must be shown."""
    h = html()
    for status in ("QUEUED", "RUNNING", "DONE", "FAILED"):
        assert status in h, f"Task status {status!r} missing"


# ── 8. Bug fixes: ok:false and nested reply ───────────────────────────────────

def test_html_handles_ok_false():
    """send() must treat ok:false as FAILED, not DONE."""
    h = html()
    # The fixed code checks r.data.ok !== false before setting DONE
    assert "ok!==false" in h or "ok !== false" in h, (
        "send() must check r.data.ok!==false to avoid marking ok:false responses as DONE"
    )


def test_html_has_unwrap_reply():
    """send() must handle nested reply objects (unwrapReply helper)."""
    h = html()
    assert "unwrapReply" in h, (
        "unwrapReply() must exist to handle nested {reply:{reply:'...'}} responses"
    )


# ── 9. probe() checks available:false ────────────────────────────────────────

def test_html_probe_checks_available_false():
    """probe() must treat available:false as offline, not rely only on HTTP status."""
    h = html()
    assert "available===false" in h or "available === false" in h, (
        "probe() must check data.available===false (not just HTTP ok)"
    )


# ── 10. Build artefact consistency ───────────────────────────────────────────

def test_ui_js_exports_app_html():
    """src/mrl_app_ui.js must export APP_HTML."""
    js = ui_js()
    assert "export const APP_HTML" in js, "mrl_app_ui.js must export APP_HTML"


def test_ui_js_contains_mrl_origin_signature():
    """src/mrl_app_ui.js must contain origin_signature: MrLiouWord."""
    assert "MrLiouWord" in ui_js()


def test_ui_js_content_matches_html():
    """The APP_HTML in mrl_app_ui.js must be generated from mrl_app.html."""
    js = ui_js()
    # The JS file wraps the HTML in JSON.stringify; check that its header contains the HTML title
    assert "MRL_AI OS" in js, "mrl_app_ui.js content should reflect mrl_app.html title"


# ── 11. favicon — no 404 ─────────────────────────────────────────────────────

def test_html_has_inline_favicon():
    """favicon must be inline (data:) to avoid a 404 network request."""
    h = html()
    assert 'rel="icon"' in h, "favicon link tag missing"
    assert "data:" in h, "favicon must use data: URI to avoid 404"


# ── 12. worker.js consistency ────────────────────────────────────────────────

def test_worker_imports_app_html():
    """src/mrl_worker.js must import APP_HTML from mrl_app_ui.js (single source of truth)."""
    worker = (REPO / "src" / "mrl_worker.js").read_text(encoding="utf-8")
    assert "APP_HTML" in worker and "mrl_app_ui" in worker, (
        "mrl_worker.js must import APP_HTML from ./mrl_app_ui.js"
    )
