# DL580 Local API Map

## Bridge

- Service: `MRL_Bridge`
- Status: `Running`
- StartType: `Automatic`
- Entry: `D:\mrl\bridge\server.js`
- Runtime: `D:\MrlToolchain\node\node.exe`
- Port: `7800`
- Auth: API key SHA-256，支援 `x-api-key` 或 query `?key=`

## Public GET

- `/health`
- `/version`
- `/MRL_platform`

## Authenticated GET

- `/MRL_pg`
- `/MRL_tables`
- `/MRL_ls`
- `/MRL_cat`
- `/MRL_run`
- `/MRL_redis_cmd`
- `/MRL_sysinfo`
- `/MRL_write`
- `/MRL_audit`

## Authenticated POST

- `/MRL_file/write`
- `/MRL_file/read`
- `/MRL_file/list`
- `/MRL_exec`
- `/MRL_pg/query`
- `/MRL_redis`
- `/MRL_progress/log`

## Confirmed local modules/processes

- `MRL_Agent_Orchestrator.cjs`
- `MRL_Memory_Engine.cjs`
- `MRL_Toolchain_Engine.cjs`
- `MRL_RuntimeServer.js`
- `MRL_mrliouai_api_server.py`
- `mrl_runtime_adapter.py`
- `MRL_Operations_API.py`
- `MRL_Inference_API.py`
- Redis 6379
- PostgreSQL 5432
- FlowCoreLoop 8787
- ParticleGlobe 8788

## MCP status

未確認：

- `/mcp`
- `McpServer`
- `FastMCP`
- `@modelcontextprotocol`
- `tools/list`
- `tools/call`
- `StreamableHTTP`
