# AI Computer Runtime (v0.1)

This runtime provides a local HTTP API + CLI for safe file operations within the vault root.

## Layout

- Runtime: `tools/ai-computer/ai_computer.py`
- Workspace (writable): `work/`
- Index output: `artifacts/index/manifest.json`
- Trace output: `artifacts/trace/trace.jsonl`

## Quickstart

```bash
python tools/ai-computer/ai_computer.py serve --host 127.0.0.1 --port 8765
```

### Health

```bash
curl http://127.0.0.1:8765/health
```

### File operations

```bash
python tools/ai-computer/ai_computer.py list .
python tools/ai-computer/ai_computer.py read README.md
echo "hello" | python tools/ai-computer/ai_computer.py write work/hello.txt
python tools/ai-computer/ai_computer.py mkdir work/demo
python tools/ai-computer/ai_computer.py info work/hello.txt
```

### Index

```bash
python tools/ai-computer/ai_computer.py index
cat artifacts/index/manifest.json
```

## HTTP API

- `GET /health`
- `GET /list?path=.`
- `GET /read?path=README.md`
- `GET /info?path=work/hello.txt`
- `POST /write` JSON: `{ "path": "work/hello.txt", "content": "hello" }`
- `POST /mkdir` JSON: `{ "path": "work/demo" }`
- `POST /index`

All operations are traced to `artifacts/trace/trace.jsonl` with `tick` and `merkle_root` to support replay.
