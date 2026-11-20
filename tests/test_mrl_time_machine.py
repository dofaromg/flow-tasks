"""MRL version/trace integration regressions. origin_signature: MrLiouWord"""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "mrl_runtime", ROOT / "MRL_Mother/04_runtime/flowcore_loop.py")
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class TimeMachineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.tracer = runtime.Tracer(self.temp.name)
        self.machine = self.tracer.timeMachine

    def initial(self):
        return self.machine.saveVersion({"coordinates": {"x": 1}, "items": [1]}, "v01.09")

    def test_exact_index_and_string_lookup(self):
        v = self.initial()
        self.assertEqual(v["timestamp"], v["version_index"])
        for ref in (v["version_id"], 1, "v01.09"):
            self.assertEqual(self.tracer.loadVersion(ref), v)

    def test_nested_mount_is_read_only(self):
        v = self.initial()
        with self.assertRaises(TypeError):
            v["snapshot"]["coordinates"]["x"] = 4
        with self.assertRaises(AttributeError):
            v["snapshot"]["items"].append(2)

    def test_branch_preserves_history_and_parent(self):
        a = self.initial()
        path = Path(self.tracer.trace_path)
        prefix = path.read_bytes()
        branch = self.tracer.branchFrom(a["version_id"])
        b = branch.commit({"coordinates": {"x": 2}}, "v2.0")
        self.assertTrue(path.read_bytes().startswith(prefix))
        self.assertEqual(b["parent_version_id"], a["version_id"])
        self.assertEqual(self.tracer.mountVersion(1), a)
        self.assertEqual(b["origin_signature"], "MrLiouWord")

    def test_direct_historical_write_rejected(self):
        self.initial()
        with self.assertRaises(PermissionError):
            self.machine.saveVersion({}, "v2.0")

    def test_stale_parent_rejected(self):
        a = self.initial()
        branch = self.machine.branchFrom(1)
        branch.commit({}, "v2.0")
        with self.assertRaises(ValueError):
            self.machine.saveVersion({}, "v3.0", branch_id=branch.branch_id, parent=a["version_id"])

    def test_diff_add_remove_and_nested_change(self):
        self.initial()
        self.machine.branchFrom(1).commit({"coordinates": {"x": 2}, "a/b": True}, "v2.0")
        diff = self.tracer.diffVersions(1, 2)
        self.assertEqual({d["path"]: d["op"] for d in diff},
                         {"/coordinates/x": "replace", "/items": "remove", "/a~1b": "add"})

    def test_diff_distinguishes_boolean_and_integer(self):
        self.machine.saveVersion({"x": True}, "v1.0")
        self.machine.branchFrom(1).commit({"x": 1}, "v2.0")
        self.assertEqual(len(self.machine.diffVersions(1, 2)), 1)

    def test_restart_reads_same_snapshots(self):
        a = self.initial()
        self.assertEqual(runtime.Tracer(self.temp.name).mountVersion(1), a)

    def test_legacy_timestamp_and_coordinates_unchanged(self):
        old = {"timestamp": "2000-01-01T00:00:00+00:00", "coordinates": [1, 2, 3]}
        self.tracer.emit("legacy", old)
        prefix = Path(self.tracer.trace_path).read_bytes()
        v = self.machine.importLegacy(old, "v1.0")
        self.assertEqual(v["snapshot"]["legacy_record"]["timestamp"], old["timestamp"])
        self.assertTrue(Path(self.tracer.trace_path).read_bytes().startswith(prefix))
        self.assertEqual(len(self.machine.queryAt("2999-01-01T00:00:00+00:00")), 3)

    def test_ring_and_checkpoint_retention(self):
        for n in range(273):
            self.tracer.emit("trace", {"n": n})
        view = self.machine.memoryWindow()
        self.assertEqual(len(view["ring"]), 64)
        self.assertEqual(len(view["checkpoints"]), 16)
        self.assertEqual(view["checkpoints"][-1]["tick"], 272)
        self.assertEqual(len(Path(self.tracer.trace_path).read_text().splitlines()), 273)

    def test_tamper_and_head_mismatch_fail_closed(self):
        self.initial()
        path = Path(self.tracer.trace_path)
        original = path.read_text()
        path.write_text(original.replace('"x":1', '"x":9'))
        with self.assertRaisesRegex(ValueError, "merkle_mismatch"):
            self.machine.loadVersion(1)
        path.write_text(original)
        self.tracer._state["merkle_root"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "head_mismatch"):
            self.machine.loadVersion(1)

    def test_validation_does_not_append(self):
        self.initial()
        before = Path(self.tracer.trace_path).read_bytes()
        for version in ("v1.0", "wrong"):
            with self.assertRaises((ValueError, PermissionError)):
                self.machine.saveVersion({}, version)
        with self.assertRaises(KeyError):
            self.machine.loadVersion("missing")
        self.assertEqual(Path(self.tracer.trace_path).read_bytes(), before)

    def test_concurrent_appends_preserve_merkle(self):
        threads = [threading.Thread(target=lambda: self.tracer.emit("test", {})) for _ in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(self.machine._events()), 20)

    def test_law_archived_once_in_existing_merkle_trace(self):
        self.initial()
        self.machine.branchFrom(1).commit({}, "v2.0")
        seals = [e for e in self.machine._events() if e["event_type"] == "timemachine_law_seal"]
        self.assertEqual(len(seals), 1)
        self.assertEqual(seals[0]["payload"]["documents"]["core/law.md"],
                         (ROOT / "core/law.md").read_text())

    def test_root_law_tampering_rejected(self):
        original = Path.read_bytes

        def tampered(path):
            if path == ROOT / "core/law.md":
                return b"tampered law"
            return original(path)

        with patch.object(Path, "read_bytes", tampered):
            with self.assertRaisesRegex(ValueError, "root_law_tampered"):
                _ = self.tracer.timeMachine

    def test_checkpoint_boundaries(self):
        for n in range(65):
            self.tracer.emit("trace", {"n": n})
        view = self.machine.memoryWindow()
        self.assertEqual([c["tick"] for c in view["checkpoints"]], [16, 32, 48, 64])
        self.assertEqual(len(view["ring"]), 64)

    def test_container_entry_uses_same_adapter(self):
        other_spec = importlib.util.spec_from_file_location(
            "mrl_container", ROOT / "MRL_Mother/09_workflow/MRL__Flowcore_Loop_2.py")
        other = importlib.util.module_from_spec(other_spec)
        other_spec.loader.exec_module(other)
        other_tracer = other.Tracer(self.temp.name)
        version = other_tracer.timeMachine.saveVersion({"x": 1}, "v1.0")
        self.assertEqual(other_tracer.mountVersion(1), version)
        branch = other_tracer.branchFrom(1)
        branch.commit({"x": 2}, "v2.0")
        self.assertEqual(len(other_tracer.diffVersions(1, 2)), 1)

    def test_http_authorization_mount_and_branch(self):
        self.initial()
        vault = runtime.Vault(self.temp.name)
        handler = runtime.make_handler(vault, self.tracer, runtime.SteeringStore(self.temp.name))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        old_token = runtime.HUMAN_TOKEN
        runtime.HUMAN_TOKEN = "test-only"
        self.addCleanup(setattr, runtime, "HUMAN_TOKEN", old_token)

        def post(op, body, token="test-only"):
            req = Request(f"http://127.0.0.1:{server.server_port}/timemachine/{op}",
                          data=json.dumps(body).encode(), headers={"X-Human-Token": token})
            with urlopen(req) as response:
                return json.load(response)["data"]

        with self.assertRaises(HTTPError) as denied:
            post("mountVersion", {"version_id": 1}, "wrong")
        self.assertEqual(denied.exception.code, 403)
        self.assertEqual(post("mountVersion", {"version_id": 1})["timestamp"], 1)
        branch = post("branchFrom", {"version_id": 1})
        b = post("saveVersion", dict(snapshot={"x": 2}, version_string="v2.0", **branch))
        self.assertEqual(b["version_index"], 2)
        self.assertTrue(post("diffVersions", {"v1": 1, "v2": 2}))


if __name__ == "__main__":
    unittest.main()
