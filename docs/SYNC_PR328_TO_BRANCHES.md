# 同步 PR #328 (Memory Quick Mount 模組) 到其他分支

本文檔說明如何將 PR #328 中的 Memory Quick Mount (MQM) 模組同步到其他分支 (記憶、宥麟、劉)。

## PR #328 概述

**標題**: Copilot/add memory quick mount module  
**連結**: https://github.com/dofaromg/flow-tasks/pull/328

### 主要變更內容

PR #328 添加了 Memory Quick Mount (MQM) 模組，這是一個用於智能代理的記憶體管理系統：

#### 核心檔案
- `particle_core/src/memory_quick_mount.py` - MQM 主模組 (558 行)
- `particle_core/src/test_memory_quick_mount.py` - 完整測試套件 (495 行)
- `particle_core/docs/memory_quick_mount.md` - 雙語文檔 (687 行)
- `particle_core/config/mqm_config.yaml` - 配置範本
- `particle_core/examples/memory_seed_example.json` - 範例種子檔案

#### 輔助檔案
- `.gitignore` - 新增 MQM 運行時目錄

## 同步步驟

### 方法 1: 使用 Git Cherry-Pick (推薦)

```bash
# 1. 切換到目標分支 (例如：記憶)
git checkout 記憶

# 2. 從 PR #328 分支複製檔案
git checkout origin/copilot/add-memory-quick-mount-module -- \
  particle_core/src/memory_quick_mount.py \
  particle_core/src/test_memory_quick_mount.py \
  particle_core/docs/memory_quick_mount.md \
  particle_core/config/mqm_config.yaml \
  particle_core/examples/memory_seed_example.json

# 3. 更新 .gitignore
# 在 .gitignore 末尾添加以下內容：
cat >> .gitignore << 'EOF'

# Memory Quick Mount (MQM) runtime directories
context/
snapshots/
# Memory Quick Mount - Dynamic files
particle_core/context/
particle_core/snapshots/
particle_core/backups/
particle_core/cache/
/tmp/test_context/
/tmp/test_snapshots/
/tmp/test_cache/
EOF

# 4. 提交變更
git add .
git commit -m "Synchronize Memory Quick Mount module from PR #328

Added Memory Quick Mount (MQM) module for particle-based state management:
- particle_core/src/memory_quick_mount.py - Main MQM module
- particle_core/src/test_memory_quick_mount.py - Comprehensive test suite
- particle_core/docs/memory_quick_mount.md - Documentation
- particle_core/config/mqm_config.yaml - Configuration template
- particle_core/examples/memory_seed_example.json - Example seed file
- Updated .gitignore for MQM runtime directories"

# 5. 推送到遠端
git push origin 記憶
```

### 方法 2: 使用腳本自動同步

使用提供的同步腳本 `scripts/sync_mqm_to_branches.sh`：

```bash
# 同步到所有目標分支
bash scripts/sync_mqm_to_branches.sh

# 或同步到特定分支
bash scripts/sync_mqm_to_branches.sh 記憶
```

## 目標分支

需要同步 MQM 模組到以下分支：

1. **記憶** (Memory) - 記憶體相關功能分支
2. **宥麟** - 個人開發分支
3. **劉** - 個人開發分支

## 驗證步驟

同步完成後，在每個分支上執行以下驗證：

```bash
# 1. 確認檔案存在
ls -la particle_core/src/memory_quick_mount.py
ls -la particle_core/docs/memory_quick_mount.md

# 2. 運行測試
python particle_core/src/test_memory_quick_mount.py

# 3. 檢查文檔
cat particle_core/docs/memory_quick_mount.md | head -50
```

## MQM 模組功能

### 核心功能

1. **粒子級數據壓縮** - 使用符號表示減少數據足跡 (⏰, 👤, ⚡, 📦等)
2. **記憶種子掛載** - 將配置/上下文種子載入運行時
3. **代理狀態快照** - 在任意時間點保存代理執行狀態
4. **狀態再水化** - 從快照恢復代理到先前狀態
5. **緩存集成** - 可選的基於磁碟的緩存以快速訪問

### 主要組件

1. **ParticleCompressor** - 使用粒子符號的基本壓縮
2. **AdvancedParticleCompressor** - 嵌套結構的遞歸壓縮
3. **MemoryQuickMounter** - 管理種子、快照和再水化的主類

### 特性

- 雙語支持（英文/繁體中文）
- JSON/YAML 配置檔案
- CLI 接口，支援 mount/snapshot/rehydrate 命令
- 離線操作（無需外部 API）

## 配置示例

### mqm_config.yaml

```yaml
mqm:
  context_dir: "context"
  snapshot_dir: "snapshots"
  cache_dir: "cache"
  seed_mount_paths:
    - "particle_core/examples/memory_seed_example.json"
```

### memory_seed_example.json

```json
{
  "seed_name": "example_agent_state",
  "timestamp": "2026-02-01T10:00:00Z",
  "agent_context": {
    "current_task": "Process user query",
    "memory": {
      "short_term": [],
      "long_term": []
    }
  }
}
```

## 注意事項

1. 確保在同步前備份目標分支
2. 如果目標分支已有衝突的檔案，請先解決衝突
3. 同步後建議運行完整測試套件
4. 更新後需要重新安裝依賴（如果有新依賴）

## 疑難排解

### 問題：檔案已存在

```bash
# 解決方案：強制覆蓋
git checkout --force origin/copilot/add-memory-quick-mount-module -- particle_core/src/memory_quick_mount.py
```

### 問題：分支衝突

```bash
# 解決方案：創建新的同步分支
git checkout -b sync-mqm-記憶 origin/記憶
# 然後按照正常步驟操作
```

### 問題：推送被拒絕

```bash
# 解決方案：先拉取最新變更
git pull origin 記憶 --rebase
git push origin 記憶
```

## 相關資源

- [PR #328](https://github.com/dofaromg/flow-tasks/pull/328)
- [Memory Quick Mount 文檔](../particle_core/docs/memory_quick_mount.md)
- [Particle Core README](../particle_core/README.md)

## 更新歷史

- 2026-02-01: 創建同步文檔
- 2026-02-01: PR #328 Memory Quick Mount 模組添加
