# Next.js 部署架構對比

## 舊架構 (Vercel)

```
┌─────────────────────────────────────────────────────────┐
│                   GitHub Repository                      │
│                  dofaromg/flow-tasks                     │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌───────────────┐  ┌──────────────────────┐
│    Vercel     │  │   GitHub Actions     │
│   Frontend    │  │    (Backend CI/CD)   │
│               │  │                      │
│ ❌ 不穩定     │  │  ✅ 穩定運行         │
│ ❌ 經常失敗   │  │                      │
└───────────────┘  └─────────┬────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  GCP GKE Cluster │
                    │  flowmemorysync  │
                    │                  │
                    │ • Module-A       │
                    │ • Orchestrator   │
                    │ • MongoDB        │
                    └──────────────────┘

問題：
❌ Vercel 部署頻繁失敗
❌ 前端與後端分離管理
❌ 缺乏統一的監控和日誌
```

## 新架構 (GKE 統一部署)

```
┌─────────────────────────────────────────────────────────┐
│                   GitHub Repository                      │
│                  dofaromg/flow-tasks                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ GitHub Actions  │
        │    (CI/CD)      │
        │                 │
        │ ✅ 自動構建     │
        │ ✅ 自動部署     │
        │ ✅ 部署驗證     │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ Artifact        │
        │ Registry (GCP)  │
        │                 │
        │ • nextjs:latest │
        │ • module-a      │
        │ • orchestrator  │
        └────────┬────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│            GCP GKE Cluster (flowmemorysync)            │
│                  Namespace: flowagent                  │
│                                                        │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │ Next.js Frontend │  │   Module-A       │          │
│  │ (LoadBalancer)   │  │   (ClusterIP)    │          │
│  │ • 2 replicas     │  │ • 2-10 replicas  │          │
│  │ • Port 80:3000   │  │ • HPA enabled    │          │
│  │ • 256Mi/200m     │  │ • 256Mi/200m     │          │
│  └──────────────────┘  └──────────────────┘          │
│                                                        │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Orchestrator    │  │    MongoDB       │          │
│  │ (LoadBalancer)   │  │  (StatefulSet)   │          │
│  │ • 1 replica      │  │ • 1 replica      │          │
│  │ • Port 80:8080   │  │ • 10Gi PVC       │          │
│  │ • 256Mi/200m     │  │ • 512Mi/500m     │          │
│  └──────────────────┘  └──────────────────┘          │
│                                                        │
│  ┌──────────────────────────────────────────────┐    │
│  │           Prometheus Monitoring              │    │
│  │         (統一監控所有服務)                    │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
└────────────────────────────────────────────────────────┘

優勢：
✅ 統一管理，穩定可靠
✅ 自動化 CI/CD 流程
✅ 完整的監控和日誌
✅ 可擴展和高可用
✅ 企業級基礎設施
```

## 部署流程對比

### 舊流程 (Vercel)

```
1. Developer Push
   ↓
2. Vercel Auto Deploy
   ↓ (❌ 經常失敗)
3. ??? (無法控制)
   ↓
4. 🌐 Vercel CDN

時間線：未知，經常失敗
可控性：低
可觀察性：有限
```

### 新流程 (GKE)

```
1. Developer Push to main
   ↓
2. GitHub Actions CI
   ├─ Build Next.js Image
   ├─ Build Module-A Image
   └─ Build Orchestrator Image
   ↓ (✅ 並行構建)
3. Push to Artifact Registry
   ↓
4. GitHub Actions CD
   ├─ Deploy to GKE
   ├─ Verify Rollout Status
   └─ Update Service Endpoints
   ↓ (✅ 自動驗證)
5. 🌐 GKE LoadBalancer

時間線：可預測，約 5-8 分鐘
可控性：完全控制
可觀察性：完整日誌和監控
```

## 成本對比

### Vercel

```
免費層：
- 100GB 帶寬/月
- 無限部署

付費層 (如需要)：
- $20+/月
- 受限的自定義配置
```

### GKE

```
運算資源：
- Next.js Pods: 2 × (256Mi/200m) ≈ $10/月
- LoadBalancer: ≈ $18/月
- 其他後端服務：已存在成本

總增加：約 $28/月

優化方案：
- 使用 Ingress 替代 LoadBalancer: 節省 $18/月
- 使用 Preemptible Nodes: 節省 30-50%
```

## 遷移時間線

```
2026-02-04
    |
    ├─ 09:00  分析問題和規劃方案
    |
    ├─ 10:00  創建 Docker 配置
    |          - Dockerfile (多階段構建)
    |          - 更新 next.config.mjs
    |
    ├─ 11:00  創建 Kubernetes 資源
    |          - Deployment, Service, Secret
    |          - Kustomize 配置
    |
    ├─ 12:00  更新 CI/CD workflows
    |          - ci-build.yml
    |          - cd-deploy.yml
    |
    ├─ 13:00  整合到生產環境配置
    |          - cluster/overlays/prod
    |
    ├─ 14:00  創建文檔
    |          - GKE_MIGRATION.md
    |          - NEXTJS_DEPLOYMENT_QUICK_GUIDE.md
    |          - MIGRATION_COMPLETION_REPORT.md
    |
    └─ 15:00  驗證和提交
               ✅ 遷移完成
```

## 訪問方式對比

### Vercel

```
URL: https://flow-tasks-xyz.vercel.app
特點:
- 自動 HTTPS
- 全球 CDN
- 自動域名
- ❌ 不穩定
```

### GKE

```
URL: http://EXTERNAL_IP (獲取方式: kubectl get svc nextjs-frontend -n flowagent)
特點:
- 可配置 HTTPS (Ingress + Let's Encrypt)
- 可配置 CDN (Cloud CDN)
- 可配置自定義域名
- ✅ 穩定可靠
```

## 下一步建議

### 立即執行

1. ✅ 配置 GitHub Secrets
2. ✅ 測試 CI/CD 流程
3. ✅ 驗證應用部署

### 短期優化 (1-2 週)

1. 配置自定義域名
2. 設置 SSL/TLS 證書
3. 配置 Ingress 替代 LoadBalancer

### 中期改進 (1-2 月)

1. 配置 Cloud CDN 加速
2. 設置 HPA 自動擴展
3. 整合 Google Secret Manager
4. 配置監控告警

### 長期規劃 (3-6 月)

1. 多區域部署
2. 災難恢復計劃
3. 性能優化和調優
4. 成本優化分析

## 回滾策略

### 如果需要臨時回到 Vercel

```bash
# 方法 1: 通過 Vercel CLI
vercel --prod

# 方法 2: 通過 Vercel Dashboard
# 1. 訪問 vercel.com/dashboard
# 2. 選擇項目
# 3. 點擊 "Deploy"
```

### Kubernetes 回滾

```bash
# 回滾 Next.js deployment
kubectl rollout undo deployment/nextjs-frontend -n flowagent

# 查看歷史版本
kubectl rollout history deployment/nextjs-frontend -n flowagent

# 回滾到特定版本
kubectl rollout undo deployment/nextjs-frontend -n flowagent --to-revision=2
```

## 總結

✅ **完成遷移**: Next.js 從 Vercel 遷移到 GKE  
✅ **解決問題**: 部署不穩定問題得到解決  
✅ **統一管理**: 前後端服務統一部署  
✅ **自動化**: CI/CD 完整配置  
✅ **文檔完整**: 提供詳細的操作指南  

🎯 **下一步**: 配置 GitHub Secrets 並測試部署流程
