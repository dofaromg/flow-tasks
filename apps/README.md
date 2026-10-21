# FlowAgent 應用程式清單

此目錄包含 FlowAgent 系統的所有 Kubernetes 應用程式清單。

## 📁 目錄結構

```
apps/
├── mongodb/          # MongoDB 資料庫
│   ├── deployment.yaml
│   ├── pvc.yaml
│   └── secret.yaml
├── module-a/         # Module-A 服務
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── deployment.yaml
│   └── hpa.yaml
├── orchestrator/     # Orchestrator 協調器
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── deployment.yaml
├── monitoring/       # Prometheus 監控
│   └── prometheus.yaml
└── keda/            # KEDA 自動擴展
    ├── README.md
    └── module-a-scaledobject.yaml
```

## 🔧 組件說明

### MongoDB
- **用途**: 資料庫
- **部署**: 1 個 replica
- **持久化**: 使用 PVC (10Gi)
- **密碼**: 存儲在 Secret 中（生產環境請修改）

### Module-A
- **用途**: 微服務模組
- **部署**: 2 個 replicas（可自動擴展）
- **端口**: 8080
- **健康檢查**: `/health` 和 `/ready` 端點
- **自動擴展**: HPA 配置（2-10 replicas）

### Orchestrator
- **用途**: 服務協調器
- **部署**: 1 個 replica
- **端口**: 8081
- **服務類型**: LoadBalancer（對外暴露）
- **依賴**: Module-A, MongoDB

### Monitoring
- **用途**: 系統監控
- **組件**: Prometheus
- **命名空間**: monitoring
- **訪問**: ClusterIP (需要 port-forward)

### KEDA
- **用途**: 事件驅動自動擴展
- **需要**: 先安裝 KEDA operator
- **配置**: 基於 CPU 和記憶體的擴展規則

## 🚀 使用方式

### 單獨部署某個組件

```bash
# 部署 MongoDB
kubectl apply -f apps/mongodb/

# 部署 Module-A
kubectl apply -f apps/module-a/

# 部署 Orchestrator
kubectl apply -f apps/orchestrator/

# 部署 Monitoring
kubectl apply -f apps/monitoring/
```

### 使用 Kustomize 部署所有組件

```bash
kubectl apply -k cluster/overlays/prod
```

## 🐳 建置 Docker 映像

### Module-A

```bash
cd apps/module-a
docker build -t asia-east1-docker.pkg.dev/flowmemorysync/flowagent/module-a:latest .
docker push asia-east1-docker.pkg.dev/flowmemorysync/flowagent/module-a:latest
```

### Orchestrator

```bash
cd apps/orchestrator
docker build -t asia-east1-docker.pkg.dev/flowmemorysync/flowagent/orchestrator:latest .
docker push asia-east1-docker.pkg.dev/flowmemorysync/flowagent/orchestrator:latest
```

## 🔍 測試應用程式

### 本地測試

```bash
# Module-A
cd apps/module-a
pip install -r requirements.txt
python app.py

# Orchestrator
cd apps/orchestrator
pip install -r requirements.txt
python app.py
```

### Kubernetes 測試

```bash
# 檢查 pods
kubectl get pods -n flowagent

# 查看日誌
kubectl logs -f deployment/module-a -n flowagent
kubectl logs -f deployment/orchestrator -n flowagent

# Port forward 測試
kubectl port-forward svc/module-a 8080:8080 -n flowagent
curl http://localhost:8080/health

kubectl port-forward svc/orchestrator 8081:80 -n flowagent
curl http://localhost:8081/health
```

## 📝 配置說明

### 環境變數

#### Module-A
- `MONGODB_URI`: MongoDB 連接字串
- `MODULE_NAME`: 模組名稱
- `LOG_LEVEL`: 日誌級別

#### Orchestrator
- `MONGODB_URI`: MongoDB 連接字串
- `MODULE_A_ENDPOINT`: Module-A 服務端點
- `LOG_LEVEL`: 日誌級別

### 資源限制

所有服務都配置了資源請求和限制：

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"
```

## 🔐 安全性注意事項

1. **MongoDB 密碼**: 生產環境請修改 `apps/mongodb/secret.yaml` 中的密碼
2. **映像安全**: 定期更新基礎映像以修復安全漏洞
3. **網路策略**: 考慮添加 NetworkPolicy 限制 pod 間通信
4. **Secret 管理**: 建議使用 Google Secret Manager 或其他密鑰管理服務

## 📊 監控和觀測

### Prometheus 指標

所有服務都應該暴露 `/metrics` 端點供 Prometheus 抓取。

添加 annotations 到 pod 模板：

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"
  prometheus.io/path: "/metrics"
```

### 日誌

使用結構化日誌格式，方便日誌聚合和分析。

## 🔄 持續部署

通過 GitHub Actions 自動建置和部署：

1. 推送代碼到 `main` 分支
2. CI workflow 建置並推送 Docker 映像
3. CD workflow 部署到 GKE

## 📚 相關文檔

- [DEPLOYMENT.md](../DEPLOYMENT.md) - 完整部署指南
- [README.md](../README.md) - 專案概覽
- [ArgoCD README](../argocd/README.md) - GitOps 配置
