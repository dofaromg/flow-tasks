# 06_trace

Audit trail and approval records (L6 REFLECT layer).

## Sub-directories

| Directory | Purpose |
|-----------|---------|
| `traces/` | Operational JSONL trace lines + runtime data (`_data/` — gitignored) |
| `approvals/` | Human-approval proof records |

## Dual-stream design

| Stream | Writer | Schema |
|--------|--------|--------|
| Canonical | Merkle chain (`03_memory/merkle/`) | `01_schema/trace_record.schema.json` |
| Operational | JSONL append (`06_trace/traces/_data/`) | `01_schema/runtime_trace.schema.json` |

## Required trace fields

`trace_id` · `created_at` · `persona_id` · `action_id` · `action_type` · `decision` · `rule_hits` · `merkle_root` · `merkle_prev`

## Approval proof schema

Approval records must include `type` (CLI/NOTION/MOBILE), `token`, and `approved_at`.
