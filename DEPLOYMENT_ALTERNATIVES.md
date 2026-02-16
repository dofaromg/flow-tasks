# 🚀 部署替代方案指南 / Deployment Alternatives Guide

> 📌 **不想用 Vercel？這裡有多種替代方案！**
> 
> Don't want to use Vercel? Here are multiple alternatives!

---

## 📋 目錄 / Table of Contents

1. [當前狀況說明](#當前狀況說明)
2. [推薦方案](#推薦方案)
3. [所有可用選項](#所有可用選項)
4. [方案對比](#方案對比)
5. [快速開始指南](#快速開始指南)

---

## 🎯 當前狀況說明

### ✅ 專案已遷移至 GKE

**好消息！** 本專案**已經不再使用 Vercel**作為主要部署平台。

我們已經完成從 Vercel 到 Google Kubernetes Engine (GKE) 的遷移，原因是：

- ❌ Vercel 部署經常失敗
- ❌ 與後端服務分離，管理複雜
- ❌ 受限於平台限制

**當前主要部署方式是 GKE**，具有以下優勢：

- ✅ 穩定可靠的企業級基礎設施
- ✅ 與後端服務統一管理
- ✅ 完全控制部署流程
- ✅ GitOps 自動化部署
- ✅ 可擴展和高可用性

### 📚 相關文檔

- [GKE 遷移指南](GKE_MIGRATION.md) - 從 Vercel 遷移到 GKE 的完整說明
- [GKE 部署指南](DEPLOYMENT.md) - 完整的 GKE 部署步驟
- [Vercel 部署指南](VERCEL_DEPLOYMENT.md) - **已棄用**，僅供參考

---

## 🌟 推薦方案

### 1. Google Kubernetes Engine (GKE) ⭐⭐⭐⭐⭐ 【當前使用】

**最推薦**，專案已完整配置並正在使用。

#### 優點
- ✅ 企業級穩定性和可靠性
- ✅ 完整的 CI/CD 自動化
- ✅ 與後端服務統一管理
- ✅ 可擴展性強
- ✅ 詳細的監控和日誌
- ✅ **已有完整配置，開箱即用**

#### 快速開始
```bash
# 1. 配置 GCP 認證
gcloud auth login
gcloud config set project flowmemorysync

# 2. 獲取 cluster 憑證
gcloud container clusters get-credentials modular-cluster \
  --zone asia-east1-a --project flowmemorysync

# 3. 部署
kubectl apply -k cluster/overlays/prod/

# 4. 查看服務
kubectl get svc -n flowagent
```

📖 **詳細文檔**: [GKE_MIGRATION.md](GKE_MIGRATION.md)

---

### 2. Docker 本地/自託管部署 ⭐⭐⭐⭐

適合開發測試或自己有服務器的情況。

#### 優點
- ✅ 完全控制
- ✅ 無雲服務費用
- ✅ 簡單快速
- ✅ **專案已有 Dockerfile**

#### 快速開始

**Next.js 前端：**
```bash
# 構建
docker build -t flowagent-nextjs -f apps/nextjs-frontend/Dockerfile .

# 運行
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_GROWTHBOOK_API_HOST=https://cdn.growthbook.io \
  -e NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY=your_key \
  flowagent-nextjs
```

**Python 後端：**
```bash
# 構建
docker build -t flowagent-backend .

# 運行
docker run -p 8000:8000 \
  -v $(pwd)/config.yaml:/data/config.yaml \
  flowagent-backend
```

**使用 Docker Compose：**
```bash
# 創建 docker-compose.yml 後
docker-compose up -d
```

---

## 🎨 所有可用選項

### 3. Railway.app ⭐⭐⭐⭐

現代化的部署平台，類似 Vercel 但更穩定。

#### 特點
- ✅ 從 GitHub 一鍵部署
- ✅ 自動 HTTPS
- ✅ 內建數據庫支持
- ✅ 簡單的環境變數管理
- ✅ **免費額度**

#### 部署步驟
1. 前往 [railway.app](https://railway.app)
2. 使用 GitHub 登入
3. 點擊 "New Project" → "Deploy from GitHub repo"
4. 選擇 `dofaromg/flow-tasks`
5. 配置環境變數（如需要）
6. 點擊 "Deploy"

#### Next.js 配置
Railway 會自動檢測 Next.js 項目，使用：
- **構建命令**: `npm run build`
- **啟動命令**: `npm start`
- **端口**: 3000

---

### 4. Render.com ⭐⭐⭐⭐

免費額度豐富，適合小型項目。

#### 特點
- ✅ 免費 SSL
- ✅ 自動從 GitHub 部署
- ✅ 支持 Docker
- ✅ 內建 PostgreSQL/Redis
- ✅ **免費層級**

#### 部署步驟

**Web Service (Next.js):**
1. 前往 [render.com](https://render.com)
2. 點擊 "New +" → "Web Service"
3. 連接 GitHub repository
4. 配置：
   - **Name**: flowagent-nextjs
   - **Environment**: Node
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
   - **Plan**: Free

**Docker Service:**
1. 點擊 "New +" → "Web Service"
2. 選擇 "Docker"
3. 設置 Dockerfile 路徑: `apps/nextjs-frontend/Dockerfile`

---

### 5. Fly.io ⭐⭐⭐⭐

全球分佈式部署，低延遲。

#### 特點
- ✅ 全球邊緣網絡
- ✅ 支持 Docker
- ✅ 自動擴展
- ✅ 免費額度
- ✅ WebSocket 支持

#### 部署步驟

**安裝 Fly CLI:**
```bash
curl -L https://fly.io/install.sh | sh
```

**部署 Next.js:**
```bash
# 1. 登入
fly auth login

# 2. 在項目目錄初始化
fly launch

# 3. 部署
fly deploy

# 4. 查看應用
fly open
```

**使用現有 Dockerfile:**
```bash
# 指定 Dockerfile 路徑
fly launch --dockerfile apps/nextjs-frontend/Dockerfile
```

---

### 6. Netlify ⭐⭐⭐

適合靜態站點和 JAMstack 應用。

#### 特點
- ✅ 極快的 CDN
- ✅ 一鍵部署
- ✅ 表單處理
- ✅ Serverless Functions
- ✅ **免費額度**

#### 部署步驟

**方法 1: 從 Git 部署**
1. 前往 [netlify.com](https://netlify.com)
2. 點擊 "Add new site" → "Import an existing project"
3. 選擇 GitHub
4. 選擇 repository
5. 配置：
   - **Build command**: `npm run build`
   - **Publish directory**: `.next`
   - **Base directory**: (留空)

**方法 2: CLI 部署**
```bash
# 安裝 Netlify CLI
npm install -g netlify-cli

# 登入
netlify login

# 部署
netlify deploy --prod
```

**注意**: Netlify 主要適合靜態導出，需要在 `next.config.mjs` 中設置：
```javascript
output: 'export'
```

---

### 7. AWS (ECS/EKS) ⭐⭐⭐⭐

企業級雲服務，完全可控。

#### 選項 A: AWS ECS (Elastic Container Service)

**特點:**
- ✅ 無需管理 Kubernetes
- ✅ 與 AWS 服務深度整合
- ✅ 按需付費

**部署步驟:**
```bash
# 1. 安裝 AWS CLI
aws configure

# 2. 創建 ECR repository
aws ecr create-repository --repository-name flowagent-nextjs

# 3. 構建並推送映像
aws ecr get-login-password | docker login --username AWS --password-stdin <ecr-uri>
docker build -t flowagent-nextjs -f apps/nextjs-frontend/Dockerfile .
docker tag flowagent-nextjs:latest <ecr-uri>/flowagent-nextjs:latest
docker push <ecr-uri>/flowagent-nextjs:latest

# 4. 創建 ECS task definition 和 service
# 可以通過 AWS Console 或 CloudFormation 完成
```

#### 選項 B: AWS EKS (Elastic Kubernetes Service)

類似 GKE，但在 AWS 上：
```bash
# 1. 創建 EKS cluster
eksctl create cluster --name flowagent-cluster --region us-east-1

# 2. 使用現有 Kubernetes 配置
kubectl apply -k cluster/overlays/prod/
```

---

### 8. DigitalOcean App Platform ⭐⭐⭐

簡單易用，價格透明。

#### 特點
- ✅ 簡單的 UI
- ✅ 透明定價
- ✅ 自動 SSL
- ✅ 從 GitHub 部署

#### 部署步驟
1. 前往 [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. 點擊 "Create App"
3. 選擇 GitHub repository
4. 配置：
   - **Type**: Web Service
   - **Build Command**: `npm run build`
   - **Run Command**: `npm start`
5. 選擇計畫（基礎方案 $5/月）
6. 點擊 "Launch App"

---

### 9. Cloudflare Pages ⭐⭐⭐

超快的全球 CDN，適合靜態站點。

#### 特點
- ✅ 無限免費帶寬
- ✅ 全球 CDN
- ✅ 自動 HTTPS
- ✅ GitHub 整合

#### 部署步驟
1. 前往 [Cloudflare Pages](https://pages.cloudflare.com)
2. 連接 GitHub repository
3. 配置：
   - **Framework preset**: Next.js (Static Export)
   - **Build command**: `npm run build`
   - **Build output directory**: `out`
4. 在 `next.config.mjs` 添加：
   ```javascript
   output: 'export'
   ```

---

### 10. Heroku ⭐⭐⭐

經典 PaaS 平台。

#### 特點
- ✅ 簡單易用
- ✅ 豐富的 add-ons
- ✅ Git-based 部署

#### 部署步驟
```bash
# 1. 安裝 Heroku CLI
brew install heroku/brew/heroku

# 2. 登入
heroku login

# 3. 創建應用
heroku create flowagent-app

# 4. 部署
git push heroku main

# 5. 查看
heroku open
```

**注意**: Heroku 已取消免費方案，最低 $7/月。

---

## 📊 方案對比

| 平台 | 難度 | 成本 | 穩定性 | 推薦度 | 備註 |
|------|------|------|--------|--------|------|
| **GKE** | ⭐⭐⭐⭐ | $$$ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **當前使用，最推薦** |
| **Docker 本地** | ⭐⭐ | $ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 開發測試首選 |
| **Railway** | ⭐ | $$ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Vercel 最佳替代 |
| **Render** | ⭐ | $ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 免費額度豐富 |
| **Fly.io** | ⭐⭐ | $$ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 全球分佈式 |
| **Netlify** | ⭐ | $ | ⭐⭐⭐ | ⭐⭐⭐ | 靜態站點最佳 |
| **AWS ECS/EKS** | ⭐⭐⭐⭐ | $$$ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 企業級方案 |
| **DigitalOcean** | ⭐⭐ | $$ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 簡單易用 |
| **Cloudflare Pages** | ⭐ | 免費 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 靜態站點 |
| **Heroku** | ⭐ | $$ | ⭐⭐⭐ | ⭐⭐ | 經典但較貴 |

**難度**: ⭐ = 簡單, ⭐⭐⭐⭐⭐ = 複雜  
**成本**: $ = 便宜/免費, $$$ = 較貴  
**穩定性**: ⭐ = 一般, ⭐⭐⭐⭐⭐ = 極穩定

---

## 🚀 快速開始指南

### 情境 1: 我想要最簡單的方案

**推薦**: Railway.app 或 Render.com

```bash
# 只需要 3 步：
1. 註冊帳號 (railway.app 或 render.com)
2. 連接 GitHub repository
3. 點擊 Deploy
```

---

### 情境 2: 我想要免費方案

**推薦**: Render.com (免費層級) 或 Fly.io (免費額度)

免費額度：
- **Render**: 750 小時/月免費
- **Fly.io**: 3 個免費應用
- **Netlify**: 100GB 免費帶寬/月

---

### 情境 3: 我想要最穩定的方案

**推薦**: 繼續使用 GKE（當前方案）或 AWS EKS

你已經在使用最穩定的方案！
```bash
# 確認當前部署狀態
kubectl get pods -n flowagent
kubectl get svc -n flowagent
```

---

### 情境 4: 我想在本地或自己的服務器部署

**推薦**: Docker 部署

```bash
# 1. 構建映像
docker build -t flowagent -f apps/nextjs-frontend/Dockerfile .

# 2. 運行
docker run -d -p 3000:3000 \
  --name flowagent-app \
  -e NEXT_PUBLIC_GROWTHBOOK_API_HOST=https://cdn.growthbook.io \
  flowagent

# 3. 訪問
open http://localhost:3000
```

---

### 情境 5: 我想要全球 CDN 加速

**推薦**: Cloudflare Pages 或 Netlify

需要將 Next.js 配置為靜態導出：
```javascript
// next.config.mjs
const nextConfig = {
  output: 'export', // 啟用靜態導出
};
```

---

## 🔧 環境變數配置

所有方案都需要配置以下環境變數（如使用 GrowthBook）：

```bash
NEXT_PUBLIC_GROWTHBOOK_API_HOST=https://cdn.growthbook.io
NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY=your_actual_key_here
```

### 各平台設置方法

**GKE:**
```bash
kubectl create secret generic growthbook-config \
  --from-literal=api-host=https://cdn.growthbook.io \
  --from-literal=client-key=your_key \
  -n flowagent
```

**Railway/Render/Fly.io:**
在 Dashboard 的環境變數設置頁面添加

**Docker:**
```bash
docker run -e NEXT_PUBLIC_GROWTHBOOK_API_HOST=... \
           -e NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY=... \
           your-image
```

**Netlify/Cloudflare:**
在網站設置的環境變數部分添加

---

## 📚 相關文檔

### 主要文檔
- [GKE 遷移指南](GKE_MIGRATION.md) - 完整的 GKE 遷移說明
- [GKE 部署指南](DEPLOYMENT.md) - GKE 部署步驟
- [Vercel 部署指南](VERCEL_DEPLOYMENT.md) - 已棄用，僅供參考

### 應用配置
- [Next.js Frontend README](apps/nextjs-frontend/README.md)
- [Docker 配置](Dockerfile)
- [Kubernetes 配置](cluster/)

---

## ❓ 常見問題

### Q: Vercel 配置文件還需要嗎？

A: 不需要。`vercel.json` 和 `.vercelignore` 已標記為棄用，保留僅供參考。

### Q: 我可以同時使用多個平台嗎？

A: 可以！你可以：
- GKE 用於生產環境
- Railway/Render 用於測試環境
- Docker 用於本地開發

### Q: 哪個方案最便宜？

A: 
- **完全免費**: Docker 本地部署
- **有免費額度**: Render.com, Fly.io, Netlify, Cloudflare Pages
- **最便宜的雲服務**: Railway ($5/月起)

### Q: 我需要改變代碼嗎？

A: 大部分情況不需要！專案已配置支持：
- Docker 部署 (`output: 'standalone'`)
- Kubernetes 部署（完整配置）
- 靜態導出（需要改為 `output: 'export'`，僅 Netlify/Cloudflare Pages）

### Q: 如何選擇最適合的方案？

考慮以下因素：
1. **預算**: 免費額度 vs 付費服務
2. **技術能力**: 簡單 UI vs Kubernetes
3. **可控性**: 完全控制 vs 托管服務
4. **流量**: 小流量 vs 大流量
5. **需求**: 快速原型 vs 生產環境

---

## 🆘 需要幫助？

### 文檔資源
- [GKE 官方文檔](https://cloud.google.com/kubernetes-engine/docs)
- [Docker 文檔](https://docs.docker.com)
- [Next.js 部署文檔](https://nextjs.org/docs/deployment)

### 社群支持
- [GitHub Issues](https://github.com/dofaromg/flow-tasks/issues)
- [GitHub Discussions](https://github.com/dofaromg/flow-tasks/discussions)

---

## 📝 總結建議

### 🏆 最推薦的選擇

1. **繼續使用 GKE** - 你已經在用最好的方案！
2. **Railway.app** - 如果想要更簡單的管理界面
3. **Docker 本地** - 如果想要完全控制和零成本

### ⚡ 快速決策樹

```
需要企業級穩定性？
  ├─ Yes → 繼續使用 GKE 或 AWS EKS
  └─ No → 繼續往下
      需要免費方案？
        ├─ Yes → Render.com 或 Fly.io
        └─ No → 繼續往下
            想要簡單易用？
              ├─ Yes → Railway.app
              └─ No → Docker 自託管
```

---

**🎉 結論**: 你已經在使用最好的方案（GKE）！如果需要更簡單的管理，Railway.app 是最佳替代。

如有任何問題，請在 [GitHub Issues](https://github.com/dofaromg/flow-tasks/issues) 提出！
