"""Local CLI. Only public policy, signed requests and sandbox events are accepted."""

import argparse
import json
import sys
from pathlib import Path

from .core import Ledger, Rejected, canonical


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Rejected("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def read_json(path):
    raw = Path(path).read_bytes()
    if len(raw) > 1024 * 1024:
        raise Rejected("INPUT_TOO_LARGE")
    return json.loads(raw, object_pairs_hook=_unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(Rejected("NONFINITE_JSON")))


def main(argv=None):
    parser = argparse.ArgumentParser(description="MRL 金融制度核心：本地測試單位帳本")
    parser.add_argument("--policy", required=True, help="可信任來源的公開政策 JSON")
    parser.add_argument("--db", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("snapshot").add_argument("--expected-head")
    submit = sub.add_parser("submit")
    submit.add_argument("--request", required=True)
    submit.add_argument("--signatures", required=True)
    sub.add_parser("signing-bytes").add_argument("--request", required=True)
    args = parser.parse_args(argv)
    try:
        policy = read_json(args.policy)
        if args.command == "signing-bytes":
            sys.stdout.buffer.write(canonical(read_json(args.request)))
            return 0
        ledger = Ledger.create(args.db, policy) if args.command == "init" else Ledger(args.db, policy)
        if args.command == "submit":
            output = ledger.submit(read_json(args.request), read_json(args.signatures))
        else:
            output = ledger.snapshot(getattr(args, "expected_head", None))
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (Rejected, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc),
                          "real_asset_moved": False}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
