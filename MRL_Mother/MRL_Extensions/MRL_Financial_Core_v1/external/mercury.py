"""Official Mercury account reads and approval-required ACH payment requests."""

from decimal import Decimal, InvalidOperation
import json
import os
from uuid import UUID

from ..core import Rejected, require


def uuid_string(value):
    require(isinstance(value, str), "INVALID_MERCURY_ID")
    try:
        require(str(UUID(value)) == value, "INVALID_MERCURY_ID")
    except ValueError:
        raise Rejected("INVALID_MERCURY_ID") from None
    return value


class Mercury:
    def __init__(self, settings, transport, enable_live=False):
        require(type(settings) is dict and set(settings) == {
            "environment", "accounts", "recipients", "max_amount_cents",
        }, "INVALID_MERCURY_SETTINGS")
        require(settings["environment"] in ("sandbox", "live"), "UNKNOWN_BANK_ENVIRONMENT")
        for field in ("accounts", "recipients"):
            require(type(settings[field]) is list, "INVALID_BANK_ALLOWLIST")
            for value in settings[field]:
                uuid_string(value)
            require(len(settings[field]) == len(set(settings[field])), "DUPLICATE_BANK_ID")
        require(type(settings["max_amount_cents"]) is int and
                0 < settings["max_amount_cents"] <= 100000000, "INVALID_BANK_LIMIT")
        self.settings, self.transport = settings, transport
        self.environment = "mercury-" + settings["environment"]
        self.live_enabled = enable_live
        self.base = ("https://api.mercury.com/api/v1" if settings["environment"] == "live"
                     else "https://api-sandbox.mercury.com/api/v1")

    def environment_check(self):
        require(self.settings["environment"] != "live" or self.live_enabled, "LIVE_ACCESS_DISABLED")

    def source(self, account):
        self.environment_check()
        uuid_string(account)
        require(account in self.settings["accounts"], "BANK_ACCOUNT_NOT_ALLOWED")
        return "mercury:" + account

    def _call(self, method, path, body=None):
        self.environment_check()
        token = os.environ.get("MRL_MERCURY_API_TOKEN", "")
        require(token and token.isascii() and not any(c.isspace() for c in token),
                "MERCURY_TOKEN_NOT_CONFIGURED")
        return self.transport.request(method, self.base + path, body,
                                      {"Authorization": "Bearer " + token})

    def account(self, account):
        self.source(account)
        result = self._call("GET", "/account/" + account)
        require(type(result) is dict and result.get("id") == account, "BANK_ACCOUNT_RESPONSE_MISMATCH")
        # Never expose routing/account numbers, legal names or provider auth data.
        return {"account_id": account, "environment": self.environment,
                "current_balance_usd": str(result.get("currentBalance", "UNKNOWN")),
                "available_balance_usd": str(result.get("availableBalance", "UNKNOWN")),
                "state": "BANK_REPORTED_BALANCE", "settlement_verified": False}

    def transaction(self, account, transaction):
        self.source(account)
        uuid_string(transaction)
        result = self._call("GET", f"/account/{account}/transaction/{transaction}")
        require(type(result) is dict and result.get("accountId") == account and
                result.get("id") == transaction, "BANK_TRANSACTION_RESPONSE_MISMATCH")
        return {"transaction_id": transaction, "account_id": account,
                "provider_status": result.get("status", "UNKNOWN"),
                "amount_usd": str(result.get("amount", "UNKNOWN")),
                "state": "BANK_TRANSACTION_OBSERVED", "settlement_verified": False}

    def validate(self, operation):
        require(type(operation) is dict and set(operation) == {
            "kind", "environment", "account", "recipient", "amount_cents",
        } and operation["kind"] == "mercury.request_ach", "INVALID_BANK_OPERATION")
        resource = self.source(operation["account"])
        require(operation["environment"] == self.environment, "BANK_ENVIRONMENT_MISMATCH")
        uuid_string(operation["recipient"])
        require(operation["recipient"] in self.settings["recipients"], "BANK_RECIPIENT_NOT_ALLOWED")
        require(type(operation["amount_cents"]) is int and
                0 < operation["amount_cents"] <= self.settings["max_amount_cents"], "BANK_AMOUNT_LIMIT")
        return "financial.mercury.request_ach", resource, "mercury-recipient:" + operation["recipient"]

    def send(self, operation, request_id):
        """Queue only the approval-required path; never call the direct-send endpoint."""
        self.validate(operation)
        amount = operation["amount_cents"]
        # Fixed-point USD JSON number; avoid converting money to binary float.
        body = ('{"amount":' + f"{amount // 100}.{amount % 100:02d}" +
                ',"idempotencyKey":' + json.dumps("MRL_" + request_id) +
                ',"paymentMethod":"ach","recipientId":' + json.dumps(operation["recipient"]) + '}')
        result = self._call("POST", f'/account/{operation["account"]}/request-send-money', body.encode())
        require(type(result) is dict and result.get("accountId") == operation["account"] and
                result.get("recipientId") == operation["recipient"] and
                result.get("paymentMethod") == "ach", "BANK_REQUEST_RESPONSE_MISMATCH")
        try:
            matched = Decimal(str(result.get("amount"))) == Decimal(amount) / 100
        except InvalidOperation:
            matched = False
        require(matched and isinstance(result.get("requestId"), str) and result["requestId"],
                "BANK_REQUEST_RESPONSE_MISMATCH")
        require(result.get("status") in ("pendingApproval", "approved", "rejected", "cancelled"),
                "UNKNOWN_BANK_REQUEST_STATUS")
        return {"state": "BANK_REQUEST_RECORDED", "provider_request_id": result["requestId"],
                "provider_status": result["status"], "environment": self.environment,
                "settlement_verified": False, "sandbox_ledger_credited": False}
