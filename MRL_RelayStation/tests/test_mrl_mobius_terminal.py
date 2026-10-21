import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "runtime" / "mrl_mobius_terminal.py"
SPEC = importlib.util.spec_from_file_location("mrl_mobius_terminal", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["mrl_mobius_terminal"] = module
SPEC.loader.exec_module(module)


class MobiusTerminalTests(unittest.TestCase):
    def test_valid_chain_and_reverse_replay(self):
        first = module.create_event(
            name="mrl.mobius.trace.0001",
            sequence=0,
            operation="ingest",
            domain="event",
            authority_level="L0",
            depth=0,
            twist=0,
            payload={"value": 1},
            previous_hash="GENESIS",
        )
        second = module.create_event(
            name="mrl.mobius.trace.0002",
            sequence=1,
            operation="rotate",
            domain="knowledge",
            authority_level="L1",
            depth=1,
            twist=1,
            payload={"value": 2},
            previous_hash=first.record_hash,
        )
        events = [first, second]
        self.assertEqual(module.verify_chain(events), [])
        reverse = module.replay(events, reverse=True)
        self.assertEqual(reverse[0]["sequence"], 1)
        self.assertEqual(reverse[-1]["sequence"], 0)

    def test_non_mrl_name_is_rejected(self):
        with self.assertRaises(ValueError):
            module.create_event(
                name="random-terminal",
                sequence=0,
                operation="ingest",
                domain="event",
                authority_level="L0",
                depth=0,
                twist=0,
                payload={},
                previous_hash="GENESIS",
            )

    def test_only_dofaromg_can_promote(self):
        event = module.create_event(
            name="MRL_MobiusTrace_0001",
            sequence=0,
            operation="verify",
            domain="authority",
            authority_level="L2",
            depth=0,
            twist=0,
            payload={},
            previous_hash="GENESIS",
        )
        with self.assertRaises(PermissionError):
            module.promote([event], "other")
        result = module.promote([event], "dofaromg")
        self.assertTrue(result["construction_allowed"])
        self.assertEqual(result["authority_account"], "dofaromg")

    def test_tampered_chain_fails(self):
        event = module.create_event(
            name="mrl.mobius.trace.0001",
            sequence=0,
            operation="ingest",
            domain="event",
            authority_level="L0",
            depth=0,
            twist=0,
            payload={},
            previous_hash="WRONG",
        )
        self.assertTrue(module.verify_chain([event]))

    def test_append_and_read(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "chain.jsonl"
            event = module.create_event(
                name="mrl.mobius.trace.0001",
                sequence=0,
                operation="ingest",
                domain="product",
                authority_level="L0",
                depth=0,
                twist=0,
                payload={"product": "terminal"},
                previous_hash="GENESIS",
            )
            module.append_event(ledger, event)
            loaded = module.read_events(ledger)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].record_hash, event.record_hash)


if __name__ == "__main__":
    unittest.main()
