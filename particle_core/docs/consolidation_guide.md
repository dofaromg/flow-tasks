# 記憶種子合併工具使用指南

## 📖 簡介

記憶種子合併工具（Memory Seeds Consolidation Tool）是一個自動化工具，用於將多個記憶種子合併為指定數量的種子，有效管理和優化記憶儲存空間。

## 🎯 使用場景

- 當記憶種子數量過多時，合併為較少的種子以便管理
- 整合相關的記憶種子為單一記憶單元
- 優化儲存空間和查詢效率
- 準備記憶備份或匯出

## 🚀 快速開始

### 1. 創建範例種子（測試用）

如果您想要測試合併功能，可以先創建一些範例種子：

```bash
cd particle_core/src

# 創建 25 個範例種子
python create_sample_seeds.py --count 25

# 創建指定數量的種子
python create_sample_seeds.py --count 50
```

### 2. 列出現有種子

```bash
# 查看所有記憶種子
python consolidate_memory_seeds.py --list
```

### 3. 模擬合併（不實際執行）

在實際合併前，建議先使用 `--dry-run` 模式查看合併計劃：

```bash
# 模擬合併至 10 個種子
python consolidate_memory_seeds.py --target 10 --dry-run

# 使用不同策略模擬
python consolidate_memory_seeds.py --target 10 --strategy by_date --dry-run
```

### 4. 執行合併

確認合併計劃後，執行實際合併：

```bash
# 合併至 10 個種子（預設）
python consolidate_memory_seeds.py --target 10

# 合併至指定數量
python consolidate_memory_seeds.py --target 5

# 使用特定策略
python consolidate_memory_seeds.py --target 10 --strategy by_date
```

## 📋 命令參數說明

### 基本參數

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--target N` | 目標種子數量 | 10 |
| `--strategy` | 合併策略 | auto |
| `--storage PATH` | 種子儲存路徑 | memory_seeds |
| `--dry-run` | 只模擬不實際執行 | - |
| `--list` | 列出所有種子 | - |
| `--cleanup` | 清理舊種子（需輸入 DELETE 確認） | - |
| `--force-cleanup` | 強制清理舊種子（危險！） | - |

### 合併策略

- **auto**: 自動策略，按創建時間智能分組
- **by_date**: 按日期排序，時間相近的種子合併在一起
- **by_size**: 按大小排序，大小相近的種子合併在一起
- **even**: 平均分配，盡可能讓每組種子數量相近

## 📚 使用範例

### 範例 1: 基本合併流程

```bash
# 步驟 1: 創建測試種子
python create_sample_seeds.py --count 25

# 步驟 2: 查看當前種子
python consolidate_memory_seeds.py --list

# 步驟 3: 模擬合併
python consolidate_memory_seeds.py --target 10 --dry-run

# 步驟 4: 執行合併
python consolidate_memory_seeds.py --target 10
```

### 範例 2: 使用不同合併策略

```bash
# 按日期合併
python consolidate_memory_seeds.py --target 10 --strategy by_date

# 平均分配合併
python consolidate_memory_seeds.py --target 10 --strategy even
```

### 範例 3: 自訂儲存路徑

```bash
# 指定自訂路徑
python consolidate_memory_seeds.py --target 10 --storage /path/to/custom/seeds
```

### 範例 4: 清理原始種子（驗證後）

合併完成並驗證無誤後，可以清理原始種子以釋放空間：

```bash
# 清理原始種子（需要輸入 DELETE 確認）
python consolidate_memory_seeds.py --cleanup

# 強制清理（跳過確認，請謹慎使用）
python consolidate_memory_seeds.py --cleanup --force-cleanup
```

**重要提醒**：
- 清理操作會永久刪除原始種子
- 建議先備份重要資料
- 需要輸入 'DELETE' 進行確認
- 清理後無法復原

```python
from consolidate_memory_seeds import MemorySeedConsolidator

# 創建合併器
consolidator = MemorySeedConsolidator("memory_seeds")

# 查看所有種子
seeds = consolidator.get_all_seeds()
print(f"當前有 {len(seeds)} 個種子")

# 執行合併
result = consolidator.consolidate_to_target(
    target_count=10,
    strategy="auto",
    dry_run=False
)

print(f"合併完成: {result['final_count']} 個種子")
```

## 🔍 輸出說明

### 合併過程輸出

```
============================================================
記憶種子合併工具 - Memory Seeds Consolidation
============================================================

📊 當前種子數量: 25
🎯 目標種子數量: 10
📋 合併策略: auto
🔍 模擬模式: 否

🔄 需要減少 15 個種子

📦 合併計劃:
   組 1: 3 個種子 → 合併為 1 個
      - sample_seed_001
      - sample_seed_002
      - sample_seed_003
   組 2: 3 個種子 → 合併為 1 個
      - sample_seed_004
      - sample_seed_005
      - sample_seed_006
   ...

🚀 開始合併...

合併組 1...
  ✅ 已合併為: consolidated_01_20250711_143022
合併組 2...
  ✅ 已合併為: consolidated_02_20250711_143023
...

✅ 合併完成！
   原始數量: 25
   最終數量: 10
```

### 合併結果結構

```python
{
    "status": "success",
    "original_count": 25,
    "final_count": 10,
    "target_count": 10,
    "merged_seeds": [
        {
            "seed_name": "consolidated_01_...",
            "seed_file": "memory_seeds/consolidated_01_....mseed.json",
            "checksum": "...",
            "created_at": "..."
        },
        # ... 其他 9 個合併後的種子
    ]
}
```

## ⚠️ 注意事項

### 安全性

1. **備份重要資料**: 合併前建議先備份重要的記憶種子
2. **使用 --dry-run**: 先用模擬模式查看合併計劃
3. **驗證結果**: 合併後驗證資料完整性
4. **保留原始**: 預設不刪除原始種子，合併後會同時保留原始和合併後的種子
   - 合併 25 個種子至 10 個後，會有 35 個種子（25 原始 + 10 合併）
   - 驗證合併成功後，可使用 `--cleanup` 清理原始種子
5. **謹慎清理**: `--cleanup` 功能需要謹慎使用，建議手動備份後再執行

### 最佳實踐

1. **分批合併**: 大量種子建議分批合併
2. **定期維護**: 定期執行合併以保持種子數量適當
3. **選擇策略**: 根據資料特性選擇合適的合併策略
4. **記錄日誌**: 保留合併操作的記錄

### 限制

- 合併操作不可逆，合併後的種子無法自動拆分
- `--cleanup` 功能需要謹慎使用，建議手動備份後再執行
- 大量種子合併可能需要較長時間

## 🔧 故障排除

### 問題 1: 找不到種子

**錯誤訊息**: `FileNotFoundError: 記憶種子不存在`

**解決方法**:
- 確認種子路徑是否正確
- 使用 `--list` 查看可用的種子
- 檢查種子名稱是否正確

### 問題 2: 權限錯誤

**錯誤訊息**: `PermissionError`

**解決方法**:
- 確認對儲存目錄有讀寫權限
- 檢查檔案是否被其他程式佔用

### 問題 3: 記憶體不足

**解決方法**:
- 減少目標種子數量，分批合併
- 關閉其他佔用記憶體的程式
- 使用較小的種子進行合併

## 📞 獲取幫助

```bash
# 查看幫助資訊
python consolidate_memory_seeds.py --help

# 查看範例種子創建工具幫助
python create_sample_seeds.py --help
```

## 🎓 進階使用

### 自訂合併邏輯

您可以擴展 `MemorySeedConsolidator` 類別來實現自訂的合併邏輯：

```python
from consolidate_memory_seeds import MemorySeedConsolidator

class CustomConsolidator(MemorySeedConsolidator):
    def _create_merge_groups(self, seeds, target_count, strategy):
        # 實現您的自訂分組邏輯
        if strategy == "my_custom_strategy":
            # 自訂策略實作
            pass
        return super()._create_merge_groups(seeds, target_count, strategy)

# 使用自訂合併器
consolidator = CustomConsolidator()
result = consolidator.consolidate_to_target(
    target_count=10,
    strategy="my_custom_strategy"
)
```

### 與 CI/CD 整合

可以將合併工具整合到自動化流程中：

```yaml
# GitHub Actions 範例
- name: Consolidate Memory Seeds
  run: |
    cd particle_core/src
    python consolidate_memory_seeds.py --target 10
```

## 📊 效能指標

| 操作 | 25 個種子 → 10 個 | 100 個種子 → 10 個 |
|------|-------------------|---------------------|
| 模擬時間 | < 1 秒 | < 2 秒 |
| 合併時間 | 2-3 秒 | 8-10 秒 |
| 記憶體使用 | < 50 MB | < 200 MB |

## 🔗 相關文檔

- [記憶封存種子快速入門](../../記憶封存種子快速入門.md)
- [記憶封存種子系統說明](../docs/記憶封存種子說明.md)
- [本地執行說明](../docs/本地執行說明.md)

---

**專案**: FlowAgent.Runtime  
**工具**: 記憶種子合併工具 v1.0  
**作者**: MRLiou / dofaromg  
**更新**: 2025-12-11
