"""MRL-34 policy tests; synthetic acceptances never enter the release matrix."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
MATRIX_SOURCE = ROOT / 'hardware/MRL_hardware_matrix_v1.json'
sys.path.insert(0, str(ROOT / 'scripts'))
import MRL_hardware_admission_v1 as gate


def fixture():
    host = {
        'schema': 'MRL_Hardware_Manifest_v1', 'origin_signature': 'MrLiouWord',
        'observation': 'current', 'os': {'family': 'windows', 'version': '10.0.17763', 'arch': 'AMD64'},
        'driver': {'vendor': 'NVIDIA', 'version': '539.56'},
        'gpus': [{'id': 0, 'uuid': 'GPU-test-only-0', 'vendor': 'NVIDIA', 'architecture': 'Volta', 'sku': 'Tesla V100-SXM2-32GB',
                  'compute_capability': '7.0', 'vram_mib': 32768}],
    }
    workload = {
        'schema': 'MRL_Workload_Manifest_v1', 'origin_signature': 'MrLiouWord',
        'source_commit': 'a' * 40, 'track': 'dl580-v100', 'gpu_ids': [0],
        'bundle_id': 'MRL_APIWorks_BYOH_DL580_V100_CUDA12_v1',
        'bundle_digest': '', 'os': copy.deepcopy(host['os']),
        'cuda_runtime': '12.2', 'runtime_abi': 'cuda-12', 'toolkit': '12.2',
        'runner': {'id': 'llama.cpp', 'version': 'synthetic-test-build', 'digest': ''},
        'runtime_binary': {'id': 'cuda-runtime', 'version': '12.2', 'digest': ''},
        'model': {'id': 'synthetic-model', 'version': 'test-only', 'digest': ''},
        'quantization': 'fp16', 'image': {'id': 'native', 'cuda_major': 0},
    }
    host['loaded_runner'] = copy.deepcopy(workload['runner'])
    host['loaded_runtime'] = copy.deepcopy(workload['runtime_binary'])
    host['loaded_image'] = 'native'
    return host, workload


def write_artifacts(root, workload):
    root.mkdir(parents=True, exist_ok=True)
    paths = {'bundle': 'bundle', 'model': 'model', 'runner': 'runner.bin', 'runtime': 'runtime.bin'}
    (root / 'bundle').mkdir()
    (root / 'bundle' / 'manifest.json').write_text('{"bundle":"synthetic"}')
    (root / 'model').mkdir()
    (root / 'model' / 'weights-00001.bin').write_bytes(b'test-shard-1')
    (root / 'model' / 'weights-00002.bin').write_bytes(b'test-shard-2')
    (root / 'runner.bin').write_bytes(b'test-runner')
    (root / 'runtime.bin').write_bytes(b'test-runtime')
    workload['bundle_digest'] = gate.artifact_digest(root, paths['bundle'])
    workload['model']['digest'] = gate.artifact_digest(root, paths['model'])
    workload['runner']['digest'] = gate.artifact_digest(root, paths['runner'])
    workload['runtime_binary']['digest'] = gate.artifact_digest(root, paths['runtime'])
    return paths


def write_tested_matrix(host, workload, path):
    matrix = json.loads(gate.MATRIX.read_text(encoding='utf-8'))
    configuration_digest = gate.digest({'host': host, 'workload': workload})
    acceptance_id = 'TEST_ONLY_SYNTHETIC'
    receipt = {
        'origin_signature': 'MrLiouWord', 'status': 'hardware_verified',
        'acceptance_id': acceptance_id, 'configuration_digest': configuration_digest,
        'checks': {'device_query': True, 'runtime_smoke': True,
                   'model_smoke': True, 'restart_smoke': True},
        'source': 'SYNTHETIC_TEST_ONLY_NOT_HARDWARE',
    }
    raw = json.dumps(receipt, sort_keys=True, separators=(',', ':')).encode()
    (path.parent / 'test-receipt.json').write_bytes(raw)
    matrix['acceptances'] = [{
        'acceptance_id': acceptance_id,
        'bundle_id': workload['bundle_id'],
        'track': workload['track'],
        'configuration_digest': configuration_digest,
        'status': 'passed', 'evidence_kind': 'real_hardware_smoke_and_restart',
        'source_commit': 'a' * 40,
        'evidence_digest': 'sha256:' + hashlib.sha256(raw).hexdigest(),
        'receipt_path': 'test-receipt.json',
        'evidence_ref': 'test-fixture://synthetic-not-production',
    }]
    path.write_text(json.dumps(matrix, sort_keys=True), encoding='utf-8')


class HardwareAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.artifact_root = root / 'artifacts'
        self.matrix_path = root / 'MRL_hardware_matrix_v1.json'
        self.matrix_path.write_text(MATRIX_SOURCE.read_text(encoding='utf-8'), encoding='utf-8')
        self.matrix_patch = patch.object(gate, 'MATRIX', self.matrix_path)
        self.matrix_patch.start()
        self.addCleanup(self.matrix_patch.stop)
        self.reset_fixture()

    def reset_fixture(self):
        self.h, self.w = fixture()
        shutil.rmtree(self.artifact_root, ignore_errors=True)
        self.artifact_paths = write_artifacts(self.artifact_root, self.w)
        self.h['loaded_runner'] = copy.deepcopy(self.w['runner'])
        self.h['loaded_runtime'] = copy.deepcopy(self.w['runtime_binary'])

    def check_status(self, status, reason=None):
        result = gate.evaluate(self.h, self.w, self.artifact_root, self.artifact_paths)
        self.assertEqual(result['status'], status, result)
        self.assertEqual(result['allowed'], status == 'admitted')
        if reason:
            self.assertIn(reason, result['reasons'][0])

    def test_exact_tested_cuda12_preserved(self):
        write_tested_matrix(self.h, self.w, self.matrix_path)
        self.check_status('admitted')

    def test_release_catalog_does_not_invent_acceptance(self):
        self.assertEqual(gate.load_matrix()['acceptances'], [])
        self.check_status('unknown', 'NO_EXACT_HARDWARE_ACCEPTANCE')

    def test_artifact_bytes_and_sharded_file_set_are_verified(self):
        write_tested_matrix(self.h, self.w, self.matrix_path)
        self.check_status('admitted')
        (self.artifact_root / 'model' / 'weights-00002.bin').write_bytes(b'tampered')
        self.check_status('unknown', 'artifact bytes')

    def test_missing_and_symlinked_artifacts_fail_closed(self):
        write_tested_matrix(self.h, self.w, self.matrix_path)
        (self.artifact_root / 'runner.bin').unlink()
        self.check_status('unknown')
        try:
            self.artifact_root.joinpath('runner.bin').symlink_to(self.artifact_root / 'runtime.bin')
        except OSError:
            self.skipTest('symlink creation is unavailable')
        self.check_status('unknown')

    def test_receipt_missing_tampered_or_failed_is_not_admitted(self):
        write_tested_matrix(self.h, self.w, self.matrix_path)
        receipt = self.matrix_path.parent / 'test-receipt.json'
        receipt.write_text('{}', encoding='utf-8')
        self.check_status('unknown')
        write_tested_matrix(self.h, self.w, self.matrix_path)
        receipt.unlink()
        self.check_status('unknown')
        write_tested_matrix(self.h, self.w, self.matrix_path)
        failed = json.loads(receipt.read_text(encoding='utf-8'))
        failed['checks']['model_smoke'] = False
        raw = json.dumps(failed, sort_keys=True, separators=(',', ':')).encode()
        receipt.write_bytes(raw)
        matrix = json.loads(self.matrix_path.read_text(encoding='utf-8'))
        matrix['acceptances'][0]['evidence_digest'] = 'sha256:' + hashlib.sha256(raw).hexdigest()
        self.matrix_path.write_text(json.dumps(matrix), encoding='utf-8')
        self.check_status('unknown')

    def test_cuda13_runtime_toolkit_image_rejected(self):
        for field in ('runtime', 'toolkit', 'image'):
            with self.subTest(field=field):
                self.reset_fixture()
                if field == 'runtime':
                    self.w.update(cuda_runtime='13.0', runtime_abi='cuda-13')
                    self.h['loaded_runtime']['version'] = '13.0'
                elif field == 'toolkit':
                    self.w['toolkit'] = '13.0'
                else:
                    self.w['image'] = {'id': 'vllm-omni@sha256:' + '5'*64, 'cuda_major': 13}
                write_tested_matrix(self.h, self.w, self.matrix_path)
                self.check_status('rejected', 'VOLTA_REQUIRES_CUDA12')

    def test_tensorrt_rtx_blocked(self):
        for name in ('tensorrt-rtx', 'TensorRT_RTX', 'NVIDIA TensorRT for RTX'):
            with self.subTest(runner=name):
                self.w['runner']['id'] = name
                self.h['loaded_runner']['id'] = name
                self.check_status('rejected', 'TENSORRT_RTX')

    def test_tensorrt_volta_removal(self):
        self.w['runner'].update(id='tensorrt', version='10.5.0')
        self.h['loaded_runner'] = copy.deepcopy(self.w['runner'])
        self.check_status('rejected', 'TENSORRT_VERSION')

    def test_driver_floor_is_os_specific(self):
        for family, driver in [('windows', '527.99'), ('linux', '525.60.12')]:
            self.h['os']['family'] = family
            self.w['os'] = copy.deepcopy(self.h['os'])
            self.h['driver']['version'] = driver
            self.check_status('rejected', 'DRIVER_BELOW')

    def test_r580_not_confused_with_cuda13(self):
        self.h['driver']['version'] = '580.99'
        write_tested_matrix(self.h, self.w, self.matrix_path)
        self.check_status('admitted')

    def test_new_driver_not_automatically_tested(self):
        write_tested_matrix(self.h, self.w, self.matrix_path)
        self.h['driver']['version'] = '580.99'
        self.check_status('unknown')

    def test_after_r580_volta_driver_rejected(self):
        self.h['driver']['version'] = '590.10'
        self.check_status('rejected', 'LAST_SUPPORTED_BRANCH')

    def test_missing_and_malformed_fields_fail_closed(self):
        for obj, key in [('host', 'gpus'), ('host', 'driver'), ('workload', 'runner'),
                         ('workload', 'bundle_digest'), ('workload', 'runtime_abi')]:
            self.reset_fixture()
            del (self.h if obj == 'host' else self.w)[key]
            self.check_status('unknown')
        self.reset_fixture()
        self.h['driver']['version'] = 'R535'
        self.check_status('unknown')

    def test_historical_snapshot_not_live(self):
        self.h['observation'] = 'historical'
        write_tested_matrix(self.h, self.w, self.matrix_path)
        self.check_status('unknown', 'HISTORICAL')

    def test_unpinned_image_blocked(self):
        self.w['image'] = {'id': 'vllm-omni:latest', 'cuda_major': 12}
        self.check_status('unknown', 'digest pinned')

    def test_changed_exact_inputs_invalidate_acceptance(self):
        for field in ('bundle_digest', 'quantization', 'model', 'runner', 'os'):
            self.reset_fixture()
            write_tested_matrix(self.h, self.w, self.matrix_path)
            if field in ('model', 'runner'):
                self.w[field]['digest'] = 'sha256:' + 'f'*64
            elif field == 'os':
                self.h['os']['version'] = 'changed'
                self.w['os'] = copy.deepcopy(self.h['os'])
            else:
                self.w[field] = 'sha256:' + 'f'*64 if field == 'bundle_digest' else 'int8'
            self.check_status('unknown')

    def test_wrong_route_cannot_accept_v100(self):
        self.w['bundle_id'] = 'MRL_APIWorks_BYOH_Modern_NVIDIA_CUDA12_v1'
        self.w['track'] = 'modern-gpu'
        self.check_status('rejected', 'BUNDLE_HARDWARE_ROUTE_MISMATCH')

    def test_modern_cuda13_is_unknown(self):
        self.h['gpus'][0].update(architecture='Ada', sku='RTX 4090', compute_capability='8.9')
        self.h['driver']['version'] = '580.99'
        self.w.update(bundle_id='MRL_APIWorks_BYOH_Modern_NVIDIA_CUDA13_v1',
                      cuda_runtime='13.0', toolkit='13.0', runtime_abi='cuda-13')
        self.check_status('unknown', 'CUDA_PATH_NOT_VALIDATED')

    def test_unsupported_precision(self):
        for precision in ('bf16', 'fp8', 'fp4'):
            self.w['quantization'] = precision
            self.check_status('rejected', 'PRECISION')

    def test_v100_identity_spoof_and_mixed_inventory(self):
        self.h['gpus'][0]['compute_capability'] = '8.9'
        self.check_status('rejected', 'IDENTITY')
        self.reset_fixture()
        self.h['gpus'].append(dict(self.h['gpus'][0]))
        self.check_status('unknown', 'duplicate')

    def test_evidence_required_even_for_pass_label(self):
        for key, value in [('evidence_digest', ''), ('source_commit', ''),
                           ('evidence_kind', 'unit_test'), ('evidence_ref', '')]:
            write_tested_matrix(self.h, self.w, self.matrix_path)
            matrix = json.loads(self.matrix_path.read_text(encoding='utf-8'))
            matrix['acceptances'][0][key] = value
            self.matrix_path.write_text(json.dumps(matrix), encoding='utf-8')
            self.check_status('unknown')

    def test_cli_missing_input_nonzero(self):
        artifact_paths = Path(self.temporary.name) / 'paths.json'
        artifact_paths.write_text('{}', encoding='utf-8')
        result = subprocess.run([sys.executable, str(ROOT/'scripts/MRL_hardware_admission_v1.py'),
                                 '--host', '/nonexistent', '--workload', '/nonexistent',
                                 '--artifact-root', str(self.artifact_root),
                                 '--artifact-paths', str(artifact_paths)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stdout)['allowed'])



if __name__ == '__main__':
    unittest.main()
