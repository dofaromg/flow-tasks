"""MRL橋接轉譯中心 acceptance tests. origin_signature: MrLiouWord"""
import hashlib
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from MRL_Bridge.translation_center import TranslationCenter


class CenterTests(unittest.TestCase):
    def label(self, center, payload, **extra):
        return center.label(payload, source_ref="MRL.test", destination_ref="external", **extra)

    def test_original_code_and_external_signature_are_preserved(self):
        payload = {"filename": "original.py", "code": "print('MRL')\n", "origin_signature": "external-author"}
        envelope = TranslationCenter().envelope(payload, source_ref="external", destination_ref="MRL")
        self.assertIs(envelope["payload"], payload)
        self.assertEqual(payload["origin_signature"], "external-author")
        self.assertEqual(envelope["mrl_bridge"]["mrl_affiliation"], "MRL")
        self.assertIsNone(envelope["mrl_bridge"]["payload_origin_signature"])

    def test_binary_content_hash(self):
        raw = b"\x00\xffMRL\r\n"
        record = self.label(TranslationCenter(), raw)
        self.assertEqual(record["payload_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(record["hash_scope"], "bytes")

    def test_receipt_links_do_not_claim_delivery(self):
        center = TranslationCenter()
        first = self.label(center, {"code": 1}, status="dispatching")
        second = center.label(b"denied", source_ref="external", destination_ref="MRL",
                              direction="external_to_mrl", trace_id=first["trace_id"],
                              parent_ref=first["event_id"], http_status=403, status="received")
        self.assertEqual(second["trace_id"], first["trace_id"])
        self.assertEqual(second["parent_ref"], first["event_id"])
        self.assertEqual(second["http_status"], 403)
        self.assertEqual(second["status"], "received")

    def test_concurrent_append_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            center = TranslationCenter(path)
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda n: self.label(center, {"n": n}), range(40)))
            reopened = TranslationCenter(path)
            self.assertEqual(len(reopened.records), 40)
            last = self.label(reopened, b"new")
            self.assertEqual(last["sequence"], 40)
            self.assertEqual(last["previous_sha256"], center.records[-1]["record_sha256"])

    def test_tampered_ledger_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            self.label(TranslationCenter(path), "original")
            text = path.read_text().replace('"mrl_affiliation":"MRL"', '"mrl_affiliation":"OTHER"')
            path.write_text(text)
            with self.assertRaises(ValueError):
                TranslationCenter(path)

    def test_payload_and_secrets_not_written_to_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            self.label(TranslationCenter(path), {"token": "DO_NOT_STORE_THIS"})
            self.assertNotIn("DO_NOT_STORE_THIS", path.read_text())

    def test_memory_is_bounded_and_explicit(self):
        center = TranslationCenter()
        for n in range(1030):
            record = self.label(center, n)
        self.assertEqual(len(center.records), 1024)
        self.assertEqual(record["storage"], "memory-only")

    def test_invalid_direction_is_rejected(self):
        with self.assertRaises(ValueError):
            self.label(TranslationCenter(), 1, direction="unknown")

    def test_non_json_value_does_not_get_silently_coerced(self):
        with self.assertRaises(TypeError):
            self.label(TranslationCenter(), object())

    def test_mobius_keeps_classification_and_adds_boundary_chain(self):
        import sys
        workflow = Path(__file__).resolve().parents[1] / "MRL_Mother" / "09_workflow"
        sys.path.insert(0, str(workflow))
        from MRL_Mobius_Closure_Engine_v1 import MobiusClosureEngine
        center = TranslationCenter()
        engine = MobiusClosureEngine(lambda r: r, lambda a: a, lambda a: a)
        engine.bridge_center = center
        self.assertEqual(engine.classify({"v": 42})["verdict"], "REAL")
        records = list(center.records)
        self.assertEqual(len(records), 4)
        self.assertEqual(len({r["trace_id"] for r in records}), 1)
        for previous, current in zip(records, records[1:]):
            self.assertEqual(current["parent_ref"], previous["event_id"])

    def test_mobius_failure_is_tagged_and_propagated(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "MRL_Mother" / "09_workflow"))
        from MRL_Mobius_Closure_Engine_v1 import MobiusClosureEngine
        def fail(value):
            raise RuntimeError("boundary failed")
        center = TranslationCenter()
        engine = MobiusClosureEngine(fail, lambda a: a, lambda a: a)
        engine.bridge_center = center
        with self.assertRaises(RuntimeError):
            engine.roundtrip({"v": 1})
        self.assertEqual(center.records[-1]["status"], "operation_error")
        self.assertEqual(engine.log, [])

    def test_non_json_mobius_states_keep_historical_behavior(self):
        import sys
        from datetime import datetime, timezone
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "MRL_Mother" / "09_workflow"))
        from MRL_Mobius_Closure_Engine_v1 import MobiusClosureEngine, _hash
        for value in ({1, 2}, datetime(2026, 10, 19, tzinfo=timezone.utc), object()):
            with self.subTest(value=type(value).__name__):
                center = TranslationCenter()
                engine = MobiusClosureEngine(lambda r: r, lambda a: a, lambda a: a)
                engine.bridge_center = center
                self.assertEqual(engine.classify(value)["verdict"], "REAL")
                self.assertEqual(center.records[0]["payload_sha256"], _hash(value))


if __name__ == "__main__":
    unittest.main()
