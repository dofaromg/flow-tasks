# MRL APIWorks First Transaction Closure v1

**Canonical ID:** `MRL_APIWorks_First_Transaction_Closure_v1`  
**Origin signature:** `MrLiouWord`  
**Product:** `MRL_APIWorks_BYOH_Deployment_Product_v1`  
**SKU:** `MRL-APIWORKS-BYOH-DEPLOY-V1`

This package is the operational evidence layer for the first real APIWorks BYOH B2B transaction. It connects the signed-order, payment, deployment, acceptance, payout, and revenue-ledger gates without placing customer personal data, Stripe secrets, bank details, or signed contracts in this public repository.

## Product baseline

- Previous acceptance-safe product baseline: `1.0.0-rc2`, PR #645, main commit `10248fd51138698d5d8aa144b969adcf8695c69e`.
- Current source candidate: `1.0.0-rc3`, adding a structured real-model acceptance receipt and verifier; it becomes a mainline baseline only after its own PR and CI complete.
- Customer ZIP SHA-256 is generated for each authorized delivery and must be verified against that delivery's receipt; no superseded rc1 hash is canonical here.
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

## Offline evidence entrance

[Evidence entry guide](docs/Mrliou_MRL_Evidence_Entry_v1.md) connects the existing
product definition, exact source, Git role records, local tests and customer ZIP
in a private offline review. Run from this package with a new output directory:

```sh
python scripts/Mrliou_MRL_build_evidence_entry_v1.py --output /absolute/new/private/review
```

Open the generated `index.html`; run `VERIFY_EVIDENCE.py` to independently
recheck its integrity. Engineering verification does not change any transaction
gate. No deployment, publishing or payment action is performed.

The repository workflow also builds this entry from the reviewed commit and
runs real Chromium desktop/mobile acceptance:

```sh
node scripts/Mrliou_MRL_browser_acceptance_v1.mjs \
  --input /absolute/review \
  --output /absolute/new/browser-evidence
```

The browser evidence contains desktop/mobile PNGs, rendered DOM snapshots,
an exact expected-file list, SHA-256 coverage and a machine-readable receipt.
It verifies the five visible sections, required content, local links, console
errors and horizontal overflow. It remains product UI evidence, not customer
model, payment or revenue evidence.

## Read-only public route receipts

`scripts/Mrliou_MRL_public_route_receipt_v1.py` captures bounded HTTPS evidence
for the three version-specific Cloudflare Preview URLs already recorded by the
closure control. It writes an exact three-file artifact containing the receipt,
expected-file list and SHA-256 manifest, and supports offline re-verification.

The manually authorized `MRL APIWorks Public Route Evidence` workflow runs only
from `main`, performs GET requests, retains the artifact for 30 days, and never
deploys, changes DNS, selects a Worker version or changes traffic allocation.
The checked-in route map deliberately keeps the canonical route unresolved and
production traffic unasserted.

## Real-model acceptance receipt

The customer package now requires the live PowerShell acceptance flow to hash a
real local model artifact, cross-check its MRL Model Release manifest, bind Git/head, hardware and operator identities,
confirm the external-model-disconnected observation, and produce a structured
receipt. `MRL_verify_live_acceptance_receipt_v1.py` rejects missing fields,
external model endpoints and non-PASS receipts. This creates the acceptance
entrypoint; a real customer/node PASS remains unasserted until it is executed on
the authorized installation.
