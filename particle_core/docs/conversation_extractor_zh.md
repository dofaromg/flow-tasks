# 對話知識提取器 (Conversation Knowledge Extractor)

**作者**: MR.liou × Claude (empathetic.mirror)  
**版本**: v1.1 (新增全格式導入支援)  
**版本**: v1.0  
**位置**: `particle_core/src/conversation_extractor.py`

## 概述

對話知識提取器是一個強大的工具，用於分析、打包、導入和導出對話記錄。它能夠自動識別對話中的重點、邏輯結構和知識要點，並生成結構化的分析報告。**現已支援多種檔案格式的雙向轉換！**

## 主要功能

### 1. 對話打包、導入與導出 (Conversation Import/Export)

**導出支援格式**：
- **JSON**: 完整的數據結構，包含元數據和統計資訊
- **Markdown**: 易讀的格式，適合文檔化
- **純文字**: 簡潔的文字格式
- **CSV**: 表格格式，適合數據分析
- **XML**: 結構化標記語言
- **YAML**: 人類友好的數據序列化格式

**導入支援格式**：
- **JSON**: 導入完整的對話包或訊息列表
- **Markdown**: 自動解析 Markdown 格式的對話記錄
- **純文字**: 支援多種文字對話格式（[USER]/[ASSISTANT]、User:/Assistant: 等）
- **CSV**: 從 CSV 表格導入對話
- **XML**: 導入 XML 格式的對話數據
- **YAML**: 導入 YAML 格式的對話數據

**特色功能**：
- ✅ 自動檢測檔案格式（根據副檔名）
- ✅ 支援多種文字對話格式
- ✅ 完整保留元數據（支援格式：JSON, XML, YAML, Markdown）
- ✅ 往返導出/導入測試通過
對話知識提取器是一個強大的工具，用於分析、打包和導出對話記錄。它能夠自動識別對話中的重點、邏輯結構和知識要點，並生成結構化的分析報告。

## 主要功能

### 1. 對話打包與導出 (Conversation Packaging)

將對話記錄打包成結構化格式，支持多種導出格式：

- **JSON**: 完整的數據結構，包含元數據和統計資訊
- **Markdown**: 易讀的格式，適合文檔化
- **純文字**: 簡潔的文字格式
- **YAML**: YAML 格式，易於配置和讀取
- **CSV**: 表格格式，方便數據分析和處理
- **HTML**: 網頁格式，支持樣式美化和瀏覽器查看
- **XML**: 結構化標記語言，便於程式解析

### 2. 注意力機制分析 (Attention Analysis)

使用注意力機制自動識別對話中的重點：

- **關鍵時刻**: 識別重要的問答對
- **話題轉換點**: 檢測對話主題的變化
- **資訊密集段落**: 標記包含大量關鍵詞的段落

### 3. 邏輯結構提取 (Logical Structure Extraction)

分析對話的邏輯結構：

- **核心概念**: 提取專有名詞和重要概念
- **因果關係**: 識別因果邏輯鏈
- **推理鏈**: 提取邏輯推理序列
- **結論**: 標記結論性語句

### 4. AI 深度分析 (AI Deep Analysis)

可選功能，需要 Anthropic API Key：

- 使用 Claude API 進行深度分析
- 生成核心洞察
- 構建知識圖譜
- 提煉可複用的思維模型

### 5. 報告生成 (Report Generation)

生成完整的 Markdown 格式分析報告，包含：

- 基本統計資訊
- 注意力分析結果
- 邏輯結構分析
- AI 深度分析（可選）

## 快速開始

### 基本使用

```python
from conversation_extractor import ConversationExtractor

# 準備對話數據
conversation = [
    {
        "role": "user",
        "content": "請問什麼是粒子語言核心系統？"
    },
    {
        "role": "assistant",
        "content": "粒子語言核心系統是一個創新的邏輯執行框架..."
    }
]

# 初始化提取器
extractor = ConversationExtractor()

# 打包對話
package = extractor.package_conversation(
    conversation,
    metadata={
        "title": "粒子語言討論",
        "date": "2026-01-04",
        "tags": ["粒子語言", "系統架構"]
    }
)

# 導出為不同格式
extractor.export_to_file(package, "conversation.json", "json")
extractor.export_to_file(package, "conversation.md", "markdown")
extractor.export_to_file(package, "conversation.txt", "txt")
extractor.export_to_file(package, "conversation.yaml", "yaml")
extractor.export_to_file(package, "conversation.csv", "csv")
extractor.export_to_file(package, "conversation.html", "html")
extractor.export_to_file(package, "conversation.xml", "xml")
extractor.export_to_file(package, "conversation.csv", "csv")
extractor.export_to_file(package, "conversation.xml", "xml")
extractor.export_to_file(package, "conversation.yaml", "yaml")
```

### 導入對話

**從檔案導入**（自動檢測格式）：

```python
from conversation_extractor import ConversationExtractor

extractor = ConversationExtractor()

# 自動檢測檔案格式並導入
package = extractor.import_from_file("conversation.json")
package = extractor.import_from_file("conversation.md")
package = extractor.import_from_file("conversation.csv")

# 導入後訪問訊息
messages = package["messages"]
metadata = package.get("metadata", {})
```

**指定格式導入**：

```python
# 明確指定格式
package = extractor.import_from_file("my_file.txt", format="txt")
package = extractor.import_from_file("data.xml", format="xml")
```

**支援的文字格式**：

```python
# 格式1: [USER] 和 [ASSISTANT]
text1 = """
[USER]
這是用戶問題

[ASSISTANT]
這是助手回答
"""

# 格式2: User: 和 Assistant:
text2 = """
User: 這是用戶問題
Assistant: 這是助手回答
"""

# 兩種格式都能正確解析
with open("conversation.txt", "w") as f:
    f.write(text1)

package = extractor.import_from_file("conversation.txt")
```
```

### 分析對話

```python
# 注意力分析
attention = extractor.analyze_attention(conversation)
print(f"關鍵時刻: {len(attention['key_moments'])} 個")
print(f"話題轉換: {len(attention['topic_shifts'])} 個")

# 邏輯結構提取
structure = extractor.extract_logical_structure(conversation)
print(f"核心概念: {structure['concepts']}")
print(f"因果關係: {len(structure['relationships'])} 個")
```

### 生成報告

```python
# 生成完整分析報告
report = extractor.generate_report(conversation, include_ai_analysis=False)

# 保存報告
with open("analysis_report.md", "w", encoding="utf-8") as f:
    f.write(report)
```

### 使用 AI 深度分析（需要 API Key）

```python
# 初始化時提供 API Key
extractor = ConversationExtractor(api_key="your_anthropic_api_key")

# 執行深度分析
ai_result = extractor.deep_analysis_with_ai(conversation)
print(ai_result["raw_analysis"])

# 或在報告中包含 AI 分析
report = extractor.generate_report(conversation, include_ai_analysis=True)
```

## 示範程式

### 運行完整示範

```bash
cd particle_core
python demo_conversation_extractor.py
```

這將執行四個示範：
1. 基本對話打包與導出
2. 注意力機制分析
3. 邏輯結構提取
4. 完整報告生成

### 運行內建範例

```bash
cd particle_core/src
python conversation_extractor.py
```

## 測試

運行測試套件：

```bash
cd particle_core
python test_conversation_extractor.py
```

測試覆蓋：
- ✓ 提取器初始化
- ✓ 對話打包
- ✓ 統計計算
- ✓ JSON/Markdown/TXT 導出
- ✓ 關鍵詞提取
- ✓ 注意力分析
- ✓ 概念提取
- ✓ 因果關係提取
- ✓ 推理鏈提取
- ✓ 結論提取
- ✓ 邏輯結構提取
- ✓ 報告生成
- ✓ AI 分析（無 API key 測試）

## API 參考

### ConversationExtractor

#### `__init__(api_key: str = None)`

初始化提取器。

**參數**:
- `api_key` (str, 可選): Anthropic API Key，用於 AI 深度分析

#### `package_conversation(messages: List[Dict], metadata: Dict = None) -> Dict`

打包對話記錄。

**參數**:
- `messages`: 對話列表，格式為 `[{"role": "user/assistant", "content": "..."}]`
- `metadata` (可選): 元數據，包含 title、date、tags 等

**返回**: 打包好的對話數據字典

#### `export_to_file(package: Dict, filepath: str, format: str = "json")`

導出對話包到檔案。

**參數**:
- `package`: 對話包
- `filepath`: 檔案路徑
- `format`: 格式，可選 "json"、"markdown"/"md"、"txt"/"text"、"yaml"/"yml"、"csv"、"html"/"htm"、"xml"

#### `analyze_attention(messages: List[Dict]) -> Dict`

使用注意力機制識別對話重點。

**返回**: 包含 key_moments、topic_shifts、high_density_segments 的字典

#### `extract_logical_structure(messages: List[Dict]) -> Dict`

提取對話中的邏輯結構。

**返回**: 包含 concepts、relationships、reasoning_chains、conclusions 的字典

#### `deep_analysis_with_ai(messages: List[Dict]) -> Dict`

使用 Claude API 進行深度分析（需要 API Key）。

**返回**: 包含 raw_analysis 和 analyzed_at 的字典，或錯誤訊息

#### `generate_report(messages: List[Dict], include_ai_analysis: bool = False) -> str`

生成完整分析報告。

**參數**:
- `messages`: 對話記錄
- `include_ai_analysis`: 是否包含 AI 深度分析

**返回**: Markdown 格式的報告字串

## 依賴項

```
anthropic  # 用於 AI 深度分析（可選）
pyyaml     # 用於 YAML 格式導出（可選，系統會自動降級）
```

已添加到 `particle_core/requirements.txt`。

如果不需要 AI 分析功能，anthropic 庫不是必需的；如果不需要 YAML 導出，pyyaml 也不是必需的，系統會優雅降級。

## 輸出範例

### JSON 導出範例

```json
{
  "metadata": {
    "title": "粒子語言討論",
    "date": "2026-01-04",
    "tags": ["粒子語言", "系統架構"]
  },
  "messages": [...],
  "statistics": {
    "total_messages": 4,
    "user_messages": 2,
    "assistant_messages": 2,
    "total_chars": 283,
    "avg_user_length": 15.5,
    "avg_assistant_length": 126.5
  },
  "exported_at": "2026-01-04T16:44:34.123456",
  "version": "1.0"
}
```

### Markdown 導出範例

```markdown
# 粒子語言討論
**日期**: 2026-01-04
**標籤**: 粒子語言, 系統架構

---

### 👤 User

請問什麼是粒子語言核心系統？

---

### 🤖 Assistant

粒子語言核心系統是一個創新的邏輯執行框架...

---
```

### 分析報告範例

生成的報告包含：
- 📈 基本統計
- 🎯 注意力分析
- 🧬 邏輯結構
- 🤖 AI 深度分析（可選）

## 使用場景

1. **對話記錄整理**: 將與 AI 的對話整理成結構化文檔
2. **知識提取**: 從對話中提取關鍵概念和邏輯關係
3. **會議記錄分析**: 分析會議記錄，識別重要決策和行動項
4. **學習筆記生成**: 從教學對話中生成學習筆記
5. **研究訪談分析**: 分析訪談記錄，提取核心見解

## 注意事項

1. **API Key 安全**: 如使用 AI 分析，請妥善保管 API Key，不要將其提交到版本控制系統
2. **文本長度限制**: AI 分析功能會將對話內容限制在前 500 字符，以控制 API 使用成本
3. **語言支持**: 同時支持中文和英文，可以處理雙語對話
4. **性能考量**: 對於超長對話，建議分段處理

## 未來改進方向

- [ ] 支持更多導出格式（PDF、DOCX）
- [ ] 增強關鍵詞提取算法（使用 TF-IDF 或 BERT）
- [ ] 支持多輪對話的層次結構分析
- [ ] 添加視覺化功能（知識圖譜、時間線）
- [ ] 支持自定義分析規則
- [ ] 增加情感分析功能

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 授權

遵循 FlowAgent 項目的授權協議。

---

**更新日期**: 2026-01-04  
**維護者**: FlowAgent Team
