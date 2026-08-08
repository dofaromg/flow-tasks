#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for MrLioū.Particle.EnvParameters.v1 - 粒子環境參數與創世公式
"""

import unittest
import os
import json
from particle_env_parameters import ParticleEnvParameters


class TestParticleEnvParameters(unittest.TestCase):
    """Test cases for ParticleEnvParameters class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = ParticleEnvParameters()
        
    def test_particle_id(self):
        """Test particle ID and versioning"""
        self.assertEqual(self.manager.version, "v1.0.0")
        self.assertEqual(self.manager.particle_id, "MrLioū.Particle.EnvParameters.v1.0.0")

    def test_default_parameters(self):
        """Test default values of the parameters are initialized correctly"""
        self.assertEqual(self.manager.context_weight, 0.4)
        self.assertEqual(self.manager.runtime_weight, 0.3)
        self.assertEqual(self.manager.dependency_weight, 0.2)
        self.assertEqual(self.manager.external_noise, 0.1)
        self.assertEqual(self.manager.trust_score, 0.9)
        self.assertEqual(self.manager.scale_mode, "linear")

    def test_calculate_eta(self):
        """Test eta calculation formula and clipping boundaries"""
        # Ideal scenario: context=1.0, runtime=1.0, dependency=1.0
        # eta = (1.0*0.4 + 1.0*0.3 + 1.0*0.2) * (1 - 0.1) * 0.9
        #     = 0.9 * 0.9 * 0.9 = 0.729
        eta_ideal = self.manager.calculate_eta(1.0, 1.0, 1.0)
        self.assertAlmostEqual(eta_ideal, 0.729, places=6)
        
        # Lower/Upper boundaries checking: negative inputs or inputs > 1.0 should still clip gracefully
        eta_zero = self.manager.calculate_eta(0.0, 0.0, 0.0)
        self.assertEqual(eta_zero, 0.0)
        
        eta_large = self.manager.calculate_eta(10.0, 10.0, 10.0)
        self.assertEqual(eta_large, 1.0) # clipped at 1.0

    def test_genesis_forward_formula(self):
        """Test genesis forward growth: P_{k+1} = N_k * P_k * eta_k"""
        p_k = 100.0
        n_k = 2.0
        eta_k = 0.5
        
        # Specified eta_k
        val, eta_used = self.manager.genesis_forward(p_k, n_k, eta_k=eta_k)
        self.assertEqual(val, 100.0) # 100 * 2 * 0.5 = 100
        self.assertEqual(eta_used, 0.5)
        
        # Dynamic eta_k calculation
        val_dyn, eta_dyn = self.manager.genesis_forward(p_k, n_k, context_val=1.0, runtime_val=1.0, dependency_val=1.0)
        # Expected dynamic eta = 0.729
        # Expected val = 100.0 * 2.0 * 0.729 = 145.8
        self.assertAlmostEqual(eta_dyn, 0.729, places=6)
        self.assertAlmostEqual(val_dyn, 145.8, places=6)

    def test_genesis_backward_formula(self):
        """Test genesis backward regression: P_k = P_{k+1} / (N_k * eta_k)"""
        p_k_plus_1 = 145.8
        n_k = 2.0
        eta_k = 0.729
        
        # Specified eta_k
        p_k, eta_used = self.manager.genesis_backward(p_k_plus_1, n_k, eta_k=eta_k)
        self.assertAlmostEqual(p_k, 100.0, places=6)
        self.assertEqual(eta_used, 0.729)
        
        # Dynamic eta_k calculation
        p_k_dyn, eta_dyn = self.manager.genesis_backward(p_k_plus_1, n_k, context_val=1.0, runtime_val=1.0, dependency_val=1.0)
        self.assertAlmostEqual(eta_dyn, 0.729, places=6)
        self.assertAlmostEqual(p_k_dyn, 100.0, places=6)

    def test_genesis_backward_zero_division(self):
        """Test division by zero checks in regression"""
        with self.assertRaises(ValueError):
            self.manager.genesis_backward(100.0, 0.0, eta_k=0.5)
            
        with self.assertRaises(ValueError):
            self.manager.genesis_backward(100.0, 2.0, eta_k=0.0)

    def test_forward_backward_reversible(self):
        """Test that forward growth and backward regression are mathematically reversible"""
        p_k_init = 250.0
        n_k = 3.5
        
        p_k_plus_1, eta_used = self.manager.genesis_forward(p_k_init, n_k, context_val=0.8, runtime_val=0.9, dependency_val=0.7)
        p_k_restored, _ = self.manager.genesis_backward(p_k_plus_1, n_k, eta_k=eta_used)
        
        self.assertAlmostEqual(p_k_init, p_k_restored, places=10)

    def test_export_to_json(self):
        """Test export parameters to JSON format and parsing correctness"""
        json_str = self.manager.export_to_json()
        parsed = json.loads(json_str)
        
        self.assertEqual(parsed["particle_id"], self.manager.particle_id)
        self.assertEqual(parsed["MRL_環境變化公式"]["context_weight"], 0.4)
        self.assertEqual(parsed["MRL_創世公式"]["eta_k"], 0.618)


if __name__ == "__main__":
    unittest.main()
