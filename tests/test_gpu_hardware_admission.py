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


if __name__ == '__main__':
    unittest.main()
