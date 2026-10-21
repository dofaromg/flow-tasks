#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mr.liou.IO.Server — MRL 零依賴 HTTP API 服務器
Mr.liou.IO.Server.v1

替代 FastAPI / uvicorn，使用 Python 標準庫：
  - http.server.BaseHTTPRequestHandler
  - socketserver.ThreadingTCPServer
  - json（標準庫）
  - threading（標準庫）

支援：
  - RESTful 路由（GET / POST / PUT / DELETE）
  - JSON 請求體解析
  - 查詢字符串解析
  - 路徑參數（/{id} 風格）
  - 中間件（日誌、CORS、錯誤處理）
  - 異步友好（每個請求在獨立線程中處理）
  - 優雅關機

設計：API 盡量對齊 FastAPI 的使用習慣，便於遷移。
"""

import json
import os
import re
import sys
import time
import threading
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse, unquote
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger("Mr.liou.IO.Server")


# ===========================================================================
# 請求 / 響應 數據類
# ===========================================================================

@dataclass
class Request:
    """HTTP 請求對象"""
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    path_params: Dict[str, str]
    body: Optional[bytes]
    client_host: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def json(self) -> Any:
        """解析 JSON 請求體"""
        if not self.body:
            return None
        return json.loads(self.body.decode("utf-8"))

    def form(self) -> Dict[str, str]:
        """解析表單數據"""
        if not self.body:
            return {}
        return dict(parse_qs(self.body.decode("utf-8")))

    @property
    def content_type(self) -> str:
        return self.headers.get("content-type", "")


@dataclass
class Response:
    """HTTP 響應對象"""
    content: Any = None
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    media_type: str = "application/json"

    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: str = "application/json",
    ):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}
        self.media_type = media_type

    def body_bytes(self) -> bytes:
        if self.content is None:
            return b""
        if isinstance(self.content, bytes):
            return self.content
        if isinstance(self.content, str):
            return self.content.encode("utf-8")
        return json.dumps(self.content, ensure_ascii=False, default=str).encode("utf-8")


class JSONResponse(Response):
    def __init__(self, content: Any, status_code: int = 200, **kwargs):
        super().__init__(content, status_code, media_type="application/json", **kwargs)


class PlainTextResponse(Response):
    def __init__(self, content: str, status_code: int = 200, **kwargs):
        super().__init__(content, status_code, media_type="text/plain; charset=utf-8", **kwargs)


class HTMLResponse(Response):
    def __init__(self, content: str, status_code: int = 200, **kwargs):
        super().__init__(content, status_code, media_type="text/html; charset=utf-8", **kwargs)


# ===========================================================================
# 路由系統
# ===========================================================================

@dataclass
class Route:
    """單條路由規則"""
    method: str
    path: str
    handler: Callable
    _regex: re.Pattern = field(init=False, repr=False)
    _param_names: List[str] = field(init=False, repr=False)

    def __post_init__(self):
        # 將 /{param} 轉換為正則表達式
        pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", self.path)
        pattern = f"^{pattern}$"
        self._regex = re.compile(pattern)
        self._param_names = re.findall(r"\{(\w+)\}", self.path)

    def match(self, method: str, path: str) -> Optional[Dict[str, str]]:
        """匹配路由，返回路徑參數或 None"""
        if self.method != method and self.method != "*":
            return None
        m = self._regex.match(path)
        if m:
            return m.groupdict()
        return None


class Router:
    """
    MRL 路由器

    使用方式：
        router = Router()

        @router.get("/particles")
        def list_particles(req: Request) -> Response:
            return JSONResponse({"particles": []})

        @router.post("/particles/{name}")
        def create_particle(req: Request) -> Response:
            name = req.path_params["name"]
            return JSONResponse({"created": name}, status_code=201)
    """

    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self._routes: List[Route] = []
        self._startup_hooks: List[Callable] = []
        self._shutdown_hooks: List[Callable] = []

    def _add_route(self, method: str, path: str) -> Callable:
        full_path = self.prefix + path

        def decorator(func: Callable) -> Callable:
            self._routes.append(Route(method=method.upper(), path=full_path, handler=func))
            return func
        return decorator

    def get(self, path: str) -> Callable:
        return self._add_route("GET", path)

    def post(self, path: str) -> Callable:
        return self._add_route("POST", path)

    def put(self, path: str) -> Callable:
        return self._add_route("PUT", path)

    def delete(self, path: str) -> Callable:
        return self._add_route("DELETE", path)

    def patch(self, path: str) -> Callable:
        return self._add_route("PATCH", path)

    def route(self, path: str, methods: List[str]) -> Callable:
        def decorator(func: Callable) -> Callable:
            for m in methods:
                self._routes.append(Route(method=m.upper(), path=self.prefix + path, handler=func))
            return func
        return decorator

    def on_startup(self, func: Callable) -> Callable:
        self._startup_hooks.append(func)
        return func

    def on_shutdown(self, func: Callable) -> Callable:
        self._shutdown_hooks.append(func)
        return func

    def dispatch(self, request: Request) -> Response:
        """路由分發"""
        for route in self._routes:
            path_params = route.match(request.method, request.path)
            if path_params is not None:
                request.path_params = path_params
                try:
                    result = route.handler(request)
                    if isinstance(result, Response):
                        return result
                    if isinstance(result, dict):
                        return JSONResponse(result)
                    if isinstance(result, str):
                        return PlainTextResponse(result)
                    return JSONResponse(result)
                except Exception as e:
                    tb = traceback.format_exc()
                    logger.error(f"路由處理錯誤: {e}\n{tb}")
                    return JSONResponse(
                        {"error": str(e), "detail": tb},
                        status_code=500,
                    )

        return JSONResponse(
            {"error": "Not Found", "path": request.path},
            status_code=404,
        )

    def include_router(self, other: "Router"):
        """合併另一個路由器的路由"""
        self._routes.extend(other._routes)
        self._startup_hooks.extend(other._startup_hooks)
        self._shutdown_hooks.extend(other._shutdown_hooks)


# ===========================================================================
# HTTP 請求處理器
# ===========================================================================

class _MRLRequestHandler(BaseHTTPRequestHandler):
    """內部 HTTP 請求處理器"""

    router: Router = None  # 由 MRLServer 注入
    middleware_chain: List[Callable] = []
    access_log: bool = True

    def log_message(self, format: str, *args):
        if self.access_log:
            logger.info(
                f"{self.client_address[0]} - "
                f'"{self.command} {self.path}" {args[1]}'
            )

    def _parse_request(self) -> Request:
        """解析 HTTP 請求為 Request 對象"""
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query_raw = parse_qs(parsed.query or "")
        query = {k: v[0] if len(v) == 1 else v for k, v in query_raw.items()}

        headers = {k.lower(): v for k, v in self.headers.items()}
        content_length = int(headers.get("content-length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        return Request(
            method=self.command,
            path=path,
            headers=headers,
            query_params=query,
            path_params={},
            body=body,
            client_host=self.client_address[0],
        )

    def _send_response(self, resp: Response):
        """發送 Response 對象"""
        self.send_response(resp.status_code)
        body = resp.body_bytes()
        self.send_header("Content-Type", resp.media_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Powered-By", "Mr.liou.IO.Server.v1")
        for k, v in resp.headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _handle(self):
        try:
            request = self._parse_request()
            response = self.router.dispatch(request)
            self._send_response(response)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"請求處理異常: {e}\n{tb}")
            err_resp = JSONResponse({"error": "Internal Server Error"}, status_code=500)
            self._send_response(err_resp)

    def do_GET(self): self._handle()
    def do_POST(self): self._handle()
    def do_PUT(self): self._handle()
    def do_DELETE(self): self._handle()
    def do_PATCH(self): self._handle()
    def do_HEAD(self): self._handle()
    def do_OPTIONS(self): self._handle()


# ===========================================================================
# MRLServer — 主要服務器類別
# ===========================================================================

class MRLServer:
    """
    Mr.liou.IO.Server — MRL HTTP API 服務器

    替代 FastAPI / uvicorn，完全零外部依賴。

    使用方式：
        server = MRLServer(host="0.0.0.0", port=8000)
        router = server.router

        @router.get("/health")
        def health(req: Request):
            return {"status": "ok", "version": "v1"}

        @router.post("/particles/{name}")
        def create(req: Request):
            data = req.json()
            name = req.path_params["name"]
            return {"created": name, "data": data}

        server.run()
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        access_log: bool = True,
        cors: bool = False,
        cors_origins: Optional[List[str]] = None,
    ):
        self.host = host
        self.port = port
        self.access_log = access_log
        self.cors = cors
        self.cors_origins = cors_origins or ["*"]
        self.router = Router()
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

        # 預設路由
        self._add_default_routes()

    def _add_default_routes(self):
        """添加默認路由"""
        @self.router.get("/")
        def root(req: Request):
            return JSONResponse({
                "service": "Mr.liou.IO.Server",
                "version": "v1",
                "status": "running",
                "timestamp": datetime.now().isoformat(),
            })

        @self.router.get("/health")
        def health(req: Request):
            return JSONResponse({"status": "ok"})

    def _build_handler_class(self):
        """動態建立配置好的處理器類"""
        router = self.router
        access_log = self.access_log
        cors = self.cors
        cors_origins = self.cors_origins

        class ConfiguredHandler(_MRLRequestHandler):
            pass

        ConfiguredHandler.router = router
        ConfiguredHandler.access_log = access_log

        if cors:
            # 包裝 _send_response 以添加 CORS 頭
            original_handle = ConfiguredHandler._handle

            def cors_handle(self_h):
                original_handle(self_h)

            # 在 _send_response 前注入 CORS
            orig_send = ConfiguredHandler._send_response

            def cors_send_response(self_h, resp: Response):
                origin = self_h.headers.get("Origin", "*")
                if "*" in cors_origins or origin in cors_origins:
                    resp.headers["Access-Control-Allow-Origin"] = origin
                resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
                resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
                orig_send(self_h, resp)

            ConfiguredHandler._send_response = cors_send_response

        return ConfiguredHandler

    def run(
        self,
        background: bool = False,
    ):
        """
        啟動服務器

        Args:
            background: True 時在後台線程運行，False 時阻塞主線程
        """
        # 執行啟動鉤子
        for hook in self.router._startup_hooks:
            hook()

        handler_class = self._build_handler_class()
        self._server = ThreadingHTTPServer((self.host, self.port), handler_class)
        self._server.daemon_threads = True

        logger.info(f"Mr.liou.IO.Server 啟動: http://{self.host}:{self.port}")
        print(f"\n🚀 Mr.liou.IO.Server 運行中: http://{self.host}:{self.port}")
        print(f"   路由數量: {len(self.router._routes)}")
        print(f"   使用 Ctrl+C 停止\n")

        if background:
            self._thread = threading.Thread(
                target=self._server.serve_forever,
                daemon=True,
            )
            self._thread.start()
        else:
            try:
                self._server.serve_forever()
            except KeyboardInterrupt:
                self.shutdown()

    def shutdown(self):
        """優雅關機"""
        if self._server:
            print("\n⏹ 正在關閉服務器...")
            for hook in self.router._shutdown_hooks:
                try:
                    hook()
                except Exception as e:
                    logger.error(f"關閉鉤子錯誤: {e}")
            self._server.shutdown()
            self._server = None
            print("✅ 服務器已關閉")

    def __enter__(self):
        self.run(background=True)
        return self

    def __exit__(self, *_):
        self.shutdown()


# ===========================================================================
# 中間件輔助裝飾器
# ===========================================================================

def require_json(handler: Callable) -> Callable:
    """要求 Content-Type: application/json 的中間件裝飾器"""
    def wrapper(req: Request) -> Response:
        if "application/json" not in req.content_type:
            return JSONResponse(
                {"error": "Content-Type must be application/json"},
                status_code=415,
            )
        return handler(req)
    return wrapper


def require_auth(token: str) -> Callable:
    """
    ****** 驗證裝飾器

    使用 hmac.compare_digest 進行恆定時間比較，防止 timing attack。

    Args:
        token: 有效的 ****** 字串

    使用方式：
        @require_auth("my-secret-token")
        @router.get("/protected")
        def protected_route(req: Request) -> Response:
            ...
    """
    import hmac
    expected = f"******"

    def decorator(handler: Callable) -> Callable:
        def wrapper(req: Request) -> Response:
            auth = req.headers.get("authorization", "")
            # 恆定時間比較，防止 timing attack
            if not hmac.compare_digest(auth.encode(), expected.encode()):
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            return handler(req)
        return wrapper
    return decorator


def rate_limiter(max_calls: int = 100, window_sec: float = 60.0) -> Callable:
    """簡單速率限制裝飾器"""
    _calls: Dict[str, List[float]] = {}
    _lock = threading.Lock()

    def decorator(handler: Callable) -> Callable:
        def wrapper(req: Request) -> Response:
            ip = req.client_host
            now = time.time()
            with _lock:
                times = _calls.get(ip, [])
                times = [t for t in times if now - t < window_sec]
                if len(times) >= max_calls:
                    return JSONResponse(
                        {"error": "Too Many Requests"},
                        status_code=429,
                    )
                times.append(now)
                _calls[ip] = times
            return handler(req)
        return wrapper
    return decorator


# ===========================================================================
# MRL 粒子 API 藍圖（示例路由集合）
# ===========================================================================

def create_particle_api_router(
    particle_manager_instance: Any = None,
) -> Router:
    """
    建立 MRL 粒子 API 路由器
    提供粒子的 CRUD 操作端點。

    Args:
        particle_manager_instance: MRL_Particle_Manager 實例（可選）

    Returns:
        配置好的 Router
    """
    router = Router(prefix="/api/v1")

    @router.get("/particles")
    def list_particles(req: Request) -> Response:
        """列出所有粒子"""
        if particle_manager_instance:
            particles = particle_manager_instance.list_all_particles()
            return JSONResponse({"particles": particles, "count": len(particles)})
        return JSONResponse({"particles": [], "count": 0})

    @router.get("/particles/{name}")
    def get_particle(req: Request) -> Response:
        """取得單個粒子詳情"""
        name = req.path_params.get("name", "")
        if particle_manager_instance:
            status = particle_manager_instance.get_particle_status(name)
            if status.get("status") == "not_found":
                return JSONResponse({"error": f"粒子未找到: {name}"}, status_code=404)
            return JSONResponse(status)
        return JSONResponse({"name": name, "status": "demo"})

    @router.post("/particles")
    @require_json
    def create_particle(req: Request) -> Response:
        """建立新粒子（接收 JSON body）"""
        data = req.json()
        if not data or "name" not in data:
            return JSONResponse({"error": "缺少 'name' 字段"}, status_code=422)
        return JSONResponse(
            {"created": True, "name": data["name"]},
            status_code=201,
        )

    @router.delete("/particles/{name}")
    def delete_particle(req: Request) -> Response:
        """刪除粒子"""
        name = req.path_params.get("name", "")
        return JSONResponse({"deleted": name})

    @router.get("/particles/{name}/status")
    def particle_status(req: Request) -> Response:
        """查詢粒子訓練狀態"""
        name = req.path_params.get("name", "")
        if particle_manager_instance:
            return JSONResponse(particle_manager_instance.get_particle_status(name))
        return JSONResponse({"name": name, "status": "unknown"})

    @router.get("/fusion/report")
    def fusion_report(req: Request) -> Response:
        """融合引擎報告"""
        return JSONResponse({
            "engine": "Mr.liou.Particle.Fusion.v2",
            "status": "active",
            "timestamp": datetime.now().isoformat(),
        })

    return router


# ===========================================================================
# 自檢 / 演示
# ===========================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    server = MRLServer(host="127.0.0.1", port=8765, access_log=True, cors=True)
    particle_router = create_particle_api_router()
    server.router.include_router(particle_router)

    # 自定義路由示例
    @server.router.get("/demo")
    def demo_route(req: Request) -> Response:
        return JSONResponse({
            "message": "Mr.liou.IO.Server 運行中",
            "query": req.query_params,
            "server": "v1",
        })

    @server.router.post("/echo")
    def echo_route(req: Request) -> Response:
        return JSONResponse({
            "method": req.method,
            "path": req.path,
            "body": req.json() if req.body else None,
        })

    print("Mr.liou.IO.Server 自檢模式")
    print("可用端點：")
    for route in server.router._routes:
        print(f"  {route.method:8s} {route.path}")
    print()

    if "--test" in sys.argv:
        # 非互動測試：後台啟動後立即退出
        with server:
            import urllib.request
            time.sleep(0.5)
            try:
                resp = urllib.request.urlopen("http://127.0.0.1:8765/health")
                print(f"健康檢查: {resp.read().decode()}")
                print("✅ 服務器自檢通過")
            except Exception as e:
                print(f"❌ 自檢失敗: {e}")
    else:
        server.run()
