#!/usr/bin/env python3
"""Standard-library APIWorks gateway for the autonomous MRL mother runtime."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from runtime.MRL_mother_runtime_v1 import MRLMotherRuntime
else:
    from .MRL_mother_runtime_v1 import MRLMotherRuntime


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    size = int(handler.headers.get("Content-Length", "0"))
    if size <= 0 or size > 1_048_576:
        raise ValueError("JSON body must be between 1 byte and 1 MiB")
    value = json.loads(handler.rfile.read(size).decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON body must be an object")
    return value


def build_handler(runtime: MRLMotherRuntime) -> type[BaseHTTPRequestHandler]:
    """Bind one runtime to an isolated HTTP handler class."""

    class MRLAPIWorksHandler(BaseHTTPRequestHandler):
        server_version = "MRLAPIWorksGateway/1.0"

        def _write(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-MRL-Origin", "MrLiouWord")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                health = runtime.health()
                self._write(200 if health["ready"] else 503, health)
                return
            if parsed.path == "/v1/memory/recall":
                query = parse_qs(parsed.query)
                world_id = (query.get("world_id") or ["MRL_main"])[0]
                session_id = (query.get("session_id") or [None])[0]
                self._write(200, runtime.recall(world_id=world_id, session_id=session_id))
                return
            self._write(404, {"ok": False, "error": "MRL_ROUTE_NOT_FOUND"})

        def do_POST(self) -> None:  # noqa: N802
            try:
                body = _read_json(self)
                if self.path == "/v1/mother/run":
                    result = runtime.run(
                        prompt=str(body.get("prompt") or ""),
                        world_id=str(body.get("world_id") or "MRL_main"),
                        session_id=body.get("session_id"),
                        system_prompt=str(
                            body.get("system_prompt")
                            or "You are the local MRL AI mother runtime."
                        ),
                    )
                    self._write(200, result)
                    return
                self._write(404, {"ok": False, "error": "MRL_ROUTE_NOT_FOUND"})
            except ValueError as exc:
                self._write(400, {"ok": False, "error": str(exc)})
            except Exception as exc:  # runtime failure is already evidence-recorded
                self._write(503, {"ok": False, "error": str(exc)})

        def log_message(self, format_string: str, *args: object) -> None:
            print(f"MRL_APIWorks {self.address_string()} {format_string % args}")

    return MRLAPIWorksHandler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7811)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("baseline gateway must bind to loopback; use a governed proxy for exposure")
    runtime = MRLMotherRuntime.from_file(args.config, args.data_dir)
    server = ThreadingHTTPServer((args.host, args.port), build_handler(runtime))
    print(json.dumps(runtime.health(), ensure_ascii=False, sort_keys=True))
    print(f"MRL_APIWORKS_GATEWAY_LISTENING http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        # graceful shutdown on Ctrl-C; no cleanup needed beyond server_close() in finally
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

