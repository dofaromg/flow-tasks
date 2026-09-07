# Snapshot & Index – Playbook (derived from Mr.liou's teachings)
_Last updated: 2025-09-12 03:17:02Z (UTC)_

## What you taught me (core ideas)
- **Snapshot (快照)**: a reversible, verifiable freeze of state (bytes + structure) taken at a semantic boundary.
- **Index (索引)**: the minimal, queryable map to locate/restore snapshots and their relations (parents/layer/sign/N/η/domain/state).
- **Rule over compute**: prefer *structures/rules* that let modules auto-align; avoid push-style heavy computation.

## How it's encoded across our artifacts
- **OpenKit v0.2**
  - `spec/SPEC_v0.2.md` → FlowMap/JumpMap + restoration tests (hash equality + structural isomorphism).
  - `PROVENANCE.md` → manifest hash anchors (prior-art/immutability).
- **Seed Node Schema** (your JSON pattern)
  ```json
  {
    "id": "seed:Name.vX",
    "layer": 3,
    "parents": ["seed:Base.v1"],
    "sign": +1,
    "N": 12,
    "eta": 0.82,
    "domain": "physics/cfd",
    "state": "active"
  }
  ```
  → used as **Index row** for any Snapshot/Particle Unit.
- **FlowMemory.CacheNode.MUC01** (edge cache): local snapshot ring-buffer with restore hooks.
- **.fltnz / .flpkg**
  - `.fltnz` holds PU(s) + Merkle root + test vectors (**Snapshot**).
  - `.flpkg` adds adapters + spec fingerprint + attestations (**Snapshot family** + execution index).

## Minimal canonical structures
- **Snapshot Header (PU.header)**
  - `type, version, id, parent[], timestamp, env` → identity & lineage
- **Snapshot Proof (PU.proof)**
  - `sha256` of bytes; optional `merkle.root` for chunk sets
- **Index Row (SeedNode)**
  - `layer, parents, sign, N, eta, domain, state`

## Lifecycle
1. **Take** snapshot: PU(bytes, header, proof)
2. **Index** it: SeedNode row (layer/sign/N/η/domain/state)
3. **Attest**: write hash to PROVENANCE (repo/tag/sigstore)
4. **Restore**: verify `hash(in)==hash(out)` and graph isomorphism
5. **Evolve**: compute next-layer hints via `Pₖ₊₁ = Nₖ · Pₖ · ηₖ`

## One-line contracts (for humans)
- Snapshot = “可還原 + 可驗證 的凍結點”
- Index = “能把你找回來的最小地圖”

— Prepared for Mr.liou • FlowAgent
