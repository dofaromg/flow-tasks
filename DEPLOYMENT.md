# FlowAgent GKE 部署指南

本指南提供完整的 FlowAgent 叢集部署步驟。

## 📋 前置需求

1. **Google Cloud Platform 帳號**
   - 已建立 GCP 專案 (例如: `flowmemorysync`)
   - 已啟用計費

2. **本地工具**（如使用 Cloud Shell 則已預安裝）
   - gcloud CLI
   - kubectl
   - kustomize

## 🚀 快速開始

### 選項 A: 使用一鍵初始化腳本

最簡單的方式是使用我們提供的初始化腳本：

```bash
# 1. 克隆 repository
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks

# 2. 執行初始化腳本
bash scripts/oneclick_gke_init.sh

# 3. 部署應用
kubectl apply -k cluster/overlays/prod
```

### 選項 B: 手動部署步驟

#### 1. 設定環境變數

```bash
export PROJECT_ID=flowmemorysync
export REGION=asia-east1
export ZONE=asia-east1-a
export CLUSTER_NAME=modular-cluster
export NS=flowagent
```

#### 2. 設定 GCP 專案並啟用 API

```bash
gcloud config set project $PROJECT_ID
gcloud services enable container.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

#### 3. 建立 GKE 叢集（如果不存在）

```bash
gcloud container clusters create $CLUSTER_NAME \
  --zone $ZONE \
  --num-nodes 3 \
  --machine-type e2-standard-2 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade \
  --release-channel regular
```

#### 4. 取得叢集憑證

```bash
gcloud container clusters get-credentials $CLUSTER_NAME \
  --zone $ZONE \
  --project $PROJECT_ID
```

#### 5. 建立命名空間

```bash
kubectl create namespace $NS
kubectl create namespace monitoring
```

#### 6. 部署應用（使用 Kustomize）

```bash
kubectl apply -k cluster/overlays/prod
```

#### 7. 驗證部署

```bash
# 檢查 pods 狀態
kubectl get pods -n $NS

# 檢查 services
kubectl get svc -n $NS

# 檢查部署
kubectl get deployments -n $NS
```

## 🔄 GitOps 部署（使用 ArgoCD）

### 1. 安裝 ArgoCD

```bash
# 建立 namespace
kubectl create namespace argocd

# 安裝 ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 等待安裝完成
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
```

### 2. 取得 ArgoCD 密碼

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo
```

### 3. 訪問 ArgoCD UI

```bash
# Port forward
kubectl port-forward svc/argocd-server -n argocd 8080:443

# 瀏覽器訪問 https://localhost:8080
# 用戶名: admin
# 密碼: 使用上面的命令取得
```

### 4. 部署 FlowAgent 應用

```bash
kubectl apply -f argocd/app.yaml
```

### 5. 同步應用

通過 UI 或 CLI 同步應用：

```bash
# 如果已安裝 ArgoCD CLI
argocd app sync flowagent
```

## 🔧 配置自定義參數

### 修改 GCP 專案

在 `argocd/app.yaml` 和所有 deployment 檔案中，將以下參數替換為你的值：

- `PROJECT_ID`: 你的 GCP 專案 ID
- `REGION`: 你的區域 (例如: `asia-east1`)
- `ZONE`: 你的可用區 (例如: `asia-east1-a`)
- `CLUSTER_NAME`: 你的叢集名稱

### 修改容器映像

在 `cluster/overlays/prod/kustomization.yaml` 中更新映像路徑：

```yaml
images:
- name: asia-east1-docker.pkg.dev/YOUR_PROJECT/flowagent/module-a
  newTag: latest
- name: asia-east1-docker.pkg.dev/YOUR_PROJECT/flowagent/orchestrator
  newTag: latest
```

## 🏗️ CI/CD 設定

### GitHub Actions 設定

1. **建立 Workload Identity Federation**

```bash
# 建立 Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# 建立 Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

2. **建立 Service Account**

```bash
# 建立 SA
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer"

# 授予權限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/container.developer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

3. **設定 GitHub Secrets**

在你的 GitHub repository 設定中，添加以下 secrets：

- `GCP_WIF_PROVIDER`: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider`
- `GCP_DEPLOYER_SA`: `github-deployer@PROJECT_ID.iam.gserviceaccount.com`

## 📊 監控和日誌

### 查看應用日誌

```bash
# Module-A 日誌
kubectl logs -f deployment/module-a -n flowagent

# Orchestrator 日誌
kubectl logs -f deployment/orchestrator -n flowagent

# MongoDB 日誌
kubectl logs -f deployment/mongodb -n flowagent
```

### 訪問 Prometheus

```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# 訪問 http://localhost:9090
```

## 🔍 故障排除

### Pods 無法啟動

```bash
# 查看 pod 詳情
kubectl describe pod <pod-name> -n flowagent

# 查看事件
kubectl get events -n flowagent --sort-by='.lastTimestamp'
```

### 映像拉取失敗

確保你的 GKE 節點有權限訪問 Artifact Registry：

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$(gcloud container clusters describe $CLUSTER_NAME \
    --zone=$ZONE --format='value(nodeConfig.serviceAccount)')" \
  --role="roles/artifactregistry.reader"
```

### Service 無法連接

```bash
# 檢查 service
kubectl get svc -n flowagent

# 檢查 endpoints
kubectl get endpoints -n flowagent

# 測試連接
kubectl run test-pod --rm -i --tty --image=busybox -n flowagent -- sh
# 在 pod 中: wget -O- http://module-a:8080/health
```

## 📦 架構說明

```
flowagent namespace
├── MongoDB (資料庫)
├── Module-A (服務模組)
│   ├── Deployment (2 replicas)
│   ├── Service (ClusterIP)
│   └── HPA (自動擴展)
└── Orchestrator (協調器)
    ├── Deployment (1 replica)
    └── Service (LoadBalancer)

monitoring namespace
└── Prometheus (監控)
```

## 🎯 下一步

1. 配置域名和 Ingress
2. 設定 SSL/TLS 憑證
3. 配置備份策略
4. 設定告警規則
5. 整合 particle_core 系統

## 📚 相關文檔

- [README.md](../README.md) - 專案概覽
- [ArgoCD README](../argocd/README.md) - GitOps 配置
- [KEDA README](../apps/keda/README.md) - 自動擴展配置

## 💡 提示

- 首次部署建議使用 Cloud Shell，避免本地環境配置問題
- 生產環境請務必修改 MongoDB 密碼
- 建議使用 GitOps (ArgoCD) 進行持續部署
- 定期備份 MongoDB 資料

## 🔗 有用連結

- [GKE 控制台](https://console.cloud.google.com/kubernetes/list?project=flowmemorysync)
- [Artifact Registry](https://console.cloud.google.com/artifacts?project=flowmemorysync)
- [Cloud Shell](https://console.cloud.google.com/?cloudshell=true&project=flowmemorysync)
