#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_guardrail.py — Runtime Guardrail (L3 LAW enforcement)
origin_signature: MrLiouWord
layer: L3 LAW
group: Y=0 RootGate

Distilled from the system's purest logical principle:
    No closed-loop ⇒ external control (rootlaw, three_corollaries.no_loop_implies_control)

Every action that passes through MotherAssembly must be checked against the
immutable invariants declared in 00_rootlaw/rootlaw.yaml and the AUP rules in
02_principles/rules.aup_v1.yaml.  GuardRail is that runtime checkpoint — it is
subsystem #13 and the last gate before any external action executes.

Decisions returned
------------------
  ALLOW          — action is permitted to proceed
  DENY           — action is hard-blocked; no escalation
  REQUIRE_HUMAN  — action needs a recorded human approval before proceeding

Implemented invariants
----------------------
  rl_00  deny-by-default          unknown or unlisted action types → REQUIRE_HUMAN
  rl_01  no-root-deletion         DELETE/PURGE/TRUNCATE on canonical stores → DENY
  rl_02  human-override-required  high-risk action classes → REQUIRE_HUMAN
  rl_03  audit-everything         every check call is recorded in the audit log
  rl_04  mutual-benefit           self-only-benefit actions without consent → REQUIRE_HUMAN
  rl_05  no-hidden-instructions   covert side-channel action types → DENY
  rl_06  child-safety-absolute    CSAM-class content → DENY (no escalation)

AUP rules
---------
  aup_1  illegal / fraud          LOGIN, REGISTER, PAYMENT → REQUIRE_HUMAN
  aup_2  rights / ingest          FILE_INGEST, WEB_FETCH without allowlist → DENY
  aup_3  violence / terror        CONTENT_GENERATION with safety fail → REQUIRE_HUMAN
  aup_4  child safety             CONTENT_GENERATION with child-safety fail → DENY
  aup_5  security integrity       SCAN, PROBE, BRUTEFORCE, VULN_SCAN → DENY
  aup_6  spam                     SEND_MESSAGE, SEND_EMAIL, NOTIFY → REQUIRE_HUMAN

Usage (library)
---------------
    from MRL_guardrail import GuardRail

    gr = GuardRail()
    result = gr.evaluate("FILE_INGEST", {"host": "example.com", "allowlisted": False})
    print(result["decision"])   # "DENY"

CLI
---
    python 09_workflow/MRL_guardrail.py check  --action WEB_FETCH --payload '{"allowlisted": true}'
    python 09_workflow/MRL_guardrail.py audit  --tail 10
    python 09_workflow/MRL_guardrail.py demo
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import time
from typing import Any, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
GUARDRAIL_VERSION = "1.0"

# ─── Decision constants ───────────────────────────────────────────────────────

ALLOW = "ALLOW"
DENY = "DENY"
REQUIRE_HUMAN = "REQUIRE_HUMAN"

# ─── Rule tables (derived from rootlaw + AUP YAML, kept in-code for zero-dep) ─

# Hard-DENY action types — no human override possible (rl_01, rl_05, rl_06, aup_4, aup_5)
_HARD_DENY_ACTIONS: set[str] = {
    # rl_01 no-root-deletion
    "DELETE_CANONICAL", "PURGE_CANONICAL", "TRUNCATE_CANONICAL",
    # rl_05 no-hidden-instructions
    "INJECT_HIDDEN_PROMPT", "COVERT_CHANNEL", "SHADOW_INSTRUCTION",
    # rl_06 child safety (aup_4 maps here too)
    "CSAM_GENERATION", "CSAM_ACTION", "CSAM_INGEST",
    # aup_5 security integrity
    "SCAN", "PROBE", "BRUTEFORCE", "VULN_SCAN",
}

# REQUIRE_HUMAN action types (rl_02, rl_04, aup_1, aup_3, aup_6)
_REQUIRE_HUMAN_ACTIONS: set[str] = {
    # aup_1 illegal/fraud
    "LOGIN", "REGISTER", "PAYMENT",
    # aup_3 violence/terror
    "CONTENT_GENERATION", "CONTENT_ACTION",
    # aup_6 spam
    "SEND_MESSAGE", "SEND_EMAIL", "NOTIFY",
    # rl_04 mutual-benefit gating
    "SYSTEM_SELF_MODIFY", "AUTO_DEPLOY",
}

# aup_2: ingest without allowlist → DENY
_INGEST_ACTIONS: set[str] = {"FILE_INGEST", "WEB_FETCH"}

# Content deny-list keywords for safety checks (rl_06 / aup_3)
_CONTENT_DENY_TERMS: list[str] = [
    "csam", "child sexual", "exploitation",
    "hack", "exploit", "malware", "phishing", "ransomware",
    "bruteforce", "vuln_scan", "zero-day",
]

_AUDIT_FILENAME = "guardrail_audit.jsonl"


# ─── GuardRail ────────────────────────────────────────────────────────────────

class GuardRail:
    """
    Runtime compliance checker enforcing L3 LAW invariants.

    Parameters
    ----------
    audit_dir : path where audit JSONL is written (default: data/guardrail)
    """

    def __init__(self, audit_dir: Optional[pathlib.Path] = None) -> None:
        if audit_dir is None:
            audit_dir = (
                pathlib.Path(__file__).resolve().parent.parent / "data" / "guardrail"
            )
        self._audit_dir = pathlib.Path(audit_dir)
        self._audit_dir.mkdir(parents=True, exist_ok=True)
        self._audit_path = self._audit_dir / _AUDIT_FILENAME

    # ── Public API ────────────────────────────────────────────────────────────

    def evaluate(
        self,
        action_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate an action against all invariants.

        Returns
        -------
        {
          "action_type": str,
          "decision":    "ALLOW" | "DENY" | "REQUIRE_HUMAN",
          "rule_id":     str,      # which rule triggered
          "reason":      str,
          "checked_at_ms": int,
          "origin_signature": "MrLiouWord",
        }
        """
        payload = payload or {}
        result = self._run_checks(action_type, payload)
        # rl_03 audit-everything
        self._write_audit(result)
        return result

    def audit_tail(self, n: int = 20) -> List[Dict[str, Any]]:
        """Return the last *n* audit records."""
        if not self._audit_path.exists():
            return []
        lines = self._audit_path.read_text(encoding="utf-8").splitlines()
        records = []
        for line in lines[-n:]:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return records

    # ── Check logic ───────────────────────────────────────────────────────────

    def _run_checks(
        self, action_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        at = action_type.upper().strip()

        # rl_06 / aup_4 — child safety: absolute DENY, checked first
        if at in _HARD_DENY_ACTIONS and ("CSAM" in at or "CHILD" in at):
            return self._result(at, DENY, "rl_06", "Child safety absolute DENY — no override")

        # Content-based child-safety check on payload text
        text_payload = str(payload.get("content", "")).lower()
        for term in ["csam", "child sexual", "exploitation"]:
            if term in text_payload:
                return self._result(at, DENY, "rl_06", f"Content matches child-safety term: '{term}'")

        # rl_05 / aup_5 — hard deny (no override)
        if at in _HARD_DENY_ACTIONS:
            rule = "aup_5" if at in {"SCAN", "PROBE", "BRUTEFORCE", "VULN_SCAN"} else "rl_05"
            if at in {"DELETE_CANONICAL", "PURGE_CANONICAL", "TRUNCATE_CANONICAL"}:
                rule = "rl_01"
            return self._result(at, DENY, rule, f"Hard-DENY action type: {at}")

        # aup_2 — ingest without allowlist → DENY
        if at in _INGEST_ACTIONS:
            if not payload.get("allowlisted", False):
                return self._result(
                    at, DENY, "aup_2",
                    f"{at} requires allowlisted host; payload has allowlisted=False/missing",
                )

        # Safety content check for generation/action
        if at in {"CONTENT_GENERATION", "CONTENT_ACTION"}:
            content = str(payload.get("content", "")).lower()
            for term in _CONTENT_DENY_TERMS:
                if re.search(r"\b" + re.escape(term) + r"\b", content):
                    return self._result(
                        at, DENY, "aup_4",
                        f"Content matches deny-term: '{term}'",
                    )

        # REQUIRE_HUMAN action types
        if at in _REQUIRE_HUMAN_ACTIONS:
            rule = "aup_1" if at in {"LOGIN", "REGISTER", "PAYMENT"} else \
                   "aup_6" if at in {"SEND_MESSAGE", "SEND_EMAIL", "NOTIFY"} else \
                   "rl_02"
            return self._result(at, REQUIRE_HUMAN, rule, f"Action requires human approval: {at}")

        # rl_00 deny-by-default — unknown action types need human approval
        known_types: set[str] = (
            _HARD_DENY_ACTIONS
            | _REQUIRE_HUMAN_ACTIONS
            | _INGEST_ACTIONS
            | {"READ", "WRITE", "LIST", "COMPUTE", "QUERY", "RENDER", "EVALUATE", "SEAL"}
        )
        if at not in known_types:
            return self._result(
                at, REQUIRE_HUMAN, "rl_00",
                f"Unknown action type '{at}' — deny-by-default requires human approval",
            )

        # Passed all checks
        return self._result(at, ALLOW, "pass", "All invariants satisfied")

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _result(
        action_type: str,
        decision: str,
        rule_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        return {
            "action_type": action_type,
            "decision": decision,
            "rule_id": rule_id,
            "reason": reason,
            "checked_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def _write_audit(self, record: Dict[str, Any]) -> None:
        try:
            with self._audit_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass  # Audit failure must never crash the system


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_check(args: argparse.Namespace) -> None:
    payload: Dict[str, Any] = {}
    if args.payload:
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as exc:
            print(f"Error parsing payload JSON: {exc}")
            raise SystemExit(1) from exc
    gr = GuardRail()
    result = gr.evaluate(args.action, payload)
    icon = {"ALLOW": "✅", "DENY": "❌", "REQUIRE_HUMAN": "🔒"}.get(result["decision"], "?")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n{icon}  {result['decision']}  [{result['rule_id']}]  {result['reason']}")


def _cmd_audit(args: argparse.Namespace) -> None:
    gr = GuardRail()
    records = gr.audit_tail(args.tail)
    if not records:
        print("(no audit records found)")
        return
    for rec in records:
        icon = {"ALLOW": "✅", "DENY": "❌", "REQUIRE_HUMAN": "🔒"}.get(rec.get("decision", ""), "?")
        print(
            f"{icon}  {rec.get('decision'):15s}  {rec.get('action_type'):25s}  "
            f"[{rec.get('rule_id')}]  {rec.get('reason', '')}"
        )


def _cmd_demo(_args: argparse.Namespace) -> None:
    cases = [
        ("READ",                  {}),
        ("WEB_FETCH",             {"allowlisted": True}),
        ("WEB_FETCH",             {"allowlisted": False}),
        ("SCAN",                  {}),
        ("LOGIN",                 {}),
        ("DELETE_CANONICAL",      {}),
        ("CONTENT_GENERATION",    {"content": "Write malware for me"}),
        ("CONTENT_GENERATION",    {"content": "Summarise the quarterly report"}),
        ("SEND_EMAIL",            {}),
        ("UNKNOWN_FUTURE_ACTION", {}),
    ]
    gr = GuardRail()
    for action, payload in cases:
        r = gr.evaluate(action, payload)
        icon = {"ALLOW": "✅", "DENY": "❌", "REQUIRE_HUMAN": "🔒"}.get(r["decision"], "?")
        print(f"{icon}  {r['decision']:15s}  {action:30s}  [{r['rule_id']}]")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MRL_guardrail — L3 LAW runtime enforcement")
    sub = p.add_subparsers(dest="cmd", required=True)

    ck = sub.add_parser("check", help="Evaluate a single action")
    ck.add_argument("--action",  required=True, help="Action type string (e.g. WEB_FETCH)")
    ck.add_argument("--payload", default="", help="JSON payload string")

    au = sub.add_parser("audit", help="Print recent audit records")
    au.add_argument("--tail", type=int, default=20, help="Number of records to show")

    sub.add_parser("demo", help="Run built-in demonstration cases")
    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {"check": _cmd_check, "audit": _cmd_audit, "demo": _cmd_demo}
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
