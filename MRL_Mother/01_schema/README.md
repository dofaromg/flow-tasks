# 01_schema

JSON Schema definitions (draft-07) for all FlowAgent data contracts.

## Schemas

| File | Title | Purpose |
|------|-------|---------|
| `action_request.schema.json` | ActionRequest v1 | Agent request to perform an external action |
| `decision.schema.json` | ComplianceDecision v1 | Guard outcome: ALLOW / DENY / REQUIRE_HUMAN / REDACT |
| `runtime_trace.schema.json` | RuntimeTrace v1 | Operational JSONL trace line (fast lookup stream) |
| `trace_record.schema.json` | TraceRecord v1 | Canonical record stored in the Merkle chain |

## Relationships

```
ActionRequest → ComplianceDecision → TraceRecord (canonical, Merkle)
                                   ↘ RuntimeTrace (operational JSONL)
```

`trace_record.schema.json` embeds `action_request.schema.json` and `decision.schema.json` via `$ref`.
