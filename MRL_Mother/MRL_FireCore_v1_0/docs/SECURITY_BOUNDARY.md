# Security Boundary

## Non-negotiable rules

1. The ed25519 private key does not leave DL580.
2. A Cloudflare Worker may request a signed token or signed origin result, but it must not store the private key.
3. Every persistent table and Worker-facing environment carries `origin_signature`.
4. Actual Cloudflare write operations are out of scope for this local backfill package.
5. Any future deployment must be promoted by an explicit operator step and verified through health checks.

## Required verification gates

1. Syntax gate: TypeScript parses.
2. Startup gate: Worker can bind environment values.
3. Health gate: `/health` returns an origin_signature-bearing response.
4. Endpoint gate: core route contracts respond deterministically.
5. Error gate: no new runtime error log entries after a controlled local test.
