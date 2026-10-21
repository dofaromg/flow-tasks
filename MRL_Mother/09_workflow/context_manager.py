#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
context_manager.py — Context Window Manager
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

Industry capability: intelligent context window management — prevents
                     token overflow and keeps the most relevant messages
                     within the model's context budget.
MRL extension: context decisions are stamped with origin_signature and are
               compatible with the ConversationSession message format.

Strategies
----------
  TRUNCATE_OLDEST  — drop oldest non-system messages until within budget
  SLIDING_WINDOW   — keep the system prompt + last N messages
  SUMMARISE_OLDEST — replace oldest messages with a summary stub

Usage (library)
---------------
    from context_manager import ContextManager, Strategy

    cm = ContextManager(max_tokens=4096, strategy=Strategy.TRUNCATE_OLDEST)
    messages = [{"role": "user", "content": "..."}, ...]
    trimmed, stats = cm.fit(messages)
    print(stats["dropped"])   # number of messages dropped

CLI
---
    python 09_workflow/context_manager.py fit \
        --messages '[{"role":"user","content":"Hello"}]' \
        --max-tokens 100
"""

from __future__ import annotations

import argparse
import json
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"

# Rough chars-per-token heuristic (conservative — works for Latin and CJK)
_CHARS_PER_TOKEN = 3


def _estimate_tokens(messages: List[Dict[str, Any]]) -> int:
    """Estimate total token count for a message list."""
    total = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, list):
            # Multi-modal blocks
            content = " ".join(
                b.get("text", "") for b in content if isinstance(b, dict)
            )
        total += max(1, len(str(content)) // _CHARS_PER_TOKEN)
        total += 4  # per-message overhead (role + formatting)
    return total


# ─── Strategy ────────────────────────────────────────────────────────────────

class Strategy(str, Enum):
    TRUNCATE_OLDEST = "truncate_oldest"
    SLIDING_WINDOW  = "sliding_window"
    SUMMARISE_OLDEST = "summarise_oldest"


# ─── ContextManager ──────────────────────────────────────────────────────────

class ContextManager:
    """
    Fits a message list into a token budget.

    Parameters
    ----------
    max_tokens   : int
        Token budget (default 4096). Includes both input and a reserved
        margin for the model's reply.
    reply_reserve : int
        Tokens to reserve for the model's reply (default 512).
    strategy     : Strategy
        How to reduce context when over budget (default TRUNCATE_OLDEST).
    summary_stub : str
        Text to insert when using SUMMARISE_OLDEST strategy (override to
        use an actual summariser).
    """

    def __init__(
        self,
        max_tokens: int = 4096,
        reply_reserve: int = 512,
        strategy: Strategy = Strategy.TRUNCATE_OLDEST,
        summary_stub: Optional[str] = None,
    ) -> None:
        self.max_tokens = max_tokens
        self.reply_reserve = reply_reserve
        self.strategy = strategy
        self._summary_stub = summary_stub or "[Earlier messages summarised to fit context window.]"
        self._budget = max(1, max_tokens - reply_reserve)

    # ── Core fit ─────────────────────────────────────────────────────────────

    def fit(
        self,
        messages: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Reduce *messages* to fit within the token budget.

        Returns
        -------
        (trimmed_messages, stats_dict)

        stats_dict fields:
          original_count  : number of input messages
          final_count     : number of output messages
          dropped         : number of messages removed
          strategy_used   : strategy name
          estimated_tokens: final estimated token count
          fitted_at_ms    : timestamp
          origin_signature
        """
        original = list(messages)
        original_count = len(original)

        if _estimate_tokens(original) <= self._budget:
            return original, self._stats(original_count, original, 0)

        if self.strategy == Strategy.SLIDING_WINDOW:
            trimmed, dropped = self._sliding_window(original)
        elif self.strategy == Strategy.SUMMARISE_OLDEST:
            trimmed, dropped = self._summarise_oldest(original)
        else:
            trimmed, dropped = self._truncate_oldest(original)

        return trimmed, self._stats(original_count, trimmed, dropped)

    # ── Strategies ────────────────────────────────────────────────────────────

    def _truncate_oldest(
        self, messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Drop oldest non-system messages until within budget."""
        system = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]
        dropped = 0

        while non_system and _estimate_tokens(system + non_system) > self._budget:
            non_system.pop(0)
            dropped += 1

        return system + non_system, dropped

    def _sliding_window(
        self, messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Keep system prompt + as many recent messages as fit."""
        system = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        window: List[Dict[str, Any]] = []
        for m in reversed(non_system):
            candidate = system + [m] + window
            if _estimate_tokens(candidate) <= self._budget:
                window.insert(0, m)
            else:
                break

        dropped = len(non_system) - len(window)
        return system + window, dropped

    def _summarise_oldest(
        self, messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Replace oldest messages with a summary stub until within budget."""
        system = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        stub: Dict[str, Any] = {
            "role": "system",
            "content": self._summary_stub,
            "ts_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
            "_context_stub": True,
        }

        dropped = 0
        while non_system and _estimate_tokens(system + [stub] + non_system) > self._budget:
            non_system.pop(0)
            dropped += 1

        base = system + ([stub] if dropped else []) + non_system
        return base, dropped

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _stats(
        self,
        original_count: int,
        trimmed: List[Dict[str, Any]],
        dropped: int,
    ) -> Dict[str, Any]:
        return {
            "original_count": original_count,
            "final_count": len(trimmed),
            "dropped": dropped,
            "strategy_used": self.strategy.value,
            "estimated_tokens": _estimate_tokens(trimmed),
            "budget_tokens": self._budget,
            "fitted_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def estimate(self, messages: List[Dict[str, Any]]) -> int:
        """Return estimated token count for *messages*."""
        return _estimate_tokens(messages)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_fit(args: argparse.Namespace) -> None:
    messages = json.loads(args.messages)
    strategy = Strategy(args.strategy)
    cm = ContextManager(max_tokens=args.max_tokens, strategy=strategy)
    trimmed, stats = cm.fit(messages)
    print("=== Stats ===")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"\n=== Trimmed ({len(trimmed)} messages) ===")
    for m in trimmed:
        snippet = str(m.get("content", ""))[:80]
        print(f"  [{m['role']}]  {snippet}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ContextManager — context window management")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fit", help="Fit a message list to a token budget")
    f.add_argument("--messages", required=True, help="JSON array of message dicts")
    f.add_argument("--max-tokens", type=int, default=4096)
    f.add_argument(
        "--strategy",
        default=Strategy.TRUNCATE_OLDEST.value,
        choices=[s.value for s in Strategy],
    )

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    if args.cmd == "fit":
        _cmd_fit(args)


if __name__ == "__main__":
    main()
