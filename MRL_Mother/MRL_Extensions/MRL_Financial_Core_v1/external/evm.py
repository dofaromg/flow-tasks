"""EIP-1559 native-currency transfers signed outside MRL. No custody of keys."""

import re

from eth_account import Account
from eth_account.typed_transactions import TypedTransaction
from eth_utils import keccak
from hexbytes import HexBytes

from ..core import Rejected, canonical, require
from .transport import https_url

ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}\Z")
TXHASH = re.compile(r"0x[0-9a-fA-F]{64}\Z")
RPC_METHODS = {"eth_chainId", "eth_getBalance", "eth_getCode", "eth_getTransactionCount",
               "eth_sendRawTransaction", "eth_getTransactionReceipt", "eth_getTransactionByHash"}


def address(value):
    require(isinstance(value, str) and ADDRESS.fullmatch(value) and int(value, 16) != 0,
            "INVALID_EVM_ADDRESS")
    return value.lower()


def quantity(value):
    require(isinstance(value, str) and re.fullmatch(r"0x(?:0|[1-9a-f][0-9a-f]*)", value),
            "INVALID_RPC_QUANTITY")
    return int(value, 16)


class EVM:
    def __init__(self, settings, transport, enable_live=False):
        require(type(settings) is dict and set(settings) == {
            "chain_id", "rpc_url", "wallets", "recipients", "max_value_wei", "max_fee_wei",
        }, "INVALID_EVM_SETTINGS")
        require(type(settings["chain_id"]) is int and settings["chain_id"] in (1, 11155111),
                "UNSUPPORTED_CHAIN")
        for field in ("wallets", "recipients"):
            require(type(settings[field]) is list, "INVALID_EVM_ALLOWLIST")
            values = [address(v) for v in settings[field]]
            require(len(set(values)) == len(values), "DUPLICATE_EVM_ADDRESS")
        for field in ("max_value_wei", "max_fee_wei"):
            require(type(settings[field]) is int and 0 < settings[field] < 2**128, "INVALID_EVM_LIMIT")
        if settings["rpc_url"]:
            https_url(settings["rpc_url"])
        self.settings, self.transport = settings, transport
        self.environment = "evm-mainnet" if settings["chain_id"] == 1 else "evm-sepolia"
        self.live_enabled = enable_live

    def source(self, wallet):
        require(self.settings["chain_id"] != 1 or self.live_enabled, "LIVE_ACCESS_DISABLED")
        wallet = address(wallet)
        require(wallet in [address(x) for x in self.settings["wallets"]], "WALLET_NOT_ALLOWED")
        return f'evm:{self.settings["chain_id"]}:{wallet}'

    def rpc(self, method, params):
        require(method in RPC_METHODS, "RPC_METHOD_NOT_ALLOWED")
        require(self.settings["rpc_url"], "EVM_RPC_NOT_CONFIGURED")
        data = self.transport.request("POST", self.settings["rpc_url"],
            canonical({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}))
        require(type(data) is dict and data.get("jsonrpc") == "2.0" and data.get("id") == 1 and
                "result" in data and "error" not in data, "RPC_RESULT_INVALID")
        return data["result"]

    def check_chain(self):
        require(quantity(self.rpc("eth_chainId", [])) == self.settings["chain_id"], "RPC_WRONG_CHAIN")

    def observe(self, wallet, tx_hash=None):
        self.source(wallet)
        wallet = address(wallet)
        self.check_chain()
        if tx_hash is None:
            return {"state": "RPC_REPORTED_BALANCE", "balance_wei": str(quantity(
                self.rpc("eth_getBalance", [wallet, "latest"]))), "environment": self.environment,
                "settlement_verified": False}
        require(isinstance(tx_hash, str) and TXHASH.fullmatch(tx_hash), "INVALID_TX_HASH")
        transaction = self.rpc("eth_getTransactionByHash", [tx_hash])
        if transaction is None:
            return {"state": "TX_NOT_OBSERVED", "tx_hash": tx_hash, "settlement_verified": False}
        require(type(transaction) is dict and transaction.get("hash", "").lower() == tx_hash.lower() and
                address(transaction.get("from")) == wallet, "RPC_TRANSACTION_MISMATCH")
        receipt = self.rpc("eth_getTransactionReceipt", [tx_hash])
        if receipt is None:
            return {"state": "TX_PENDING", "tx_hash": tx_hash, "settlement_verified": False}
        require(type(receipt) is dict and receipt.get("transactionHash", "").lower() == tx_hash.lower() and
                address(receipt.get("from")) == wallet and
                receipt.get("status") in ("0x0", "0x1"), "RPC_RECEIPT_MISMATCH")
        return {"state": "TX_RECEIPT_OBSERVED", "tx_hash": tx_hash,
                "execution_success": receipt["status"] == "0x1",
                "block_hash": receipt.get("blockHash"), "block_number": receipt.get("blockNumber"),
                "settlement_verified": False, "finality": "NOT_VERIFIED"}

    def validate(self, operation):
        require(type(operation) is dict and set(operation) == {
            "kind", "environment", "source", "transaction",
        } and operation["kind"] == "evm.native_transfer", "INVALID_EVM_OPERATION")
        resource = self.source(operation["source"])
        require(operation["environment"] == self.environment, "EVM_ENVIRONMENT_MISMATCH")
        t = operation["transaction"]
        require(type(t) is dict and set(t) == {"type", "chainId", "nonce", "to", "value", "gas",
            "maxFeePerGas", "maxPriorityFeePerGas", "data", "accessList"}, "EVM_TRANSACTION_FIELDS")
        for field in ("type", "chainId", "nonce", "value", "gas", "maxFeePerGas", "maxPriorityFeePerGas"):
            require(type(t[field]) is int and 0 <= t[field] < 2**256, "EVM_INTEGER_REQUIRED")
        require(t["type"] == 2 and t["chainId"] == self.settings["chain_id"] and
                t["gas"] == 21000 and t["data"] == "0x" and t["accessList"] == [],
                "ONLY_NATIVE_EIP1559_ALLOWED")
        recipient = address(t["to"])
        require(recipient in [address(x) for x in self.settings["recipients"]] and
                recipient != address(operation["source"]), "EVM_RECIPIENT_NOT_ALLOWED")
        require(0 < t["value"] <= self.settings["max_value_wei"] and
                0 < t["maxPriorityFeePerGas"] <= t["maxFeePerGas"] and
                t["gas"] * t["maxFeePerGas"] <= self.settings["max_fee_wei"], "EVM_VALUE_OR_FEE_LIMIT")
        return "financial.evm.send_native", resource, f'evm:{t["chainId"]}:{recipient}'

    def preflight(self, operation):
        self.validate(operation)
        self.check_chain()
        t = operation["transaction"]
        for wallet in (operation["source"], t["to"]):
            require(self.rpc("eth_getCode", [address(wallet), "pending"]) == "0x",
                    "CONTRACT_OR_DELEGATED_ACCOUNT_NOT_SUPPORTED")
        require(quantity(self.rpc("eth_getTransactionCount", [address(operation["source"]), "pending"])) ==
                t["nonce"], "EVM_NONCE_CHANGED")
        balance = quantity(self.rpc("eth_getBalance", [address(operation["source"]), "pending"]))
        require(balance >= t["value"] + t["gas"] * t["maxFeePerGas"], "EVM_INSUFFICIENT_BALANCE")

    def signed_transaction(self, operation, raw):
        """Recover the source and compare EVERY execution field before broadcasting."""
        self.validate(operation)
        require(isinstance(raw, str) and re.fullmatch(r"0x02[0-9a-fA-F]{2,2048}", raw) and
                len(raw) % 2 == 0, "ONLY_SIGNED_EIP1559_ALLOWED")
        try:
            encoded = HexBytes(raw)
            decoded = TypedTransaction.from_bytes(encoded).as_dict()
            signer = Account.recover_transaction(encoded)
            expected = operation["transaction"]
            require(set(decoded) == set(expected) | {"v", "r", "s"}, "SIGNED_FIELDS_MISMATCH")
            normalized = {**decoded, "to": "0x" + bytes(decoded["to"]).hex(),
                          "data": "0x" + bytes(decoded["data"]).hex(),
                          "accessList": list(decoded["accessList"])}
            require(all(normalized[k] == expected[k] for k in expected), "SIGNED_FIELDS_MISMATCH")
            require(address(signer) == address(operation["source"]), "SIGNED_SOURCE_MISMATCH")
            return "0x" + keccak(encoded).hex()
        except Rejected:
            raise
        except (ValueError, TypeError, KeyError, IndexError):
            raise Rejected("SIGNED_TRANSACTION_INVALID") from None

    def send(self, operation, raw):
        """Broadcast after Gateway preflight and its final root-registry recheck."""
        expected = self.signed_transaction(operation, raw)
        result = self.rpc("eth_sendRawTransaction", [raw])
        require(isinstance(result, str) and result.lower() == expected, "BROADCAST_HASH_MISMATCH")
        return {"state": "TX_BROADCAST", "tx_hash": expected, "environment": self.environment,
                "settlement_verified": False, "sandbox_ledger_credited": False}
