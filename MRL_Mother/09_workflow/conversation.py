#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conversation.py — Multi-Turn Conversation & Session Manager
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

Goal: product-level local session management — no external dependencies,
      zero network calls, pure Python stdlib only.

Features
--------
- Named sessions with role-based message history (system / user / assistant)
- Context-window budgeting: auto-prunes oldest non-system messages when the
  estimated token count exceeds the configured limit
- Persistent sessions: each session is saved as a JSONL file under
  data/sessions/<session_id>.jsonl
- Summary memory: when pruning, a summary entry is injected to retain context
- Session registry: list, load, delete sessions by id
- Every message stamped with origin_signature + monotonic seq number
- Integration hooks for LLMGateway (optional, injected via set_gateway)

Token budget model
------------------
  Tokens are estimated as ceil(chars / 4).  This is a coarse heuristic that
  avoids any external tokeniser dependency while staying conservative.

Message envelope
----------------
    {
      "seq":              int,       # monotonic within session
      "role":             str,       # "system" | "user" | "assistant" | "summary"
      "content":          str,
      "ts_ms":            int,
      "session_id":       str,
      "origin_signature": "MrLiouWord",
    }

Usage (library)
---------------
    from conversation import ConversationManager

    mgr = ConversationManager()
    sid = mgr.new_session(system_prompt="You are a local assistant.")

    mgr.add_user(sid, "What is MRL?")

    # If LLMGateway is connected:
    reply = mgr.generate_reply(sid)   # calls gateway, appends assistant turn
    print(reply)

    # Or append a hand-crafted assistant reply:
    mgr.add_assistant(sid, "MRL is the Mother-Reversible-Loop system.")

    print(mgr.render(sid))   # full formatted history

CLI
---
    python 09_workflow/conversation.py new  --system "You are helpful."
    python 09_workflow/conversation.py list
    python 09_workflow/conversation.py show --id <sid>
    python 09_workflow/conversation.py chat --id <sid> --msg "Hello"
    python 09_workflow/conversation.py delete --id <sid>
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import time
import uuid
from typing import Any, Dict, Iterator, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"
SESSION_VERSION  = "1.0"

_REPO_ROOT    = pathlib.Path(__file__).resolve().parent.parent
_SESSION_DIR  = _REPO_ROOT / "data" / "sessions"

# Rough chars per token: 3 chars consumed per estimated token (conservative for CJK + English mix)
_CHARS_PER_TOKEN = 3


def _est_tokens(text: str) -> int:
    return math.ceil(len(text) / _CHARS_PER_TOKEN)


# ─── Message helpers ──────────────────────────────────────────────────────────

def _make_message(
    session_id: str,
    seq: int,
    role: str,
    content: str,
) -> Dict[str, Any]:
    return {
        "seq":              seq,
        "role":             role,
        "content":          content,
        "ts_ms":            int(time.time() * 1000),
        "session_id":       session_id,
        "origin_signature": ORIGIN_SIGNATURE,
    }


# ─── Session ──────────────────────────────────────────────────────────────────

class Session:
    """
    A single conversation session.

    Parameters
    ----------
    session_id : str
    system_prompt : str
        Initial system message (never pruned).
    max_tokens : int
        Context-window budget in (estimated) tokens.  Default = 4096.
    store_dir : pathlib.Path
        Directory where session JSONL files are persisted.
    """

    def __init__(
        self,
        session_id: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        store_dir: pathlib.Path = _SESSION_DIR,
    ) -> None:
        self.session_id = session_id
        self.max_tokens = max_tokens
        self._store_dir = store_dir
        self._messages: List[Dict[str, Any]] = []
        self._seq = 0
        self._created_at_ms = int(time.time() * 1000)

        if system_prompt:
            self._append("system", system_prompt, persist=False)

        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._store_dir / f"{session_id}.jsonl"
        self._persist_all()

    # ── Append ────────────────────────────────────────────────────────────────

    def _append(self, role: str, content: str, persist: bool = True) -> Dict[str, Any]:
        msg = _make_message(self.session_id, self._seq, role, content)
        self._seq += 1
        self._messages.append(msg)
        if persist:
            self._persist_one(msg)
        return msg

    def add_user(self, content: str) -> Dict[str, Any]:
        msg = self._append("user", content)
        self._maybe_prune()
        return msg

    def add_assistant(self, content: str) -> Dict[str, Any]:
        return self._append("assistant", content)

    def add_system(self, content: str) -> Dict[str, Any]:
        return self._append("system", content)

    # ── Context-window management ─────────────────────────────────────────────

    def _token_count(self) -> int:
        return sum(_est_tokens(m["content"]) for m in self._messages)

    def _maybe_prune(self) -> None:
        """
        When total tokens exceed budget, summarise and remove the oldest
        non-system messages until we are back under 80 % of max_tokens.
        """
        if self._token_count() < self.max_tokens:
            return

        target = int(self.max_tokens * 0.8)
        non_system = [m for m in self._messages if m["role"] != "system"]
        pruned: List[Dict[str, Any]] = []

        while self._token_count() > target and non_system:
            oldest = non_system.pop(0)
            self._messages.remove(oldest)
            pruned.append(oldest)

        if pruned:
            summary_lines = [f"[{m['role']}] {m['content'][:120]}" for m in pruned]
            summary_text = (
                f"[Context summary — {len(pruned)} earlier message(s) condensed]\n"
                + "\n".join(summary_lines)
            )
            # Insert summary right after the last system message
            insert_pos = max(
                (i for i, m in enumerate(self._messages) if m["role"] == "system"),
                default=-1,
            ) + 1
            summary_msg = _make_message(self.session_id, self._seq, "summary", summary_text)
            self._seq += 1
            self._messages.insert(insert_pos, summary_msg)
            self._persist_all()

    # ── Export for LLM ────────────────────────────────────────────────────────

    def remove_last_assistant_message(self) -> bool:
        """Remove the most recently appended assistant message (used by guardrail rollback)."""
        for i in range(len(self._messages) - 1, -1, -1):
            if self._messages[i].get("role") == "assistant":
                self._messages.pop(i)
                self._persist_all()
                return True
        return False

    def to_messages(self) -> List[Dict[str, str]]:
        """
        Return messages in LLM-compatible format (role + content only).
        Summary messages are mapped to "system" role for compatibility.
        """
        out = []
        for m in self._messages:
            role = "system" if m["role"] == "summary" else m["role"]
            out.append({"role": role, "content": m["content"]})
        return out

    def last_assistant(self) -> Optional[str]:
        for m in reversed(self._messages):
            if m["role"] == "assistant":
                return m["content"]
        return None

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(self, max_chars: int = 0) -> str:
        lines = []
        for m in self._messages:
            role = m["role"].upper()
            content = m["content"]
            if max_chars and len(content) > max_chars:
                content = content[:max_chars] + "…"
            lines.append(f"[{role}] {content}")
        return "\n".join(lines)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "session_id":       self.session_id,
            "message_count":    len(self._messages),
            "estimated_tokens": self._token_count(),
            "max_tokens":       self.max_tokens,
            "created_at_ms":    self._created_at_ms,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    # ── Persistence ───────────────────────────────────────────────────────────

    def _persist_one(self, msg: Dict[str, Any]) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    def _persist_all(self) -> None:
        tmp = self._path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            # Write a metadata header line so load() can restore session config
            meta = {
                "_meta":         True,
                "max_tokens":    self.max_tokens,
                "created_at_ms": self._created_at_ms,
            }
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")
            for msg in self._messages:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        tmp.replace(self._path)

    @classmethod
    def load(cls, session_id: str, store_dir: pathlib.Path = _SESSION_DIR) -> "Session":
        path = store_dir / f"{session_id}.jsonl"
        if not path.exists():
            raise FileNotFoundError(f"Session '{session_id}' not found")
        sess = cls.__new__(cls)
        sess.session_id     = session_id
        sess.max_tokens     = 4096
        sess._store_dir     = store_dir
        sess._messages      = []
        sess._seq           = 0
        sess._created_at_ms = int(time.time() * 1000)  # fallback; overwritten below if _meta line exists
        sess._path          = path
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                msg = json.loads(line)
                # A metadata line (written by _persist_all) carries session config
                if msg.get("_meta"):
                    sess.max_tokens     = int(msg.get("max_tokens", 4096))
                    sess._created_at_ms = int(msg.get("created_at_ms", sess._created_at_ms))
                    continue
                sess._messages.append(msg)
                sess._seq = max(sess._seq, msg.get("seq", 0) + 1)
        # Derive creation time from first message if no metadata line was present
        if sess._messages:
            first_ts = sess._messages[0].get("ts_ms")
            if first_ts and sess._created_at_ms > first_ts:
                sess._created_at_ms = first_ts
        return sess


# ─── ConversationManager ─────────────────────────────────────────────────────

class ConversationManager:
    """
    Registry and factory for Session objects.

    Parameters
    ----------
    store_dir : pathlib.Path
        Where session files are persisted.
    gateway : any
        Optional LLMGateway instance.  If set, generate_reply() works.
    max_tokens : int
        Default context-window budget for new sessions.
    """

    def __init__(
        self,
        store_dir: pathlib.Path = _SESSION_DIR,
        gateway: Any = None,
        max_tokens: int = 4096,
    ) -> None:
        self._store_dir  = pathlib.Path(store_dir)
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._gateway    = gateway
        self._max_tokens = max_tokens
        self._sessions: Dict[str, Session] = {}

    # ── Session lifecycle ─────────────────────────────────────────────────────

    def new_session(
        self,
        *,
        system_prompt: str = "",
        session_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        sid = session_id or uuid.uuid4().hex[:16]
        sess = Session(
            sid,
            system_prompt=system_prompt,
            max_tokens=max_tokens or self._max_tokens,
            store_dir=self._store_dir,
        )
        self._sessions[sid] = sess
        return sid

    def get(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session.load(session_id, self._store_dir)
        return self._sessions[session_id]

    def delete(self, session_id: str) -> bool:
        path = self._store_dir / f"{session_id}.jsonl"
        if path.exists():
            path.unlink()
        self._sessions.pop(session_id, None)
        return True

    def list_sessions(self) -> List[Dict[str, Any]]:
        result = []
        for p in sorted(self._store_dir.glob("*.jsonl")):
            sid = p.stem
            try:
                sess = self.get(sid)
                result.append(sess.snapshot())
            except Exception as exc:
                result.append({"session_id": sid, "error": str(exc)})
        return result

    # ── Convenience turn helpers ──────────────────────────────────────────────

    def add_user(self, session_id: str, content: str) -> Dict[str, Any]:
        return self.get(session_id).add_user(content)

    def add_assistant(self, session_id: str, content: str) -> Dict[str, Any]:
        return self.get(session_id).add_assistant(content)

    # ── LLM integration ───────────────────────────────────────────────────────

    def set_gateway(self, gateway: Any) -> None:
        self._gateway = gateway

    def generate_reply(
        self,
        session_id: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        """
        Call the attached LLMGateway with the session history and append the
        assistant reply to the session.  Returns the reply text.
        """
        if self._gateway is None:
            placeholder = "[LLMGateway not connected — set via set_gateway()]"
            self.get(session_id).add_assistant(placeholder)
            return placeholder

        sess = self.get(session_id)
        messages = sess.to_messages()
        resp = self._gateway.chat(messages, max_tokens=max_tokens, temperature=temperature)
        text = resp.get("text", "")
        sess.add_assistant(text)
        return text

    def stream_reply(
        self,
        session_id: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """
        Streaming version of generate_reply.  Yields text chunks; appends
        the complete reply to the session when the stream is exhausted.
        """
        if self._gateway is None:
            text = "[LLMGateway not connected]"
            self.get(session_id).add_assistant(text)
            yield text
            return

        sess = self.get(session_id)
        messages = sess.to_messages()
        chunks: List[str] = []
        for chunk in self._gateway.stream_chat(
            messages, max_tokens=max_tokens, temperature=temperature
        ):
            chunks.append(chunk)
            yield chunk
        sess.add_assistant("".join(chunks))

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(self, session_id: str, max_chars: int = 200) -> str:
        return self.get(session_id).render(max_chars=max_chars)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_new(args: argparse.Namespace) -> None:
    mgr = ConversationManager()
    sid = mgr.new_session(system_prompt=args.system or "")
    print(f"Created session: {sid}")
    print(json.dumps(mgr.get(sid).snapshot(), ensure_ascii=False, indent=2))


def _cmd_list(_args: argparse.Namespace) -> None:
    mgr = ConversationManager()
    sessions = mgr.list_sessions()
    if not sessions:
        print("No sessions found.")
        return
    for s in sessions:
        print(f"  {s['session_id']}  msgs={s.get('message_count','?')}  "
              f"tokens≈{s.get('estimated_tokens','?')}")


def _cmd_show(args: argparse.Namespace) -> None:
    mgr = ConversationManager()
    try:
        print(mgr.render(args.id, max_chars=0))
    except FileNotFoundError as exc:
        print(f"Error: {exc}")


def _cmd_chat(args: argparse.Namespace) -> None:
    mgr = ConversationManager()
    try:
        mgr.add_user(args.id, args.msg)
        reply = mgr.generate_reply(args.id)
        print(f"[ASSISTANT] {reply}")
    except FileNotFoundError as exc:
        print(f"Error: {exc}")


def _cmd_delete(args: argparse.Namespace) -> None:
    mgr = ConversationManager()
    mgr.delete(args.id)
    print(f"Deleted session: {args.id}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ConversationManager — multi-turn session manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new",    help="Create a new session")
    n.add_argument("--system", default="", help="System prompt text")

    sub.add_parser("list", help="List all sessions")

    sh = sub.add_parser("show", help="Print a session's history")
    sh.add_argument("--id", required=True, help="Session ID")

    ch = sub.add_parser("chat", help="Add a user message and generate a reply")
    ch.add_argument("--id",  required=True)
    ch.add_argument("--msg", required=True)

    dl = sub.add_parser("delete", help="Delete a session")
    dl.add_argument("--id", required=True)

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "new":    _cmd_new,
        "list":   _cmd_list,
        "show":   _cmd_show,
        "chat":   _cmd_chat,
        "delete": _cmd_delete,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
