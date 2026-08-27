#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conversation_manager.py — Multi-Turn Conversation Session Manager
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

Industry capability: persistent multi-turn conversation sessions with full
                     message history (ChatGPT / Claude / Gemini style chat).
MRL extension: every message and session event is stamped with
               origin_signature and can be sealed into the MerkleChain.

Key concepts
------------
Message     — a single turn (role: system | user | assistant | tool).
Session     — an ordered list of messages sharing a session_id.
ConversationManager — manages multiple sessions, persists to JSON.

Usage (library)
---------------
    from conversation_manager import ConversationManager

    mgr = ConversationManager()

    sid = mgr.new_session(system_prompt="You are a helpful MRL assistant.")
    mgr.add_message(sid, "user", "Hello!")
    mgr.add_message(sid, "assistant", "Hi! How can I help?")

    history = mgr.get_history(sid)
    print(history[-1]["content"])

CLI
---
    python 09_workflow/conversation_manager.py new   --system "You are MRL."
    python 09_workflow/conversation_manager.py add   --sid <id> --role user --content "Hello"
    python 09_workflow/conversation_manager.py show  --sid <id>
    python 09_workflow/conversation_manager.py list
    python 09_workflow/conversation_manager.py delete --sid <id>
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import time
import uuid
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"
VALID_ROLES = {"system", "user", "assistant", "tool"}

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DEFAULT_STORE = _REPO_ROOT / "data" / "conversations.json"


# ─── Message ─────────────────────────────────────────────────────────────────

def _make_message(
    role: str,
    content: str,
    *,
    name: Optional[str] = None,
    tool_call_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role}'. Must be one of {VALID_ROLES}.")
    msg: Dict[str, Any] = {
        "role": role,
        "content": content,
        "ts_ms": int(time.time() * 1000),
        "msg_id": str(uuid.uuid4()),
        "origin_signature": ORIGIN_SIGNATURE,
    }
    if name:
        msg["name"] = name
    if tool_call_id:
        msg["tool_call_id"] = tool_call_id
    if meta:
        msg["meta"] = meta
    return msg


# ─── Session ─────────────────────────────────────────────────────────────────

class ConversationSession:
    """
    A single conversation session: ordered list of messages + metadata.
    """

    def __init__(
        self,
        session_id: str,
        system_prompt: str = "",
        label: str = "",
        created_at_ms: Optional[int] = None,
    ) -> None:
        self.session_id = session_id
        self.label = label
        self.created_at_ms: int = created_at_ms or int(time.time() * 1000)
        self.updated_at_ms: int = self.created_at_ms
        self.messages: List[Dict[str, Any]] = []

        if system_prompt:
            self.messages.append(
                _make_message("system", system_prompt, meta={"is_system_prompt": True})
            )

    # ── Message management ────────────────────────────────────────────────────

    def add(
        self,
        role: str,
        content: str,
        *,
        name: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append a message and return it."""
        msg = _make_message(role, content, name=name, tool_call_id=tool_call_id, meta=meta)
        self.messages.append(msg)
        self.updated_at_ms = msg["ts_ms"]
        return msg

    def history(
        self,
        *,
        roles: Optional[List[str]] = None,
        last_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return message history, optionally filtered by role and/or limited to
        the last *last_n* messages.
        """
        msgs = self.messages
        if roles:
            msgs = [m for m in msgs if m["role"] in roles]
        if last_n is not None:
            msgs = msgs[-last_n:]
        return list(msgs)

    def clear(self, keep_system: bool = True) -> None:
        """Clear history, optionally preserving the system prompt."""
        if keep_system:
            self.messages = [m for m in self.messages if m.get("meta", {}).get("is_system_prompt")]
        else:
            self.messages = []
        self.updated_at_ms = int(time.time() * 1000)

    @property
    def turn_count(self) -> int:
        """Number of non-system turns."""
        return sum(1 for m in self.messages if m["role"] != "system")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "label": self.label,
            "created_at_ms": self.created_at_ms,
            "updated_at_ms": self.updated_at_ms,
            "turn_count": self.turn_count,
            "messages": self.messages,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ConversationSession":
        sess = cls(
            session_id=d["session_id"],
            label=d.get("label", ""),
            created_at_ms=d.get("created_at_ms"),
        )
        sess.messages = d.get("messages", [])
        sess.updated_at_ms = d.get("updated_at_ms", sess.created_at_ms)
        return sess


# ─── ConversationManager ─────────────────────────────────────────────────────

class ConversationManager:
    """
    Manages multiple named conversation sessions with JSON persistence.

    Parameters
    ----------
    store_path : pathlib.Path
        Path to the JSON file used for persistence.
    """

    def __init__(self, store_path: pathlib.Path = _DEFAULT_STORE) -> None:
        self._path = pathlib.Path(store_path)
        self._sessions: Dict[str, ConversationSession] = {}
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                for d in data.get("sessions", []):
                    sess = ConversationSession.from_dict(d)
                    self._sessions[sess.session_id] = sess
            except (json.JSONDecodeError, KeyError):
                pass  # corrupt store — start fresh

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "origin_signature": ORIGIN_SIGNATURE,
            "total_sessions": len(self._sessions),
            "saved_at_ms": int(time.time() * 1000),
            "sessions": [s.to_dict() for s in self._sessions.values()],
        }
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        # Restrict file to owner-only read/write (session data is private)
        try:
            os.chmod(self._path, 0o600)
        except OSError:
            pass

    # ── Session lifecycle ─────────────────────────────────────────────────────

    def new_session(
        self,
        *,
        system_prompt: str = "",
        label: str = "",
        session_id: Optional[str] = None,
    ) -> str:
        """Create a new session. Returns the session_id."""
        sid = session_id or str(uuid.uuid4())
        sess = ConversationSession(sid, system_prompt=system_prompt, label=label)
        self._sessions[sid] = sess
        self._save()
        return sid

    def delete_session(self, session_id: str) -> bool:
        """Remove a session. Returns True if it existed."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save()
            return True
        return False

    def rename_session(self, session_id: str, label: str) -> bool:
        """Rename a session label. Returns True if the session existed."""
        sess = self._sessions.get(session_id)
        if sess is None:
            return False
        sess.label = label
        self._save()
        return True

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Return lightweight session summaries (no message bodies)."""
        return [
            {
                "session_id": s.session_id,
                "label": s.label,
                "turn_count": s.turn_count,
                "created_at_ms": s.created_at_ms,
                "updated_at_ms": s.updated_at_ms,
            }
            for s in sorted(self._sessions.values(), key=lambda s: s.updated_at_ms, reverse=True)
        ]

    # ── Messaging ─────────────────────────────────────────────────────────────

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
        Add a message to a session.

        Raises
        ------
        KeyError  if session_id does not exist.
        ValueError if role is invalid.
        """
        sess = self._sessions.get(session_id)
        if sess is None:
            raise KeyError(f"session not found: '{session_id}'")
        msg = sess.add(role, content, name=name, tool_call_id=tool_call_id, meta=meta)
        self._save()
        return msg

    def get_history(
        self,
        session_id: str,
        *,
        roles: Optional[List[str]] = None,
        last_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return the message history for a session."""
        sess = self._sessions.get(session_id)
        if sess is None:
            raise KeyError(f"session not found: '{session_id}'")
        return sess.history(roles=roles, last_n=last_n)

    def clear_session(self, session_id: str, keep_system: bool = True) -> None:
        """Clear message history for a session."""
        sess = self._sessions.get(session_id)
        if sess is None:
            raise KeyError(f"session not found: '{session_id}'")
        sess.clear(keep_system=keep_system)
        self._save()

    def export_markdown(self, session_id: str) -> str:
        """
        Export a session as a Markdown-formatted string.

        Each message is rendered as a level-3 heading with the speaker role,
        followed by the message body.  Returns an empty string when the
        session does not exist.

        Parameters
        ----------
        session_id : ID of the session to export.
        """
        sess = self.get_session(session_id)
        if sess is None:
            return ""
        title = sess.label or sess.session_id
        lines: List[str] = [
            f"# Conversation: {title}",
            "",
            f"- **Session ID**: `{sess.session_id}`",
            f"- **Turns**: {sess.turn_count}",
            f"- **Origin**: {ORIGIN_SIGNATURE}",
            "",
        ]
        for msg in sess.history():
            role = msg["role"].capitalize()
            content = msg["content"]
            ts = msg.get("ts_ms", "")
            lines.append(f"### {role}")
            if ts:
                lines.append(f"*{ts}*")
            lines.append("")
            lines.append(content)
            lines.append("")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._sessions)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_new(args: argparse.Namespace) -> None:
    mgr = ConversationManager()
    sid = mgr.new_session(system_prompt=args.system or "", label=args.label or "")
    print(f"✅ New session created: {sid}")


def _cmd_add(args: argparse.Namespace) -> None:
    mgr = ConversationManager()
    msg = mgr.add_message(args.sid, args.role, args.content)
    print(f"✅ Message added  role={msg['role']}  msg_id={msg['msg_id']}")


def _cmd_show(args: argparse.Namespace) -> None:
    mgr = ConversationManager()
    history = mgr.get_history(args.sid)
    for m in history:
        print(f"[{m['role']}]  {m['content'][:120]}")


def _cmd_list(_args: argparse.Namespace) -> None:
    mgr = ConversationManager()
    sessions = mgr.list_sessions()
    print(f"{len(sessions)} session(s):")
    for s in sessions:
        print(f"  {s['session_id'][:8]}…  turns={s['turn_count']}  label={s['label']}")


def _cmd_delete(args: argparse.Namespace) -> None:
    mgr = ConversationManager()
    ok = mgr.delete_session(args.sid)
    print(f"{'✅ Deleted' if ok else '❌ Not found'}: {args.sid}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ConversationManager — multi-turn session manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="Create a new conversation session")
    n.add_argument("--system", default="", help="System prompt")
    n.add_argument("--label", default="", help="Human-readable session label")

    a = sub.add_parser("add", help="Add a message to a session")
    a.add_argument("--sid", required=True, help="Session ID")
    a.add_argument("--role", required=True, choices=list(VALID_ROLES))
    a.add_argument("--content", required=True)

    s = sub.add_parser("show", help="Print the message history of a session")
    s.add_argument("--sid", required=True)

    sub.add_parser("list", help="List all sessions")

    d = sub.add_parser("delete", help="Delete a session")
    d.add_argument("--sid", required=True)

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "new":    _cmd_new,
        "add":    _cmd_add,
        "show":   _cmd_show,
        "list":   _cmd_list,
        "delete": _cmd_delete,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
