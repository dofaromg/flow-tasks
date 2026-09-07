"""
module-a core — MRL particle compute (pure, zero-dependency).
origin_signature: MrLiouWord

Business logic lives here with no Flask/Mongo import so it is unit-testable with
the standard library alone. app.py is a thin Flask transport over these
functions. Replaces the previous health-only shell with real deterministic work.
"""

import hashlib
import math
import re

_TOKEN_RE = re.compile(r"[A-Za-z0-9一-鿿]+")


def tokenize(text: str) -> list:
    """Lowercase word/CJK tokenization."""
    return _TOKEN_RE.findall(text.lower())


def _hash64(token: str) -> int:
    return int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:8], "big")


def simhash64(tokens: list) -> int:
    """Real 64-bit SimHash content fingerprint (near-duplicate detection)."""
    if not tokens:
        return 0
    bits = [0] * 64
    for t in tokens:
        h = _hash64(t)
        for i in range(64):
            bits[i] += 1 if (h >> i) & 1 else -1
    out = 0
    for i in range(64):
        if bits[i] > 0:
            out |= 1 << i
    return out


def particle_score(tokens: list) -> float:
    """Deterministic score: lexical-diversity * log-length."""
    if not tokens:
        return 0.0
    return round(len(set(tokens)) / len(tokens) * math.log2(len(tokens) + 1), 6)


def compute_particle(text) -> dict:
    """Full particle analysis of a text payload."""
    if not isinstance(text, str):
        raise ValueError("text_must_be_string")
    tokens = tokenize(text)
    return {
        "char_count": len(text),
        "token_count": len(tokens),
        "unique_tokens": len(set(tokens)),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "simhash64": format(simhash64(tokens), "016x"),
        "particle_score": particle_score(tokens),
        "origin_signature": "MrLiouWord",
    }


def capabilities() -> dict:
    return {
        "service": "module-a",
        "version": "2.0.0",
        "capabilities": ["compute_particle", "tokenize", "simhash64", "particle_score"],
        "origin_signature": "MrLiouWord",
    }
