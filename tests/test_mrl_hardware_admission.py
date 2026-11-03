"""Synthetic policy tests, never DL580 hardware evidence. MrLiouWord."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from utils.mrl_hardware_admission import admit, load_matrix, DEFAULT_MATRIX, FIELDS

ROOT = Path(__file__).resolve().parents[1]


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'matrix.json'
        self.manifest = dict(zip(FIELDS, [
            'NVIDIA', 'Volta', 'V100-SXM2-32GB', '7.0', 32768, '539.56',
            'Windows Server 2019', 'synthetic-runtime', '1.0', 'synthetic-abi',
            '12.2', None, 'fp16', 'synthetic-runner', '1.0', 'sha256:' + 'a'*64,
            'dl580-v100', 'MRL_TEST_ONLY_V100', 'sha256:' + 'b'*64]))
        self.matrix = {'schema_version': 'MRL.hardware_matrix/v1',
                       'origin_signature': 'MrLiouWord', 'verified_combinations': []}
        self.add_verified(self.manifest, 'TEST_ONLY_ACCEPTANCE')
        self.save()

    def add_verified(self, manifest, name):
        receipt = {'origin_signature': 'MrLiouWord', 'status': 'hardware_verified',
                   'manifest': copy.deepcopy(manifest), 'acceptance_id': name,
                   'observed_at': 'TEST_ONLY', 'source': 'SYNTHETIC_UNIT_TEST_NOT_HARDWARE',
                   'checks': dict.fromkeys(('device_query', 'runtime_smoke', 'model_smoke'), True)}
        raw = json.dumps(receipt).encode()
        filename = name + '.json'
        (self.path.parent / filename).write_bytes(raw)
        self.matrix['verified_combinations'].append({
            'manifest': copy.deepcopy(manifest), 'acceptance': {
                'path': filename, 'digest': 'sha256:' + hashlib.sha256(raw).hexdigest(), 'id': name}})

    def save(self):
        self.path.write_text(json.dumps(self.matrix))

    def test_verified_cuda12_exact_match(self):
        self.assertTrue(admit(self.manifest, self.path)['admitted'])

    def test_cuda13_and_other_majors_deny(self):
        for version in ('13.0', '13.1', '14.0', '11.8'):
            with self.subTest(version=version):
                self.assertEqual(admit(dict(self.manifest, cuda=version), self.path)['reason'],
                                 'V100_REQUIRES_VERIFIED_CUDA_12')

    def test_every_field_mismatch_denies(self):
        for key in FIELDS:
            value = self.manifest[key]
            changed = 16384 if key == 'vram_mib' else ('12.3' if key == 'cuda' else 'different')
            with self.subTest(key=key):
                self.assertFalse(admit(dict(self.manifest, **{key: changed}), self.path)['admitted'])

    def test_each_missing_field_denies(self):
        for key in FIELDS:
            manifest = self.manifest.copy()
            del manifest[key]
            with self.subTest(key=key):
                self.assertFalse(admit(manifest, self.path)['admitted'])

    def test_malformed_inputs_deny(self):
        for manifest in (None, [], {}, dict(self.manifest, vram_mib=True),
                         dict(self.manifest, cuda='13garbage'), dict(self.manifest, driver='unknown'),
                         dict(self.manifest, runtime_abi=None), dict(self.manifest, extra='x')):
            with self.subTest(manifest=manifest):
                self.assertFalse(admit(manifest, self.path)['admitted'])

    def test_v100_identity_cannot_be_bypassed(self):
        for changes in ({'track': 'modern-gpu'}, {'architecture': 'Ampere'},
                        {'compute_capability': '8.0'}, {'model_runner': 'TensorRT RTX'},
                        {'model_runner': 'vLLM-Omni', 'cuda': '13.0'}):
            self.assertFalse(admit(dict(self.manifest, **changes), self.path)['admitted'])

    def test_missing_tampered_or_failed_receipt_denies(self):
        receipt = self.path.parent / 'TEST_ONLY_ACCEPTANCE.json'
        receipt.write_text('{}')
        self.assertFalse(admit(self.manifest, self.path)['admitted'])
        receipt.unlink()
        self.assertFalse(admit(self.manifest, self.path)['admitted'])

    def test_hash_valid_but_failed_smoke_denies(self):
        row = self.matrix['verified_combinations'][0]
        receipt = self.path.parent / row['acceptance']['path']
        content = json.loads(receipt.read_text())
        content['checks']['model_smoke'] = False
        raw = json.dumps(content).encode()
        receipt.write_bytes(raw)
        row['acceptance']['digest'] = 'sha256:' + hashlib.sha256(raw).hexdigest()
        self.save()
        self.assertFalse(admit(self.manifest, self.path)['admitted'])

    def test_invalid_registry_denies(self):
        self.path.write_text('[]')
        self.assertFalse(admit(self.manifest, self.path)['admitted'])

    def test_receipt_traversal_denies(self):
        self.matrix['verified_combinations'][0]['acceptance']['path'] = '../outside.json'
        self.save()
        self.assertFalse(admit(self.manifest, self.path)['admitted'])

    def test_modern_gpu_independent_profile(self):
        modern = dict(self.manifest, sku='A100', architecture='Ampere', compute_capability='8.0',
                      track='modern-gpu', bundle_id='MRL_TEST_ONLY_MODERN', bundle_digest='sha256:'+'c'*64)
        self.assertFalse(admit(modern, self.path)['admitted'])
        self.add_verified(modern, 'TEST_ONLY_MODERN_ACCEPTANCE')
        self.save()
        self.assertTrue(admit(modern, self.path)['admitted'])
        self.assertTrue(admit(self.manifest, self.path)['admitted'])

    def test_cross_track_identity_reuse_denies(self):
        for field in ('bundle_id', 'bundle_digest'):
            modern = dict(self.manifest, sku='A100', architecture='Ampere', compute_capability='8.0',
                          track='modern-gpu', bundle_id='MRL_TEST_ONLY_MODERN', bundle_digest='sha256:'+'c'*64)
            modern[field] = self.manifest[field]
            self.add_verified(modern, 'TEST_ONLY_COLLISION_'+field)
            self.save()
            self.assertFalse(admit(modern, self.path)['admitted'])

    def test_production_matrix_has_no_fabricated_support(self):
        matrix = load_matrix()
        self.assertEqual(matrix['verified_combinations'], [])
        self.assertEqual(matrix['public_support'], [])
        self.assertEqual(matrix['historical_observations'][0]['cuda'], '12.2')
        self.assertFalse(admit(self.manifest)['admitted'])

    def test_cli_exit_codes_and_json(self):
        manifest = self.path.parent / 'manifest.json'
        command = [sys.executable, '-m', 'utils.mrl_hardware_admission',
                   '--matrix', str(self.path), '--manifest', str(manifest)]
        for cuda, code in [('12.2', 0), ('13.0', 2), ('12.3', 2)]:
            manifest.write_text(json.dumps(dict(self.manifest, cuda=cuda)))
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, code, result.stderr)
            self.assertEqual(json.loads(result.stdout)['admitted'], code == 0)
        manifest.write_text('bad json')
        self.assertEqual(subprocess.run(command, cwd=ROOT, capture_output=True).returncode, 2)

    def test_orchestrator_enforces_all_selected_devices(self):
        # No CUDA installation or GPU initialization: isolate only external imports.
        torch = types.ModuleType('torch')
        torch.device = object
        torch.nn = types.SimpleNamespace(Module=object)
        props = types.SimpleNamespace(name='V100-SXM2-32GB', major=7, minor=0,
                                      total_memory=32768 * 1024**2)
        torch.cuda = types.SimpleNamespace(get_device_properties=lambda _: props)
        with patch.dict(sys.modules, {'torch': torch, 'yaml': types.ModuleType('yaml')}):
            spec = importlib.util.spec_from_file_location('mrl_test_orchestrator', ROOT/'utils/gpu_orchestrator.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        instance = module.GPUOrchestrator.__new__(module.GPUOrchestrator)
        instance.num_gpus = 6
        instance.gpu_assignments = {'digital_human': [0, 1]}
        devices = {0: self.manifest, 1: self.manifest}
        self.assertEqual(instance.allocate_admitted_gpu('digital_human', devices, self.path), [0, 1])
        for devices in ({0: self.manifest}, {0: self.manifest, 1: dict(self.manifest, cuda='13.0')}):
            with self.assertRaises(ValueError):
                instance.allocate_admitted_gpu('digital_human', devices, self.path)
        with self.assertRaises(ValueError):
            instance.allocate_admitted_gpu('unknown', {}, self.path)
        props.major = 8
        with self.assertRaises(ValueError):
            instance.allocate_admitted_gpu('digital_human', {0: self.manifest, 1: self.manifest}, self.path)
        props.major = 7
        other = dict(self.manifest, bundle_id='MRL_TEST_ONLY_OTHER', bundle_digest='sha256:'+'d'*64)
        self.add_verified(other, 'TEST_ONLY_OTHER')
        self.save()
        with self.assertRaises(ValueError):
            instance.allocate_admitted_gpu('digital_human', {0: self.manifest, 1: other}, self.path)
        instance.gpu_assignments['digital_human'] = [0, 9]
        with self.assertRaises(ValueError):
            instance.allocate_admitted_gpu('digital_human', {0: self.manifest, 9: self.manifest}, self.path)


if __name__ == '__main__':
    unittest.main()
