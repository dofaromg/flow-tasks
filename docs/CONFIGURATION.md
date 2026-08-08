# Configuration System Documentation
# 配置系統文檔

A comprehensive configuration system for the FlowAgent project with YAML-based configuration and integration with context management strategies.

FlowAgent 專案的綜合配置系統，支援基於 YAML 的配置和上下文管理策略整合。

---

## 🚀 Quick Start (快速開始)

### 1. Create Configuration File (創建配置文件)

```bash
# Copy the sample configuration
cp config.sample.yaml config.yaml

# Edit config.yaml with your settings
# 使用您的設定編輯 config.yaml
```

### 2. Basic Usage (基本使用)

```python
from config_loader import ConfigLoader

# Load configuration
loader = ConfigLoader()
config = loader.load()

# Get configuration values
data_dir = loader.get('data_dir')
notion_enabled = loader.is_notion_enabled()
```

### 3. Use with Context Management (與上下文管理一起使用)

```python
from config_loader import ConfigLoader

loader = ConfigLoader()

# Create workspace strategy from config
workspace = loader.create_context_strategy('workspace')

# Use the strategy
results = workspace.retrieve(query="python", limit=10)
```

---

## 📋 Configuration File Structure (配置文件結構)

### Basic Settings (基本設定)

```yaml
# Data directory for storing files
data_dir: data
```

### Notion Integration (Notion 整合)

```yaml
notion:
  enabled: false          # Enable/disable Notion integration
  root_page_id: ""       # Notion root page ID (optional)
  database_id: ""        # Notion database ID (optional)
```

### GitHub Integration (GitHub 整合)

```yaml
github:
  enabled: false         # Enable/disable GitHub integration
```

### Context Management Strategies (上下文管理策略)

The configuration supports five different context management strategies:

配置支援五種不同的上下文管理策略：

#### 1. Workspace Strategy (工作空間策略) ⭐ **RECOMMENDED**

Best for file-based context management.

最適合基於文件的上下文管理。

```yaml
context_management:
  default_strategy: "workspace"
  
  workspace:
    path: "./workspace"
    watch_enabled: false
    file_patterns:
      - "*.py"
      - "*.md"
      - "*.txt"
      - "*.json"
      - "*.yaml"
    ignore_patterns:
      - ".git"
      - "node_modules"
      - "__pycache__"
      - "*.pyc"
      - ".DS_Store"
```

#### 2. Sliding Window Strategy (滑動視窗策略)

Best for real-time data streams and conversations.

最適合即時資料流和對話。

```yaml
context_management:
  sliding_window:
    window_size: 50          # Number of items to keep in window
    overlap_size: 5          # Overlap between windows
    prioritize_important: true
    max_tokens: 4096
```

#### 3. Summary Strategy (摘要壓縮策略)

Best for long conversations that need compression.

最適合需要壓縮的長對話。

```yaml
context_management:
  summary:
    segment_size: 10         # Items per segment before summarization
    preserve_recent: 5       # Number of recent items to keep uncompressed
    summary_ratio: 0.3       # Target compression ratio (30%)
    max_tokens: 4096
```

#### 4. RAG Strategy (RAG 檢索策略)

Best for document retrieval with semantic search.

最適合使用語義搜索的文件檢索。

```yaml
context_management:
  rag:
    use_vector_db: false     # Set true to use sentence-transformers
    model_name: "all-MiniLM-L6-v2"
    max_tokens: 4096
```

**Note:** When `use_vector_db: true`, you need to install sentence-transformers:

```bash
pip install sentence-transformers
```

#### 5. Hybrid Strategy (混合策略)

Combines multiple strategies for complex scenarios.

結合多種策略以應對複雜場景。

```yaml
context_management:
  hybrid:
    strategies:
      - "workspace"
      - "sliding_window"
    weights:
      - 0.6
      - 0.4
    routing_rules:
      file: "WorkspaceStrategy"
      recent: "SlidingWindowStrategy"
```

---

## 🔧 API Reference (API 參考)

### ConfigLoader Class

Main class for loading and managing configuration.

主要的配置加載和管理類別。

#### Constructor

```python
loader = ConfigLoader(config_path: Optional[Path | str] = None)
```

**Parameters:**
- `config_path`: Optional path to configuration file. If not provided, searches for:
  1. `config.yaml`
  2. `config/config.yaml`
  3. `config.sample.yaml`

#### Methods

##### load()

```python
config = loader.load() -> Dict[str, Any]
```

Load and validate configuration from file.

從文件加載並驗證配置。

**Returns:** Configuration dictionary

**Raises:** `ConfigurationError` if config is invalid

##### get()

```python
value = loader.get(key: str, default: Any = None) -> Any
```

Get configuration value by key with dot notation support.

使用點符號支援按鍵獲取配置值。

**Examples:**
```python
data_dir = loader.get('data_dir')
notion_enabled = loader.get('notion.enabled')
workspace_path = loader.get('context_management.workspace.path', './default')
```

##### get_data_dir()

```python
data_dir = loader.get_data_dir() -> Path
```

Get data directory path. Creates directory if it doesn't exist.

獲取資料目錄路徑。如果目錄不存在則創建。

##### is_notion_enabled()

```python
enabled = loader.is_notion_enabled() -> bool
```

Check if Notion integration is enabled.

##### is_github_enabled()

```python
enabled = loader.is_github_enabled() -> bool
```

Check if GitHub integration is enabled.

##### get_default_context_strategy()

```python
strategy_name = loader.get_default_context_strategy() -> str
```

Get the name of the default context management strategy.

##### get_context_strategy_config()

```python
config = loader.get_context_strategy_config(strategy_name: str) -> Dict[str, Any]
```

Get configuration for a specific context management strategy.

獲取特定上下文管理策略的配置。

**Parameters:**
- `strategy_name`: One of: `workspace`, `sliding_window`, `summary`, `rag`, `hybrid`

##### create_context_strategy()

```python
strategy = loader.create_context_strategy(strategy_name: Optional[str] = None)
```

Create and configure a context management strategy instance.

創建並配置上下文管理策略實例。

**Parameters:**
- `strategy_name`: Strategy to create, or None for default

**Returns:** Configured strategy instance

**Example:**
```python
# Create workspace strategy
workspace = loader.create_context_strategy('workspace')

# Create default strategy
default_strategy = loader.create_context_strategy()

# Use the strategy
results = workspace.retrieve(query="python", limit=5)
```

### Convenience Functions

#### load_config()

```python
from config_loader import load_config

config = load_config(config_path: Optional[Path | str] = None) -> Dict[str, Any]
```

Quick way to load configuration without creating a ConfigLoader instance.

快速加載配置而無需創建 ConfigLoader 實例。

#### get_config_loader()

```python
from config_loader import get_config_loader

loader = get_config_loader(config_path: Optional[Path | str] = None) -> ConfigLoader
```

Factory function to get a ConfigLoader instance.

---

## 💡 Usage Examples (使用範例)

### Example 1: Basic Configuration Loading

```python
from config_loader import ConfigLoader

loader = ConfigLoader()
config = loader.load()

print(f"Data directory: {config['data_dir']}")
print(f"Notion enabled: {config['notion']['enabled']}")
```

### Example 2: Using with CLI

```python
from config_loader import ConfigLoader
from amp.storage import Storage
from amp.ledger import Ledger

loader = ConfigLoader()
data_dir = loader.get_data_dir()

storage = Storage(data_dir)
ledger = Ledger(storage)

# Initialize ledger
ledger.init()
```

### Example 3: Context Management Integration

```python
from config_loader import ConfigLoader
from modules.context_management import ContextItem

# Load config and create strategy
loader = ConfigLoader()
strategy = loader.create_context_strategy()  # Uses default from config

# Add items
strategy.add(ContextItem(
    id="item1",
    content="Important information",
    priority=1
))

# Retrieve items
results = strategy.retrieve(query="information", limit=5)
```

### Example 4: Conditional Integration Features

```python
from config_loader import ConfigLoader

loader = ConfigLoader()

# Check feature flags
if loader.is_notion_enabled():
    from adapters.notion_adapter import NotionAdapter
    adapter = NotionAdapter(loader.get_data_dir())
    # Sync to Notion...

if loader.is_github_enabled():
    from adapters.github_adapter import GitHubAdapter
    adapter = GitHubAdapter(loader.get_data_dir())
    # Export to GitHub...
```

### Example 5: Multiple Strategies

```python
from config_loader import ConfigLoader

loader = ConfigLoader()

# Create different strategies for different purposes
workspace = loader.create_context_strategy('workspace')  # For files
window = loader.create_context_strategy('sliding_window')  # For conversation
summary = loader.create_context_strategy('summary')  # For compression

# Use appropriate strategy based on context
if working_with_files:
    results = workspace.retrieve(query="function", limit=10)
elif in_conversation:
    results = window.retrieve(limit=5)
```

---

## ⚙️ Configuration Best Practices (配置最佳實踐)

### 1. Keep config.yaml Private (保持 config.yaml 私密)

The `config.yaml` file is in `.gitignore` to prevent committing sensitive data.

`config.yaml` 文件在 `.gitignore` 中，以防止提交敏感數據。

- ✅ DO: Use `config.sample.yaml` as template
- ✅ DO: Copy to `config.yaml` for local use
- ❌ DON'T: Commit `config.yaml` to version control
- ❌ DON'T: Store API keys or secrets in config files

### 2. Use Environment-Specific Configs (使用特定環境的配置)

```python
import os
env = os.getenv('ENVIRONMENT', 'development')
loader = ConfigLoader(f'config/{env}.yaml')
```

### 3. Validate Configuration Early (盡早驗證配置)

```python
try:
    loader = ConfigLoader()
    config = loader.load()  # Validates on load
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    sys.exit(1)
```

### 4. Use Appropriate Strategy (使用適當的策略)

Choose the right context management strategy for your use case:

為您的用例選擇正確的上下文管理策略：

- **Workspace**: File-heavy workflows, code repositories
- **Sliding Window**: Real-time conversations, chat applications
- **Summary**: Long-running conversations that need compression
- **RAG**: Large document collections, knowledge bases
- **Hybrid**: Complex scenarios combining multiple needs

### 5. Monitor Resource Usage (監控資源使用)

```python
# For workspace strategy
workspace_config = loader.get_context_strategy_config('workspace')
if workspace_config.get('watch_enabled'):
    # File watching uses resources
    print("Note: File watching is enabled")

# For RAG strategy
rag_config = loader.get_context_strategy_config('rag')
if rag_config.get('use_vector_db'):
    # Vector DB uses memory
    print("Note: Vector database is enabled")
```

---

## 🔍 Troubleshooting (疑難排解)

### Error: "Config file not found"

**Solution:**
```bash
cp config.sample.yaml config.yaml
```

### Error: "Missing required field: data_dir"

**Solution:** Ensure `data_dir` is present in your config.yaml:
```yaml
data_dir: data
```

### Error: "Invalid default_strategy"

**Solution:** Use one of the valid strategies:
```yaml
context_management:
  default_strategy: "workspace"  # or: sliding_window, summary, rag, hybrid
```

### Strategy Creation Fails

**Check:**
1. Configuration is valid YAML
2. Required fields are present for the strategy
3. Dependencies are installed (e.g., sentence-transformers for RAG)

---

## 📚 Related Documentation (相關文檔)

- [Context Management Strategies](modules/context_management/README.md)
- [AMP Ledger CLI](README.md)
- [Configuration Sample](config.sample.yaml)

---

## 🤝 Contributing (貢獻)

When adding new configuration options:

1. Update `config.sample.yaml` with the new option
2. Add validation in `config_loader.py`
3. Add helper methods if appropriate
4. Update this documentation
5. Add examples showing the new feature

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details
