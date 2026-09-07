# 🔄 外部倉庫檔案同步功能 / External Repository File Sync Feature

## 這是什麼？ / What is This?

一個強大的自動化工具，讓你可以從其他 GitHub 倉庫自動拉取特定的檔案和目錄到本地倉庫。

A powerful automation tool that allows you to automatically pull specific files and directories from other GitHub repositories into your local repository.

## ✨ 為什麼需要這個功能？ / Why Do You Need This?

### 常見使用場景 / Common Use Cases

1. **共享程式碼庫** / Shared Code Libraries
   - 從公司的工具庫同步常用函數
   - Sync utility functions from company libraries

2. **配置模板** / Configuration Templates
   - 保持多個專案的配置檔案同步
   - Keep config files in sync across multiple projects

3. **文檔同步** / Documentation Sync
   - 自動更新共享的文檔檔案
   - Automatically update shared documentation

4. **依賴管理** / Dependency Management
   - 整合外部組件而不需要完整複製
   - Integrate external components without full duplication

## 🚀 快速開始 / Quick Start

### 5 分鐘上手 / 5-Minute Setup

```bash
# 1️⃣ 複製範例配置
cp repos_sync.example.yaml repos_sync.yaml

# 2️⃣ 編輯配置檔案
vim repos_sync.yaml
# 取消註解並修改 URL 和路徑

# 3️⃣ 測試配置
python scripts/sync_external_repos.py --list

# 4️⃣ 執行同步
python scripts/sync_external_repos.py

# 5️⃣ 檢查結果
ls -la examples/synced_files/
```

## 📋 配置範例 / Configuration Example

### 基本範例 / Basic Example

```yaml
repositories:
  - name: "my-utils"
    url: "https://github.com/username/utilities.git"
    branch: "main"
    enabled: true
    files:
      - src: "helpers.py"
        dest: "src/imported/helpers.py"
```

### 進階範例 / Advanced Example

```yaml
repositories:
  - name: "shared-configs"
    url: "https://github.com/company/configs.git"
    branch: "v2.0"
    enabled: true
    directories:
      - src: "kubernetes"
        dest: "cluster/imported"
        exclude:
          - "*.secret"
          - "*.example"
    files:
      - src: "README.md"
        dest: "docs/external/README.md"

settings:
  backup_before_sync: true
  conflict_strategy: "skip"
  verify_integrity: true
```

## 💡 主要功能 / Key Features

| 功能 / Feature | 說明 / Description |
|---------------|-------------------|
| 🎯 **選擇性同步** | 只拉取需要的檔案，不是整個倉庫 / Pull only needed files, not entire repo |
| 📁 **目錄同步** | 批次同步整個目錄 / Batch sync entire directories |
| 🔗 **Submodule 支援** | 可作為 Git submodule 整合 / Can integrate as Git submodule |
| 💾 **自動備份** | 覆寫前自動備份檔案 / Auto backup before overwriting |
| 🔒 **完整性驗證** | SHA-256 雜湊值驗證 / SHA-256 hash verification |
| ⚖️ **衝突處理** | 三種策略：跳過/覆寫/詢問 / Three strategies: skip/overwrite/prompt |
| 🤖 **自動化** | GitHub Actions 定期執行 / GitHub Actions scheduled runs |
| 🌐 **雙語** | 中文和英文介面 / Chinese and English interface |

## 📚 文檔導覽 / Documentation Guide

| 文件 / Document | 用途 / Purpose |
|----------------|---------------|
| 📖 [完整指南](docs/EXTERNAL_REPO_SYNC.md) | 詳細的使用說明 / Detailed usage guide |
| 📝 [範例集](docs/REPO_SYNC_EXAMPLES.md) | 7 個實用範例 / 7 practical examples |
| ⚡ [快速參考](docs/REPO_SYNC_QUICKREF.md) | 常用命令速查 / Quick command reference |
| 📄 [範例配置](repos_sync.example.yaml) | 可用的配置模板 / Ready-to-use config template |

## 🎮 常用命令 / Common Commands

```bash
# 列出所有配置的倉庫
python scripts/sync_external_repos.py --list

# 同步所有倉庫
python scripts/sync_external_repos.py

# 同步特定倉庫
python scripts/sync_external_repos.py --repo repo-name

# 使用自訂配置
python scripts/sync_external_repos.py --config custom.yaml

# 顯示幫助
python scripts/sync_external_repos.py --help

# 運行測試
python test_repo_sync.py
```

## 🤖 自動化同步 / Automated Sync

系統已整合 GitHub Actions，會在以下情況自動同步：

The system is integrated with GitHub Actions and syncs automatically:

- ⏰ **定時執行** / Scheduled: 每週一 00:00 UTC / Every Monday at 00:00 UTC
- 📝 **配置變更** / Config change: 當 `repos_sync.yaml` 更新時 / When `repos_sync.yaml` updates
- 👆 **手動觸發** / Manual trigger: 在 GitHub Actions 頁面手動執行 / Manual run from GitHub Actions page

### 如何手動觸發？ / How to Manually Trigger?

1. 前往 GitHub 倉庫 / Go to GitHub repository
2. 點擊 `Actions` 標籤 / Click `Actions` tab
3. 選擇 `Sync External Repositories` workflow
4. 點擊 `Run workflow` 按鈕 / Click `Run workflow` button
5. （可選）輸入要同步的倉庫名稱 / (Optional) Enter repository name
6. 點擊綠色的 `Run workflow` 執行 / Click green `Run workflow` to execute

## 🛡️ 安全性 / Security

### 建議的安全措施 / Recommended Security Measures

1. ✅ **排除敏感檔案** / Exclude sensitive files
   ```yaml
   exclude_patterns:
     - "*.secret"
     - "*.key"
     - ".env"
     - "credentials.json"
   ```

2. ✅ **使用特定版本** / Use specific versions
   ```yaml
   branch: "v1.2.3"  # 使用版本標籤 / Use version tags
   ```

3. ✅ **啟用驗證** / Enable verification
   ```yaml
   settings:
     verify_integrity: true
   ```

4. ✅ **定期審查** / Regular review
   - 檢查同步的內容 / Review synced content
   - 更新排除規則 / Update exclude rules

## 🔧 故障排除 / Troubleshooting

### 常見問題 / Common Issues

#### 1. 複製倉庫失敗 / Clone Failed

```bash
# 檢查 URL 是否正確
git ls-remote https://github.com/username/repo.git

# 檢查分支是否存在
git ls-remote --heads https://github.com/username/repo.git
```

#### 2. 權限錯誤 / Permission Error

```bash
# 確保腳本可執行
chmod +x scripts/sync_external_repos.py

# 檢查目標目錄權限
ls -la path/to/destination/
```

#### 3. YAML 語法錯誤 / YAML Syntax Error

```bash
# 安裝 yamllint
pip install yamllint

# 驗證語法
yamllint repos_sync.yaml
```

#### 4. 測試失敗 / Test Failed

```bash
# 運行完整測試
python test_repo_sync.py

# 檢查依賴
pip install -r requirements.txt
```

## 📊 測試驗證 / Test Validation

運行測試套件來驗證安裝：

Run the test suite to validate installation:

```bash
python test_repo_sync.py
```

✅ 預期結果 / Expected result:
```
🎉 所有測試通過！ / All tests passed!
總計 / Total: 8/8 測試通過 / tests passed
```

## 🎯 實際應用範例 / Real-World Examples

### 範例 1: 同步公司工具庫 / Example 1: Sync Company Utils

```yaml
repositories:
  - name: "company-python-utils"
    url: "https://github.com/company/python-utils.git"
    branch: "stable"
    enabled: true
    files:
      - src: "logger.py"
        dest: "src/utils/logger.py"
      - src: "validator.py"
        dest: "src/utils/validator.py"
```

### 範例 2: 同步 K8s 配置模板 / Example 2: Sync K8s Templates

```yaml
repositories:
  - name: "k8s-templates"
    url: "https://github.com/company/k8s-templates.git"
    branch: "v2.0"
    enabled: true
    directories:
      - src: "monitoring"
        dest: "cluster/monitoring"
        exclude:
          - "*.dev.yaml"
```

### 範例 3: 整合共享組件 / Example 3: Integrate Shared Components

```yaml
repositories:
  - name: "ui-components"
    url: "https://github.com/company/ui-components.git"
    branch: "v4.0.0"
    enabled: true
    submodule: true
    dest: "vendor/ui-components"
```

## 🤝 貢獻 / Contributing

歡迎提交 Issue 和 Pull Request！

Issues and Pull Requests are welcome!

## 📞 支援 / Support

- 📖 查看[完整文檔](docs/EXTERNAL_REPO_SYNC.md)
- 💡 查看[範例集](docs/REPO_SYNC_EXAMPLES.md)
- 🐛 [提交 Issue](https://github.com/dofaromg/flow-tasks/issues)
- 💬 在 PR 中留言討論

## 📄 授權 / License

本功能遵循主專案的授權條款。

This feature follows the main project's license.

---

**更新日期 / Last Updated:** 2024-12-19

**版本 / Version:** 1.0.0

**作者 / Author:** FlowAgent Team
