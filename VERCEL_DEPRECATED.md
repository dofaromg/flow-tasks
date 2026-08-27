# Vercel Configuration (Deprecated / 已棄用)

⚠️ **This configuration is deprecated and kept for reference only.**

## Migration Notice / 遷移通知

Due to frequent deployment failures on Vercel, this project has been migrated to **Google Kubernetes Engine (GKE)**.

由於 Vercel 部署經常失敗，此專案已遷移至 **Google Kubernetes Engine (GKE)**。

### New Deployment Method / 新的部署方式

Please refer to the following guides:

- 🔄 [GKE Migration Guide / GKE 遷移指南](./GKE_MIGRATION.md)
- 🚀 [GKE Deployment Guide / GKE 部署指南](./DEPLOYMENT.md)
- 📖 [Next.js Frontend README / Next.js 前端說明](./apps/nextjs-frontend/README.md)

### Files Kept for Reference / 保留的參考文件

The following files are kept for reference and as a fallback option:

- `vercel.json` - Vercel configuration
- `.vercelignore` - Vercel ignore file
- `VERCEL_DEPLOYMENT.md` - Vercel deployment guide (marked as deprecated)

### Quick Start with GKE / GKE 快速開始

```bash
# Deploy to GKE
kubectl apply -k cluster/overlays/prod/

# Check deployment status
kubectl get pods -n flowagent
kubectl get svc nextjs-frontend -n flowagent
```

For more details, see [GKE_MIGRATION.md](./GKE_MIGRATION.md).
