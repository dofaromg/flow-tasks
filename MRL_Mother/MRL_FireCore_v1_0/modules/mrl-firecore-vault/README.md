# mrl-firecore-vault

**Firebase counterpart:** Firebase Storage  
**Priority:** P1  
**Batch:** Batch 053  
**origin_signature:** `MrLiouWord`

## Role

R2 edge object cache with DL580 NAS as authoritative storage.

## Local endpoints

- `/health`
- `/v1/vault/objects`
- `/v1/vault/objects/:object_id`
- `/v1/vault/signed-url`

## D1 tables

- `mrl_fc_vault_objects`
- `mrl_fc_vault_transfers`
- `mrl_fc_vault_audit`

## Deployment boundary

This module is prepared as a local backfill. Production promotion requires an explicit operator step, configured Cloudflare bindings, and DL580 signing-service availability.
