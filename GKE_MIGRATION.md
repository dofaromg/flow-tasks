# Next.js 從 Vercel 遷移到 GKE 指南

## 📋 遷移原因

由於 Vercel 部署經常失敗，我們已將 Next.js 前端應用遷移到 Google Kubernetes Engine (GKE)，與後端服務統一部署和管理。

## 🎯 遷移方案對比

### 原方案：Vercel 部署
**優點**：
- 自動部署，零配置
- 全球 CDN 加速
- 簡單易用

**缺點**：
- 部署經常失敗 ❌
- 與後端服務分離，管理複雜
- 受限於 Vercel 平台限制
- 無法完全控制基礎設施

### 新方案：GKE 部署
**優點**：
- ✅ 穩定可靠的企業級基礎設施
- ✅ 與後端服務統一管理
- ✅ 完全控制部署流程和資源
- ✅ 使用現有的 GCP 基礎設施
- ✅ GitOps 自動化部署
- ✅ 可擴展和高可用性

**缺點**：
- 需要配置 Kubernetes 資源
- 需要管理 Docker 映像

## 🚀 新部署架構

```
GitHub Repository
    |
    v
GitHub Actions (CI/CD)
    |
    +---> Build Docker Image (Next.js)
    |
    +---> Push to Artifact Registry
    |
    v
Google Kubernetes Engine (GKE)
    |
    +---> Next.js Frontend (LoadBalancer)
    +---> Module-A Service
    +---> Orchestrator Service
    +---> MongoDB Database
```

## 📦 已完成的遷移步驟

### 1. Docker 化 Next.js 應用

創建了 `apps/nextjs-frontend/Dockerfile`，使用多階段構建：
- **deps 階段**: 安裝生產依賴
- **builder 階段**: 構建 Next.js 應用
- **runner 階段**: 最小化運行時映像

關鍵配置：
```dockerfile
# 啟用 standalone 輸出模式
# 在 next.config.mjs 中設置：output: 'standalone'
```

### 2. Kubernetes 資源配置

創建了以下資源：
- **Deployment**: 2 個副本，自動負載均衡
- **Service**: LoadBalancer 類型，對外暴露 HTTP 端口
- **Secret**: GrowthBook 配置

文件位置：
- `apps/nextjs-frontend/deployment.yaml`
- `apps/nextjs-frontend/secret.yaml`
- `apps/nextjs-frontend/kustomization.yaml`

### 3. CI/CD 自動化

更新了 GitHub Actions workflows：

**CI Workflow** (`.github/workflows/ci-build.yml`):
- 自動構建 Next.js Docker 映像
- 推送到 GCP Artifact Registry
- 觸發條件：推送到 `main` 分支或手動觸發

**CD Workflow** (`.github/workflows/cd-deploy.yml`):
- 自動部署到 GKE
- 驗證所有服務部署狀態
- CI 成功後自動觸發

### 4. 更新 Next.js 配置

修改 `next.config.mjs`：
```javascript
output: 'standalone'  // 啟用 Docker 部署優化
```

### 5. Kustomize 整合

將 Next.js 前端整合到 `cluster/overlays/prod/kustomization.yaml`：
```yaml
resources:
  - ../../../apps/nextjs-frontend
images:
  - name: asia-east1-docker.pkg.dev/flowmemorysync/flowagent/nextjs-frontend
    newTag: latest
```

## 🔧 部署指南

### 前置需求

1. **GCP 配置**
   - GCP 專案 ID: `flowmemorysync`
   - GKE 叢集: `modular-cluster`
   - 區域: `asia-east1-a`

2. **GitHub Secrets 配置**
   - `GCP_WIF_PROVIDER`: Workload Identity Provider
   - `GCP_DEPLOYER_SA`: Service Account
   - `NEXT_PUBLIC_GROWTHBOOK_API_HOST`: (可選) GrowthBook API
   - `NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY`: (可選) GrowthBook 金鑰

### 自動部署 (推薦)

推送到 `main` 分支，GitHub Actions 會自動：
1. 構建 Docker 映像
2. 推送到 Artifact Registry
3. 部署到 GKE

```bash
git push origin main
```

### 手動部署

#### 方法 1: 使用 kubectl

```bash
# 1. 更新 secret.yaml 中的配置
# 2. 應用配置
kubectl apply -k apps/nextjs-frontend/
```

#### 方法 2: 使用 Kustomize 整合部署

```bash
kubectl apply -k cluster/overlays/prod/
```

#### 方法 3: 本地構建和推送

```bash
# 設置環境變數
export PROJECT_ID=flowmemorysync
export REGION=asia-east1
export REGISTRY=asia-east1-docker.pkg.dev

# 認證 Docker
gcloud auth configure-docker $REGION-docker.pkg.dev

# 構建映像
docker build \
  -t $REGISTRY/$PROJECT_ID/flowagent/nextjs-frontend:latest \
  -f apps/nextjs-frontend/Dockerfile \
  .

# 推送映像
docker push $REGISTRY/$PROJECT_ID/flowagent/nextjs-frontend:latest

# 部署到 GKE
kubectl apply -k cluster/overlays/prod/
```

## 🌐 訪問應用

### 獲取外部 IP

```bash
kubectl get svc nextjs-frontend -n flowagent
```

輸出示例：
```
NAME              TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)        AGE
nextjs-frontend   LoadBalancer   10.96.1.100     34.80.123.45     80:30001/TCP   5m
```

訪問 `http://34.80.123.45` (使用你的實際外部 IP)

### 配置域名 (可選)

如果要使用自定義域名：

1. **創建 Ingress 資源**
2. **配置 SSL/TLS 證書**
3. **更新 DNS 記錄**

參考 [GKE Ingress 文檔](https://cloud.google.com/kubernetes-engine/docs/how-to/load-balance-ingress)

## 📊 監控和維護

### 查看部署狀態

```bash
# 查看 Pods
kubectl get pods -l app=nextjs-frontend -n flowagent

# 查看服務
kubectl get svc nextjs-frontend -n flowagent

# 查看部署
kubectl get deployment nextjs-frontend -n flowagent
```

### 查看日誌

```bash
# 實時查看日誌
kubectl logs -f -l app=nextjs-frontend -n flowagent

# 查看特定 Pod 日誌
kubectl logs <pod-name> -n flowagent
```

### 擴展副本數

```bash
# 手動擴展到 3 個副本
kubectl scale deployment nextjs-frontend -n flowagent --replicas=3

# 或編輯 deployment.yaml 並重新應用
```

### 更新應用

```bash
# 方法 1: 通過 CI/CD (推薦)
git push origin main

# 方法 2: 手動更新映像
kubectl set image deployment/nextjs-frontend \
  nextjs=asia-east1-docker.pkg.dev/flowmemorysync/flowagent/nextjs-frontend:new-tag \
  -n flowagent

# 方法 3: 重新應用配置
kubectl apply -k cluster/overlays/prod/
```

### 回滾部署

```bash
# 查看部署歷史
kubectl rollout history deployment/nextjs-frontend -n flowagent

# 回滾到上一個版本
kubectl rollout undo deployment/nextjs-frontend -n flowagent

# 回滾到特定版本
kubectl rollout undo deployment/nextjs-frontend -n flowagent --to-revision=2
```

## 🔒 環境變數配置

### GrowthBook 功能旗標

在 `apps/nextjs-frontend/secret.yaml` 中配置：

```yaml
stringData:
  growthbook-api-host: "https://cdn.growthbook.io"
  growthbook-client-key: "YOUR_ACTUAL_KEY"
```

更新後重新應用：
```bash
kubectl apply -f apps/nextjs-frontend/secret.yaml
kubectl rollout restart deployment/nextjs-frontend -n flowagent
```

### 使用 Google Secret Manager (生產環境推薦)

1. 在 GCP Secret Manager 中創建 secrets
2. 配置 Workload Identity
3. 在 deployment.yaml 中引用 secrets

參考 [GKE Secret Manager 整合](https://cloud.google.com/secret-manager/docs/using-other-products#kubernetes-engine)

## 🛡️ 安全最佳實踐

1. **更新 Secrets**: 定期更新 GrowthBook 和其他敏感配置
2. **使用 HTTPS**: 配置 Ingress 和 SSL/TLS 證書
3. **限制資源**: 已設置 CPU 和內存限制
4. **網路策略**: 考慮添加 NetworkPolicy 限制流量
5. **映像掃描**: 定期掃描 Docker 映像的安全漏洞

## 📈 性能優化

### 已實施的優化

1. **Standalone 輸出模式**: 減少映像大小
2. **多階段構建**: 最小化運行時映像
3. **資源限制**: 防止資源耗盡
4. **健康檢查**: 自動重啟不健康的 Pods
5. **多副本**: 負載均衡和高可用性

### 進一步優化建議

1. **CDN 整合**: 使用 Google Cloud CDN
2. **靜態資源**: 使用 GCS 存儲靜態資源
3. **快取策略**: 配置適當的 HTTP 快取頭
4. **水平擴展**: 配置 HPA (Horizontal Pod Autoscaler)

## 📚 相關文檔

- [GKE 部署指南](DEPLOYMENT.md)
- [Next.js Frontend README](apps/nextjs-frontend/README.md)
- [Vercel 部署指南](VERCEL_DEPLOYMENT.md) (已棄用)
- [CI/CD Workflows](.github/workflows/)

## 🔗 相關資源

- [GKE 控制台](https://console.cloud.google.com/kubernetes/list?project=flowmemorysync)
- [Artifact Registry](https://console.cloud.google.com/artifacts?project=flowmemorysync)
- [GitHub Actions](https://github.com/dofaromg/flow-tasks/actions)

## 🆘 故障排除

### Pods 無法啟動

```bash
# 查看 Pod 詳情
kubectl describe pod <pod-name> -n flowagent

# 查看事件
kubectl get events -n flowagent --sort-by='.lastTimestamp'
```

### 映像拉取失敗

確保 GKE 節點有權限訪問 Artifact Registry：
```bash
gcloud projects add-iam-policy-binding flowmemorysync \
  --member="serviceAccount:$(gcloud container clusters describe modular-cluster \
    --zone=asia-east1-a --format='value(nodeConfig.serviceAccount)')" \
  --role="roles/artifactregistry.reader"
```

### LoadBalancer 無法分配外部 IP

```bash
# 檢查服務狀態
kubectl describe svc nextjs-frontend -n flowagent

# 查看 GCP 負載均衡器配置
gcloud compute forwarding-rules list
```

### 應用無法訪問

1. 檢查 Pod 是否運行: `kubectl get pods -n flowagent`
2. 檢查服務是否正確: `kubectl get svc -n flowagent`
3. 檢查防火牆規則: GCP Console → VPC Network → Firewall
4. 測試內部連接: `kubectl run test-pod --rm -i --tty --image=busybox -n flowagent -- wget -O- http://nextjs-frontend:3000`

## ✅ 遷移檢查清單

- [x] 創建 Docker 配置
- [x] 創建 Kubernetes 資源
- [x] 更新 CI/CD workflows
- [x] 整合到 Kustomize 配置
- [x] 更新 Next.js 配置
- [x] 創建部署文檔
- [ ] 配置 GitHub Secrets (需要管理員權限)
- [ ] 測試自動部署流程
- [ ] 配置自定義域名 (可選)
- [ ] 配置 SSL/TLS 證書 (可選)
- [ ] 設置監控和告警 (可選)

## 💡 注意事項

1. **Vercel 配置保留**: `vercel.json` 和 `.vercelignore` 文件已保留，作為備選方案
2. **環境變數**: 記得在 GitHub Secrets 和 Kubernetes Secrets 中配置環境變數
3. **成本**: GKE LoadBalancer 會產生額外費用，可考慮使用 Ingress 替代
4. **首次部署**: 首次部署可能需要 5-10 分鐘等待 LoadBalancer 分配外部 IP

## 📞 需要幫助？

- GitHub Issues: [github.com/dofaromg/flow-tasks/issues](https://github.com/dofaromg/flow-tasks/issues)
- GKE 文檔: [cloud.google.com/kubernetes-engine/docs](https://cloud.google.com/kubernetes-engine/docs)
- Next.js 文檔: [nextjs.org/docs](https://nextjs.org/docs)
