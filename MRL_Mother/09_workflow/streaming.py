#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
streaming.py — Streaming Output Support
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 MrLiouAIRuntime

Industry capability: real-time token-by-token streaming output — the same
                     pattern used by ChatGPT, Claude, and Gemini to deliver
                     progressive responses.
MRL extension: each chunk is stamped with origin_signature and stream_id;
               the completed stream is a trace-compatible record that can be
               sealed into the MerkleChain.

Key classes
-----------
  StreamChunk   — a single streaming delta (token or partial text)
  StreamBuffer  — accumulates chunks; yields the final assembled text
  StreamSession — wraps a generator and emits chunks with MRL metadata
  StreamReplay  — replays a saved stream from a list of chunks (testing)

Usage (library)
---------------
    from streaming import StreamSession

    def my_source():
        for word in ["Hello", " ", "world", "!"]:
            yield word

    sess = StreamSession(my_source(), model="mock", session_id="demo")
    for chunk in sess:
        print(chunk.delta, end="", flush=True)
    print()
    print(sess.result())   # full assembled text + trace record

CLI
---
    python 09_workflow/streaming.py demo
    python 09_workflow/streaming.py replay --chunks '["Hello"," ","world"]'
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, Iterable, Iterator, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"


# ─── StreamChunk ─────────────────────────────────────────────────────────────

@dataclass
class StreamChunk:
    """
    A single delta emitted from a streaming response.

    Fields
    ------
    delta       : incremental text fragment
    index       : 0-based chunk sequence number
    stream_id   : identifier shared by all chunks in the same stream
    finish      : True if this is the final chunk
    ts_ms       : timestamp of this chunk
    model       : model that generated this chunk
    """

    delta: str
    index: int
    stream_id: str
    finish: bool = False
    ts_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    model: str = ""
    meta: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delta": self.delta,
            "index": self.index,
            "stream_id": self.stream_id,
            "finish": self.finish,
            "ts_ms": self.ts_ms,
            "model": self.model,
            "meta": self.meta,
            "origin_signature": ORIGIN_SIGNATURE,
        }


# ─── StreamBuffer ────────────────────────────────────────────────────────────

class StreamBuffer:
    """
    Accumulates StreamChunks and provides the assembled full text.
    """

    def __init__(self) -> None:
        self._chunks: List[StreamChunk] = []
        self._text = ""

    def push(self, chunk: StreamChunk) -> None:
        self._chunks.append(chunk)
        self._text += chunk.delta

    @property
    def text(self) -> str:
        return self._text

    @property
    def chunks(self) -> List[StreamChunk]:
        return list(self._chunks)

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)


# ─── StreamSession ───────────────────────────────────────────────────────────

class StreamSession:
    """
    Wraps a text-delta generator into a trace-compatible streaming session.

    Iterating over a StreamSession yields StreamChunks.
    After the stream completes, call ``result()`` for the assembled record.

    Parameters
    ----------
    source  : Iterable[str]
        Any iterable (generator, list, …) that yields text delta strings.
    model   : str
        Model identifier (for metadata).
    session_id : str
        Links to a ConversationSession if relevant.
    stream_id  : str
        Auto-generated if not provided.
    """

    def __init__(
        self,
        source: Iterable[str],
        *,
        model: str = "",
        session_id: str = "",
        stream_id: Optional[str] = None,
    ) -> None:
        self._source = iter(source)
        self.stream_id = stream_id or str(uuid.uuid4())
        self.model = model
        self.session_id = session_id
        self._buffer = StreamBuffer()
        self._started_at_ms: int = int(time.time() * 1000)
        self._ended_at_ms: Optional[int] = None
        self._done = False

    # ── Iterator ─────────────────────────────────────────────────────────────

    def __iter__(self) -> Iterator[StreamChunk]:
        return self._stream()

    def _stream(self) -> Generator[StreamChunk, None, None]:
        index = 0
        try:
            for delta in self._source:
                chunk = StreamChunk(
                    delta=str(delta),
                    index=index,
                    stream_id=self.stream_id,
                    finish=False,
                    model=self.model,
                )
                self._buffer.push(chunk)
                yield chunk
                index += 1
        finally:
            # Emit a final finish chunk (empty delta, finish=True)
            finish_chunk = StreamChunk(
                delta="",
                index=index,
                stream_id=self.stream_id,
                finish=True,
                model=self.model,
            )
            self._buffer.push(finish_chunk)
            yield finish_chunk
            self._ended_at_ms = int(time.time() * 1000)
            self._done = True

    # ── Result ────────────────────────────────────────────────────────────────

    def result(self) -> Dict[str, Any]:
        """
        Return the assembled trace-compatible result record.
        Only meaningful after the stream has been fully consumed.
        """
        return {
            "stream_id": self.stream_id,
            "model": self.model,
            "session_id": self.session_id,
            "text": self._buffer.text,
            "chunk_count": self._buffer.chunk_count,
            "started_at_ms": self._started_at_ms,
            "ended_at_ms": self._ended_at_ms or int(time.time() * 1000),
            "done": self._done,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    @property
    def text(self) -> str:
        return self._buffer.text

    @property
    def buffer(self) -> StreamBuffer:
        return self._buffer


# ─── StreamReplay ────────────────────────────────────────────────────────────

class StreamReplay:
    """
    Replays a saved list of text deltas as a StreamSession.

    Useful for testing and demo purposes without a live LLM.
    """

    def __init__(self, chunks: List[str], *, model: str = "replay", delay_ms: int = 0) -> None:
        self._chunks = chunks
        self._model = model
        self._delay_ms = delay_ms

    def session(self, *, session_id: str = "") -> StreamSession:
        def _gen() -> Generator[str, None, None]:
            for c in self._chunks:
                if self._delay_ms:
                    time.sleep(self._delay_ms / 1000)
                yield c

        return StreamSession(_gen(), model=self._model, session_id=session_id)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_demo(_args: argparse.Namespace) -> None:
    """Stream a demo sentence word by word."""
    words = ["The", " ", "MRL", " ", "AI", " ", "System", " ", "streams", " ", "in", " ", "real-time", "!"]
    replay = StreamReplay(words, model="mock-demo")
    sess = replay.session(session_id="demo")
    print("Streaming: ", end="", flush=True)
    for chunk in sess:
        if not chunk.finish:
            print(chunk.delta, end="", flush=True)
    print()
    print(json.dumps(sess.result(), ensure_ascii=False, indent=2))


def _cmd_replay(args: argparse.Namespace) -> None:
    chunks: List[str] = json.loads(args.chunks)
    replay = StreamReplay(chunks, model="replay")
    sess = replay.session()
    for chunk in sess:
        if not chunk.finish:
            print(chunk.delta, end="", flush=True)
    print()
    print(json.dumps(sess.result(), ensure_ascii=False, indent=2))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="streaming — streaming output support")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="Run a streaming demo")
    r = sub.add_parser("replay", help="Replay a list of text chunks")
    r.add_argument("--chunks", required=True, help='JSON array of strings e.g. ["Hello"," ","world"]')
    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {"demo": _cmd_demo, "replay": _cmd_replay}
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
