"""Operator CLI. Tokens come from the environment, never tool or command arguments."""

import argparse
import json
import re
from pathlib import Path

from ..cli import read_json
from ..core import Rejected
from .gate import default_settings
from .gateway import Gateway


def main(argv=None):
    parser = argparse.ArgumentParser(description="MRL 授權銀行／EVM 連接器")
    parser.add_argument("--ledger-policy", required=True)
    parser.add_argument("--settings", required=True)
    parser.add_argument("--root-registry", required=True)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--enable-live", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-settings")
    sub.add_parser("init-journal")
    sub.add_parser("observe").add_argument("--query", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--operation", required=True)
    plan.add_argument("--request-id", required=True)
    send = sub.add_parser("submit")
    send.add_argument("--request", required=True)
    send.add_argument("--signatures", required=True)
    send.add_argument("--signed-raw-file")
    sub.add_parser("status").add_argument("--request-id", required=True)
    args = parser.parse_args(argv)
    try:
        policy = read_json(args.ledger_policy)
        if args.command == "init-settings":
            output = default_settings(policy)
            with Path(args.settings).open("x", encoding="utf-8") as stream:
                json.dump(output, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            print(json.dumps({"state": "DISABLED_SETTINGS_CREATED", "writes_enabled": False}))
            return 0
        gateway = Gateway(policy, read_json(args.settings), args.root_registry, args.journal,
                          enable_live=args.enable_live)
        if args.command == "init-journal":
            gateway.gate.initialize_journal()
            output = {"state": "EMPTY_EXTERNAL_JOURNAL_CREATED"}
        elif args.command == "observe":
            output = gateway.observe(read_json(args.query))
        elif args.command == "plan":
            output = gateway.plan(read_json(args.operation), args.request_id)
        elif args.command == "submit":
            raw = read_json(args.signed_raw_file) if args.signed_raw_file else ""
            output = gateway.submit(read_json(args.request), read_json(args.signatures), raw)
        else:
            output = gateway.gate.status(args.request_id)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 2 if output.get("state") == "SUBMISSION_UNKNOWN" else 0
    except (Rejected, ValueError, OSError, TypeError, KeyError) as exc:
        # Paths, provider tokens, exception contexts and account secrets stay local.
        reason = str(exc) if isinstance(exc, Rejected) and re.fullmatch(r"[A-Z0-9_]+", str(exc)) else "LOCAL_INPUT_INVALID"
        print(json.dumps({"state": "EXTERNAL_OPERATION_REJECTED",
                          "reason": reason,
                          "origin_signature": "MrLiouWord"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
