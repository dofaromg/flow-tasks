"""Adversarial financial invariants; all keys generated temporarily for tests."""

import copy
from contextlib import closing
import concurrent.futures
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .cli import read_json
from .core import Ledger, Rejected, canonical, policy_hash, register_tools


class ClockLedger(Ledger):
    clock = 1000

    def _now(self):
        return self.clock


class FinancialCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.keys = [Ed25519PrivateKey.generate() for _ in range(6)]
        self.public = [key.public_key().public_bytes_raw().hex() for key in self.keys]
        self.policy = {
            "ledger_id": "MRL_test_finance", "origin_signature": "MrLiouWord",
            "council_keys": self.public[:3], "quorum": 2, "assets": ["MRL_TEST"],
            "settlement_delay": 10, "review_delay": 20, "max_request_lifetime": 60,
        }
        self.db = Path(self.temp.name) / "ledger.sqlite"
        self.ledger = ClockLedger.create(self.db, self.policy)
        self.ledger.clock = 1000
        self.counter = 0
        for name, index in (("alice", 3), ("bob", 4), ("carol", 5)):
            self.send("open_account", {"account": name, "owner_key": self.public[index]}, [0, 1])
        self.send("issue", {"account": "alice", "asset": "MRL_TEST", "amount": 100,
                            "evidence_sha256": "a" * 64}, [0, 1])

    def request(self, action, payload):
        self.counter += 1
        return {"version": 1, "ledger_id": self.policy["ledger_id"],
                "policy_sha256": policy_hash(self.policy), "request_id": f"r{self.counter}",
                "issued_at": self.ledger.clock, "expires_at": self.ledger.clock + 60,
                "action": action, "payload": payload}

    def signatures(self, request, indices):
        return {self.public[i]: self.keys[i].sign(canonical(request)).hex() for i in indices}

    def send(self, action, payload, indices):
        request = self.request(action, payload)
        return self.ledger.submit(request, self.signatures(request, indices))

    def transfer(self, amount=60):
        self.send("propose", {"transfer": "t1", "source": "alice", "destination": "bob",
                              "asset": "MRL_TEST", "amount": amount}, [3])

    def settle(self):
        self.ledger.clock += 10
        self.send("settle", {"transfer": "t1"}, [3])

    def dispute(self):
        self.send("dispute", {"transfer": "t1", "evidence_sha256": "b" * 64}, [3])

    def resolve(self, decision="refund"):
        self.send("resolve", {"transfer": "t1", "decision": decision,
                              "evidence_sha256": "c" * 64}, [0, 1])

    def state(self):
        return self.ledger.snapshot()["state"]

    def test_settled_refund_preserves_original_and_balances(self):
        self.transfer()
        self.settle()
        self.dispute()
        self.ledger.clock += 20
        self.resolve()
        state = self.state()
        self.assertEqual(state["balances"]["alice"]["MRL_TEST"], 100)
        self.assertEqual(state["balances"]["bob"]["MRL_TEST"], 0)
        self.assertEqual(len(state["postings"]), 6)
        self.assertEqual(sum(p["delta"] for p in state["postings"]), 0)
        self.assertEqual(state["transfers"]["t1"]["status"], "refunded")

    def test_delay_and_dispute_prevent_settlement(self):
        self.transfer()
        with self.assertRaisesRegex(Rejected, "SETTLEMENT_DELAY"):
            self.send("settle", {"transfer": "t1"}, [3])
        self.dispute()
        self.ledger.clock += 30
        with self.assertRaisesRegex(Rejected, "NOT_SETTLEABLE"):
            self.send("settle", {"transfer": "t1"}, [3])

    def test_pending_refund_releases_reservation_without_mint(self):
        self.transfer()
        self.dispute()
        self.ledger.clock += 20
        self.resolve()
        state = self.state()
        self.assertEqual(state["transfers"]["t1"]["status"], "cancelled")
        self.assertEqual(len(state["postings"]), 2)
        self.send("propose", {"transfer": "t2", "source": "alice", "destination": "carol",
                              "asset": "MRL_TEST", "amount": 100}, [3])

    def test_reservations_prevent_double_spend(self):
        self.transfer()
        with self.assertRaisesRegex(Rejected, "INSUFFICIENT_AVAILABLE"):
            self.send("propose", {"transfer": "t2", "source": "alice", "destination": "carol",
                                  "asset": "MRL_TEST", "amount": 60}, [3])

    def test_disputed_received_units_are_reserved(self):
        self.transfer()
        self.settle()
        self.dispute()
        with self.assertRaisesRegex(Rejected, "INSUFFICIENT_AVAILABLE"):
            self.send("propose", {"transfer": "t2", "source": "bob", "destination": "carol",
                                  "asset": "MRL_TEST", "amount": 1}, [4])

    def test_shortfall_does_not_create_money_or_close_case(self):
        self.transfer()
        self.settle()
        self.send("propose", {"transfer": "t2", "source": "bob", "destination": "carol",
                              "asset": "MRL_TEST", "amount": 60}, [4])
        self.ledger.clock += 10
        self.send("settle", {"transfer": "t2"}, [4])
        self.dispute()
        self.ledger.clock += 20
        before = self.ledger.snapshot()
        with self.assertRaisesRegex(Rejected, "RETURN_SHORTFALL"):
            self.resolve()
        self.assertEqual(self.ledger.snapshot(), before)

    def test_single_council_member_cannot_issue_or_resolve(self):
        with self.assertRaisesRegex(Rejected, "QUORUM"):
            self.send("issue", {"account": "bob", "asset": "MRL_TEST", "amount": 1,
                                "evidence_sha256": "a" * 64}, [0])
        self.transfer()
        self.dispute()
        self.ledger.clock += 20
        with self.assertRaisesRegex(Rejected, "QUORUM"):
            self.send("resolve", {"transfer": "t1", "decision": "refund",
                                  "evidence_sha256": "a" * 64}, [0])

    def test_tampered_signature_and_wrong_owner_rejected(self):
        request = self.request("issue", {"account": "bob", "asset": "MRL_TEST",
                                         "amount": 1, "evidence_sha256": "a" * 64})
        sigs = self.signatures(request, [0, 1])
        request["payload"]["amount"] = 2
        with self.assertRaisesRegex(Rejected, "INVALID_SIGNATURE"):
            self.ledger.submit(request, sigs)
        with self.assertRaisesRegex(Rejected, "OWNER_SIGNATURE"):
            self.send("propose", {"transfer": "t1", "source": "alice", "destination": "bob",
                                  "asset": "MRL_TEST", "amount": 1}, [4])

    def test_replayed_request_rejected(self):
        request = self.request("propose", {"transfer": "t1", "source": "alice", "destination": "bob",
                                           "asset": "MRL_TEST", "amount": 1})
        sigs = self.signatures(request, [3])
        self.ledger.submit(request, sigs)
        with self.assertRaisesRegex(Rejected, "REQUEST_REPLAY"):
            self.ledger.submit(request, sigs)

    def test_expiry_domain_and_clock_regression(self):
        for mutation, reason in (({"expires_at": 1000}, "REQUEST_TIME"),
                                 ({"ledger_id": "another_ledger"}, "WRONG_SIGNING_DOMAIN")):
            request = self.request("settle", {"transfer": "missing"})
            request.update(mutation)
            with self.assertRaisesRegex(Rejected, reason):
                self.ledger.submit(request, self.signatures(request, [3]))
        self.ledger.clock = 999
        with self.assertRaisesRegex(Rejected, "CLOCK_REGRESSION"):
            self.transfer()

    def test_bool_negative_float_and_zero_amounts_rejected(self):
        for amount in (True, -1, 0, 1.5):
            with self.subTest(amount=amount), self.assertRaisesRegex(Rejected, "INVALID_AMOUNT"):
                self.transfer(amount)

    def test_appeal_extends_review_and_cannot_loop(self):
        self.transfer()
        self.dispute()
        self.send("appeal", {"transfer": "t1", "evidence_sha256": "d" * 64}, [4])
        self.ledger.clock += 20
        with self.assertRaisesRegex(Rejected, "CASE_NOT_READY"):
            self.resolve()
        with self.assertRaisesRegex(Rejected, "APPEAL_UNAVAILABLE"):
            self.send("appeal", {"transfer": "t1", "evidence_sha256": "d" * 64}, [4])
        self.ledger.clock += 20
        self.resolve("release")
        self.send("settle", {"transfer": "t1"}, [3])

    def test_policy_pin_and_rollback_checkpoint(self):
        modified = copy.deepcopy(self.policy)
        modified["review_delay"] = 1
        with self.assertRaisesRegex(Rejected, "POLICY_MISMATCH"):
            ClockLedger(self.db, modified).snapshot()
        old = self.ledger.snapshot()["head"]
        self.transfer()
        with self.assertRaisesRegex(Rejected, "CHECKPOINT_MISMATCH"):
            self.ledger.snapshot(old)

    def test_append_only_and_tamper_detection(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("DELETE FROM events WHERE seq=2")
            db.execute("DROP TRIGGER immutable_update")
            db.execute("UPDATE events SET body='{}' WHERE seq=2")
        with self.assertRaisesRegex(Rejected, "BROKEN_EVENT_CHAIN"):
            self.ledger.snapshot()

    def test_invalid_policy_and_create_only(self):
        with self.assertRaises(FileExistsError):
            ClockLedger.create(self.db, self.policy)
        for field, value in (("quorum", 1), ("council_keys", [self.public[0]] * 3),
                             ("settlement_delay", 0)):
            policy = {**self.policy, field: value}
            with self.assertRaises(Rejected):
                ClockLedger(self.db, policy)

    def test_unknown_fields_rejected_and_cli_duplicate_keys(self):
        request = self.request("issue", {"account": "bob", "asset": "MRL_TEST", "amount": 1,
                                         "evidence_sha256": "a" * 64, "force": True})
        with self.assertRaisesRegex(Rejected, "PAYLOAD_SCHEMA"):
            self.ledger.submit(request, self.signatures(request, [0, 1]))
        path = Path(self.temp.name) / "duplicate.json"
        path.write_text('{"a":1,"a":2}', encoding="utf-8")
        with self.assertRaisesRegex(Rejected, "DUPLICATE_JSON_KEY"):
            read_json(path)

    def test_existing_mother_tool_registry_integration(self):
        path = Path(__file__).resolve().parents[2] / "09_workflow" / "tool_registry.py"
        spec = importlib.util.spec_from_file_location("mrl_existing_tools", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        registry = module.ToolRegistry()
        register_tools(registry, self.ledger)
        self.assertEqual(len(registry.list_tools()), 2)
        result = registry.call("MRL_financial_snapshot", {})
        self.assertTrue(result["ok"])
        self.assertEqual(result["output"]["mode"], "SANDBOX_UNITS_ONLY")
        result = registry.call("MRL_financial_submit", {"request": {}, "signatures": {}})
        self.assertFalse(result["ok"])
        with self.assertRaisesRegex(Rejected, "TOOL_ALREADY_REGISTERED"):
            register_tools(registry, self.ledger)

    def test_concurrent_reservations_are_serialized(self):
        requests = [self.request("propose", {"transfer": f"t{i}", "source": "alice",
                    "destination": "bob", "asset": "MRL_TEST", "amount": 70}) for i in range(2)]

        def attempt(request):
            ledger = ClockLedger(self.db, self.policy)
            try:
                ledger.submit(request, self.signatures(request, [3]))
                return "ACCEPTED"
            except Rejected as exc:
                return str(exc)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(attempt, requests))
        self.assertEqual(sorted(results), ["ACCEPTED", "INSUFFICIENT_AVAILABLE"])
        self.assertEqual(len(self.state()["transfers"]), 1)

    def test_external_head_detects_restored_old_database(self):
        backup = Path(self.temp.name) / "before.sqlite"
        with closing(sqlite3.connect(self.db)) as source, closing(sqlite3.connect(backup)) as target:
            source.backup(target)
        self.transfer()
        head = self.ledger.snapshot()["head"]
        with closing(sqlite3.connect(backup)) as source, closing(sqlite3.connect(self.db)) as target:
            source.backup(target)
        with self.assertRaisesRegex(Rejected, "CHECKPOINT_MISMATCH"):
            self.ledger.snapshot(head)


if __name__ == "__main__":
    unittest.main()
