# API Documentation Guide
# API 文檔指南

This guide provides a comprehensive overview of all APIs available in the FlowAgent project.

本指南提供 FlowAgent 專案中所有可用 API 的綜合概述。

---

## Table of Contents / 目錄

1. [REST API Server](#rest-api-server)
2. [MetaEnv Control API](#metaenv-control-api)
3. [Configuration API](#configuration-api)
4. [Particle Core API](#particle-core-api)
5. [Context Management API](#context-management-api)

---

## REST API Server

The REST API server is implemented in Flask and provides endpoints for text translation and trace restoration.

REST API 伺服器使用 Flask 實現，提供文本翻譯和追蹤還原的端點。

### Base URL

```
http://localhost:8080
```

### Endpoints

#### POST /translate

Translate input text using the advanced parser.

使用進階解析器翻譯輸入文本。

**Request:**
```json
{
  "text": "Your input text here"
}
```

**Response:**
```json
{
  "result": "Translated/parsed output"
}
```

**Error Response (400):**
```json
{
  "error": "Missing text parameter"
}
```

**Example:**
```bash
curl -X POST http://localhost:8080/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```

#### POST /restore

Restore trace from a file using the Fluin interpreter.

使用 Fluin 解譯器從檔案還原追蹤。

**Request:**
```json
{
  "file": "/path/to/trace/file"
}
```

**Response:**
```json
{
  "result": "Restored trace data"
}
```

**Error Response (400):**
```json
{
  "error": "Missing file parameter"
}
```

**Example:**
```bash
curl -X POST http://localhost:8080/restore \
  -H "Content-Type: application/json" \
  -d '{"file": "./traces/example.trace"}'
```

### Running the Server

```bash
python src_server_api_Version3.py
# Server starts on http://0.0.0.0:8080
```

---

## MetaEnv Control API

The MetaEnv Control API provides endpoints for managing the metacode sandbox environment. This API follows OpenAPI 3.1.0 specification.

MetaEnv Control API 提供管理元代碼沙盒環境的端點。此 API 遵循 OpenAPI 3.1.0 規範。

### Servers

| Server | Description |
|--------|-------------|
| `https://metaenv.local` | Internal controller (內網控制器) |
| `http://localhost:8000` | Development/Testing (開發測試) |

### API Categories

| Tag | Description (English) | Description (中文) |
|-----|----------------------|-------------------|
| `env` | Environment lifecycle (spawn/health) | 環境生命週期（spawn/health）|
| `policy` | Guard.v1 security policy and attestation | Guard.v1 安全政策與 attestation |
| `snapshot` | Encrypted snapshots (non-exportable) | 加密快照（不可匯出）|
| `channel` | Channel map derivation and mounting | 通道地圖推演與掛載 |
| `reverse` | Reverse miner (trace → rules/channel map) | 反推器（trace → 規則/通道地圖）|
| `guard` | Risk handling (lockdown) | 風險處理（鎖死）|
| `backtrace` | Canary event reporting | Canary 事件上報 |

### Endpoints

#### Environment Management / 環境管理

##### POST /api/v1/env/spawn

Start a new metacode sandbox.

啟動一個新的元代碼沙盒。

**Request Body:**
```json
{
  "env_id": "optional-custom-id",
  "role": "core",
  "shape": {
    "cpu": 2,
    "gpu": 0,
    "ram": "8G"
  },
  "policy": "Mr.liou.MetaCode.Guard.v1"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `env_id` | string | No | Custom ID (auto-generated if empty) |
| `role` | string | No | `core` or `node` (default: `core`) |
| `shape` | object | Yes | Resource configuration |
| `shape.cpu` | integer | Yes | CPU count (minimum: 1) |
| `shape.gpu` | integer | No | GPU count (default: 0) |
| `shape.ram` | string | Yes | RAM size (e.g., "8G") |
| `policy` | string | No | Security policy to apply |

**Response:**
```json
{
  "ok": true,
  "env_id": "generated-env-id",
  "status": "starting"
}
```

##### GET /api/v1/env/health

Query the controller health status.

查詢控制器健康狀態。

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `env_id` | string | No | Specific environment ID |

**Response:**
```json
{
  "ok": true,
  "time": "2026-02-05T16:00:00Z",
  "env_id": "env-123"
}
```

#### Security Policy Management / 安全政策管理

##### POST /api/v1/policy/apply

Apply Guard.v1 policy to an environment.

對指定環境套用 Guard.v1 政策。

**Request Body:**
```json
{
  "env_id": "env-123",
  "policy": "Mr.liou.MetaCode.Guard.v1"
}
```

**Response:**
```json
{
  "ok": true,
  "env_id": "env-123",
  "policy": "Mr.liou.MetaCode.Guard.v1"
}
```

##### POST /api/v1/policy/attest/check

Verify environment attestation evidence (optional).

驗證環境 attestation 證據（可選）。

**Request Body:**
```json
{
  "env_id": "env-123",
  "quotes": ["quote1", "quote2"]
}
```

**Response:**
```json
{
  "ok": true,
  "env_id": "env-123",
  "status": "running"
}
```

| Status | Description |
|--------|-------------|
| `running` | Environment is running |
| `terminated` | Environment terminated |
| `failed` | Environment failed |
| `pending` | Environment pending |

#### Snapshot Management / 快照管理

##### POST /api/v1/snapshot/create

Create an encrypted snapshot (non-exportable).

建立加密快照（不可匯出）。

**Request Body:**
```json
{
  "env_id": "env-123",
  "encrypted": true,
  "exportable": false,
  "label": "my-snapshot"
}
```

**Response:**
```json
{
  "ok": true,
  "snapshot_id": "snap-456",
  "encrypted": true,
  "exportable": false
}
```

#### Channel Management / 通道管理

##### POST /api/v1/channel/map

Apply channel map for mounting or rollback.

依通道地圖掛載或回滾。

**Request Body:**
```json
{
  "app": "MyApp",
  "mode": "apply",
  "from": "FlowMemory:/persona/MyApp",
  "to": "%USERPROFILE%/Documents/MyApp",
  "map": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `app` | string | Yes | Application name |
| `mode` | string | No | `dry-run`, `apply`, or `revert` (default: `dry-run`) |
| `from` | string | No | FlowMemory path |
| `to` | string | Yes | Target mount point |
| `map` | object | No | Channel map (uses server default if not provided) |

**Response:**
```json
{
  "ok": true,
  "changes": ["change1", "change2"],
  "revert_token": "token-789"
}
```

#### Reverse Mining / 反推器

##### POST /api/v1/reverse/miner

Upload trace data to generate rules and channel map.

上傳追蹤資料以產出規則與通道地圖。

**Request (multipart/form-data):**
| Field | Type | Description |
|-------|------|-------------|
| `trace_fs` | file | trace_fs.csv (fullpath, op, ts) |
| `trace_ops` | file | trace_ops.csv (ts, case, app, action, path, elevation) |

**Response:**
```json
{
  "ok": true,
  "rules_yaml": "generated rules content",
  "channel_map_yaml": "generated channel map content",
  "report_url": "https://..."
}
```

#### Guard Operations / Guard 操作

##### POST /api/v1/guard/lockdown

One-click lockdown (disconnect, revoke token, freeze snapshot).

一鍵鎖死（斷外連、撤 token、凍結快照）。

**Request Body:**
```json
{
  "reason": "Security incident",
  "scope": "env",
  "env_id": "env-123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | No | Reason for lockdown |
| `scope` | string | No | `env` or `global` (default: `env`) |
| `env_id` | string | Conditional | Required if scope is `env` |

**Response:**
```json
{
  "ok": true,
  "actions": ["disconnect", "revoke_token", "freeze_snapshot"]
}
```

#### Backtrace Reporting / 事件回報

##### POST /api/v1/backtrace/report

Report Canary/watermark triggered events.

上報 Canary/水印被觸發的事件。

**Request Body:**
```json
{
  "event_type": "canary_triggered",
  "timestamp": "2026-02-05T16:00:00Z",
  "details": {}
}
```

**Response:**
```json
{
  "ok": true,
  "id": "event-001"
}
```

---

## Configuration API

The Configuration API provides programmatic access to FlowAgent configuration.

配置 API 提供對 FlowAgent 配置的程式化存取。

### ConfigLoader Class

```python
from config_loader import ConfigLoader

loader = ConfigLoader(config_path="config.yaml")
config = loader.load()
```

### Methods

| Method | Description |
|--------|-------------|
| `load()` | Load and validate configuration |
| `get(key, default)` | Get configuration value by key (supports dot notation) |
| `get_data_dir()` | Get data directory path |
| `is_notion_enabled()` | Check if Notion integration is enabled |
| `is_github_enabled()` | Check if GitHub integration is enabled |
| `get_default_context_strategy()` | Get default context management strategy |
| `get_context_strategy_config(name)` | Get configuration for specific strategy |
| `create_context_strategy(name)` | Create a context management strategy instance |

### Example Usage

```python
from config_loader import ConfigLoader

loader = ConfigLoader()
config = loader.load()

# Get values using dot notation
data_dir = loader.get('data_dir')
notion_enabled = loader.get('notion.enabled', False)
workspace_path = loader.get('context_management.workspace.path', './workspace')

# Create context strategy
strategy = loader.create_context_strategy('workspace')
results = strategy.retrieve(query="python", limit=10)
```

For detailed configuration options, see [Configuration Documentation](./CONFIGURATION.md).

---

## Particle Core API

The Particle Core API provides access to the MRLiou Particle Language Core system.

粒子核心 API 提供對 MRLiou 粒子語言核心系統的存取。

### Core Components

| Component | Module | Description |
|-----------|--------|-------------|
| Logic Pipeline | `logic_pipeline.py` | Main logic pipeline orchestration |
| CLI Runner | `cli_runner.py` | CLI simulator and executor |
| Rebuild Function | `rebuild_fn.py` | Compression and restoration engine |
| Logic Transformer | `logic_transformer.py` | Logic transformation utilities |
| Memory Archive | `memory_archive_seed.py` | Memory archival and restoration |
| Conversation Extractor | `conversation_extractor.py` | Conversation analysis and export |
| Fluin Dict Agent | `fluin_dict_agent.py` | Dictionary seed memory snapshots |
| AI Persona Toolkit | `ai_persona_toolkit.py` | AI persona management |

### Logic Pipeline API

```python
from logic_pipeline import LogicPipeline

pipeline = LogicPipeline()

# Execute logic chain
# STRUCTURE → MARK → FLOW → RECURSE → STORE
result = pipeline.simulate(input_data)
```

### Memory Archive API

```python
from memory_archive_seed import MemoryArchiveSeed

archive = MemoryArchiveSeed()

# Create memory seed
result = archive.create_seed(
    particle_data="Your data",
    seed_name="my_memory_seed"
)

# Restore memory seed
restored = archive.restore_seed("my_memory_seed")
```

### Conversation Extractor API

```python
from conversation_extractor import ConversationExtractor

extractor = ConversationExtractor()

# Package conversation
conversation = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"}
]

package = extractor.package_conversation(
    conversation,
    metadata={"title": "Chat", "date": "2026-02-05"}
)

# Export to various formats
extractor.export_to_file(package, "chat.json", "json")
extractor.export_to_file(package, "chat.md", "markdown")
extractor.export_to_file(package, "chat.csv", "csv")

# Import from file
imported = extractor.import_from_file("chat.json")

# Analyze attention
attention = extractor.analyze_attention(conversation)

# Generate report
report = extractor.generate_report(conversation)
```

### Fluin Dict Agent API

```python
from fluin_dict_agent import FluinDictAgent

agent = FluinDictAgent()

# Echo/Jump operations
agent.create_echo("greeting", "Hello!")
agent.set_jump_point("start", 0)
agent.trigger_echo("greeting")

# Dictionary seed operations
agent.create_dict_seed(
    seed_id="my_seed",
    data={"key": "value"},
    metadata={"purpose": "demo"}
)

restored = agent.restore_dict_seed("my_seed")

# System snapshot
agent.create_snapshot("my_snapshot")

# Particle notation output
notation = agent.compress_to_particle_notation()
```

For more details, see [Particle Core README](../particle_core/README.md).

---

## Context Management API

The Context Management API provides strategies for managing conversation and file context.

上下文管理 API 提供管理對話和檔案上下文的策略。

### Available Strategies

| Strategy | Use Case |
|----------|----------|
| `workspace` | File-heavy workflows, code repositories |
| `sliding_window` | Real-time conversations, chat applications |
| `summary` | Long-running conversations that need compression |
| `rag` | Large document collections, knowledge bases |
| `hybrid` | Complex scenarios combining multiple needs |

### Usage Example

```python
from config_loader import ConfigLoader

loader = ConfigLoader()

# Create workspace strategy
workspace = loader.create_context_strategy('workspace')
results = workspace.retrieve(query="function", limit=10)

# Create sliding window strategy
window = loader.create_context_strategy('sliding_window')
recent = window.retrieve(limit=5)

# Create summary strategy
summary = loader.create_context_strategy('summary')
compressed = summary.retrieve(query="important", limit=3)
```

---

## Error Handling / 錯誤處理

All APIs follow consistent error response patterns.

所有 API 遵循一致的錯誤回應模式。

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (missing required parameters) |
| 401 | Unauthorized |
| 404 | Not Found |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": {}
}
```

---

## Rate Limiting / 速率限制

Currently, no rate limiting is enforced on local deployments. For production deployments, consider implementing rate limiting at the load balancer or API gateway level.

目前本地部署未強制執行速率限制。對於生產部署，請考慮在負載均衡器或 API 閘道層級實施速率限制。

---

## Security Considerations / 安全考量

1. **Authentication**: Implement authentication for production deployments
2. **HTTPS**: Use HTTPS for all production traffic
3. **Input Validation**: All endpoints validate input parameters
4. **Secrets Management**: Store API keys and secrets securely (not in config files)

1. **身份驗證**: 為生產部署實施身份驗證
2. **HTTPS**: 對所有生產流量使用 HTTPS
3. **輸入驗證**: 所有端點都會驗證輸入參數
4. **密鑰管理**: 安全地存儲 API 金鑰和密鑰（不在配置檔案中）

---

## Related Documentation / 相關文檔

- [Configuration Documentation](./CONFIGURATION.md)
- [Particle Core README](../particle_core/README.md)
- [MetaEnv OpenAPI Specification](../P.MetaEnv.openapi.yaml.txt)
- [Deployment Guide](../DEPLOYMENT.md)

---

*Last updated: 2026-02-05*
