# HCRA Context Manager

The HCRA Context Manager provides a lightweight way to store short context snippets and retrieve them using similarity search. It is designed for applications that need to track conversation or document fragments without relying on a heavyweight vector database.

## Key Concepts

- **Contexts**: Each entry stores the original text and optional metadata.
- **Tokenization**: Tokenizes text using `tiktoken` when available, with a regex fallback.
- **Similarity**: Uses cosine similarity over normalized term frequencies to rank results.

## Typical Workflow

1. **Add context** with an ID, text, and metadata.
2. **Search** with a query string to retrieve the most similar snippets.
3. **Remove** contexts that are no longer needed.

## Example

```python
from hcra import HCRAManager

manager = HCRAManager()
manager.add_context("intro", "Hello world", {"source": "notes"})
manager.add_context("mission", "Launch checklist and status")

results = manager.search("hello")
for result in results:
    print(result["context_id"], result["score"])
```

## Design Notes

- Uses a normalized term-frequency representation for speed and simplicity.
- Supports metadata alongside each stored context.
- Designed for in-memory usage in lightweight services or scripts.
