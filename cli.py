from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

from amp.ledger import Ledger
from amp.storage import Storage
from adapters.notion_adapter import NotionAdapter
from adapters.github_adapter import GitHubAdapter


DEFAULT_CONFIG_PATH = Path("config.yaml")


def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open() as f:
        return yaml.safe_load(f)


def get_ledger(config: Dict[str, Any]) -> Ledger:
    data_dir = Path(config.get("data_dir", "data"))
    storage = Storage(data_dir)
    return Ledger(storage)


def cmd_init(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ledger = get_ledger(config)
    ledger.init(reset=args.reset)
    print(f"Ledger initialized at {ledger.storage.data_dir}")


def cmd_append(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ledger = get_ledger(config)
    entry = ledger.append(args.content)
    print(json.dumps(entry.to_dict(), indent=2, ensure_ascii=False))


def cmd_snapshot(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ledger = get_ledger(config)
    snap = ledger.snapshot(args.name)
    print(json.dumps(snap, indent=2, ensure_ascii=False))


def cmd_verify(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ledger = get_ledger(config)
    ok, msg = ledger.verify()
    if ok:
        print(msg)
    else:
        print(msg, file=sys.stderr)
        sys.exit(1)


def cmd_log(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ledger = get_ledger(config)
    entries = ledger.log(args.n)
    print(json.dumps(entries, indent=2, ensure_ascii=False))


def cmd_notion_sync(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ledger = get_ledger(config)
    entries = ledger.log(args.n)
    notion_cfg = config.get("notion", {})
    adapter = NotionAdapter(ledger.storage.data_dir)
    export_path = adapter.sync_entries(entries, notion_cfg)
    print(f"Synced {len(entries)} entries to Notion (export at {export_path})")


def cmd_github_export(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ledger = get_ledger(config)
    entries = ledger.log(args.n)
    adapter = GitHubAdapter(ledger.storage.data_dir)
    path = adapter.export(entries)
    print(f"Exported {len(entries)} entries to {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AMP Index-only ledger CLI")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to config file (default: config.yaml)",
    )
    subparsers = parser.add_subparsers(dest="command")

    p_init = subparsers.add_parser("init", help="Initialize the ledger")
    p_init.add_argument("--reset", action="store_true", help="Reset the ledger before initializing")
    p_init.set_defaults(func=cmd_init)

    p_append = subparsers.add_parser("append", help="Append a new entry")
    p_append.add_argument("content", help="Content to append")
    p_append.set_defaults(func=cmd_append)

    p_snapshot = subparsers.add_parser("snapshot", help="Create a named snapshot")
    p_snapshot.add_argument("name", help="Snapshot name")
    p_snapshot.set_defaults(func=cmd_snapshot)

    p_verify = subparsers.add_parser("verify", help="Verify chain integrity")
    p_verify.set_defaults(func=cmd_verify)

    p_log = subparsers.add_parser("log", help="Show ledger log")
    p_log.add_argument("--n", type=int, default=10, help="Number of entries to show (0 for all)")
    p_log.set_defaults(func=cmd_log)

    p_notion = subparsers.add_parser("notion-sync", help="Sync entries to Notion (best effort)")
    p_notion.add_argument("--n", type=int, default=20, help="Number of entries to sync")
    p_notion.set_defaults(func=cmd_notion_sync)

    p_github = subparsers.add_parser("github-export", help="Export entries to GitHub adapter")
    p_github.add_argument("--n", type=int, default=20)
    p_github.set_defaults(func=cmd_github_export)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
