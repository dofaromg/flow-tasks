"""MRL-34 policy tests; synthetic acceptances never enter the release matrix."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import MRL_hardware_admission_v1 as gate


def fixture():
    host = {
        'schema': 'MRL_Hardware_Manifest_v1', 'origin_signature': 'MrLiouWord',
        'observation': 'current', 'os': {'family': 'windows', 'version': '10.0.17763', 'arch': 'AMD64'},
        'driver': {'vendor': 'NVIDIA', 'version': '539.56'},
        'gpus': [{'id': 0, 'vendor': 'NVIDIA', 'architecture': 'Volta', 'sku': 'Tesla V100-SXM2-32GB',
                  'compute_capability': '7.0', 'vram_mib': 32768}],
    }
    workload = {
        'schema': 'MRL_Workload_Manifest_v1', 'origin_signature': 'MrLiouWord',
        'bundle_id': 'MRL_APIWorks_BYOH_DL580_V100_CUDA12_v1',
        'bundle_digest': 'sha256:' + '1' * 64, 'os': copy.deepcopy(host['os']),
        'cuda_runtime': '12.2', 'runtime_abi': 'cuda-12', 'toolkit': '12.2',
        'runner': {'id': 'llama.cpp', 'version': 'synthetic-test-build', 'digest': 'sha256:' + '2' * 64},
        'model': {'id': 'synthetic-model', 'version': 'test-only', 'digest': 'sha256:' + '3' * 64},
        'quantization': 'fp16', 'image': {'id': 'native', 'cuda_major': 0},
    }
    return host, workload


def tested_matrix(host, workload):
    matrix = gate.load_matrix()
    matrix['acceptances'] = [{
        'bundle_id': workload['bundle_id'],
        'configuration_digest': gate.digest({'host': host, 'workload': workload}),
        'status': 'passed', 'evidence_kind': 'real_hardware_smoke_and_restart',
        'source_commit': 'a' * 40, 'evidence_digest': 'sha256:' + '4' * 64,
        'evidence_ref': 'test-fixture://synthetic-not-production',
    }]
    return matrix


class HardwareAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.h, self.w = fixture()

    def check_status(self, status, reason=None, matrix=None):
        result = gate.evaluate(self.h, self.w, matrix)
        self.assertEqual(result['status'], status, result)
        self.assertEqual(result['allowed'], status == 'admitted')
        if reason:
            self.assertIn(reason, result['reasons'][0])

    def test_exact_tested_cuda12_preserved(self):
        self.check_status('admitted', matrix=tested_matrix(self.h, self.w))

    def test_release_catalog_does_not_invent_acceptance(self):
        self.assertEqual(gate.load_matrix()['acceptances'], [])
        self.check_status('unknown', 'NO_EXACT_HARDWARE_ACCEPTANCE')

    def test_cuda13_runtime_toolkit_image_rejected(self):
        for field in ('runtime', 'toolkit', 'image'):
            with self.subTest(field=field):
                self.h, self.w = fixture()
                if field == 'runtime':
                    self.w.update(cuda_runtime='13.0', runtime_abi='cuda-13')
                elif field == 'toolkit':
                    self.w['toolkit'] = '13.0'
                else:
                    self.w['image'] = {'id': 'vllm-omni@sha256:' + '5'*64, 'cuda_major': 13}
                self.check_status('rejected', 'VOLTA_REQUIRES_CUDA12', tested_matrix(self.h, self.w))

    def test_tensorrt_rtx_blocked(self):
        for name in ('tensorrt-rtx', 'TensorRT_RTX', 'NVIDIA TensorRT for RTX'):
            with self.subTest(runner=name):
                self.w['runner']['id'] = name
                self.check_status('rejected', 'TENSORRT_RTX')

    def test_tensorrt_volta_removal(self):
        self.w['runner'].update(id='tensorrt', version='10.5.0')
        self.check_status('rejected', 'TENSORRT_VERSION')

    def test_driver_floor_is_os_specific(self):
        for family, driver in [('windows', '527.99'), ('linux', '525.60.12')]:
            self.h['os']['family'] = family
            self.w['os'] = copy.deepcopy(self.h['os'])
            self.h['driver']['version'] = driver
            self.check_status('rejected', 'DRIVER_BELOW')

    def test_r580_not_confused_with_cuda13(self):
        self.h['driver']['version'] = '580.99'
        self.check_status('admitted', matrix=tested_matrix(self.h, self.w))

    def test_new_driver_not_automatically_tested(self):
        matrix = tested_matrix(self.h, self.w)
        self.h['driver']['version'] = '580.99'
        self.check_status('unknown', matrix=matrix)

    def test_after_r580_volta_driver_rejected(self):
        self.h['driver']['version'] = '590.10'
        self.check_status('rejected', 'LAST_SUPPORTED_BRANCH')

    def test_missing_and_malformed_fields_fail_closed(self):
        for obj, key in [('host', 'gpus'), ('host', 'driver'), ('workload', 'runner'),
                         ('workload', 'bundle_digest'), ('workload', 'runtime_abi')]:
            self.h, self.w = fixture()
            del (self.h if obj == 'host' else self.w)[key]
            self.check_status('unknown')
        self.h, self.w = fixture()
        self.h['driver']['version'] = 'R535'
        self.check_status('unknown')

    def test_historical_snapshot_not_live(self):
        self.h['observation'] = 'historical'
        self.check_status('unknown', 'HISTORICAL', tested_matrix(self.h, self.w))

    def test_unpinned_image_blocked(self):
        self.w['image'] = {'id': 'vllm-omni:latest', 'cuda_major': 12}
        self.check_status('unknown', 'digest pinned')

    def test_changed_exact_inputs_invalidate_acceptance(self):
        for field in ('bundle_digest', 'quantization', 'model', 'runner', 'os'):
            self.h, self.w = fixture()
            matrix = tested_matrix(self.h, self.w)
            if field in ('model', 'runner'):
                self.w[field]['digest'] = 'sha256:' + 'f'*64
            elif field == 'os':
                self.h['os']['version'] = 'changed'
                self.w['os'] = copy.deepcopy(self.h['os'])
            else:
                self.w[field] = 'sha256:' + 'f'*64 if field == 'bundle_digest' else 'int8'
            self.check_status('unknown', matrix=matrix)

    def test_wrong_route_cannot_accept_v100(self):
        self.w['bundle_id'] = 'MRL_APIWorks_BYOH_Modern_NVIDIA_CUDA12_v1'
        self.check_status('rejected', 'HARDWARE_ROUTE')

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
        self.h, self.w = fixture()
        self.h['gpus'].append(dict(self.h['gpus'][0]))
        self.check_status('unknown', 'duplicate')

    def test_evidence_required_even_for_pass_label(self):
        for key, value in [('evidence_digest', ''), ('source_commit', ''),
                           ('evidence_kind', 'unit_test'), ('evidence_ref', '')]:
            matrix = tested_matrix(self.h, self.w)
            matrix['acceptances'][0][key] = value
            self.check_status('unknown', matrix=matrix)

    def test_cli_missing_input_nonzero(self):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/MRL_hardware_admission_v1.py'),
                                 '--host', '/nonexistent', '--workload', '/nonexistent'], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stdout)['allowed'])



if __name__ == '__main__':
    unittest.main()
