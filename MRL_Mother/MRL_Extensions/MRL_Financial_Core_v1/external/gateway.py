"""Explicit mother tool adapter for scoped external account operations."""

from ..core import Rejected, require
from .evm import EVM, address
from .gate import OperationGate, digest
from .mercury import Mercury
from .transport import JsonTransport


class Gateway:
    """Each externally effective call needs provider credentials and MRL consent.

    No model-generated accusation can create an account grant. Native-currency
    wallet signatures must come from the actual permitted source wallet.
    """

    def __init__(self, ledger_policy, settings, root_registry, journal,
                 enable_live=False, transport=None):
        self.gate = OperationGate(ledger_policy, settings, root_registry, journal)
        transport = transport or JsonTransport()
        live = enable_live is True and settings["allow_live"] is True
        self.bank = Mercury(settings["mercury"], transport, live)
        self.wallet = EVM(settings["evm"], transport, live)

    def _adapter(self, operation):
        require(type(operation) is dict, "INVALID_EXTERNAL_OPERATION")
        kind = operation.get("kind")
        if kind == "mercury.request_ach":
            return self.bank
        if kind == "evm.native_transfer":
            return self.wallet
        raise Rejected("UNSUPPORTED_EXTERNAL_OPERATION")

    def _admit(self, operation):
        adapter = self._adapter(operation)
        action, resource, destination = adapter.validate(operation)
        return self.gate.admit(action, resource, destination, adapter.environment)

    def plan(self, operation, request_id):
        """Validate scope and optionally read chain state, then emit an unsigned consent envelope."""
        self._admit(operation)
        if operation["kind"] == "evm.native_transfer":
            self.wallet.preflight(operation)
        return self.gate.envelope(operation, request_id)

    def observe(self, query):
        require(type(query) is dict, "INVALID_EXTERNAL_QUERY")
        kind = query.get("kind")
        if kind == "mercury.account" and set(query) == {"kind", "account"}:
            resource = self.bank.source(query["account"])
            self.gate.admit("financial.mercury.read", resource, "local-operator", self.bank.environment)
            return self.bank.account(query["account"])
        if kind == "mercury.transaction" and set(query) == {"kind", "account", "transaction"}:
            resource = self.bank.source(query["account"])
            self.gate.admit("financial.mercury.read", resource, "local-operator", self.bank.environment)
            return self.bank.transaction(query["account"], query["transaction"])
        if kind == "evm.wallet" and set(query) in ({"kind", "wallet"}, {"kind", "wallet", "tx_hash"}):
            resource = self.wallet.source(query["wallet"])
            self.gate.admit("financial.evm.read", resource, "local-operator", self.wallet.environment)
            return self.wallet.observe(query["wallet"], query.get("tx_hash"))
        raise Rejected("UNSUPPORTED_EXTERNAL_QUERY")

    def submit(self, request, signatures, signed_raw=""):
        """Submit a consent-bound operation once. Acceptance is never called settlement."""
        self.gate.authorize(request, signatures)
        operation = request["operation"]
        require(self._admit(operation) == request["root_registry_sha256"], "ROOT_CHANGED")
        adapter = self._adapter(operation)
        if adapter is self.wallet:
            self.wallet.signed_transaction(operation, signed_raw)
            self.wallet.preflight(operation)
            tx = operation["transaction"]
            intent = f'evm:{tx["chainId"]}:{address(operation["source"])}:{tx["nonce"]}'
        else:
            require(signed_raw == "", "UNEXPECTED_SIGNED_TRANSACTION")
            intent = "bank:" + request["request_id"]
        self.gate.reserve(request, intent)
        # This row is already committed. Provider exceptions leave UNKNOWN and
        # require reconciliation; no implicit retries or silent resubmission.
        try:
            require(self._admit(operation) == request["root_registry_sha256"], "ROOT_CHANGED")
            if adapter is self.wallet:
                receipt = self.wallet.send(operation, signed_raw)
            else:
                receipt = self.bank.send(operation, digest({"ledger": self.gate.policy["ledger_id"],
                                                          "request_id": request["request_id"]}))
            receipt.update(origin_signature="MrLiouWord", request_id=request["request_id"],
                           request_sha256=digest(request))
            self.gate.finish(request["request_id"], receipt)
            return receipt
        except Exception:
            # Never place provider errors, tokens or signed raw payloads in tool tracebacks.
            return {"state": "SUBMISSION_UNKNOWN", "request_id": request["request_id"],
                    "origin_signature": "MrLiouWord", "automatic_retry": False,
                    "settlement_verified": False, "sandbox_ledger_credited": False}


def register_external_tools(registry, gateway):
    """Attach to the existing mother's ToolRegistry, preserving all original tools."""
    names = {"MRL_financial_external_plan", "MRL_financial_external_observe",
             "MRL_financial_external_submit", "MRL_financial_external_status"}
    require(not names & set(registry.list_tools()), "EXTERNAL_TOOL_ALREADY_REGISTERED")
    registry.add(gateway.plan, name="MRL_financial_external_plan",
                 description="建立已授權銀行／錢包操作的待簽核請求。",
                 parameters={"operation": dict, "request_id": str})
    registry.add(gateway.observe, name="MRL_financial_external_observe",
                 description="查詢已授權外部帳戶；不把查詢結果視為返還完成。",
                 parameters={"query": dict})
    registry.add(gateway.submit, name="MRL_financial_external_submit",
                 description="提交具有效根授權、核准簽章與錢包簽名的操作；不保管私鑰。",
                 parameters={"request": dict, "signatures": dict, "signed_raw": str})
    registry.add(gateway.gate.status, name="MRL_financial_external_status",
                 description="讀回本機提交回執；UNKNOWN 不會自動重送。",
                 parameters={"request_id": str})
