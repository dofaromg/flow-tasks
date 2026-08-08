# 外部倉庫同步快速參考 / External Repo Sync Quick Reference

## 一分鐘快速開始 / 1-Minute Quick Start

```bash
# 1. 複製範例配置 / Copy example config
cp repos_sync.example.yaml repos_sync.yaml

# 2. 編輯配置 (取消註解並修改 URL) / Edit config (uncomment and modify URL)
vim repos_sync.yaml

# 3. 測試配置 / Test configuration
python scripts/sync_external_repos.py --list

# 4. 執行同步 / Run sync
python scripts/sync_external_repos.py
```

## 常用命令 / Common Commands

```bash
# 列出所有配置的倉庫 / List all configured repositories
python scripts/sync_external_repos.py --list

# 同步所有倉庫 / Sync all repositories
python scripts/sync_external_repos.py

# 同步特定倉庫 / Sync specific repository
python scripts/sync_external_repos.py --repo repo-name

# 使用自訂配置檔案 / Use custom config file
python scripts/sync_external_repos.py --config my-config.yaml

# 顯示幫助 / Show help
python scripts/sync_external_repos.py --help
```

## 配置範本 / Config Template

```yaml
repositories:
  - name: "my-repo"
    url: "https://github.com/user/repo.git"
    branch: "main"
    enabled: true
    files:
      - src: "path/in/source/repo.txt"
        dest: "path/in/this/repo.txt"
```

## GitHub Actions 使用 / GitHub Actions Usage

1. 前往: `Actions` → `Sync External Repositories`
2. 點擊: `Run workflow`
3. （可選）輸入倉庫名稱
4. 點擊: 綠色的 `Run workflow` 按鈕

## 衝突策略 / Conflict Strategies

| 策略 / Strategy | 說明 / Description |
|----------------|-------------------|
| `skip` | 跳過已存在的檔案 / Skip existing files |
| `overwrite` | 覆寫已存在的檔案 (會備份) / Overwrite with backup |
| `prompt` | 每次詢問 / Ask each time |

## 檔案位置 / File Locations

- 📄 配置檔案 / Config: `repos_sync.yaml`
- 📜 同步腳本 / Script: `scripts/sync_external_repos.py`
- 📦 備份目錄 / Backups: `.sync_backups/`
- 📚 完整文檔 / Full docs: `docs/EXTERNAL_REPO_SYNC.md`
- 📖 範例 / Examples: `docs/REPO_SYNC_EXAMPLES.md`

## 需要幫助？ / Need Help?

1. 查看文檔: `docs/EXTERNAL_REPO_SYNC.md`
2. 查看範例: `docs/REPO_SYNC_EXAMPLES.md`
3. 執行: `python scripts/sync_external_repos.py --help`
4. 建立 GitHub Issue

---

💡 **提示** / Tip: 先在測試配置中驗證，再部署到生產環境
