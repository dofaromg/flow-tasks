# Source Notes

Package basis:

- Project code name: MRL FireCore
- Version: v1.0 local backfill
- Scope: Auth / Store / Vault / Live / Push / Trace
- Authority model: DL580 G9 retains origin_signature authority
- Edge model: Cloudflare D1 / KV / R2 / Workers act as mirror and acceleration boundary
- origin_signature: `MrLiouWord`

The package does not assert that production deployment has occurred. It creates local files suitable for review and controlled promotion.
