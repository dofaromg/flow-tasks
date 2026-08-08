# Next.js Frontend Deployment

此目錄包含 Next.js 前端應用的 Kubernetes 部署配置。

## 🎯 目的

將原本部署在 Vercel 的 Next.js 應用遷移到 GKE，解決 Vercel 部署不穩定的問題。

## 📦 部署內容

- **Deployment**: Next.js 應用，2 個副本
- **Service**: LoadBalancer 類型，對外暴露 HTTP 端口
- **Secret**: GrowthBook 配置和其他敏感資訊

## 🚀 部署方式

### 方法 1: 使用 kubectl 直接部署

```bash
# 更新 secret.yaml 中的 GrowthBook 配置
# 然後應用配置
kubectl apply -k apps/nextjs-frontend/
```

### 方法 2: 透過 Kustomize 整合部署

Next.js 前端已整合到 `cluster/overlays/prod/kustomization.yaml` 中：

```bash
kubectl apply -k cluster/overlays/prod/
```

### 方法 3: 透過 CI/CD 自動部署

當推送到 `main` 分支時，GitHub Actions 會自動：
1. 構建 Next.js Docker 映像
2. 推送到 GCP Artifact Registry
3. 部署到 GKE

## 🔧 配置說明

### 環境變數

在 `secret.yaml` 中配置以下環境變數：

- `NEXT_PUBLIC_GROWTHBOOK_API_HOST`: GrowthBook API 端點
- `NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY`: GrowthBook 客戶端金鑰

### 資源配置

**請求 (Requests)**:
- CPU: 200m
- Memory: 256Mi

**限制 (Limits)**:
- CPU: 500m
- Memory: 512Mi

### 健康檢查

- **Liveness Probe**: 每 10 秒檢查一次，確保應用運行
- **Readiness Probe**: 每 5 秒檢查一次，確保應用就緒

## 🌐 訪問應用

部署完成後，使用以下命令獲取外部 IP：

```bash
kubectl get svc nextjs-frontend -n flowagent
```

等待 `EXTERNAL-IP` 分配完成後，通過瀏覽器訪問該 IP。

## 📊 監控和日誌

### 查看日誌

```bash
# 查看所有副本的日誌
kubectl logs -l app=nextjs-frontend -n flowagent --tail=100 -f

# 查看特定 pod 的日誌
kubectl logs <pod-name> -n flowagent -f
```

### 查看 Pod 狀態

```bash
kubectl get pods -l app=nextjs-frontend -n flowagent
kubectl describe pod <pod-name> -n flowagent
```

### 查看服務狀態

```bash
kubectl get svc nextjs-frontend -n flowagent
kubectl describe svc nextjs-frontend -n flowagent
```

## 🔄 更新部署

### 更新映像版本

編輯 `cluster/overlays/prod/kustomization.yaml` 中的映像標籤，然後：

```bash
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

## 🛡️ 安全考量

1. **Secret 管理**: 生產環境中，建議使用 Google Secret Manager 整合
2. **網路策略**: 考慮添加 NetworkPolicy 限制流量
3. **HTTPS**: 建議配置 Ingress 和 SSL/TLS 證書
4. **資源限制**: 已設置資源限制防止資源耗盡

## 📚 相關文檔

- [GKE 部署指南](../../DEPLOYMENT.md)
- [Vercel 部署指南](../../VERCEL_DEPLOYMENT.md)（已棄用）
- [GKE 遷移說明](../../GKE_MIGRATION.md)

## 🔗 相關服務

- **Module-A**: `apps/module-a/`
- **Orchestrator**: `apps/orchestrator/`
- **MongoDB**: `apps/mongodb/`
