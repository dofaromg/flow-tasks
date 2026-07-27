#!/usr/bin/env python3
"""Validate MRL root authority and reversible naming changes.

This validator is intentionally dependency-free so it can run in recovery,
CI, Windows, Linux, and DL580 pre-deployment environments.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "MRL_NAMING_LINEAGE_REGISTRY_v1.json"
AUTHORITY = ROOT / "MRL_Mother" / "00_rootlaw" / "MRL_ROOT_AUTHORITY_v1.md"


def fail(message: str) -> None:
    print(f"MRL_ROOT_GATE_FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def git_changed_files(base: str, head: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        fail(proc.stderr.strip() or "git diff failed")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def main() -> int:
    if not REGISTRY.is_file() or REGISTRY.stat().st_size == 0:
        fail("missing or empty naming registry")
    if not AUTHORITY.is_file() or AUTHORITY.stat().st_size == 0:
        fail("missing or empty root authority document")

    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("canonical_root") != "MRL":
        fail("canonical_root must be MRL")
    if data.get("origin_signature") != "MrLiouWord":
        fail("origin_signature must be MrLiouWord")

    hierarchy = data.get("hierarchy", {})
    for child in ("MRL_Mother", "MrLiouAI", "FlowAgent", "flowmemorysync"):
        if child not in hierarchy:
            fail(f"missing hierarchy node: {child}")
        if hierarchy[child].get("parent") != "MRL":
            fail(f"{child} must extend from MRL")

    contract = data.get("rename_contract", {})
    if contract.get("global_string_replace_allowed") is not False:
        fail("global string replacement must remain disabled")
    if contract.get("lineage_preservation_required") is not True:
        fail("lineage preservation must be required")

    if len(sys.argv) == 3:
        changed = git_changed_files(sys.argv[1], sys.argv[2])
        protected = tuple(data.get("protected_path_prefixes", []))
        touched = [path for path in changed if path.startswith(protected)]
        allowlist = ROOT / ".mrl" / "lineage-change-allowlist.txt"
        allowed: set[str] = set()
        if allowlist.is_file():
            allowed = {
                line.strip()
                for line in allowlist.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            }
        forbidden = [path for path in touched if path not in allowed]
        if forbidden:
            preview = "\n".join(f"  - {path}" for path in forbidden[:50])
            fail(
                "historical lineage paths changed without explicit allowlist:\n"
                + preview
            )

    print("MRL_ROOT_GATE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
