#!/usr/bin/env python3
"""Product packaging acceptance tests."""

from __future__ import annotations

import json
import subprocess
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProductBundleTests(unittest.TestCase):
    def test_builds_complete_customer_zip(self) -> None:
        subprocess.run(["python", "scripts/MRL_build_product_bundle_v1.py"], cwd=ROOT, check=True)
        bundle = ROOT / "dist" / "MRL_APIWorks_BYOH_Deployment_Product_v1.zip"
        self.assertTrue(bundle.is_file())
        with zipfile.ZipFile(bundle) as archive:
            names = set(archive.namelist())
            self.assertIn("MRL_PRODUCT_BUNDLE_MANIFEST.json", names)
            manifest = json.loads(archive.read("MRL_PRODUCT_BUNDLE_MANIFEST.json"))
            expected = {item["path"] for item in manifest["files"]}
            self.assertEqual(names - {"MRL_PRODUCT_BUNDLE_MANIFEST.json"}, expected)
            self.assertTrue(any(name.endswith("runtime/MRL_apiworks_gateway_v1.py") for name in expected))
            self.assertEqual(manifest["origin_signature"], "MrLiouWord")


if __name__ == "__main__":
    unittest.main()

