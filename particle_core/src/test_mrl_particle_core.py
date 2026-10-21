#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import tempfile
import unittest

from mrl_particle_core import (
    MRL_Capability_Type,
    MRL_Particle,
    MRL_Particle_Fusion_Engine,
    MRL_Particle_Manager,
)
from mrl_tensor import tensor


class TestMRLParticleCore(unittest.TestCase):
    def test_particle_serialization_round_trip(self):
        particle = MRL_Particle(
            name="Mr.liou.Particle.Reasoning.P19.v1",
            capability_type=MRL_Capability_Type.REASONING,
            version="v1",
            base_model="Mr.liou.Base.Qwen.v1",
            teacher_model="teacher-model",
        )
        particle.training_loss_history = list(range(25))

        restored = MRL_Particle.from_dict(particle.to_dict())

        self.assertEqual(restored.name, particle.name)
        self.assertEqual(restored.capability_type, MRL_Capability_Type.REASONING)
        self.assertEqual(len(restored.training_loss_history), 20)
        self.assertEqual(len(particle.compute_hash()), 16)

    def test_fusion_engine_fallback_without_registered_particle(self):
        engine = MRL_Particle_Fusion_Engine()
        x = tensor([[1.0, 2.0]])

        result = engine.fuse_for_task(MRL_Capability_Type.CODING, "layer", x)

        self.assertEqual(result["activated_particles"], [])
        self.assertEqual(result["fusion_weights"], {})
        self.assertIn("warning", result)
        self.assertEqual(result["output"].shape, x.shape)

    def test_particle_manager_save_and_load(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir)

        manager = MRL_Particle_Manager(storage_path=temp_dir)
        particle = MRL_Particle(
            name="Mr.liou.Particle.Coding.C1.v1",
            capability_type=MRL_Capability_Type.CODING,
            version="v1",
            base_model="Mr.liou.Base.Qwen.v1",
            teacher_model="teacher-model",
        )

        saved_path = manager.save_particle(particle)
        loaded = manager.load_particle(particle.name)
        listed = manager.list_all_particles()
        status = manager.get_particle_status(particle.name)

        self.assertTrue(saved_path.endswith(".json"))
        self.assertEqual(loaded.name, particle.name)
        self.assertEqual(len(listed), 1)
        self.assertEqual(status["status"], "loaded")
        self.assertEqual(status["capability_type"], MRL_Capability_Type.CODING.value)


if __name__ == "__main__":
    unittest.main()
