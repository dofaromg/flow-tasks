"""Scope/consent admission and durable submission journal for external operations."""

from contextlib import closing
from datetime import datetime, timezone
import getpass
import hashlib
import json
from pathlib import Path
import sqlite3
import time

from ..cli import read_json
from ..core import Ledger, Rejected, canonical, policy_hash, require, valid_name


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def default_settings(ledger_policy):
    """Build a complete disabled configuration; never invent account grants."""
    return {
        "schema": "MRL_Financial_External/v1", "origin_signature": "MrLiouWord",
        "ledger_policy_sha256": policy_hash(ledger_policy),
        "writes_enabled": False, "allow_live": False,
        "mercury": {"environment": "sandbox", "accounts": [], "recipients": [],
                    "max_amount_cents": 10000},
        "evm": {"chain_id": 11155111, "rpc_url": "", "wallets": [], "recipients": [],
                "max_value_wei": 1000000000000000, "max_fee_wei": 1000000000000000},
    }


class OperationGate:
    """Require root-registry scope AND an independent signed operation envelope.

    The optional financial_external_grants array extends the SAME root registry;
    it does not modify or reuse its structure-index grants. Nothing ships active.
    """

    def __init__(self, ledger_policy, settings, root_registry, journal):
        from ..core import validate_policy
        validate_policy(ledger_policy)
        self.policy = json.loads(canonical(ledger_policy))
        self.settings = json.loads(canonical(settings))
        require(type(settings) is dict and set(settings) == {
            "schema", "origin_signature", "ledger_policy_sha256", "writes_enabled",
            "allow_live", "mercury", "evm",
        }, "INVALID_EXTERNAL_SETTINGS")
        require(settings["schema"] == "MRL_Financial_External/v1" and
                settings["origin_signature"] == "MrLiouWord" and
                settings["ledger_policy_sha256"] == policy_hash(self.policy), "SETTINGS_POLICY_MISMATCH")
        require(type(settings["writes_enabled"]) is bool and type(settings["allow_live"]) is bool,
                "INVALID_LIVE_FLAGS")
        self.root = Path(root_registry)
        self.journal = Path(journal)

    def now(self):
        return int(time.time())

    def _root(self):
        require(self.root.is_file() and not self.root.is_symlink(), "ROOT_REGISTRY_REQUIRED")
        root = read_json(self.root)
        require(type(root) is dict, "INVALID_ROOT_POLICY")
        model = root.get("authorization_model", {})
        require(root.get("root_authority") == "Mr.liou" and
                root.get("origin_signature") == "MrLiouWord" and
                model.get("default_decision") == "DENY" and
                model.get("explicit_grant_required") is True and
                model.get("implicit_authorization_allowed") is False, "INVALID_ROOT_POLICY")
        return root

    def admit(self, action, resource, destination, environment):
        """Re-read revocation and expiry on every call, including before submission."""
        root = self._root()
        grants = root.get("financial_external_grants", [])
        require(type(grants) is list, "INVALID_EXTERNAL_GRANTS")
        matches = []
        now = datetime.fromtimestamp(self.now(), timezone.utc)
        for grant in grants:
            require(type(grant) is dict and set(grant) == {
                "record_id", "issued_by", "actor", "issued_at", "expires_at", "status",
                "action", "resource", "destination", "environment", "evidence_reference",
            }, "INVALID_EXTERNAL_GRANT")
            valid_name(grant["record_id"])
            require(isinstance(grant["evidence_reference"], str) and
                    grant["evidence_reference"].strip(), "GRANT_EVIDENCE_REQUIRED")
            try:
                start = datetime.fromisoformat(grant["issued_at"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(grant["expires_at"].replace("Z", "+00:00"))
                require(start.tzinfo is not None and end.tzinfo is not None and start < end,
                        "INVALID_GRANT_TIME")
            except (TypeError, ValueError, AttributeError) as exc:
                raise Rejected("INVALID_GRANT_TIME") from None
            if (grant["issued_by"] == "MrLiouWord" and grant["status"] == "active" and
                    grant["actor"] == "local:" + getpass.getuser() and
                    start <= now < end and grant["action"] == action and
                    grant["resource"] == resource and grant["destination"] == destination and
                    grant["environment"] == environment):
                matches.append(grant["record_id"])
        require(len(matches) == 1, "NO_UNIQUE_EXTERNAL_ROOT_GRANT")
        return digest(root)

    def envelope(self, operation, request_id):
        """Build bytes-to-approve data only; this function does not create a signature."""
        valid_name(request_id)
        now = self.now()
        return {"version": 1, "ledger_id": self.policy["ledger_id"],
                "ledger_policy_sha256": policy_hash(self.policy),
                "connector_policy_sha256": digest(self.settings),
                "root_registry_sha256": digest(self._root()),
                "request_id": request_id, "issued_at": now,
                "expires_at": now + min(300, self.policy["max_request_lifetime"]),
                "operation": operation}

    def authorize(self, request, signatures):
        """Check exact domain and majority signatures before any write-side network IO."""
        require(self.settings["writes_enabled"], "EXTERNAL_WRITES_DISABLED")
        require(type(request) is dict and set(request) == {
            "version", "ledger_id", "ledger_policy_sha256", "connector_policy_sha256",
            "root_registry_sha256", "request_id", "issued_at", "expires_at", "operation",
        }, "INVALID_EXTERNAL_REQUEST")
        require(type(request["version"]) is int and request["version"] == 1 and
                request["ledger_id"] == self.policy["ledger_id"] and
                request["ledger_policy_sha256"] == policy_hash(self.policy) and
                request["connector_policy_sha256"] == digest(self.settings) and
                request["root_registry_sha256"] == digest(self._root()), "EXTERNAL_DOMAIN_MISMATCH")
        valid_name(request["request_id"])
        start, end, now = request["issued_at"], request["expires_at"], self.now()
        require(type(start) is int and type(end) is int and 0 <= start <= now < end and
                end - start <= min(300, self.policy["max_request_lifetime"]), "EXTERNAL_REQUEST_TIME")
        # Reuse the existing sandbox's verified signature implementation, not its balances.
        verifier = object.__new__(Ledger)
        verifier.policy = self.policy
        signers = verifier._signers(request, signatures)
        verifier._quorum(signers)

    def initialize_journal(self):
        """Create only an empty external outbox; never replace a previous outbox."""
        with self.journal.open("xb"):
            pass
        with closing(sqlite3.connect(self.journal)) as db, db:
            db.execute("CREATE TABLE attempts (request_id TEXT PRIMARY KEY, "
                       "intent TEXT UNIQUE NOT NULL, request_sha256 TEXT NOT NULL, "
                       "state TEXT NOT NULL, receipt TEXT NOT NULL)")
            db.execute("CREATE TABLE history (seq INTEGER PRIMARY KEY, body TEXT NOT NULL, "
                       "previous TEXT NOT NULL, hash TEXT NOT NULL)")
            db.execute("CREATE TRIGGER history_no_update BEFORE UPDATE ON history "
                       "BEGIN SELECT RAISE(ABORT, 'APPEND_ONLY'); END")
            db.execute("CREATE TRIGGER history_no_delete BEFORE DELETE ON history "
                       "BEGIN SELECT RAISE(ABORT, 'APPEND_ONLY'); END")

    @staticmethod
    def _history(db, event=None):
        previous = "0" * 64
        for index, (seq, body, parent, recorded) in enumerate(db.execute(
                "SELECT seq,body,previous,hash FROM history ORDER BY seq"), 1):
            require(seq == index and parent == previous and recorded == hashlib.sha256(
                    bytes.fromhex(previous) + body.encode("utf-8")).hexdigest(), "EXTERNAL_HISTORY_BROKEN")
            previous = recorded
        if event is not None:
            body = canonical(event)
            recorded = hashlib.sha256(bytes.fromhex(previous) + body).hexdigest()
            db.execute("INSERT INTO history(body,previous,hash) VALUES (?,?,?)",
                       (body.decode("utf-8"), previous, recorded))
            previous = recorded
        return previous

    def reserve(self, request, intent):
        """Commit UNKNOWN before calling provider. A crash/timeout cannot auto-retry."""
        require(self.journal.is_file() and not self.journal.is_symlink(), "EXTERNAL_JOURNAL_REQUIRED")
        with closing(sqlite3.connect(self.journal, timeout=10)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("INSERT INTO attempts VALUES (?,?,?,?,?)", (
                    request["request_id"], intent, digest(request), "SUBMISSION_UNKNOWN", "{}"))
                self._history(db, {"event": "reserved", "request_id": request["request_id"],
                                   "request_sha256": digest(request), "intent": intent})
            except sqlite3.IntegrityError:
                raise Rejected("EXTERNAL_REQUEST_OR_INTENT_ALREADY_RESERVED") from None

    def finish(self, request_id, receipt):
        with closing(sqlite3.connect(self.journal)) as db, db:
            db.execute("UPDATE attempts SET state=?, receipt=? WHERE request_id=?",
                       (receipt["state"], canonical(receipt).decode("utf-8"), request_id))
            self._history(db, {"event": "provider_response", "request_id": request_id, "receipt": receipt})

    def status(self, request_id):
        """Local attempt state, not an assertion of bank settlement or chain finality."""
        valid_name(request_id)
        require(self.journal.is_file() and not self.journal.is_symlink(), "EXTERNAL_JOURNAL_REQUIRED")
        with closing(sqlite3.connect(self.journal)) as db:
            head = self._history(db)
            row = db.execute("SELECT state, receipt, request_sha256 FROM attempts WHERE request_id=?",
                             (request_id,)).fetchone()
            events = [json.loads(item[0]) for item in db.execute("SELECT body FROM history ORDER BY seq")]
        require(row is not None, "EXTERNAL_REQUEST_NOT_FOUND")
        related = [e for e in events if e["request_id"] == request_id]
        require(related and related[0]["event"] == "reserved" and
                related[0]["request_sha256"] == row[2], "EXTERNAL_CACHE_MISMATCH")
        expected_receipt = related[-1].get("receipt", {})
        require(json.loads(row[1]) == expected_receipt and
                row[0] == expected_receipt.get("state", "SUBMISSION_UNKNOWN"), "EXTERNAL_CACHE_MISMATCH")
        return {"request_id": request_id, "state": row[0], "receipt": json.loads(row[1]),
                "request_sha256": row[2], "journal_head": head}
