# DL580 and Cloudflare Edge Notes

DL580 is the canonical mother node for FireCore. Cloudflare is treated as edge acceleration, routing, cache, and mirror. The architecture uses Cloudflare primitives to reduce latency, but it does not change the source of authority.

## DL580 responsibilities

- PostgreSQL canonical data state
- NAS canonical object storage
- ed25519 origin_signature signing
- PG LISTEN/NOTIFY event source
- policy decisions for writes and dispatch

## Cloudflare responsibilities

- D1 mirror tables
- KV public cache and revocation state
- R2 object cache
- Workers API façade
- Durable Objects realtime fanout
- Queues for notification dispatch
- Analytics boundary for trace events

## Consistency model

Edge state can be eventually consistent. A signed DL580 origin result is the authority marker.
