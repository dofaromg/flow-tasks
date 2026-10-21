# 外部倉庫同步範例 / External Repository Sync Examples

本文件提供多個實際使用範例，幫助你快速配置和使用倉庫同步功能。

This document provides practical examples to help you quickly configure and use the repository sync feature.

## 範例 1: 同步單一檔案 / Example 1: Sync Single File

從另一個倉庫同步一個配置檔案：

```yaml
repositories:
  - name: "config-example"
    url: "https://github.com/username/config-repo.git"
    branch: "main"
    enabled: true
    files:
      - src: "config/app.json"
        dest: "config/external_app.json"
```

執行同步：
```bash
python scripts/sync_external_repos.py --repo config-example
```

## 範例 2: 同步多個檔案 / Example 2: Sync Multiple Files

從工具庫同步多個 Python 工具函數：

```yaml
repositories:
  - name: "python-utils"
    url: "https://github.com/company/python-utilities.git"
    branch: "stable"
    enabled: true
    files:
      - src: "utils/string_helpers.py"
        dest: "src/utils/string_helpers.py"
      - src: "utils/date_helpers.py"
        dest: "src/utils/date_helpers.py"
      - src: "utils/validation.py"
        dest: "src/utils/validation.py"
```

## 範例 3: 同步整個目錄 / Example 3: Sync Entire Directory

同步 Kubernetes 配置模板目錄：

```yaml
repositories:
  - name: "k8s-templates"
    url: "https://github.com/company/kubernetes-templates.git"
    branch: "v2.0"
    enabled: true
    directories:
      - src: "base"
        dest: "cluster/imported/base"
        exclude:
          - "*.example"
          - "secrets.yaml"
          - ".gitkeep"
```

## 範例 4: 使用 Git Submodule / Example 4: Using Git Submodule

將共享組件庫作為 submodule 引入：

```yaml
repositories:
  - name: "shared-components"
    url: "https://github.com/company/shared-ui-components.git"
    branch: "v3.0"
    enabled: true
    submodule: true
    dest: "vendor/shared-components"
```

## 範例 5: 混合模式配置 / Example 5: Mixed Mode Configuration

同時使用檔案同步和目錄同步：

```yaml
repositories:
  - name: "mixed-sync"
    url: "https://github.com/company/shared-resources.git"
    branch: "main"
    enabled: true
    files:
      - src: "README.md"
        dest: "docs/external/README.md"
      - src: "LICENSE"
        dest: "licenses/EXTERNAL_LICENSE"
    directories:
      - src: "assets"
        dest: "public/external-assets"
        exclude:
          - "*.psd"
          - "*.ai"
```

## 範例 6: 測試環境配置 / Example 6: Test Environment

創建一個測試配置來驗證同步功能：

```yaml
# repos_sync.test.yaml
version: "1.0"

repositories:
  - name: "test-repo"
    url: "https://github.com/octocat/Hello-World.git"
    branch: "master"
    enabled: true
    files:
      - src: "README"
        dest: "test_sync/hello_world_readme.txt"

settings:
  backup_before_sync: true
  backup_dir: ".sync_backups"
  conflict_strategy: "skip"
  verify_integrity: true

exclude_patterns:
  - "*.pyc"
  - "__pycache__"
  - ".git"
```

執行測試：
```bash
python scripts/sync_external_repos.py --config repos_sync.test.yaml
```

## 範例 7: 生產環境配置 / Example 7: Production Environment

生產環境的完整配置範例：

```yaml
# repos_sync.prod.yaml
version: "1.0"

repositories:
  # 共享工具庫
  - name: "shared-utils"
    url: "https://github.com/company/utilities.git"
    branch: "v2.1.0"  # 使用特定版本標籤
    enabled: true
    files:
      - src: "python/logger.py"
        dest: "src/utils/logger.py"
      - src: "python/metrics.py"
        dest: "src/utils/metrics.py"
  
  # Kubernetes 配置
  - name: "k8s-configs"
    url: "https://github.com/company/k8s-configs.git"
    branch: "prod"
    enabled: true
    directories:
      - src: "monitoring"
        dest: "cluster/monitoring"
        exclude:
          - "*.dev.yaml"
          - "test-*"
  
  # 共享前端組件 (作為 submodule)
  - name: "ui-components"
    url: "https://github.com/company/ui-components.git"
    branch: "v4.0.0"
    enabled: true
    submodule: true
    dest: "frontend/vendor/ui-components"

settings:
  backup_before_sync: true
  backup_dir: ".sync_backups"
  conflict_strategy: "skip"
  verify_integrity: true
  post_sync_commands:
    - "pip install -r requirements.txt"
    - "npm install"

exclude_patterns:
  - "*.pyc"
  - "__pycache__"
  - ".git"
  - ".github"
  - "node_modules"
  - ".DS_Store"
  - "*.log"
  - "*.test.js"
  - "*.spec.js"
```

## 測試和驗證 / Testing and Verification

### 測試步驟 / Test Steps

1. **列出配置的倉庫**
   ```bash
   python scripts/sync_external_repos.py --list
   ```

2. **測試單一倉庫同步**
   ```bash
   python scripts/sync_external_repos.py --repo test-repo
   ```

3. **驗證同步結果**
   ```bash
   ls -la test_sync/
   cat test_sync/hello_world_readme.txt
   ```

4. **檢查備份**
   ```bash
   ls -la .sync_backups/
   ```

### 常見問題排除 / Common Issues

1. **權限錯誤**
   ```bash
   # 確保腳本有執行權限
   chmod +x scripts/sync_external_repos.py
   ```

2. **YAML 語法錯誤**
   ```bash
   # 使用 yamllint 檢查語法
   pip install yamllint
   yamllint repos_sync.yaml
   ```

3. **Git 連接問題**
   ```bash
   # 測試 Git 連接
   git ls-remote https://github.com/username/repo.git
   ```

## 最佳實踐 / Best Practices

1. ✅ **使用版本標籤而非分支名稱**
   ```yaml
   branch: "v1.2.3"  # 好
   branch: "main"     # 避免
   ```

2. ✅ **定期更新同步的內容**
   - 設置 GitHub Actions 定期執行
   - 審查同步的變更

3. ✅ **使用排除模式保護敏感檔案**
   ```yaml
   exclude:
     - "*.secret"
     - "*.key"
     - ".env"
   ```

4. ✅ **測試後再部署到生產**
   - 先在測試配置中驗證
   - 確認沒有問題後再應用到生產

5. ✅ **保持配置檔案簡潔明瞭**
   - 添加註解說明每個倉庫的用途
   - 使用有意義的倉庫名稱

## 更多資源 / More Resources

- [完整文檔](./EXTERNAL_REPO_SYNC.md)
- [配置檔案範例](../repos_sync.yaml)
- [GitHub Actions Workflow](../.github/workflows/sync-external-repos.yml)

---

更新日期 / Last Updated: 2024-12-19
