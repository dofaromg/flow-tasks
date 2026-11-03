"""WorldModule closure regression tests (stdlib only).
origin_signature: MrLiouWord
"""
import inspect
from contextlib import closing
import subprocess
from unittest import TestCase, main, mock
import importlib.util
import json
import pathlib
import sqlite3
import sys
import tempfile

WORLD_DIR = pathlib.Path(__file__).resolve().parents[1] / "05_persona"
sys.path.insert(0, str(WORLD_DIR))
from world_closure_store import WorldClosureIntegrityError

spec = importlib.util.spec_from_file_location("world_module", WORLD_DIR / "world_module.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WorldClosureTests(TestCase):
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
        with closing(sqlite3.connect(self.folder / "world_events.sqlite3")) as db, db:
            db.execute("UPDATE events SET snapshot_json = '{}' WHERE version_index = 1")
        with self.assertRaises(WorldClosureIntegrityError):
            module.WorldModule(self.folder)
        with self.assertRaises(WorldClosureIntegrityError):
            self.world.set_state("x", 2)

    def test_invalid_rewind_does_not_mutate(self):
        self.assertFalse(self.world.rewind(1)[0])
        self.assertFalse(self.world.rewind(0)[0])
        self.assertEqual(self.world.version_index, 0)
        with self.assertRaises(KeyError):
            self.world.restore_version(99)

    def assert_world(self, world, expected):
        snap = world.snapshot()
        self.assertEqual({k: snap[k] for k in ('nodes', 'state', 'globe')}, expected)
        for key in expected:
            self.assertEqual(json.loads((self.folder / (key + '.json')).read_text(encoding='utf-8')),
                             expected[key])

    def test_restore_all_components_and_keep_every_historical_row(self):
        self.world.set_node('n', {'版本': 1})
        self.world.set_state('mode', {'values': [1]})
        self.world.set_globe_coord('n', 25, 121, 4, {'v': 1})
        target = self.world.load_version(3)
        self.world.set_node('n', {'版本': 2})
        self.world.set_node('extra', {})
        self.world.set_state('mode', {'values': [2]})
        self.world.set_globe_coord('n', -20, -30, 9)
        before = self.world.history()
        self.assertEqual(self.world.restore_version(3), target)
        self.assert_world(self.world, target)
        self.assertEqual(self.world.history()[:-1], before)
        self.assertEqual(self.world.history()[-1]['detail']['target_version_index'], 3)
        for event in before:
            self.assertEqual(self.world.load_version(event['version_index']), event['snapshot'])
        self.assert_world(module.WorldModule(self.folder), target)
        self.world.restore_version(7)
        self.assert_world(self.world, before[-1]['snapshot'])
        self.world.restore_version(0)
        self.assert_world(self.world, {'nodes': {}, 'state': {}, 'globe': {}})

    def test_full_legacy_import_once_preserves_trajectory_bytes(self):
        folder = self.folder / 'legacy_full'
        folder.mkdir()
        initial = {'nodes': {'舊節點': {'data': {'v': 1}}},
                   'state': {'mode': ['old']}, 'globe': {'舊節點': {'lat': 25, 'lon': 121}}}
        for key, value in initial.items():
            (folder / (key + '.json')).write_text(json.dumps(value), encoding='utf-8')
        trace = b'{"legacy":"trace"}\r\n'
        (folder / 'trajectory.jsonl').write_bytes(trace)
        world = module.WorldModule(folder)
        self.assertEqual(world.load_version(0), initial)
        self.assertEqual((folder / 'trajectory.jsonl').read_bytes(), trace)
        world.set_state('mode', 'new')
        world.restore_version(0)
        reopened = module.WorldModule(folder)
        self.assertEqual(reopened.version_index, 2)
        self.assertEqual(reopened.load_version(0), initial)
        self.assertTrue((folder / 'trajectory.jsonl').read_bytes().startswith(trace))

    def test_malformed_legacy_fails_without_overwriting_source(self):
        for bad in ('{broken', '[]', '{"x":NaN}'):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as directory:
                folder = pathlib.Path(directory)
                source = folder / 'state.json'
                source.write_text(bad, encoding='utf-8')
                with self.assertRaises(ValueError):
                    module.WorldModule(folder)
                self.assertEqual(source.read_text(encoding='utf-8'), bad)
                self.assertFalse((folder / 'nodes.json').exists())

    def test_reopen_repairs_missing_corrupt_and_stale_mirrors(self):
        self.world.set_node('n', {'v': 1})
        self.world.set_state('x', 1)
        self.world.set_globe_coord('n', 1, 2)
        expected = self.world.load_version(3)
        history = self.world.history()
        (self.folder / 'nodes.json').unlink()
        (self.folder / 'state.json').write_text('{truncated', encoding='utf-8')
        (self.folder / 'globe.json').write_text('{}', encoding='utf-8')
        reopened = module.WorldModule(self.folder)
        self.assert_world(reopened, expected)
        self.assertEqual(reopened.history(), history)

    def test_failure_halfway_through_mirrors_recovers_committed_restore(self):
        self.world.set_node('n', {'v': 1})
        self.world.set_state('x', 1)
        before = self.world.history()
        save = module._save_json
        def fail_state(path, obj):
            if path.name == 'state.json':
                raise OSError('injected disk failure')
            save(path, obj)
        with mock.patch.object(module, '_save_json', side_effect=fail_state):
            with self.assertRaises(OSError):
                self.world.restore_version(0)
        reopened = module.WorldModule(self.folder)
        self.assert_world(reopened, before[0]['snapshot'])
        self.assertEqual(reopened.history()[:-1], before)
        self.assertEqual(reopened.version_index, 3)

    def test_atomic_replace_failure_preserves_previous_json(self):
        path = self.folder / 'state.json'
        before = path.read_bytes()
        with mock.patch.object(module.os, 'replace', side_effect=OSError('replace failed')):
            with self.assertRaises(OSError):
                module._save_json(path, {'new': 1})
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(list(self.folder.glob('*.tmp')), [])

    def test_trajectory_append_failure_does_not_lose_committed_state(self):
        with mock.patch.object(self.world, '_record_trajectory', side_effect=OSError('trace failure')):
            with self.assertRaises(OSError):
                self.world.set_state('committed', True)
        reopened = module.WorldModule(self.folder)
        self.assertEqual(reopened.get_state('committed'), True)
        self.assertEqual(reopened.version_index, 1)

    def test_invalid_restore_and_failed_mutation_leave_history_unchanged(self):
        before = self.world.history()
        for value in (-1, True, 1.5, '0', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.world.restore_version(value)
        with self.assertRaises(ValueError):
            self.world.set_state('bad', float('nan'))
        self.assertEqual(self.world.history(), before)
        self.assertEqual(self.world.get_state('bad'), None)

    def test_detached_snapshots_cannot_modify_archived_versions(self):
        self.world.set_state('nested', {'values': [1]})
        for snap in (self.world.load_version(1), self.world.snapshot(),
                     self.world.history()[1]['snapshot']):
            snap['state']['nested']['values'].append(99)
        self.assertEqual(self.world.load_version(1)['state']['nested']['values'], [1])
        self.assertEqual(self.world.get_state('nested'), {'values': [1]})

    def test_corruption_detected_by_reads_and_writes(self):
        for sql in ("UPDATE events SET snapshot_json='not json' WHERE version_index=0",
                    "UPDATE events SET prev_hash='broken' WHERE version_index=0",
                    "DELETE FROM events"):
            with self.subTest(sql=sql), tempfile.TemporaryDirectory() as directory:
                world = module.WorldModule(pathlib.Path(directory))
                with closing(sqlite3.connect(world._closure.path)) as db, db:
                    db.execute(sql)
                with self.assertRaises(WorldClosureIntegrityError):
                    module.WorldModule(pathlib.Path(directory))
                for read in (world.history, world.verify_history,
                             lambda: world.load_version(0), lambda: world.set_state('x', 1)):
                    with self.assertRaises(WorldClosureIntegrityError):
                        read()

    def test_process_exit_before_and_after_sqlite_commit(self):
        for phase in ('before', 'after'):
            with self.subTest(phase=phase):
                folder = self.folder / phase
                world = module.WorldModule(folder)
                world.set_state('x', 'old')
                code = '''
import os, pathlib, sys
sys.path.insert(0, sys.argv[1])
from world_module import WorldModule
world = WorldModule(pathlib.Path(sys.argv[2]))
if sys.argv[3] == 'before':
    original = world._closure._insert
    def crash(*args):
        original(*args)
        os._exit(73)
    world._closure._insert = crash
else:
    world._apply_snapshot = lambda snapshot: os._exit(73)
world.set_state('x', 'new')
'''
                child = subprocess.run([sys.executable, '-c', code, str(WORLD_DIR), str(folder), phase],
                                       capture_output=True, text=True, timeout=30)
                self.assertEqual(child.returncode, 73, child.stderr)
                reopened = module.WorldModule(folder)
                self.assertEqual(reopened.get_state('x'), 'old' if phase == 'before' else 'new')
                self.assertEqual(reopened.version_index, 1 if phase == 'before' else 2)
                self.assertEqual(reopened.load_version(1)['state']['x'], 'old')
                self.assertEqual(reopened.verify_history()['integrity'], 'PASS')

    def test_legacy_api_signatures_and_return_shapes(self):
        expected = {
            'set_node': ['self', 'name', 'data'], 'get_node': ['self', 'name'],
            'list_nodes': ['self'], 'set_state': ['self', 'key', 'value'],
            'get_state': ['self', 'key', 'default'], 'snapshot': ['self'],
            'set_globe_coord': ['self', 'node_name', 'lat', 'lon', 'alt', 'meta'],
            'get_globe_coord': ['self', 'node_name'], 'trajectory': ['self'],
            'rewind': ['self', 'steps']}
        for method, names in expected.items():
            self.assertEqual(list(inspect.signature(getattr(module.WorldModule, method)).parameters), names)
        self.assertIsNone(self.world.get_node('missing'))
        self.assertEqual(self.world.get_state('missing', 7), 7)
        self.assertIsNone(self.world.set_state('x', 1))
        entry = self.world.set_node('n', {})
        self.assertEqual(set(entry), {'name', 'data', 'updated_at_ms', 'hash'})
        self.assertEqual(self.world.list_nodes(), ['n'])
        coord = self.world.set_globe_coord('n', 1, 2)
        self.assertEqual(set(coord), {'lat', 'lon', 'alt', 'meta', 'updated_at_ms'})
        self.assertIsInstance(self.world.trajectory(), list)
        self.assertIsInstance(self.world.rewind(), tuple)
        self.assertEqual(module.ORIGIN_SIGNATURE, 'MrLiouWord')


if __name__ == "__main__":
    main()
