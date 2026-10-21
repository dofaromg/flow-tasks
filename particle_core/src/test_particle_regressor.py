#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for MrLioū.Particle.Mrlword.v1 - 粒子回溯器
"""

import unittest
import os
import json
from particle_regressor import ParticleRegressor


class TestParticleRegressor(unittest.TestCase):
    """Test cases for ParticleRegressor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.regressor = ParticleRegressor()
        self.test_output_dir = "test_regress_output"
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up test output directory"""
        if os.path.exists(self.test_output_dir):
            for f in os.listdir(self.test_output_dir):
                os.remove(os.path.join(self.test_output_dir, f))
            os.rmdir(self.test_output_dir)
    
    def test_particle_id(self):
        """Test particle ID follows naming convention"""
        self.assertEqual(
            self.regressor.particle_id,
            "MrLioū.Particle.Mrlword.v1"
        )
        self.assertEqual(self.regressor.version, "v1")
    
    def test_regress_state_formula(self):
        """Test regression formula: P_{k-1} = P_k / (N_{k-1} * η_{k-1})"""
        # Test case 1: P_k = 100, N = 2, eta = 0.5
        p_k = 100.0
        n = 2.0
        eta = 0.5
        expected = 100.0  # 100 / (2 * 0.5) = 100
        result = self.regressor.regress_state(p_k, n, eta)
        self.assertAlmostEqual(result, expected, places=10)
        
        # Test case 2: P_k = 48, N = 4, eta = 0.5
        p_k = 48.0
        n = 4.0
        eta = 0.5
        expected = 24.0  # 48 / (4 * 0.5) = 24
        result = self.regressor.regress_state(p_k, n, eta)
        self.assertAlmostEqual(result, expected, places=10)
    
    def test_regress_state_zero_division(self):
        """Test regression raises error for zero factors"""
        with self.assertRaises(ValueError) as context:
            self.regressor.regress_state(100.0, 0, 0.5)
        self.assertIn("N_{k-1}", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            self.regressor.regress_state(100.0, 2.0, 0)
        self.assertIn("η_{k-1}", str(context.exception))
    
    def test_growth_state_formula(self):
        """Test growth formula: P_k = P_{k-1} * N_{k-1} * η_{k-1}"""
        p_k_minus_1 = 50.0
        n = 2.0
        eta = 0.8
        expected = 80.0  # 50 * 2 * 0.8 = 80
        result = self.regressor.growth_state(p_k_minus_1, n, eta)
        self.assertAlmostEqual(result, expected, places=10)
    
    def test_growth_regress_inverse(self):
        """Test that Growth and Regress are inverse operations"""
        initial = 42.0
        n = 3.0
        eta = 0.7
        
        # Apply Growth then Regress
        grown = self.regressor.growth_state(initial, n, eta)
        regressed = self.regressor.regress_state(grown, n, eta)
        
        self.assertAlmostEqual(initial, regressed, places=10)
    
    def test_backward_steps_order(self):
        """Test backward steps are in correct reverse order"""
        expected_backward = ["store", "recurse", "flow", "mark", "structure"]
        self.assertEqual(self.regressor.backward_steps, expected_backward)
        
        # Verify it's reverse of forward steps
        expected_forward = ["structure", "mark", "flow", "recurse", "store"]
        self.assertEqual(
            list(reversed(self.regressor.backward_steps)),
            expected_forward
        )
    
    def test_regress_logic_chain(self):
        """Test regress logic chain execution"""
        result = self.regressor.regress_logic_chain("test_data")
        
        # Should contain all backward steps
        for step in self.regressor.backward_steps:
            self.assertIn(step.upper() + "_REGRESS", result)
        
        # Should contain input data
        self.assertIn("test_data", result)
    
    def test_compress_regress_chain(self):
        """Test compression of regress chain"""
        compressed = self.regressor.compress_regress_chain()
        
        self.assertIn("REGRESS_SEED(X)", compressed)
        self.assertIn("(X)", compressed)
    
    def test_decompress_regress_chain(self):
        """Test decompression of regress chain"""
        compressed = self.regressor.compress_regress_chain()
        decompressed = self.regressor.decompress_regress_chain(compressed)
        
        self.assertEqual(decompressed, self.regressor.backward_steps)
    
    def test_trace_particle_path(self):
        """Test particle path tracing"""
        trace = self.regressor.trace_particle_path(
            states=[10.0],
            n_factors=[2.0, 3.0],
            eta_factors=[0.8, 0.9]
        )
        
        self.assertEqual(trace["particle_id"], self.regressor.particle_id)
        self.assertEqual(trace["start_value"], 10.0)
        self.assertTrue(trace["verified"])
        
        # Forward path should have n+1 entries (initial + n growth steps)
        self.assertEqual(len(trace["forward_path"]), 3)
        
        # Backward path should also have n+1 entries
        self.assertEqual(len(trace["backward_path"]), 3)
    
    def test_trace_particle_path_empty_input(self):
        """Test trace raises error for empty input"""
        with self.assertRaises(ValueError):
            self.regressor.trace_particle_path([], [2.0], [0.8])
        
        with self.assertRaises(ValueError):
            self.regressor.trace_particle_path([10.0], [], [0.8])
    
    def test_trace_particle_path_mismatched_length(self):
        """Test trace raises error for mismatched factor lengths"""
        with self.assertRaises(ValueError) as context:
            self.regressor.trace_particle_path(
                states=[10.0],
                n_factors=[2.0, 3.0],
                eta_factors=[0.8]  # Different length
            )
        self.assertIn("長度", str(context.exception))
    
    def test_simulate(self):
        """Test complete simulation"""
        simulation = self.regressor.simulate("test_input")
        
        self.assertEqual(simulation["particle_id"], self.regressor.particle_id)
        self.assertEqual(simulation["version"], "v1")
        self.assertEqual(simulation["input"], "test_input")
        self.assertEqual(simulation["backward_steps"], self.regressor.backward_steps)
        self.assertIn("REGRESS_SEED", simulation["compressed"])
        self.assertIn("timestamp", simulation)
    
    def test_backtrack_memory(self):
        """Test memory backtracking"""
        memory_state = {"data": "test", "count": 5}
        history = self.regressor.backtrack_memory(memory_state, steps_to_backtrack=3)
        
        self.assertEqual(len(history), 3)
        
        for i, entry in enumerate(history):
            self.assertEqual(entry["step"], i + 1)
            self.assertEqual(entry["operation"], "REGRESS")
            self.assertIn("from_state", entry)
            self.assertIn("to_state", entry)
            self.assertIn("timestamp", entry)
    
    def test_store_result(self):
        """Test storing execution result"""
        result = self.regressor.regress_logic_chain("test_data")
        filename = self.regressor.store_result(
            "test_data",
            result,
            output_dir=self.test_output_dir
        )
        
        self.assertTrue(os.path.exists(filename))
        self.assertIn("regress_result_", filename)
        self.assertTrue(filename.endswith(".json"))
        
        # Verify file content
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertEqual(data["particle_id"], self.regressor.particle_id)
        self.assertEqual(data["input"], "test_data")
        self.assertEqual(data["backward_chain"], self.regressor.backward_steps)
    
    def test_backward_explanations(self):
        """Test backward step explanations are defined"""
        for step in self.regressor.backward_steps:
            self.assertIn(step, self.regressor.backward_explanations)
            self.assertTrue(len(self.regressor.backward_explanations[step]) > 0)


if __name__ == '__main__':
    unittest.main()
