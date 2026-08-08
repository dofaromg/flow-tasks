# MRL FireCore v1.0 Local Backfill Package

**Target local path:** `D:\modules\MRL_FireCore_v1_0`  
**Package date:** 2026-07-01T15:52:08Z  
**origin_signature:** `MrLiouWord`

This package is a local disk backfill for MRL FireCore v1.0. It reconstructs a verifiable module tree for the Firebase replacement layer without performing Cloudflare writes, network deployment, or DL580 mutation.

## Included FireCore modules

| Module | Firebase counterpart | Priority | Batch | Local scope |
|---|---|---:|---|---|
| `mrl-firecore-auth` | Firebase Auth | P0 | Batch 052 | Identity, password verification, refresh-token lifecycle, and DL580 signing handoff. |
| `mrl-firecore-store` | Firestore | P1 | Batch 053 | Collection/document model using D1 mirror with DL580 PostgreSQL as authority. |
| `mrl-firecore-vault` | Firebase Storage | P1 | Batch 053 | R2 edge object cache with DL580 NAS as authoritative storage. |
| `mrl-firecore-live` | Firestore Listeners | P2 | Batch 054 | Realtime bridge using Durable Objects, WebSocket/SSE, and DL580 PostgreSQL LISTEN/NOTIFY. |
| `mrl-firecore-push` | Cloud Messaging / FCM | P3 | Batch 055 | APNs, Web Push, and queue-backed notification dispatch through DL580 policy authority. |
| `mrl-firecore-trace` | Analytics | P3 | Batch 055 | Event trace collection using D1 event tables and Workers analytics boundary. |


## Install on Windows

Open PowerShell from the extracted package root and run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install_to_D_modules.ps1 -DestinationRoot D:\modules
```

Then verify:

```powershell
.\verify_backfill.ps1 -Root D:\modules\MRL_FireCore_v1_0
```

## Safety boundary

- No production secrets are included.
- No ed25519 private key is included.
- No Cloudflare D1 / KV / R2 / Worker write is executed by this package.
- DL580 remains the authoritative origin_signature signer.
- The package is intended for local reconstruction, inspection, and later controlled deployment.
