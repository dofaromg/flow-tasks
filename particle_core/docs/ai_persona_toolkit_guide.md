# AI 模組人格通用套件使用說明

## 概述

**MRLiou AI 模組人格通用套件** (`ai_persona_toolkit.py`) 提供完整的 AI 人格管理與檔案壓縮功能：

- **人格連結器 (PersonaConnector)**: 連接、管理與切換多個 AI 人格模組
- **通用 ZIP 處理器 (UniversalZipHandler)**: 支援任意檔案名稱的壓縮/解壓縮（無限制）
- **整合工具包 (AIPersonaToolkit)**: 便捷的統一介面

## 快速開始

### 基本使用

```python
from ai_persona_toolkit import AIPersonaToolkit

# 建立套件實例
toolkit = AIPersonaToolkit()

# 註冊人格
toolkit.connector.register_persona(
    persona_id="my_assistant",
    name="我的助手",
    role=["助手", "翻譯"],
    traits=["友善", "專業"]
)

# 連接並切換人格
toolkit.connector.connect("my_assistant")
toolkit.connector.switch_persona("my_assistant")
```

### ZIP 壓縮/解壓縮

```python
# 壓縮檔案
result = toolkit.zip_handler.compress(
    ["file1.txt", "folder/"],
    output_path="archive.zip"
)

# 解壓縮
result = toolkit.zip_handler.decompress(
    "archive.zip",
    output_dir="extracted/"
)

# 壓縮記憶體資料（支援任意檔名）
data = {
    "中文檔案.txt": "中文內容",
    "special!@#$.json": '{"data": "value"}',
    "路徑/子目錄/file.txt": "nested content"
}
result = toolkit.zip_handler.compress(data)
```

## 人格連結器 API

### PersonaConnector

| 方法 | 說明 |
|------|------|
| `register_persona(persona_id, name, role, ...)` | 註冊新人格 |
| `connect(persona_id)` | 連接到人格 |
| `disconnect(persona_id)` | 斷開連接 |
| `switch_persona(persona_id)` | 切換活動人格 |
| `get_active_persona()` | 獲取當前活動人格 |
| `list_personas()` | 列出所有人格 |
| `send_message(message)` | 向人格發送訊息 |
| `add_hook(event, callback)` | 添加事件鉤子 |
| `load_registry(path)` | 載入人格註冊表 |
| `save_registry(path)` | 儲存人格註冊表 |

### 事件鉤子

支援的事件：
- `on_connect`: 連接時觸發
- `on_disconnect`: 斷開時觸發
- `on_switch`: 切換人格時觸發
- `on_message`: 發送訊息時觸發

```python
def my_hook(persona_id, data):
    print(f"Event for {persona_id}")

toolkit.connector.add_hook("on_connect", my_hook)
```

## ZIP 處理器 API

### UniversalZipHandler

| 方法 | 說明 |
|------|------|
| `compress(source, output_path)` | 壓縮檔案或資料 |
| `decompress(zip_path, output_dir)` | 解壓縮 ZIP 檔案 |
| `list_contents(zip_path)` | 列出 ZIP 內容 |
| `compress_to_memory(source)` | 壓縮至記憶體 (bytes) |
| `decompress_from_memory(zip_data)` | 從記憶體解壓 |
| `compress_to_base64(source)` | 壓縮並轉 Base64 |
| `decompress_from_base64(base64_data)` | 從 Base64 解壓 |

### 壓縮來源格式

支援三種來源格式：

1. **單一路徑** (str): `"path/to/file.txt"` 或 `"path/to/folder/"`
2. **路徑列表** (List[str]): `["file1.txt", "file2.txt", "folder/"]`
3. **資料字典** (Dict[str, bytes|str]): `{"filename.txt": "content"}`

### 無檔案名稱限制

本套件支援任意 Unicode 檔案名稱：

```python
# 中文檔名
data = {"中文測試.txt": "內容"}

# 特殊字元
data = {"file!@#$%^&().txt": "content"}

# 空格和路徑
data = {"my folder/sub folder/file name.txt": "content"}
```

## 互動模式

啟動互動式介面：

```bash
cd particle_core/src
python ai_persona_toolkit.py interactive
```

## 與其他模組整合

### 與記憶封存系統整合

```python
from ai_persona_toolkit import AIPersonaToolkit
from memory_archive_seed import MemoryArchiveSeed

toolkit = AIPersonaToolkit()
archive = MemoryArchiveSeed()

# 創建記憶種子
seed = archive.create_seed({"data": "test"}, seed_name="my_seed")

# 壓縮記憶種子檔案
result = toolkit.zip_handler.compress(
    [seed["seed_file"]],
    "memory_backup.zip"
)
```

### 與人格註冊表整合

```python
# 載入現有人格
toolkit = AIPersonaToolkit(
    registry_path="FlowAgent_Persona_Registry.json"
)

# 列出已載入的人格
for persona in toolkit.connector.list_personas():
    print(f"{persona['id']}: {persona['name']}")
```

## 版本歷史

- **v1.0.0** (2025-11): 初始版本
  - 人格連結器
  - 通用 ZIP 壓縮/解壓縮
  - Base64 支援
  - 互動模式

## 授權

FlowAgent 專用任務系統內部模組
