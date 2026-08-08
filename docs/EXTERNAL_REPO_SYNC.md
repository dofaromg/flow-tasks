# 外部倉庫檔案同步系統 / External Repository File Sync System

## 概述 / Overview

這個系統允許你從其他 GitHub 倉庫自動拉取特定的檔案和目錄到本地倉庫。支援多種同步模式和衝突處理策略。

This system allows you to automatically pull specific files and directories from other GitHub repositories into your local repository. It supports multiple sync modes and conflict resolution strategies.

## 功能特性 / Features

- ✅ **選擇性檔案同步** / Selective file synchronization
- ✅ **目錄同步** / Directory synchronization  
- ✅ **Git Submodule 支援** / Git Submodule support
- ✅ **自動備份** / Automatic backup
- ✅ **檔案完整性驗證** / File integrity verification
- ✅ **排除模式** / Exclude patterns
- ✅ **衝突處理策略** / Conflict resolution strategies
- ✅ **倉庫穩定性檢查** / Repository stability checking
- ✅ **GitHub Actions 自動化** / GitHub Actions automation
- ✅ **雙語支援** / Bilingual support (中文/English)

## 快速開始 / Quick Start

### 1. 配置要同步的倉庫 / Configure Repositories

編輯 `repos_sync.yaml` 檔案，添加你要同步的倉庫：

```yaml
repositories:
  - name: "my-shared-library"
    url: "https://github.com/username/shared-library.git"
    branch: "main"
    enabled: true
    files:
      - src: "utils/helper.py"
        dest: "scripts/imported_helper.py"
```

### 2. 檢查倉庫穩定性 / Check Repository Stability

在同步之前，建議先檢查倉庫的可訪問性和穩定性：

Before syncing, it's recommended to check repository accessibility and stability:

```bash
# 檢查所有配置的倉庫 / Check all configured repositories
python scripts/check_repo_stability.py

# 生成詳細報告 / Generate detailed report
python scripts/check_repo_stability.py --report

# 指定自訂報告檔名 / Specify custom report filename
python scripts/check_repo_stability.py --report --output my_report.md
```

### 3. 手動執行同步 / Run Sync Manually

```bash
# 同步所有倉庫 / Sync all repositories
python scripts/sync_external_repos.py

# 同步特定倉庫 / Sync specific repository
python scripts/sync_external_repos.py --repo my-shared-library

# 列出所有配置的倉庫 / List all configured repositories
python scripts/sync_external_repos.py --list
```

### 4. 使用 GitHub Actions 自動同步 / Use GitHub Actions

系統會在以下情況自動執行同步：

- 📅 每週一 UTC 00:00 定時執行 / Weekly on Monday at 00:00 UTC
- 🔧 當 `repos_sync.yaml` 配置檔案變更時 / When `repos_sync.yaml` changes
- 👆 手動觸發（在 GitHub Actions 頁面） / Manual trigger (in GitHub Actions page)

## 配置說明 / Configuration Guide

詳細配置說明請參考 `repos_sync.yaml` 檔案中的註解。

For detailed configuration, refer to comments in `repos_sync.yaml` file.

## 倉庫穩定性檢查 / Repository Stability Check

穩定性檢查工具可以幫助你在同步之前驗證所有配置的倉庫是否可訪問和健康。

The stability checker helps you verify that all configured repositories are accessible and healthy before syncing.

### 檢查內容 / What It Checks

- 🔗 **網路連線** / Network connectivity
- 📡 **倉庫可訪問性** / Repository accessibility
- 🌿 **分支存在性** / Branch existence
- ⏱️ **回應時間** / Response time
- 🔢 **分支數量** / Number of branches

### 使用方式 / Usage

```bash
# 基本檢查 / Basic check
python scripts/check_repo_stability.py

# 生成詳細報告 / Generate detailed report
python scripts/check_repo_stability.py --report

# 使用自訂配置檔案 / Use custom config file
python scripts/check_repo_stability.py --config my_config.yaml
```

### 狀態說明 / Status Descriptions

- ✅ **healthy** - 倉庫可訪問且分支存在 / Repository accessible and branch exists
- ⏸️ **disabled** - 配置中已停用 / Disabled in configuration
- ❌ **unreachable** - 無法訪問倉庫 / Cannot access repository
- ⚠️ **branch_missing** - 倉庫可訪問但分支不存在 / Repository accessible but branch missing
- 🔥 **error** - 檢查過程中發生錯誤 / Error occurred during check

## 支援 / Support

如有問題或建議，請建立 GitHub Issue。

For issues or suggestions, please create a GitHub Issue.

---

最後更新 / Last Updated: 2024-12-19
