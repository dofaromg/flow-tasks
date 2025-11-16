# FlowAgent GKE Starter (GitOps + CI/CD)

**✅ 完整的 GKE 部署基礎設施已就緒！** 這個 repository 提供完整的 Kubernetes 部署配置、CI/CD 流程和 GitOps 支援。

## 🚀 快速部署

選擇一種部署方式開始：

### 方式 1: 一鍵部署 (最簡單)
```bash
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks
bash scripts/oneclick_gke_init.sh
kubectl apply -k cluster/overlays/prod
```

### 方式 2: GitOps (ArgoCD) - 生產環境推薦
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f argocd/app.yaml
```

### 方式 3: GitHub Actions CI/CD
設定 GitHub Secrets 後，推送到 main 分支自動部署

📚 **詳細文檔**：
- [完整部署指南](DEPLOYMENT.md)
- [快速參考](QUICKSTART.md)
- [架構圖表](ARCHITECTURE.md)
- [應用程式說明](apps/README.md)

---

這個壓縮包是「一次搞定」的部署骨架。你把整包丟到 GitHub（或上傳到你的空間）即可：

## 🆕 粒子語言核心系統 (Particle Language Core)

本專案包含完整的 **MRLiou 粒子語言核心系統**，提供：

- **邏輯鏈執行**: STRUCTURE → MARK → FLOW → RECURSE → STORE
- **記憶封存種子系統**: 完整的記憶快照、還原與管理功能
- **邏輯壓縮**: .flpkg 格式支援
- **CLI 互動介面**: 豐富的命令列工具

### 快速開始

```bash
cd particle_core

# 執行示範
python demo.py demo

# 啟動 CLI 介面
python src/cli_runner.py

# 記憶封存系統
python src/memory_archive_seed.py interactive
```

詳細說明請參閱：
- [本地執行說明](particle_core/docs/本地執行說明.md)
- [記憶封存種子說明](particle_core/docs/記憶封存種子說明.md)
- [記憶封存種子系統更新說明](記憶封存種子系統更新說明.md)

---

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

kubectl create namespace $NS || true
kubectl create namespace monitoring || true
kubectl apply -n monitoring -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml
kubectl apply -f https://github.com/kedacore/keda/releases/latest/download/keda-2.13.1.yaml
```

---

## 目錄說明

### 部署基礎設施
- **`apps/`**：完整的 Kubernetes 應用清單
  - `mongodb/`：資料庫部署 (Deployment + PVC + Secret)
  - `module-a/`：微服務模組 (Flask app + Dockerfile + HPA)
  - `orchestrator/`：協調器服務 (Flask app + Dockerfile + LoadBalancer)
  - `monitoring/`：Prometheus 監控配置
  - `keda/`：事件驅動自動擴展配置
- **`cluster/`**：Kustomize 叢集配置
  - `base/`：基礎配置 (命名空間)
  - `overlays/prod/`：生產環境配置 (9 個資源)
  - `overlays/monitoring/`：監控配置 (6 個資源)
- **`argocd/`**：GitOps 配置
  - `app.yaml`：ArgoCD Application 定義
  - `README.md`：ArgoCD 部署說明
- **`.github/workflows/`**：CI/CD 流程
  - `ci-build.yml`：建置並推送 Docker 映像
  - `cd-deploy.yml`：部署到 GKE 叢集
- **`scripts/`**：部署腳本
  - `oneclick_gke_init.sh`：一鍵初始化 GKE 叢集
  - `validate_deployment.sh`：驗證 Kubernetes 配置

### 粒子語言核心
- **`particle_core/`**：MRLiou 粒子語言核心系統
  - 邏輯鏈執行框架
  - 記憶封存種子系統
  - CLI 互動介面

### 文檔
- **`DEPLOYMENT.md`**：完整部署指南 (6000+ 字)
- **`QUICKSTART.md`**：快速參考 (5000+ 字)
- **`ARCHITECTURE.md`**：架構和流程圖 (11000+ 字)
- **`apps/README.md`**：應用程式詳細說明

