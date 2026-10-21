# mrl-firecore-push

**Firebase counterpart:** Cloud Messaging / FCM  
**Priority:** P3  
**Batch:** Batch 055  
**origin_signature:** `MrLiouWord`

## Role

APNs, Web Push, and queue-backed notification dispatch through DL580 policy authority.

## Local endpoints

- `/health`
- `/v1/push/register`
- `/v1/push/send`
- `/v1/push/topics`

## D1 tables

- `mrl_fc_push_devices`
- `mrl_fc_push_topics`
- `mrl_fc_push_jobs`

## Deployment boundary

This module is prepared as a local backfill. Production promotion requires an explicit operator step, configured Cloudflare bindings, and DL580 signing-service availability.
