# MRL_MotherModel_v0_1

**Bootstrap Date**: 2026-06-26  
**Origin Signature**: MrLiouWord  
**Status**: Initialization (additive-only mode active)  
**Purpose**: Receive, verify, and absorb evidence from progressive batches into canonical mother system  

## Structure

- `mother_model.json` — Model registry and metadata
- `module_registry.json` — All tracked modules and their current state
- `evidence_registry.jsonl` — Verified evidence items (one per line)
- `ingest_queue.jsonl` — Queued files awaiting absorption
- `dependency_map.json` — Module dependency graph
- `absorb_log.jsonl` — Log of all absorption operations
- `runtime_bridge.json` — Bridge integration status
- `verification_gate.json` — Verification requirements and status
- `replay_restore_hooks.json` — Hooks for replay/restore operations
- `state_snapshot.json` — Current state snapshot

## Scripts

- `mrl_mothermodel_ingest.py` — Add files to ingest queue
- `mrl_mothermodel_absorb.py` — Process ingest queue into registries
- `mrl_mothermodel_verify.py` — Verify all components exist and are valid
- `mrl_mothermodel_snapshot.py` — Generate state snapshot

## Usage

```bash
# Queue files for absorption
python3 scripts/mrl_mothermodel_ingest.py /path/to/file1 /path/to/file2

# Absorb queued files into registries
python3 scripts/mrl_mothermodel_absorb.py

# Verify system integrity
python3 scripts/mrl_mothermodel_verify.py

# Snapshot current state
python3 scripts/mrl_mothermodel_snapshot.py
```

## Rules

- ADDITIVE_ONLY: Files only created/appended, never overwritten or deleted
- Evidence-driven: All claims backed by SHA256 verification
- NO_RUNTIME_MUTATION: Mother system state changes only via absorption log
- Auth-gated access for BaseWorld, RuntimeDaemon bridge functions
- Reversibility law applied: all state changes are traceable and reversible

## Evidence Source

Based on MRL_EvidenceChain_Batch04_20260612:
- 348 verified evidence items (batches 01-04)
- 14 mainline nodes reconstructed
- 9 wave gate receipts (418/418 PASS)
- 1 Notion page exported (MrLiouAI 53 blocks)
- Bridge API v3.1.0 verified live

See: `../MRL_AI_ModuleModel_Recovery_Map_v1.md`
