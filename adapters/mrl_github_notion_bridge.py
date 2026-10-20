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
    required = {"schema": "MRL_GitHub_Notion_Bridge_v1",
                "parent_module": "MRL_FlowEditBridge_v0.2",
                "parent_source": "dropbox:/MRL_FlowEditBridge_v0/MRL_FlowEditBridge_v0.2/MRL_Notion/MRL_Edit.py",
                "operation": "github_read_to_notion_append_and_readback",
                "notion_definition_direction": "upstream_reference_only",
                "notion_authority_page": "3ede7f4e-6c55-8064-a840-e3a531cb2aef",
                "notion_receipt_page": "3e9e7f4e-6c55-80e4-9f3d-c8292dda835a"}
    if any(config.get(k) != v for k, v in required.items()):
        raise BridgeError("Unapproved mapping or upstream contract")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", config.get("repository", "")):
        raise BridgeError("Invalid repository")
    for field in ("notion_authority_page", "notion_receipt_page"):
        if not re.fullmatch(r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}", config.get(field, "")):
            raise BridgeError("Invalid Notion page ID")
    prs = config.get("pull_requests")
    if (not isinstance(prs, list) or not prs or any(type(n) is not int or n <= 0 for n in prs)
            or len(prs) != len(set(prs))):
        raise BridgeError("Explicit positive pull request numbers required")


def blocks(client: Client, page: str):
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
            if not block.get("archived") and not block.get("in_trash"):
                yield block
        if not result.get("has_more"):
            return
        cursor = result.get("next_cursor")
        if not cursor or cursor in seen:
            raise BridgeError("Incomplete Notion pagination")
        seen.add(cursor)


def rich_text(items: list) -> str:
    return "".join(t.get("plain_text", t.get("text", {}).get("content", "")) for t in items)


def paragraphs(client: Client, page: str):
    for block in blocks(client, page):
        if block.get("type") == "paragraph":
            yield rich_text(block["paragraph"].get("rich_text", []))


def verify_authority(config: dict, client: Client) -> dict:
    """Check the pinned live root's declarations and direct mother-page link.

    Native Wiki verification is not exposed by this pinned REST version.
    This verifies governance content, not a cryptographic signature or Wiki badge.
    """
    evidence = list(blocks(client, config["notion_authority_page"]))
    text = "\n".join(rich_text(b.get(b.get("type"), {}).get("rich_text", [])) for b in evidence)
    declarations = {re.sub(r"[\s*_：:]", "", line).lower() for line in text.splitlines()}
    if not {"canonicalauthoritymr.liou", "originsignaturemrliouword"}.issubset(declarations):
        raise BridgeError("Authority declarations unavailable or changed")
    def links(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("href", "url", "page_id") and isinstance(item, str):
                    yield item
                if key == "page" and isinstance(item, dict) and "id" in item:
                    yield item["id"]
                yield from links(item)
        elif isinstance(value, list):
            for item in value:
                yield from links(item)
    target = config["notion_receipt_page"].replace("-", "")
    if not any(target in link.replace("-", "") for link in links(evidence)):
        raise BridgeError("Authority no longer links the existing mother page")
    return {"status": "DECLARATIONS_AND_LINK_VERIFIED",
            "native_wiki_verification": "NOT_ASSESSED_BY_RUNNER"}


def sync(config: dict, client: Client, apply: bool = False, journal=None) -> dict:
    """Read source versions, optionally append receipts, and verify each write."""
    validate(config)
    pages = {}
    for field in ("notion_authority_page", "notion_receipt_page"):
        page = client.call("notion", "GET", "/pages/" + config[field])
        if page.get("archived") or page.get("in_trash") or page.get("object") != "page":
            raise BridgeError("Notion target is unavailable")
        if page.get("id", "").replace("-", "") != config[field].replace("-", ""):
            raise BridgeError("Notion page identity mismatch")
        pages[field] = {"id": page["id"], "last_edited_time": page.get("last_edited_time")}
    authority = verify_authority(config, client)
    existing = list(paragraphs(client, config["notion_receipt_page"]))
    results = []
    for number in config["pull_requests"]:
        pr = client.call("github", "GET", f"/repos/{config['repository']}/pulls/{number}")
        if (pr.get("number") != number or pr.get("base", {}).get("repo", {}).get("full_name") != config["repository"]
                or any(not re.fullmatch(r"[0-9a-f]{40}", pr.get(side, {}).get("sha", "")) for side in ("head", "base"))):
            raise BridgeError("GitHub source identity mismatch")
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
            if journal:
                journal({"phase": "APPEND_INTENT", "sha256": digest,
                         "receipt_page": config["notion_receipt_page"], "source": source})
            client.call("notion", "PATCH", f"/blocks/{config['notion_receipt_page']}/children",
                        {"children": [{"object": "block", "type": "paragraph",
                                       "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}}]})
            readback = list(paragraphs(client, config["notion_receipt_page"]))
            if [p for p in readback if p.startswith(marker)] != [text]:
                raise BridgeError("Write readback mismatch; do not blindly retry")
            existing = readback
            status = "APPEND_READBACK_PASS"
        if journal:
            journal({"phase": status, "sha256": digest})
        results.append({"source": source, "sha256": digest, "status": status})
    return {"origin_signature": "MrLiouWord", "observed_at": datetime.now(timezone.utc).isoformat(),
            "mode": "apply" if apply else "plan", "notion_pages": pages, "authority": authority, "receipts": results,
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
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        journal_path = output / f"MRL_GitHub_Notion_{stamp}.jsonl"
        def journal(event):
            with journal_path.open("a", encoding="utf-8") as stream:
                stream.write(canonical(event) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        journal({"phase": "START", "mode": "apply" if args.apply else "plan"})
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        validate(config)
        client = Client(os.environ.get("GITHUB_TOKEN", ""), os.environ.get("NOTION_TOKEN", ""))
        report = sync(config, client, args.apply, journal)
        path = output / f"MRL_GitHub_Notion_{stamp}.json"
        with path.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
        print(canonical({"receipt_file": str(path), "statuses": [r["status"] for r in report["receipts"]]}))
        return 0
    except (BridgeError, KeyError, ValueError, OSError, TypeError) as exc:
        if "journal_path" in locals() and journal_path.exists():
            journal({"phase": "FAIL_RECONCILE_BEFORE_RETRY", "error_type": type(exc).__name__})
        raise
    finally:
        lock.rmdir()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BridgeError, KeyError, ValueError, OSError, TypeError) as exc:
        # Do not print HTTP bodies, credential values or arbitrary exception messages.
        print(canonical({"status": "FAIL", "error_type": type(exc).__name__}))
        raise SystemExit(1)
