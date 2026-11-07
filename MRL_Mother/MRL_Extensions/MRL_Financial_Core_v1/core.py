"""Signed, append-only financial sandbox; never connects to payment networks.

MRL source authority: Mr.liou. origin_signature: MrLiouWord.
Balances are test ledger units, not bank deposits or blockchain assets.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ZERO = "0" * 64
NAME = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
FIELDS = {
    "open_account": {"account", "owner_key"},
    "issue": {"account", "asset", "amount", "evidence_sha256"},
    "propose": {"transfer", "source", "destination", "asset", "amount"},
    "settle": {"transfer"},
    "dispute": {"transfer", "evidence_sha256"},
    "appeal": {"transfer", "evidence_sha256"},
    "resolve": {"transfer", "decision", "evidence_sha256"},
}


class Rejected(ValueError):
    """The request cannot be admitted under the pinned ledger policy."""


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


def canonical(value) -> bytes:
    """Stable signing encoding: JSON UTF-8, sorted keys, no insignificant spaces."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def policy_hash(policy) -> str:
    return hashlib.sha256(canonical(policy)).hexdigest()


def valid_name(value):
    require(isinstance(value, str) and NAME.fullmatch(value), "INVALID_IDENTIFIER")


def positive(value):
    require(type(value) is int and 0 < value <= 2**63 - 1, "INVALID_AMOUNT")


def valid_hash(value):
    require(isinstance(value, str) and HEX.fullmatch(value), "INVALID_HASH")


def valid_key(value):
    valid_hash(value)
    Ed25519PublicKey.from_public_bytes(bytes.fromhex(value))


def validate_policy(policy):
    require(type(policy) is dict and set(policy) == {
        "ledger_id", "origin_signature", "council_keys", "quorum", "assets",
        "settlement_delay", "review_delay", "max_request_lifetime",
    }, "INVALID_POLICY")
    valid_name(policy["ledger_id"])
    require(policy["origin_signature"] == "MrLiouWord", "INVALID_ORIGIN")
    keys = policy["council_keys"]
    require(type(keys) is list and 3 <= len(keys) <= 20, "INVALID_COUNCIL")
    for key in keys:
        valid_key(key)
    require(len(set(keys)) == len(keys), "DUPLICATE_COUNCIL_KEY")
    q = policy["quorum"]
    require(type(q) is int and len(keys) // 2 < q <= len(keys), "INVALID_QUORUM")
    assets = policy["assets"]
    require(type(assets) is list and 0 < len(assets) <= 100, "INVALID_ASSETS")
    for asset in assets:
        valid_name(asset)
    require(len(set(assets)) == len(assets), "DUPLICATE_ASSET")
    for key in ("settlement_delay", "review_delay", "max_request_lifetime"):
        require(type(policy[key]) is int and 0 < policy[key] <= 31536000,
                "INVALID_POLICY_TIME")


class Ledger:
    """Local unit ledger with trusted policy supplied externally on every open.

    Signer keys are public. No private keys, signing or network send API exists.
    A host owner can alter files; pin heads externally to detect rollback.
    """

    def __init__(self, path, policy):
        validate_policy(policy)
        self.path = Path(path)
        self.policy = json.loads(canonical(policy))
        require(self.path.is_file() and not self.path.is_symlink(), "LEDGER_NOT_FOUND")

    @classmethod
    def create(cls, path, policy):
        """Create a new sandbox only; refuse to overwrite an existing file."""
        validate_policy(policy)
        path = Path(path)
        with path.open("xb"):
            pass
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY, body TEXT NOT NULL, "
                       "previous TEXT NOT NULL, hash TEXT NOT NULL)")
            db.execute("CREATE TRIGGER immutable_update BEFORE UPDATE ON events "
                       "BEGIN SELECT RAISE(ABORT, 'APPEND_ONLY'); END")
            db.execute("CREATE TRIGGER immutable_delete BEFORE DELETE ON events "
                       "BEGIN SELECT RAISE(ABORT, 'APPEND_ONLY'); END")
            cls._append(db, {"genesis": policy}, ZERO)
        return cls(path, policy)

    @staticmethod
    def _append(db, body, previous):
        raw = canonical(body)
        digest = hashlib.sha256(bytes.fromhex(previous) + raw).hexdigest()
        db.execute("INSERT INTO events(body,previous,hash) VALUES (?,?,?)",
                   (raw.decode("utf-8"), previous, digest))
        return digest

    def _read(self, db):
        state = {"accounts": {}, "balances": {}, "transfers": {},
                 "requests": [], "postings": []}
        previous = ZERO
        last_time = 0
        rows = db.execute("SELECT seq,body,previous,hash FROM events ORDER BY seq").fetchall()
        require(bool(rows), "MISSING_GENESIS")
        for index, (seq, raw, parent, digest) in enumerate(rows, 1):
            require(seq == index and parent == previous and digest ==
                    hashlib.sha256(bytes.fromhex(parent) + raw.encode("utf-8")).hexdigest(),
                    "BROKEN_EVENT_CHAIN")
            body = json.loads(raw)
            if index == 1:
                require(body == {"genesis": self.policy}, "POLICY_MISMATCH")
            else:
                require(set(body) == {"request", "signatures", "accepted_at"}, "BAD_EVENT")
                now = body["accepted_at"]
                require(type(now) is int and now >= last_time, "CLOCK_REGRESSION")
                self._apply(state, body["request"], body["signatures"], now)
                last_time = now
            previous = digest
        return state, previous, last_time

    def snapshot(self, expected_head=None):
        """Replay hashes AND signatures; optional external head rejects stale copies."""
        with sqlite3.connect(self.path) as db:
            state, head, _ = self._read(db)
        require(expected_head is None or expected_head == head, "CHECKPOINT_MISMATCH")
        return {"origin_signature": "MrLiouWord", "mode": "SANDBOX_UNITS_ONLY",
                "policy_sha256": policy_hash(self.policy), "head": head, "state": state}

    def submit(self, request, signatures):
        """Admit an externally signed request atomically using the host clock."""
        # Test subclasses override _now; callers cannot supply time through tools/CLI.
        now = self._now()
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            state, head, last = self._read(db)
            require(now >= last, "CLOCK_REGRESSION")
            self._apply(state, request, signatures, now)
            head = self._append(db, {"request": request, "signatures": signatures,
                                     "accepted_at": now}, head)
        return {"status": "RECORDED_IN_SANDBOX", "head": head,
                "origin_signature": "MrLiouWord", "real_asset_moved": False}

    def _now(self):
        return int(time.time())

    def _signers(self, request, signatures):
        require(type(signatures) is dict and 0 < len(signatures) <= 22, "SIGNATURES_REQUIRED")
        for key, signature in signatures.items():
            valid_key(key)
            require(isinstance(signature, str) and re.fullmatch(r"[0-9a-f]{128}", signature),
                    "INVALID_SIGNATURE_ENCODING")
            try:
                Ed25519PublicKey.from_public_bytes(bytes.fromhex(key)).verify(
                    bytes.fromhex(signature), canonical(request))
            except InvalidSignature as exc:
                raise Rejected("INVALID_SIGNATURE") from exc
        return set(signatures)

    def _quorum(self, signers):
        require(len(signers & set(self.policy["council_keys"])) >= self.policy["quorum"],
                "COUNCIL_QUORUM_REQUIRED")

    @staticmethod
    def _balance(state, account, asset):
        return state["balances"].get(account, {}).get(asset, 0)

    def _available(self, state, account, asset, excluding=None):
        reserved = 0
        for tid, transfer in state["transfers"].items():
            if tid == excluding or transfer["asset"] != asset:
                continue
            if transfer["status"] == "pending" and transfer["source"] == account:
                reserved += transfer["amount"]
            elif transfer["status"] == "settled" and transfer["disputed"] and transfer["destination"] == account:
                reserved += transfer["amount"]
        return self._balance(state, account, asset) - reserved

    @staticmethod
    def _post(state, source, destination, asset, amount, reference):
        for account, delta in ((source, -amount), (destination, amount)):
            balances = state["balances"].setdefault(account, {})
            balances[asset] = balances.get(asset, 0) + delta
            state["postings"].append({"account": account, "asset": asset,
                                      "delta": delta, "reference": reference})

    def _apply(self, state, request, signatures, now):
        require(type(request) is dict and set(request) == {
            "version", "ledger_id", "policy_sha256", "request_id", "issued_at",
            "expires_at", "action", "payload",
        }, "INVALID_REQUEST_SCHEMA")
        require(type(request["version"]) is int and request["version"] == 1,
                "INVALID_REQUEST_VERSION")
        require(request["ledger_id"] == self.policy["ledger_id"] and
                request["policy_sha256"] == policy_hash(self.policy), "WRONG_SIGNING_DOMAIN")
        valid_name(request["request_id"])
        require(request["request_id"] not in state["requests"], "REQUEST_REPLAY")
        issued, expires = request["issued_at"], request["expires_at"]
        require(type(issued) is int and type(expires) is int and
                0 <= issued <= now < expires and
                0 < expires - issued <= self.policy["max_request_lifetime"], "REQUEST_TIME_INVALID")
        action, p = request["action"], request["payload"]
        require(isinstance(action, str) and action in FIELDS, "UNKNOWN_ACTION")
        require(type(p) is dict and set(p) == FIELDS[action], "INVALID_PAYLOAD_SCHEMA")
        signers = self._signers(request, signatures)
        for field in ("account", "source", "destination", "transfer"):
            if field in p:
                valid_name(p[field])
        if "evidence_sha256" in p:
            valid_hash(p["evidence_sha256"])
        if "amount" in p:
            positive(p["amount"])
        if "asset" in p:
            require(p["asset"] in self.policy["assets"], "UNKNOWN_ASSET")
        accounts, transfers = state["accounts"], state["transfers"]
        if action == "open_account":
            self._quorum(signers)
            valid_key(p["owner_key"])
            require(p["owner_key"] not in self.policy["council_keys"], "SEPARATE_OWNER_AND_COUNCIL")
            require(p["account"] not in accounts, "ACCOUNT_EXISTS")
            accounts[p["account"]] = p["owner_key"]
        elif action == "issue":
            self._quorum(signers)
            require(p["account"] in accounts, "ACCOUNT_NOT_FOUND")
            self._post(state, "@issuance", p["account"], p["asset"], p["amount"], request["request_id"])
        elif action == "propose":
            require(p["source"] in accounts and p["destination"] in accounts, "ACCOUNT_NOT_FOUND")
            require(accounts[p["source"]] in signers, "OWNER_SIGNATURE_REQUIRED")
            require(p["source"] != p["destination"], "SELF_TRANSFER")
            require(p["transfer"] not in transfers, "TRANSFER_EXISTS")
            require(self._available(state, p["source"], p["asset"]) >= p["amount"], "INSUFFICIENT_AVAILABLE")
            transfers[p["transfer"]] = {**p, "status": "pending", "disputed": False,
                "ready_at": now + self.policy["settlement_delay"], "case_closed": False,
                "appealed": False}
        else:
            require(p["transfer"] in transfers, "TRANSFER_NOT_FOUND")
            t = transfers[p["transfer"]]
            owners = {accounts[t["source"]], accounts[t["destination"]]}
            if action == "settle":
                require(accounts[t["source"]] in signers, "OWNER_SIGNATURE_REQUIRED")
                require(t["status"] == "pending" and not t["disputed"], "TRANSFER_NOT_SETTLEABLE")
                require(now >= t["ready_at"], "SETTLEMENT_DELAY")
                require(self._available(state, t["source"], t["asset"], p["transfer"]) >= t["amount"],
                        "INSUFFICIENT_AVAILABLE")
                self._post(state, t["source"], t["destination"], t["asset"], t["amount"], request["request_id"])
                t["status"] = "settled"
            elif action == "dispute":
                require(bool(signers & (owners | set(self.policy["council_keys"]))), "CASE_SIGNER_REQUIRED")
                require(not t["case_closed"] and not t["disputed"], "CASE_UNAVAILABLE")
                t.update(disputed=True, review_at=now + self.policy["review_delay"],
                         evidence_sha256=p["evidence_sha256"])
            elif action == "appeal":
                require(bool(signers & owners), "PARTY_SIGNATURE_REQUIRED")
                require(t["disputed"] and not t["appealed"], "APPEAL_UNAVAILABLE")
                t.update(appealed=True, review_at=max(t["review_at"], now) + self.policy["review_delay"],
                         appeal_evidence_sha256=p["evidence_sha256"])
            elif action == "resolve":
                self._quorum(signers)
                require(t["disputed"] and now >= t["review_at"], "CASE_NOT_READY")
                require(p["decision"] in ("refund", "release"), "INVALID_DECISION")
                if p["decision"] == "refund":
                    if t["status"] == "settled":
                        require(self._available(state, t["destination"], t["asset"], p["transfer"]) >= t["amount"],
                                "RETURN_SHORTFALL_EXTERNAL_RECOVERY_REQUIRED")
                        self._post(state, t["destination"], t["source"], t["asset"],
                                   t["amount"], request["request_id"])
                        t["status"] = "refunded"
                    else:
                        t["status"] = "cancelled"
                t.update(disputed=False, case_closed=True, decision=p["decision"],
                         resolution_evidence_sha256=p["evidence_sha256"])
        state["requests"].append(request["request_id"])


def register_tools(registry, ledger):
    """Explicitly mount onto the existing MRL ToolRegistry; no automatic startup."""
    require(not {"MRL_financial_snapshot", "MRL_financial_submit"} &
            set(registry.list_tools()), "TOOL_ALREADY_REGISTERED")
    registry.add(ledger.snapshot, name="MRL_financial_snapshot",
                 description="核對 MRL 測試帳本、簽章與事件鏈；不操作真實資產。", parameters={})
    registry.add(ledger.submit, name="MRL_financial_submit",
                 description="提交外部簽署的測試帳本請求；Agent 無私鑰或裁決權。",
                 parameters={"request": dict, "signatures": dict})
