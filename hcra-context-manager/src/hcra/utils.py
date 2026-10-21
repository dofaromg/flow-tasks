"""Utility helpers for tokenization and similarity."""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

import numpy as np

try:
    import tiktoken
except ImportError:  # pragma: no cover - optional dependency
    tiktoken = None


_WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)


def tokenize(text: str, encoder_name: str = "cl100k_base") -> list[str]:
    """Tokenize text using tiktoken when available, otherwise fallback to words."""
    if not text:
        return []
    if tiktoken is None:
        return [match.group(0).lower() for match in _WORD_RE.finditer(text)]

    encoder = tiktoken.get_encoding(encoder_name)
    token_ids = encoder.encode(text)
    return [str(token_id) for token_id in token_ids]


def term_frequencies(tokens: Iterable[str]) -> dict[str, float]:
    """Convert tokens into normalized term frequencies."""
    counts = Counter(tokens)
    total = sum(counts.values())
    if total == 0:
        return {}
    return {token: count / total for token, count in counts.items()}


def cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse frequency maps."""
    if not a or not b:
        return 0.0
    shared = set(a) & set(b)
    dot = sum(a[token] * b[token] for token in shared)
    norm_a = np.sqrt(sum(value * value for value in a.values()))
    norm_b = np.sqrt(sum(value * value for value in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))
