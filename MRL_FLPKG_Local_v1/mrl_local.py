"""CLI and loopback operation console for the MRL FLPKG worker."""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import sys
import threading

from mrl_package import extract_verified, verify_package
from mrl_runtime import Runtime

DEFAULT = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share"))) / "MRL_FLPKG"
PAGE = Path(__file__).with_name("console.html")


def worker(runtime, stop):
    while not stop.is_set():
        if runtime.step() is None:
            stop.wait(0.5)


def serve(runtime, port):
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def headers_response(self, code, mime, body):
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def reply(self, code, value):
            self.headers_response(code, "application/json; charset=utf-8",
                         json.dumps(value, ensure_ascii=False).encode())

        def allow(self):
            return self.headers_host() == f"127.0.0.1:{self.server.server_port}"

        def headers_host(self):
            return self.headers.get("Host")

        def do_GET(self):
            if not self.allow() or self.path != "/":
                self.reply(404, {"error": "Not found"})
                return
            html = PAGE.read_text(encoding="utf-8").replace("__TOKEN__", token)
            self.headers_response(200, "text/html; charset=utf-8", html.encode())

        def do_POST(self):
            if (not self.allow() or
                    not hmac.compare_digest(self.headers.get("X-MRL-Token", ""), token)):
                self.reply(403, {"error": "Local console token required"})
                return
            if self.headers.get("Origin") not in (None, f"http://{self.headers_host()}"):
                self.reply(403, {"error": "Origin rejected"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 8 * 1024 * 1024:
                    raise ValueError("Request size not permitted")
                if self.headers.get_content_type() != "application/json":
                    raise ValueError("Expected application/json")
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError("Expected JSON object")
                operations = {
                    "/api/status": runtime.status,
                    "/api/submit": lambda **kw: {"job": runtime.submit(**kw)},
                    "/api/cancel": lambda **kw: {"cancel_requested": runtime.cancel(**kw) is None},
                    "/api/retry": lambda **kw: {"job": runtime.retry(**kw)},
                    "/api/quota": lambda **kw: {"updated": runtime.config(**kw) is None},
                    "/api/verify": lambda job: verify_job(runtime, job),
                }
                action = operations.get(self.path)
                if action is None:
                    self.reply(404, {"error": "Not found"})
                    return
                self.reply(200, action(**data))
            except (ValueError, TypeError, OSError, KeyError, RuntimeError) as exc:
                self.reply(400, {"error": str(exc)})

    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        stop = threading.Event()
        thread = threading.Thread(target=worker, args=(runtime, stop), daemon=True)
        thread.start()
        print(f"http://127.0.0.1:{server.server_port}/", flush=True)
        try:
            server.serve_forever()
        finally:
            stop.set()


def verify_job(runtime, job):
    from mrl_runtime import digest_file
    row = runtime.status(job)
    if row["status"] != "done":
        raise ValueError("Job is not complete")
    result = row["result"]
    path = runtime.root / "artifacts" / result["file"]
    if digest_file(path) != result["sha256"] or path.stat().st_size != result["size"]:
        raise ValueError("Output digest or size differs")
    if row["kind"] == "package":
        verify_package(path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT)
    sub = parser.add_subparsers(dest="command", required=True)
    web = sub.add_parser("serve")
    web.add_argument("--port", type=int, default=8765)
    run = sub.add_parser("worker")
    run.add_argument("--once", action="store_true")
    submit = sub.add_parser("submit")
    submit.add_argument("kind", choices=["generate", "package", "diagnostic"])
    submit.add_argument("value", nargs="?", default="")
    submit.add_argument("--source-job")
    submit.add_argument("--parent")
    submit.add_argument("--target", default="portable")
    submit.add_argument("--options", type=json.loads)
    state = sub.add_parser("status")
    state.add_argument("job", nargs="?")
    for name in ("retry", "cancel", "verify-job"):
        sub.add_parser(name).add_argument("job")
    quota = sub.add_parser("quota")
    quota.add_argument("limit", type=int)
    quota.add_argument("mode", choices=["alert", "deny", "queue", "throttle"])
    quota.add_argument("--rate", type=int, default=1048576)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("package", type=Path)
    extract = sub.add_parser("extract")
    extract.add_argument("package", type=Path)
    extract.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.command == "inspect":
        output = verify_package(args.package)
    elif args.command == "extract":
        output = extract_verified(args.package, args.destination)
    else:
        runtime = Runtime(args.data)
        if args.command == "serve":
            serve(runtime, args.port)
            return
        if args.command == "worker":
            if not args.once:
                worker(runtime, threading.Event())
                return
            output = runtime.step()
            if output and output["status"] not in {"done", "waiting"}:
                print(json.dumps(output, ensure_ascii=False, indent=2))
                sys.exit(1)
        elif args.command == "submit":
            output = {"job": runtime.submit(args.kind, args.value, source_job=args.source_job,
                                            parent=args.parent, target=args.target, options=args.options)}
        elif args.command == "status":
            output = runtime.status(args.job)
        elif args.command == "retry":
            output = {"job": runtime.retry(args.job)}
        elif args.command == "cancel":
            runtime.cancel(args.job)
            output = {"cancel_requested": True}
        elif args.command == "quota":
            runtime.config(args.limit, args.mode, args.rate)
            output = runtime.status()["quota"]
        else:
            output = verify_job(runtime, args.job)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
