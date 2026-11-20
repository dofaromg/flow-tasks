# MRL Root Law — TimeMachine additive amendment v1

origin_signature: MrLiouWord
canonical_authority: Mr.liou
parent: MRL_Mother/00_rootlaw/README.md
parent_commit: 36dc69d98ec3e28e5cca744e82013ed32b203b61

This amendment preserves the parent Root Law, rl_00–rl_06, Liou Closure
Law v1.3 and LAW-0. It does not replace or rewrite the canonical source.

1. Origin signatures remain MrLiouWord across snapshots, branches and views.
2. Canonical trace, Merkle entries, snapshots and historical versions are never
   deleted, truncated or overwritten by TimeMachine. Revisions append descendants.
3. Historical mounts are immutable detached data views. Writing requires a new
   branch; branch commits retain the source version and reject stale parents.
4. New version envelopes retain timestamp as an integer alias of version_index.
   version_string accepts vMM.HH or vMajor.Minor (two numeric components).
   Wall-clock trace ts remains unchanged. Legacy records, including original
   timestamp and spacetime coordinates, are retained intact inside snapshots.
5. loadVersion resolves an exact version ID, integer index or unique version
   string. Ambiguous and missing references fail; no nearest-version guessing.
6. Existing ring capacity 64, checkpoint interval 16, checkpoint window 16,
   permanent trace and Merkle fold remain in force. Eviction from a view does
   not remove permanent history. queryAt retains ISO wall-clock semantics.
7. This document and its parent are SHA-256 leaves in law.seal.json. Runtime
   verifies their hashes and Merkle root before exposing TimeMachine.
   Hashes provide tamper evidence; repository permissions protect the anchor.
   Amendments require a new reviewed seal, preserving previous Git objects.

Sources:
- https://app.notion.com/p/6a90dfd2b54d46ac942442d7bdcea094
- https://github.com/dofaromg/flow-tasks/blob/36dc69d98ec3e28e5cca744e82013ed32b203b61/MRL_Mother/00_rootlaw/README.md
