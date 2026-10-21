# 07_ingest

Ingest pipeline configuration — allowlists, denylists, and source gates (L2 PARTICLE layer).

## Sub-directories

| Directory | Purpose |
|-----------|---------|
| `allowlist/` | Explicitly permitted sources, hosts, and recipients |
| `denylist/` | Hard-blocked action types (no override possible) |

## Allowlist files

| File | Gates |
|------|-------|
| `allowlist/allowed_sources.yaml` | Trusted data sources for FILE_INGEST / WEB_FETCH |
| `allowlist/allowed_hosts.yaml` | External hosts permitted for outbound calls |
| `allowlist/allowed_recipients.yaml` | Recipients allowed for outbound messages |

## Denylist

`denylist/blocked_actions.yaml` — action types that are HARD DENIED at the kernel level (SCAN, PROBE, BRUTEFORCE, VULN_SCAN, EXPLOIT).

## Policy

Deny-by-default: sources/hosts/recipients not listed here require human approval or are denied. See `02_principles/rules.aup_v1.yaml` for rule logic.
