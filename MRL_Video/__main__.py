"""MRL Video CLI: local queue operations and persistent private worker server."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from .audit import verify_package
from .model import VideoError
from .service import Service
from .store import Store, TERMINAL


def output(value):
    """Machine-readable pipes; optional rich formatting on interactive terminals."""
    if sys.stdout.isatty():
        try:
            from rich import print_json
            print_json(data=value, ensure_ascii=False)
            return
        except ImportError:
            pass
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="MRL local evidence-backed video production")
    parser.add_argument("--root", type=Path, default=Path(os.environ.get("MRL_VIDEO_ROOT", "MRL_video_data")))
    parser.add_argument("--source-root", type=Path, default=Path(os.environ.get("MRL_VIDEO_SOURCE_ROOT", ".")))
    parser.add_argument("--font", type=Path, default=Path(os.environ.get("MRL_VIDEO_FONT", "font-not-configured.ttf")))
    parser.add_argument("--law", type=Path, default=Path(os.environ["MRL_VIDEO_LAW"]) if os.environ.get("MRL_VIDEO_LAW") else None)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("submit", "run", "branch"):
        item = sub.add_parser(name)
        item.add_argument("request", type=Path)
        item.add_argument("--idempotency")
        if name == "branch":
            item.add_argument("--parent", required=True)
    for name in ("status", "cancel", "events", "load-version"):
        sub.add_parser(name).add_argument("job_id")
    item = sub.add_parser("diff")
    item.add_argument("left")
    item.add_argument("right")
    sub.add_parser("list")
    sub.add_parser("verify-chain")
    sub.add_parser("verify-package").add_argument("zip", type=Path)
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=7812)
    serve.add_argument("--allow-host", action="append", default=[])
    serve.add_argument("--workers", type=int, choices=range(1, 5), default=2)
    args = parser.parse_args()
    if args.command == "verify-package":
        output(verify_package(args.zip))
        return 0
    if args.command in {"run", "serve"}:
        service = Service(args.root, args.source_root, args.font, getattr(args, "workers", 2), args.law)
        if not args.font.is_file():
            raise VideoError("Configure MRL_VIDEO_FONT as a local TTF/OTF/TTC font")
        if args.command == "serve":
            from .web import Server
            key = os.environ.get("MRL_VIDEO_API_KEY") or os.environ.get("MRL_BRIDGE_API_KEY", "")
            server = Server((args.host, args.port), service, key, args.allow_host)
            try:
                service.start()
                output({"service": "MRL_Video", "address": list(server.server_address), "status": "READY"})
                server.serve_forever(poll_interval=.25)
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
                service.close()
            return 0
        service.start()
        try:
            request = json.loads(args.request.read_text(encoding="utf-8"))
            job = service.store.submit(request, args.idempotency)
            while service.store.get(job["id"])["state"] not in TERMINAL:
                time.sleep(.25)
            job = service.store.get(job["id"])
            output(job)
            return 0 if job["state"] == "SUCCEEDED" else 1
        finally:
            service.close()
    store = Store(args.root)
    if args.command in {"submit", "branch"}:
        value = store.submit(json.loads(args.request.read_text(encoding="utf-8")), args.idempotency,
                             getattr(args, "parent", None))
    elif args.command == "status":
        value = store.get(args.job_id)
    elif args.command == "cancel":
        value = store.cancel(args.job_id)
    elif args.command == "events":
        value = store.history(args.job_id)
    elif args.command == "load-version":
        value = store.request(args.job_id)
    elif args.command == "diff":
        value = store.diff(args.left, args.right)
    elif args.command == "list":
        value = store.list()
    else:
        valid = store.verify_chain()
        output({"event_chain_valid": valid})
        return 0 if valid else 1
    output(value)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VideoError, OSError, ValueError, KeyError) as exc:
        output({"status": "FAIL", "error": str(exc) if isinstance(exc, VideoError) else type(exc).__name__})
        sys.exit(1)
