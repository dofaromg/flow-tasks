# 🚀 FlowAgent 部署快速參考
# FlowAgent Deployment Quick Reference

**快速索引 / Quick Index** - 用於快速查找部署結構位置

---

## 📍 部署檔案位置 / Deployment File Locations

### ⚡ 快速部署 (一鍵)
```bash
📁 scripts/oneclick_gke_init.sh          # 一鍵初始化並部署
```

### 🎯 主要部署目錄

```
📂 apps/                                  # 所有應用部署清單
├── 📂 module-a/                         # 模組 A (主服務)
│   ├── deployment.yaml                  # ⭐ 部署配置
│   ├── service.yaml                     # ⭐ 服務配置
│   ├── hpa.yaml                         # 自動擴展
│   └── kustomization.yaml
│
├── 📂 orchestrator/                     # 協調器 (入口服務)
│   ├── deployment.yaml                  # ⭐ 部署配置
│   ├── service.yaml                     # ⭐ LoadBalancer
│   └── kustomization.yaml
│
├── 📂 mongodb/                          # 資料庫
│   ├── deployment.yaml                  # ⭐ 部署配置
│   ├── service.yaml                     # ⭐ 服務配置
│   ├── pvc.yaml                         # 持久化存儲
│   ├── secret.yaml                      # 🔐 密碼
│   └── kustomization.yaml
│
├── 📂 monitoring/                       # 監控系統
│   ├── prometheus.yaml                  # Prometheus
│   ├── namespace.yaml
│   └── kustomization.yaml
│
└── 📂 keda/                             # 自動擴展
    └── module-a-scaledobject.yaml
```

### 🔧 叢集配置

```
📂 cluster/
├── 📂 base/                             # 基礎配置
│   ├── namespace.yaml                   # flowagent namespace
│   └── kustomization.yaml               # ⭐ 基礎 Kustomize
│
└── 📂 overlays/                         # 環境配置
    ├── 📂 prod/                         # 🌟 生產環境
    │   └── kustomization.yaml           # ⭐ 生產配置集合
    └── 📂 monitoring/                   # 監控環境
        └── kustomization.yaml
```

### 🔄 GitOps 配置

```
📂 argocd/
├── app.yaml                             # ⭐ ArgoCD 應用定義
├── app-multi-env.yaml                   # 多環境配置
└── README.md
```

---

## 🎯 關鍵服務端口 / Key Service Ports

| 服務 / Service | 類型 / Type | 內部端口 / Internal | 外部端口 / External | 命名空間 / Namespace |
|---------------|------------|-------------------|-------------------|-------------------|
| **Orchestrator** | LoadBalancer | 8081 | 80 | flowagent |
| **Module-A** | ClusterIP | 8080 | - | flowagent |
| **MongoDB** | ClusterIP | 27017 | - | flowagent |
| **Prometheus** | ClusterIP | 9090 | - | monitoring |

---

## 📊 部署命令速查 / Deployment Commands Cheatsheet

### 🚀 一鍵部署
```bash
# 最簡單的方式
bash scripts/oneclick_gke_init.sh
```

### 📦 手動部署
```bash
# 1. 設定 GCP 專案
export PROJECT_ID=flowmemorysync
export REGION=asia-east1
export ZONE=asia-east1-a
gcloud config set project $PROJECT_ID

# 2. 取得叢集憑證
gcloud container clusters get-credentials modular-cluster --zone $ZONE

# 3. 部署應用
kubectl apply -k cluster/overlays/prod/
```

### 🔍 驗證部署
```bash
# 查看所有 Pods
kubectl get pods -n flowagent

# 查看所有 Services
kubectl get svc -n flowagent

# 查看所有資源
kubectl get all -n flowagent
```

### 📝 查看日誌
```bash
# Module-A 日誌
kubectl logs -f deployment/module-a -n flowagent

# Orchestrator 日誌
kubectl logs -f deployment/orchestrator -n flowagent

# MongoDB 日誌
kubectl logs -f deployment/mongodb -n flowagent
```

### 🔄 更新部署
```bash
# 重啟 Module-A
kubectl rollout restart deployment/module-a -n flowagent

# 重啟 Orchestrator
kubectl rollout restart deployment/orchestrator -n flowagent

# 查看部署狀態
kubectl rollout status deployment/module-a -n flowagent
```

### 🗑️ 清理部署
```bash
# 刪除所有部署
kubectl delete -k cluster/overlays/prod/

# 只刪除特定應用
kubectl delete -k apps/module-a/
kubectl delete -k apps/orchestrator/
kubectl delete -k apps/mongodb/
```

---

## 🔐 GCP 配置參數 / GCP Configuration

```bash
# 主要參數
PROJECT_ID="flowmemorysync"
REGION="asia-east1"
ZONE="asia-east1-a"
CLUSTER_NAME="modular-cluster"

# Container Registry
REGISTRY="asia-east1-docker.pkg.dev/flowmemorysync/flowagent"

# 命名空間
NAMESPACE="flowagent"
MONITORING_NS="monitoring"
```

---

## 📂 配置檔案對照表 / Configuration File Reference

| 組件 | 部署配置 | 服務配置 | 其他配置 |
|------|---------|---------|---------|
| **Module-A** | `apps/module-a/deployment.yaml` | `apps/module-a/service.yaml` | `apps/module-a/hpa.yaml` |
| **Orchestrator** | `apps/orchestrator/deployment.yaml` | `apps/orchestrator/service.yaml` | - |
| **MongoDB** | `apps/mongodb/deployment.yaml` | `apps/mongodb/service.yaml` | `apps/mongodb/pvc.yaml`<br>`apps/mongodb/secret.yaml` |
| **Prometheus** | `apps/monitoring/prometheus.yaml` | - | `apps/monitoring/namespace.yaml` |

---

## 🎨 部署架構圖 / Deployment Architecture

```
┌────────────────────────────────────────────────┐
│              Internet / 網際網路                 │
└───────────────────┬────────────────────────────┘
                    │
                    ▼
          ┌─────────────────┐
          │  Load Balancer  │  (GCP L4 LB)
          └────────┬────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│          GKE Cluster: modular-cluster            │
│  ┌────────────────────────────────────────────┐ │
│  │   Namespace: flowagent                     │ │
│  │                                            │ │
│  │   ┌────────────┐                          │ │
│  │   │Orchestrator│ (LoadBalancer)           │ │
│  │   │ Port: 80   │                          │ │
│  │   └─────┬──────┘                          │ │
│  │         │                                  │ │
│  │    ┌────┴─────┐                           │ │
│  │    ▼          ▼                           │ │
│  │  ┌─────┐  ┌────────┐                     │ │
│  │  │M-A  │  │MongoDB │                     │ │
│  │  │8080 │  │27017   │                     │ │
│  │  │x2-10│  │+ PVC   │                     │ │
│  │  └─────┘  └────────┘                     │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │   Namespace: monitoring                    │ │
│  │   ┌────────────┐                          │ │
│  │   │ Prometheus │                          │ │
│  │   │ Port: 9090 │                          │ │
│  │   └────────────┘                          │ │
│  └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

---

## 🔄 GitOps 流程 / GitOps Workflow

```
┌────────────┐       ┌──────────┐       ┌─────────┐
│ Git Push   │──────▶│ ArgoCD   │──────▶│   GKE   │
│ (開發者)    │       │ (監控)    │       │ (叢集)   │
└────────────┘       └──────────┘       └─────────┘
     │                     │                  │
     │                     │                  │
     └─────────────────────┴──────────────────┘
              自動同步 / Auto Sync
              自我修復 / Self Heal
```

---

## 📊 資源配置速查 / Resource Configuration Quick View

### Module-A
```yaml
Replicas: 2-10 (auto-scaling)
CPU:      100m-200m
Memory:   128Mi-256Mi
HPA:      CPU 70%, Memory 80%
```

### Orchestrator
```yaml
Replicas: 1
CPU:      100m-200m
Memory:   128Mi-256Mi
```

### MongoDB
```yaml
Replicas: 1
CPU:      100m-500m
Memory:   256Mi-512Mi
Storage:  10Gi (PVC)
```

---

## 🆘 故障排除速查 / Troubleshooting Quick Reference

### Pod 無法啟動
```bash
kubectl describe pod <pod-name> -n flowagent
kubectl get events -n flowagent --sort-by='.lastTimestamp'
```

### 服務無法連接
```bash
kubectl get svc -n flowagent
kubectl get endpoints -n flowagent
```

### 映像拉取失敗
```bash
# 檢查 Artifact Registry 權限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$(gcloud container clusters describe $CLUSTER_NAME \
    --zone=$ZONE --format='value(nodeConfig.serviceAccount)')" \
  --role="roles/artifactregistry.reader"
```

### 查看資源使用
```bash
kubectl top pods -n flowagent
kubectl top nodes
```

---

## 📚 相關文檔索引 / Related Documentation Index

| 文檔 | 說明 | 路徑 |
|-----|------|------|
| 🌍 **部署結構索引** | 完整部署結構說明 | `DEPLOYMENT_STRUCTURE_INDEX.md` |
| 📖 **部署指南** | 詳細部署步驟 | `DEPLOYMENT.md` |
| 🏗️ **架構說明** | 系統架構與流程圖 | `ARCHITECTURE.md` |
| 📊 **結構索引** | 專案檔案結構 | `STRUCTURE.md` |
| ⚡ **快速開始** | 快速部署指南 | `QUICKSTART.md` |
| 🔄 **ArgoCD** | GitOps 配置 | `argocd/README.md` |

---

## 💡 常見任務快速指令 / Common Tasks Quick Commands

### 獲取外部 IP
```bash
kubectl get svc orchestrator -n flowagent -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### 測試服務健康
```bash
EXTERNAL_IP=$(kubectl get svc orchestrator -n flowagent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$EXTERNAL_IP/health
```

### 查看 HPA 狀態
```bash
kubectl get hpa -n flowagent
kubectl describe hpa module-a-hpa -n flowagent
```

### 連接到 MongoDB
```bash
kubectl port-forward svc/mongodb 27017:27017 -n flowagent
# 然後使用: mongosh "mongodb://admin:<password>@localhost:27017"
```

### 訪問 Prometheus
```bash
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
# 瀏覽器: http://localhost:9090
```

### 查看 ArgoCD 應用狀態
```bash
kubectl get application -n argocd
kubectl describe application flowagent -n argocd
```

---

## 🎯 下一步建議 / Next Steps

1. ✅ 完成初始部署
2. ✅ 驗證所有服務正常運行
3. ✅ 修改 MongoDB 預設密碼
4. ✅ 配置域名和 SSL 憑證
5. ✅ 設定監控告警
6. ✅ 配置備份策略
7. ✅ 整合 CI/CD 流程
8. ✅ 整合 particle_core 系統

---

**版本 / Version**: v3.0.0  
**最後更新 / Last Updated**: 2026-02-04  
**維護者 / Maintainer**: FlowAgent Team

---

**🌟 快速提示**: 
- 使用 `bash scripts/oneclick_gke_init.sh` 進行一鍵部署
- 所有主要配置都在 `cluster/overlays/prod/kustomization.yaml`
- 使用 ArgoCD 進行 GitOps 自動化部署
