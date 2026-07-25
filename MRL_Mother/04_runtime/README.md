# 04_runtime

MrLiouAI execution kernel (L7 LOOP layer).

## Files

| File | Purpose |
|------|---------|
| `flowcore_loop.py` | Main kernel loop — heartbeat, trace writing, Merkle chain commits |
| `runtime_manifest.yaml` | Canonical install / recovery spec: TotalCore · Runtime · Container · CLI |

## Runtime data

Operational data written to gitignored paths:
- `06_trace/traces/_data/runtime_trace.jsonl` — JSONL operational trace
- `03_memory/_data/memory_chain/` — Merkle chain entries + head pointer

## Loop cycle

`Observe → Resolve → Mirror → Project → Verify → Iterate`

## Execution tiers

| Tier | Description | Start command |
|------|-------------|---------------|
| **TotalCore** | All six core groups loaded and cross-linked | see `runtime_manifest.yaml` |
| **Runtime** | Minimal kernel: loop + Merkle chain + trace | `python 04_runtime/flowcore_loop.py` |
| **Container** | FlowCoreLoop HTTP control plane + Vault | `python 09_workflow/MRL__Flowcore_Loop_2.py serve` |
| **CLI** | Day-to-day operator commands | `python 09_workflow/mrl_librarian.py …` etc. |

See `runtime_manifest.yaml` for the full install order and recovery protocol.

## Running (minimal)

```bash
python 04_runtime/flowcore_loop.py
```
