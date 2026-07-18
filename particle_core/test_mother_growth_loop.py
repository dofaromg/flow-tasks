#!/usr/bin/env python3
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from mother_growth_loop import MotherGrowthLoop


def pipeline(*texts):
    return {
        "views": {
            "memory_seed": {
                "seed_type": "distilled_external_analysis",
                "created_at": "volatile",
                "source_count": len(texts),
                "dedup": {"removed": 0},
                "insights": [
                    {"insight": text, "confidence": 0.9, "provenance": [{"source": "test"}]}
                    for text in texts
                ],
            }
        }
    }


class StubExtractor:
    def process_external_analysis_pipeline(self, source, **kwargs):
        return pipeline(str(source))


class MotherGrowthLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.loop = MotherGrowthLoop(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_create_upgrade_no_change_and_next_task_context(self):
        first = self.loop.absorb_pipeline_result(pipeline("alpha"), "core")
        self.assertEqual(first["status"], "created")
        self.assertEqual(first["version"], 1)
        unchanged = self.loop.absorb_pipeline_result(pipeline("alpha"), "core")
        self.assertEqual(unchanged["status"], "unchanged")
        self.assertEqual(unchanged["version"], 1)
        upgraded = self.loop.absorb_pipeline_result(pipeline("alpha", "beta"), "core")
        self.assertEqual(upgraded["status"], "upgraded")
        self.assertEqual(upgraded["version"], 2)
        self.assertEqual(upgraded["diff"]["added"], ["beta"])
        prepared = self.loop.prepare_next_task({"task_id": "next"}, ["core"])
        self.assertEqual(prepared["mother_context"][0]["version"], 2)
        self.assertEqual(len(prepared["mother_context"][0]["insights"]), 2)
        self.assertEqual(self.loop.verify_store("core")["status"], "PASS")

    def test_rollback_preserves_newer_version(self):
        self.loop.absorb_pipeline_result(pipeline("v1"), "core")
        second = self.loop.absorb_pipeline_result(pipeline("v2"), "core")
        self.loop.rollback("core", 1)
        self.assertEqual(self.loop.load_active("core")["version"], 1)
        self.assertTrue((Path(self.temp.name) / second["path"]).exists())
        self.assertEqual(self.loop.verify_store("core")["status"], "PASS")

    def test_tamper_is_detected(self):
        created = self.loop.absorb_pipeline_result(pipeline("trusted"), "core")
        version_path = Path(self.temp.name) / created["path"]
        json_module = __import__("json")
        data = json_module.loads(version_path.read_text(encoding="utf-8"))
        data["seed"]["insights"][0]["insight"] = "tampered"
        version_path.write_text(json_module.dumps(data), encoding="utf-8")
        self.assertEqual(self.loop.verify_store("core")["status"], "FAIL")

    def test_process_and_absorb_connects_extractor_to_store(self):
        result = self.loop.process_and_absorb(StubExtractor(), "source text", "external")
        self.assertEqual(result["backfill"]["status"], "created")
        self.assertEqual(self.loop.build_context("external")["insights"][0]["insight"], "source text")
        exported = __import__("json").loads(
            Path(result["mqm_export"]["path"]).read_text(encoding="utf-8")
        )
        self.assertEqual(exported["structure"]["mother_seed_version"], 1)
        self.assertEqual(
            exported["structure"]["mother_seed_hash"],
            result["backfill"]["content_hash"],
        )

    def test_invalid_seed_is_rejected(self):
        with self.assertRaises(ValueError):
            self.loop.absorb_pipeline_result({"views": {"memory_seed": {"seed_type": "x"}}}, "bad")


if __name__ == "__main__":
    unittest.main()
