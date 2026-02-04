# FlowAgent — GKE Starter with Particle Language Core
# FlowAgent — GKE 啟動器與粒子語言核心

版本 / Version: v1.0.0  •  更新時間 / Updated: 2026-02-04

## 🌍 部署結構索引 / Deployment Structure Index

**⭐ 快速查看完整的"地球結構"部署架構 / Quick View Complete "Earth Structure" Deployment:**

- 📖 [**部署結構索引 / Deployment Structure Index**](./DEPLOYMENT_STRUCTURE_INDEX.md) - 完整的部署組件、配置和拓撲圖
- ⚡ [**部署快速參考 / Deployment Quick Reference**](./DEPLOYMENT_QUICK_REFERENCE.md) - 快速命令和配置速查表
- 🚀 [**部署指南 / Deployment Guide**](./DEPLOYMENT.md) - 詳細的部署步驟和故障排除
- 🏗️ [**架構說明 / Architecture**](./ARCHITECTURE.md) - 系統架構與流程圖

### 🎯 一鍵部署 / One-Click Deployment
```bash
# 快速開始 - 一鍵初始化 GKE 叢集並部署所有服務
bash scripts/oneclick_gke_init.sh

# 或使用 kubectl + kustomize
kubectl apply -k cluster/overlays/prod/
```

---

## 📦 專案概覽 / Project Overview

這個專案整合了：
This project integrates:

1) **GKE 部署架構** - 完整的 Kubernetes 微服務部署
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

> 注意：本專案包含完整的 GKE 部署配置和粒子語言核心系統。
> Note: This project includes complete GKE deployment configurations and the Particle Language Core system.

---

## 快速開始 / Quick Start

### 選項 1: GKE 部署 (推薦用於生產環境)
```bash
# 1) 克隆 repository
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks

# 2) 一鍵初始化 GKE 叢集
bash scripts/oneclick_gke_init.sh

# 3) 部署應用
kubectl apply -k cluster/overlays/prod/

# 4) 驗證部署
kubectl get pods -n flowagent
kubectl get svc -n flowagent
```

### 選項 2: 本地開發 (粒子語言核心)
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

### 選項 3: 冷儲存管理 (新增功能)
```bash
# 掃描需要歸檔的檔案
python particle_core/src/cold_storage_manager.py scan

# 歸檔檔案到冷儲存（保留原檔案，不刪除）
python scripts/archive_to_cold_storage.py

# 查看統計資訊
python particle_core/src/cold_storage_manager.py stats

# 詳細說明
查看: COLD_STORAGE_QUICKSTART.md
```

---

## 🗂️ 專案結構 / Project Structure

```
flow-tasks/
├── 📂 apps/                    # Kubernetes 應用部署清單
│   ├── module-a/              # 主服務模組
│   ├── orchestrator/          # 協調器服務
│   ├── mongodb/               # 資料庫
│   └── monitoring/            # 監控系統
├── 📂 cluster/                # 叢集配置
│   ├── base/                  # 基礎配置
│   └── overlays/              # 環境覆蓋 (prod, monitoring)
├── 📂 argocd/                 # GitOps 配置
├── 📂 particle_core/          # 粒子語言核心系統
├── 📂 scripts/                # 部署和工具腳本
└── 📚 文檔 / Documentation
    ├── DEPLOYMENT_STRUCTURE_INDEX.md    # 🌍 部署結構索引
    ├── DEPLOYMENT_QUICK_REFERENCE.md    # ⚡ 快速參考
    ├── DEPLOYMENT.md                    # 📖 部署指南
    └── ARCHITECTURE.md                  # 🏗️ 架構說明
```

---

## 🎯 核心功能 / Core Features

### 1. GKE 微服務部署
- ✅ Module-A: 主服務模組 (2-10 replicas, HPA)
- ✅ Orchestrator: 協調器與入口 (LoadBalancer)
- ✅ MongoDB: 持久化資料庫 (10Gi PVC)
- ✅ Prometheus: 監控系統

### 2. 粒子語言核心 (Particle Language Core)
- ✅ 邏輯種子計算與執行
- ✅ 函數鏈管道處理
- ✅ 記憶封存與還原系統
- ✅ CLI 運行器與模擬器

### 3. GitOps + CI/CD
- ✅ GitHub Actions (CI 建置 + CD 部署)
- ✅ ArgoCD (自動同步與自我修復)
- ✅ Kustomize (配置管理)

---

## 📚 文檔索引 / Documentation Index

| 文檔 | 說明 |
|-----|------|
| 🌍 [部署結構索引](./DEPLOYMENT_STRUCTURE_INDEX.md) | 完整的部署組件、配置和拓撲圖 |
| ⚡ [部署快速參考](./DEPLOYMENT_QUICK_REFERENCE.md) | 快速命令和配置速查表 |
| 📖 [部署指南](./DEPLOYMENT.md) | 詳細的部署步驟和故障排除 |
| 🏗️ [架構說明](./ARCHITECTURE.md) | 系統架構與流程圖 |
| 📊 [結構索引](./STRUCTURE.md) | 專案檔案結構統計 |
| ⚡ [快速開始](./QUICKSTART.md) | 快速部署指南 |
| 🧠 [Particle Core](./particle_core/README.md) | 粒子語言核心系統 |

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
├── module-a:latest
└── orchestrator:latest
```

---

