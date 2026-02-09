# 🌍 FlowAgent 地球結構部署索引
# FlowAgent Earth Structure Deployment Index

**生成時間 / Generated**: 2026-02-04  
**版本 / Version**: v3.0.0  
**專案 / Project**: FlowAgent GKE Starter

---

## 📋 概覽 / Overview

本文件提供 FlowAgent 完整的部署結構索引，讓您可以快速了解整個"地球結構"部署架構。  
This document provides a complete deployment structure index for FlowAgent, allowing you to quickly understand the entire "Earth Structure" deployment architecture.

---

## 🗺️ 部署結構地圖 / Deployment Structure Map

```
flow-tasks/
├── 📦 apps/                          # 應用程式部署清單 / Application Deployments
│   ├── keda/                         # KEDA 自動擴展 / Auto-scaling
│   │   └── module-a-scaledobject.yaml
│   ├── module-a/                     # 模組 A 服務 / Module A Service
│   │   ├── deployment.yaml           # 部署配置 (2 replicas)
│   │   ├── service.yaml              # 服務定義 (ClusterIP:8080)
│   │   ├── hpa.yaml                  # 自動擴展配置
│   │   └── kustomization.yaml
│   ├── orchestrator/                 # 協調器服務 / Orchestrator Service
│   │   ├── deployment.yaml           # 部署配置 (1 replica)
│   │   ├── service.yaml              # 服務定義 (LoadBalancer:80)
│   │   └── kustomization.yaml
│   ├── mongodb/                      # MongoDB 資料庫 / Database
│   │   ├── deployment.yaml           # 部署配置
│   │   ├── service.yaml              # 服務定義 (ClusterIP:27017)
│   │   ├── pvc.yaml                  # 持久化存儲 (10Gi)
│   │   ├── secret.yaml               # 密碼配置
│   │   └── kustomization.yaml
│   └── monitoring/                   # 監控系統 / Monitoring
│       ├── prometheus.yaml           # Prometheus 配置
│       ├── namespace.yaml
│       └── kustomization.yaml
│
├── 🔧 cluster/                       # 叢集配置 / Cluster Configuration
│   ├── base/                         # 基礎配置 / Base Config
│   │   ├── namespace.yaml            # flowagent namespace
│   │   └── kustomization.yaml
│   └── overlays/                     # 環境覆蓋配置 / Environment Overlays
│       ├── prod/                     # 生產環境 / Production
│       │   └── kustomization.yaml    # 生產配置集合
│       └── monitoring/               # 監控環境 / Monitoring
│           └── kustomization.yaml    # 監控配置集合
│
├── 🔄 argocd/                        # GitOps 配置 / GitOps Config
│   ├── app.yaml                      # ArgoCD 應用定義
│   ├── app-multi-env.yaml            # 多環境配置
│   └── README.md
│
└── 📜 scripts/                       # 部署腳本 / Deployment Scripts
    ├── oneclick_gke_init.sh          # 一鍵初始化腳本
    └── validate_deployment.sh        # 部署驗證腳本
```

---

## 🎯 核心部署組件 / Core Deployment Components

### 1. 應用層 / Application Layer

#### Module-A (模組 A)
- **位置 / Location**: `apps/module-a/`
- **功能 / Function**: 主要服務模組
- **副本數 / Replicas**: 2 (可自動擴展至 10)
- **端口 / Port**: 8080
- **類型 / Type**: ClusterIP Service
- **自動擴展 / Auto-scaling**: 
  - CPU > 70% 觸發擴展
  - Memory > 80% 觸發擴展
  - 最小: 2, 最大: 10

#### Orchestrator (協調器)
- **位置 / Location**: `apps/orchestrator/`
- **功能 / Function**: 服務協調與路由
- **副本數 / Replicas**: 1
- **端口 / Port**: 8081 (對外: 80)
- **類型 / Type**: LoadBalancer Service
- **對外訪問 / External Access**: ✅ (通過 GCP Load Balancer)

#### MongoDB (資料庫)
- **位置 / Location**: `apps/mongodb/`
- **功能 / Function**: 持久化資料存儲
- **副本數 / Replicas**: 1
- **端口 / Port**: 27017
- **類型 / Type**: ClusterIP Service
- **存儲 / Storage**: 10Gi PersistentVolume
- **密碼 / Credentials**: 存儲在 `secret.yaml`

### 2. 監控層 / Monitoring Layer

#### Prometheus
- **位置 / Location**: `apps/monitoring/`
- **功能 / Function**: 指標收集與監控
- **命名空間 / Namespace**: monitoring
- **端口 / Port**: 9090
- **抓取間隔 / Scrape Interval**: 15s

### 3. 自動擴展層 / Auto-scaling Layer

#### KEDA (Kubernetes Event-Driven Autoscaling)
- **位置 / Location**: `apps/keda/`
- **功能 / Function**: 事件驅動的自動擴展
- **監控目標 / Targets**: module-a

---

## 🚀 部署方式 / Deployment Methods

### 方式 1: 直接部署 / Direct Deployment
```bash
# 使用 kubectl + kustomize 直接部署
kubectl apply -k cluster/overlays/prod/

# 驗證部署
kubectl get pods -n flowagent
kubectl get svc -n flowagent
```

### 方式 2: GitOps (ArgoCD)
```bash
# 安裝 ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 部署應用
kubectl apply -f argocd/app.yaml

# 同步應用
argocd app sync flowagent
```

### 方式 3: 一鍵初始化 / One-Click Init
```bash
# 使用初始化腳本（推薦）
bash scripts/oneclick_gke_init.sh
```

### 方式 4: GitHub Actions CI/CD
- **CI Build**: `.github/workflows/ci-build.yml`
  - 建置 Docker 映像
  - 推送到 Artifact Registry
- **CD Deploy**: `.github/workflows/cd-deploy.yml`
  - 自動部署到 GKE

---

## 📊 部署拓撲 / Deployment Topology

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │  GCP Load Balancer   │  (External IP)
                └──────────┬───────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                  GKE Cluster: modular-cluster                 │
│  Region: asia-east1  │  Zone: asia-east1-a                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Namespace: flowagent                                │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │                                                      │    │
│  │  ┌─────────────────┐      ┌──────────────────┐    │    │
│  │  │  Orchestrator   │─────▶│   Module-A       │    │    │
│  │  │  (LoadBalancer) │      │   (ClusterIP)    │    │    │
│  │  │  Port: 80       │      │   Port: 8080     │    │    │
│  │  │  Replicas: 1    │      │   Replicas: 2-10 │    │    │
│  │  └─────────┬───────┘      └──────────────────┘    │    │
│  │            │                                        │    │
│  │            │                                        │    │
│  │            ▼                                        │    │
│  │  ┌─────────────────┐                              │    │
│  │  │    MongoDB      │                              │    │
│  │  │   (ClusterIP)   │                              │    │
│  │  │  Port: 27017    │                              │    │
│  │  │  + PVC 10Gi     │                              │    │
│  │  └─────────────────┘                              │    │
│  │                                                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Namespace: monitoring                               │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │                                                      │    │
│  │  ┌─────────────────┐                               │    │
│  │  │   Prometheus    │  ◀─── Scrapes metrics         │    │
│  │  │   Port: 9090    │       from all pods           │    │
│  │  └─────────────────┘                               │    │
│  │                                                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 關鍵配置檔案 / Key Configuration Files

### Kustomization 主檔案
- **生產環境**: `cluster/overlays/prod/kustomization.yaml`
  - 包含所有生產環境配置
  - 映像標籤管理
  - 命名空間設定

- **監控環境**: `cluster/overlays/monitoring/kustomization.yaml`
  - Prometheus 配置
  - 監控命名空間

### 部署清單
每個應用都包含:
- `deployment.yaml` - Pod 部署配置
- `service.yaml` - Service 定義
- `kustomization.yaml` - Kustomize 配置

### GitOps 配置
- `argocd/app.yaml` - ArgoCD 應用定義
  - 自動同步: ✅
  - 自我修復: ✅
  - Repository: github.com/dofaromg/flow-tasks
  - Path: cluster/overlays/prod

---

## 🔐 環境變數與密鑰 / Environment Variables & Secrets

### GCP 配置
```bash
PROJECT_ID=flowmemorysync
REGION=asia-east1
ZONE=asia-east1-a
CLUSTER_NAME=modular-cluster
```

### MongoDB 密碼
- **位置**: `apps/mongodb/secret.yaml`
- **⚠️ 重要**: 生產環境請務必修改預設密碼

### Container Registry
```
asia-east1-docker.pkg.dev/flowmemorysync/flowagent/
├── module-a:latest
└── orchestrator:latest
```

---

## 📈 資源配置 / Resource Configuration

### Module-A
```yaml
Resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"

HPA:
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### Orchestrator
```yaml
Resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

### MongoDB
```yaml
Resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"

Storage:
  size: 10Gi
  storageClass: standard-rwo
```

---

## 🔍 驗證部署 / Verify Deployment

### 檢查所有 Pods
```bash
kubectl get pods -n flowagent
```

預期輸出:
```
NAME                            READY   STATUS    RESTARTS   AGE
module-a-xxxxxxxxx-xxxxx        1/1     Running   0          5m
module-a-xxxxxxxxx-xxxxx        1/1     Running   0          5m
orchestrator-xxxxxxxxx-xxxxx    1/1     Running   0          5m
mongodb-xxxxxxxxx-xxxxx         1/1     Running   0          5m
```

### 檢查所有 Services
```bash
kubectl get svc -n flowagent
```

預期輸出:
```
NAME           TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE
module-a       ClusterIP      10.x.x.x        <none>          8080/TCP       5m
orchestrator   LoadBalancer   10.x.x.x        34.x.x.x        80:xxxxx/TCP   5m
mongodb        ClusterIP      10.x.x.x        <none>          27017/TCP      5m
```

### 測試服務連接
```bash
# 獲取外部 IP
EXTERNAL_IP=$(kubectl get svc orchestrator -n flowagent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# 測試健康檢查
curl http://$EXTERNAL_IP/health
```

---

## 📚 相關文檔 / Related Documentation

1. **部署指南**: [DEPLOYMENT.md](./DEPLOYMENT.md)
   - 詳細的部署步驟
   - 一鍵初始化腳本
   - 故障排除

2. **架構說明**: [ARCHITECTURE.md](./ARCHITECTURE.md)
   - 系統架構圖
   - 部署流程
   - 網路拓撲

3. **結構索引**: [STRUCTURE.md](./STRUCTURE.md)
   - 專案檔案結構
   - 代碼統計
   - 模組說明

4. **ArgoCD 配置**: [argocd/README.md](./argocd/README.md)
   - GitOps 配置
   - 自動同步設定

5. **快速開始**: [QUICKSTART.md](./QUICKSTART.md)
   - 快速部署指南

---

## 🎓 快速參考 / Quick Reference

### 常用命令 / Common Commands

```bash
# 查看所有資源
kubectl get all -n flowagent

# 查看日誌
kubectl logs -f deployment/module-a -n flowagent
kubectl logs -f deployment/orchestrator -n flowagent
kubectl logs -f deployment/mongodb -n flowagent

# 進入 Pod
kubectl exec -it deployment/module-a -n flowagent -- sh

# 端口轉發
kubectl port-forward svc/mongodb 27017:27017 -n flowagent
kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# 刪除部署
kubectl delete -k cluster/overlays/prod/

# 重新部署
kubectl rollout restart deployment/module-a -n flowagent
```

### 目錄快捷方式 / Directory Shortcuts

- 應用部署: `cd apps/`
- 叢集配置: `cd cluster/`
- ArgoCD: `cd argocd/`
- 腳本: `cd scripts/`

---

## 💡 提示與最佳實踐 / Tips & Best Practices

1. ✅ **使用 GitOps (ArgoCD)** 進行生產部署
2. ✅ **修改預設密碼** (MongoDB)
3. ✅ **配置資源限制** 避免資源耗盡
4. ✅ **設定監控告警** 及時發現問題
5. ✅ **定期備份** MongoDB 資料
6. ✅ **使用命名空間** 隔離不同環境
7. ✅ **啟用自動擴展** 應對流量波動

---

## 🆘 需要幫助? / Need Help?

- 📖 閱讀 [DEPLOYMENT.md](./DEPLOYMENT.md) 了解詳細步驟
- 🔍 查看 [故障排除](./DEPLOYMENT.md#-故障排除) 章節
- 💬 提交 GitHub Issue
- 📧 聯絡維護者

---

**更新日期 / Last Updated**: 2026-02-04  
**維護者 / Maintainer**: FlowAgent Team  
**授權 / License**: MIT

---

此文件提供了完整的 FlowAgent "地球結構" 部署索引，讓您可以清楚看到所有部署組件和配置。  
This document provides a complete FlowAgent "Earth Structure" deployment index, allowing you to clearly see all deployment components and configurations.
