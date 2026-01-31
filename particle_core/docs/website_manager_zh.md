# 🤖 AI 助手網站管家文檔

## 概述

AI 助手網站管家 (Website Manager) 是一個完整的網站專案管理系統，提供專案建立、備份、版本控制、主題管理等功能。讓你輕鬆管理多個對話網站專案。

**版本**: v1.0  
**作者**: MR.liou × Copilot  
**日期**: 2026-01-10

## 快速開始

### 安裝

網站管家已包含在 particle_core 模組中：

```python
from website_manager import WebsiteManager
```

### 基本使用

```python
# 初始化管家
manager = WebsiteManager(workspace_dir="./my_websites")

# 建立專案
conversation = [
    {"role": "user", "content": "你好！"},
    {"role": "assistant", "content": "你好，有什麼可以幫助你的嗎？"}
]

project_id = manager.create_project(
    project_name="我的對話網站",
    conversation=conversation,
    metadata={
        "title": "對話記錄",
        "date": "2026-01-10",
        "tags": ["示範", "測試"]
    }
)

# 查看專案
projects = manager.list_projects()

# 備份專案
manager.backup_project(project_id)
```

## 核心功能

### 1. 專案管理

#### 建立專案

```python
project_id = manager.create_project(
    project_name="專案名稱",
    conversation=conversation_data,
    metadata={
        "title": "對話標題",
        "date": "2026-01-10",
        "tags": ["標籤1", "標籤2"]
    },
    themes=["default", "ocean", "sunset"]  # 可選，預設所有主題
)
```

**參數**:
- `project_name` (str): 專案名稱
- `conversation` (List[Dict]): 對話內容
- `metadata` (Dict, 可選): 對話元數據
- `themes` (List[str], 可選): 要生成的主題列表

**返回**: 專案 ID (字串)

#### 列出專案

```python
projects = manager.list_projects()
```

**返回**: 專案資訊列表

輸出示例:
```
📋 專案列表
============================================================

🔹 我的對話網站
   ID: proj_20260110_171210_123456
   建立時間: 2026-01-10T17:12:10
   主題數量: 6 個
   版本: v1
============================================================
```

#### 取得專案資訊

```python
project = manager.get_project(project_id)
```

**返回**: 專案資訊字典或 None

專案資訊結構:
```python
{
    "project_id": "proj_xxx",
    "project_name": "專案名稱",
    "created_at": "2026-01-10T17:12:10",
    "updated_at": "2026-01-10T17:12:10",
    "directory": "/path/to/project",
    "themes": ["default", "ocean", "sunset"],
    "metadata": {...},
    "statistics": {...},
    "version": 1
}
```

#### 刪除專案

```python
# 需要確認
manager.delete_project(project_id, confirm=True)
```

**注意**: 刪除前會自動備份專案

### 2. 備份與版本控制

#### 手動備份

```python
backup_path = manager.backup_project(project_id)
```

**返回**: 備份檔案路徑

**備份檔名格式**: `proj_xxx_v1_20260110_171210.zip`

#### 自動備份

更新專案時會自動備份（如果啟用）:

```python
# 在配置中設定
manager.config["settings"]["auto_backup"] = True  # 預設啟用
```

#### 備份清理

自動清理舊備份，保留最新的 N 個：

```python
# 設定保留數量
manager.config["settings"]["max_backups"] = 10  # 預設 10 個
manager._save_config()
```

### 3. 主題管理

#### 更新專案主題

```python
manager.update_project_theme(project_id, "ocean")
```

支援的主題:
- `default` - 預設主題
- `ocean` - 海洋主題
- `sunset` - 日落主題
- `night` - 夜晚主題
- `forest` - 森林主題
- `minimal` - 極簡主題

### 4. 統計分析

#### 取得統計資訊

```python
stats = manager.get_statistics()
```

**返回**:
```python
{
    "total_projects": 5,
    "total_backups": 12,
    "total_conversations": 5,
    "total_messages": 47,
    "workspace_dir": "./my_websites",
    "created_at": "2026-01-10T17:00:00"
}
```

#### 顯示統計

```python
manager.print_statistics()
```

輸出示例:
```
📊 網站管家統計
============================================================
   專案總數: 5 個
   備份總數: 12 個
   對話總數: 5 個
   訊息總數: 47 條
   工作空間: ./my_websites
   建立時間: 2026-01-10T17:00:00
============================================================
```

### 5. 瀏覽器整合

#### 在瀏覽器中打開專案

```python
manager.open_project(project_id)
```

自動使用系統預設瀏覽器打開專案的索引頁面。

## 配置系統

### 配置檔案

管家的配置儲存在 `workspace_dir/manager_config.json`：

```json
{
    "version": "1.0",
    "created_at": "2026-01-10T17:00:00",
    "projects": {
        "proj_xxx": {
            "project_id": "proj_xxx",
            "project_name": "專案名稱",
            "created_at": "2026-01-10T17:12:10",
            "updated_at": "2026-01-10T17:12:10",
            "directory": "/path/to/project",
            "themes": ["default", "ocean"],
            "metadata": {...},
            "statistics": {...},
            "version": 1
        }
    },
    "settings": {
        "auto_backup": true,
        "default_theme": "default",
        "max_backups": 10
    }
}
```

### 修改配置

```python
# 修改設定
manager.config["settings"]["max_backups"] = 20
manager.config["settings"]["default_theme"] = "ocean"

# 儲存配置
manager._save_config()
```

## 工作空間結構

```
workspace/
├── projects/                    # 專案目錄
│   ├── proj_20260110_171210/
│   │   ├── index.html          # 索引頁面
│   │   ├── conversation_default.html
│   │   ├── conversation_ocean.html
│   │   ├── conversation.json
│   │   ├── conversation.yaml
│   │   ├── conversation.csv
│   │   └── ...
│   └── proj_20260110_171220/
│       └── ...
├── backups/                     # 備份目錄
│   ├── proj_xxx_v1_timestamp.zip
│   ├── proj_xxx_v2_timestamp.zip
│   └── ...
└── manager_config.json          # 配置檔案
```

## 進階用法

### 批次操作

```python
# 備份所有專案
for project_id in manager.config["projects"]:
    manager.backup_project(project_id)
```

### 自訂工作空間

```python
# 使用自訂工作空間
manager = WebsiteManager(workspace_dir="/custom/path")
```

### 條件查詢

```python
# 查詢特定條件的專案
ocean_projects = [
    p for p in manager.config["projects"].values()
    if "ocean" in p.get("themes", [])
]
```

## 最佳實踐

### 1. 定期備份

```python
# 建議在重要操作前備份
manager.backup_project(project_id)
manager.update_project_theme(project_id, "new_theme")
```

### 2. 專案命名

使用有意義的專案名稱：

```python
project_id = manager.create_project(
    project_name="2026-01 客戶支援對話記錄",  # 好
    # 不要: "project1"  # 不好
    conversation=conversation
)
```

### 3. 元數據管理

提供完整的元數據：

```python
metadata = {
    "title": "清晰的標題",
    "date": "2026-01-10",
    "tags": ["分類1", "分類2"],
    "author": "作者名稱",
    "description": "簡短描述"
}
```

### 4. 備份策略

```python
# 根據專案重要性調整備份數量
manager.config["settings"]["max_backups"] = 20  # 重要專案
manager._save_config()
```

## 錯誤處理

### 常見錯誤

#### 1. ConversationExtractor 不可用

```python
try:
    manager = WebsiteManager()
except RuntimeError as e:
    print(f"錯誤: {e}")
    # 確保 conversation_extractor.py 在正確路徑
```

#### 2. 專案不存在

```python
project = manager.get_project("non_existent_id")
if project is None:
    print("專案不存在")
```

#### 3. 工作空間權限

```python
import os
workspace = "./my_websites"
if not os.access(workspace, os.W_OK):
    print("沒有寫入權限")
```

## API 參考

### WebsiteManager

#### 初始化

```python
WebsiteManager(workspace_dir: str = None)
```

#### 方法

| 方法 | 說明 |
|------|------|
| `create_project()` | 建立新專案 |
| `list_projects()` | 列出所有專案 |
| `get_project()` | 取得專案資訊 |
| `update_project_theme()` | 更新專案主題 |
| `delete_project()` | 刪除專案 |
| `backup_project()` | 備份專案 |
| `get_statistics()` | 取得統計資訊 |
| `print_statistics()` | 顯示統計資訊 |
| `open_project()` | 在瀏覽器中打開 |

## 示範腳本

運行示範:

```bash
cd particle_core/src
python website_manager.py
```

## 測試

運行測試套件:

```bash
cd particle_core
python test_website_manager.py
```

測試覆蓋:
- ✅ 管家初始化
- ✅ 專案建立
- ✅ 專案列表
- ✅ 專案查詢
- ✅ 專案備份
- ✅ 主題更新
- ✅ 專案刪除
- ✅ 統計資訊
- ✅ 配置持久化
- ✅ 備份清理

## 常見問題

### Q: 如何遷移工作空間？

A: 直接複製整個工作空間目錄即可：

```bash
cp -r ./my_websites ./new_location/
```

### Q: 如何恢復備份？

A: 解壓縮備份檔案到專案目錄：

```bash
unzip backup.zip -d workspace/projects/proj_xxx/
```

### Q: 專案 ID 如何生成？

A: 使用時間戳+微秒確保唯一性：

```
proj_YYYYMMDD_HHMMSS_microseconds
```

### Q: 可以手動編輯配置檔嗎？

A: 可以，但建議通過 API 操作以確保一致性。

## 限制與注意事項

1. **檔案系統依賴**: 需要檔案系統寫入權限
2. **配置格式**: 配置檔必須是有效的 JSON
3. **專案 ID**: 專案 ID 一旦生成不可更改
4. **備份大小**: 大型專案的備份可能較大
5. **並發**: 不支援多進程並發操作

## 未來改進

計劃中的功能:
- [ ] Web UI 管理介面
- [ ] 專案導出/導入功能
- [ ] 專案合併功能
- [ ] 自動定時備份
- [ ] 雲端同步支援
- [ ] 專案搜尋功能
- [ ] 備份壓縮選項
- [ ] 專案標籤系統

## 總結

AI 助手網站管家提供了完整的專案生命週期管理功能，讓你可以輕鬆管理多個對話網站專案。透過自動備份、版本控制和主題管理，確保你的專案安全可靠且易於維護。

---

**相關文檔**:
- [對話知識提取器文檔](conversation_extractor_zh.md)
- [主題系統文檔](../THEME_AND_COMPOSITION_UPDATE.md)
- [完整功能文檔](../CONVERSATION_EXTRACTOR_FORMAT_UPDATE.md)
