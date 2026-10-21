# GitHub Codespaces 快速參考指南

## 📋 基本命令 / Basic Commands

以下是管理 GitHub Codespaces 的常用命令：

### 1. 列出所有 Codespaces
```bash
gh codespace list
```
顯示您所有的 Codespaces，包括名稱、狀態和最後使用時間。

### 2. 連接到 Codespace
```bash
gh codespace code -c CODESPACE_NAME
```
在 VS Code 中打開指定的 Codespace。這會重置刪除計時器。

**替代方式：**
```bash
# 使用 SSH 連接
gh codespace ssh -c CODESPACE_NAME

# 在瀏覽器中打開
gh codespace code -w -c CODESPACE_NAME
```

### 3. 停止 Codespace（節省使用時數）
```bash
gh codespace stop -c CODESPACE_NAME
```
停止正在運行的 Codespace 以節省計算時數。停止的 Codespace 不會被刪除。

**注意：** 停止的 Codespace 仍然計入 30 天刪除期限。

### 4. 刪除 Codespace
```bash
gh codespace delete -c CODESPACE_NAME
```
永久刪除指定的 Codespace。此操作無法撤銷。

---

## 🚀 快速入門 / Quick Start

### 安裝 GitHub CLI
```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows
winget install --id GitHub.cli
```

### 驗證身份
```bash
gh auth login
```

### 創建新的 Codespace
```bash
gh codespace create --repo OWNER/REPO
```

---

## 💡 實用技巧 / Useful Tips

### 查看 Codespace 詳細信息
```bash
gh codespace view -c CODESPACE_NAME
```

### 列出帶有 JSON 輸出
```bash
gh codespace list --json name,state,lastUsedAt
```

### 端口轉發
```bash
gh codespace ports -c CODESPACE_NAME
```

### 查看日誌
```bash
gh codespace logs -c CODESPACE_NAME
```

---

## ⚠️ 重要提醒 / Important Notes

### Codespace 刪除政策
- **非活動期限**: 30 天
- GitHub 會在 Codespace 30 天未使用後自動刪除
- 在刪除前 7、3 和 1 天會發送電子郵件通知

### 保持 Codespace 活躍
要防止 Codespace 被刪除，至少每 30 天執行以下操作之一：
1. 連接到 Codespace (`gh codespace code -c CODESPACE_NAME`)
2. 在瀏覽器中打開: https://github.com/codespaces
3. 在 Codespace 中執行命令或編輯文件

### 成本優化
- 不使用時停止 Codespace 以節省核心時數
- 定期刪除不需要的 Codespace
- 免費帳戶每月有 120 核心時數
- Pro 帳戶每月有 180 核心時數

---

## 📊 監控工具 / Monitoring Tools

本專案包含自動化監控工具：

### 檢查 Codespace 狀態
```bash
# 快速檢查
./scripts/check-codespace-retention.sh

# 詳細監控（包含警告）
./scripts/monitor-codespaces.sh
```

### 自動化工作流程
- `.github/workflows/codespace-monitoring.yml`
- 每週自動檢查 Codespace 狀態
- 自動創建問題提醒即將刪除的 Codespace

---

## 📚 更多資源 / More Resources

- 📖 [完整管理指南](./CODESPACE_MANAGEMENT.md) - 詳細的管理文檔（英文）
- ⚡ [快速行動指南](./QUICK_ACTION_CODESPACE.md) - 緊急情況處理
- 🔍 [刪除分析](./CODESPACE_DELETION_ANALYSIS_ZH.md) - 深入分析（中文）
- 🌐 [GitHub 官方文檔](https://docs.github.com/en/codespaces)

---

## 🆘 常見問題 / FAQ

### Q: 如何找到我的 CODESPACE_NAME？
A: 運行 `gh codespace list` 查看所有 Codespace 的名稱。

### Q: 停止和刪除有什麼區別？
A: 
- **停止**: 暫時停止運行，節省核心時數，數據保留
- **刪除**: 永久移除，無法恢復

### Q: 如何防止意外刪除？
A: 
1. 定期連接到 Codespace（每 2 週一次）
2. 啟用電子郵件通知
3. 使用自動化監控腳本
4. 經常提交和推送代碼到 Git

### Q: Codespace 被刪除後能恢復嗎？
A: 
- 已提交的代碼：可以從 Git 歷史恢復
- 未提交的工作：無法恢復
- 建議：養成頻繁提交的習慣

---

## ✅ 最佳實踐 / Best Practices

1. **定期連接**: 至少每 2 週連接一次
2. **頻繁提交**: 經常將工作提交到 Git
3. **使用監控**: 啟用自動化監控工作流程
4. **清理舊的**: 每月刪除不需要的 Codespace
5. **停止不用的**: 不工作時停止 Codespace 節省時數

---

**最後更新**: 2026-02-04  
**專案**: dofaromg/flow-tasks
