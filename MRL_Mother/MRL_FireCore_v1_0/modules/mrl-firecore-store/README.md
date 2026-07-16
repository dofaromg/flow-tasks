# mrl-firecore-store

**Firebase counterpart:** Firestore  
**Priority:** P1  
**Batch:** Batch 053  
**origin_signature:** `MrLiouWord`

## Role

Collection/document model using D1 mirror with DL580 PostgreSQL as authority.

## Local endpoints

- `/health`
- `/v1/store/documents`
- `/v1/store/documents/:collection/:id`
- `/v1/store/query`

## D1 tables

- `mrl_fc_documents`
- `mrl_fc_document_versions`
- `mrl_fc_store_audit`

## Deployment boundary

This module is prepared as a local backfill. Production promotion requires an explicit operator step, configured Cloudflare bindings, and DL580 signing-service availability.
