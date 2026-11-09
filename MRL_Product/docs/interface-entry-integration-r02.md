# MRL_Interface_v1 — Mother Entry Integration R02

origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
repository: dofaromg/flow-tasks  
base_commit: 175fa4ee7edf621f6378ef100b0057606a41d42a  
review_gate: OWNER_REVIEW_REQUIRED / NO_AUTO_MERGE / NO_DEPLOY

## Existing mother position
MRL_Product/frontend/interface.html → backend/routes/page.js → backend/server.js → existing /api, /admin, SQLite tables. Does not create a parallel system, rename original project, migrate the database, rewrite engine, memory or L0-L7 architecture.

## API wiring
- GET /interface: existing page route.
- GET /api/interface/status: current HTTP service and local SQLite query; DL580 / Bridge / V100 remain UNKNOWN, never inferred from configuration.
- GET /api/interface/timeline: read-only view of existing event_logs and analyses, scoped by session or verified user.
- Task uses existing /app, /api/analyze and product generator.
- Product uses existing /product. Admin retains /admin with separate header authentication.
- Root / continues serving the original page until Owner review.

## P0 security integration
- Email-only POST /api/login rejected. A server-side password now verifies the configured Owner email and creates a JWT with a verified claim.
- In a local secure environment set `MRL_OWNER_EMAIL`, `MRL_OWNER_PASSWORD_SCRYPT` as `saltHex:derivedKeyHex` (16-byte salt, 64-byte scrypt key). Generate on a trusted machine: `node -e "const c=require('node:crypto'),s=c.randomBytes(16),p=process.env.MRL_OWNER_PASSWORD;if(!p||p.length<12)throw Error('password >=12 chars');console.log(s.toString('hex')+':'+c.scryptSync(p,s,64).toString('hex'))"`. Never commit passwords, hashes or real .env data.
- Ownership checked before GET /api/result, GET /api/order, POST /api/pay/once and ProductPack generation/export. Existing subscription and paid-result flows remain.
- Admin key removed from URL query support for /admin/* and /api/pack listing. The admin browser session now stores it in sessionStorage rather than persistent localStorage.
- Security follow-up needed: rate limiting, CSRF/CSP, admin auth hardening and JWT/session revocation. No production approval from this change alone.

## Evidence and tests
Initial base commit pinned above; compare PR against that commit. Execute `cd MRL_Product && npm run test:interface`, Node syntax checks, existing product and payment regression tests, cross-user access tests, credential tests, and DL580 live receipt. All Gate statuses other than verified code changes are UNKNOWN until exact-head checks pass.
