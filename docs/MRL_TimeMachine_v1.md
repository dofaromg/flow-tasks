# MRL TimeMachine v1 — additive integration

origin_signature: MrLiouWord
canonical_authority: Mr.liou
source_parent_commit: 36dc69d98ec3e28e5cca744e82013ed32b203b61

## Canonical lineage and engineering location

- Root Law remains `MRL_Mother/00_rootlaw/README.md` and `rootlaw.yaml`.
  `/core/law.md` is an additive amendment; its parent remains untouched.
- Existing runtime: `MRL_Mother/04_runtime/flowcore_loop.py`, documented by
  `MRL_Mother/04_runtime/README.md`. Its `Tracer` now exposes TimeMachine.
- `flowagent.service` names Wakeup Core but references a compose deployment
  without a matching core service. No runnable class named WakeupCore or
  PersistentTimeline was found in the inspected default branch. Integration
  therefore uses the existing runtime Tracer and HTTP control plane, without
  inventing a second Wakeup process or persistent timeline.
- Container entry `MRL_Mother/09_workflow/MRL__Flowcore_Loop_2.py` exposes
  the same Python Tracer methods through the same adapter. Its pre-existing
  unauthenticated HTTP surface is not extended with version write endpoints.
- New adapter: `core/time_machine.py`; all data goes to existing `trace.jsonl`
  and `trace_state.json`. Existing `MerkleChain.rollback()` is never invoked.
- Historical source bundles, snapshots, MerkleChain files and Root Law are
  unchanged. No Notion source is rewritten.

## Version timeline and spacetime coordinates

The shared version envelope for both systems contains `version_id`,
`version_index`, `timestamp` (integer alias of version_index), `version_string`,
`parent_version_id`, `branch_id`, `origin_signature`, `law_merkle_root`, `snapshot`.
Coordinates retain their original names and values inside the snapshot.
Strings such as `v01.09` and `v2.0` are opaque labels, not wall-clock dates.
Indices are monotonic global integers; version strings must be globally unique.
Version lookups are exact. Branches retain explicit parent IDs and reject stale
parents rather than silently discarding concurrent changes.

Legacy trace `ts` and Merkle inputs retain their existing meaning and bytes.
`queryAt(ISO_timestamp)` returns all original-order events at or before the
requested wall-clock instant. `importLegacy(record, version_string)` preserves
the full record in `snapshot.legacy_record`; after the first snapshot use a
branch commit with the same wrapper. There is no destructive bulk migration.

## Wakeup runtime API

```python
tracer = Tracer(log_dir=existing_runtime_log_directory)
machine = tracer.timeMachine
first = machine.saveVersion({"coordinates": {"x": 1}}, "v01.09")
view = tracer.mountVersion(first["version_id"])  # recursively immutable
branch = tracer.branchFrom(first["version_id"])
next_version = branch.commit({"coordinates": {"x": 2}}, "v2.0")
changes = tracer.diffVersions(first["version_id"], next_version["version_id"])
same_view = tracer.loadVersion("v01.09")
```

History mounts are data views, not filesystem paths. They expose no write
method. Existing live Vault operations continue addressing the live vault;
they do not target or modify mounted versions.

The existing `serve` command exposes POST `/timemachine/loadVersion`,
`mountVersion`, `diffVersions`, `branchFrom`, `saveVersion` (same prefix).
All require existing `X-Human-Token`; no new credential mechanism is added.
Load/mount/branch take `version_id`; diff takes `v1`, `v2`.
Save takes `snapshot`, `version_string` and, after genesis, `branch_id`,
`parent` returned by branchFrom or the latest version ID of that branch.
JSON mounts are detached copies: changing the client response cannot change
the append-only history.

## Preservation and verification

The first snapshot archives the complete law amendment and parent document
with their seal in the existing trace Merkle chain. Every snapshot references
that seal. Runtime validates document leaves and the seal root; full trace
fold and saved head are checked before each version operation. Tampered or
incomplete history fails closed and is not repaired by truncation.

`memoryWindow()` reconstructs the latest 64 trace records and last 16
checkpoints at 16-event boundaries. Checkpoints retain trace tick/Merkle root
and the hash of the latest snapshot (null before a snapshot exists).
These are derived views; existing checkpoint/snapshot files remain untouched.

Writes are serialized within the existing runtime process. Use one writer
process per trace directory. Multi-process coordination and power-loss repair
are not introduced by this amendment; a trace/head discrepancy requires
explicit recovery and never silently passes verification.

Validation command:
`python3 -m unittest discover -s tests -p test_mrl_time_machine.py -v`
The dedicated GitHub workflow runs the same tests without third-party packages.
FSD requests is loaded lazily only for FSD operations; TimeMachine has no new
third-party runtime dependency.

## Traceable sources

- https://app.notion.com/p/6a90dfd2b54d46ac942442d7bdcea094
- https://github.com/dofaromg/flow-tasks/blob/36dc69d98ec3e28e5cca744e82013ed32b203b61/MRL_Mother/00_rootlaw/README.md
- https://github.com/dofaromg/flow-tasks/blob/36dc69d98ec3e28e5cca744e82013ed32b203b61/MRL_Mother/04_runtime/README.md
- https://github.com/dofaromg/flow-tasks/blob/36dc69d98ec3e28e5cca744e82013ed32b203b61/core/memory_system.py
