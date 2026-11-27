"""Integration tests for the existing GPU orchestrator's MRL-34 boundary."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, MagicMock

REPO = Path(__file__).resolve().parents[1]


class GPUAdmissionIntegrationTests(unittest.TestCase):
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
