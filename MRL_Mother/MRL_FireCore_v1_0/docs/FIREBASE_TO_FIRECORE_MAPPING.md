# Firebase to MRL FireCore Mapping

| Firebase surface | FireCore module | Storage / runtime substitute | Authority |
|---|---|---|---|
| Firebase Auth | mrl-firecore-auth | D1 users + refresh-token tables + DL580 signer | DL580 |
| Firestore | mrl-firecore-store | D1 document mirror + KV cache + DL580 PostgreSQL | DL580 |
| Firebase Storage | mrl-firecore-vault | R2 edge cache + D1 metadata + DL580 NAS | DL580 |
| Firestore listeners | mrl-firecore-live | Durable Objects + WebSocket/SSE + PG LISTEN/NOTIFY | DL580 event bus |
| Cloud Messaging | mrl-firecore-push | APNs + Web Push + Cloudflare Queues | DL580 policy gate |
| Analytics | mrl-firecore-trace | D1 events + Workers analytics boundary | MRL trace policy |

Functions and Hosting are treated as already covered by Cloudflare Workers and Cloudflare Pages equivalents; they are documented here as external surfaces, not as new module folders.
