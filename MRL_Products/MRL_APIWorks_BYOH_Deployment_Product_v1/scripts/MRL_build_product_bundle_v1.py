#!/usr/bin/env python3
"""Build the audited customer delivery ZIP for the MRL APIWorks BYOH product."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PRODUCT_ROOT.parents[1]
RUNTIME_ROOT = REPO_ROOT / "MRL_Mother" / "MRL_MotherModel" / "MRL_AI_Mother_Autonomous_Runtime_Baseline_v1"
DIST = PRODUCT_ROOT / "dist"
MANIFEST_NAME = "MRL_PRODUCT_BUNDLE_MANIFEST.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def files_under(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and "dist" not in path.parts
    )


def main() -> int:
    subprocess.run(
        ["python", str(RUNTIME_ROOT / "scripts" / "MRL_verify_package_v1.py")],
        cwd=RUNTIME_ROOT,
        check=True,
    )
    DIST.mkdir(parents=True, exist_ok=True)
    output = DIST / "MRL_APIWorks_BYOH_Deployment_Product_v1.zip"
    with tempfile.TemporaryDirectory() as temporary:
        stage = Path(temporary) / "MRL_APIWorks_BYOH_Deployment_Product_v1"
        runtime_target = stage / "runtime_package"
        product_target = stage / "product"
        shutil.copytree(RUNTIME_ROOT, runtime_target, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(PRODUCT_ROOT, product_target, ignore=shutil.ignore_patterns("dist", "__pycache__"))
        entries = []
        for path in files_under(stage):
            name = path.relative_to(stage).as_posix()
            entries.append({"path": name, "size": path.stat().st_size, "sha256": sha256(path)})
        manifest = {
            "schema": "MRL_Product_Bundle_Manifest_v1",
            "canonical_id": "MRL_APIWorks_BYOH_Deployment_Product_v1",
            "sku": "MRL-APIWORKS-BYOH-DEPLOY-V1",
            "origin_signature": "MrLiouWord",
            "files": entries,
        }
        (stage / MANIFEST_NAME).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in files_under(stage):
                archive.write(path, path.relative_to(stage).as_posix())
    print(json.dumps({"delivery_gate": "PRODUCT_BUNDLE_DELIVERY_PASS", "path": str(output), "sha256": sha256(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

