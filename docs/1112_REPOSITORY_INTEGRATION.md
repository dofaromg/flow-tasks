# 1112 Repository Integration
# 1112 倉庫整合說明

## Overview / 概述

The 1112 repository has been added to the repository synchronization configuration in `repos_sync.yaml`. This allows automatic syncing of files from the 1112 repository to this project.

1112 倉庫已新增至 `repos_sync.yaml` 的倉庫同步配置中。這允許從 1112 倉庫自動同步檔案到此專案。

## Current Status / 當前狀態

- **Repository URL**: `https://github.com/dofaromg/1112.git`
- **Status**: Disabled (repository is currently empty)
- **Default Branch**: `main`

- **倉庫網址**: `https://github.com/dofaromg/1112.git`
- **狀態**: 停用（倉庫目前為空）
- **預設分支**: `main`

## Configuration / 配置

The 1112 repository is configured to sync the following files when enabled:

當啟用時，1112 倉庫將同步以下檔案：

### Files / 檔案
- `README.md` → `examples/synced_files/1112_readme.md`

### Directories / 目錄
- `src/` → `lib/1112/`
  - Excludes: `*.pyc`, `__pycache__`, `*.egg-info`, `node_modules`

## How to Enable / 如何啟用

Once the 1112 repository has content, follow these steps to enable syncing:

一旦 1112 倉庫有內容，請遵循以下步驟來啟用同步：

1. **Edit the configuration file** / **編輯配置檔案**:
   ```bash
   vim repos_sync.yaml
   ```

2. **Change the `enabled` field** / **變更 `enabled` 欄位**:
   ```yaml
   - name: "repository-1112"
     url: "https://github.com/dofaromg/1112.git"
     branch: "main"
     enabled: true  # Change from false to true / 從 false 改為 true
   ```

3. **Run the sync script** / **執行同步腳本**:
   ```bash
   python scripts/sync_external_repos.py
   ```

4. **Or use the convenience command** / **或使用便捷命令**:
   ```bash
   python scripts/sync_external_repos.py --repo repository-1112
   ```

## Testing / 測試

To test the configuration without actually syncing:

若要測試配置而不實際同步：

```bash
# List all configured repositories / 列出所有配置的倉庫
python scripts/sync_external_repos.py --list

# Check repository stability / 檢查倉庫穩定性
python scripts/check_repo_stability.py
```

## Customization / 自訂

You can customize the sync configuration by editing the `repository-1112` entry in `repos_sync.yaml`:

您可以透過編輯 `repos_sync.yaml` 中的 `repository-1112` 項目來自訂同步配置：

- **Change destination paths** / **變更目標路徑**: Modify `dest` fields in `files` and `directories`
- **Add more files** / **新增更多檔案**: Add entries to the `files` list
- **Add more directories** / **新增更多目錄**: Add entries to the `directories` list
- **Modify exclusion patterns** / **修改排除模式**: Update the `exclude` list

## Troubleshooting / 疑難排解

If sync fails:

如果同步失敗：

1. **Verify repository is not empty** / **確認倉庫不是空的**:
   ```bash
   git ls-remote https://github.com/dofaromg/1112.git
   ```

2. **Check network connectivity** / **檢查網路連線**:
   ```bash
   curl -I https://github.com/dofaromg/1112.git
   ```

3. **Review sync logs** / **檢視同步日誌**:
   ```bash
   python scripts/sync_external_repos.py --verbose
   ```

4. **Ensure proper permissions** / **確保有適當的權限**:
   - The repository must be publicly accessible, or
   - You must have proper authentication configured
   
   - 倉庫必須可公開存取，或
   - 您必須配置適當的身份驗證

## Related Files / 相關檔案

- `repos_sync.yaml` - Main synchronization configuration / 主要同步配置
- `repos_sync.example.yaml` - Example configuration template / 範例配置模板
- `scripts/sync_external_repos.py` - Sync script / 同步腳本
- `scripts/check_repo_stability.py` - Stability checker / 穩定性檢查器
- `docs/EXTERNAL_REPO_SYNC.md` - General sync documentation / 通用同步文件

## GitHub Actions Integration / GitHub Actions 整合

The repository sync can also be automated via GitHub Actions workflow:

倉庫同步也可以透過 GitHub Actions 工作流程自動化：

- Workflow file: `.github/workflows/sync-external-repos.yml`
- Trigger: Manual dispatch or scheduled
- 工作流程檔案: `.github/workflows/sync-external-repos.yml`
- 觸發: 手動調度或排程

## Notes / 注意事項

- The repository is currently empty and disabled by default
- Enable only when the 1112 repository contains content
- Review synced files before committing them to the main branch
- Consider using `.gitignore` to exclude certain synced files if needed

- 倉庫目前為空且預設為停用狀態
- 僅在 1112 倉庫包含內容時才啟用
- 在將同步的檔案提交至主分支之前請先檢視
- 如需要，考慮使用 `.gitignore` 排除某些同步的檔案
