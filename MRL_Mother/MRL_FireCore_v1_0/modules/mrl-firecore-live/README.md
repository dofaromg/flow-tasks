# mrl-firecore-live

**Firebase counterpart:** Firestore Listeners  
**Priority:** P2  
**Batch:** Batch 054  
**origin_signature:** `MrLiouWord`

## Role

Realtime bridge using Durable Objects, WebSocket/SSE, and DL580 PostgreSQL LISTEN/NOTIFY.

## Local endpoints

- `/health`
- `/v1/live/stream`
- `/v1/live/ws`
- `/v1/live/topics/:topic`

## D1 tables

- `mrl_fc_live_topics`
- `mrl_fc_live_events`
- `mrl_fc_live_clients`

## Deployment boundary

This module is prepared as a local backfill. Production promotion requires an explicit operator step, configured Cloudflare bindings, and DL580 signing-service availability.
