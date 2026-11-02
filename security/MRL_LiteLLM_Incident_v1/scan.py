"""MRL-32 static scanner. Run ONLY with a trusted interpreter: python -I -S.

Never imports target packages, runs target tools, extracts archives or loads .pth.
HIT means a reference/artifact indicator, not proof of execution/exfiltration.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
POLICY = json.loads((HERE / "policy.json").read_text(encoding="utf-8"))
CONTROL = "security/MRL_LiteLLM_Incident_v1"
SKIP = {".git", "node_modules", "__pycache__"}
EXT = {".txt", ".in", ".toml", ".lock", ".json", ".yaml", ".yml",
       ".sh", ".ps1", ".py", ".cfg", ".ini", ".env", ".log"}
IMAGE = re.compile(r"(?<![\w.-])(?:[\w.-]+(?::\d+)?/)*litellm(?:[-_]database|[-_]non_root|[-_]spend_logs)?(?::[\w.${}-]+)?(?:@sha256:[a-fA-F0-9]+)?", re.I)
MENTION = re.compile(r"(?<![\w-])litellm(?![\w-])", re.I)
EXACT = re.compile(r"\blitellm(?:\[[^\]]*\])?\s*(?:===|==|[=:])\s*[\"']?v?(\d+\.\d+\.\d+(?:[\w.+-]*))", re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def version_state(version):
    # PEP 440 equivalent release forms (v prefix, trailing zero, local suffix).
    value = version.lower().lstrip("v").split("+")[0]
    if re.fullmatch(r"\d+(?:\.\d+)+", value):
        def normalized(raw):
            parts = [int(part) for part in raw.split(".")]
            while parts and parts[-1] == 0:
                parts.pop()
            return parts
        if any(normalized(value) == normalized(denied) for denied in POLICY["deny_versions"]):
            return "HIT"
    return "NO_HIT"


def inspect_text(text):
    """Return normalized rules only; never include raw lines or secret values."""
    result = []
    def add(state, rule):
        if (state, rule) not in result:
            result.append((state, rule))
    for digest in re.findall(r"(?:sha256:)?\b([a-fA-F0-9]{64})\b", text):
        if digest.lower() in POLICY["bad_file_sha256"]:
            add("HIT", "affected_artifact_hash")
        if any(digest.lower().startswith(p) for p in POLICY["bad_digest_prefixes"]):
            add("HIT", "affected_image_digest_or_published_prefix")
    metadata_name = re.search(r"^Name:\s*litellm\s*$", text, re.I | re.M)
    metadata_version = re.search(r"^Version:\s*(\S+)", text, re.I | re.M)
    if metadata_name and metadata_version:
        add(version_state(metadata_version[1]), "structured_installed_metadata")
    # Block known bad version even if a second reference in the file is pinned safely.
    for denied in POLICY["deny_versions"]:
        if re.search(r"\blitellm(?:\[[^\]]*\])?[^\n]{0,24}?" + re.escape(denied) + r"(?![\w.-])", text, re.I):
            add("HIT", "affected_version_reference")
    for image in IMAGE.finditer(text):
        value = image.group().lower()
        if "/" not in value and ":" not in value and "@" not in value:
            continue  # Python package, handled separately below.
        tag = value.split("@", 1)[0].rsplit(":", 1)[-1]
        if tag.lstrip("v") in POLICY["deny_versions"]:
            add("HIT", "affected_image_tag")
        elif tag in POLICY["deny_tags"] or "@sha256:" not in value:
            add("UNKNOWN", "image_requires_immutable_digest")
        else:
            add("UNKNOWN", "image_requires_signature_provenance_and_sbom_verification")
    # Structured lockfile / SBOM records, without executing any config.
    objects = []
    try:
        objects.append(json.loads(text))
    except (ValueError, TypeError):
        pass
    try:
        import tomllib
        objects.append(tomllib.loads(text))
    except (ValueError, ImportError):
        pass
    def walk(obj):
        if isinstance(obj, dict):
            if str(obj.get("name", "")).lower() == "litellm":
                version = str(obj.get("version", ""))
                add(version_state(version) if re.fullmatch(r"v?\d+\.\d+\.\d+[\w.+-]*", version) else "UNKNOWN", "structured_package_version")
            for key, val in obj.items():
                if key.lower() == "litellm":
                    raw = val.get("version", "") if isinstance(val, dict) else str(val)
                    m = re.fullmatch(r"(?:==|===)?\s*(v?\d+\.\d+\.\d+[\w.+-]*)", raw)
                    add(version_state(m[1]) if m else "UNKNOWN", "structured_dependency")
                walk(val)
        elif isinstance(obj, list):
            for child in obj:
                walk(child)
    for obj in objects:
        walk(obj)
    # Each mention must be accounted for. Unknown syntax/ranges/imports fail closed.
    for line in text.splitlines():
        if not MENTION.search(line) or line.lstrip().startswith("#"):
            continue
        matches = list(EXACT.finditer(line))
        if matches:
            for match in matches:
                add(version_state(match[1]), "exact_package_pin")
            if len(matches) < len(list(MENTION.finditer(line))):
                add("UNKNOWN", "additional_unresolved_reference")
        elif re.search(r"\blitellm(?:\[[^\]]*\])?\s*(?:[<>~!]|@)", line, re.I):
            add("UNKNOWN", "unresolved_package_constraint")
        elif not result or not any(rule.startswith("structured_") for _, rule in result):
            add("UNKNOWN", "unresolved_litellm_reference")
    return result


def scan(root, runtime=False):
    """Read local files only. Missing, unreadable, links and archives stay UNKNOWN."""
    root = Path(root)
    findings, files, gaps = [], [], []
    if not root.is_dir() or root.is_symlink():
        return {"state": "UNKNOWN", "findings": [], "files": [], "gaps": ["root_unavailable_or_symlink"]}
    def finding(path, state, rule):
        findings.append({"path": path, "state": state, "rule": rule})
    def onerror(error):
        gaps.append({"path": os.path.relpath(error.filename, root), "reason": "directory_unreadable"})
    for directory, dirs, names in os.walk(root, followlinks=False, onerror=onerror):
        for name in list(dirs):
            path = Path(directory) / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                gaps.append({"path": rel, "reason": "symlink_not_followed"})
                dirs.remove(name)
            elif (not runtime and name in SKIP) or (not runtime and rel == CONTROL):
                gaps.append({"path": rel, "reason": "declared_exclusion"})
                dirs.remove(name)
            elif re.fullmatch(r"litellm-1\.107\.0\.dist-info", name, re.I):
                finding(rel, "HIT", "affected_installed_metadata_directory")
        for name in sorted(names):
            path = Path(directory) / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                gaps.append({"path": rel, "reason": "symlink_not_followed"})
                continue
            if name in {"cook.pth", "cook.py", "sitecustomize.py"} or re.fullmatch(r"(?:cook|sitecustomize).*\.pyc", name):
                finding(rel, "UNKNOWN", "startup_hook_requires_static_investigation")
            archive = name.endswith((".zip", ".whl", ".tar.gz", ".tgz", ".flpkg"))
            candidate = path.suffix.lower() in EXT or "dockerfile" in name.lower() or name == "Pipfile" or name == "METADATA"
            if not (candidate or archive or runtime):
                continue
            try:
                size = path.stat().st_size
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
                hexdigest = digest.hexdigest()
                files.append({"path": rel, "size": size, "sha256": hexdigest})
                if hexdigest in POLICY["bad_file_sha256"]:
                    finding(rel, "HIT", "affected_artifact_hash")
                if re.search(r"litellm[-_]1\.107\.0(?:-|\.)", name, re.I):
                    finding(rel, "HIT", "affected_artifact_filename")
                if archive:
                    gaps.append({"path": rel, "reason": "archive_not_extracted"})
                elif candidate and size <= 8 * 1024 * 1024:
                    data = path.read_bytes()
                    if b"\x00" in data:
                        gaps.append({"path": rel, "reason": "binary_not_parsed"})
                    else:
                        for state, rule in inspect_text(data.decode("utf-8-sig")):
                            finding(rel, state, rule)
                elif candidate:
                    gaps.append({"path": rel, "reason": "text_size_limit"})
            except (OSError, UnicodeError):
                gaps.append({"path": rel, "reason": "unreadable_or_non_utf8"})
    incomplete = any(g.get("reason") != "declared_exclusion" for g in gaps if isinstance(g, dict))
    state = "HIT" if any(f["state"] == "HIT" for f in findings) else "UNKNOWN" if incomplete or any(f["state"] == "UNKNOWN" for f in findings) else "NO_HIT"
    return {"schema": "MRL_LiteLLM_Scan/v1.0.0", "origin_signature": "MrLiouWord",
            "scanned_at_utc": datetime.now(timezone.utc).isoformat(),
            "state": state, "scope": "static_selected_files_only", "runtime_verified": False,
            "policy_sha256": sha((HERE / "policy.json").read_bytes()),
            "scanner_sha256": sha(Path(__file__).read_bytes()),
            "findings": findings, "files": sorted(files, key=lambda f: f["path"]), "gaps": gaps}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--output", required=True, help="new private evidence file outside scan root")
    parser.add_argument("--runtime", action="store_true", help="include venv/cache files; clean interpreter ONLY")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.is_relative_to(Path(args.root).resolve()):
        parser.error("output must be outside root to prevent recursive evidence/self matches")
    report = scan(args.root, args.runtime)
    # create-only preserves evidence history
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"state": report["state"], "files": len(report["files"]),
                      "findings": len(report["findings"]), "gaps": len(report["gaps"])}))
    return {"NO_HIT": 0, "HIT": 1, "UNKNOWN": 2}[report["state"]]


if __name__ == "__main__":
    sys.exit(main())
