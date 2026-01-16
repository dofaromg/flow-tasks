# Vercel 部署指南 / Vercel Deployment Guide

## 🚀 快速部署 Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fdofaromg%2Fflow-tasks)

## 📋 前置需求 Prerequisites

- [Vercel 帳號](https://vercel.com/signup)
- GitHub 帳號
- Node.js 18+ (本地開發時)

## 🎯 專案介紹 Project Introduction

**FlowAgent GKE Starter** 是一個完整的 GitOps + CI/CD 部署框架，結合：

- ✅ Next.js 14 前端應用
- ✅ GrowthBook 功能旗標系統
- ✅ Kubernetes (GKE) 後端部署
- ✅ 粒子語言核心系統

此專案可同時部署到：
1. **Vercel** - 前端 Next.js 應用（本指南）
2. **Google Kubernetes Engine (GKE)** - 後端服務 ([查看 DEPLOYMENT.md](DEPLOYMENT.md))

---

## 方法一：通過 Vercel Dashboard 部署

### 步驟 1: 導入專案
1. 前往 [Vercel Dashboard](https://vercel.com/dashboard)
2. 點擊 "Add New..." → "Project"
3. 選擇 "Import Git Repository"
4. 選擇 `dofaromg/flow-tasks` 倉庫
5. 點擊 "Import"

### 步驟 2: 配置專案
Vercel 會自動偵測到 Next.js 框架，使用以下設定：

- **Framework Preset**: Next.js
- **Root Directory**: `./`
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `npm install`

### 步驟 3: 配置環境變數（可選）
如果使用 GrowthBook 功能旗標，請添加：

```
NEXT_PUBLIC_GROWTHBOOK_API_HOST=https://cdn.growthbook.io
NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY=your_client_key_here
```

### 步驟 4: 部署
點擊 "Deploy" 按鈕，等待部署完成。

---

## 方法二：通過 Vercel CLI 部署

### 安裝 Vercel CLI
```bash
npm install -g vercel
```

### 登入 Vercel
```bash
vercel login
```

### 部署到生產環境
```bash
# 首次部署
vercel

# 後續部署到生產環境
vercel --prod
```

### 本地預覽
```bash
vercel dev
```

---

## 方法三：通過 GitHub 整合自動部署

### 步驟 1: 連接 GitHub
1. 在 Vercel Dashboard 中導入專案（如方法一）
2. Vercel 會自動設置 GitHub 整合

### 步驟 2: 自動部署流程
- **推送到 `main` 分支** → 自動部署到生產環境
- **推送到其他分支** → 自動部署預覽環境
- **Pull Request** → 自動生成預覽 URL

### 步驟 3: 部署通知
Vercel 會在以下情況自動評論：
- PR 開啟時
- 新的提交推送時
- 部署完成時（附預覽 URL）

---

## 🔧 Vercel 配置說明

### vercel.json 配置
專案已包含 `vercel.json` 配置文件，提供：

1. **安全標頭**: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
2. **環境變數**: GrowthBook API 配置
3. **構建設置**: 優化的 Next.js 構建流程

### 自訂域名
在 Vercel Dashboard 中：
1. 選擇專案
2. 前往 "Settings" → "Domains"
3. 添加自訂域名
4. 更新 DNS 記錄（Vercel 會提供指示）

---

## 🌍 環境變數管理

### 在 Vercel Dashboard 設置
1. 選擇專案
2. 前往 "Settings" → "Environment Variables"
3. 添加以下變數：

| 變數名稱 | 描述 | 示例值 |
|---------|------|--------|
| `NEXT_PUBLIC_GROWTHBOOK_API_HOST` | GrowthBook API 端點 | `https://cdn.growthbook.io` |
| `NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY` | GrowthBook 客戶端金鑰 | `sdk-abc123...` |

### 通過 CLI 設置
```bash
# 添加生產環境變數
vercel env add NEXT_PUBLIC_GROWTHBOOK_API_HOST production

# 添加預覽環境變數
vercel env add NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY preview

# 列出所有環境變數
vercel env ls
```

---

## 🔍 功能旗標 (Feature Flags)

本專案整合了 GrowthBook，支援動態功能控制：

### 可用功能旗標
- `show-summer-sale` - 顯示夏季促銷橫幅
- `show-free-delivery` - 顯示免費配送橫幅  
- `proceed-to-checkout-color` - 結帳按鈕顏色 (blue/green/red)

### 在 Vercel 中測試
部署後，訪問您的 Vercel URL，功能旗標會自動生效。您可以在 GrowthBook Dashboard 中即時修改旗標值。

---

## 📊 性能優化

### Next.js 優化
- ✅ 靜態生成 (SSG)
- ✅ 圖片優化 (Next.js Image)
- ✅ 程式碼分割
- ✅ 樹狀結構移除 (Tree Shaking)

### Vercel Edge Network
- ✅ 全球 CDN 快取
- ✅ 自動 HTTPS
- ✅ HTTP/2 和 HTTP/3 支援
- ✅ 智能路由

### 建議
1. 使用 `next/image` 進行圖片優化
2. 啟用 ISR (Incremental Static Regeneration) 適用於動態內容
3. 使用 Vercel Analytics 監控效能

---

## 🐛 故障排除

### 構建失敗
```bash
# 本地測試構建
npm run build

# 檢查依賴版本
npm list next react react-dom
```

### 環境變數未生效
1. 確認變數名稱以 `NEXT_PUBLIC_` 開頭（客戶端變數）
2. 重新部署以套用新的環境變數
3. 清除瀏覽器快取

### 路由問題
確保 `next.config.mjs` 正確配置：
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
```

---

## 📚 相關資源

### Vercel 文檔
- [Vercel 官方文檔](https://vercel.com/docs)
- [Next.js 部署指南](https://nextjs.org/docs/deployment)
- [Vercel CLI 參考](https://vercel.com/docs/cli)

### 專案文檔
- [完整部署指南](DEPLOYMENT.md) - GKE 部署
- [快速開始](QUICKSTART.md)
- [架構說明](ARCHITECTURE.md)
- [GrowthBook 整合](GROWTHBOOK.md)

---

## 🎉 部署完成後

### 驗證部署
1. 訪問 Vercel 提供的 URL
2. 確認頁面正常載入
3. 測試功能旗標（橫幅顯示/隱藏）
4. 檢查控制台無錯誤訊息

### 後續步驟
1. 設置自訂域名
2. 配置 Vercel Analytics
3. 啟用 Vercel Speed Insights
4. 設置 GitHub 整合的自動部署
5. 配置環境特定的環境變數

---

## 🆘 需要幫助？

- **Vercel 支援**: [vercel.com/support](https://vercel.com/support)
- **GitHub Issues**: [github.com/dofaromg/flow-tasks/issues](https://github.com/dofaromg/flow-tasks/issues)
- **Next.js 討論**: [github.com/vercel/next.js/discussions](https://github.com/vercel/next.js/discussions)

---

## 📝 變更歷史

- **2026-01-14**: 創建 Vercel 部署指南
- 添加 `vercel.json` 配置
- 整合 GrowthBook 環境變數
- 添加安全標頭配置
