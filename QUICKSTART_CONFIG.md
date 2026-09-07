# Quick Start: Configuration System
# 快速開始：配置系統

Get started with the FlowAgent configuration system in 5 minutes!

5 分鐘開始使用 FlowAgent 配置系統！

---

## 🚀 1. Create Your Configuration (創建配置)

```bash
# Copy the sample configuration
cp config.sample.yaml config.yaml

# Edit with your preferred editor
nano config.yaml  # or vim, code, etc.
```

---

## ⚙️ 2. Basic Configuration (基本配置)

Edit `config.yaml` with your settings:

```yaml
# Data directory for storing files
data_dir: data

# Notion integration (optional)
notion:
  enabled: false  # Set to true to enable
  database_id: ""  # Add your database ID

# GitHub integration (optional)
github:
  enabled: false  # Set to true to enable

# Context management (recommended defaults)
context_management:
  default_strategy: "workspace"  # Good for most use cases
```

---

## 💻 3. Use in Python (Python 中使用)

### Simple Usage

```python
from config_loader import ConfigLoader

# Load configuration
loader = ConfigLoader()
config = loader.load()

# Get values
data_dir = loader.get('data_dir')
print(f"Data directory: {data_dir}")
```

### With Context Management

```python
from config_loader import ConfigLoader

# Load and create strategy
loader = ConfigLoader()
strategy = loader.create_context_strategy()  # Uses default from config

# Use the strategy
results = strategy.retrieve(query="python", limit=5)
for result in results:
    print(result.content[:100])
```

---

## 🖥️ 4. Use with CLI (CLI 使用)

```bash
# Initialize ledger with config
python cli.py --config config.yaml init

# Add an entry
python cli.py --config config.yaml append "My first entry"

# Verify integrity
python cli.py --config config.yaml verify

# View log
python cli.py --config config.yaml log --n 10
```

---

## 📚 5. Run Examples (執行範例)

```bash
# Run all examples
python examples_config_usage.py

# Run tests
python test_config_loader.py

# Or with pytest
python -m pytest test_config_loader.py -v
```

---

## 🎯 Common Use Cases (常見用例)

### File-Based Workflow (檔案工作流)

Default configuration works great! Uses workspace strategy.

```python
from config_loader import ConfigLoader

loader = ConfigLoader()
workspace = loader.create_context_strategy()
results = workspace.retrieve(query="function", limit=10)
```

### Conversation Management (對話管理)

Use sliding window for real-time conversations:

```yaml
context_management:
  default_strategy: "sliding_window"
```

```python
from config_loader import ConfigLoader
from modules.context_management import ContextItem

loader = ConfigLoader()
strategy = loader.create_context_strategy()

# Add messages
strategy.add(ContextItem(
    id="msg1",
    content="Hello, how are you?",
    priority=1
))

# Get recent messages
recent = strategy.retrieve(limit=5)
```

### Long Conversation Compression (長對話壓縮)

Use summary strategy for memory efficiency:

```yaml
context_management:
  default_strategy: "summary"
```

---

## ⚡ Quick Reference (快速參考)

### Common Methods

```python
loader = ConfigLoader()

# Get configuration values
value = loader.get('key.subkey', default_value)

# Check features
if loader.is_notion_enabled():
    # Use Notion
    pass

if loader.is_github_enabled():
    # Use GitHub
    pass

# Get data directory
data_dir = loader.get_data_dir()

# Create strategies
workspace = loader.create_context_strategy('workspace')
window = loader.create_context_strategy('sliding_window')
summary = loader.create_context_strategy('summary')
rag = loader.create_context_strategy('rag')
hybrid = loader.create_context_strategy('hybrid')
```

---

## 🔧 Troubleshooting (疑難排解)

### Problem: "Config file not found"

**Solution:**
```bash
cp config.sample.yaml config.yaml
```

### Problem: "Missing required field"

**Solution:** Make sure your config.yaml has all required fields:
```yaml
data_dir: data  # Required!
```

### Problem: Strategy creation fails

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt

# For RAG with vector search:
pip install sentence-transformers
```

---

## 📖 Next Steps (下一步)

1. **Read full documentation**: See [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
2. **Explore examples**: Run `python examples_config_usage.py`
3. **Read implementation details**: See [CONFIGURATION_IMPLEMENTATION.md](CONFIGURATION_IMPLEMENTATION.md)
4. **Learn about strategies**: See [modules/context_management/README.md](modules/context_management/README.md)

---

## 🤝 Need Help? (需要幫助？)

- Check the full documentation: `docs/CONFIGURATION.md`
- Run examples: `python examples_config_usage.py`
- Run tests: `python test_config_loader.py`
- View sample config: `config.sample.yaml`

---

**That's it! You're ready to use the configuration system! 🎉**

**就是這樣！您已準備好使用配置系統！🎉**
