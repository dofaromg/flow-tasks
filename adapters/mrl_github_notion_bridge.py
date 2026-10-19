"""MRL GitHub/Notion receipt bridge; supplements FlowEditBridge v0.2.

origin_signature: MrLiouWord. Notion definitions remain upstream.
No repository mutation, page replacement, server restart or token persistence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import urllib.error
import urllib.request


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class BridgeError(RuntimeError):
    """A connection or readback failure; never reported as synchronization success."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    """Send credentials only to fixed service endpoints, without redirects."""

    def __init__(self, github_token: str, notion_token: str) -> None:
        if not github_token or not notion_token:
            raise BridgeError("GITHUB_TOKEN and NOTION_TOKEN are required")
        self.tokens = {"github": github_token, "notion": notion_token}

    def call(self, service: str, method: str, path: str, payload=None) -> dict:
        base = {"github": "https://api.github.com", "notion": "https://api.notion.com/v1"}[service]
        if not path.startswith("/") or ".." in path or "#" in path:
            raise BridgeError("Invalid API path")
        headers = {"Authorization": "Bearer " + self.tokens[service],
                   "Content-Type": "application/json", "User-Agent": "MRL_GitHub_Notion_Bridge/1"}
        if service == "notion":
            headers["Notion-Version"] = "2022-06-28"
        else:
            headers["Accept"] = "application/vnd.github+json"
            headers["X-GitHub-Api-Version"] = "2022-11-28"
        body = canonical(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(base + path, data=body, headers=headers, method=method)
        try:
            with urllib.request.build_opener(NoRedirect()).open(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise BridgeError(f"{service} HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise BridgeError(f"{service} transport failure; reconcile before retrying writes") from None
        except (ValueError, UnicodeError):
            raise BridgeError(f"{service} returned invalid JSON") from None


def validate(config: dict) -> None:
    """Require explicit targets; forbid unknown destinations and missing lineage."""
    if config.get("origin_signature") != "MrLiouWord" or config.get("canonical_authority") != "Mr.liou":
        raise BridgeError("Invalid MRL authority configuration")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", config.get("repository", "")):
        raise BridgeError("Invalid repository")
    for field in ("notion_authority_page", "notion_receipt_page"):
        if not re.fullmatch(r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}", config.get(field, "")):
            raise BridgeError("Invalid Notion page ID")
    prs = config.get("pull_requests")
    if not isinstance(prs, list) or not prs or any(type(n) is not int or n <= 0 for n in prs):
        raise BridgeError("Explicit positive pull request numbers required")


def paragraphs(client: Client, page: str):
    """Read every top-level block, including receipts after the first 100 blocks."""
    cursor = ""
    seen = set()
    while True:
        path = f"/blocks/{page}/children?page_size=100"
        if cursor:
            from urllib.parse import quote
            path += "&start_cursor=" + quote(cursor, safe="")
        result = client.call("notion", "GET", path)
        if not isinstance(result.get("results"), list):
            raise BridgeError("Malformed Notion block listing")
        for block in result["results"]:
            if not block.get("archived") and block.get("type") == "paragraph":
                yield "".join(t.get("plain_text", t.get("text", {}).get("content", ""))
                              for t in block["paragraph"].get("rich_text", []))
        if not result.get("has_more"):
            return
        cursor = result.get("next_cursor")
        if not cursor or cursor in seen:
            raise BridgeError("Incomplete Notion pagination")
        seen.add(cursor)


def sync(config: dict, client: Client, apply: bool = False) -> dict:
    """Read source versions, optionally append receipts, and verify each write."""
    validate(config)
    pages = {}
    for field in ("notion_authority_page", "notion_receipt_page"):
        page = client.call("notion", "GET", "/pages/" + config[field])
        if page.get("archived") or page.get("in_trash") or page.get("object") != "page":
            raise BridgeError("Notion target is unavailable")
        pages[field] = {"id": page["id"], "last_edited_time": page.get("last_edited_time")}
    existing = list(paragraphs(client, config["notion_receipt_page"]))
    results = []
    for number in config["pull_requests"]:
        pr = client.call("github", "GET", f"/repos/{config['repository']}/pulls/{number}")
        # No PR body or arbitrary code is forwarded to Notion or executed.
        source = {"repository": config["repository"], "pr": number,
                  "head_sha": pr["head"]["sha"], "base_sha": pr["base"]["sha"],
                  "state": pr["state"], "merged": pr["merged"],
                  "updated_at": pr["updated_at"],
                  "source_url": f"https://github.com/{config['repository']}/pull/{number}",
                  "origin_signature": "MrLiouWord", "canonical_authority": "Mr.liou",
                  "authority_page": config["notion_authority_page"],
                  "kind": "engineering_metadata_only"}
        digest = hashlib.sha256(canonical(source).encode("utf-8")).hexdigest()
        marker = "MRL_GITHUB_NOTION_RECEIPT_v1:" + digest
        text = marker + "\n" + canonical(source)
        if len(text) > 1900:
            raise BridgeError("Receipt exceeds Notion text limit")
        matches = [p for p in existing if p.startswith(marker)]
        if matches and matches != [text]:
            raise BridgeError("Duplicate or conflicting receipt marker")
        status = "ALREADY_VERIFIED" if matches else "PLANNED"
        if apply and not matches:
            client.call("notion", "PATCH", f"/blocks/{config['notion_receipt_page']}/children",
                        {"children": [{"object": "block", "type": "paragraph",
                                       "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}}]})
            readback = list(paragraphs(client, config["notion_receipt_page"]))
            if readback.count(text) != 1:
                raise BridgeError("Write readback mismatch; do not blindly retry")
            existing = readback
            status = "APPEND_READBACK_PASS"
        results.append({"source": source, "sha256": digest, "status": status})
    return {"origin_signature": "MrLiouWord", "observed_at": datetime.now(timezone.utc).isoformat(),
            "mode": "apply" if apply else "plan", "notion_pages": pages, "receipts": results,
            "deployment_acceptance": "NOT_ASSESSED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    lock = output / "MRL_GitHub_Notion_Bridge.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise BridgeError("Bridge already running or stale lock requires review") from None
    try:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        client = Client(os.environ.get("GITHUB_TOKEN", ""), os.environ.get("NOTION_TOKEN", ""))
        report = sync(config, client, args.apply)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = output / f"MRL_GitHub_Notion_{stamp}.json"
        with path.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
        print(canonical({"receipt_file": str(path), "statuses": [r["status"] for r in report["receipts"]]}))
        return 0
    finally:
        lock.rmdir()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BridgeError, KeyError, ValueError, OSError) as exc:
        # Do not print HTTP bodies, credential values or arbitrary exception messages.
        print(canonical({"status": "FAIL", "error_type": type(exc).__name__}))
        raise SystemExit(1)
