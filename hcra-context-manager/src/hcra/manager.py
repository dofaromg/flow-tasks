"""Core HCRA manager implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .utils import cosine_similarity, term_frequencies, tokenize


@dataclass
class ContextEntry:
    """Stored context entry for similarity search."""

    context_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    vector: dict[str, float] = field(default_factory=dict)


class HCRAManager:
    """Manage and retrieve context snippets with similarity search."""

    def __init__(self, encoder_name: str = "cl100k_base") -> None:
        self._encoder_name = encoder_name
        self._entries: dict[str, ContextEntry] = {}

    def add_context(
        self, context_id: str, text: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add or update a context entry."""
        tokens = tokenize(text, self._encoder_name)
        vector = term_frequencies(tokens)
        self._entries[context_id] = ContextEntry(
            context_id=context_id,
            text=text,
            metadata=metadata or {},
            vector=vector,
        )

    def remove_context(self, context_id: str) -> None:
        """Remove a context entry by id."""
        self._entries.pop(context_id, None)

    def get_context(self, context_id: str) -> ContextEntry | None:
        """Retrieve a context entry by id."""
        return self._entries.get(context_id)

    def list_contexts(self) -> list[str]:
        """Return a list of all context IDs."""
        return sorted(self._entries.keys())

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search contexts by similarity to the query."""
        query_tokens = tokenize(query, self._encoder_name)
        query_vector = term_frequencies(query_tokens)
        scored = []
        for entry in self._entries.values():
            score = cosine_similarity(query_vector, entry.vector)
            scored.append((score, entry))
        scored.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, entry in scored[:top_k]:
            results.append(
                {
                    "context_id": entry.context_id,
                    "score": score,
                    "text": entry.text,
                    "metadata": entry.metadata,
                }
            )
        return results

    def bulk_add(self, entries: Iterable[tuple[str, str, dict[str, Any] | None]]) -> None:
        """Add multiple context entries."""
        for context_id, text, metadata in entries:
            self.add_context(context_id, text, metadata)
