# MRL APIWorks First Transaction Closure v1

**Canonical ID:** `MRL_APIWorks_First_Transaction_Closure_v1`  
**Origin signature:** `MrLiouWord`  
**Product:** `MRL_APIWorks_BYOH_Deployment_Product_v1`  
**SKU:** `MRL-APIWORKS-BYOH-DEPLOY-V1`

This package is the operational evidence layer for the first real APIWorks BYOH B2B transaction. It connects the signed-order, payment, deployment, acceptance, payout, and revenue-ledger gates without placing customer personal data, Stripe secrets, bank details, or signed contracts in this public repository.

## Product baseline

- Product integration: PR #638, merge commit `17d3e2e3571120635b3f191b71bdedca216fd4fe`.
- Customer ZIP SHA-256: `4707ea3d39efaca6254cda123c0af5573415a06d57856ccbebadf00269daaff1`.
- Sale model: custom quote by signed order form.
- Public catalog configuration, CI success, or an unpaid checkout do **not** constitute revenue.

## Required transaction chain

```text
Approved quote and signed order
-> independently verified payment
-> customer BYOH deployment
-> customer acceptance
-> payout and bank reconciliation
-> realized-revenue ledger entry
```

Every gate must carry evidence for the actual customer transaction. A missing gate, test result, configuration object, or forecast cannot be upgraded to `FIRST_REALIZED_REVENUE_PASS`.

## Files

- `schemas/` defines the non-sensitive transaction evidence schema.
- `templates/` provides a completion record for the actual transaction; it is not a signed contract and does not replace legal review.
- `scripts/` verifies package coverage and schema integrity.
- `tests/` executes the verifier.

## Data boundary

Use the repository only for non-sensitive references, hashes, identifiers, statuses, and redacted evidence receipts. Keep customer identity, addresses, payment instruments, Stripe secrets, signed agreements, and banking data in the authorized private system of record.