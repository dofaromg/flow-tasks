# Next.js Frontend 快速部署指南 / Quick Deployment Guide

## 📋 快速概覽 / Quick Overview

此專案的 Next.js 前端已從 Vercel 遷移到 GKE，與後端服務統一部署管理。

The Next.js frontend has been migrated from Vercel to GKE for unified deployment with backend services.

## 🚀 一鍵部署 / One-Click Deployment

```bash
# 部署所有服務（包括 Next.js 前端）
kubectl apply -k cluster/overlays/prod/

# 檢查 Next.js 前端狀態
kubectl get pods -l app=nextjs-frontend -n flowagent
kubectl get svc nextjs-frontend -n flowagent
```

## 🔧 獨立部署 Next.js / Deploy Next.js Separately

```bash
# 只部署 Next.js 前端
kubectl apply -k apps/nextjs-frontend/

# 驗證部署
kubectl rollout status deployment/nextjs-frontend -n flowagent
```

## 🌐 獲取訪問地址 / Get Access URL

```bash
# 獲取 LoadBalancer 外部 IP
kubectl get svc nextjs-frontend -n flowagent

# 輸出示例 / Example output:
# NAME              TYPE           EXTERNAL-IP      PORT(S)
# nextjs-frontend   LoadBalancer   34.80.123.45     80:30001/TCP

# 訪問應用 / Access app:
# http://34.80.123.45
```

## 📊 監控與日誌 / Monitoring & Logs

```bash
# 查看實時日誌
kubectl logs -f -l app=nextjs-frontend -n flowagent --tail=100

# 查看 Pod 狀態
kubectl get pods -l app=nextjs-frontend -n flowagent -w

# 查看資源使用
kubectl top pods -l app=nextjs-frontend -n flowagent
```

## 🔄 更新與回滾 / Update & Rollback

```bash
# 重啟 deployment（應用環境變數變更）
kubectl rollout restart deployment/nextjs-frontend -n flowagent

# 查看部署歷史
kubectl rollout history deployment/nextjs-frontend -n flowagent

# 回滾到上一版本
kubectl rollout undo deployment/nextjs-frontend -n flowagent
```

## 🔐 配置 Secrets / Configure Secrets

```bash
# 編輯 secret 文件
nano apps/nextjs-frontend/secret.yaml

# 更新 GrowthBook 配置
# growthbook-api-host: "https://cdn.growthbook.io"
# growthbook-client-key: "YOUR_KEY_HERE"

# 應用變更
kubectl apply -f apps/nextjs-frontend/secret.yaml

# 重啟 pods 使其生效
kubectl rollout restart deployment/nextjs-frontend -n flowagent
```

## 📈 擴展副本數 / Scale Replicas

```bash
# 手動擴展到 3 個副本
kubectl scale deployment nextjs-frontend -n flowagent --replicas=3

# 自動擴展（需要先創建 HPA）
kubectl autoscale deployment nextjs-frontend -n flowagent \
  --min=2 --max=10 --cpu-percent=70
```

## 🐛 故障排除 / Troubleshooting

### Pod 無法啟動

```bash
# 查看 Pod 詳情
kubectl describe pod <pod-name> -n flowagent

# 查看事件
kubectl get events -n flowagent --sort-by='.lastTimestamp' | grep nextjs
```

### 映像拉取失敗

```bash
# 檢查 Artifact Registry 權限
gcloud projects add-iam-policy-binding flowmemorysync \
  --member="serviceAccount:$(gcloud container clusters describe modular-cluster \
    --zone=asia-east1-a --format='value(nodeConfig.serviceAccount)')" \
  --role="roles/artifactregistry.reader"
```

### LoadBalancer 無法分配 IP

```bash
# 檢查 GCP 配額
gcloud compute project-info describe --project=flowmemorysync

# 查看服務狀態
kubectl describe svc nextjs-frontend -n flowagent

# 如果長時間未分配，考慮改用 ClusterIP + Ingress
```

## 🔗 相關資源 / Related Resources

- 📖 [完整遷移指南](./GKE_MIGRATION.md)
- 🚀 [GKE 部署指南](./DEPLOYMENT.md)
- 📚 [Next.js Frontend 文檔](./apps/nextjs-frontend/README.md)
- 🏗️ [架構說明](./ARCHITECTURE.md)

## 💡 最佳實踐 / Best Practices

1. **使用 GitOps**: 通過 Git 推送觸發自動部署
2. **監控資源使用**: 定期檢查 CPU 和記憶體使用率
3. **配置健康檢查**: 已預設配置 liveness 和 readiness probes
4. **定期更新映像**: 保持依賴和基礎映像最新
5. **備份配置**: 保存 secret 和 configmap 的備份

## ⚠️ 注意事項 / Important Notes

- LoadBalancer 會產生 GCP 費用
- 首次部署需要 5-10 分鐘
- Secret 應定期輪換
- 生產環境建議使用 Ingress + SSL/TLS

## 🎯 下一步 / Next Steps

- [ ] 配置自定義域名
- [ ] 設置 SSL/TLS 證書
- [ ] 配置 CDN（Cloud CDN）
- [ ] 設置監控告警
- [ ] 配置自動備份
