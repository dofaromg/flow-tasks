# HCRA Context Manager

A lightweight, in-memory context manager that supports similarity search over stored snippets. HCRA stands for *Hierarchical Context Retrieval Assistant* and focuses on fast retrieval for small to medium context sets.

## Features

- Add, list, and remove context entries.
- Search using cosine similarity over normalized term frequencies.
- Optional metadata per context entry.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from hcra import HCRAManager

manager = HCRAManager()
manager.add_context("intro", "Hello world", {"source": "notes"})
manager.add_context("mission", "Launch checklist and status")

results = manager.search("hello")
for result in results:
    print(result["context_id"], result["score"])
```

## Local Professional Script

For a fully local, observable, single-file implementation with REPL-style commands, run:

```bash
python hcra_local_v1_professional.py
```

This script includes layered context management (L0–L3), consent-gated anchors, origin protection with withdraw behavior, pointer/channel tracking, eviction logs, and snapshot export.

## Development

```bash
python -m pytest
```

## License

Apache-2.0
