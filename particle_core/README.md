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
- **對話知識提取器**: 對話分析、打包與知識圖譜生成系統 (v1.0) 🆕
- **CLI 模擬器**: 命令列邏輯模擬與執行介面
- **人類可讀**: 邏輯步驟的中文說明與視覺化
- **模組化設計**: 可擴展的邏輯模組與人格生成系統

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

# 對話知識提取器
python demo_conversation_extractor.py
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

## 對話知識提取器 - Conversation Knowledge Extractor (新功能)

對話知識提取器是一個強大的工具，用於分析、打包、導入和導出對話記錄。支援注意力機制分析、邏輯結構提取和 AI 深度分析。**v1.1 新增全格式導入支援！**
對話知識提取器是一個強大的工具，用於分析、打包和導出對話記錄。支援注意力機制分析、邏輯結構提取和 AI 深度分析。

```python
from conversation_extractor import ConversationExtractor

# 初始化提取器
extractor = ConversationExtractor()

# 打包對話
conversation = [
    {"role": "user", "content": "什麼是粒子語言？"},
    {"role": "assistant", "content": "粒子語言是創新的邏輯執行框架..."}
]

package = extractor.package_conversation(
    conversation,
    metadata={"title": "粒子語言討論", "date": "2026-01-05"}
)

# 導出為多種格式 (新增支援 CSV, XML, YAML)
extractor.export_to_file(package, "conversation.json", "json")
extractor.export_to_file(package, "conversation.md", "markdown")
extractor.export_to_file(package, "conversation.csv", "csv")
extractor.export_to_file(package, "conversation.xml", "xml")
extractor.export_to_file(package, "conversation.yaml", "yaml")

# 從檔案導入 (自動檢測格式)
imported = extractor.import_from_file("conversation.json")
imported = extractor.import_from_file("conversation.md")
imported = extractor.import_from_file("conversation.csv")
    metadata={"title": "粒子語言討論", "date": "2026-01-04"}
)

# 導出為不同格式
extractor.export_to_file(package, "conversation.json", "json")
extractor.export_to_file(package, "conversation.md", "markdown")

# 注意力分析
attention = extractor.analyze_attention(conversation)
print(f"關鍵時刻: {len(attention['key_moments'])} 個")
print(f"話題轉換: {len(attention['topic_shifts'])} 個")

# 邏輯結構提取
structure = extractor.extract_logical_structure(conversation)
print(f"核心概念: {structure['concepts']}")

# 生成完整報告
report = extractor.generate_report(conversation)
with open("analysis_report.md", "w", encoding="utf-8") as f:
    f.write(report)
```

**主要功能**:
- 📦 對話打包與導出 (JSON/Markdown/TXT/YAML/CSV/HTML/XML) - 支援所有常見檔案格式
- 🎨 **主題調色盤系統** (6 種預設主題 + 自訂調色盤) - 🆕
- 🌐 **網站套件生成** (多主題 HTML + 所有格式 + 美觀索引頁) - 🆕
- 📦 **批次導出功能** (一次導出所有格式) - 🆕
- 🤖 **AI 助手網站管家** (專案管理、自動備份、版本控制) - 🆕🆕
- 📦 對話打包與導出 (JSON/Markdown/TXT/CSV/XML/YAML)
- 📥 對話導入 (JSON/Markdown/TXT/CSV/XML/YAML) 🆕
- 🔍 自動檢測檔案格式 🆕
- 📦 對話打包與導出 (JSON/Markdown/TXT)
- 🎯 注意力機制分析 (關鍵時刻、話題轉換、資訊密集段落)
- 🧬 邏輯結構提取 (概念、因果關係、推理鏈、結論)
- 🤖 AI 深度分析 (需要 Anthropic API Key)
- 📊 完整分析報告生成

**預設主題**:
- 🎨 預設 (Default) - 清新綠色
- 🌊 海洋 (Ocean) - 藍綠色調
- 🌅 日落 (Sunset) - 橙紅色調
- 🌙 夜晚 (Night) - 深色模式
- 🌲 森林 (Forest) - 自然綠色
- ⚪ 極簡 (Minimal) - 黑白灰色

詳細說明請參閱:
- [對話知識提取器使用說明 (中文)](docs/conversation_extractor_zh.md)
- [Conversation Extractor Guide (English)](docs/conversation_extractor_en.md)

### AI 助手網站管家

完整的網站專案管理系統，提供專案建立、備份、版本控制等功能。

```python
from website_manager import WebsiteManager

# 初始化管家
manager = WebsiteManager(workspace_dir="./my_websites")

# 建立專案
project_id = manager.create_project(
    project_name="我的對話網站",
    conversation=conversation,
    metadata={"title": "專案標題", "date": "2026-01-10"}
)

# 列出所有專案
projects = manager.list_projects()

# 備份專案
manager.backup_project(project_id)

# 更新主題
manager.update_project_theme(project_id, "ocean")

# 查看統計
manager.print_statistics()
```

**網站管家功能**:
- 🏗️ 專案建立與管理
- 💾 自動備份與版本控制
- 🎨 主題動態切換
- 📊 統計分析
- 🗂️ 多專案管理
- 🔍 專案查詢與預覽

## 種子資料集

- **AI Memory Protocol Seed** (`examples/AI-Memory-Protocol-Seed.json`): 保存 AI 記憶協定的語意粒子樹格式資料，包含核心粒子、章節索引與雙向記憶流程，可直接作為記憶封存/召回範例輸入。

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

```

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
## 語言規格

粒子語言的核心規格文件位於 [`language_spec/`](language_spec/) 目錄：
- 語言結構定義（.fxmanifest, .fxintro）
- 壓縮規則（.fxscale）
- 粒子詞典（.fxjson）
- 代碼範例（.pcode）
- 封包種子與邏輯圖譜（.fltnz, .flynz.map）

詳細說明請參考 [語言規格索引](language_spec/INDEX.md)。

## 授權

FlowAgent 專用任務系統內部模組
粒子語言規格遵循 CPLL 授權條款（© MR.liou）
