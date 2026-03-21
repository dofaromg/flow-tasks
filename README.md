# FlowAgent GKE Starter (GitOps + CI/CD)

**✅ 完整的 GKE 部署基礎設施已就緒！** 這個 repository 提供完整的 Kubernetes 部署配置、CI/CD 流程和 GitOps 支援。

**🤖 GitHub Copilot Coding Agent 支援：可以在這裡使用！** This repository supports GitHub Copilot Coding Agent — it can be used here to implement features, fix bugs, and assist with development tasks.

## 🔄 外部倉庫檔案同步 / External Repository File Sync

**全新功能！** 自動從其他 GitHub 倉庫拉取檔案到本地倉庫。

**New Feature!** Automatically pull files from other GitHub repositories to your local repository.

### 快速開始 / Quick Start

```bash
# 配置要同步的倉庫 / Configure repositories to sync
vim repos_sync.yaml

# 手動執行同步 / Run sync manually
python scripts/sync_external_repos.py

# 列出所有配置的倉庫 / List all configured repositories
python scripts/sync_external_repos.py --list
```

📚 **完整文檔**: [外部倉庫檔案同步系統指南](docs/EXTERNAL_REPO_SYNC.md)

---

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
- [分支整合優化指南](BRANCH_INTEGRATION_GUIDE.md) ⭐ 新增
- [Codespace 管理指南](CODESPACE_MANAGEMENT.md) 🆕 新增

---

## 📦 GitHub Codespaces 開發環境

使用 GitHub Codespaces 快速啟動雲端開發環境：

### 快速開始
```bash
# 創建 Codespace
gh codespace create --repo dofaromg/flow-tasks

# 或直接從 GitHub 網頁介面創建
# 點擊 "Code" → "Codespaces" → "Create codespace on main"
```

### Codespace 生命週期管理

⚠️ **重要提醒**：Codespace 在 30 天不活動後會自動刪除。

**防止刪除的方法**：
1. 定期連接 Codespace（建議每 2 週一次）
2. 使用監控腳本：`./scripts/monitor-codespaces.sh`
3. 啟用自動監控：查看 `.github/workflows/codespace-monitoring.yml`

**快速管理命令**：
```bash
# 列出所有 Codespaces
gh codespace list

# 連接到 Codespace
gh codespace code -c CODESPACE_NAME

# 停止 Codespace（節省使用時數）
gh codespace stop -c CODESPACE_NAME

# 刪除 Codespace
gh codespace delete -c CODESPACE_NAME
```

📖 **完整指南**：查看 [Codespace 管理指南](CODESPACE_MANAGEMENT.md) 了解：
- 詳細的生命週期管理策略
- 自動化監控和提醒設置
- 最佳實踐和故障排除
- 成本優化建議

---

這個壓縮包是「一次搞定」的部署骨架。你把整包丟到 GitHub（或上傳到你的空間）即可：

## 🧩 解壓縮 DLL

新增可重複使用的 .NET 8 解壓縮 DLL（`dll/DecompressionUtility`）：
- 以 `DecompressionHelper.ExtractZip` 將 ZIP 檔案解壓到指定資料夾，可選擇是否覆寫。
- 以 `DecompressionHelper.ListEntries` 先行列出壓縮檔內容，避免盲目解壓。
- 透過 `dotnet build` 直接產出 `DecompressionUtility.dll`，方便在其他模組或自動化腳本中載入使用。
- 透過 `bash scripts/publish_decompression_dll.sh` 打包成 ZIP，方便上傳 GitHub Release 或內部 Artifact Registry。

## 🆕 粒子語言核心系統 (Particle Language Core)

本專案包含完整的 **MRLiou 粒子語言核心系統**，提供：

- **邏輯鏈執行**: STRUCTURE → MARK → FLOW → RECURSE → STORE
- **記憶封存種子系統**: 完整的記憶快照、還原與管理功能
- **邏輯壓縮**: .flpkg 格式支援
- **CLI 互動介面**: 豐富的命令列工具
- **AI 人格套件**: 人格連結器與通用 ZIP 壓縮/解壓縮（無檔案名稱限制）

### 快速開始

```bash
cd particle_core

# 執行示範
python demo.py demo

# 啟動 CLI 介面
python src/cli_runner.py

# 記憶封存系統
python src/memory_archive_seed.py interactive

# AI 人格套件
python src/ai_persona_toolkit.py
```

詳細說明請參閱：
- [本地執行說明](particle_core/docs/本地執行說明.md)
- [記憶封存種子說明](particle_core/docs/記憶封存種子說明.md)
- [AI 人格套件使用說明](particle_core/docs/ai_persona_toolkit_guide.md)
- [記憶封存種子系統更新說明](記憶封存種子系統更新說明.md)

---

## 🔄 分支整合優化 (Branch Integration Optimization)

本專案已實施完整的分支整合檢查機制，確保程式碼品質和部署穩定性：

### 自動化檢查 (Automated Checks)
- ✅ **PR 驗證工作流程**: 自動測試、語法檢查、K8s 配置驗證
- ✅ **多環境分支追蹤**: Production (main) / Staging (develop)
- ✅ **本地驗證腳本**: 建立 PR 前的預先檢查

### 快速驗證 (Quick Validation)
```bash
# 在建立 PR 前執行本地驗證
bash scripts/validate_branch_integration.sh
```

### 工作流程 (Workflow)
1. **建立功能分支** (Create feature branch)
2. **開發和測試** (Develop and test)
3. **本地驗證** (Local validation) - 使用驗證腳本
4. **建立 Pull Request** (Create PR)
5. **自動化檢查** (Automated checks) - CI/CD 流程
6. **審核和合併** (Review and merge)

詳細指南請參閱: [分支整合優化指南](BRANCH_INTEGRATION_GUIDE.md)

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

相關 CI 工作流程：`.github/workflows/ci.yml` 會自動跑一次 smoke test 並上傳 `data/` 產物。 
