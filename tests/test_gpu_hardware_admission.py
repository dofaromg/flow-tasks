"""Integration tests for the existing GPU orchestrator's MRL-34 boundary."""
import importlib.util
from pathlib import Path
import sys
import copy
import json
import tempfile
import types
import unittest
from unittest.mock import patch, MagicMock

REPO = Path(__file__).resolve().parents[1]


class GPUAdmissionIntegrationTests(unittest.TestCase):
    def test_full_live_per_card_path_accepts_and_rejects_mismatch(self):
        product = REPO / 'MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1'
        sys.path.insert(0, str(product / 'tests'))
        from test_hardware_admission import fixture, write_artifacts, tested_matrix
        from MRL_Products.MRL_APIWorks_BYOH_Deployment_Product_v1.scripts import MRL_hardware_admission_v1 as gate
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            host, workload = fixture()
            paths = write_artifacts(root / 'artifacts', workload)
            workload['runner']['id'] = 'pytorch'
            workload['runner']['version'] = 'test-torch'
            host['loaded_runner'] = copy.deepcopy(workload['runner'])
            host['loaded_runtime'] = copy.deepcopy(workload['runtime_binary'])
            for i in range(1, 6):
                host['gpus'].append(dict(host['gpus'][0], id=i, uuid='GPU-test-only-' + str(i)))
            workload['gpu_ids'] = [0, 1]
            for name, value in [('host', host), ('workload', workload)]:
                (root / (name + '.json')).write_text(json.dumps(value))
            matrix = root / 'matrix.json'
            tested_matrix(host, workload, matrix)
            torch = MagicMock()
            torch.__file__ = str(root / 'artifacts/runner.bin')
            torch.__version__ = 'test-torch'
            torch.version.cuda = '12.2'
            torch.cuda.get_device_properties.return_value = types.SimpleNamespace(
                name=host['gpus'][0]['sku'], total_memory=32768 * 1024**2)
            torch.cuda.get_device_capability.return_value = (7, 0)
            with patch.dict(sys.modules, {'torch': torch, 'yaml': MagicMock()}), patch.object(gate, 'MATRIX', matrix):
                spec = importlib.util.spec_from_file_location('mrl_full_allocator', REPO/'utils/gpu_orchestrator.py')
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                allocator = mod.GPUOrchestrator.__new__(mod.GPUOrchestrator)
                allocator.num_gpus = 6
                allocator.gpu_assignments = {'engine': [0, 1]}
                allocator.config = {'load_balancing': {'enabled': False}, 'hardware_admission': {
                    'host_manifest': str(root / 'host.json'), 'workloads': {'engine': str(root / 'workload.json')},
                    'artifact_root': str(root / 'artifacts'), 'artifact_paths': {'engine': paths}}}
                live = '\n'.join(f"{i}, GPU-test-only-{i}, {host['gpus'][i]['sku']}, 539.56, 32768 MiB" for i in range(6))
                with patch.object(mod.platform, 'system', return_value='Windows'), \
                     patch.object(mod.platform, 'version', return_value=host['os']['version']), \
                     patch.object(mod.platform, 'machine', return_value=host['os']['arch']), \
                     patch.object(mod.subprocess, 'run', return_value=types.SimpleNamespace(stdout=live)) as query, \
                     patch.object(gate, 'loaded_module_paths', return_value={root/'artifacts/runtime.bin'}):
                    self.assertEqual(allocator.allocate_gpu('engine'), [0, 1])
                    allocator.set_device([0, 1])
                    torch.cuda.set_device.assert_called_once_with(0)
                    for broken in (live.replace('GPU-test-only-5', 'GPU-wrong'),
                                   live + '\n' + live.splitlines()[0], '0, malformed'):
                        query.return_value.stdout = broken
                        with self.assertRaises(mod.AdmissionError):
                            allocator.allocate_gpu('engine')
                    query.return_value.stdout = live
                    (root/'artifacts/runtime.bin').write_bytes(b'changed runtime')
                    with self.assertRaises(mod.AdmissionError):
                        allocator.allocate_gpu('engine')

    def test_allocator_blocks_missing_config_before_return(self):
        # Load real allocator with dependency stubs; no CUDA imports/side effects.
        torch = MagicMock()
        with patch.dict(sys.modules, {'torch': torch, 'yaml': MagicMock()}):
            sys.path.insert(0, str(REPO))
            spec = importlib.util.spec_from_file_location('mrl_test_allocator', REPO/'utils/gpu_orchestrator.py')
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            allocator = mod.GPUOrchestrator.__new__(mod.GPUOrchestrator)
            allocator.config = {'load_balancing': {'enabled': False}}
            allocator.gpu_assignments = {'engine': [0]}
            with self.assertRaises(ValueError):
                allocator.allocate_gpu('engine')

    def test_final_balanced_allocation_is_gated(self):
        with patch.dict(sys.modules, {'torch': MagicMock(), 'yaml': MagicMock()}):
            sys.path.insert(0, str(REPO))
            spec = importlib.util.spec_from_file_location('mrl_test_allocator2', REPO/'utils/gpu_orchestrator.py')
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            allocator = mod.GPUOrchestrator.__new__(mod.GPUOrchestrator)
            allocator.config = {'load_balancing': {'enabled': True}}
            allocator.gpu_assignments = {'engine': [0]}
            allocator._balance_load = MagicMock(return_value=[1])
            allocator._admit_workload = MagicMock(side_effect=mod.AdmissionError('blocked'))
            with self.assertRaises(ValueError):
                allocator.allocate_gpu('engine')
            allocator._admit_workload.assert_called_once_with('engine', [1])

    def test_device_selection_rechecks_current_admission(self):
        torch = MagicMock()
        with patch.dict(sys.modules, {'torch': torch, 'yaml': MagicMock()}):
            sys.path.insert(0, str(REPO))
            spec = importlib.util.spec_from_file_location('mrl_test_allocator3', REPO/'utils/gpu_orchestrator.py')
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            allocator = mod.GPUOrchestrator.__new__(mod.GPUOrchestrator)
            allocator._last_admitted_engine_name = 'engine'
            allocator._last_admitted_gpu_ids = (0,)
            allocator._admit_workload = MagicMock(side_effect=mod.AdmissionError('artifact changed'))
            with self.assertRaises(mod.AdmissionError):
                allocator.set_device([0])
            allocator._admit_workload.assert_called_once_with('engine', [0])
            torch.cuda.set_device.assert_not_called()

    def test_load_balancing_telemetry_does_not_select_an_unadmitted_gpu(self):
        torch = MagicMock()
        torch.cuda.is_available.return_value = True
        torch.cuda.get_device_properties.return_value.name = 'test GPU'
        torch.cuda.get_device_properties.return_value.total_memory = 1024**3
        with patch.dict(sys.modules, {'torch': torch, 'yaml': MagicMock()}):
            sys.path.insert(0, str(REPO))
            spec = importlib.util.spec_from_file_location('mrl_test_allocator4', REPO/'utils/gpu_orchestrator.py')
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            allocator = mod.GPUOrchestrator.__new__(mod.GPUOrchestrator)
            allocator.num_gpus = 1
            allocator.get_gpu_status(0)
            torch.cuda.set_device.assert_not_called()


if __name__ == '__main__':
    unittest.main()
