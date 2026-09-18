#!/usr/bin/env python3
"""Product packaging acceptance tests."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT_NAME = "MRL_APIWorks_BYOH_Deployment_Product_v1"
RUNTIME_RELATIVE = Path(
    "MRL_Mother/MRL_MotherModel/MRL_AI_Mother_Autonomous_Runtime_Baseline_v1"
)
PRODUCT_RELATIVE = Path("MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1")
MUTABLE_CONFIG = Path("customer_config/MRL_runtime.local.json")


class ProductBundleTests(unittest.TestCase):
    def test_builds_runnable_customer_zip(self) -> None:
        """Exercise extraction, mutable configuration, and both package verifiers."""
        subprocess.run(["python", "scripts/MRL_build_product_bundle_v1.py"], cwd=ROOT, check=True)
        bundle = ROOT / "dist" / f"{BUNDLE_ROOT_NAME}.zip"
        self.assertTrue(bundle.is_file())
        with tempfile.TemporaryDirectory() as temporary:
            extraction_root = Path(temporary)
            with zipfile.ZipFile(bundle) as archive:
                names = set(archive.namelist())
                prefix = f"{BUNDLE_ROOT_NAME}/"
                self.assertTrue(names)
                self.assertTrue(all(name.startswith(prefix) for name in names))
                archive.extractall(extraction_root)

            delivery_root = extraction_root / BUNDLE_ROOT_NAME
            manifest = json.loads((delivery_root / "MRL_PRODUCT_BUNDLE_MANIFEST.json").read_text(encoding="utf-8"))
            expected = {f"{prefix}{item['path']}" for item in manifest["files"]}
            self.assertEqual(names - {f"{prefix}MRL_PRODUCT_BUNDLE_MANIFEST.json"}, expected)
            self.assertEqual(manifest["archive_root"], BUNDLE_ROOT_NAME)
            self.assertEqual(manifest["mutable_after_extraction"], [MUTABLE_CONFIG.as_posix()])
            mutable_entry = next(item for item in manifest["files"] if item["path"] == MUTABLE_CONFIG.as_posix())
            self.assertTrue(mutable_entry["mutable_after_extraction"])

            runtime_root = delivery_root / RUNTIME_RELATIVE
            product_root = delivery_root / PRODUCT_RELATIVE
            self.assertTrue((runtime_root / "runtime" / "MRL_apiworks_gateway_v1.py").is_file())
            self.assertTrue((product_root / "scripts" / "MRL_build_product_bundle_v1.py").is_file())

            customer_config = delivery_root / MUTABLE_CONFIG
            config = json.loads(customer_config.read_text(encoding="utf-8"))
            config["local_model"]["model"] = "customer-owned-model"
            customer_config.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            subprocess.run(["python", "scripts/MRL_verify_package_v1.py"], cwd=runtime_root, check=True)
            subprocess.run(["python", "scripts/MRL_verify_product_source_v1.py"], cwd=product_root, check=True)

            config_from_start_script = (
                runtime_root / "scripts" / ".." / ".." / ".." / ".." / MUTABLE_CONFIG
            ).resolve()
            self.assertEqual(config_from_start_script, customer_config.resolve())

            acceptance = (product_root / "docs" / "MRL_DELIVERY_ACCEPTANCE_v1.md").read_text(encoding="utf-8")
            self.assertIn("-ConfigPath", acceptance)
            self.assertIn(r"..\..\..\..\customer_config\MRL_runtime.local.json", acceptance)
            self.assertIn("-ModelArtifactPath", acceptance)
            self.assertIn("-ModelReleaseManifestPath", acceptance)
            self.assertIn("-ExternalModelDisconnected", acceptance)
            self.assertIn("-ReceiptPath", acceptance)
            self.assertEqual(manifest["origin_signature"], "MrLiouWord")


if __name__ == "__main__":
    unittest.main()
