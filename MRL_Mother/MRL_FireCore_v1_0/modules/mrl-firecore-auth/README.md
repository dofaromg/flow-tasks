# mrl-firecore-auth

**Firebase counterpart:** Firebase Auth  
**Priority:** P0  
**Batch:** Batch 052  
**origin_signature:** `MrLiouWord`

## Role

Identity, password verification, refresh-token lifecycle, and DL580 signing handoff.

## Local endpoints

- `/health`
- `/v1/auth/signup`
- `/v1/auth/signin`
- `/signin`
- `/v1/auth/refresh`
- `/v1/auth/verify`

## D1 tables

- `mrl_fc_users`
- `mrl_fc_refresh_tokens`
- `mrl_fc_auth_audit`

## Deployment boundary

This module is prepared as a local backfill. Production promotion requires an explicit operator step, configured Cloudflare bindings, and DL580 signing-service availability.
