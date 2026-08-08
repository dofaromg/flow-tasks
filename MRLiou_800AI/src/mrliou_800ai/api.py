from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from .physics.conservation import mass_terms
from .security import authentication_enabled, is_authorized


class APIServer:
    def __init__(self, host, port, registry, orchestrator, store, trace):
        self.host, self.port = host, port
        self.registry, self.orchestrator, self.store, self.trace = registry, orchestrator, store, trace

    def serve(self):
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                return

            def send_json(self, code, obj, extra_headers=None):
                body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                if extra_headers:
                    for key, value in extra_headers.items():
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(body)

            def body(self):
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    return json.loads(self.rfile.read(length) or b"{}")
                except Exception as exc:
                    raise ValueError(f"invalid JSON: {exc}") from exc

            def require_auth(self):
                if is_authorized(self.headers):
                    return True
                self.send_json(
                    401,
                    {"ok": False, "error": "authentication_required"},
                    {"WWW-Authenticate": "Bearer"},
                )
                return False

            def do_GET(self):
                if self.path == "/health":
                    rec = parent.trace.emit("health", {})
                    return self.send_json(
                        200,
                        {
                            "ok": True,
                            "origin_signature": "MrLiouWord",
                            "trace_anchor": rec["merkle_root"],
                            "authentication_enabled": authentication_enabled(),
                        },
                    )

                if not self.require_auth():
                    return
                if self.path == "/agents":
                    return self.send_json(200, {"agents": parent.registry.list_agents()})
                if self.path == "/organization":
                    return self.send_json(200, parent.registry.organization)
                return self.send_json(404, {"ok": False, "error": "not_found"})

            def do_POST(self):
                if not self.require_auth():
                    return
                try:
                    body = self.body()
                    if self.path == "/tasks/dispatch":
                        if not isinstance(body.get("task"), str):
                            raise ValueError("task string required")
                        return self.send_json(200, parent.orchestrator.dispatch(body["task"], body.get("evidence")))
                    if self.path == "/vault/write":
                        return self.send_json(200, parent.store.write_text(body["path"], body["text"]))
                    if self.path == "/physics/mass-audit":
                        result = mass_terms(
                            np.array(body["rho"]),
                            np.array(body["u"]),
                            np.array(body["v"]),
                            np.array(body["t"]),
                            body["dx"],
                            body["dy"],
                            np.array(body["w"]) if "w" in body else None,
                            body.get("dz"),
                        )
                        return self.send_json(
                            200,
                            {
                                "equation": "d(rho)/dt + div(rho*V) = 0",
                                "abs_mean": result["abs_mean"],
                                "abs_max": result["abs_max"],
                                "residual_mean_series": result["residual_mean_series"].tolist(),
                            },
                        )
                    return self.send_json(404, {"ok": False, "error": "not_found"})
                except (KeyError, ValueError, TypeError) as exc:
                    return self.send_json(400, {"ok": False, "error": str(exc)})

        ThreadingHTTPServer((self.host, self.port), Handler).serve_forever()
