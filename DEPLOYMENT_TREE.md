# 🌲 FlowAgent 部署目錄樹狀結構
# FlowAgent Deployment Directory Tree

**更新時間 / Updated**: 2026-02-04

此文件以樹狀結構展示 FlowAgent 的完整部署配置目錄，讓您可以清楚看到所有部署文件的位置。  
This file shows the complete deployment configuration directory of FlowAgent in a tree structure.

---

## 📂 完整部署目錄結構 / Complete Deployment Directory Structure

```
flow-tasks/
│
├── 🚀 apps/                                    # 應用程式部署清單目錄
│   │                                           # Application Deployment Manifests
│   │
│   ├── 📦 keda/                               # KEDA 自動擴展配置
│   │   └── module-a-scaledobject.yaml         # Module-A 擴展對象
│   │
│   ├── 📦 module-a/                           # Module-A 主服務
│   │   ├── deployment.yaml                    # 部署配置 (2 replicas)
│   │   ├── service.yaml                       # Service (ClusterIP, Port 8080)
│   │   ├── hpa.yaml                           # 水平自動擴展配置
│   │   └── kustomization.yaml                 # Kustomize 配置
│   │
│   ├── 📦 orchestrator/                       # Orchestrator 協調器服務
│   │   ├── deployment.yaml                    # 部署配置 (1 replica)
│   │   ├── service.yaml                       # Service (LoadBalancer, Port 80)
│   │   └── kustomization.yaml                 # Kustomize 配置
│   │
│   ├── 📦 mongodb/                            # MongoDB 資料庫
│   │   ├── deployment.yaml                    # 部署配置 (1 replica)
│   │   ├── service.yaml                       # Service (ClusterIP, Port 27017)
│   │   ├── pvc.yaml                           # PersistentVolumeClaim (10Gi)
│   │   ├── secret.yaml                        # 🔐 密碼配置
│   │   └── kustomization.yaml                 # Kustomize 配置
│   │
│   └── 📦 monitoring/                         # 監控系統
│       ├── prometheus.yaml                    # Prometheus 配置
│       ├── namespace.yaml                     # monitoring namespace
│       └── kustomization.yaml                 # Kustomize 配置
│
├── 🔧 cluster/                                # 叢集配置目錄
│   │                                          # Cluster Configuration
│   │
│   ├── 📂 base/                              # 基礎配置
│   │   ├── namespace.yaml                    # flowagent namespace 定義
│   │   └── kustomization.yaml                # 基礎 Kustomize 配置
│   │
│   └── 📂 overlays/                          # 環境覆蓋配置
│       │
│       ├── 📂 prod/                          # 🌟 生產環境配置
│       │   └── kustomization.yaml            # 生產環境配置集合
│       │                                     # (包含所有應用的引用)
│       │
│       └── 📂 monitoring/                    # 監控環境配置
│           └── kustomization.yaml            # 監控環境配置集合
│
├── 🔄 argocd/                                # GitOps 配置目錄
│   │                                         # GitOps Configuration
│   │
│   ├── app.yaml                              # ⭐ ArgoCD 應用定義 (主要)
│   │                                         # - 自動同步: enabled
│   │                                         # - 自我修復: enabled
│   │                                         # - Repository: github.com/dofaromg/flow-tasks
│   │                                         # - Path: cluster/overlays/prod
│   │
│   ├── app-multi-env.yaml                    # 多環境 ArgoCD 配置
│   └── README.md                             # ArgoCD 使用說明
│
├── 📜 scripts/                               # 部署腳本目錄
│   │                                         # Deployment Scripts
│   │
│   ├── oneclick_gke_init.sh                  # ⚡ 一鍵初始化腳本
│   │                                         # (GKE 叢集建立與初始化)
│   │
│   └── validate_deployment.sh                # 部署驗證腳本
│                                             # (YAML 語法與配置檢查)
│
├── 🔐 .github/                               # GitHub 配置目錄
│   │
│   └── workflows/                            # CI/CD 工作流程
│       ├── ci-build.yml                      # CI: 建置 & 推送映像
│       │                                     # - 建置 Docker 映像
│       │                                     # - 推送到 Artifact Registry
│       │
│       └── cd-deploy.yml                     # CD: 部署到 GKE
│                                             # - 取得 GKE 憑證
│                                             # - Kustomize build
│                                             # - kubectl apply
│
├── 🧠 particle_core/                         # 粒子語言核心系統
│   │                                         # Particle Language Core
│   │
│   ├── src/                                  # 核心源碼模組
│   │   ├── logic_pipeline.py                # 邏輯管道
│   │   ├── cli_runner.py                    # CLI 運行器
│   │   ├── rebuild_fn.py                    # 重建功能
│   │   └── memory_archive_seed.py           # 記憶封存
│   │
│   ├── config/                               # 配置文件
│   │   └── core_config.json                 # 核心配置
│   │
│   ├── docs/                                 # 文檔 (中英雙語)
│   ├── examples/                             # 使用範例
│   └── demo.py                               # 演示程式
│
└── 📚 Documentation/                         # 📚 文檔目錄
    │
    ├── 🌍 DEPLOYMENT_STRUCTURE_INDEX.md     # ⭐ 部署結構索引 (本文件的詳細版)
    │                                         # - 完整部署架構說明
    │                                         # - 部署拓撲圖
    │                                         # - 組件詳細資訊
    │
    ├── ⚡ DEPLOYMENT_QUICK_REFERENCE.md      # ⭐ 部署快速參考
    │                                         # - 快速命令速查
    │                                         # - 配置參數速查
    │                                         # - 故障排除速查
    │
    ├── 📖 DEPLOYMENT.md                      # 完整部署指南
    │                                         # - 詳細部署步驟
    │                                         # - 一鍵初始化說明
    │                                         # - 故障排除
    │
    ├── 🏗️ ARCHITECTURE.md                    # 系統架構說明
    │                                         # - 部署流程圖
    │                                         # - 網路架構
    │                                         # - 服務架構
    │
    ├── 📊 STRUCTURE.md                       # 專案結構索引
    │                                         # - 檔案統計
    │                                         # - 模組說明
    │
    ├── 🌲 DEPLOYMENT_TREE.md                 # 部署目錄樹狀結構 (本文件)
    │
    ├── ⚡ QUICKSTART.md                      # 快速開始指南
    │
    └── 📝 README.md                          # 專案主文檔

```

---

## 🎯 關鍵文件說明 / Key Files Description

### ⭐ 最重要的配置文件 / Most Important Configuration Files

1. **cluster/overlays/prod/kustomization.yaml**
   - 📍 位置: `cluster/overlays/prod/kustomization.yaml`
   - 🎯 功能: 生產環境配置集合，包含所有應用的引用
   - 📝 說明: 這是部署的主要入口點

2. **argocd/app.yaml**
   - 📍 位置: `argocd/app.yaml`
   - 🎯 功能: ArgoCD 應用定義，用於 GitOps 自動部署
   - 📝 說明: 配置自動同步和自我修復

3. **scripts/oneclick_gke_init.sh**
   - 📍 位置: `scripts/oneclick_gke_init.sh`
   - 🎯 功能: 一鍵初始化 GKE 叢集
   - 📝 說明: 最簡單的部署方式

### 📦 應用部署文件 / Application Deployment Files

每個應用目錄都包含以下文件:
- `deployment.yaml` - Pod 部署配置
- `service.yaml` - Service 定義
- `kustomization.yaml` - Kustomize 配置

特殊文件:
- `apps/mongodb/pvc.yaml` - MongoDB 持久化存儲
- `apps/mongodb/secret.yaml` - MongoDB 密碼 (🔐 生產環境請修改)
- `apps/module-a/hpa.yaml` - Module-A 自動擴展配置

---

## 🚀 快速導航 / Quick Navigation

### 要查看完整的部署配置？
👉 前往 `cluster/overlays/prod/kustomization.yaml`

### 要了解每個服務的詳細配置？
👉 前往 `apps/` 目錄，每個服務都有獨立的子目錄

### 要使用 GitOps 部署？
👉 查看 `argocd/app.yaml` 和 `argocd/README.md`

### 要快速部署？
👉 執行 `bash scripts/oneclick_gke_init.sh`

### 要了解部署架構？
👉 閱讀 [DEPLOYMENT_STRUCTURE_INDEX.md](./DEPLOYMENT_STRUCTURE_INDEX.md)

### 要查看快速命令？
👉 閱讀 [DEPLOYMENT_QUICK_REFERENCE.md](./DEPLOYMENT_QUICK_REFERENCE.md)

---

## 📊 目錄統計 / Directory Statistics

```
部署配置文件總數:
- Apps 目錄: 5 個應用 (module-a, orchestrator, mongodb, monitoring, keda)
- Deployment YAML: 4 個
- Service YAML: 4 個
- Kustomization YAML: 8 個
- ArgoCD 配置: 2 個
- 部署腳本: 2 個
```

---

## 🔍 如何使用此文件 / How to Use This File

1. **快速查找**: 使用此樹狀結構快速找到需要的配置文件位置
2. **理解結構**: 了解整個部署配置的組織方式
3. **導航指南**: 作為探索專案的地圖
4. **新手友好**: 對新加入專案的開發者特別有幫助

---

## 💡 提示 / Tips

- 🌟 所有部署配置都在 `apps/` 和 `cluster/` 目錄
- 🚀 使用 `kubectl apply -k cluster/overlays/prod/` 進行部署
- 🔄 使用 ArgoCD 進行自動化 GitOps 部署
- 📖 查看 [DEPLOYMENT.md](./DEPLOYMENT.md) 了解詳細步驟
- ⚡ 查看 [DEPLOYMENT_QUICK_REFERENCE.md](./DEPLOYMENT_QUICK_REFERENCE.md) 獲取快速命令

---

**版本 / Version**: v3.0.0  
**最後更新 / Last Updated**: 2026-02-04  
**維護者 / Maintainer**: FlowAgent Team

---

此樹狀結構讓您可以清楚看到 FlowAgent "地球結構" 部署的所有配置文件位置。  
This tree structure allows you to clearly see the location of all configuration files for FlowAgent "Earth Structure" deployment.
