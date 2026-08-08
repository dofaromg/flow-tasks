#!/usr/bin/env python3
import argparse
import hashlib
import http.server
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

# ── Product naming ──────────────────────────────────────────────────────────
# Try to import the centralized naming model from the repository root.
# If the script is run from a different working directory, fall back to
# inline defaults so the runtime always stays self-contained.
try:
    _repo_root = Path(__file__).resolve().parents[2]
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))
    from flowcore_naming import (  # type: ignore[import]
        event_name as _event_name,
        health_metadata as _health_metadata,
        index_metadata as _index_metadata,
        server_banner as _server_banner,
        server_version_header as _server_version_header,
        cli_description as _cli_description,
    )
    _NAMING_AVAILABLE = True
except ImportError:
    _NAMING_AVAILABLE = False

    def _event_name(component: str, action: str) -> str:  # type: ignore[misc]
        return f"mrliou.flowcore.{component}.{action}"

    def _health_metadata(component: str = "runtime") -> Dict[str, str]:  # type: ignore[misc]
        return {}

    def _index_metadata() -> Dict[str, str]:  # type: ignore[misc]
        return {}

    def _server_banner(component: str = "runtime", version: str | None = None) -> str:  # type: ignore[misc]
        return "AI Computer Runtime"

    def _server_version_header(component: str = "runtime") -> str:  # type: ignore[misc]
        return "AIComputerRuntime/0.1"

    def _cli_description(component: str = "runtime") -> str:  # type: ignore[misc]
        return "AI Computer Runtime"
# ────────────────────────────────────────────────────────────────────────────

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
TRACE_FILE = Path("artifacts/trace/trace.jsonl")
INDEX_FILE = Path("artifacts/index/manifest.json")


def get_vault_root() -> Path:
    env_root = os.environ.get("VAULT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


def ensure_directories() -> None:
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    Path("work").mkdir(parents=True, exist_ok=True)


def safe_path(relative_path: str) -> Path:
    root = get_vault_root()
    target = (root / relative_path).resolve()
    if os.path.commonpath([root, target]) != str(root):
        raise ValueError("path escapes vault root")
    return target


def read_last_trace() -> Tuple[int, str]:
    if not TRACE_FILE.exists():
        return 0, ""
    with TRACE_FILE.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        if size == 0:
            return 0, ""
        offset = min(4096, size)
        handle.seek(-offset, os.SEEK_END)
        data = handle.read().splitlines()
        if not data:
            return 0, ""
        last = data[-1].decode("utf-8")
    try:
        payload = json.loads(last)
        return int(payload.get("tick", 0)), str(payload.get("merkle_root", ""))
    except json.JSONDecodeError:
        return 0, ""


def compute_merkle_root(prev_root: str, payload: Dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    hasher = hashlib.sha256()
    hasher.update(prev_root.encode("utf-8"))
    hasher.update(normalized)
    return hasher.hexdigest()


def append_trace(operation: str, path: Optional[str], status: str, detail: Dict[str, Any]) -> Dict[str, Any]:
    ensure_directories()
    last_tick, last_root = read_last_trace()
    tick = last_tick + 1
    payload = {
        "operation": operation,
        "path": path,
        "status": status,
        "detail": detail,
    }
    merkle_root = compute_merkle_root(last_root, payload)
    record: Dict[str, Any] = {
        "tick": tick,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "operation": operation,
        "event": _event_name("trace", operation),
        "path": path,
        "status": status,
        "detail": detail,
        "merkle_root": merkle_root,
    }
    with TRACE_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def file_info(target: Path) -> Dict[str, Any]:
    stat = target.stat()
    return {
        "path": str(target),
        "name": target.name,
        "is_dir": target.is_dir(),
        "is_file": target.is_file(),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }


def list_directory(relative_path: str) -> List[Dict[str, Any]]:
    target = safe_path(relative_path)
    if not target.exists():
        raise FileNotFoundError("path not found")
    if not target.is_dir():
        raise NotADirectoryError("path is not a directory")
    entries = []
    for entry in sorted(target.iterdir(), key=lambda p: p.name):
        entries.append(file_info(entry))
    return entries


def read_file(relative_path: str) -> Dict[str, Any]:
    target = safe_path(relative_path)
    if not target.exists():
        raise FileNotFoundError("path not found")
    if not target.is_file():
        raise IsADirectoryError("path is not a file")
    content = target.read_text(encoding="utf-8")
    return {"path": str(target), "content": content}


def write_file(relative_path: str, content: str) -> Dict[str, Any]:
    target = safe_path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target), "bytes": len(content.encode("utf-8"))}


def make_directory(relative_path: str, parents: bool = True) -> Dict[str, Any]:
    target = safe_path(relative_path)
    target.mkdir(parents=parents, exist_ok=True)
    return {"path": str(target)}


def compute_index() -> Dict[str, Any]:
    root = get_vault_root()
    records: List[Dict[str, Any]] = []
    ignore_dirs = {".git", "node_modules", "artifacts", "work"}
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        if current_path == root:
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for name in files:
            file_path = current_path / name
            if file_path == INDEX_FILE or file_path == TRACE_FILE:
                continue
            rel_path = file_path.relative_to(root)
            digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
            stat = file_path.stat()
            records.append(
                {
                    "path": str(rel_path),
                    "sha256": digest,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                }
            )
    records.sort(key=lambda item: item["path"])
    hasher = hashlib.sha256()
    for item in records:
        hasher.update(item["path"].encode("utf-8"))
        hasher.update(item["sha256"].encode("utf-8"))
    merkle_root = hasher.hexdigest()
    manifest: Dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": str(root),
        "file_count": len(records),
        "files": records,
        "merkle_root": merkle_root,
        "product": _index_metadata(),
    }
    ensure_directories()
    INDEX_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def info_path(relative_path: str) -> Dict[str, Any]:
    target = safe_path(relative_path)
    if not target.exists():
        raise FileNotFoundError("path not found")
    return file_info(target)


def health_status() -> Dict[str, Any]:
    result: Dict[str, Any] = {"status": "ok", "root": str(get_vault_root())}
    result.update(_health_metadata("runtime"))
    return result


def run_operation(operation: str, path: Optional[str], func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        trace = append_trace(operation, path, "ok", {"result": "success"})
        return True, result, trace
    except Exception as exc:  # noqa: BLE001 - want to capture error details
        trace = append_trace(operation, path, "error", {"error": str(exc)})
        return False, {"error": str(exc)}, trace


class RuntimeHandler(http.server.BaseHTTPRequestHandler):
    server_version = _server_version_header("runtime")

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        data = self.rfile.read(length)
        return json.loads(data.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == "/health":
            ok, result, trace = run_operation("health", None, health_status)
            self._send_json(200, {"ok": ok, "data": result, "trace": trace})
            return
        if parsed.path == "/list":
            target = params.get("path", ["."])[0]
            ok, result, trace = run_operation("list", target, list_directory, target)
            status = 200 if ok else 400
            self._send_json(status, {"ok": ok, "data": result, "trace": trace})
            return
        if parsed.path == "/read":
            target = params.get("path", [""])[0]
            ok, result, trace = run_operation("read", target, read_file, target)
            status = 200 if ok else 400
            self._send_json(status, {"ok": ok, "data": result, "trace": trace})
            return
        if parsed.path == "/info":
            target = params.get("path", [""])[0]
            ok, result, trace = run_operation("info", target, info_path, target)
            status = 200 if ok else 400
            self._send_json(status, {"ok": ok, "data": result, "trace": trace})
            return
        self._send_json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            body = self._parse_body()
        except json.JSONDecodeError as exc:
            self._send_json(400, {"ok": False, "error": f"invalid json: {exc}"})
            return
        if parsed.path == "/write":
            target = body.get("path")
            content = body.get("content", "")
            ok, result, trace = run_operation("write", target, write_file, target, content)
            status = 200 if ok else 400
            self._send_json(status, {"ok": ok, "data": result, "trace": trace})
            return
        if parsed.path == "/mkdir":
            target = body.get("path")
            ok, result, trace = run_operation("mkdir", target, make_directory, target)
            status = 200 if ok else 400
            self._send_json(status, {"ok": ok, "data": result, "trace": trace})
            return
        if parsed.path == "/index":
            ok, result, trace = run_operation("index", None, compute_index)
            status = 200 if ok else 400
            self._send_json(status, {"ok": ok, "data": result, "trace": trace})
            return
        self._send_json(404, {"ok": False, "error": "not found"})

    def log_message(self, format: str, *args: Any) -> None:
        return


def serve(host: str, port: int) -> None:
    ensure_directories()
    server = http.server.ThreadingHTTPServer((host, port), RuntimeHandler)
    print(_server_banner("runtime"))
    print(f"Listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")


def cli() -> None:
    parser = argparse.ArgumentParser(description=_cli_description("runtime"))
    sub = parser.add_subparsers(dest="command", required=True)

    serve_parser = sub.add_parser("serve", help="Run HTTP server")
    serve_parser.add_argument("--host", default=DEFAULT_HOST)
    serve_parser.add_argument("--port", type=int, default=DEFAULT_PORT)

    list_parser = sub.add_parser("list")
    list_parser.add_argument("path", nargs="?", default=".")

    read_parser = sub.add_parser("read")
    read_parser.add_argument("path")

    write_parser = sub.add_parser("write")
    write_parser.add_argument("path")
    write_parser.add_argument("--content", default=None)

    mkdir_parser = sub.add_parser("mkdir")
    mkdir_parser.add_argument("path")

    info_parser = sub.add_parser("info")
    info_parser.add_argument("path")

    sub.add_parser("index")
    sub.add_parser("health")

    args = parser.parse_args()

    if args.command == "serve":
        serve(args.host, args.port)
        return

    if args.command == "list":
        ok, result, _ = run_operation("list", args.path, list_directory, args.path)
    elif args.command == "read":
        ok, result, _ = run_operation("read", args.path, read_file, args.path)
    elif args.command == "write":
        content = args.content
        if content is None:
            content = sys.stdin.read()
        ok, result, _ = run_operation("write", args.path, write_file, args.path, content)
    elif args.command == "mkdir":
        ok, result, _ = run_operation("mkdir", args.path, make_directory, args.path)
    elif args.command == "info":
        ok, result, _ = run_operation("info", args.path, info_path, args.path)
    elif args.command == "index":
        ok, result, _ = run_operation("index", None, compute_index)
    elif args.command == "health":
        ok, result, _ = run_operation("health", None, health_status)
    else:
        ok, result = False, {"error": "unknown command"}

    if ok:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    cli()
