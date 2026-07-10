---
name: metaenv-api
description: >
  Mr.liou MetaEnv Control API skill — for building, deploying, and managing MetaEnv sandbox
  environments with Guard.v1 security policies, channel maps, reverse mining, encrypted
  snapshots, and lockdown capabilities. Also covers Anthropic API integration patterns
  including Messages, Batches, Beta Skills API, MCP toolsets, Memory Tool, and streaming.
  Use this skill when:
  (1) Creating or managing MetaEnv sandbox environments (spawn, health, policy, lockdown)
  (2) Working with Guard.v1 security policies and attestation
  (3) Building channel map routing (FlowMemory mount/revert)
  (4) Running reverse miner trace analysis (trace_fs/trace_ops → rules + channel_map)
  (5) Creating encrypted snapshots (non-exportable)
  (6) Handling Canary/watermark backtrace events
  (7) Integrating Anthropic API with MetaEnv (Messages, Batches, Skills, MCP, Memory)
  (8) Building Workers or agents that bridge Anthropic Claude ↔ MetaEnv control plane
  (9) Generating OpenAPI client code or Cloudflare Worker handlers for MetaEnv endpoints
---

# MetaEnv API Skill

## Architecture Overview

MetaEnv is a meta-code sandbox control system with three core pillars:

1. **Reverse Miner** — Upload trace data → generate rules + channel maps automatically
2. **Channel Map** — Mount/rollback FlowMemory paths to target applications
3. **Guard.v1** — Security policies, attestation, lockdown, encrypted snapshots

## MetaEnv API Endpoints (Quick Reference)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/env/spawn` | POST | Spawn new sandbox (cpu/gpu/ram shape) |
| `/api/v1/env/health` | GET | Health check (optional env_id filter) |
| `/api/v1/policy/apply` | POST | Apply Guard.v1 policy to env |
| `/api/v1/policy/attest/check` | POST | Verify TEE/VM attestation |
| `/api/v1/snapshot/create` | POST | Create encrypted snapshot (non-exportable) |
| `/api/v1/channel/map` | POST | Mount/rollback channel map (dry-run/apply/revert) |
| `/api/v1/reverse/miner` | POST | Upload trace → rules_yaml + channel_map_yaml |
| `/api/v1/guard/lockdown` | POST | Emergency lockdown (disconnect, revoke, freeze) |
| `/api/v1/backtrace/report` | POST | Report Canary/watermark trigger events |

For full OpenAPI schema details, see `references/metaenv_openapi.yaml`.

## Anthropic API Integration Points

When bridging Claude ↔ MetaEnv, use these Anthropic SDK patterns:

### Core APIs
- `client.messages.create()` — Standard message completion
- `client.messages.stream()` — SSE streaming
- `client.messages.countTokens()` — Token counting before send
- `client.messages.batches.create()` — Batch processing

### Beta APIs (require `?beta=true`)
- `client.beta.skills.create/retrieve/list/delete` — Skills CRUD
- `client.beta.skills.versions.create/retrieve/list/delete` — Skill versioning
- `client.beta.files.upload/download/list/delete` — File management
- `BetaMCPToolset` / `BetaMCPToolUseBlock` — MCP server integration
- `BetaMemoryTool20250818` — Memory tool (create/delete/insert/rename/str_replace/view)
- `BetaToolBash20250124` — Bash execution tool
- `BetaToolTextEditor20250728` — Text editor tool
- `BetaToolComputerUse20251124` — Computer use tool

For full SDK type reference, see `references/anthropic_sdk_api.md`.

## Common Workflows

### 1. Spawn + Secure Environment

```
POST /api/v1/env/spawn
  { shape: { cpu: 4, ram: "16G", gpu: 1 }, policy: "Mr.liou.MetaCode.Guard.v1" }
→ { ok: true, env_id: "env-xxx", status: "starting" }

POST /api/v1/policy/apply
  { env_id: "env-xxx", policy: "Mr.liou.MetaCode.Guard.v1" }
→ { ok: true }
```

### 2. Reverse Mine → Channel Map

```
POST /api/v1/reverse/miner  (multipart: trace_fs.csv + trace_ops.csv)
→ { ok: true, rules_yaml: "...", channel_map_yaml: "...", report_url: "..." }

POST /api/v1/channel/map
  { app: "MyApp", mode: "dry-run", from: "FlowMemory:/persona/MyApp",
    to: "%USERPROFILE%/Documents/MyApp" }
→ { ok: true, changes: [...], revert_token: "tok-xxx" }
```

### 3. Emergency Lockdown

```
POST /api/v1/guard/lockdown
  { reason: "canary triggered", scope: "env", env_id: "env-xxx" }
→ { ok: true, actions: ["net_disconnect", "token_revoke", "snapshot_freeze"] }
```

### 4. Anthropic → MetaEnv Worker Bridge

When building a Cloudflare Worker that bridges Claude Messages API to MetaEnv:

1. Receive user message via Claude Messages API
2. Extract tool_use blocks for MetaEnv operations
3. Forward to MetaEnv control endpoints
4. Return tool_result blocks back to Claude

Use `BetaMCPToolset` for direct MCP integration, or custom tool definitions
mapping to MetaEnv endpoints.

## Code Generation Guidelines

When generating client code or Worker handlers for MetaEnv:

- Always validate `env_id` exists before policy/snapshot/lockdown operations
- Channel map operations: default to `dry-run` mode, require explicit `apply`
- Reverse miner accepts `multipart/form-data` (trace_fs.csv + trace_ops.csv)
- Snapshot: `encrypted: true, exportable: false` are secure defaults
- Lockdown scope: prefer `env` over `global` unless explicitly requested
- All responses follow `{ ok: boolean, ... }` pattern — check `ok` first

## Reference Files

- `references/metaenv_openapi.yaml` — Complete OpenAPI 3.1.0 specification with all schemas
- `references/anthropic_sdk_api.md` — Full Anthropic SDK TypeScript API reference (types + methods)
