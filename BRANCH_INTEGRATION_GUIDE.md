# 分支整合優化指南 (Branch Integration Optimization Guide)

## 概述 (Overview)

本文檔說明 FlowAgent 專案的分支整合最佳實踐和優化建議。

This document outlines the branch integration best practices and optimization recommendations for the FlowAgent project.

## 分支策略 (Branch Strategy)

### 主要分支 (Main Branches)

- **`main`**: 生產環境分支 (Production branch)
  - 所有部署到 GKE 的程式碼必須經過此分支
  - 受保護，需要 PR 審核
  - All code deployed to GKE must go through this branch
  - Protected, requires PR review

- **`develop`**: 開發整合分支 (Development integration branch)
  - 功能分支合併的目標
  - 用於整合測試
  - Target for feature branch merges
  - Used for integration testing

### 功能分支 (Feature Branches)

命名規範 (Naming Convention):
- `feature/feature-name`: 新功能開發
- `bugfix/bug-description`: 錯誤修復
- `hotfix/critical-fix`: 緊急修復
- `refactor/refactor-description`: 重構
- `copilot/task-description`: Copilot 自動化任務

## 整合檢查流程 (Integration Check Process)

### 1. 建立 Pull Request 前 (Before Creating PR)

```bash
# 確保分支是最新的 (Ensure branch is up-to-date)
git fetch origin
git rebase origin/main

# 本地測試 (Local testing)
python -m pip install -r requirements.txt
python test_integration.py
python test_comprehensive.py

# Kubernetes 配置驗證 (K8s manifest validation)
kustomize build cluster/overlays/prod > /tmp/test-manifests.yaml
```

### 2. Pull Request 檢查清單 (PR Checklist)

建立 PR 時，以下檢查會自動執行 (The following checks run automatically when creating a PR):

- ✅ **語法檢查 (Lint Check)**: Python 程式碼風格驗證
- ✅ **單元測試 (Unit Tests)**: 基礎功能測試
- ✅ **整合測試 (Integration Tests)**: 系統整合驗證
- ✅ **K8s 配置驗證 (K8s Validation)**: Kustomize 建置測試
- ✅ **Docker 建置測試 (Docker Build)**: 容器映像建置驗證
- ✅ **分支衝突檢查 (Conflict Check)**: 與主分支的衝突檢測

### 3. 自動化工作流程 (Automated Workflows)

#### PR 驗證工作流程 (PR Validation Workflow)
文件位置: `.github/workflows/pr-validation.yml`

此工作流程在每次 PR 更新時執行：
- 程式碼品質檢查
- 測試執行
- 配置驗證
- 整合狀態檢查

This workflow runs on every PR update:
- Code quality checks
- Test execution
- Configuration validation
- Integration status checks

#### CI/CD 工作流程 (CI/CD Workflows)
- **CI Build** (`.github/workflows/ci-build.yml`): 建置並推送 Docker 映像
- **CD Deploy** (`.github/workflows/cd-deploy.yml`): 部署到 GKE 叢集
- **FlowAgent CI** (`.github/workflows/blank.yml`): FlowAgent 任務系統測試

## 最佳實踐 (Best Practices)

### 1. 提交訊息規範 (Commit Message Convention)

使用清晰的提交訊息 (Use clear commit messages):

```
類型(範圍): 簡短描述

詳細說明（可選）

Type(scope): Brief description

Detailed explanation (optional)
```

類型 (Types):
- `feat`: 新功能 (New feature)
- `fix`: 錯誤修復 (Bug fix)
- `docs`: 文檔更新 (Documentation update)
- `style`: 程式碼格式 (Code formatting)
- `refactor`: 重構 (Refactoring)
- `test`: 測試相關 (Test related)
- `chore`: 維護任務 (Maintenance tasks)

範例 (Examples):
```
feat(particle-core): 新增記憶封存壓縮功能
fix(k8s): 修正 MongoDB PVC 配置問題
docs(readme): 更新部署指南
```

### 2. 分支生命週期 (Branch Lifecycle)

```
1. 建立分支 (Create branch)
   git checkout -b feature/new-feature

2. 開發和提交 (Develop and commit)
   git add .
   git commit -m "feat: add new feature"

3. 保持更新 (Keep updated)
   git fetch origin
   git rebase origin/main

4. 推送和建立 PR (Push and create PR)
   git push origin feature/new-feature

5. 通過檢查 (Pass checks)
   等待自動化測試完成 (Wait for automated tests)

6. 審核和合併 (Review and merge)
   PR 審核通過後合併 (Merge after PR review)

7. 清理分支 (Clean up branch)
   git branch -d feature/new-feature
```

### 3. 衝突解決 (Conflict Resolution)

當遇到合併衝突時 (When encountering merge conflicts):

```bash
# 更新主分支 (Update main branch)
git fetch origin

# 變基到最新的主分支 (Rebase to latest main)
git rebase origin/main

# 解決衝突 (Resolve conflicts)
# 編輯衝突的檔案 (Edit conflicting files)

# 標記為已解決 (Mark as resolved)
git add <resolved-files>
git rebase --continue

# 強制推送 (Force push)
git push --force-with-lease
```

### 4. PR 審核指南 (PR Review Guidelines)

審核者應該檢查 (Reviewers should check):

- [ ] 程式碼品質和風格 (Code quality and style)
- [ ] 測試覆蓋率 (Test coverage)
- [ ] 文檔更新 (Documentation updates)
- [ ] 安全性考量 (Security considerations)
- [ ] 效能影響 (Performance impact)
- [ ] 向後相容性 (Backward compatibility)

## 整合優化 (Integration Optimization)

### 已實施的優化 (Implemented Optimizations)

1. **自動化 PR 驗證** (Automated PR Validation)
   - 多層次測試檢查
   - Kubernetes 配置驗證
   - Docker 建置測試

2. **依賴管理** (Dependency Management)
   - 更新 requirements.txt 包含 pytest
   - 統一的 Python 版本 (3.10+)

3. **工作流程優化** (Workflow Optimization)
   - 並行執行多個檢查
   - 條件性 Docker 建置
   - 清晰的狀態報告

### 未來優化建議 (Future Optimization Recommendations)

1. **分支保護規則** (Branch Protection Rules)
   - 啟用 main 分支保護
   - 要求狀態檢查通過
   - 要求審核批准

2. **快取優化** (Cache Optimization)
   - Docker 層快取
   - Python 依賴快取
   - Kustomize 建置快取

3. **通知整合** (Notification Integration)
   - Slack/Discord 通知
   - 電子郵件摘要
   - 狀態徽章

## 疑難排解 (Troubleshooting)

### 常見問題 (Common Issues)

#### 1. PR 檢查失敗 (PR Checks Failing)

```bash
# 本地重現問題 (Reproduce issue locally)
pip install -r requirements.txt
python test_integration.py

# 檢查具體錯誤日誌 (Check specific error logs)
# 在 GitHub Actions 頁面查看詳細日誌
```

#### 2. Kubernetes 配置驗證失敗 (K8s Validation Failing)

```bash
# 驗證 Kustomize 配置 (Validate Kustomize config)
kustomize build cluster/overlays/prod

# 檢查 YAML 語法 (Check YAML syntax)
python -c "import yaml; yaml.safe_load(open('cluster/overlays/prod/kustomization.yaml'))"
```

#### 3. Docker 建置失敗 (Docker Build Failing)

```bash
# 本地測試建置 (Test build locally)
cd apps/module-a
docker build -t test-module-a .

# 檢查 Dockerfile 語法 (Check Dockerfile syntax)
docker build --no-cache -t test .
```

## 資源連結 (Resource Links)

- [GitHub Flow 指南](https://guides.github.com/introduction/flow/)
- [Kubernetes 最佳實踐](https://kubernetes.io/docs/concepts/configuration/overview/)
- [GitOps 工作流程](https://www.gitops.tech/)
- [ArgoCD 文檔](https://argo-cd.readthedocs.io/)

## 聯絡資訊 (Contact Information)

如有問題或建議，請：
- 建立 Issue
- 提交 Pull Request
- 聯絡專案維護者

For questions or suggestions:
- Create an Issue
- Submit a Pull Request
- Contact project maintainers
