# MRLiou Particle Language Core

MRLiou 粒子語言核心系統 - 邏輯種子運算與函數鏈執行框架

## 功能特色

- **函數鏈執行**: 支援 STRUCTURE → MARK → FLOW → RECURSE → STORE 邏輯鏈
- **邏輯壓縮**: .flpkg 格式的邏輯模組壓縮與還原
- **記憶封存**: 完整的記憶種子創建、還原與管理系統
- **CLI 模擬器**: 命令列邏輯模擬與執行介面
- **人類可讀**: 邏輯步驟的中文說明與視覺化
- **模組化設計**: 可擴展的邏輯模組與人格生成系統
- **AI 人格套件**: 人格連結器與通用 ZIP 壓縮/解壓縮（無檔案名稱限制）
- **字典種子記憶**: Fluin Dict Agent 字典種子記憶快照系統 (DictSeed.0003)

## 快速開始

```bash
# 執行 CLI 模擬器
python src/cli_runner.py

# 邏輯管線處理
python src/logic_pipeline.py

# 壓縮還原測試
python src/rebuild_fn.py

# 記憶封存系統
python src/memory_archive_seed.py

# AI 人格通用套件
python src/ai_persona_toolkit.py

# Fluin Dict Agent 字典種子
python src/fluin_dict_agent.py
```

## Fluin Dict Agent - 字典種子記憶快照 (新功能)

✦Seed:⊕Echo/▽Jump.0001→⚙Fusion[⊕Code, △Fluin]
∞Trace → ζMemory^↻Loop
⊕Tool:μField/∴Map
⊕Core → ⟁1053
💬 粒子語句可封裝模組、展開人格、觸發記憶

[字典版本: DictSeed.0003]

```python
from fluin_dict_agent import FluinDictAgent

agent = FluinDictAgent()

# Echo/Jump 融合
agent.create_echo("greeting", "Hello Fluin!")
agent.set_jump_point("start", 0)
agent.trigger_echo("greeting")

# 字典種子操作
agent.create_dict_seed(
    seed_id="my_seed",
    data={"key": "value"},
    metadata={"purpose": "demo"}
)

# 還原種子
restored = agent.restore_dict_seed("my_seed")

# 人格展開
agent.register_persona("assistant", "Helper", ["helpful"])
agent.expand_persona("assistant")

# 工具/欄位映射
agent.register_tool("parser", "text", ["input", "output"])
agent.map_field("parser", "input", "raw_data")

# 系統快照
agent.create_snapshot("my_snapshot")

# 粒子符號輸出
print(agent.compress_to_particle_notation())
```

詳細說明請參閱 [Fluin Dict Agent 使用說明](docs/fluin_dict_agent_guide.md)

## AI 模組人格通用套件

提供 AI 人格管理與通用 ZIP 壓縮/解壓縮功能：

```python
from ai_persona_toolkit import AIPersonaToolkit

toolkit = AIPersonaToolkit()

# 人格管理
toolkit.connector.register_persona(
    persona_id="assistant",
    name="助手",
    role=["助手", "翻譯"],
    traits=["友善", "專業"]
)
toolkit.connector.connect("assistant")

# ZIP 壓縮（支援任意檔名，無限制）
toolkit.zip_handler.compress(
    {"中文檔案.txt": "內容", "special!@#$.json": "{}"},
    output_path="archive.zip"
)

# ZIP 解壓縮
toolkit.zip_handler.decompress("archive.zip", "output/")
```

詳細說明請參閱 [AI 人格套件使用說明](docs/ai_persona_toolkit_guide.md)

## 記憶封存種子系統

創建、還原與管理粒子語言記憶狀態：

```python
from memory_archive_seed import MemoryArchiveSeed

archive = MemoryArchiveSeed()

# 創建記憶種子
result = archive.create_seed(
    particle_data="您的資料",
    seed_name="my_memory_seed"
)

# 還原記憶種子
restored = archive.restore_seed("my_memory_seed")
```

詳細說明請參閱 [記憶封存種子說明](docs/記憶封存種子說明.md)

## 需求

- Python 3.10+
- fastapi, uvicorn, rich

## 文檔

- [使用指南](docs/usage_guide.md)
- [本地執行說明](docs/本地執行說明.md)
- [記憶封存種子說明](docs/記憶封存種子說明.md)
- [AI 人格套件使用說明](docs/ai_persona_toolkit_guide.md)
- [Fluin Dict Agent 使用說明](docs/fluin_dict_agent_guide.md)

## 授權

FlowAgent 專用任務系統內部模組