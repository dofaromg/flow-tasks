"""Deterministic, incremental generator for the MRL Mother Registry.

The implementation intentionally uses only the Python standard library so it can
run in recovery environments before the rest of the MRL runtime is available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REGISTRY_NAMES = (
    "assets", "knowledge_graph", "dependency_graph", "runtime_registry",
    "platform_registry", "product_registry", "organization_registry",
    "ip_registry", "governance_registry", "capability_registry",
    "service_registry", "architecture_registry", "lineage_registry",
    "evidence_registry", "archive_registry", "metadata_registry",
)
REPORT_NAMES = (
    "enterprise-asset-inventory", "enterprise-architecture", "runtime-architecture",
    "knowledge-graph", "capability-matrix", "product-portfolio", "platform-topology",
    "governance-structure", "intellectual-property-inventory", "dependency-report",
    "risk-report", "technical-debt-report", "gap-analysis", "roadmap",
    "executive-summary",
)
RUNTIME_EXTENSIONS = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".sh", ".ps1", ".go",
    ".rs", ".java", ".cs", ".c", ".cc", ".cpp", ".exe", ".dll", ".so",
}
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".7z", ".rar", ".bak"}
SOURCE_PRIORITY = {
    name: index for index, name in enumerate(
        ("dropbox", "github", "notion", "google-drive", "local-runtime", "dl580",
         "archive", "export-package", "backup-snapshot", "external-documentation"), 1
    )
}
NAMESPACE = uuid.UUID("ace9d54a-5205-50f7-84fa-d424c428a60f")


def _utc(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")


def _slug(value: str) -> str:
    value = re.sub(r"(?:copy|backup|final|old|new|v(?:ersion)?\d+(?:\.\d+)*)", "", value, flags=re.I)
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unnamed"


def _category(path: Path, runtime: bool) -> str:
    text = "/".join(path.parts).lower()
    rules = (
        ("Governance", ("governance", "policy", "rootlaw")),
        ("Intellectual Property", ("license", "patent", "trademark", "copyright")),
        ("Security", ("security", "certificate", "secret")),
        ("Infrastructure", ("terraform", "kubernetes", "cluster", "deploy", "docker")),
        ("AI", ("model", "agent", "prompt", "inference", "ai")),
        ("Product", ("product", "frontend", "mobile", "desktop")),
        ("Archives", ("archive", "backup", "snapshot")),
        ("Documentation", ("docs", "readme", "specification")),
    )
    for category, needles in rules:
        if any(needle in text for needle in needles):
            return category
    return "Runtime" if runtime else "Knowledge"


def _asset_type(path: Path) -> str:
    if path.name.lower() in {"dockerfile", "containerfile"}:
        return "container-definition"
    return {
        ".md": "markdown", ".pdf": "pdf", ".json": "json", ".yaml": "yaml",
        ".yml": "yaml", ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".sql": "sql", ".png": "image", ".jpg": "image", ".jpeg": "image",
    }.get(path.suffix.lower(), mimetypes.guess_type(path.name)[0] or "binary")


@dataclass(frozen=True)
class Source:
    name: str
    root: Path
    owner: str = "UNKNOWN"


class MotherRegistry:
    """Discover source trees and emit a referentially consistent registry set."""

    def __init__(self, sources: Iterable[Source], output: Path):
        self.sources = sorted(sources, key=lambda s: SOURCE_PRIORITY.get(s.name.lower(), 999))
        self.output = output.resolve()
        self.cache_path = self.output / ".scan-cache.json"
        self.cache = self._read_json(self.cache_path, {}).get("files", {})

    @staticmethod
    def _read_json(path: Path, default):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return default

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def _discover(self):
        records, next_cache = [], {}
        for source in self.sources:
            root = source.root.resolve()
            if not root.exists():
                raise FileNotFoundError(f"source does not exist: {root}")
            for path in sorted(root.rglob("*")):
                if not path.is_file() or self.output in path.parents or ".git" in path.parts:
                    continue
                stat = path.stat()
                key = f"{source.name}:{path}"
                fingerprint = f"{stat.st_size}:{stat.st_mtime_ns}"
                cached = self.cache.get(key, {})
                sha = cached.get("sha256") if cached.get("fingerprint") == fingerprint else self._hash(path)
                next_cache[key] = {"fingerprint": fingerprint, "sha256": sha}
                records.append((source, root, path, stat, sha))
        return records, next_cache

    def build(self) -> dict:
        discovered, next_cache = self._discover()
        grouped: dict[str, list] = {}
        for record in discovered:
            grouped.setdefault(record[4], []).append(record)
        assets, evidence = [], []
        for sha, copies in sorted(grouped.items()):
            source, root, path, stat, _ = copies[0]
            asset_id = f"mrl:{uuid.uuid5(NAMESPACE, sha)}"
            runtime = path.suffix.lower() in RUNTIME_EXTENSIONS or path.name.lower() in {"dockerfile", "makefile"}
            provenances = []
            for copy_source, copy_root, copy_path, copy_stat, _ in copies:
                evidence_id = f"evidence:{uuid.uuid5(NAMESPACE, copy_source.name + ':' + str(copy_path))}"
                relative = copy_path.relative_to(copy_root).as_posix()
                provenance = {"evidence_id": evidence_id, "asset_id": asset_id,
                              "source": copy_source.name, "original_path": relative,
                              "observed_at": _utc(copy_stat.st_mtime)}
                evidence.append(provenance)
                provenances.append(evidence_id)
            relative = path.relative_to(root).as_posix()
            assets.append({
                "asset_id": asset_id, "canonical_name": _slug(path.stem), "aliases": sorted({c[2].name for c in copies}),
                "display_name": path.name, "asset_type": _asset_type(path), "category": _category(path, runtime),
                "secondary_categories": [], "owner": source.owner, "source": source.name,
                "original_path": relative, "version": "unversioned", "hash_sha256": sha,
                "created_at": _utc(stat.st_ctime), "modified_at": _utc(stat.st_mtime), "status": "discovered",
                "parent": "ROOT", "children": [], "tags": [], "runtime_capable": runtime,
                "canonical": True, "confidence": 70, "provenance": provenances,
            })
        assets.sort(key=lambda item: item["asset_id"])
        lineage = self._lineage(assets)
        result = self._registries(assets, evidence, lineage)
        self._validate(result)
        self.output.mkdir(parents=True, exist_ok=True)
        for name, payload in result.items():
            self._write_json(self.output / f"{name}.json", payload)
        self._write_json(self.cache_path, {"schema_version": "1.0", "files": next_cache})
        self._reports(result)
        return result

    @staticmethod
    def _lineage(assets):
        by_name: dict[str, list] = {}
        for asset in assets:
            by_name.setdefault(asset["canonical_name"], []).append(asset)
        edges = []
        for versions in by_name.values():
            versions.sort(key=lambda item: (item["modified_at"], item["asset_id"]))
            for before, after in zip(versions, versions[1:]):
                if before["asset_id"] != after["asset_id"]:
                    edges.append({"from": before["asset_id"], "relationship": "evolved_into", "to": after["asset_id"]})
        return edges

    def _registries(self, assets, evidence, lineage):
        edges = [{"from": edge["from"], "relationship": edge["relationship"], "to": edge["to"]} for edge in lineage]
        runtime = [a["asset_id"] for a in assets if a["runtime_capable"]]
        archived = [a["asset_id"] for a in assets if Path(a["display_name"]).suffix.lower() in ARCHIVE_EXTENSIONS]
        base = {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
        result = {name: {**base, "items": []} for name in REGISTRY_NAMES}
        result["assets"]["items"] = assets
        result["knowledge_graph"]["nodes"] = [a["asset_id"] for a in assets]
        result["knowledge_graph"]["edges"] = edges
        result["dependency_graph"]["nodes"] = [a["asset_id"] for a in assets]
        result["dependency_graph"]["edges"] = []
        result["runtime_registry"]["items"] = [{"asset_id": item, "state": "unknown"} for item in runtime]
        result["service_registry"]["items"] = [{"asset_id": item, "buildable": "unknown", "runnable": "unknown", "deployable": "unknown"} for item in runtime]
        result["lineage_registry"]["items"] = lineage
        result["evidence_registry"]["items"] = sorted(evidence, key=lambda item: item["evidence_id"])
        result["archive_registry"]["items"] = [{"asset_id": item} for item in archived]
        result["metadata_registry"]["items"] = [{"asset_id": a["asset_id"], "confidence": a["confidence"]} for a in assets]
        return result

    @staticmethod
    def _validate(result):
        assets = result["assets"]["items"]
        ids = {a["asset_id"] for a in assets}
        if len(ids) != len(assets):
            raise ValueError("duplicate canonical identities")
        required = {"asset_id", "hash_sha256", "source", "version", "owner", "status", "category"}
        for asset in assets:
            if required - asset.keys() or asset["parent"] not in {"ROOT", *ids}:
                raise ValueError(f"invalid asset: {asset.get('asset_id')}")
        for graph in ("knowledge_graph", "dependency_graph"):
            for edge in result[graph].get("edges", []):
                if edge["from"] not in ids or edge["to"] not in ids:
                    raise ValueError(f"unresolved relationship in {graph}")
        if any(item["asset_id"] not in ids for item in result["evidence_registry"]["items"]):
            raise ValueError("unresolved evidence")

    @staticmethod
    def _write_json(path: Path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _reports(self, result):
        report_dir = self.output / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        assets = result["assets"]["items"]
        runtime_count = len(result["runtime_registry"]["items"])
        summary = (f"Assets: **{len(assets)}**  \nRuntime candidates: **{runtime_count}**  \n"
                   f"Evidence records: **{len(result['evidence_registry']['items'])}**\n")
        for name in REPORT_NAMES:
            title = name.replace("-", " ").title()
            (report_dir / f"{name}.md").write_text(
                f"# MRL {title}\n\nGenerated from the canonical machine-readable registries.\n\n{summary}", encoding="utf-8")


def _source(value: str) -> Source:
    try:
        name, path = value.split("=", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("source must be NAME=PATH") from exc
    return Source(name.strip().lower(), Path(path).expanduser())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build the MRL Mother Registry")
    parser.add_argument("--source", action="append", type=_source, required=True, help="NAME=PATH (repeatable)")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = MotherRegistry(args.source, args.output).build()
    print(f"MRL Mother Registry: {len(result['assets']['items'])} canonical assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
