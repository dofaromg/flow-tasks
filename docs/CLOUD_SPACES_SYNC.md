# 多雲空間同步系統 / Multi-Cloud Space Sync System

## 概述 / Overview

多雲空間同步系統整合粒子地球儀記憶法，實現跨雲端環境的智能同步與通道升級。

Multi-cloud space synchronization system with particle globe memory integration for intelligent sync across cloud environments and channel upgrades.

## 功能特性 / Features

### 核心功能 / Core Features

- 🌍 **粒子地球儀記憶法** / Particle Globe Memory Method
  - 自動創建記憶檢查點
  - SHA-256 完整性驗證
  - 狀態快照與還原
  
- ☁️ **多雲空間支援** / Multi-Cloud Space Support
  - 生產環境 (Production)
  - 預備環境 (Staging)
  - 沙盒環境 (Sandbox) ✨
  - 開發環境 (Development)
  - 本地環境 (Local)

- 🔼 **通道升級** / Channel Upgrades
  - 漸進式發布 (Progressive Rollout)
  - 藍綠部署 (Blue-Green Deployment)
  - 金絲雀發布 (Canary Deployment)
  - 自動回滾 (Auto Rollback)

- 🔄 **智能同步** / Intelligent Sync
  - 並行同步支援
  - 自動重試機制
  - 完整性驗證
  - 備份保護

## 快速開始 / Quick Start

### 1. 安裝依賴 / Install Dependencies

```bash
# 確保已安裝 particle_core 依賴
pip install -r particle_core/requirements.txt
```

### 2. 列出雲空間 / List Cloud Spaces

```bash
# 查看所有配置的雲空間
python scripts/sync_cloud_spaces.py --list
```

輸出範例 / Example Output:
```
🌐 Configured Cloud Spaces:
======================================================================

✅ production
   類型 / Type: gke
   集群 / Cluster: modular-cluster
   區域 / Region: asia-east1
   同步路徑數 / Sync paths: 2

✅ sandbox
   類型 / Type: local
   描述 / Description: 本地沙盒環境用於測試
   同步路徑數 / Sync paths: 2
```

### 3. 同步所有雲空間 / Sync All Cloud Spaces

```bash
# 執行完整同步（包含通道升級）
python scripts/sync_cloud_spaces.py
```

特點 / Features:
- ✅ 自動創建粒子地球儀記憶檢查點
- ✅ 執行通道升級策略
- ✅ 生成完整性校驗碼
- ✅ 支援自動回滾

### 4. 同步特定雲空間 / Sync Specific Cloud Space

```bash
# 只同步沙盒環境
python scripts/sync_cloud_spaces.py --space sandbox

# 只同步生產環境
python scripts/sync_cloud_spaces.py --space production
```

### 5. 查看記憶檢查點 / View Memory Checkpoints

```bash
# 顯示粒子地球儀記憶檢查點
python scripts/sync_cloud_spaces.py --memory
```

輸出範例 / Example Output:
```
🌍 Particle Globe Memory Checkpoints:
======================================================================

📍 cloud_sync_production_20260126_071219.json
   時間 / Time: 2026-01-26T07:12:19.430576
   校驗碼 / Checksum: ae3212a62d902928...

📍 cloud_sync_sandbox_20260126_071219.json
   時間 / Time: 2026-01-26T07:12:19.440737
   校驗碼 / Checksum: e869399c28b1ff4a...
```

## 配置說明 / Configuration

### 雲空間配置 / Cloud Space Configuration

配置檔案: `cloud_spaces_sync.yaml`

```yaml
version: "1.0"

# 粒子地球儀記憶配置
particle_globe_memory:
  enabled: true
  memory_archive_path: ".cloud_sync_memory"
  checkpoint_frequency: "每次同步 / every sync"
  retention_days: 30

# 雲空間定義
cloud_spaces:
  - name: "production"
    type: "gke"
    enabled: true
    cluster_name: "modular-cluster"
    region: "asia-east1"
    zone: "asia-east1-a"
    namespace: "flowagent"
    sync_paths:
      - src: "cluster/overlays/prod"
        dest: "deployed/prod"
      - src: "apps/"
        dest: "deployed/apps"
  
  - name: "sandbox"
    type: "local"
    enabled: true
    description: "本地沙盒環境用於測試"
    sync_paths:
      - src: "particle_core/"
        dest: "sandbox/particle_core"
      - src: "examples/"
        dest: "sandbox/examples"

# 通道升級配置
channel_upgrades:
  enabled: true
  upgrade_strategies:
    - progressive_rollout  # 漸進式發布
    - blue_green          # 藍綠部署
    - canary              # 金絲雀發布
  auto_rollback: true
  health_check_timeout: 300

# 同步設定
sync_settings:
  parallel_sync: true
  max_workers: 4
  retry_attempts: 3
  backup_before_sync: true
  verify_integrity: true
```

## 粒子地球儀記憶法 / Particle Globe Memory Method

### 什麼是粒子地球儀記憶法？

粒子地球儀記憶法是一種基於粒子語言核心系統的狀態封存與還原技術：

1. **記憶檢查點** / Memory Checkpoints
   - 每次同步自動創建狀態快照
   - 記錄完整的同步數據和雲空間狀態
   - 使用 SHA-256 確保數據完整性

2. **多層記憶結構** / Multi-Layer Memory Structure
   - Structure（結構層）：基礎資料結構
   - Mark（標記層）：邏輯跳點與標記
   - Flow（流程層）：執行流程
   - Recurse（遞歸層）：細部展開
   - Store（封存層）：最終封存狀態

3. **智能還原** / Intelligent Restoration
   - 支援回滾到任意檢查點
   - 自動驗證數據完整性
   - 保留歷史記錄供查詢

### 記憶檢查點結構 / Checkpoint Structure

```json
{
  "seed_name": "cloud_sync_production_20260126_071219",
  "version": "1.0",
  "created_at": "2026-01-26T07:12:19.430576",
  "particle_data": {
    "space_name": "production",
    "sync_timestamp": "2026-01-26T07:12:19.430576",
    "sync_data": {
      "paths_synced": 2,
      "total_paths": 2,
      "success": true
    },
    "cloud_space_state": {
      "name": "production",
      "type": "gke",
      "enabled": true
    }
  },
  "checksum": "ae3212a62d902928...",
  "metadata": {
    "type": "cloud_sync_checkpoint",
    "space": "production",
    "globe_memory_enabled": true
  }
}
```

## 通道升級策略 / Channel Upgrade Strategies

### 1. 漸進式發布 / Progressive Rollout
逐步將新版本推送到更多節點，可隨時暫停或回滾。

Gradually roll out new versions to more nodes, with ability to pause or rollback.

### 2. 藍綠部署 / Blue-Green Deployment
維護兩個相同的生產環境，切換時零停機時間。

Maintain two identical production environments for zero-downtime switching.

### 3. 金絲雀發布 / Canary Deployment
先向少量用戶發布新版本，監控後再擴大範圍。

Release to a small subset of users first, monitor, then expand.

## 沙盒環境 / Sandbox Environment

沙盒環境是一個隔離的測試空間，用於：

The sandbox environment is an isolated testing space for:

- 📝 測試新的同步配置 / Testing new sync configurations
- 🧪 驗證粒子核心功能 / Validating particle core features
- 🔬 實驗性功能開發 / Experimental feature development
- 🛡️ 安全測試 / Security testing

### 沙盒同步示例 / Sandbox Sync Example

```bash
# 只同步到沙盒環境
python scripts/sync_cloud_spaces.py --space sandbox

# 查看沙盒內容
ls -la sandbox/
```

## 故障排除 / Troubleshooting

### 問題：粒子記憶系統未啟用

**錯誤訊息:**
```
⚠️  粒子記憶系統未載入，使用基本同步模式
⚠️  Particle memory system not loaded, using basic sync mode
```

**解決方案:**
```bash
# 安裝 particle_core 依賴
pip install -r particle_core/requirements.txt

# 確認 memory_archive_seed.py 存在
ls particle_core/src/memory_archive_seed.py
```

### 問題：同步路徑不存在

**錯誤訊息:**
```
⚠️  來源不存在 / Source not found
```

**解決方案:**
檢查配置檔案中的路徑是否正確，確保來源目錄存在。

### 問題：權限錯誤

確保腳本有執行權限：
```bash
chmod +x scripts/sync_cloud_spaces.py
```

## 整合 / Integration

### 與 GitHub Actions 整合

創建 `.github/workflows/sync-cloud-spaces.yml`:

```yaml
name: Sync Cloud Spaces

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # 每日執行
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r particle_core/requirements.txt
      
      - name: Sync all cloud spaces
        run: python scripts/sync_cloud_spaces.py
      
      - name: Show memory checkpoints
        run: python scripts/sync_cloud_spaces.py --memory
```

### 與 Kubernetes 整合

在實際部署中，可以使用 `kubectl` 命令同步到 GKE：

```bash
# 獲取集群憑證
gcloud container clusters get-credentials modular-cluster \
  --zone asia-east1-a

# 應用配置
kubectl apply -k cluster/overlays/prod/
```

## 高級用法 / Advanced Usage

### 自訂配置檔案

```bash
# 使用自訂配置
python scripts/sync_cloud_spaces.py --config my_config.yaml
```

### 程式化使用

```python
from sync_cloud_spaces import CloudSpaceSyncManager

# 初始化管理器
manager = CloudSpaceSyncManager("cloud_spaces_sync.yaml")

# 列出所有雲空間
manager.list_cloud_spaces()

# 同步特定空間
manager.sync_specific_space("sandbox")

# 同步所有空間
manager.sync_all_spaces()

# 查看記憶檢查點
manager.show_memory_checkpoints()
```

## 最佳實踐 / Best Practices

1. **定期備份** / Regular Backups
   - 保留至少 30 天的記憶檢查點
   - 定期驗證檢查點完整性

2. **測試優先** / Test First
   - 先在沙盒環境測試
   - 驗證通過後再部署到生產環境

3. **監控** / Monitoring
   - 監控同步狀態和錯誤
   - 設置告警通知

4. **文檔記錄** / Documentation
   - 記錄每次重要的通道升級
   - 保存配置變更歷史

## 支援 / Support

如有問題或建議，請建立 GitHub Issue。

For issues or suggestions, please create a GitHub Issue.

---

最後更新 / Last Updated: 2026-01-26
版本 / Version: 1.0.0
