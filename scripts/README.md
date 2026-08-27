# Scripts Directory / 腳本目錄

This directory contains utility scripts for the FlowAgent project.

本目錄包含 FlowAgent 專案的實用腳本。

## Git Utilities / Git 工具

### git-push-helper.sh

A helper script for pushing changes to origin with proper validation.

一個用於將變更推送到遠端的輔助腳本，具有適當的驗證功能。

**Usage / 使用方法:**

```bash
# Push current branch to origin
./scripts/git-push-helper.sh

# Push a specific branch to origin
./scripts/git-push-helper.sh <branch-name>
```

**Features / 功能:**
- ✅ Validates no uncommitted changes exist / 驗證沒有未提交的變更
- ✅ Checks if target branch exists / 檢查目標分支是否存在
- ✅ Compares local and remote branch status / 比較本地和遠端分支狀態
- ✅ Only pushes if changes exist / 僅在有變更時推送
- ✅ Colored output for better readability / 彩色輸出以提高可讀性

**Example Output / 輸出範例:**

```
=== Git Push Helper ===
Target branch: main

Fetching remote status...
✓ Branch is up to date with origin
Nothing to push

Done!
```

## Deployment Scripts / 部署腳本

### oneclick_gke_init.sh

One-click GKE initialization script.

一鍵式 GKE 初始化腳本。

### validate_deployment.sh

Validates deployment configuration.

驗證部署配置。

## Codespace Management / Codespace 管理

### monitor-codespaces.sh

Monitors GitHub Codespaces status.

監控 GitHub Codespaces 狀態。

### check-codespace-retention.sh

Checks Codespace retention policies.

檢查 Codespace 保留策略。

## Sync & Integration / 同步與整合

### sync_external_repos.py

Synchronizes files from external repositories.

從外部倉庫同步檔案。

See: [External Repo Sync Guide](../docs/EXTERNAL_REPO_SYNC.md)

參見: [外部倉庫同步指南](../docs/EXTERNAL_REPO_SYNC.md)

### ping-sync.ts

TypeScript sync utility.

TypeScript 同步工具。

## Quality & Performance / 品質與效能

### check_code_quality.py

Checks code quality metrics.

檢查程式碼品質指標。

### benchmark_performance.py

Benchmarks system performance.

基準測試系統效能。

## Branch Management / 分支管理

### validate_branch_integration.sh

Validates branch integration.

驗證分支整合。

## Publishing / 發布

### publish_decompression_dll.sh

Publishes decompression DLL.

發布解壓縮 DLL。

---

## Contributing / 貢獻

When adding new scripts, please:
- Make them executable: `chmod +x script-name.sh`
- Add documentation in this README
- Include usage examples
- Add bilingual descriptions (English & Traditional Chinese)

添加新腳本時，請：
- 使其可執行：`chmod +x script-name.sh`
- 在此 README 中添加文檔
- 包含使用範例
- 添加雙語說明（英文和繁體中文）
