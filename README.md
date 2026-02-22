# FlowAgent GKE Starter (GitOps + CI/CD)

這個壓縮包是「一次搞定」的部署骨架。你把整包丟到 GitHub（或上傳到你的空間）即可：

## 部署空間位置（你會用到的介面）
- **GKE 叢集控制台**：`https://console.cloud.google.com/kubernetes/list?project=flowmemorysync`
- **Artifact Registry**（容器倉庫）：`https://console.cloud.google.com/artifacts?project=flowmemorysync&supportedpurview=project`
- **Cloud Shell**：`https://console.cloud.google.com/?cloudshell=true&project=flowmemorysync`
- **（可選）Cloud Run**：`https://console.cloud.google.com/run?project=flowmemorysync`
- **（可選）備份 GCS Bucket**：`gs://flowagent-backup-flowmemorysync`

> 把 `flowmemorysync` 換成你的（例如 `flowmemorysync`）。`dofaromg/----2` 換成你的 repo URL。

---

## 路線 A：GitOps（Argo CD 拉）
1. 在叢集安裝 Argo CD：
   ```bash
   kubectl create ns argocd || true
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```
2. 將本 repo push 到 GitHub。
3. 套用 `argocd/app.yaml`（把 repo URL 改成你的）：
   ```bash
   kubectl apply -f argocd/app.yaml
   ```
4. Argo 會自動把 `cluster/overlays/prod` 底下的所有資源佈署到命名空間 `flowagent`。

## 路線 B：GitHub Actions（推進叢集）
- 設定 GitHub Secrets：`GCP_WIF_PROVIDER`、`GCP_DEPLOYER_SA`。
- 推 commit 後，`ci-build.yml` 會 build/push 映像，`cd-deploy.yml` 會 `kustomize build` 並 `kubectl apply`。

---

## 必改的參數
- 容器映像位址：`asia-east1-docker.pkg.dev/flowmemorysync/flowagent/{module-a,orchestrator}:latest`
- `argocd/app.yaml` 的 repo URL
- 叢集名稱（預設 `modular-cluster`）、區域（預設 `asia-east1-a`）

---

## 一鍵初始化（Cloud Shell）
> 將 `flowmemorysync`、`YOUR_GH_REPO` 改成你的。

```bash
export PROJECT_ID=flowmemorysync
export REGION=asia-east1
export ZONE=asia-east1-a
export NS=flowagent

gcloud config set project $PROJECT_ID
gcloud services enable container.googleapis.com artifactregistry.googleapis.com

gcloud container clusters get-credentials modular-cluster --zone $ZONE --project $PROJECT_ID
# FlowAgent — GKE Starter with Particle Language Core
# FlowAgent — GKE 啟動器與粒子語言核心

版本 / Version: v3.0.0  •  更新時間 / Updated: 2026-02-09

## 🌍 部署結構索引 / Deployment Structure Index

**⭐ 快速查看完整的"地球結構"部署架構 / Quick View Complete "Earth Structure" Deployment:**

### 🎯 專業部署分析 (Professional Analysis) - ⭐ NEW!

- 📊 [**專業部署分析報告 / Professional Deployment Analysis**](./專業部署分析報告.md) - ⭐ **NEW** 完整的專業部署架構分析（19,000+ 字）
  - 架構評估與評分
  - 安全性分析
  - 成本分析
  - 性能基準
  - 最佳實踐建議
  - 完整的行動計劃

- 📋 [**部署執行摘要 / Deployment Execution Summary**](./部署執行摘要.md) - ⭐ **NEW** 部署驗證結果與實際部署指南
  - Dry-run 測試結果
  - 部署就緒度評估
  - 實際部署流程
  - 風險分析與建議

### 📚 部署實施文檔 (Deployment Implementation)

- 🎯 [**實際部署指南 / Actual Deployment Guide**](./實際部署指南.md) - 完整的生產環境實際部署流程
- ✅ [**部署後檢查清單 / Post-Deployment Checklist**](./部署後檢查清單.md) - 部署完成後必須檢查的項目
- 📖 [**部署結構索引 / Deployment Structure Index**](./DEPLOYMENT_STRUCTURE_INDEX.md) - 完整的部署組件、配置和拓撲圖
- ⚡ [**部署快速參考 / Deployment Quick Reference**](./DEPLOYMENT_QUICK_REFERENCE.md) - 快速命令和配置速查表
- 🚀 [**部署指南 / Deployment Guide**](./DEPLOYMENT.md) - 詳細的部署步驟和故障排除
- 🏗️ [**架構說明 / Architecture**](./ARCHITECTURE.md) - 系統架構與流程圖
- 🔄 [**GKE 遷移指南 / GKE Migration Guide**](./GKE_MIGRATION.md) - Next.js 從 Vercel 遷移到 GKE
- 🌟 [**部署替代方案 / Deployment Alternatives**](./DEPLOYMENT_ALTERNATIVES.md) - 不用 Vercel？10+ 種替代方案
- 🐳 [**Docker Compose 指南 / Docker Compose Guide**](./DOCKER_COMPOSE_GUIDE.md) - 本地/自託管部署

### 🎯 一鍵部署 / One-Click Deployment
```bash
# 🚀 實際部署 - 完整的生產環境部署 (推薦)
bash scripts/actual_deploy.sh

# 或分步驟部署
bash scripts/oneclick_gke_init.sh  # 初始化 GKE 叢集
kubectl apply -k cluster/overlays/prod/  # 部署應用

# 檢查部署狀態
bash scripts/check_deployment_status.sh
```

---

## 📦 專案概覽 / Project Overview

這個專案整合了：
This project integrates:

1) **GKE 部署架構** - 完整的 Kubernetes 微服務部署
   - Next.js Frontend (React 前端應用)
   - Astro Frontend (靜態網站前端)
   - Module-A (主服務模組)
   - Orchestrator (協調器)
   - MongoDB (資料庫)
   - Prometheus (監控)

2) **粒子語言核心系統 (Particle Language Core)** - MRLiou 粒子邏輯執行框架
   - 從 `particle_core/` 讀取粒子檔案
   - 邏輯種子計算與函數鏈執行
   - 支援記憶封存與還原

3) **GitOps + CI/CD** - 自動化部署流程
   - GitHub Actions (CI/CD)
   - ArgoCD (GitOps)
   - Kustomize (配置管理)

📚 **詳細文檔**：
- [完整部署指南](DEPLOYMENT.md)
- [快速參考](QUICKSTART.md)
- [架構圖表](ARCHITECTURE.md)
- [應用程式說明](apps/README.md)
- [分支整合優化指南](BRANCH_INTEGRATION_GUIDE.md) ⭐ 新增
- [Codespace 管理指南](CODESPACE_MANAGEMENT.md) 🆕 新增
- [分支神經網絡系統](BRANCH_NEURAL_MAP.md) 🧠 新增 - 視覺化分支連結關係
- [FlowHub 整合套件](FLOWHUB_EXPORT_PACKAGE.md) 📦 [commit:ffebfa0](https://github.com/dofaromg/flow-tasks/commit/ffebfa0)
> 注意：本專案包含完整的 GKE 部署配置和粒子語言核心系統。
> Note: This project includes complete GKE deployment configurations and the Particle Language Core system.

---

## 快速開始 / Quick Start

> 💡 **提示 / Tip**: 在開始之前，您可以運行驗證腳本來檢查所有必要的文件和工具:
> ```bash
> bash scripts/verify_quickstart.sh
> ```
> Before starting, you can run the verification script to check all necessary files and tools.

### 選項 1: GKE 部署 (推薦用於生產環境)
```bash
# 1) 克隆 repository
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks

# 2) 實際部署到 GKE (完整自動化流程)
bash scripts/actual_deploy.sh

# 或手動分步驟
bash scripts/oneclick_gke_init.sh  # 初始化叢集

# 3) 部署應用
kubectl apply -k cluster/overlays/prod/

# 4) 驗證部署
kubectl get pods -n flowagent
kubectl get svc -n flowagent
```

### 選項 2: Docker Compose 本地部署 (最簡單)
```bash
# 1) 克隆 repository
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks

# 2) (可選) 配置環境變數
cp .env.docker-example .env
# 編輯 .env 如需要

# 3) 啟動所有服務
docker-compose up -d

# 4) 訪問應用
# Next.js Frontend: http://localhost:3000
# MongoDB: localhost:27017

# 查看日誌
docker-compose logs -f
```

📖 完整指南: [Docker Compose 部署指南](./DOCKER_COMPOSE_GUIDE.md)

### 選項 3: 本地開發 (Astro Frontend)
```bash
# 1) 進入 Astro 目錄
cd apps/astro-frontend

# 2) 安裝依賴
npm install

# 3) 啟動開發伺服器
npm run dev
# 訪問 http://localhost:4321

# 4) 或建置生產版本
npm run build
npm run preview
```

### 選項 4: 本地開發 (粒子語言核心)
```bash
# 1) 建立與設定環境
python -m venv .venv && . .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env，填入你的 OPENAI_API_KEY

# 2) 啟動粒子核心演示
cd particle_core
python demo.py demo

# 3) 或啟動 FastAPI 服務
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🎯 本地部署的優勢 / Benefits of Local Deployment

通過在本地克隆並部署此專案，您可以獲得以下優勢：
By cloning and deploying this project locally, you gain the following benefits:

- ✅ **完全控制源代碼** / Full control over source code
  - 可以自由修改和定制功能 / Free to modify and customize features
  - 無需依賴第三方平台 / No dependency on third-party platforms
  
- ✅ **完整的配置管理** / Complete configuration management
  - 自定義環境變數和配置 / Customize environment variables and configs
  - 靈活調整部署架構 / Flexibly adjust deployment architecture
  
- ✅ **數據主權** / Data sovereignty
  - 數據完全存儲在您的基礎設施中 / Data stored entirely in your infrastructure
  - 符合數據隱私和合規要求 / Meet data privacy and compliance requirements
  
- ✅ **不受下載限制** / No download restrictions
  - 避免網絡限制和訪問問題 / Avoid network restrictions and access issues
  - 離線開發和測試 / Offline development and testing
  
- ✅ **完整的開發環境** / Complete development environment
  - 本地調試和測試 / Local debugging and testing
  - 快速迭代和實驗 / Rapid iteration and experimentation

> 💡 如果您需要對其他倉庫（例如 flow-webset）做類似測試，按照同樣的方法克隆即可。
> 
> If you need to test other repositories (e.g., flow-webset) similarly, simply clone them using the same method.

---

## 🗂️ 專案結構 / Project Structure

kubectl create namespace $NS || true
kubectl create namespace monitoring || true
kubectl apply -n monitoring -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml
kubectl apply -f https://github.com/kedacore/keda/releases/latest/download/keda-2.13.1.yaml
```
<<<<<<< 記憶

---

## 目錄說明
- `apps/*`：Mongo、模組、監控、KEDA 等 YAML
- `cluster/overlays/prod/kustomization.yaml`：列出所有資源
- `argocd/app.yaml`：ArgoCD Application（指向你的 GitHub repo）
- `.github/workflows/*`：CI（build/push 映像）與 CD（套用 K8s）
- `scripts/oneclick_gke_init.sh`：Cloud Shell 一鍵初始化腳本

=======
flow-tasks/
├── 📂 apps/                    # Kubernetes 應用部署清單
│   ├── nextjs-frontend/       # Next.js 前端應用
│   ├── astro-frontend/        # Astro 靜態網站前端
│   ├── module-a/              # 主服務模組
│   ├── orchestrator/          # 協調器服務
│   ├── mongodb/               # 資料庫
│   └── monitoring/            # 監控系統
├── 📂 cluster/                # 叢集配置
│   ├── base/                  # 基礎配置
│   └── overlays/              # 環境覆蓋 (prod, monitoring)
├── 📂 argocd/                 # GitOps 配置
├── 📂 particle_core/          # 粒子語言核心系統
├── 📂 pages/                  # Next.js 頁面
├── 📂 lib/                    # Next.js 工具庫
├── 📂 scripts/                # 部署和工具腳本
└── 📚 文檔 / Documentation
    ├── DEPLOYMENT_STRUCTURE_INDEX.md    # 🌍 部署結構索引
    ├── DEPLOYMENT_QUICK_REFERENCE.md    # ⚡ 快速參考
    ├── DEPLOYMENT.md                    # 📖 部署指南
    ├── GKE_MIGRATION.md                 # 🔄 GKE 遷移指南
    └── ARCHITECTURE.md                  # 🏗️ 架構說明
```

---

## 🎯 核心功能 / Core Features

### 1. GKE 微服務部署
- ✅ Next.js Frontend: React 前端應用 (2 replicas, LoadBalancer)
- ✅ Astro Frontend: 靜態網站前端 (2 replicas, LoadBalancer, nginx-based)
- ✅ Module-A: 主服務模組 (2-10 replicas, HPA)
- ✅ Orchestrator: 協調器與入口 (LoadBalancer)
- ✅ MongoDB: 持久化資料庫 (10Gi PVC)
- ✅ Prometheus: 監控系統

### 2. 粒子語言核心 (Particle Language Core)
- ✅ 邏輯種子計算與執行
- ✅ 函數鏈管道處理
- ✅ 記憶封存與還原系統
- ✅ CLI 運行器與模擬器
- 🆕 **並行執行與快取機制** - 增強系統演算能力
- 🆕 **計算原語模組** - 矩陣、統計、圖算法、張量運算
- 🆕 **批次處理** - 高效能批次資料處理

### 3. GitOps + CI/CD
- ✅ GitHub Actions (CI 建置 + CD 部署)
- ✅ ArgoCD (自動同步與自我修復)
- ✅ Kustomize (配置管理)

### 4. AI 超級電腦 (AI SuperComputer)
- ✅ 多 AI 提供者融合系統 (OpenAI, Claude, Gemini)
- 🆕 **進階融合策略** - 投票、集成、自適應融合
- ✅ 莫比烏斯循環 (Möbius Loop)
- ✅ HTTP API 界面

### 5. 企業級長時間作業管理 🆕🆕
- 🆕 **異步任務調度與執行** - 多執行緒/多進程支持
- 🆕 **優先級隊列系統** - CRITICAL > HIGH > NORMAL > LOW
- 🆕 **自動重試機制** - 指數退避策略
- 🆕 **進度追蹤與監控** - 實時狀態更新
- 🆕 **任務持久化** - 跨會話數據恢復
- 🆕 **指標收集** - 成功率、執行時間、吞吐量

---

## 📚 文檔索引 / Documentation Index

| 文檔 | 說明 |
|-----|------|
| 🌍 [部署結構索引](./DEPLOYMENT_STRUCTURE_INDEX.md) | 完整的部署組件、配置和拓撲圖 |
| ⚡ [部署快速參考](./DEPLOYMENT_QUICK_REFERENCE.md) | 快速命令和配置速查表 |
| 📖 [部署指南](./DEPLOYMENT.md) | 詳細的部署步驟和故障排除 |
| 🔄 [GKE 遷移指南](./GKE_MIGRATION.md) | Next.js 從 Vercel 遷移到 GKE |
| 🏗️ [架構說明](./ARCHITECTURE.md) | 系統架構與流程圖 |
| 📊 [結構索引](./STRUCTURE.md) | 專案檔案結構統計 |
| ⚡ [快速開始](./QUICKSTART.md) | 快速部署指南 |
| 🧠 [Particle Core](./particle_core/README.md) | 粒子語言核心系統 |
| 💻 [Codespaces 快速參考](./CODESPACE_QUICK_REFERENCE_ZH.md) | GitHub Codespaces 管理命令 (中文) |
| 📖 [Codespaces 管理指南](./CODESPACE_MANAGEMENT.md) | 完整的 Codespaces 管理文檔 (English) |
| 🚀 [**增強演算能力指南**](./ENHANCED_COMPUTATION_GUIDE.md) | **🆕 並行處理、快取、計算原語、AI融合** |
| 📋 [**企業任務管理指南**](./ENTERPRISE_TASK_MANAGER_GUIDE.md) | **🆕🆕 長時間作業管理、異步執行、任務調度** |

---

## 💻 GitHub Codespaces 管理 / GitHub Codespaces Management

### 快速命令 / Quick Commands

```bash
# 列出所有 Codespaces / List all codespaces
gh codespace list

# 連接到 Codespace / Connect to a codespace
gh codespace code -c CODESPACE_NAME

# 停止 Codespace（節省使用時數）/ Stop codespace (save core hours)
gh codespace stop -c CODESPACE_NAME

# 刪除 Codespace / Delete a codespace
gh codespace delete -c CODESPACE_NAME
```

### 監控工具 / Monitoring Tools

```bash
# 檢查 Codespace 保留狀態 / Check retention status
./scripts/check-codespace-retention.sh

# 詳細監控（含警告）/ Detailed monitoring with warnings
./scripts/monitor-codespaces.sh
```

### 相關文檔 / Related Documentation
- 📖 [中文快速參考 / Chinese Quick Reference](./CODESPACE_QUICK_REFERENCE_ZH.md)
- 📖 [英文完整指南 / English Complete Guide](./CODESPACE_MANAGEMENT.md)
- ⚡ [緊急行動指南 / Emergency Action Guide](./QUICK_ACTION_CODESPACE.md)

---

## 🔧 配置 / Configuration

### GCP 配置參數
```bash
PROJECT_ID=flowmemorysync
REGION=asia-east1
ZONE=asia-east1-a
CLUSTER_NAME=modular-cluster
```

### Container Registry
```
asia-east1-docker.pkg.dev/flowmemorysync/flowagent/
├── nextjs-frontend:latest
├── module-a:latest
└── orchestrator:latest
```

---

相關 CI 工作流程：`.github/workflows/ci.yml` 會自動跑一次 smoke test 並上傳 `data/` 產物。 

---

## 📦 FlowHub Integration Export Package

**新功能！** 完整的 FlowHub 整合套件已準備就緒，可將 Memory Cache 和 Wire-Memory Integration 功能匯出到 dofaromg/flowhub 儲存庫。

### 快速開始

```bash
# 方法 1: 使用 Git Bundle (推薦)
git bundle verify flowhub-integration.bundle
git remote add flow-tasks flowhub-integration.bundle
git fetch flow-tasks
git merge flow-tasks/copilot/update-flow-tasks

# 方法 2: 使用 Patch 檔案
git am patches/*.patch
```

### 套件內容
- 6 個 patch 檔案 (76 KB)
- Git bundle 包含完整提交歷史 (24 KB)
- Wire-Memory Integration 驗證
- Memory Cache Disk Mapping 系統 (LRU 快取，自動持久化)
- 完整測試和文檔

📚 **詳細文檔**：
- [FlowHub 整合套件說明](FLOWHUB_EXPORT_PACKAGE.md)
- [FlowHub 整合指南](FLOWHUB_INTEGRATION_GUIDE.md)


## AMP（Index-only Ledger）

這個倉庫現在包含一個可直接執行的 AMP index-only ledger。以下步驟可以在本地或 CI 中重放：

### 安裝與設定
1. 建立虛擬環境並安裝依賴：
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. 建立設定檔：
   ```bash
   cp config.sample.yaml config.yaml
   ```

### 基本操作（Smoke Test）
```bash
python cli.py init
python cli.py append "A"
python cli.py append "B"
python cli.py snapshot s1
python cli.py verify
python cli.py log --n 10
```

資料會寫入 `data/`：
- `chain.jsonl`: 交易鏈（每筆一行 JSON）。
- `dag_edges.jsonl`: 節點邊索引。
- `refs.json`: 目前 head 與長度。
- `snapshots/*.json`: 命名快照。

### Docker 執行
```bash
docker build -t amp .
docker run --rm -v "$PWD:/data" amp init
docker run --rm -v "$PWD:/data" amp append "hello"
docker run --rm -v "$PWD:/data" amp verify
```

### （可選）Notion 同步
- 需要 `NOTION_TOKEN`（可放在環境變數或 GitHub Secrets）。
- 將 `config.yaml` 中的 `notion` 區段填入 root page/database id。
- 執行：
  ```bash
  python cli.py notion-sync
  ```

### 重播 (Replay)
1. 確認 `data/chain.jsonl` 在工作目錄中。
2. 重新執行 `python cli.py verify` 以驗證鏈條完整性。
3. 使用 `python cli.py log --n 0` 匯出全部事件並據此重建需要的狀態。

### 推送與部署責任說明
- 本倉庫未代替你自動推送或佈署；請依照你的 Git 運維流程自行 push 到遠端或目標環境。
- 如果要在 CI/CD 或 GitOps 環境佈署，將上方產生的 `data/` 內容隨同程式碼一起提交並觸發你的流水線即可。
- 本 README 的指令與 Docker 範例確保本地可重放與驗證，但實際上線發佈仍需由你執行。

### 生命週期自我成長優化沙盒比對
使用沙盒目錄快速驗證「自我成長」變更是否與正式鏈條保持一致：

```bash
# 先複製正式資料到沙盒（預設路徑 data_sandbox，可在 config.yaml 變更）
cp -r data data_sandbox

# 確認沙盒與正式鏈條完全一致
python cli.py sandbox-compare

# 或自訂沙盒目錄
python cli.py sandbox-compare --sandbox-dir /tmp/amp_sandbox
```

該指令會先驗證雙方鏈條，再逐 entry 比對 hash/head，便於在沙盒中試驗優化後再推進正式生命週期。

相關 CI 工作流程：`.github/workflows/ci.yml` 會自動跑一次 smoke test 並上傳 `data/` 產物。
>>>>>>> main
