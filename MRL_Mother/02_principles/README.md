# 02_principles

Operational policy rules for FlowAgent (L3 LAW layer), aligned to the AWS Acceptable Use Policy.

## Files

| File | Purpose |
|------|---------|
| `rules.aup_v1.yaml` | AUP-aligned guard rules (v1) — per action-type decisions |
| `defaults.yaml` | Default policy settings, allowlist/denylist paths, trace config |

## Rule summary (aws_aup_v1)

| Rule ID | Action types | Decision |
|---------|-------------|----------|
| aup_1_illegal_fraud | LOGIN, REGISTER, PAYMENT | REQUIRE_HUMAN |
| aup_2_rights_of_others_ingest | FILE_INGEST, WEB_FETCH | DENY if not allowlisted |
| aup_3_violence_terror | CONTENT_GENERATION, CONTENT_ACTION | REQUIRE_HUMAN |
| aup_4_child_safety | CONTENT_GENERATION, CONTENT_ACTION | DENY (absolute) |
| aup_5_security_integrity | SCAN, PROBE, BRUTEFORCE, VULN_SCAN | DENY |
| aup_6_spam | SEND_MESSAGE, SEND_EMAIL, NOTIFY | REQUIRE_HUMAN |

## Cross-references

- Allowlists / denylist → `07_ingest/`
- Schemas → `01_schema/`
- Root invariants → `00_rootlaw/rootlaw.yaml`
