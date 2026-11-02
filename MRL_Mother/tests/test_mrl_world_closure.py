"""WorldModule closure regression tests (stdlib only).
origin_signature: MrLiouWord
"""
import importlib.util
import json
import pathlib
import sqlite3
import sys
import tempfile
import unittest

WORLD_DIR = pathlib.Path(__file__).resolve().parents[1] / "05_persona"
sys.path.insert(0, str(WORLD_DIR))
spec = importlib.util.spec_from_file_location("world_module", WORLD_DIR / "world_module.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WorldClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = pathlib.Path(self.temp.name)
        self.world = module.WorldModule(data_dir=self.folder)

    def test_mutations_are_versioned_and_reopen(self):
        self.assertEqual(self.world.version_index, 0)
        self.world.set_node("FlowSeed", {"layer": "L1"})
        self.world.set_state("active", "FlowSeed")
        self.world.set_globe_coord("FlowSeed", 25.0, 121.5, 3.0)
        self.assertEqual(self.world.version_index, 3)
        self.assertEqual(self.world.get_state("active"), "FlowSeed")
        self.assertEqual(self.world.get_globe_coord("FlowSeed")["alt"], 3.0)
        self.assertEqual(self.world.verify_history()["integrity"], "PASS")
        reopened = module.WorldModule(data_dir=self.folder)
        self.assertEqual(reopened.version_index, 3)
        self.assertEqual(reopened.get_node("FlowSeed")["data"]["layer"], "L1")

    def test_rewind_restores_state_without_erasing_history(self):
        self.world.set_state("answer", "before")
        self.world.set_state("answer", "after")
        self.assertEqual(self.world.version_index, 2)
        ok, msg = self.world.rewind(1)
        self.assertTrue(ok, msg)
        self.assertEqual(self.world.version_index, 3)
        self.assertEqual(self.world.get_state("answer"), "before")
        self.assertEqual(self.world.load_version(2)["state"]["answer"], "after")
        self.assertEqual(len(self.world.history()), 4)
        self.assertEqual(module.WorldModule(self.folder).get_state("answer"), "before")
        self.assertEqual(self.world.verify_history()["integrity"], "PASS")

    def test_restore_nodes_and_globe(self):
        self.world.set_node("n", {"v": 1})
        self.world.set_globe_coord("n", 10, 20)
        self.world.set_node("n", {"v": 2})
        self.world.restore_version(1)
        self.assertEqual(self.world.get_node("n")["data"]["v"], 1)
        self.assertIsNone(self.world.get_globe_coord("n"))
        self.assertEqual(self.world.verify_history()["latest_version_index"], 4)

    def test_bootstrap_preserves_existing_legacy_data(self):
        legacy_dir = self.folder / "legacy_import"
        legacy_dir.mkdir()
        (legacy_dir / "nodes.json").write_text(json.dumps({"old": {"data": {"v": 1}}}))
        (legacy_dir / "trajectory.jsonl").write_text('{"old":"trace"}\n')
        w = module.WorldModule(legacy_dir)
        self.assertEqual(w.get_node("old")["data"]["v"], 1)
        self.assertEqual(w.version_index, 0)
        self.assertIn("old", (legacy_dir / "trajectory.jsonl").read_text())

    def test_integrity_tampering_fails_closed(self):
        self.world.set_state("x", 1)
        with sqlite3.connect(self.folder / "world_events.sqlite3") as db:
            db.execute("UPDATE events SET snapshot_json = '{}' WHERE version_index = 1")
        with self.assertRaises(module.WorldClosureIntegrityError):
            module.WorldModule(self.folder)
        with self.assertRaises(module.WorldClosureIntegrityError):
            self.world.set_state("x", 2)

    def test_invalid_rewind_does_not_mutate(self):
        self.assertFalse(self.world.rewind(1)[0])
        self.assertFalse(self.world.rewind(0)[0])
        self.assertEqual(self.world.version_index, 0)
        with self.assertRaises(KeyError):
            self.world.restore_version(99)


if __name__ == "__main__":
    unittest.main()
