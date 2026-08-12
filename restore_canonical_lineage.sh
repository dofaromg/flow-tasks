#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="${ROOT_DIR}/.mrliou/authority-lock.json"
MODE="${1:-}"

if [[ "${MODE}" != "" && "${MODE}" != "--check" ]]; then
  echo "Usage: ./restore_canonical_lineage.sh [--check]" >&2
  exit 2
fi

if [[ ! -f "${CONFIG_PATH}" ]]; then
  echo "Missing config: ${CONFIG_PATH}" >&2
  exit 1
fi

python3 - "$ROOT_DIR" "$CONFIG_PATH" "$MODE" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
config_path = Path(sys.argv[2])
check_mode = sys.argv[3] == "--check"

cfg = json.loads(config_path.read_text(encoding="utf-8"))
signature = cfg["origin_signature"]
mappings = cfg.get("canonical_mappings", [])
governed_paths = cfg.get("governed_paths", [])
replacement_exempt = set(cfg.get("replacement_exempt_paths", []))
replacement_scope = cfg.get("replacement_scope", {})
targets = cfg.get("signature_targets", {})

md_targets = set(targets.get("markdown", []))
json_targets = set(targets.get("json", []))
yaml_targets = set(targets.get("yaml", []))

missing_files: list[str] = []
changed_files: list[str] = []
required_fixes: list[str] = []


def git(*args: str, allow_one: bool = False) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode and not (allow_one and proc.returncode == 1):
        raise SystemExit(proc.stderr.strip() or f"git command failed: {' '.join(args)}")
    return proc.stdout


def apply_replacements(content: str) -> str:
    result = content
    for item in mappings:
        src = item.get("from")
        dst = item.get("to")
        if isinstance(src, str) and src and isinstance(dst, str):
            result = result.replace(src, dst)
    return result


def list_replacement_targets() -> list[str]:
    mode = replacement_scope.get("mode", "git_tracked")
    if mode != "git_tracked":
        raise SystemExit(f"Unsupported replacement_scope.mode: {mode}")

    excluded = set(replacement_scope.get("exclude_paths", []))
    matched: set[str] = set()
    for item in mappings:
        src = item.get("from")
        if not isinstance(src, str) or not src:
            continue
        out = git("grep", "-I", "-l", "-F", "-e", src, "--", ".", allow_one=True)
        for line in out.splitlines():
            path = line.strip()
            if not path or path in excluded:
                continue
            matched.add(path)
    return sorted(matched)


def ensure_markdown_signature(content: str) -> str:
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            front_matter = content[4:end].splitlines()
            if any(line.strip() == f"origin_signature: {signature}" for line in front_matter):
                return content
            updated = front_matter + [f"origin_signature: {signature}"]
            return "---\n" + "\n".join(updated) + "\n---\n" + content[end + 5 :]
    return f"---\norigin_signature: {signature}\n---\n\n{content}"


def ensure_yaml_signature(content: str) -> str:
    lines = content.splitlines()
    for line in lines[:10]:
        if f"origin_signature: {signature}" in line:
            return content
    prefix = f"# origin_signature: {signature}\n"
    return prefix + content


def ensure_json_signature(path: Path, content: str) -> str:
    try:
        obj = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path.relative_to(root)}: {exc}") from exc
    if not isinstance(obj, dict):
        raise SystemExit(f"JSON root must be an object in {path.relative_to(root)}")
    if obj.get("origin_signature") == signature:
        return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    reordered = {"origin_signature": signature}
    for key, value in obj.items():
        if key != "origin_signature":
            reordered[key] = value
    return json.dumps(reordered, ensure_ascii=False, indent=2) + "\n"


replacement_targets = list_replacement_targets()
process_paths = sorted(set(governed_paths) | set(replacement_targets))

for rel in process_paths:
    path = root / rel
    if not path.exists():
        missing_files.append(rel)
        continue
    if path.is_dir():
        continue

    try:
        current = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    updated = current if rel in replacement_exempt else apply_replacements(current)

    if rel in md_targets:
        updated = ensure_markdown_signature(updated)
    if rel in yaml_targets:
        updated = ensure_yaml_signature(updated)
    if rel in json_targets:
        updated = ensure_json_signature(path, updated)

    if check_mode:
        if updated != current:
            required_fixes.append(rel)
    else:
        if updated != current:
            path.write_text(updated, encoding="utf-8")
            changed_files.append(rel)

required_missing = [item for item in missing_files if item in governed_paths]
if required_missing:
    print("Missing governed files:", file=sys.stderr)
    for item in required_missing:
        print(f"  - {item}", file=sys.stderr)
    raise SystemExit(1)

if check_mode:
    if required_fixes:
        print("Canonical lineage lock check failed. Files requiring restore:", file=sys.stderr)
        for item in required_fixes:
            print(f"  - {item}", file=sys.stderr)
        raise SystemExit(1)
    print("Canonical lineage lock check passed.")
else:
    print("Canonical lineage restore complete.")
    if changed_files:
        print("Updated files:")
        for item in changed_files:
            print(f"  - {item}")
    else:
        print("No changes were required.")
PY
