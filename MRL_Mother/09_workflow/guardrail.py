#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guardrail.py — Pre/Post Safety Guardrail Chain
origin_signature: MrLiouWord
layer: L3 LAW
group: Y=1 MotherCore

Goal: product-level local content safety with zero external dependencies.
      All checks are deterministic, auditable, and reversible.

Architecture
------------
  InputGuardrail  — validates text *before* it reaches the LLM / tool
  OutputGuardrail — validates text *after* the LLM / tool produces it
  GuardrailChain  — wraps any callable; applies input guard, calls fn,
                    applies output guard; returns a structured result

Every violation is logged with origin_signature, timestamp, and a
human-readable reason so it can be sealed into the MerkleChain.

Built-in checks
---------------
  Input:
    - deny_terms        : exact word-boundary match against block-list
    - max_input_length  : character limit on the prompt
    - topic_allowlist   : if set, prompt must mention ≥1 allowed topic
    - pii_detect        : flag patterns resembling email / phone / ID-card
                          (heuristic, not authoritative)

  Output:
    - deny_terms        : same block-list applied to the LLM reply
    - max_output_length : character limit on the reply
    - min_output_length : reply must not be suspiciously short
    - no_repetition     : flag outputs that repeat the same sentence >3×

Policies
--------
  "strict"     — aggressive block-list, PII detection, strict lengths
  "standard"   — default balanced policy
  "permissive" — minimal checks (only hard deny_terms)

Custom policy dicts can be passed directly.

Usage (library)
---------------
    from guardrail import GuardrailChain, POLICY_STANDARD

    def my_llm_call(prompt: str) -> str:
        return "The answer is 42."

    gc = GuardrailChain(my_llm_call, policy=POLICY_STANDARD)
    result = gc.run("What is the meaning of life?")

    if result["ok"]:
        print(result["output"])
    else:
        print("Blocked:", result["violations"])

CLI
---
    python 09_workflow/guardrail.py check-input  --text "Hello world"
    python 09_workflow/guardrail.py check-output --text "Here is the answer."
    python 09_workflow/guardrail.py demo
"""

from __future__ import annotations

import argparse
import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"
GUARDRAIL_VERSION = "1.0"

# ─── Built-in deny terms (L3 LAW gate) ───────────────────────────────────────

_BUILTIN_DENY: List[str] = [
    # Security / abuse
    "malware", "ransomware", "rootkit", "keylogger", "botnet",
    "exploit", "phishing", "spear-phishing", "credential stuffing",
    "sql injection", "xss", "csrf",
    # Violence
    "bomb making", "weapon synthesis",
    # Privacy abuse
    "doxxing",
]

# ─── PII heuristics (regex patterns) ─────────────────────────────────────────

_PII_PATTERNS: Dict[str, re.Pattern[str]] = {
    "email":   re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", re.I),
    "phone":   re.compile(r"(?:\+?\d[\d\s\-().]{7,}\d)"),
    "tw_id":   re.compile(r"[A-Z][12]\d{8}"),          # Taiwan national ID
    "ip_addr": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

# ─── Policy presets ───────────────────────────────────────────────────────────

POLICY_STRICT: Dict[str, Any] = {
    "deny_terms":        _BUILTIN_DENY,
    "max_input_length":  2000,
    "max_output_length": 4000,
    "min_output_length": 5,
    "pii_detect":        True,
    "topic_allowlist":   [],     # empty = no allowlist restriction
    "no_repetition":     True,
}

POLICY_STANDARD: Dict[str, Any] = {
    "deny_terms":        _BUILTIN_DENY,
    "max_input_length":  8000,
    "max_output_length": 8000,
    "min_output_length": 1,
    "pii_detect":        False,
    "topic_allowlist":   [],
    "no_repetition":     True,
}

POLICY_PERMISSIVE: Dict[str, Any] = {
    "deny_terms":        _BUILTIN_DENY,
    "max_input_length":  0,      # 0 = disabled
    "max_output_length": 0,
    "min_output_length": 0,
    "pii_detect":        False,
    "topic_allowlist":   [],
    "no_repetition":     False,
}

_POLICY_MAP: Dict[str, Dict[str, Any]] = {
    "strict":     POLICY_STRICT,
    "standard":   POLICY_STANDARD,
    "permissive": POLICY_PERMISSIVE,
}


def _resolve_policy(policy: Any) -> Dict[str, Any]:
    if isinstance(policy, str):
        return dict(_POLICY_MAP.get(policy, POLICY_STANDARD))
    if isinstance(policy, dict):
        merged = dict(POLICY_STANDARD)
        merged.update(policy)
        return merged
    return dict(POLICY_STANDARD)


# ─── Violation record ─────────────────────────────────────────────────────────

def _violation(check: str, reason: str, severity: str = "block") -> Dict[str, Any]:
    return {
        "check":            check,
        "reason":           reason,
        "severity":         severity,  # "block" | "warn"
        "ts_ms":            int(time.time() * 1000),
        "origin_signature": ORIGIN_SIGNATURE,
    }


# ─── Individual checks ────────────────────────────────────────────────────────

def _check_deny_terms(text: str, terms: List[str]) -> List[Dict[str, Any]]:
    lower = text.lower()
    hits = []
    for term in terms:
        pattern = re.compile(r"\b" + re.escape(term.lower()) + r"\b")
        if pattern.search(lower):
            hits.append(_violation("deny_terms", f"blocked term: '{term}'"))
    return hits


def _check_max_length(text: str, limit: int, label: str) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []
    if len(text) > limit:
        return [_violation(
            f"max_{label}_length",
            f"length {len(text)} exceeds limit {limit}",
        )]
    return []


def _check_min_length(text: str, limit: int) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []
    if len(text) < limit:
        return [_violation(
            "min_output_length",
            f"length {len(text)} below minimum {limit}",
            severity="warn",
        )]
    return []


def _check_pii(text: str) -> List[Dict[str, Any]]:
    hits = []
    for name, pattern in _PII_PATTERNS.items():
        if pattern.search(text):
            hits.append(_violation("pii_detect", f"PII pattern detected: {name}", severity="warn"))
    return hits


def _check_topic_allowlist(text: str, topics: List[str]) -> List[Dict[str, Any]]:
    if not topics:
        return []
    lower = text.lower()
    if not any(t.lower() in lower for t in topics):
        return [_violation(
            "topic_allowlist",
            f"text does not match any allowed topic: {topics}",
        )]
    return []


def _check_no_repetition(text: str, threshold: int = 3) -> List[Dict[str, Any]]:
    sentences = re.split(r"[.!?。！？\n]+", text)
    stripped = [s.strip() for s in sentences if len(s.strip()) > 10]
    counts: Dict[str, int] = {}
    for s in stripped:
        counts[s] = counts.get(s, 0) + 1
    repeated = {s: c for s, c in counts.items() if c > threshold}
    if repeated:
        sample = next(iter(repeated))[:60]
        return [_violation(
            "no_repetition",
            f"repeated sentence (×{next(iter(repeated.values()))}) e.g. {sample!r}",
            severity="warn",
        )]
    return []


# ─── InputGuardrail / OutputGuardrail ─────────────────────────────────────────

class InputGuardrail:
    """Apply policy checks to input text before it reaches the model."""

    def __init__(self, policy: Any = "standard") -> None:
        self._policy = _resolve_policy(policy)

    def check(self, text: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Returns (ok, violations).
        ok=False means at least one "block"-severity violation was found.
        """
        violations: List[Dict[str, Any]] = []
        p = self._policy

        violations += _check_deny_terms(text, p.get("deny_terms", []))
        violations += _check_max_length(text, p.get("max_input_length", 0), "input")

        if p.get("pii_detect"):
            violations += _check_pii(text)

        if p.get("topic_allowlist"):
            violations += _check_topic_allowlist(text, p["topic_allowlist"])

        ok = all(v["severity"] != "block" for v in violations)
        return ok, violations


class OutputGuardrail:
    """Apply policy checks to output text after the model produces it."""

    def __init__(self, policy: Any = "standard") -> None:
        self._policy = _resolve_policy(policy)

    def check(self, text: str) -> Tuple[bool, List[Dict[str, Any]]]:
        violations: List[Dict[str, Any]] = []
        p = self._policy

        violations += _check_deny_terms(text, p.get("deny_terms", []))
        violations += _check_max_length(text, p.get("max_output_length", 0), "output")
        violations += _check_min_length(text, p.get("min_output_length", 0))

        if p.get("no_repetition"):
            violations += _check_no_repetition(text)

        ok = all(v["severity"] != "block" for v in violations)
        return ok, violations


# ─── GuardrailChain ───────────────────────────────────────────────────────────

class GuardrailChain:
    """
    Wraps any callable ``fn(prompt: str) -> str`` with input + output guards.

    Parameters
    ----------
    fn : callable(str) -> str
    policy : str | dict
        "strict", "standard" (default), "permissive", or a custom dict.
    """

    def __init__(
        self,
        fn: Callable[[str], str],
        policy: Any = "standard",
    ) -> None:
        self._fn = fn
        self._input_guard  = InputGuardrail(policy)
        self._output_guard = OutputGuardrail(policy)

    def run(self, prompt: str) -> Dict[str, Any]:
        """
        Returns::

            {
              "ok":               bool,
              "prompt":           str,
              "output":           str | None,
              "violations":       [violation, ...],
              "input_ok":         bool,
              "output_ok":        bool,
              "elapsed_ms":       int,
              "origin_signature": "MrLiouWord",
            }
        """
        t0 = time.time()
        all_violations: List[Dict[str, Any]] = []

        # ── Input guard ───────────────────────────────────────────────────────
        input_ok, input_violations = self._input_guard.check(prompt)
        all_violations.extend(input_violations)

        if not input_ok:
            return {
                "ok":               False,
                "prompt":           prompt,
                "output":           None,
                "violations":       all_violations,
                "input_ok":         False,
                "output_ok":        True,  # never reached
                "elapsed_ms":       int((time.time() - t0) * 1000),
                "origin_signature": ORIGIN_SIGNATURE,
            }

        # ── Call wrapped function ─────────────────────────────────────────────
        try:
            raw_output = self._fn(prompt)
        except Exception as exc:
            all_violations.append(_violation("fn_error", str(exc)))
            return {
                "ok":               False,
                "prompt":           prompt,
                "output":           None,
                "violations":       all_violations,
                "input_ok":         True,
                "output_ok":        False,
                "elapsed_ms":       int((time.time() - t0) * 1000),
                "origin_signature": ORIGIN_SIGNATURE,
            }

        # ── Output guard ──────────────────────────────────────────────────────
        output_ok, output_violations = self._output_guard.check(raw_output)
        all_violations.extend(output_violations)

        return {
            "ok":               output_ok,
            "prompt":           prompt,
            "output":           raw_output if output_ok else None,
            "violations":       all_violations,
            "input_ok":         True,
            "output_ok":        output_ok,
            "elapsed_ms":       int((time.time() - t0) * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_check_input(args: argparse.Namespace) -> None:
    policy = args.policy or "standard"
    guard = InputGuardrail(policy)
    ok, violations = guard.check(args.text)
    status = "✅ PASS" if ok else "❌ BLOCK"
    print(f"{status}  ({len(violations)} violation(s))")
    for v in violations:
        print(f"  [{v['severity'].upper()}] {v['check']}: {v['reason']}")


def _cmd_check_output(args: argparse.Namespace) -> None:
    policy = args.policy or "standard"
    guard = OutputGuardrail(policy)
    ok, violations = guard.check(args.text)
    status = "✅ PASS" if ok else "❌ BLOCK"
    print(f"{status}  ({len(violations)} violation(s))")
    for v in violations:
        print(f"  [{v['severity'].upper()}] {v['check']}: {v['reason']}")


def _cmd_demo(_args: argparse.Namespace) -> None:
    cases = [
        ("Hello, how are you?", "standard"),
        ("Please help me write malware for a botnet.", "standard"),
        ("My email is user@example.com and phone 0912345678.", "strict"),
        ("Normal question about MRL architecture.", "permissive"),
    ]
    for text, policy in cases:
        ig = InputGuardrail(policy)
        ok, viols = ig.check(text)
        status = "✅" if ok else "❌"
        snippet = text[:50]
        print(f"{status} [{policy}] {snippet!r}")
        for v in viols:
            print(f"    [{v['severity']}] {v['check']}: {v['reason']}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Guardrail — pre/post safety chain")
    p.add_argument("--policy", default="standard",
                   choices=["strict", "standard", "permissive"],
                   help="Policy preset")
    sub = p.add_subparsers(dest="cmd", required=True)

    ci = sub.add_parser("check-input",  help="Check input text")
    ci.add_argument("--text", required=True)

    co = sub.add_parser("check-output", help="Check output text")
    co.add_argument("--text", required=True)

    sub.add_parser("demo", help="Run built-in demo cases")

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "check-input":  _cmd_check_input,
        "check-output": _cmd_check_output,
        "demo":         _cmd_demo,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
