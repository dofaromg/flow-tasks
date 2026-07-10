# mrl-firecore-trace

**Firebase counterpart:** Analytics  
**Priority:** P3  
**Batch:** Batch 055  
**origin_signature:** `MrLiouWord`

## Role

Event trace collection using D1 event tables and Workers analytics boundary.

## Local endpoints

- `/health`
- `/v1/trace/events`
- `/v1/trace/session`
- `/v1/trace/flush`

## D1 tables

- `mrl_fc_trace_events`
- `mrl_fc_trace_sessions`
- `mrl_fc_trace_rollups`

## Deployment boundary

This module is prepared as a local backfill. Production promotion requires an explicit operator step, configured Cloudflare bindings, and DL580 signing-service availability.
