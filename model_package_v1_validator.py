#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Package v1 Validator (package_version=1.0.0)

Validates a Model Package delivered as:
  - a directory: <package_id>/...
  - a zip file:  <package_id>.zip  (containing root folder <package_id>/...)

Validation focus:
  - Structural completeness
  - Required files exist
  - JSON files parse
  - manifest.artifacts sha256 & bytes match actual files
  - primary paths exist and are listed in artifacts

Exit codes:
  0: VALID
  2: INVALID
  3: ERROR (unexpected)
"""

from __future__ import annotations
import argparse
import hashlib
import json
import sys
import textwrap
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


REQUIRED_PATHS = [
    "manifest.json",
    "preview/model.glb",
    "preview/thumbnail.png",
    "report/quality.json",
    "report/pipeline.json",
    "meta/source.json",
]

REQUIRED_MANIFEST_PRIMARY_KEYS = ["preview_glb", "thumbnail", "quality_report"]
REQUIRED_MANIFEST_ARTIFACT_NAMES = ["preview_glb", "thumbnail", "quality_report", "pipeline_report", "source_meta"]
PACKAGE_VERSION = "1.0.0"


@dataclass
class Finding:
    level: str   # "ERROR" or "WARN"
    code: str
    message: str
    path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"level": self.level, "code": self.code, "message": self.message}
        if self.path:
            d["path"] = self.path
        return d


def sha256_file(p: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_json(p: Path) -> Tuple[Optional[dict], Optional[str]]:
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, str(e)


def is_zip(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".zip"


def ensure_extracted(input_path: Path, out_dir: Path) -> Tuple[Path, bool, List[Finding]]:
    findings: List[Finding] = []
    if input_path.is_dir():
        return input_path, False, findings

    if not is_zip(input_path):
        findings.append(Finding("ERROR", "INPUT_NOT_DIR_OR_ZIP",
                                "Input must be a directory or a .zip file.", str(input_path)))
        return input_path, False, findings

    try:
        with zipfile.ZipFile(input_path, "r") as z:
            z.extractall(out_dir)
    except Exception as e:
        findings.append(Finding("ERROR", "ZIP_EXTRACT_FAILED", f"Failed to extract zip: {e}", str(input_path)))
        return input_path, False, findings

    # Determine root folder: prefer single top-level directory; else out_dir itself.
    top = [p for p in out_dir.iterdir()]
    if len(top) == 1 and top[0].is_dir():
        return top[0], True, findings
    return out_dir, True, findings


def validate_manifest(manifest: dict, root: Path, findings: List[Finding]) -> Optional[dict]:
    if not isinstance(manifest, dict):
        findings.append(Finding("ERROR", "MANIFEST_NOT_OBJECT", "manifest.json must be a JSON object.", "manifest.json"))
        return None

    # package_version
    pv = manifest.get("package_version")
    if pv != PACKAGE_VERSION:
        findings.append(Finding("ERROR", "BAD_PACKAGE_VERSION",
                                f"package_version must be '{PACKAGE_VERSION}', got '{pv}'.", "manifest.json"))

    # required top keys (minimal)
    for k in ["package_id", "scan_id", "job_id", "model_revision", "created_at", "completed_at",
              "source_type", "device", "coordinate_system", "artifacts", "primary"]:
        if k not in manifest:
            findings.append(Finding("ERROR", "MANIFEST_MISSING_KEY", f"Missing required key: {k}", "manifest.json"))

    # primary
    primary = manifest.get("primary", {})
    if not isinstance(primary, dict):
        findings.append(Finding("ERROR", "PRIMARY_NOT_OBJECT", "primary must be an object.", "manifest.json"))
        primary = {}
    for k in REQUIRED_MANIFEST_PRIMARY_KEYS:
        if k not in primary:
            findings.append(Finding("ERROR", "PRIMARY_MISSING_KEY", f"primary missing key: {k}", "manifest.json"))

    # artifacts list
    artifacts = manifest.get("artifacts", [])
    if not isinstance(artifacts, list) or not artifacts:
        findings.append(Finding("ERROR", "ARTIFACTS_EMPTY", "artifacts must be a non-empty array.", "manifest.json"))
        return None

    # build artifact index by path and by name
    by_path: Dict[str, dict] = {}
    by_name: Dict[str, dict] = {}
    for idx, a in enumerate(artifacts):
        if not isinstance(a, dict):
            findings.append(Finding("ERROR", "ARTIFACT_NOT_OBJECT", f"artifact[{idx}] must be an object.", "manifest.json"))
            continue
        for k in ["name", "path", "mime", "sha256", "bytes"]:
            if k not in a:
                findings.append(Finding("ERROR", "ARTIFACT_MISSING_KEY",
                                        f"artifact[{idx}] missing key: {k}", "manifest.json"))
        name = a.get("name")
        path = a.get("path")
        if isinstance(path, str):
            by_path[path] = a
        if isinstance(name, str):
            by_name[name] = a

    # Ensure required artifact names exist (soft requirement but recommended)
    for nm in REQUIRED_MANIFEST_ARTIFACT_NAMES:
        if nm not in by_name:
            findings.append(Finding("WARN", "MISSING_RECOMMENDED_ARTIFACT_NAME",
                                    f"Recommended artifact name not found in artifacts: {nm}", "manifest.json"))

    # primary paths must exist in artifacts + in filesystem
    for k in REQUIRED_MANIFEST_PRIMARY_KEYS:
        pth = primary.get(k)
        if not isinstance(pth, str) or not pth:
            continue
        if pth not in by_path:
            findings.append(Finding("ERROR", "PRIMARY_NOT_IN_ARTIFACTS",
                                    f"primary.{k} points to '{pth}' but it's not listed in artifacts.", "manifest.json"))
        f = (root / pth)
        if not f.exists():
            findings.append(Finding("ERROR", "PRIMARY_FILE_MISSING",
                                    f"primary.{k} points to '{pth}' but file is missing.", pth))

    return {"by_path": by_path, "by_name": by_name}


def validate_required_files(root: Path, findings: List[Finding]) -> None:
    for rel in REQUIRED_PATHS:
        p = root / rel
        if not p.exists():
            findings.append(Finding("ERROR", "REQUIRED_FILE_MISSING", "Required file missing.", rel))
        elif p.is_dir():
            findings.append(Finding("ERROR", "REQUIRED_PATH_IS_DIR", "Required path is a directory, expected file.", rel))
        elif p.stat().st_size <= 0:
            # glb could be small but not zero; same for json/png
            findings.append(Finding("ERROR", "REQUIRED_FILE_EMPTY", "Required file is empty (0 bytes).", rel))


def validate_json_files(root: Path, findings: List[Finding]) -> None:
    for rel in ["manifest.json", "report/quality.json", "report/pipeline.json", "meta/source.json"]:
        p = root / rel
        if not p.exists() or p.is_dir():
            continue
        obj, err = load_json(p)
        if err:
            findings.append(Finding("ERROR", "JSON_PARSE_FAILED", f"JSON parse failed: {err}", rel))
            continue

        # Minimal semantic checks
        if rel == "report/pipeline.json":
            status = obj.get("status")
            stages = obj.get("stages", [])
            if status == "completed":
                if not stages or not isinstance(stages, list):
                    findings.append(Finding("ERROR", "PIPELINE_STAGES_INVALID", "stages must be a non-empty array.", rel))
                else:
                    last = stages[-1]
                    if isinstance(last, dict):
                        if last.get("name") != "validate" or last.get("ok") is not True:
                            findings.append(Finding("ERROR", "PIPELINE_VALIDATE_NOT_OK",
                                                    "For status=completed, last stage must be name='validate' and ok=true.", rel))
            if status == "failed":
                notes = obj.get("notes", [])
                if not notes:
                    findings.append(Finding("ERROR", "PIPELINE_MISSING_NOTES",
                                            "For status=failed, notes must contain failure details.", rel))

        if rel == "report/quality.json":
            if "overall_score" not in obj or "pass" not in obj:
                findings.append(Finding("ERROR", "QUALITY_MISSING_FIELDS", "quality.json missing required fields.", rel))


def validate_artifact_hashes(root: Path, manifest: dict, findings: List[Finding]) -> None:
    artifacts = manifest.get("artifacts", [])
    if not isinstance(artifacts, list):
        return

    for a in artifacts:
        if not isinstance(a, dict):
            continue
        rel = a.get("path")
        exp_sha = a.get("sha256")
        exp_bytes = a.get("bytes")
        if not isinstance(rel, str) or not rel:
            continue
        p = root / rel
        if not p.exists() or p.is_dir():
            findings.append(Finding("ERROR", "ARTIFACT_FILE_MISSING", "Artifact listed in manifest missing on disk.", rel))
            continue

        actual_bytes = p.stat().st_size
        if isinstance(exp_bytes, int) and exp_bytes != actual_bytes:
            findings.append(Finding("ERROR", "ARTIFACT_BYTES_MISMATCH",
                                    f"Bytes mismatch: manifest={exp_bytes}, actual={actual_bytes}", rel))

        if isinstance(exp_sha, str) and len(exp_sha) == 64:
            actual_sha = sha256_file(p)
            if exp_sha.lower() != actual_sha.lower():
                findings.append(Finding("ERROR", "ARTIFACT_SHA256_MISMATCH",
                                        f"SHA256 mismatch: manifest={exp_sha}, actual={actual_sha}", rel))
        else:
            findings.append(Finding("ERROR", "ARTIFACT_SHA256_INVALID",
                                    "Invalid sha256 in manifest (must be 64 hex chars).", rel))


def validate_lidar_constraints(root: Path, source: dict, findings: List[Finding]) -> None:
    st = source.get("source_type")
    inputs = source.get("inputs", {})
    if st == "LIDAR_SCAN" and isinstance(inputs, dict):
        has_depth = inputs.get("has_depth") is True
        has_pc = inputs.get("has_pointcloud") is True
        has_frames = inputs.get("has_arkit_frames") is True
        if not (has_depth or has_pc or has_frames):
            findings.append(Finding("ERROR", "LIDAR_INPUTS_INCOMPLETE",
                                    "LIDAR_SCAN requires at least one of has_depth / has_pointcloud / has_arkit_frames = true.",
                                    "meta/source.json"))


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="model_package_v1_validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            Validate a Model Package v1 (directory or zip).

            Examples:
              python model_package_v1_validator.py /path/to/job_123.zip
              python model_package_v1_validator.py /path/to/job_123/ --json
        """)
    )
    ap.add_argument("input", help="Path to a package directory or .zip")
    ap.add_argument("--workdir", default=".mpv1_tmp", help="Temp directory for zip extraction (default: .mpv1_tmp)")
    ap.add_argument("--json", action="store_true", help="Output findings as JSON")
    args = ap.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    workdir = Path(args.workdir).expanduser().resolve()
    findings: List[Finding] = []

    # Prepare root
    root = input_path
    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        # clean workdir
        try:
            if workdir.exists():
                # best effort cleanup
                for p in sorted(workdir.rglob("*"), reverse=True):
                    try:
                        if p.is_file() or p.is_symlink():
                            p.unlink()
                        elif p.is_dir():
                            p.rmdir()
                    except Exception:
                        # Best-effort cleanup: ignore errors when removing temp artifacts.
                        pass
                    except Exception as cleanup_error:
                        # Best-effort cleanup: log and ignore errors when removing temp artifacts.
                        sys.stderr.write(f"[WARN] Failed to remove {p}: {cleanup_error}\n")
            workdir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            findings.append(Finding("ERROR", "WORKDIR_PREP_FAILED", f"Failed to prepare workdir: {e}", str(workdir)))
            return report(findings, json_out=args.json)

        root, _extracted, f2 = ensure_extracted(input_path, workdir)
        findings.extend(f2)

    if not root.exists() or not root.is_dir():
        findings.append(Finding("ERROR", "ROOT_NOT_DIR", "Resolved package root is not a directory.", str(root)))
        return report(findings, json_out=args.json)

    # Validate required files
    validate_required_files(root, findings)

    # Parse JSON (manifest + others)
    manifest_path = root / "manifest.json"
    manifest, err = load_json(manifest_path) if manifest_path.exists() else (None, "missing")
    if err:
        findings.append(Finding("ERROR", "MANIFEST_PARSE_FAILED", f"manifest.json parse failed: {err}", "manifest.json"))
        return report(findings, json_out=args.json)

    idx = validate_manifest(manifest, root, findings)
    if idx is None:
        return report(findings, json_out=args.json)

    validate_json_files(root, findings)

    # Validate artifact hashes & sizes
    validate_artifact_hashes(root, manifest, findings)

    # Source-specific constraints
    source_path = root / "meta/source.json"
    source, serr = load_json(source_path) if source_path.exists() else (None, "missing")
    if serr:
        findings.append(Finding("ERROR", "SOURCE_PARSE_FAILED", f"source.json parse failed: {serr}", "meta/source.json"))
    else:
        validate_lidar_constraints(root, source, findings)

    return report(findings, json_out=args.json)


def report(findings: List[Finding], json_out: bool) -> int:
    has_error = any(f.level == "ERROR" for f in findings)
    status = "VALID" if not has_error else "INVALID"

    if json_out:
        out = {
            "status": status,
            "findings": [f.to_dict() for f in findings]
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(status)
        if findings:
            for f in findings:
                p = f" [{f.path}]" if f.path else ""
                print(f"- {f.level} {f.code}{p}: {f.message}")

    return 0 if status == "VALID" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print("ERROR", "UNEXPECTED_EXCEPTION", str(e))
        sys.exit(3)
