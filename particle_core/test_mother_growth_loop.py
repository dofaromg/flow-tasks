#!/usr/bin/env python3
import os
import json
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
        rolled_back = self.loop.rollback("core", 1)
        self.assertEqual(self.loop.load_active("core")["version"], 1)
        self.assertTrue((Path(self.temp.name) / second["path"]).exists())
        exported = json.loads(Path(rolled_back["mqm_export"]["path"]).read_text(encoding="utf-8"))
        self.assertEqual(exported["structure"]["mother_seed_version"], 1)
        self.assertEqual(
            exported["structure"]["mother_seed_hash"],
            self.loop.load_active("core")["content_hash"],
        )
        self.assertEqual(self.loop.verify_store("core")["status"], "PASS")

    def test_tamper_is_detected(self):
        created = self.loop.absorb_pipeline_result(pipeline("trusted"), "core")
        version_path = Path(self.temp.name) / created["path"]
        data = json.loads(version_path.read_text(encoding="utf-8"))
        data["seed"]["insights"][0]["insight"] = "tampered"
        version_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.loop.verify_store("core")["status"], "FAIL")
        with self.assertRaisesRegex(ValueError, "content hash mismatch"):
            self.loop.build_context("core")
        with self.assertRaisesRegex(ValueError, "content hash mismatch"):
            self.loop.export_active_for_mqm("core")

    def test_version_gap_never_overwrites_existing_version(self):
        first = self.loop.absorb_pipeline_result(pipeline("v1"), "core")
        second = self.loop.absorb_pipeline_result(pipeline("v2"), "core")
        third = self.loop.absorb_pipeline_result(pipeline("v3"), "core")
        second_path = Path(self.temp.name) / second["path"]
        third_path = Path(self.temp.name) / third["path"]
        third_before = third_path.read_bytes()
        second_path.unlink()
        fourth = self.loop.absorb_pipeline_result(pipeline("v4"), "core")
        self.assertEqual(first["version"], 1)
        self.assertEqual(fourth["version"], 4)
        self.assertEqual(third_path.read_bytes(), third_before)
        verification = self.loop.verify_store("core")
        self.assertEqual(verification["status"], "FAIL")
        self.assertTrue(any("Version gap" in error for error in verification["errors"]))

    def test_immutable_writer_refuses_existing_version(self):
        created = self.loop.absorb_pipeline_result(pipeline("v1"), "core")
        existing = Path(self.temp.name) / created["path"]
        with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
            self.loop._write_immutable_json(existing, {"unexpected": True})

    def test_seed_id_sanitization_is_collision_resistant(self):
        slash = self.loop.absorb_pipeline_result(pipeline("slash"), "a/b")
        underscore = self.loop.absorb_pipeline_result(pipeline("underscore"), "a_b")
        self.assertNotEqual(slash["seed_id"], underscore["seed_id"])
        self.assertEqual(self.loop.build_context("a/b")["insights"][0]["insight"], "slash")
        self.assertEqual(self.loop.build_context("a_b")["insights"][0]["insight"], "underscore")
        self.assertEqual(self.loop._safe_seed_id("CORE"), self.loop._safe_seed_id("core"))
        self.assertLessEqual(len(self.loop._safe_seed_id("x" * 300)), 96)

    def test_active_pointer_path_and_journal_binding_are_enforced(self):
        self.loop.absorb_pipeline_result(pipeline("trusted"), "core")
        pointer_path = Path(self.temp.name) / "active" / "core.json"
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        pointer["path"] = "../../outside.json"
        pointer_path.write_text(json.dumps(pointer), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "path mismatch"):
            self.loop.load_active("core")

        pointer["path"] = "seeds/core/v000001.json"
        pointer["activation_event_hash"] = "0" * 64
        pointer_path.write_text(json.dumps(pointer), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "journal event missing"):
            self.loop.load_active("core")

    def test_missing_journal_coverage_fails_verification(self):
        self.loop.absorb_pipeline_result(pipeline("trusted"), "core")
        (Path(self.temp.name) / "journal.jsonl").write_text("", encoding="utf-8")
        verification = self.loop.verify_store("core")
        self.assertEqual(verification["status"], "FAIL")
        self.assertTrue(any("Journal coverage missing" in error for error in verification["errors"]))

    def test_corrupt_journal_is_never_extended(self):
        self.loop.absorb_pipeline_result(pipeline("trusted"), "core")
        journal_path = Path(self.temp.name) / "journal.jsonl"
        journal_path.write_text(journal_path.read_text(encoding="utf-8") + "not-json\n", encoding="utf-8")
        before = journal_path.read_bytes()
        with self.assertRaisesRegex(ValueError, "Journal parse|invalid journal"):
            self.loop.absorb_pipeline_result(pipeline("trusted", "next"), "core")
        self.assertEqual(journal_path.read_bytes(), before)

    def test_changed_insight_metadata_is_reported(self):
        first = pipeline("alpha")
        self.loop.absorb_pipeline_result(first, "core")
        changed = pipeline("alpha")
        changed["views"]["memory_seed"]["insights"][0]["confidence"] = 0.5
        result = self.loop.absorb_pipeline_result(changed, "core")
        self.assertEqual(result["status"], "upgraded")
        self.assertEqual(result["diff"]["changed_count"], 1)
        self.assertEqual(result["diff"]["changed"][0]["insight"], "alpha")

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
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            self.loop.absorb_pipeline_result(
                {"views": {"memory_seed": {"seed_type": "x", "insights": []}}},
                "bad",
            )
        with self.assertRaisesRegex(ValueError, "source_count"):
            invalid_count = pipeline("alpha")
            invalid_count["views"]["memory_seed"]["source_count"] = -1
            self.loop.absorb_pipeline_result(invalid_count, "bad")

    def test_dead_process_lock_is_recovered(self):
        lock_path = Path(self.temp.name) / ".growth.lock"
        lock_path.write_text(json.dumps({"pid": 99999999}), encoding="utf-8")
        created = self.loop.absorb_pipeline_result(pipeline("recovered"), "core")
        self.assertEqual(created["status"], "created")
        self.assertFalse(lock_path.exists())

    def test_context_input_contracts_are_enforced(self):
        self.loop.absorb_pipeline_result(pipeline("alpha"), "core")
        with self.assertRaisesRegex(ValueError, "max_insights"):
            self.loop.build_context("core", max_insights=0)
        with self.assertRaisesRegex(TypeError, "task must be a mapping"):
            self.loop.prepare_next_task([], ["core"])
        with self.assertRaisesRegex(TypeError, "seed_ids"):
            self.loop.prepare_next_task({}, "core")


if __name__ == "__main__":
    unittest.main()
