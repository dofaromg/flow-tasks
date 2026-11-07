"""Public-key/provider fixtures only; no network or live accounts in these tests."""

import concurrent.futures
from contextlib import closing
import copy
from decimal import Decimal
import getpass
import importlib.util
import json
import os
import sqlite3
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlsplit

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
try:
    from eth_account import Account
    from eth_utils import keccak
    from hexbytes import HexBytes
    from .gateway import Gateway, register_external_tools
    HAS_EXTERNAL_DEPENDENCIES = True
except ModuleNotFoundError as exc:
    if exc.name != "eth_account":
        raise
    HAS_EXTERNAL_DEPENDENCIES = False

from ..core import Rejected, canonical
from .gate import default_settings
from .transport import JsonTransport, NoRedirect, https_url

ACCOUNT = "00000000-0000-4000-8000-000000000001"
RECIPIENT = "00000000-0000-4000-8000-000000000002"


class FakeTransport:
    def __init__(self, source, destination):
        self.source, self.destination = source, destination
        self.calls = []
        self.chain = 11155111
        self.code = "0x"
        self.nonce = 0
        self.fail_write = False
        self.wrong_bank_response = False
        self.receipt = None

    def request(self, method, url, body=None, headers=None):
        self.calls.append((method, url, body, headers))
        if urlsplit(url).hostname in {"api.mercury.com", "api-sandbox.mercury.com"}:
            if method == "GET":
                return {"id": ACCOUNT, "currentBalance": Decimal("123.45"),
                        "availableBalance": Decimal("120.00"), "accountNumber": "DO_NOT_RETURN"}
            data = json.loads(body, parse_float=Decimal)
            if self.fail_write:
                raise OSError("sensitive fake provider response")
            return {"accountId": ACCOUNT, "recipientId": RECIPIENT, "paymentMethod": "ach",
                    "amount": Decimal("999.99") if self.wrong_bank_response else data["amount"],
                    "requestId": "provider-request-1", "status": "pendingApproval"}
        request = json.loads(body)
        method, p = request["method"], request["params"]
        values = {"eth_chainId": hex(self.chain), "eth_getCode": self.code,
                  "eth_getTransactionCount": hex(self.nonce), "eth_getBalance": hex(10**18),
                  "eth_getTransactionReceipt": self.receipt,
                  "eth_getTransactionByHash": {"hash": p[0] if p else "", "from": self.source}}
        if method == "eth_sendRawTransaction":
            if self.fail_write:
                raise OSError("submission timeout")
            value = "0x" + keccak(HexBytes(p[0])).hex()
        else:
            value = values[method]
        return {"jsonrpc": "2.0", "id": 1, "result": value}


@unittest.skipUnless(HAS_EXTERNAL_DEPENDENCIES, "Install optional external/requirements.txt")
class ExternalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.keys = [Ed25519PrivateKey.generate() for _ in range(3)]
        self.policy = {"ledger_id": "MRL_external_test", "origin_signature": "MrLiouWord",
                       "council_keys": [k.public_key().public_bytes_raw().hex() for k in self.keys],
                       "quorum": 2, "assets": ["MRL_TEST"], "settlement_delay": 10,
                       "review_delay": 20, "max_request_lifetime": 60}
        self.wallet = Account.create()
        self.destination = Account.create().address.lower()
        self.settings = default_settings(self.policy)
        self.settings["writes_enabled"] = True
        self.settings["mercury"].update(accounts=[ACCOUNT], recipients=[RECIPIENT])
        self.settings["evm"].update(rpc_url="https://rpc.example.invalid",
                                    wallets=[self.wallet.address.lower()], recipients=[self.destination])
        self.root = {"root_authority": "Mr.liou", "origin_signature": "MrLiouWord",
                     "authorization_model": {"default_decision": "DENY", "explicit_grant_required": True,
                                             "implicit_authorization_allowed": False},
                     "active_grants": [], "financial_external_grants": []}
        self.root_path = self.directory / "root.json"
        for action, resource, dest, environment in (
            ("financial.mercury.read", "mercury:" + ACCOUNT, "local-operator", "mercury-sandbox"),
            ("financial.mercury.request_ach", "mercury:" + ACCOUNT,
             "mercury-recipient:" + RECIPIENT, "mercury-sandbox"),
            ("financial.evm.read", "evm:11155111:" + self.wallet.address.lower(), "local-operator", "evm-sepolia"),
            ("financial.evm.send_native", "evm:11155111:" + self.wallet.address.lower(),
             "evm:11155111:" + self.destination, "evm-sepolia"),
        ):
            self.root["financial_external_grants"].append({
                "record_id": "test_grant_" + str(len(self.root["financial_external_grants"])),
                "issued_by": "MrLiouWord", "actor": "local:" + getpass.getuser(),
                "issued_at": "1970-01-01T00:00:00Z", "expires_at": "2100-01-01T00:00:00Z",
                "status": "active", "action": action, "resource": resource,
                "destination": dest, "environment": environment, "evidence_reference": "TEST_FIXTURE_ONLY"})
        self.write_root()
        self.transport = FakeTransport(self.wallet.address.lower(), self.destination)
        self.gateway = self.make_gateway()
        self.gateway.gate.initialize_journal()
        self.env = patch.dict(os.environ, {"MRL_MERCURY_API_TOKEN": "FAKE_TEST_TOKEN"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def make_gateway(self, settings=None, enable_live=False):
        result = Gateway(self.policy, settings or self.settings, self.root_path,
                         self.directory / "journal.sqlite", enable_live, self.transport)
        result.gate.now = lambda: 1000
        return result

    def write_root(self):
        self.root_path.write_text(json.dumps(self.root), encoding="utf-8")

    def bank_operation(self):
        return {"kind": "mercury.request_ach", "environment": "mercury-sandbox",
                "account": ACCOUNT, "recipient": RECIPIENT, "amount_cents": 1234}

    def wallet_operation(self):
        return {"kind": "evm.native_transfer", "environment": "evm-sepolia",
                "source": self.wallet.address.lower(),
                "transaction": {"type": 2, "chainId": 11155111, "nonce": 0,
                    "to": self.destination, "value": 1000, "gas": 21000,
                    "maxFeePerGas": 200, "maxPriorityFeePerGas": 1, "data": "0x", "accessList": []}}

    def approved(self, operation=None, request_id="request1", indices=(0, 1)):
        envelope = self.gateway.plan(operation or self.bank_operation(), request_id)
        signatures = {self.policy["council_keys"][i]: self.keys[i].sign(canonical(envelope)).hex()
                      for i in indices}
        return envelope, signatures

    def signed_raw(self, operation, wallet=None):
        transaction = copy.deepcopy(operation["transaction"])
        transaction["to"] = HexBytes(transaction["to"])
        signed = Account.sign_transaction(transaction, (wallet or self.wallet).key)
        return "0x" + signed.raw_transaction.hex()

    def writes(self):
        return [c for c in self.transport.calls if c[0] == "POST" and
                (urlsplit(c[1]).hostname in {"api.mercury.com", "api-sandbox.mercury.com"} or
                 json.loads(c[2])["method"] == "eth_sendRawTransaction")]

    def test_bank_official_approval_path_and_fixed_point(self):
        request, sigs = self.approved()
        receipt = self.gateway.submit(request, sigs)
        call = self.writes()[0]
        self.assertTrue(call[1].endswith("/request-send-money"))
        self.assertIn(b'"amount":12.34', call[2])
        self.assertEqual(receipt["state"], "BANK_REQUEST_RECORDED")
        self.assertEqual(receipt["provider_status"], "pendingApproval")
        self.assertFalse(receipt["settlement_verified"])
        self.assertFalse(receipt["sandbox_ledger_credited"])
        journal = (self.directory / "journal.sqlite").read_bytes()
        self.assertNotIn(b"FAKE_TEST_TOKEN", journal)
        self.assertEqual(self.gateway.gate.status("request1")["state"], "BANK_REQUEST_RECORDED")

    def test_no_root_grants_no_provider_call(self):
        self.root.pop("financial_external_grants")
        self.write_root()
        with self.assertRaisesRegex(Rejected, "NO_UNIQUE_EXTERNAL_ROOT_GRANT"):
            self.gateway.plan(self.bank_operation(), "test")
        self.assertEqual(self.transport.calls, [])

    def test_scope_expiry_wrong_actor_and_duplicate_grants(self):
        original = copy.deepcopy(self.root)
        for field, value in (("actor", "someone_else"), ("expires_at", "1970-01-01T00:01:00Z"),
                             ("destination", "anywhere"), ("status", "revoked")):
            self.root = copy.deepcopy(original)
            self.root["financial_external_grants"][1][field] = value
            self.write_root()
            with self.assertRaisesRegex(Rejected, "NO_UNIQUE_EXTERNAL_ROOT_GRANT"):
                self.gateway.plan(self.bank_operation(), "test")
        self.root = copy.deepcopy(original)
        self.root["financial_external_grants"].append(copy.deepcopy(self.root["financial_external_grants"][1]))
        self.write_root()
        with self.assertRaisesRegex(Rejected, "NO_UNIQUE_EXTERNAL_ROOT_GRANT"):
            self.gateway.plan(self.bank_operation(), "test")

    def test_default_disabled_and_live_two_switches(self):
        disabled = copy.deepcopy(self.settings)
        disabled["writes_enabled"] = False
        gateway = self.make_gateway(disabled)
        request, sigs = self.approved()
        with self.assertRaisesRegex(Rejected, "EXTERNAL_WRITES_DISABLED"):
            gateway.submit(request, sigs)
        for file_switch, runtime_switch in ((False, False), (False, True), (True, False)):
            live = copy.deepcopy(self.settings)
            live["allow_live"] = file_switch
            live["mercury"]["environment"] = "live"
            gateway = self.make_gateway(live, runtime_switch)
            operation = self.bank_operation()
            operation["environment"] = "mercury-live"
            with self.assertRaisesRegex(Rejected, "LIVE_ACCESS_DISABLED"):
                gateway.plan(operation, "live")
        self.assertEqual(self.writes(), [])

    def test_threshold_tampering_domain_and_expiry(self):
        request, sigs = self.approved(indices=(0,))
        with self.assertRaisesRegex(Rejected, "QUORUM"):
            self.gateway.submit(request, sigs)
        request, sigs = self.approved()
        request["operation"]["amount_cents"] = 1235
        with self.assertRaisesRegex(Rejected, "INVALID_SIGNATURE"):
            self.gateway.submit(request, sigs)
        for key, value, reason in (("ledger_id", "another", "DOMAIN"),
                                   ("expires_at", 999, "TIME")):
            request, sigs = self.approved()
            request[key] = value
            with self.assertRaisesRegex(Rejected, reason):
                self.gateway.submit(request, sigs)
        self.assertEqual(self.writes(), [])

    def test_revocation_after_signing_is_effective(self):
        request, sigs = self.approved()
        self.root["financial_external_grants"][1]["status"] = "revoked"
        self.write_root()
        with self.assertRaisesRegex(Rejected, "DOMAIN"):
            self.gateway.submit(request, sigs)
        self.assertEqual(self.writes(), [])

    def test_bank_allowlist_and_integer_limits(self):
        for field, value in (("account", "00000000-0000-4000-8000-000000000003"),
                             ("recipient", "00000000-0000-4000-8000-000000000003"),
                             ("amount_cents", True), ("amount_cents", 0),
                             ("amount_cents", 10001), ("amount_cents", 1.5)):
            operation = self.bank_operation()
            operation[field] = value
            with self.assertRaises(Rejected):
                self.gateway.plan(operation, "test")
        self.assertEqual(self.writes(), [])

    def test_bank_timeout_and_bad_response_stay_unknown_without_retry(self):
        for mismatch in (False, True):
            self.transport.fail_write = not mismatch
            self.transport.wrong_bank_response = mismatch
            request, sigs = self.approved(request_id="r" + str(mismatch))
            receipt = self.gateway.submit(request, sigs)
            self.assertEqual(receipt["state"], "SUBMISSION_UNKNOWN")
            before = len(self.writes())
            with self.assertRaisesRegex(Rejected, "ALREADY_RESERVED"):
                self.gateway.submit(request, sigs)
            self.assertEqual(len(self.writes()), before)

    def test_journal_rejects_changed_cache_and_preserves_append_history(self):
        request, sigs = self.approved()
        self.gateway.submit(request, sigs)
        status = self.gateway.gate.status("request1")
        self.assertEqual(len(status["journal_head"]), 64)
        with closing(sqlite3.connect(self.directory / "journal.sqlite")) as db, db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("DELETE FROM history")
            db.execute("UPDATE attempts SET state='FAKE_SETTLED' WHERE request_id='request1'")
        with self.assertRaisesRegex(Rejected, "EXTERNAL_CACHE_MISMATCH"):
            self.gateway.gate.status("request1")

    def test_wallet_timeout_does_not_retry_or_credit_the_sandbox(self):
        operation = self.wallet_operation()
        request, sigs = self.approved(operation)
        self.transport.fail_write = True
        receipt = self.gateway.submit(request, sigs, self.signed_raw(operation))
        self.assertEqual(receipt["state"], "SUBMISSION_UNKNOWN")
        self.assertFalse(receipt["sandbox_ledger_credited"])
        self.assertFalse(receipt["automatic_retry"])
        with self.assertRaisesRegex(Rejected, "ALREADY_RESERVED"):
            self.gateway.submit(request, sigs, self.signed_raw(operation))
        self.assertEqual(len(self.writes()), 1)

    def test_bank_reads_are_restricted_and_redacted(self):
        result = self.gateway.observe({"kind": "mercury.account", "account": ACCOUNT})
        self.assertEqual(result["available_balance_usd"], "120.00")
        self.assertNotIn("DO_NOT_RETURN", json.dumps(result))
        with patch.dict(os.environ, {"MRL_MERCURY_API_TOKEN": ""}):
            with self.assertRaisesRegex(Rejected, "TOKEN_NOT_CONFIGURED"):
                self.gateway.observe({"kind": "mercury.account", "account": ACCOUNT})

    def test_concurrent_bank_submit_only_once(self):
        request, sigs = self.approved()

        def attempt(_):
            try:
                return self.gateway.submit(request, sigs)["state"]
            except Rejected as exc:
                return str(exc)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(attempt, range(2)))
        self.assertIn("BANK_REQUEST_RECORDED", results)
        self.assertIn("EXTERNAL_REQUEST_OR_INTENT_ALREADY_RESERVED", results)
        self.assertEqual(len(self.writes()), 1)

    def test_native_transfer_real_signature_binds_all_fields(self):
        operation = self.wallet_operation()
        raw = self.signed_raw(operation)
        request, sigs = self.approved(operation)
        receipt = self.gateway.submit(request, sigs, raw)
        self.assertEqual(receipt["state"], "TX_BROADCAST")
        self.assertEqual(receipt["tx_hash"], "0x" + keccak(HexBytes(raw)).hex())
        self.assertFalse(receipt["settlement_verified"])
        self.assertNotIn(raw.encode(), (self.directory / "journal.sqlite").read_bytes())
        second, second_sigs = self.approved(operation, "request2")
        with self.assertRaisesRegex(Rejected, "ALREADY_RESERVED"):
            self.gateway.submit(second, second_sigs, raw)
        self.assertEqual(len(self.writes()), 1)

    def test_wrong_wallet_signature_is_not_authority(self):
        operation = self.wallet_operation()
        raw = self.signed_raw(operation, Account.create())
        request, sigs = self.approved(operation)
        with self.assertRaisesRegex(Rejected, "SIGNED_SOURCE_MISMATCH"):
            self.gateway.submit(request, sigs, raw)
        self.assertEqual(self.writes(), [])

    def test_signed_value_nonce_destination_or_fee_mismatch_rejected(self):
        operation = self.wallet_operation()
        request, sigs = self.approved(operation)
        for field, value in (("value", 1001), ("nonce", 1), ("to", Account.create().address.lower()),
                             ("maxFeePerGas", 201)):
            altered = copy.deepcopy(operation)
            altered["transaction"][field] = value
            with self.assertRaisesRegex(Rejected, "SIGNED_FIELDS_MISMATCH"):
                self.gateway.submit(request, sigs, self.signed_raw(altered))
        self.assertEqual(self.writes(), [])

    def test_arbitrary_contract_calls_approvals_7702_and_assets_rejected(self):
        for field, value in (("type", 4), ("data", "0x095ea7b3"), ("accessList", [{}]),
                             ("chainId", 1), ("gas", 100000), ("value", True),
                             ("value", 10**18), ("maxFeePerGas", 10**20)):
            operation = self.wallet_operation()
            operation["transaction"][field] = value
            with self.assertRaises(Rejected):
                self.gateway.plan(operation, "test")
        with self.assertRaisesRegex(Rejected, "UNSUPPORTED_EXTERNAL_OPERATION"):
            self.gateway.plan({"kind": "evm.force_return"}, "test")
        self.assertEqual(self.writes(), [])

    def test_chain_delegation_and_nonce_change_fail_before_send(self):
        for field, value, reason in (("chain", 1, "WRONG_CHAIN"),
                                     ("code", "0xef0100" + "1" * 40, "DELEGATED"),
                                     ("nonce", 1, "NONCE_CHANGED")):
            setattr(self.transport, field, value)
            with self.assertRaisesRegex(Rejected, reason):
                self.gateway.plan(self.wallet_operation(), "test")
            setattr(self.transport, field, {"chain": 11155111, "code": "0x", "nonce": 0}[field])
        self.assertEqual(self.writes(), [])

    def test_rpc_receipt_is_observation_not_return_or_finality(self):
        tx_hash = "0x" + "a" * 64
        result = self.gateway.observe({"kind": "evm.wallet", "wallet": self.wallet.address,
                                       "tx_hash": tx_hash})
        self.assertEqual(result["state"], "TX_PENDING")
        self.transport.receipt = {"transactionHash": tx_hash, "from": self.wallet.address,
                                  "status": "0x1", "blockHash": "0x" + "b" * 64, "blockNumber": "0x10"}
        result = self.gateway.observe({"kind": "evm.wallet", "wallet": self.wallet.address,
                                       "tx_hash": tx_hash})
        self.assertEqual(result["state"], "TX_RECEIPT_OBSERVED")
        self.assertFalse(result["settlement_verified"])
        self.assertEqual(result["finality"], "NOT_VERIFIED")

    def test_existing_registry_mount_preserves_old_tools(self):
        path = Path(__file__).resolve().parents[3] / "09_workflow" / "tool_registry.py"
        spec = importlib.util.spec_from_file_location("mrl_existing_tools_external", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        registry = module.ToolRegistry()
        registry.add(lambda: 1, name="existing_tool", parameters={})
        register_external_tools(registry, self.gateway)
        self.assertIn("existing_tool", registry.list_tools())
        self.assertEqual(len(registry.list_tools()), 5)
        with self.assertRaisesRegex(Rejected, "ALREADY_REGISTERED"):
            register_external_tools(registry, self.gateway)
        result = registry.call("MRL_financial_external_observe",
                               {"query": {"kind": "mercury.account", "account": ACCOUNT}})
        self.assertTrue(result["ok"])
        self.assertNotIn("FAKE_TEST_TOKEN", json.dumps(registry.call_log()))

class TransportTests(unittest.TestCase):
    def test_no_credentials_queries_http_or_redirects(self):
        for url in ("http://bank.example", "https://user:pass@bank.example", "https://rpc.example/?api_key=x",
                    "https://bank.example/#key", "https://bank.example\n.evil"):
            with self.assertRaises(Rejected):
                https_url(url)
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example"))

    def test_provider_error_never_includes_token_or_body(self):
        class Opener:
            def open(self, request, timeout):
                raise HTTPError(request.full_url, 401, "SECRET_PROVIDER_TOKEN", {}, None)
        transport = JsonTransport()
        transport.opener = Opener()
        with self.assertRaisesRegex(Rejected, "PROVIDER_HTTP_401") as caught:
            transport.request("GET", "https://api.mercury.com/api/v1/accounts")
        self.assertNotIn("SECRET_PROVIDER_TOKEN", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
