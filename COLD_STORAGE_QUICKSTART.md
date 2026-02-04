# 冷儲存管理系統 - 快速開始
# Cold Storage Management System - Quick Start

## 什麼是冷儲存系統？

冷儲存系統是一個檔案歸檔和管理工具，用於：
- 🗂️ 將下載和臨時檔案歸檔到冷儲存
- 🔄 保留原始檔案，不刪除
- 🎯 自動去重，節省空間
- 📦 轉換為粒子格式，便於管理
- 📝 保存完整記錄和元數據

## 快速使用

### 1. 查看需要歸檔的檔案

```bash
python particle_core/src/cold_storage_manager.py scan
```

### 2. 歸檔檔案（互動式）

```bash
python scripts/archive_to_cold_storage.py
```

這會：
- ✅ 掃描所有需要歸檔的檔案
- ✅ 顯示檔案列表供確認
- ✅ 歸檔到 `cold_storage/` 目錄
- ✅ 保留原始檔案在原位置
- ✅ 創建重定向檔案
- ✅ 保存詳細記錄到清單

### 3. 查看統計資訊

```bash
python particle_core/src/cold_storage_manager.py stats
```

### 4. 還原檔案（如需要）

```bash
python scripts/restore_from_cold_storage.py
```

## 檔案結構

```
flow-tasks/
├── cold_storage/                      # 冷儲存目錄（自動創建）
│   ├── particles/                     # 粒子檔案
│   ├── redirects/                     # 重定向檔案
│   └── metadata/                      # 元數據
├── cold_storage_manifest.json         # 冷儲存清單（保留此檔案）
└── scripts/
    ├── archive_to_cold_storage.py     # 歸檔工具
    └── restore_from_cold_storage.py   # 還原工具
```

## 哪些檔案會被歸檔？

系統會自動識別：
- 檔名以 `下載` 開頭的檔案
- 檔名以 `點此下載` 開頭的檔案
- `.tmp` 和 `.temp` 臨時檔案
- `temp_` 開頭的檔案

**不會歸檔：**
- `.git` 目錄
- `node_modules` 目錄
- Python 虛擬環境
- 已經在 cold_storage 中的檔案

## 特性

✅ **安全** - 永不刪除原始檔案  
✅ **去重** - 相同內容只存一次  
✅ **可追蹤** - 完整的 SHA-256 校驗碼  
✅ **可還原** - 隨時從冷儲存還原  
✅ **粒子化** - 轉換為粒子語言格式  

## 詳細文檔

查看完整文檔：[docs/COLD_STORAGE_GUIDE.md](./COLD_STORAGE_GUIDE.md)

## Python API 範例

```python
from particle_core.src.cold_storage_manager import ColdStorageManager

# 初始化
manager = ColdStorageManager()

# 掃描檔案
files = manager.scan_files()
print(f"找到 {len(files)} 個檔案")

# 歸檔檔案
results = manager.archive_batch(files, keep_original=True)
print(f"已歸檔: {len(results['archived'])}")

# 查看統計
stats = manager.get_statistics()
print(f"總檔案: {stats['total_archived']}")
print(f"去重率: {stats['deduplication_ratio'] * 100:.2f}%")
```

---

**版本**: v1.0.0  
**作者**: MRLiou / dofaromg
