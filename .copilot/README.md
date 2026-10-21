# 🧠 AI 超級電腦結構表情索引代理系統

這個目錄包含專案結構掃描和索引生成系統。

## 📁 目錄結構

```
.copilot/
├── scanner/              # 結構掃描器
│   ├── structure_scanner.py
│   └── __init__.py
├── generator/            # 表情索引生成器
│   ├── emoji_indexer.py
│   └── __init__.py
├── triggers/             # 智能更新觸發器
│   ├── smart_updater.py
│   └── __init__.py
├── structure-scan.json   # 原始掃描結果
├── structure-index.json  # 分類索引（JSON 格式）
├── structure.fltnz       # 粒子語言格式索引
└── README.md            # 本文件
```

## 🚀 使用方法

### 1. 手動執行完整掃描

從專案根目錄執行：

```bash
# 使用主入口腳本
python run_structure_index.py

# 或分步執行
python .copilot/scanner/structure_scanner.py --root . --depth 8
python .copilot/generator/emoji_indexer.py --input .copilot/structure-scan.json
```

### 2. 使用智能更新觸發器

檢查是否需要更新：

```bash
python .copilot/triggers/smart_updater.py --root . --check
```

強制更新：

```bash
python .copilot/triggers/smart_updater.py --root . --force
```

### 3. 自動更新（GitHub Actions）

系統配置了自動觸發機制：

- **定期更新**: 每週一 00:00 UTC（完整掃描）
- **增量更新**: 每天 02:00 UTC
- **Push 觸發**: 當推送代碼到 main 分支時
- **手動觸發**: 在 GitHub Actions 頁面手動觸發
- **評論觸發**: 在 Issue 中評論 `@copilot update-structure-index`

## 📊 生成的文件

1. **`.copilot/structure-scan.json`**
   - 原始掃描結果，包含完整的目錄樹和統計信息
   - 機器可讀格式

2. **`.copilot/structure-index.json`**
   - 按模組分類的索引
   - 包含檔案、統計和元數據

3. **`STRUCTURE.md`** (根目錄)
   - 人類可讀的 Markdown 格式
   - 包含專案概覽、統計和模組分類

4. **`.copilot/structure.fltnz`**
   - Fluin 粒子語言格式
   - 用於粒子語言系統集成

## 🎨 表情符號分類規則

系統會自動為檔案和目錄分配表情符號：

### 檔案類型
- 🐍 Python (`.py`)
- 📜 TypeScript/JavaScript (`.ts`, `.js`, `.tsx`, `.jsx`)
- 📝 Markdown (`.md`)
- ⚙️ 配置檔 (`.yml`, `.json`, `.toml`)
- 🧪 測試檔案 (`test_*.py`, `*.test.ts`)

### 模組類別
- 🧠 AI 核心：`ai_`, `particle_`, `neural_`, `fusion_`
- ⚙️ 系統核心：`runtime/`, `core/`, `engine/`
- 📚 文件：`docs/`, `*.md`
- 🧪 測試：`tests/`, `test_*`
- 🔧 配置：`.github/`, `*.yml`, `*.json`
- 🗂️ 資料：`data/`, `seeds/`, `memory/`
- 🎨 UI：`ui/`, `frontend/`, `components/`
- 🔐 安全：`auth/`, `secrets/`
- 📊 報表：`reports/`, `logs/`, `metrics/`

## 🔧 配置

### 掃描深度

預設掃描深度為 8 層，可以通過參數調整：

```bash
python .copilot/scanner/structure_scanner.py --depth 5
```

### 觸發閾值

在 `smart_updater.py` 中定義的觸發閾值：

```python
TRIGGER_THRESHOLDS = {
    'error_rate': 0.15,         # 錯誤率 > 15%
    'failed_builds': 3,          # 連續 3 次失敗
    'structure_changes': 10,     # 單日結構變更 > 10 個檔案
    'new_files': 5,              # 新增檔案 > 5 個
    'deleted_files': 3,          # 刪除檔案 > 3 個
    'complexity_spike': 1.5,     # 複雜度增長 > 150%
}
```

## 🧠 粒子語言標記

系統使用特殊的粒子語言標記：

```
✦Seed:⊕Scan/▽Depth8.0001→⚙Analysis[📁Files, 🗺Tree]
∞Trace → ζIndex^↻Loop
```

## 📝 維護

- 掃描結果檔案會自動生成和更新
- 所有生成的檔案都應該被提交到版本控制
- 如果專案結構有重大變更，建議手動執行一次完整掃描

## 🔗 相關資源

- [專案結構索引](../STRUCTURE.md)
- [AI Fusion Guide](../MrLiou_AI_SuperComputer/docs/AI_FUSION_GUIDE.md)
- [Particle Core README](../particle_core/README.md)

---

*本系統由 AI 超級電腦結構代理自動維護*
