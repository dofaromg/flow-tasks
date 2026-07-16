# ArgoCD GitOps 配置

此目錄包含 ArgoCD Application 定義，用於 GitOps 部署。

## 安裝 ArgoCD

```bash
# 建立 argocd namespace
kubectl create namespace argocd

# 安裝 ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 等待 ArgoCD 啟動
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# 取得初始密碼
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward 訪問 UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

## 部署 FlowAgent 應用

```bash
# 套用 ArgoCD Application
kubectl apply -f app.yaml

# 查看應用狀態
kubectl get application -n argocd

# 或使用 ArgoCD CLI
argocd app list
argocd app sync flowagent
```

## 配置說明

- **repoURL**: GitHub repository URL (請修改為你的 fork)
- **targetRevision**: 分支或 tag (預設 HEAD = main branch)
- **path**: Kustomize 配置路徑
- **syncPolicy**: 自動同步配置
  - **automated**: 啟用自動同步
  - **prune**: 刪除不在 Git 中的資源
  - **selfHeal**: 自動修復偏差

## 訪問 ArgoCD UI

1. Port forward: `kubectl port-forward svc/argocd-server -n argocd 8080:443`
2. 瀏覽器訪問: `https://localhost:8080`
3. 用戶名: `admin`
4. 密碼: 使用上述命令取得

## 注意事項

- 請將 `repoURL` 修改為你自己的 repository URL
- 確保 repository 是 public 或已配置 SSH key / token
- 首次同步可能需要幾分鐘時間
