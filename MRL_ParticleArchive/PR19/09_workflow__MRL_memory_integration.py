#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_memory_integration.py — Memory Layer Integration
origin_signature: MrLiouWord
layer: L3 LAW
group: Y=2 MemoryManagement

Integrates conversation_manager with MRL_MemoryVaultPG / MRL_MemoryLayer:
  - Every user/assistant/tool event writes to memory trace
  - Each session maintains merkle checksum + origin_signature
  - Supports session replay from memory records
  - Automatic memory sealing for completed sessions

This module bridges:
  - ConversationManager (session management)
  - MerkleChain (immutable audit trail)
  - VectorStore (RAG-ready embeddings)

Usage (library)
---------------
    from MRL_memory_integration import MemoryIntegratedConversation

    conv = MemoryIntegratedConversation()

    session_id = conv.new_session(system_prompt="You are MRL_AGI")
    conv.add_message(session_id, "user", "Hello")
    conv.add_message(session_id, "assistant", "Hi there!")

    # Memory is automatically traced
    trace = conv.get_session_trace(session_id)
    print(trace["merkle_entries"])

    # Seal the session
    seal_record = conv.seal_session(session_id)

CLI
---
    python 09_workflow/MRL_memory_integration.py new --system "You are MRL_AGI"
    python 09_workflow/MRL_memory_integration.py trace --session-id <id>
    python 09_workflow/MRL_memory_integration.py seal --session-id <id>
    python 09_workflow/MRL_memory_integration.py replay --session-id <id>
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── Ensure module paths ───────────────────────────────────────────────────────

def _ensure_paths() -> None:
    for sub in [
        _REPO_ROOT / "09_workflow",
        _REPO_ROOT / "03_memory" / "merkle",
        _REPO_ROOT / "03_memory" / "vector",
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


# ─── MemoryIntegratedConversation ─────────────────────────────────────────────

class MemoryIntegratedConversation:
    """
    Conversation manager with integrated memory tracing.

    Every message event is automatically:
      1. Written to conversation store (conversation_manager.py)
      2. Traced to merkle chain (memory_chain.py)
      3. Optionally vectorized for RAG (vector_store.py)

    Session lifecycle:
      new_session → add_message* → seal_session
    """

    def __init__(self) -> None:
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        MerkleChain = _try_import("memory_chain", "MerkleChain")
        VectorStore = _try_import("vector_store", "VectorStore")

        self._conv_mgr = ConvMgr() if ConvMgr else None
        self._chain: Any = None
        self._vector: Any = None

        # Initialize merkle chain
        if MerkleChain:
            try:
                data_dir = _REPO_ROOT / "03_memory" / "_data" / "memory_chain"
                self._chain = MerkleChain(data_dir)
            except Exception:  # noqa: BLE001
                pass

        # Initialize vector store
        if VectorStore:
            try:
                self._vector = VectorStore()
            except Exception:  # noqa: BLE001
                pass

        # Session trace metadata
        self._session_traces: Dict[str, List[str]] = {}  # session_id → [entry_id, ...]
        self._session_seals: Dict[str, Dict[str, Any]] = {}  # session_id → seal_record

    # ── Session lifecycle ─────────────────────────────────────────────────────

    def new_session(
        self,
        system_prompt: str = "",
        label: str = "",
    ) -> str:
        """
        Create a new conversation session.

        Returns
        -------
        session_id : UUID string
        """
        if not self._conv_mgr:
            raise RuntimeError("ConversationManager unavailable")

        session_id = self._conv_mgr.new_session(
            system_prompt=system_prompt,
            label=label,
        )

        # Initialize trace list
        self._session_traces[session_id] = []

        # Trace session creation
        if self._chain:
            try:
                entry = self._chain.append(
                    payload={
                        "event": "session_created",
                        "session_id": session_id,
                        "label": label,
                        "system_prompt": system_prompt[:200],  # Truncate for trace
                        "created_at_ms": int(time.time() * 1000),
                    },
                    tags=["conversation", "session_created"],
                    layer="L7_LOOP",
                    meta={"session_id": session_id},
                )
                self._session_traces[session_id].append(entry["entry_id"])
            except Exception:  # noqa: BLE001
                pass  # Continue even if trace fails

        return session_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        name: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a message to a session and trace it to memory.

        Parameters
        ----------
        session_id : Session UUID
        role       : "user" | "assistant" | "tool" | "system"
        content    : Message content
        name       : Optional sender name
        tool_call_id : Optional tool call identifier
        meta       : Additional metadata

        Returns
        -------
        Message record with msg_id
        """
        if not self._conv_mgr:
            raise RuntimeError("ConversationManager unavailable")

        # Add to conversation store
        msg = self._conv_mgr.add_message(
            session_id=session_id,
            role=role,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
            meta=meta,
        )

        # Trace to merkle chain
        if self._chain:
            try:
                entry = self._chain.append(
                    payload={
                        "event": "message_added",
                        "session_id": session_id,
                        "msg_id": msg["msg_id"],
                        "role": role,
                        "content": content[:500],  # Truncate for trace
                        "ts_ms": msg["ts_ms"],
                    },
                    tags=["conversation", f"role_{role}"],
                    layer="L7_LOOP",
                    meta={"session_id": session_id, "msg_id": msg["msg_id"]},
                )
                if session_id in self._session_traces:
                    self._session_traces[session_id].append(entry["entry_id"])
            except Exception:  # noqa: BLE001
                pass

        return msg

    def get_history(
        self,
        session_id: str,
        roles: Optional[List[str]] = None,
        last_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        if not self._conv_mgr:
            raise RuntimeError("ConversationManager unavailable")
        return self._conv_mgr.get_history(session_id, roles=roles, last_n=last_n)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all conversation sessions."""
        if not self._conv_mgr:
            raise RuntimeError("ConversationManager unavailable")
        return self._conv_mgr.list_sessions()

    # ── Memory trace query ────────────────────────────────────────────────────

    def get_session_trace(self, session_id: str) -> Dict[str, Any]:
        """
        Get the full memory trace for a session.

        Returns
        -------
        Trace record with:
          - session_id
          - merkle_entries: list of entry IDs
          - total_entries: count
          - seal_record: if sealed
        """
        return {
            "session_id": session_id,
            "merkle_entries": self._session_traces.get(session_id, []),
            "total_entries": len(self._session_traces.get(session_id, [])),
            "seal_record": self._session_seals.get(session_id),
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def replay_session(self, session_id: str) -> Dict[str, Any]:
        """
        Replay a session from memory records.

        Returns
        -------
        Replay record with:
          - session_id
          - messages: reconstructed from trace
          - replay_source: "memory_chain"
        """
        if not self._chain:
            return {"error": "MerkleChain unavailable"}

        entry_ids = self._session_traces.get(session_id, [])
        if not entry_ids:
            return {"error": "No trace entries for session"}

        # Reconstruct messages from merkle entries
        messages = []
        for entry_id in entry_ids:
            try:
                entries = self._chain.list(limit=1000)  # Get all entries
                entry = next((e for e in entries if e["entry_id"] == entry_id), None)
                if entry and entry["payload"].get("event") == "message_added":
                    messages.append({
                        "role": entry["payload"]["role"],
                        "content": entry["payload"]["content"],
                        "msg_id": entry["payload"]["msg_id"],
                        "ts_ms": entry["payload"]["ts_ms"],
                    })
            except Exception:  # noqa: BLE001
                continue

        return {
            "session_id": session_id,
            "messages": messages,
            "replay_source": "memory_chain",
            "total_entries": len(entry_ids),
            "origin_signature": ORIGIN_SIGNATURE,
        }

    # ── Session sealing ───────────────────────────────────────────────────────

    def seal_session(self, session_id: str) -> Dict[str, Any]:
        """
        Seal a conversation session to the merkle chain.

        Creates a final seal entry with:
          - Session summary
          - Message count
          - Merkle checksum
          - Origin signature

        Returns
        -------
        Seal record
        """
        if not self._chain:
            return {"error": "MerkleChain unavailable"}

        if not self._conv_mgr:
            return {"error": "ConversationManager unavailable"}

        # Get session info
        try:
            history = self._conv_mgr.get_history(session_id)
        except KeyError:
            return {"error": f"Session not found: {session_id}"}

        # Create seal payload
        payload = {
            "event": "session_sealed",
            "session_id": session_id,
            "message_count": len(history),
            "turn_count": len([m for m in history if m["role"] != "system"]),
            "merkle_entries": self._session_traces.get(session_id, []),
            "sealed_at_ms": int(time.time() * 1000),
        }

        try:
            entry = self._chain.append(
                payload=payload,
                tags=["conversation", "session_sealed"],
                layer="L7_LOOP",
                meta={"session_id": session_id},
            )

            seal_record = {
                "session_id": session_id,
                "seal_entry_id": entry["entry_id"],
                "merkle_hash": entry["merkle"],
                "sealed_at_ms": entry["timestamp_ms"],
                "message_count": len(history),
                "origin_signature": ORIGIN_SIGNATURE,
            }

            self._session_seals[session_id] = seal_record

            return seal_record

        except Exception as exc:  # noqa: BLE001
            return {"error": f"Seal failed: {exc}"}


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_new(args: argparse.Namespace) -> None:
    conv = MemoryIntegratedConversation()
    session_id = conv.new_session(
        system_prompt=args.system or "",
        label=args.label or "",
    )
    print(f"Session created: {session_id}")


def _cmd_trace(args: argparse.Namespace) -> None:
    conv = MemoryIntegratedConversation()
    trace = conv.get_session_trace(args.session_id)
    print(json.dumps(trace, ensure_ascii=False, indent=2))


def _cmd_seal(args: argparse.Namespace) -> None:
    conv = MemoryIntegratedConversation()
    seal = conv.seal_session(args.session_id)
    print(json.dumps(seal, ensure_ascii=False, indent=2))


def _cmd_replay(args: argparse.Namespace) -> None:
    conv = MemoryIntegratedConversation()
    replay = conv.replay_session(args.session_id)
    print(json.dumps(replay, ensure_ascii=False, indent=2))


def _cmd_list(_args: argparse.Namespace) -> None:
    conv = MemoryIntegratedConversation()
    sessions = conv.list_sessions()
    print(f"Total sessions: {len(sessions)}")
    for sess in sessions:
        print(f"  {sess['session_id'][:8]}…  turns={sess['turn_count']}  {sess['label']}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MRL_memory_integration — Memory-integrated conversations"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # new
    n = sub.add_parser("new", help="Create new session")
    n.add_argument("--system", help="System prompt")
    n.add_argument("--label", help="Session label")

    # trace
    t = sub.add_parser("trace", help="Get session trace")
    t.add_argument("--session-id", required=True)

    # seal
    s = sub.add_parser("seal", help="Seal session")
    s.add_argument("--session-id", required=True)

    # replay
    r = sub.add_parser("replay", help="Replay session from memory")
    r.add_argument("--session-id", required=True)

    # list
    sub.add_parser("list", help="List sessions")

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "new": _cmd_new,
        "trace": _cmd_trace,
        "seal": _cmd_seal,
        "replay": _cmd_replay,
        "list": _cmd_list,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()