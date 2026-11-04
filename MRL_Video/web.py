"""Private, authenticated stdlib HTTP API and script-free mobile studio."""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import mimetypes
import re
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .model import VideoError, canonical
from .service import Service

CSS = """body{background:#101929;color:#f3f6ff;font:16px system-ui;margin:0 auto;padding:24px;max-width:980px}
a{color:#63dac5}article,form{padding:20px;background:#1c2a40;border-radius:16px;margin:16px 0}
input,textarea,select,button{font:inherit;box-sizing:border-box;max-width:100%;padding:12px;margin:6px 0}
input,textarea{width:100%;background:#0d1727;color:#f3f6ff;border:1px solid #58718e;border-radius:8px}
button{background:#63dac5;color:#101929;border:0;border-radius:8px;cursor:pointer}
textarea{min-height:220px}video,img{width:100%;border-radius:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere}
small{color:#b3c3db}label{display:block;margin-top:12px}"""


def escaped(value) -> str:
    return html.escape(str(value), quote=True)


class Server(ThreadingHTTPServer):
    """Bound simultaneous requests; use behind an existing private TLS gateway."""

    daemon_threads = True
    request_queue_size = 16

    def __init__(self, address, service: Service, key: str, allowed_hosts: list[str] | None = None):
        if len(key) < 24:
            raise VideoError("MRL_VIDEO_API_KEY must have at least 24 characters")
        self.service = service
        self.key = key.encode()
        self.slots = threading.BoundedSemaphore(12)
        super().__init__(address, Handler)
        port = self.server_address[1]
        self.hosts = set(allowed_hosts or []) | {f"127.0.0.1:{port}", f"localhost:{port}"}

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def sign(self, message: str) -> str:
        return hmac.new(self.key, message.encode(), hashlib.sha256).hexdigest()

    def cookie(self) -> str:
        value = str(int(time.time()))
        return value + "." + self.sign("session:" + value)

    def valid_cookie(self, token: str) -> bool:
        try:
            stamp, signature = token.split(".")
            age = time.time() - int(stamp)
            return 0 <= age < 3600 and hmac.compare_digest(signature, self.sign("session:" + stamp))
        except (ValueError, TypeError):
            return False


class Handler(BaseHTTPRequestHandler):
    """All data and media routes require an API key or short-lived owner cookie."""

    server_version = "MRL_Video/1.0"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format, *args):
        # Never log request paths, source text, cookies, credentials or request bodies.
        pass

    def send(self, status: int, data: bytes, content_type: str, headers: dict | None = None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; media-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def json(self, status: int, value: object):
        self.send(status, canonical(value), "application/json; charset=utf-8")

    def page(self, title: str, body: str, refresh: bool = False):
        tag = '<meta http-equiv="refresh" content="4">' if refresh else ""
        page = ('<!doctype html><html lang="zh-Hant"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{escaped(title)}</title>{tag}<style>{CSS}</style>'
                f'<h1>{escaped(title)}</h1>{body}</html>')
        self.send(200, page.encode(), "text/html; charset=utf-8")

    def context(self):
        if self.headers.get("Host") not in self.server.hosts:
            raise VideoError("Unapproved HTTP Host")
        cookies = SimpleCookie()
        cookies.load(self.headers.get("Cookie", ""))
        token = cookies["MRL_video_session"].value if "MRL_video_session" in cookies else ""
        session = self.server.valid_cookie(token)
        key = self.headers.get("x-api-key", "").encode()
        api = bool(key) and hmac.compare_digest(key, self.server.key)
        return session, api, token

    def body(self) -> bytes:
        raw = self.headers.get("Content-Length", "0")
        if not raw.isdigit() or not 0 < int(raw) <= 1024 * 1024:
            raise VideoError("Body must be 1..1048576 bytes")
        if self.headers.get("Transfer-Encoding"):
            raise VideoError("Chunked requests unsupported")
        data = self.rfile.read(int(raw))
        if len(data) != int(raw):
            raise VideoError("Incomplete body")
        return data

    def do_GET(self):
        try:
            session, api, token = self.context()
            path = urlsplit(self.path).path
            if path == "/health":
                return self.json(200, {"service": "MRL_Video", "status": "ready" if self.server.service.thread and self.server.service.thread.is_alive() else "worker_stopped",
                                       "worker_alive": bool(self.server.service.thread and self.server.service.thread.is_alive())})
            if path == "/" and not (session or api):
                return self.page("MRL 影片工作室", '<p>本地製作・來源追溯・版本保存</p>'
                                 '<form method="post" action="/login"><label>Owner API Key</label>'
                                 '<input name="key" type="password" required autocomplete="off">'
                                 '<button>進入工作室</button></form>')
            if not (session or api):
                return self.json(401, {"error": "Authentication required"})
            store = self.server.service.store
            if path == "/api/jobs":
                return self.json(200, store.list())
            if path == "/api/templates":
                return self.json(200, {"templates": ["explainer", "tutorial", "release", "promo"],
                                       "profiles": ["landscape", "portrait", "square"],
                                       "request_schema": "MRL_Video_Request/v1",
                                       "longfilm_schema": "MRL_LongFilm_Request/v1"})
            if path == "/api/chain":
                return self.json(200, {"event_chain_valid": store.verify_chain()})
            match = re.fullmatch(r"/api/jobs/(MRL_[0-9a-f]{32})(?:/(events|request|segments))?", path)
            if match:
                jid, suffix = match.groups()
                return self.json(200, store.history(jid) if suffix == "events" else
                                 store.request(jid) if suffix == "request" else
                                 store.segments(jid) if suffix == "segments" else store.get(jid))
            match = re.fullmatch(r"/api/diff/(MRL_[0-9a-f]{32})/(MRL_[0-9a-f]{32})", path)
            if match:
                return self.json(200, store.diff(*match.groups()))
            match = re.fullmatch(r"/artifacts/(MRL_[0-9a-f]{32})/([A-Za-z0-9_.-]+)", path)
            if match:
                return self.file(self.server.service.artifact(*match.groups()))
            csrf = self.server.sign("csrf:" + token)
            hidden = f'<input type="hidden" name="csrf" value="{csrf}">'
            if path == "/":
                sample = {"schema": "MRL_Video_Request/v1", "title": "MRL 系統解說", "template": "explainer",
                          "profile": "portrait", "music": True, "sources": [{"id": "s1",
                          "original_name": "使用者提供內容", "locator": "owner:inline",
                          "text": "請在這裡放入四段可驗證的原始內容，每段各占一行。"}]}
                body = '<p>提交來源與分鏡；自動分鏡需要至少四段來源文字。標題屬編輯文字，字幕必須逐字對應來源。</p>'
                body += (f'<form method="post" action="/submit">{hidden}<label>製作要求 JSON</label>'
                         f'<textarea name="request" required>{escaped(json.dumps(sample, ensure_ascii=False, indent=2))}</textarea>'
                         '<button>建立新版本並製作</button></form>')
                for job in store.list():
                    body += (f'<article><a href="/jobs/{job["id"]}">{job["version_string"]} · {job["id"]}</a>'
                             f'<p>{escaped(job["state"])} / {escaped(job["phase"])}</p></article>')
                return self.page("MRL 影片工作室", body)
            match = re.fullmatch(r"/jobs/(MRL_[0-9a-f]{32})", path)
            if match:
                jid = match[1]
                job = store.get(jid)
                body = f'<a href="/">回工作室</a><pre>{escaped(json.dumps(job, ensure_ascii=False, indent=2))}</pre>'
                if job["state"] == "SUCCEEDED":
                    body += f'<video controls playsinline preload="metadata" src="/artifacts/{jid}/explainer.mp4"></video>'
                    body += f'<img alt="各幕預覽" src="/artifacts/{jid}/explainer-stills.png">'
                    for name in ("package.zip", "subtitles.srt", "MRL_audit.json"):
                        body += f'<p><a href="/artifacts/{jid}/{name}">{name}</a></p>'
                if job["state"] in {"RUNNING", "QUEUED"}:
                    body += f'<form method="post" action="/cancel/{jid}">{hidden}<button>取消任務</button></form>'
                original = json.dumps(store.request(jid), ensure_ascii=False, indent=2)
                body += (f'<form method="post" action="/branch/{jid}">{hidden}<label>修改後建立子版本</label>'
                         f'<textarea name="request">{escaped(original)}</textarea><button>保留原版，製作子版本</button></form>')
                return self.page(job["version_string"], body, job["state"] in {"QUEUED", "RUNNING"})
            return self.json(404, {"error": "Not found"})
        except KeyError:
            return self.json(404, {"error": "Job not found"})
        except (VideoError, ValueError, TypeError):
            return self.json(400, {"error": "Invalid request or artifact integrity failure"})
        except (OSError, RuntimeError):
            return self.json(500, {"error": "Local service failure"})

    def do_POST(self):
        try:
            session, api, token = self.context()
            path = urlsplit(self.path).path
            origin = self.headers.get("Origin")
            if origin and urlsplit(origin).netloc != self.headers.get("Host"):
                return self.json(403, {"error": "Cross-origin write rejected"})
            if path == "/login":
                form = parse_qs(self.body().decode())
                supplied = form.get("key", [""])[0].encode()
                if not hmac.compare_digest(supplied, self.server.key):
                    return self.json(401, {"error": "Invalid key"})
                # TLS is provided by the private gateway; Secure follows actual HTTPS origin.
                secure = "; Secure" if origin and urlsplit(origin).scheme == "https" else ""
                return self.send(303, b"", "text/plain", {"Location": "/", "Set-Cookie":
                                 "MRL_video_session=" + self.server.cookie() + "; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600" + secure})
            if not (session or api):
                return self.json(401, {"error": "Authentication required"})
            raw = self.body()
            is_form = path == "/submit" or path.startswith(("/branch/", "/cancel/"))
            if is_form:
                form = parse_qs(raw.decode())
                if not session or not hmac.compare_digest(form.get("csrf", [""])[0], self.server.sign("csrf:" + token)):
                    return self.json(403, {"error": "CSRF check failed"})
                payload = json.loads(form["request"][0]) if "request" in form else None
            else:
                if not api:  # Cookie sessions cannot mutate the JSON API.
                    return self.json(403, {"error": "API key required"})
                payload = json.loads(raw)
            store = self.server.service.store
            match = re.fullmatch(r"/(?:api/jobs/|)(?:branch/)?(MRL_[0-9a-f]{32})(?:/branch)?", path)
            parent = None
            if path.startswith("/branch/") and match:
                parent = match[1]
            api_branch = re.fullmatch(r"/api/jobs/(MRL_[0-9a-f]{32})/branch", path)
            if api_branch:
                parent = api_branch[1]
            cancel = re.fullmatch(r"/(?:api/jobs/)?(?:cancel/)?(MRL_[0-9a-f]{32})(?:/cancel)?", path)
            if cancel and (path.startswith("/cancel/") or path.endswith("/cancel")):
                result = store.cancel(cancel[1])
            elif path in {"/api/jobs", "/submit"} or parent:
                result = store.submit(payload, self.headers.get("Idempotency-Key"), parent)
            else:
                return self.json(404, {"error": "Not found"})
            if is_form:
                return self.send(303, b"", "text/plain", {"Location": "/jobs/" + result["id"]})
            return self.json(202, result)
        except KeyError:
            return self.json(404, {"error": "Job or field not found"})
        except (VideoError, ValueError, TypeError) as exc:
            error = str(exc) if isinstance(exc, VideoError) else "Invalid JSON or fields"
            return self.json(400, {"error": error})
        except OSError:
            return self.json(500, {"error": "Local storage failure"})

    def file(self, path):
        size = path.stat().st_size
        start, end, status = 0, size - 1, 200
        range_header = self.headers.get("Range")
        if range_header:
            match = re.fullmatch(r"bytes=(\d+)-(\d*)", range_header)
            if not match:
                return self.send(416, b"", "text/plain", {"Content-Range": f"bytes */{size}"})
            start = int(match[1])
            end = min(int(match[2]) if match[2] else end, end)
            if not 0 <= start <= end < size:
                return self.send(416, b"", "text/plain", {"Content-Range": f"bytes */{size}"})
            status = 206
        self.send_response(status)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        with path.open("rb") as stream:
            stream.seek(start)
            remaining = end - start + 1
            while remaining:
                data = stream.read(min(remaining, 65536))
                if not data:
                    break
                self.wfile.write(data)
                remaining -= len(data)
        return None

