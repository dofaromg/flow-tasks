#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from process_tasks import TaskProcessor


class TaskProcessorSafetyTests(unittest.TestCase):
    def test_python_validation_does_not_execute_module(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            marker = root / "executed.txt"
            target = root / "danger.py"
            target.write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed')\n"
                "VALUE = 1\n",
                encoding="utf-8",
            )
            processor = TaskProcessor(str(root / "tasks"), run_repository_checks=False)
            result = {"checks": [], "errors": [], "warnings": []}
            processor._validate_python_file(target, result)
            self.assertFalse(marker.exists())
            self.assertFalse(result["errors"])

    def test_previous_json_is_archived_before_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tasks = root / "tasks"
            results = tasks / "results"
            results.mkdir(parents=True)
            target = results / "dated_result.json"
            target.write_text('{"original": true}\n', encoding="utf-8")
            processor = TaskProcessor(str(tasks), run_repository_checks=False)
            archived = processor._write_json_preserving_history(target, {"new": True})
            self.assertIsNotNone(archived)
            self.assertEqual(archived.read_text(encoding="utf-8"), '{"original": true}\n')
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"new": True})

    def test_repository_checks_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as temp:
            tasks = Path(temp) / "tasks"
            tasks.mkdir()
            processor = TaskProcessor(str(tasks), run_repository_checks=False)
            summary = processor.process_all_tasks()
            names = [item["check"] for item in summary["repository_checks"]["checks"]]
            self.assertIn("repository_checks_disabled", names)

    def test_legacy_directory_target_file_remains_compatible(self):
        with tempfile.TemporaryDirectory() as temp:
            processor = TaskProcessor(str(Path(temp) / "tasks"), run_repository_checks=False)
            result = {"checks": [], "errors": [], "warnings": []}
            processor._validate_schema(
                {
                    "task_id": "particle-language-core",
                    "language": "python",
                    "description": "core",
                    "target_file": "particle_core/",
                },
                result,
            )
            self.assertFalse(result["errors"])

    def test_schema_rejects_ambiguous_or_incompatible_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            processor = TaskProcessor(str(Path(temp) / "tasks"), run_repository_checks=False)
            cases = [
                {
                    "task_id": "both-targets",
                    "language": "python",
                    "description": "ambiguous",
                    "target_file": "a.py",
                    "target_directory": "src",
                },
                {
                    "task_id": "wrong-suffix",
                    "language": "python",
                    "description": "wrong suffix",
                    "target_file": "a.js",
                },
                {
                    "task_id": "unknown-language",
                    "language": "braincode",
                    "description": "unknown",
                    "target_file": "a.bc",
                },
            ]
            for task in cases:
                with self.subTest(task=task["task_id"]):
                    result = {"checks": [], "errors": [], "warnings": []}
                    processor._validate_schema(task, result)
                    self.assertTrue(result["errors"])

    def test_python_directory_validation_checks_nested_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nested = root / "src" / "nested"
            nested.mkdir(parents=True)
            (root / "src" / "valid.py").write_text("VALUE = 1\n", encoding="utf-8")
            (nested / "invalid.py").write_text("def broken(:\n", encoding="utf-8")
            processor = TaskProcessor(str(root / "tasks"), run_repository_checks=False)
            result = {"checks": [], "errors": [], "warnings": []}
            processor._validate_python_directory(root / "src", result)
            self.assertTrue(result["errors"])
            self.assertIn("invalid.py", result["errors"][0]["message"])

    def test_failed_command_output_is_redacted(self):
        with tempfile.TemporaryDirectory() as temp:
            processor = TaskProcessor(str(Path(temp) / "tasks"), run_repository_checks=False)
            result = processor._run_command(
                [sys.executable, "-c", "import sys; print('secret-token'); sys.exit(2)"]
            )
            self.assertEqual(result["returncode"], 2)
            self.assertNotIn("secret-token", result["output_excerpt"])
            self.assertIn("omitted", result["output_excerpt"])


if __name__ == "__main__":
    unittest.main()
