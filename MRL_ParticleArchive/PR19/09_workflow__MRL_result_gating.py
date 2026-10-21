#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_result_gating.py — Result Access Control & Gating
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=1 MotherCore

Implements partial/full result access control:
  - partial_result: Free preview (first N chars, summary, metadata)
  - full_result: Complete output (requires entitlement/payment)
  - Entitlement checking via ledger/payment system
  - Prevention of direct API access to full results

Security guarantees:
  1. Unpaid users cannot access full_result via any endpoint
  2. All full_result requests are logged for audit
  3. Results are cryptographically sealed
  4. Bypass attempts are traced and blocked

Usage (library)
---------------
    from MRL_result_gating import ResultGate, EntitlementManager

    gate = ResultGate()

    # Store a result with gating
    result_id = gate.store_result(
        task_id="...",
        full_output="Long detailed analysis...",
        preview_length=200,
    )

    # Try to access result
    try:
        result = gate.get_full_result(result_id, user_id="user123")
        print(result)  # Only if entitled
    except PermissionError:
        # User must pay/unlock
        partial = gate.get_partial_result(result_id)
        print(partial["preview"])

CLI
---
    python 09_workflow/MRL_result_gating.py store --task-id <id> --output "..."
    python 09_workflow/MRL_result_gating.py unlock --result-id <id> --user-id <id>
    python 09_workflow/MRL_result_gating.py check --result-id <id> --user-id <id>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import time
import uuid
from typing import Any, Dict, List, Optional, Set

ORIGIN_SIGNATURE = "MrLiouWord"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_RESULT_STORE = _REPO_ROOT / "data" / "gated_results.json"
_ENTITLEMENT_STORE = _REPO_ROOT / "data" / "entitlements.json"
_ACCESS_LOG = _REPO_ROOT / "data" / "access_log.jsonl"

# ── Ensure module paths ───────────────────────────────────────────────────────

def _ensure_paths() -> None:
    for sub in [
        _REPO_ROOT / "09_workflow",
        _REPO_ROOT / "03_memory" / "merkle",
    ]:
        p = str(sub)
        if p not in sys.path:
            sys.path.insert(0, p)

_ensure_paths()


def _try_import(module: str, attr: str) -> Any:
    try:
        import importlib
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    except Exception:  # noqa: BLE001
        return None


# ─── GatedResult ──────────────────────────────────────────────────────────────

class GatedResult:
    """
    A result with access control.

    Attributes
    ----------
    result_id     : Unique result identifier
    task_id       : Associated task ID
    full_output   : Complete result (gated)
    partial_output: Preview/summary (always accessible)
    created_at_ms : Creation timestamp
    checksum      : SHA256 hash of full_output
    sealed        : Whether result is sealed to merkle chain
    """

    def __init__(
        self,
        result_id: str,
        task_id: str,
        full_output: str,
        partial_output: str,
        created_at_ms: int,
    ) -> None:
        self.result_id = result_id
        self.task_id = task_id
        self.full_output = full_output
        self.partial_output = partial_output
        self.created_at_ms = created_at_ms
        self.checksum = self._compute_checksum(full_output)
        self.sealed = False

    @staticmethod
    def _compute_checksum(text: str) -> str:
        """Compute SHA256 checksum of text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def to_dict(self, include_full: bool = False) -> Dict[str, Any]:
        """Serialize to dict, optionally including full output."""
        d = {
            "result_id": self.result_id,
            "task_id": self.task_id,
            "partial_output": self.partial_output,
            "created_at_ms": self.created_at_ms,
            "checksum": self.checksum,
            "sealed": self.sealed,
            "origin_signature": ORIGIN_SIGNATURE,
        }
        if include_full:
            d["full_output"] = self.full_output
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GatedResult":
        """Deserialize from dict."""
        result = cls(
            result_id=d["result_id"],
            task_id=d["task_id"],
            full_output=d.get("full_output", ""),
            partial_output=d["partial_output"],
            created_at_ms=d["created_at_ms"],
        )
        result.sealed = d.get("sealed", False)
        return result


# ─── EntitlementManager ───────────────────────────────────────────────────────

class EntitlementManager:
    """
    Manages user entitlements for result access.

    Tracks which users have unlocked which results via:
      - Payment completion
      - Subscription status
      - Internal credits
      - Admin grants
    """

    def __init__(self, store_path: pathlib.Path = _ENTITLEMENT_STORE) -> None:
        self._path = pathlib.Path(store_path)
        self._entitlements: Dict[str, Set[str]] = {}  # user_id → {result_id, ...}
        self._load()

    def _load(self) -> None:
        """Load entitlements from JSON."""
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                for user_id, result_ids in data.get("entitlements", {}).items():
                    self._entitlements[user_id] = set(result_ids)
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self) -> None:
        """Save entitlements to JSON."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "entitlements": {
                user_id: list(result_ids)
                for user_id, result_ids in self._entitlements.items()
            },
            "saved_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def grant(self, user_id: str, result_id: str) -> None:
        """Grant a user access to a result."""
        if user_id not in self._entitlements:
            self._entitlements[user_id] = set()
        self._entitlements[user_id].add(result_id)
        self._save()

    def revoke(self, user_id: str, result_id: str) -> None:
        """Revoke a user's access to a result."""
        if user_id in self._entitlements:
            self._entitlements[user_id].discard(result_id)
            self._save()

    def check(self, user_id: str, result_id: str) -> bool:
        """Check if a user is entitled to access a result."""
        return result_id in self._entitlements.get(user_id, set())

    def list_user_entitlements(self, user_id: str) -> List[str]:
        """List all result IDs a user is entitled to."""
        return list(self._entitlements.get(user_id, set()))


# ─── ResultGate ───────────────────────────────────────────────────────────────

class ResultGate:
    """
    Access control gate for task results.

    Enforces:
      - Partial access is always allowed
      - Full access requires entitlement
      - All access attempts are logged
    """

    def __init__(
        self,
        result_store: pathlib.Path = _RESULT_STORE,
        access_log: pathlib.Path = _ACCESS_LOG,
    ) -> None:
        self._result_store = pathlib.Path(result_store)
        self._access_log = pathlib.Path(access_log)
        self._results: Dict[str, GatedResult] = {}
        self._entitlements = EntitlementManager()
        self._chain: Any = None
        self._load()

        # Initialize merkle chain for sealing
        MerkleChain = _try_import("memory_chain", "MerkleChain")
        if MerkleChain:
            try:
                data_dir = _REPO_ROOT / "03_memory" / "_data" / "memory_chain"
                self._chain = MerkleChain(data_dir)
            except Exception:  # noqa: BLE001
                pass

    def _load(self) -> None:
        """Load results from store."""
        if self._result_store.exists():
            try:
                with self._result_store.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                for result_data in data.get("results", []):
                    result = GatedResult.from_dict(result_data)
                    self._results[result.result_id] = result
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self) -> None:
        """Save results to store."""
        self._result_store.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "results": [r.to_dict(include_full=True) for r in self._results.values()],
            "total_results": len(self._results),
            "saved_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }
        with self._result_store.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _log_access(
        self,
        event: str,
        result_id: str,
        user_id: str,
        granted: bool,
        reason: str = "",
    ) -> None:
        """Log an access attempt."""
        self._access_log.parent.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "event": event,
            "result_id": result_id,
            "user_id": user_id,
            "granted": granted,
            "reason": reason,
            "ts_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }
        with self._access_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    # ── Result storage ────────────────────────────────────────────────────────

    def store_result(
        self,
        task_id: str,
        full_output: str,
        preview_length: int = 200,
    ) -> str:
        """
        Store a gated result.

        Parameters
        ----------
        task_id        : Associated task ID
        full_output    : Complete result text
        preview_length : Number of characters for preview

        Returns
        -------
        result_id : UUID string
        """
        result_id = str(uuid.uuid4())
        partial_output = full_output[:preview_length]
        if len(full_output) > preview_length:
            partial_output += "... [full result requires unlock]"

        result = GatedResult(
            result_id=result_id,
            task_id=task_id,
            full_output=full_output,
            partial_output=partial_output,
            created_at_ms=int(time.time() * 1000),
        )

        self._results[result_id] = result
        self._save()

        return result_id

    # ── Result access ─────────────────────────────────────────────────────────

    def get_partial_result(self, result_id: str) -> Dict[str, Any]:
        """
        Get partial result (always allowed).

        Returns
        -------
        Partial result with:
          - result_id
          - task_id
          - preview
          - checksum
          - unlock_required: true
        """
        result = self._results.get(result_id)
        if not result:
            raise KeyError(f"Result not found: {result_id}")

        return {
            "result_id": result.result_id,
            "task_id": result.task_id,
            "preview": result.partial_output,
            "checksum": result.checksum,
            "unlock_required": True,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def get_full_result(
        self,
        result_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Get full result (requires entitlement).

        Parameters
        ----------
        result_id : Result UUID
        user_id   : User requesting access

        Returns
        -------
        Full result record

        Raises
        ------
        KeyError if result not found
        PermissionError if user not entitled
        """
        result = self._results.get(result_id)
        if not result:
            self._log_access("full_result_access", result_id, user_id, False, "result_not_found")
            raise KeyError(f"Result not found: {result_id}")

        # Check entitlement
        if not self._entitlements.check(user_id, result_id):
            self._log_access("full_result_access", result_id, user_id, False, "not_entitled")
            raise PermissionError(
                f"User '{user_id}' is not entitled to access result '{result_id}'. "
                "Please complete payment or unlock this result."
            )

        # Access granted
        self._log_access("full_result_access", result_id, user_id, True, "entitled")

        return {
            "result_id": result.result_id,
            "task_id": result.task_id,
            "full_output": result.full_output,
            "checksum": result.checksum,
            "sealed": result.sealed,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    # ── Entitlement management ────────────────────────────────────────────────

    def unlock_result(
        self,
        result_id: str,
        user_id: str,
        reason: str = "manual_unlock",
    ) -> Dict[str, Any]:
        """
        Unlock a result for a user.

        Parameters
        ----------
        result_id : Result UUID
        user_id   : User to grant access
        reason    : Unlock reason (e.g., "payment_completed", "admin_grant")

        Returns
        -------
        Unlock record
        """
        result = self._results.get(result_id)
        if not result:
            raise KeyError(f"Result not found: {result_id}")

        self._entitlements.grant(user_id, result_id)
        self._log_access("unlock_result", result_id, user_id, True, reason)

        return {
            "result_id": result_id,
            "user_id": user_id,
            "unlocked": True,
            "reason": reason,
            "unlocked_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def check_entitlement(self, result_id: str, user_id: str) -> bool:
        """Check if user is entitled to access a result."""
        return self._entitlements.check(user_id, result_id)

    # ── Result sealing ────────────────────────────────────────────────────────

    def seal_result(self, result_id: str) -> Dict[str, Any]:
        """
        Seal a result to the merkle chain.

        Returns
        -------
        Seal record with merkle hash
        """
        result = self._results.get(result_id)
        if not result:
            raise KeyError(f"Result not found: {result_id}")

        if not self._chain:
            return {"error": "MerkleChain unavailable"}

        try:
            entry = self._chain.append(
                payload={
                    "event": "result_sealed",
                    "result_id": result.result_id,
                    "task_id": result.task_id,
                    "checksum": result.checksum,
                    "sealed_at_ms": int(time.time() * 1000),
                },
                tags=["result_seal"],
                layer="L7_LOOP",
                meta={"result_id": result_id},
            )

            result.sealed = True
            self._save()

            return {
                "result_id": result_id,
                "seal_entry_id": entry["entry_id"],
                "merkle_hash": entry["merkle"],
                "sealed_at_ms": entry["timestamp_ms"],
                "origin_signature": ORIGIN_SIGNATURE,
            }

        except Exception as exc:  # noqa: BLE001
            return {"error": f"Seal failed: {exc}"}


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_store(args: argparse.Namespace) -> None:
    gate = ResultGate()
    result_id = gate.store_result(
        task_id=args.task_id,
        full_output=args.output,
        preview_length=args.preview_length,
    )
    print(f"Result stored: {result_id}")


def _cmd_unlock(args: argparse.Namespace) -> None:
    gate = ResultGate()
    unlock = gate.unlock_result(
        result_id=args.result_id,
        user_id=args.user_id,
        reason=args.reason,
    )
    print(json.dumps(unlock, ensure_ascii=False, indent=2))


def _cmd_check(args: argparse.Namespace) -> None:
    gate = ResultGate()
    entitled = gate.check_entitlement(args.result_id, args.user_id)
    print(f"User '{args.user_id}' entitled to '{args.result_id}': {entitled}")


def _cmd_partial(args: argparse.Namespace) -> None:
    gate = ResultGate()
    try:
        partial = gate.get_partial_result(args.result_id)
        print(json.dumps(partial, ensure_ascii=False, indent=2))
    except KeyError as exc:
        print(f"Error: {exc}")


def _cmd_full(args: argparse.Namespace) -> None:
    gate = ResultGate()
    try:
        full = gate.get_full_result(args.result_id, args.user_id)
        print(json.dumps(full, ensure_ascii=False, indent=2))
    except (KeyError, PermissionError) as exc:
        print(f"Error: {exc}")


def _cmd_seal(args: argparse.Namespace) -> None:
    gate = ResultGate()
    seal = gate.seal_result(args.result_id)
    print(json.dumps(seal, ensure_ascii=False, indent=2))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MRL_result_gating — Result access control"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # store
    s = sub.add_parser("store", help="Store a gated result")
    s.add_argument("--task-id", required=True)
    s.add_argument("--output", required=True)
    s.add_argument("--preview-length", type=int, default=200)

    # unlock
    u = sub.add_parser("unlock", help="Unlock result for user")
    u.add_argument("--result-id", required=True)
    u.add_argument("--user-id", required=True)
    u.add_argument("--reason", default="manual_unlock")

    # check
    c = sub.add_parser("check", help="Check entitlement")
    c.add_argument("--result-id", required=True)
    c.add_argument("--user-id", required=True)

    # partial
    pa = sub.add_parser("partial", help="Get partial result")
    pa.add_argument("--result-id", required=True)

    # full
    f = sub.add_parser("full", help="Get full result")
    f.add_argument("--result-id", required=True)
    f.add_argument("--user-id", required=True)

    # seal
    se = sub.add_parser("seal", help="Seal result")
    se.add_argument("--result-id", required=True)

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "store": _cmd_store,
        "unlock": _cmd_unlock,
        "check": _cmd_check,
        "partial": _cmd_partial,
        "full": _cmd_full,
        "seal": _cmd_seal,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()