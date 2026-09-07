# 03_memory

Long-term memory layer for FlowAgent (L6 REFLECT / L7 LOOP).

## Sub-directories

| Directory | Purpose |
|-----------|---------|
| `merkle/` | Immutable append-only Merkle chain (canonical record store) |
| `vector/` | Vector store placeholder (semantic search / retrieval) |

## Merkle chain (`merkle/memory_chain.py`)

- SHA-256 linked chain: each entry hashes `(entry_id, timestamp_ms, payload, prev)`
- Supports `commit()`, `read_all()`, `verify()`, and `rollback(target_merkle)`
- Stored as JSONL + `head.txt` pointer in `_data/memory_chain/` (gitignored)

## Runtime data

Chain data written to `_data/memory_chain/` — excluded from git (see `.gitignore`).
