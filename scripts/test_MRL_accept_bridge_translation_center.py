"""Acceptance regressions: synthetic fixtures can never certify this host.

origin_signature: MrLiouWord
"""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from MRL_Bridge.translation_center import TranslationCenter

spec = importlib.util.spec_from_file_location("mrl_accept", Path(__file__).with_name("MRL_accept_bridge_translation_center.py"))
accept = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accept)


class AcceptanceTests(unittest.TestCase):
    def test_off_host_cannot_issue_a_live_acceptance_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory = Path(directory) / 'inventory.json'
            inventory.write_text('{}')
            with patch.object(accept.platform, 'system', return_value='Linux'):
                with self.assertRaisesRegex(ValueError, 'actual DL580'):
                    accept.run(SimpleNamespace(inventory=str(inventory)))

    def test_intact_and_tampered_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.jsonl"
            center = TranslationCenter(path)
            center.label(b"fixture", source_ref="MRL.test", destination_ref="MRL.test")
            self.assertEqual(len(accept.read_chain(path)), 1)
            path.write_text(path.read_text().replace('"mrl_affiliation":"MRL"', '"mrl_affiliation":"OTHER"'))
            with self.assertRaises(ValueError):
                accept.read_chain(path)

    def test_truncated_chain_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.jsonl"
            path.write_bytes(b'{"sequence":0')
            with self.assertRaises(ValueError):
                accept.read_chain(path)

    def test_streamed_hashes_and_parent_chain_are_required(self):
        center = TranslationCenter()
        first = center.label(b"", source_ref="external", destination_ref="MRL", status="started")
        second = center.label(b"request", source_ref="external", destination_ref="MRL", status="received", trace_id=first["trace_id"], parent_ref=first["event_id"])
        last = center.label(b"response", source_ref="MRL", destination_ref="external", status="sent", trace_id=first["trace_id"], parent_ref=second["event_id"], http_status=401)
        records = list(center.records)
        accept.check_trace(records, first["trace_id"], b"request", b"response", 401)
        with self.assertRaises(ValueError):
            accept.check_trace(records, first["trace_id"], b"wrong", b"response", 401)
        last["parent_ref"] = "wrong"
        records[-1] = last
        with self.assertRaises(ValueError):
            accept.check_trace(records, first["trace_id"], b"request", b"response", 401)

    def python_fixture(self):
        now = datetime.now(timezone.utc)
        since = now - timedelta(minutes=1)
        center = TranslationCenter()
        trace = "mobius-fixture"
        parent = None
        for source in ("MRL.Mobius.R", "MRL.Mobius.route", "MRL.Mobius.collapse", "MRL.Mobius.A"):
            record = center.label(b"fixture", source_ref=source, destination_ref="MRL.fixture", trace_id=trace, parent_ref=parent)
            parent = record["event_id"]
        out = center.label(b"request", source_ref="MRL.connector", destination_ref="fixture", status="dispatching")
        center.label(b"response", source_ref="fixture", destination_ref="MRL.connector", status="received", trace_id=out["trace_id"], parent_ref=out["event_id"], http_status=200)
        records = list(center.records)
        proof = records[0]["runtime_evidence"]
        loaded = now - timedelta(seconds=10)
        for record in records:
            record["runtime_evidence"]["module_loaded_at"] = loaded.isoformat()
        processes = [{"pid": os.getpid(), "created_at": (loaded - timedelta(seconds=1)).isoformat(), "executable": proof["executable"], "service_owned": True}]
        args = (records, processes, proof["module_sha256_lf"], proof["module_path"], since, datetime.now(timezone.utc))
        return args

    def test_python_requires_live_service_reload_and_full_activity(self):
        args = self.python_fixture()
        self.assertTrue(accept.python_evidence(*args)["pass"])
        args[1][0]["service_owned"] = False
        self.assertFalse(accept.python_evidence(*args)["pass"])
        args[1][0]["service_owned"] = True
        args[1][0]["created_at"] = (args[4] - timedelta(seconds=1)).isoformat()
        self.assertFalse(accept.python_evidence(*args)["pass"])

    def test_wrong_loaded_module_hash_and_missing_connector_fail(self):
        args = self.python_fixture()
        self.assertFalse(accept.python_evidence(args[0], args[1], '0' * 64, *args[3:])["pass"])
        self.assertFalse(accept.python_evidence(args[0][:4], *args[1:])["pass"])
        self.assertFalse(accept.python_evidence(args[0][1:], *args[1:])["pass"])

    def test_dispatch_without_result_and_broken_mobius_chain_fail(self):
        args = self.python_fixture()
        self.assertFalse(accept.python_evidence(args[0][:-1], *args[1:])["pass"])
        args[0][2]["parent_ref"] = "broken"
        self.assertFalse(accept.python_evidence(*args)["pass"])

    def test_future_and_wrong_interpreter_evidence_fail(self):
        args = self.python_fixture()
        args[1][0]["executable"] += ".other"
        self.assertFalse(accept.python_evidence(*args)["pass"])
        args = self.python_fixture()
        for record in args[0]:
            record["timestamp"] = (args[-1] + timedelta(seconds=1)).isoformat()
        self.assertFalse(accept.python_evidence(*args)["pass"])

    def test_retained_subset_still_checks_entire_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.jsonl"
            center = TranslationCenter(path)
            for n in range(3):
                center.label(n, source_ref="MRL.test", destination_ref="MRL.test")
            self.assertEqual(len(accept.read_chain(path, lambda r: r["sequence"] == 2)), 1)
            lines = path.read_text().splitlines()
            lines[0] = lines[0].replace('"mrl_affiliation":"MRL"', '"mrl_affiliation":"OTHER"')
            path.write_text("\n".join(lines) + "\n")
            with self.assertRaises(ValueError):
                accept.read_chain(path, lambda r: r["sequence"] == 2)

    def test_memory_only_does_not_become_durable_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.jsonl"
            record = TranslationCenter().label(b"fixture", source_ref="MRL.test", destination_ref="MRL.test")
            path.write_bytes(accept.canonical(record) + b"\n")
            with self.assertRaises(ValueError):
                accept.read_chain(path)

    def test_runtime_module_fingerprint_is_captured_at_import(self):
        from MRL_Bridge import translation_center
        record = TranslationCenter().label(b"fixture", source_ref="MRL.test", destination_ref="MRL.test")
        proof = record["runtime_evidence"]
        self.assertEqual(proof["process_id"], os.getpid())
        self.assertEqual(proof["module_sha256_lf"], hashlib.sha256(Path(translation_center.__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest())
        with patch.object(Path, "read_bytes", side_effect=AssertionError("must not re-read a potentially replaced module")):
            next_record = TranslationCenter().label(b"next", source_ref="MRL.test", destination_ref="MRL.test")
        self.assertEqual(proof["module_sha256_lf"], next_record["runtime_evidence"]["module_sha256_lf"])


if __name__ == "__main__":
    unittest.main()
