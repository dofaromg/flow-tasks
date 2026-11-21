"""Verify distinct route ZIP identities and exact file coverage."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class HardwareBundleTests(unittest.TestCase):
    def test_route_bundles_have_separate_digests_and_acceptance(self):
        matrix = json.loads((ROOT/'hardware/MRL_hardware_matrix_v1.json').read_text())
        digests = set()
        for route in matrix['routes']:
            identity = route['bundle_id']
            subprocess.run([sys.executable, str(ROOT/'scripts/MRL_build_product_bundle_v1.py'),
                            '--hardware-route', identity], capture_output=True, check=True)
            bundle = ROOT/'dist'/f'{identity}.zip'
            checksum = hashlib.sha256(bundle.read_bytes()).hexdigest()
            self.assertNotIn(checksum, digests)
            digests.add(checksum)
            self.assertEqual(bundle.with_suffix('.zip.sha256').read_text(), f'{checksum}  {bundle.name}\n')
            with zipfile.ZipFile(bundle) as archive:
                prefix = 'MRL_APIWorks_BYOH_Deployment_Product_v1/'
                manifest = json.loads(archive.read(prefix+'MRL_PRODUCT_BUNDLE_MANIFEST.json'))
                descriptor = json.loads(archive.read(prefix+'MRL_HARDWARE_ROUTE.json'))
                self.assertEqual(descriptor['bundle_id'], identity)
                self.assertEqual(descriptor['hardware_admission'], 'unknown')
                self.assertFalse(descriptor['runtime_binary_included'])
                self.assertEqual(descriptor['acceptance_evidence'], [])
                self.assertEqual(manifest['hardware_bundle_id'], identity)
                expected = {prefix+item['path'] for item in manifest['files']}
                self.assertEqual(set(archive.namelist()), expected|{prefix+'MRL_PRODUCT_BUNDLE_MANIFEST.json'})
                self.assertEqual(len(set(archive.namelist())), len(archive.namelist()))
                for item in manifest['files']:
                    data = archive.read(prefix+item['path'])
                    self.assertGreater(len(data), 0)
                    self.assertEqual(len(data), item['size'])
                    self.assertEqual(hashlib.sha256(data).hexdigest(), item['sha256'])

    def test_unknown_route_is_rejected(self):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/MRL_build_product_bundle_v1.py'),
                                 '--hardware-route', 'unknown'], capture_output=True)
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
