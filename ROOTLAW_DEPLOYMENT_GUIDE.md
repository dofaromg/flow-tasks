# RootLaw Package 自動化部署工具 v2.0

## 概述

這個工具可以自動將 RootLaw Package v1.0 部署到多個 GitHub 倉庫，並根據每個倉庫的結構自動客製化文檔。**v2.0 新增完整自動化功能**。

## 功能特色

✅ **自動複製套件**: 將完整的 RootLaw Package 複製到目標倉庫  
✅ **智能分析**: 自動分析目標倉庫的檔案結構  
✅ **客製化映射**: 根據倉庫結構自動調整 Absorption_Map.md  
✅ **批次部署**: 支援一次部署到多個倉庫  
✅ **備份機制**: 部署前自動備份現有套件  
✅ **部署報告**: 自動生成詳細的部署報告  
✅ **Git 整合**: 可選的自動提交和推送功能  
🆕 **自動拉取**: 部署前自動拉取最新變更  
🆕 **衝突檢測**: 自動檢查合併衝突  
🆕 **元代碼優化**: 自動格式化、去重、驗證交叉引用

## v2.0 新功能

### 1. 自動拉取 (--auto-pull)
在部署前自動執行 `git pull` 確保在最新代碼基礎上部署，避免版本衝突。

### 2. 自動優化 (--auto-optimize)
自動檢查和優化元代碼：
- 移除多餘的空行（超過2個連續空行）
- 格式化 Markdown 文檔
- 驗證交叉引用完整性（Evidence ID）
- 檢測重複內容

### 3. 合併衝突檢測
自動檢測 Git 合併衝突並報告衝突檔案，支援手動解決。

## 安裝要求

- Python 3.7+
- Git 命令列工具
- 對目標倉庫的訪問權限（公開倉庫或已配置的 SSH/HTTPS 認證）

## 快速開始

### 1. 部署到單個倉庫

```bash
# 基本部署（僅複製檔案，不提交）
python scripts/deploy_rootlaw_package.py --url https://github.com/username/target-repo.git

# 🆕 完整自動化：拉取、優化、提交、推送
python scripts/deploy_rootlaw_package.py \
  --url https://github.com/username/target-repo.git \
  --auto-pull --auto-optimize --commit --push --verbose

# 🆕 自動拉取 + 提交（不推送）
python scripts/deploy_rootlaw_package.py \
  --url https://github.com/username/target-repo.git \
  --auto-pull --commit

# 🆕 啟用元代碼優化
python scripts/deploy_rootlaw_package.py \
  --url https://github.com/username/target-repo.git \
  --auto-optimize --commit

# 部署到特定分支
python scripts/deploy_rootlaw_package.py --url https://github.com/username/target-repo.git --branch develop

# 詳細模式（顯示所有日誌）
python scripts/deploy_rootlaw_package.py --url https://github.com/username/target-repo.git --verbose
```

### 2. 批次部署到多個倉庫

#### 步驟 1: 創建配置檔案

複製範例配置檔案並編輯：

```bash
cp rootlaw_deploy_config.example.json rootlaw_deploy_config.json
```

編輯 `rootlaw_deploy_config.json`：

```json
{
  "version": "1.0",
  "repositories": [
    {
      "name": "my-project-1",
      "url": "https://github.com/myorg/project1.git",
      "branch": "main",
      "enabled": true,
      "commit": false,
      "push": false
    },
    {
      "name": "my-project-2",
      "url": "https://github.com/myorg/project2.git",
      "branch": "main",
      "enabled": true,
      "commit": false,
      "push": false
    }
  ]
}
```

#### 步驟 2: 執行批次部署

```bash
python scripts/deploy_rootlaw_package.py --config rootlaw_deploy_config.json --verbose
```

## 配置檔案說明

### 倉庫配置項

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `name` | string | 是 | 倉庫識別名稱 |
| `url` | string | 是 | Git 倉庫 URL (HTTPS 或 SSH) |
| `branch` | string | 否 | 目標分支 (預設: main) |
| `enabled` | boolean | 否 | 是否啟用部署 (預設: true) |
| `commit` | boolean | 否 | 是否自動提交變更 (預設: false) |
| `push` | boolean | 否 | 是否自動推送到遠端 (預設: false) |
| `description` | string | 否 | 倉庫描述 |

### 配置範例

```json
{
  "version": "1.0",
  "description": "生產環境部署配置",
  "repositories": [
    {
      "name": "frontend-app",
      "url": "https://github.com/company/frontend.git",
      "branch": "main",
      "enabled": true,
      "commit": true,
      "push": false,
      "description": "前端應用 - 自動提交但需手動推送"
    },
    {
      "name": "backend-api",
      "url": "https://github.com/company/backend.git",
      "branch": "develop",
      "enabled": true,
      "commit": false,
      "push": false,
      "description": "後端 API - 僅複製檔案"
    },
    {
      "name": "legacy-system",
      "url": "https://github.com/company/legacy.git",
      "branch": "main",
      "enabled": false,
      "description": "舊系統 - 暫時停用部署"
    }
  ]
}
```

## 部署流程

工具會執行以下步驟：

1. **驗證源套件**: 確認 `RootLaw_Package_v1.midlock/` 存在
2. **克隆目標倉庫**: 使用 `git clone --depth 1` 淺克隆
3. **備份現有套件**: 如果目標倉庫已有套件，先備份
4. **複製套件檔案**: 將所有 6 個核心文檔複製到目標倉庫
5. **分析倉庫結構**: 掃描 Python、TypeScript、YAML 檔案
6. **客製化 Absorption_Map**: 添加倉庫特定的檔案映射
7. **生成部署報告**: 創建 `DEPLOYMENT_REPORT.md`
8. **提交變更** (可選): 使用 Git 提交
9. **推送到遠端** (可選): 推送到 GitHub

## 部署後檢查

部署完成後，目標倉庫會包含：

```
target-repo/
├── RootLaw_Package_v1.midlock/
│   ├── README.md                    # 使用指南
│   ├── RootLaws_v1.md              # 42 條根律法
│   ├── Execution_Laws.md           # 5 條執行律法
│   ├── Absorption_Map.md           # 檔案映射（已客製化）
│   ├── Evidence_Index.md           # 證據索引
│   ├── Progress_Snapshot.md        # 進度快照
│   ├── DEPLOYMENT_REPORT.md        # 部署報告（新增）
│   └── .deployment_info.json       # 部署元數據（新增）
└── .rootlaw_backup_YYYYMMDD_HHMMSS/ # 備份（如果有舊版本）
```

### 驗證部署

1. 檢查 `DEPLOYMENT_REPORT.md` 了解部署詳情
2. 審閱客製化的 `Absorption_Map.md`
3. 根據倉庫特性更新 `Evidence_Index.md`
4. 配置 CI/CD 執行 E-1 自動合規檢查
5. 設定季度審查提醒（E-5）

## 命令列參數

```
用法: deploy_rootlaw_package.py [選項]

選項:
  --url URL            目標倉庫 URL
  --branch BRANCH      目標分支 (預設: main)
  --config FILE        配置檔案路徑 (JSON 格式)
  --source DIR         RootLaw Package 源倉庫路徑 (預設: .)
  --commit             自動提交變更
  --push               自動推送變更到遠端
  --verbose, -v        顯示詳細日誌
  -h, --help           顯示幫助訊息
```

## 使用範例

### 範例 1: 測試部署（不提交）

適合首次部署，先檢查結果：

```bash
python scripts/deploy_rootlaw_package.py \
  --url https://github.com/myorg/test-repo.git \
  --verbose
```

### 範例 2: 部署並提交（手動推送）

適合需要審核的部署：

```bash
python scripts/deploy_rootlaw_package.py \
  --url https://github.com/myorg/prod-repo.git \
  --commit \
  --verbose
```

然後手動審核並推送：

```bash
cd /tmp/cloned-repo
git log -1  # 檢查提交
git push    # 手動推送
```

### 範例 3: 完全自動化部署

適合信任的倉庫：

```bash
python scripts/deploy_rootlaw_package.py \
  --url https://github.com/myorg/automated-repo.git \
  --commit \
  --push \
  --verbose
```

### 範例 4: 批次部署多個倉庫

```bash
python scripts/deploy_rootlaw_package.py \
  --config production_deploy.json \
  --verbose
```

## 故障排除

### 問題 1: 克隆失敗

**錯誤**: `❌ 克隆失敗: Permission denied`

**解決方案**:
- 確認有目標倉庫的訪問權限
- 對於私有倉庫，配置 SSH 金鑰或使用個人訪問令牌
- 檢查倉庫 URL 是否正確

### 問題 2: 推送失敗

**錯誤**: `❌ 推送失敗: Authentication failed`

**解決方案**:
- 配置 Git 認證（SSH 或 HTTPS with token）
- 先使用 `--commit` 不加 `--push`，手動審核後推送
- 檢查是否有推送權限

### 問題 3: 套件不存在

**錯誤**: `RootLaw Package 不存在`

**解決方案**:
- 確保在 flow-tasks 倉庫根目錄執行
- 使用 `--source` 參數指定正確的源目錄
- 確認 `RootLaw_Package_v1.midlock/` 目錄存在

### 問題 4: 部署到錯誤的分支

**解決方案**:
- 使用 `--branch` 參數指定正確的分支
- 在配置檔案中設定 `"branch": "your-branch"`

## 進階使用

### 自訂源目錄

如果 RootLaw Package 在不同位置：

```bash
python scripts/deploy_rootlaw_package.py \
  --source /path/to/custom/repo \
  --url https://github.com/target/repo.git
```

### 使用 SSH URL

```bash
python scripts/deploy_rootlaw_package.py \
  --url git@github.com:myorg/repo.git \
  --commit
```

### 部署到企業 GitHub

```bash
python scripts/deploy_rootlaw_package.py \
  --url https://github.company.com/team/repo.git \
  --branch main \
  --commit
```

## 安全建議

⚠️ **注意事項**:

1. **測試先行**: 第一次部署時不要使用 `--push`，先手動檢查
2. **認證安全**: 使用 SSH 金鑰或個人訪問令牌，不要在腳本中硬編碼密碼
3. **權限控制**: 確保部署工具只有必要的倉庫訪問權限
4. **審核變更**: 生產環境部署前務必審核 `DEPLOYMENT_REPORT.md`
5. **備份保留**: 工具會自動備份，但建議定期備份整個倉庫

## 整合 CI/CD

### GitHub Actions 範例

創建 `.github/workflows/deploy-rootlaw.yml`:

```yaml
name: Deploy RootLaw Package

on:
  workflow_dispatch:
    inputs:
      target_repos:
        description: 'Target repositories (comma-separated)'
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Deploy RootLaw Package
        run: |
          python scripts/deploy_rootlaw_package.py \
            --config rootlaw_deploy_config.json \
            --verbose
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 版本歷史

- **v1.0** (2026-01-26): 初始版本
  - 單倉庫和批次部署
  - 自動倉庫分析
  - Absorption_Map 客製化
  - 部署報告生成

## 支援

如有問題或建議，請：
1. 查看 `DEPLOYMENT_REPORT.md` 中的日誌
2. 使用 `--verbose` 模式獲取詳細輸出
3. 在 GitHub Issues 提出問題

## 授權

本工具為 FlowAgent 專案的一部分，遵循倉庫的授權條款。

---

**作者**: MR.liou  
**版本**: v1.0  
**最後更新**: 2026-01-26
