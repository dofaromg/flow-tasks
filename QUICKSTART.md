# FlowAgent GKE 部署快速參考

## 🚀 快速開始

### 1. 一鍵部署 (推薦)

```bash
# 克隆 repository
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks

# 初始化 GKE 叢集
bash scripts/oneclick_gke_init.sh

# 部署應用程式
kubectl apply -k cluster/overlays/prod

# 部署監控 (可選)
kubectl apply -k cluster/overlays/monitoring
```

### 2. 驗證部署

```bash
# 驗證配置檔案
bash scripts/validate_deployment.sh

# 查看 pods
kubectl get pods -n flowagent

# 查看 services
kubectl get svc -n flowagent

# 取得 Orchestrator 外部 IP
kubectl get svc orchestrator -n flowagent -w
```

## 📦 部署架構

```
┌─────────────────────────────────────────────────┐
│              LoadBalancer (外部訪問)              │
│                 Orchestrator                     │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌───────▼────────┐
│   Module-A     │   │    MongoDB     │
│  (2 replicas)  │   │  (1 replica)   │
│  + HPA (2-10)  │   │   + PVC 10Gi   │
└────────────────┘   └────────────────┘

監控 namespace:
┌────────────────┐
│  Prometheus    │
│  (monitoring)  │
└────────────────┘
```

## 🔧 常用命令

### 查看狀態
```bash
# 所有資源
kubectl get all -n flowagent

# Deployment 狀態
kubectl rollout status deployment/module-a -n flowagent
kubectl rollout status deployment/orchestrator -n flowagent

# 查看日誌
kubectl logs -f deployment/module-a -n flowagent
kubectl logs -f deployment/orchestrator -n flowagent
```

### 測試服務
```bash
# Port forward Module-A
kubectl port-forward svc/module-a 8080:8080 -n flowagent
curl http://localhost:8080/health

# Port forward Orchestrator
kubectl port-forward svc/orchestrator 8081:80 -n flowagent
curl http://localhost:8081/health

# 測試 Orchestrator
curl -X POST http://localhost:8081/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"task": "test"}'
```

### 更新部署
```bash
# 修改配置後重新部署
kubectl apply -k cluster/overlays/prod

# 重啟 deployment
kubectl rollout restart deployment/module-a -n flowagent
kubectl rollout restart deployment/orchestrator -n flowagent

# 擴展 replicas
kubectl scale deployment/module-a --replicas=3 -n flowagent
```

### 查看監控
```bash
# Port forward Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# 訪問 http://localhost:9090
```

## 🎯 三種部署方式

### 方式 A: Kustomize (手動)
```bash
kubectl apply -k cluster/overlays/prod
kubectl apply -k cluster/overlays/monitoring
```

### 方式 B: ArgoCD (GitOps)
```bash
# 安裝 ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 部署應用
kubectl apply -f argocd/app.yaml

# 取得密碼
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# 訪問 UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### 方式 C: GitHub Actions (CI/CD)
```bash
# 1. 設定 GitHub Secrets:
#    - GCP_WIF_PROVIDER
#    - GCP_DEPLOYER_SA

# 2. 推送到 main 分支
git push origin main

# 3. GitHub Actions 會自動:
#    - 建置 Docker 映像
#    - 推送到 Artifact Registry
#    - 部署到 GKE
```

## 🔍 故障排除

### Pods 無法啟動
```bash
# 查看 pod 詳情
kubectl describe pod <pod-name> -n flowagent

# 查看事件
kubectl get events -n flowagent --sort-by='.lastTimestamp'

# 查看日誌
kubectl logs <pod-name> -n flowagent
```

### 映像拉取失敗
```bash
# 確保節點有權限訪問 Artifact Registry
gcloud projects add-iam-policy-binding flowmemorysync \
  --member="serviceAccount:$(gcloud container clusters describe modular-cluster \
    --zone=asia-east1-a --format='value(nodeConfig.serviceAccount)')" \
  --role="roles/artifactregistry.reader"
```

### Service 無法連接
```bash
# 測試內部連接
kubectl run test-pod --rm -i --tty --image=busybox -n flowagent -- sh
# 在 pod 中:
wget -O- http://module-a:8080/health
wget -O- http://mongodb:27017
```

## 📊 資源清單

### Namespaces
- `flowagent`: 應用程式
- `monitoring`: 監控系統

### Services
- `module-a`: ClusterIP (8080)
- `orchestrator`: LoadBalancer (80 -> 8081)
- `mongodb`: ClusterIP (27017)
- `prometheus`: ClusterIP (9090)

### Deployments
- `module-a`: 2 replicas (HPA: 2-10)
- `orchestrator`: 1 replica
- `mongodb`: 1 replica
- `prometheus`: 1 replica

### Storage
- `mongodb-pvc`: 10Gi (standard-rwo)

## 🔐 安全性檢查清單

- [ ] 修改 MongoDB 密碼 (`apps/mongodb/secret.yaml`)
- [ ] 設定 RBAC 權限
- [ ] 配置 NetworkPolicy (可選)
- [ ] 啟用 Pod Security Standards
- [ ] 使用 Secret Manager 管理敏感資訊
- [ ] 定期更新基礎映像
- [ ] 配置 SSL/TLS 憑證

## 📚 相關文檔

- [DEPLOYMENT.md](DEPLOYMENT.md) - 完整部署指南
- [apps/README.md](apps/README.md) - 應用程式說明
- [argocd/README.md](argocd/README.md) - ArgoCD 配置
- [README.md](README.md) - 專案概覽

## 💡 提示

1. **首次部署建議使用 Cloud Shell**，避免本地環境問題
2. **生產環境請務必修改 MongoDB 密碼**
3. **建議使用 GitOps (ArgoCD)** 進行持續部署
4. **定期備份 MongoDB 資料**
5. **監控資源使用情況**，適時調整 HPA 和資源限制

## 🔗 有用連結

- [GKE 控制台](https://console.cloud.google.com/kubernetes/list?project=flowmemorysync)
- [Artifact Registry](https://console.cloud.google.com/artifacts?project=flowmemorysync)
- [Cloud Shell](https://console.cloud.google.com/?cloudshell=true&project=flowmemorysync)
- [GitHub Actions](https://github.com/dofaromg/flow-tasks/actions)
