# Expected Dependency Tree

```text
MRL_FireCore_v1_0
├─ DL580 G9 Mother Node
│  ├─ origin_signature signer: ed25519
│  ├─ PostgreSQL: mrl_baseworld + mrl_firecore
│  ├─ NAS: D:\MRL_Mother\storage
│  └─ PG LISTEN/NOTIFY event bus
├─ Cloudflare Edge Boundary
│  ├─ D1 mirror tables: mrl_fc_*
│  ├─ KV namespace: mrliouword-vault
│  ├─ R2 bucket: mrl-firecore-vault
│  ├─ Workers: mrl-firecore-*
│  └─ Durable Objects / Queues / Analytics boundary
├─ FireCore Modules
│  ├─ mrl-firecore-auth  -> Firebase Auth replacement
│  ├─ mrl-firecore-store -> Firestore replacement
│  ├─ mrl-firecore-vault -> Firebase Storage replacement
│  ├─ mrl-firecore-live  -> Firestore listener replacement
│  ├─ mrl-firecore-push  -> FCM replacement
│  └─ mrl-firecore-trace -> Analytics replacement
└─ SDK Surface
   ├─ Web SDK compatibility notes
   └─ iOS SDK compatibility notes
```

All module files carry either `origin_signature` in schema/config/code or an explicit local backfill declaration.
