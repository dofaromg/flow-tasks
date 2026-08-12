# GitHub Copilot 權限升級指南 / GitHub Copilot Permission Upgrade Guide

## 問題描述 / Problem Description

如果您看到「助手沒有權限使用」的錯誤訊息，這通常表示需要升級您的 GitHub Copilot 訂閱或啟用特定功能。

If you see an error message saying "the assistant doesn't have permission to use", this usually means you need to upgrade your GitHub Copilot subscription or enable specific features.

---

## 🔧 自託管開發模式 / Self-Hosted Development Mode

**適用於自己部署系統的用戶 / For self-deployed system users**

如果您是自行部署本系統，可以使用開發模式配置來移除所有權限限制並開啟全部功能：

### 快速啟用 / Quick Setup

```bash
# 1. 複製開發模式配置（如需自訂）
cp config/dev-mode.yaml config.yaml

# 2. 設定環境變數
export FLOW_CONFIG=config/dev-mode.yaml

# 3. 啟動 Flask API 服務（無限制模式）
python src_server_api_Version3.py

# 或使用 CLI 工具
python cli.py --config config/dev-mode.yaml
```

### 配置文件位置 / Config File Location

- **開發模式配置**: `config/dev-mode.yaml`
- **生產模式配置**: `config.sample.yaml`

### 開發模式功能 / Dev Mode Features

| 功能 / Feature | 狀態 / Status |
|----------------|---------------|
| 權限檢查 / Permission Check | ❌ 已關閉 |
| 速率限制 / Rate Limiting | ❌ 已關閉 |
| 認證要求 / Authentication | ❌ 已關閉 |
| 所有工具存取 / All Tools Access | ✅ 已開啟 |
| 調試模式 / Debug Mode | ✅ 已開啟 |
| 無限資源 / Unlimited Resources | ✅ 已開啟 |

### ⚠️ 注意事項 / Important Notes

1. **僅限開發環境**: 開發模式配置會關閉所有安全檢查，切勿用於生產環境！
2. **資料安全**: 開發模式下無輸入驗證，請確保環境隔離
3. **切換到生產**: 部署時請使用 `config.sample.yaml` 作為基礎

---

## 重要連結 / Important Links

### 🔑 GitHub Copilot 訂閱管理
- **個人訂閱頁面 / Personal Subscription**: https://github.com/settings/copilot
- **組織設定 / Organization Settings**: https://github.com/organizations/{YOUR_ORG}/settings/copilot

### 📚 官方文檔 / Official Documentation
- **GitHub Copilot 文檔**: https://docs.github.com/en/copilot
- **GitHub Copilot 定價**: https://github.com/features/copilot#pricing
- **GitHub Copilot Business**: https://docs.github.com/en/copilot/copilot-business
- **GitHub Copilot Enterprise**: https://docs.github.com/en/copilot/github-copilot-enterprise

### 🛠️ Copilot Coding Agent 相關
- **Copilot Coding Agent 文檔**: https://docs.github.com/en/copilot/using-github-copilot/using-the-github-copilot-coding-agent
- **啟用 Coding Agent**: https://github.com/settings/copilot/agent

---

## 升級步驟 / Upgrade Steps

### 方案 1: 升級到 GitHub Copilot Pro (個人用戶)

1. 前往 https://github.com/settings/copilot
2. 點擊「Upgrade to Copilot Pro」或「Subscribe」
3. 選擇付款方式並完成訂閱
4. 訂閱後，重新啟動您的 IDE 以獲取新權限

### 方案 2: 加入組織的 Copilot Business/Enterprise

如果您是組織成員：
1. 聯繫您的組織管理員
2. 請求將您加入 Copilot Business 或 Enterprise 計劃
3. 管理員需在 https://github.com/organizations/{ORG}/settings/copilot 中添加您的帳戶

### 方案 3: 啟用 Copilot Coding Agent

如果您已有 Copilot 訂閱但無法使用 Coding Agent：
1. 前往 https://github.com/settings/copilot
2. 找到「Copilot coding agent」或「Agent」部分
3. 啟用該功能
4. 確保您的倉庫設定允許 Copilot 操作

---

## 不同計劃的功能比較 / Feature Comparison

| 功能 / Feature | Free | Pro | Business | Enterprise |
|----------------|------|-----|----------|------------|
| 程式碼補全 / Code Completion | ✅ 有限制 | ✅ | ✅ | ✅ |
| Chat 功能 / Chat | ✅ 有限制 | ✅ | ✅ | ✅ |
| Coding Agent | ❌ | ✅ | ✅ | ✅ |
| 自定義指令 / Custom Instructions | ❌ | ✅ | ✅ | ✅ |
| 組織政策管理 / Org Policy Management | ❌ | ❌ | ✅ | ✅ |
| 知識庫整合 / Knowledge Base | ❌ | ❌ | ❌ | ✅ |

---

## 常見問題排解 / Troubleshooting

### Q: 我已經訂閱了，為什麼還是沒有權限？

**可能原因 / Possible Reasons**:
1. **訂閱未生效**: 等待幾分鐘後重試，或重新登入 GitHub
2. **IDE 需要更新**: 確保您的 VS Code 或 IDE 已更新到最新版本
3. **擴展需要重新授權**: 嘗試重新安裝 GitHub Copilot 擴展
4. **組織限制**: 您的組織可能限制了某些功能的使用

### Q: 如何檢查我的訂閱狀態？

前往 https://github.com/settings/copilot 查看您的訂閱詳情。

### Q: Coding Agent 顯示「沒有權限」？

1. 確保您有 Copilot Pro 或更高級別的訂閱
2. 前往倉庫設定 > Actions > General
3. 確保「Allow GitHub Actions to create and approve pull requests」已啟用
4. 檢查 https://github.com/settings/copilot 中的 Agent 設定

---

## 倉庫特定設定 / Repository-Specific Settings

如果您是倉庫管理員，需要啟用 Copilot Coding Agent：

1. 前往倉庫 > Settings > Copilot
2. 或前往 https://github.com/{owner}/{repo}/settings/copilot
3. 啟用「Allow Copilot to operate on this repository」

### 對於本倉庫 (FlowAgent.Runtime)

本倉庫已配置 Copilot 相關設定：
- `.github/copilot-instructions.md` - Copilot 專用指令
- `.github/agents/` - 自定義 Agent 定義
- `.github/ISSUE_TEMPLATE/copilot_task.md` - Copilot 任務模板

---

## 學生和教育者 / Students and Educators

如果您是學生或教育者，可以申請免費的 GitHub Copilot：

1. 前往 https://education.github.com/
2. 申請 GitHub Education 福利
3. 通過驗證後，您將獲得免費的 GitHub Copilot Pro 訪問權限

---

## 聯繫支援 / Contact Support

如果上述方法都無法解決問題：

- **GitHub 支援**: https://support.github.com/
- **GitHub 社群討論**: https://github.com/orgs/community/discussions
- **Copilot 反饋**: https://github.com/github/feedback/discussions/categories/copilot

---

## 本地開發環境設定 / Local Development Setup

如果您想在本地使用 Copilot 功能：

### VS Code
1. 安裝 GitHub Copilot 擴展
   - 在 VS Code 中搜索 "GitHub Copilot" 並安裝

2. 登入 GitHub 帳戶
   - 點擊 VS Code 左下角的帳戶圖標
   - 選擇「使用 GitHub 登入」

3. 確認 Copilot 已啟用
   - 查看 VS Code 右下角是否顯示 Copilot 圖標

### JetBrains IDEs
1. 前往 Settings > Plugins
2. 搜索 "GitHub Copilot"
3. 安裝並重啟 IDE
4. 登入您的 GitHub 帳戶

---

**最後更新 / Last Updated**: 2026-01-27  
**維護者 / Maintainer**: GitHub Copilot Coding Agent
