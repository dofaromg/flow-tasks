# 🚀 專業部署優化 - 快速開始指南
# Professional Deployment Optimization - Quick Start Guide

## ✨ 最新更新 (Latest Updates)

**版本**: v2.0.0  
**日期**: 2026-02-04  
**狀態**: ✅ 完成

---

## 🎯 優化概覽

本次專業部署優化為 FlowAgent 專案帶來了：

### ✅ 核心優化
1. **安全性增強** - NetworkPolicy + SecurityContext + 私人容器倉庫
2. **可靠性提升** - Health Checks + PDB + 優化部署策略
3. **可觀測性** - ServiceMonitor + Prometheus 集成
4. **自動化** - 自動備份 + 垃圾回收
5. **私人倉庫** - 完整的容器鏡像管理解決方案 ⭐ NEW

### 📊 優化數據
- **新增配置文件**: 27+ 個
- **安全增強**: 4 個 NetworkPolicy + 所有服務 SecurityContext
- **監控集成**: 2 個 ServiceMonitor (Prometheus)
- **自動化**: 2 個 CronJob (備份 + 清理)
- **私人倉庫**: 100Gi 存儲 + 自動管理

---

## 🚀 快速部署

### 選項 A: 完整部署（推薦）

```bash
# 1. 驗證配置
bash scripts/validate_deployment.sh

# 2. 部署所有優化（包括私人倉庫）
kubectl apply -k cluster/overlays/prod/

# 3. 驗證部署
kubectl get all -n flowagent
kubectl get pdb,networkpolicy -n flowagent
```

### 選項 B: 僅部署私人倉庫

```bash
# 使用快速部署腳本
bash scripts/deploy_private_registry.sh

# 或手動部署
kubectl apply -k apps/registry/
```

### 選項 C: 從零開始

```bash
# 1. 初始化 GKE 集群
bash scripts/oneclick_gke_init.sh

# 2. 部署所有服務
kubectl apply -k cluster/overlays/prod/

# 3. 部署監控
kubectl apply -k cluster/overlays/monitoring/
```

---

## 🔐 私人容器倉庫快速使用

### 訪問信息

- **集群內地址**: `registry.flowagent.svc.cluster.local:5000`
- **NodePort 訪問**: `${NODE_IP}:30500`
- **用戶名**: `admin`
- **密碼**: `FlowAgent2026!`

⚠️ **重要**: 生產環境請立即更改預設密碼！

### 快速開始

```bash
# 1. 登入 Registry
docker login registry.flowagent.svc.cluster.local:5000 \
  -u admin -p FlowAgent2026!

# 2. 推送鏡像
docker tag myapp:latest \
  registry.flowagent.svc.cluster.local:5000/myapp:latest
docker push \
  registry.flowagent.svc.cluster.local:5000/myapp:latest

# 3. 創建 ImagePullSecret
kubectl create secret docker-registry registry-cred \
  --docker-server=registry.flowagent.svc.cluster.local:5000 \
  --docker-username=admin \
  --docker-password=FlowAgent2026! \
  --namespace=flowagent

# 4. 在 Deployment 中使用
kubectl patch deployment myapp -n flowagent -p \
  '{"spec":{"template":{"spec":{"imagePullSecrets":[{"name":"registry-cred"}]}}}}'
```

---

## 📋 部署檢查清單

### 部署前檢查
- [ ] 已安裝 kubectl 和 kustomize
- [ ] 已配置 GKE 集群訪問
- [ ] 已創建 flowagent namespace
- [ ] 已運行配置驗證 (`bash scripts/validate_deployment.sh`)

### 部署後驗證
- [ ] 所有 Pods 處於 Running 狀態
- [ ] 所有服務正常運行
- [ ] NetworkPolicy 已應用
- [ ] PDB 已配置
- [ ] ServiceMonitor 已創建
- [ ] 私人倉庫可訪問
- [ ] 備份 CronJob 已設置

### 安全配置
- [ ] 已更改 Registry 預設密碼
- [ ] 已更改 MongoDB 密碼
- [ ] 已配置 TLS/SSL（推薦）
- [ ] 已設置監控告警
- [ ] 已配置備份策略

---

## 🛠️ 常用命令

### 查看部署狀態
```bash
# 查看所有資源
kubectl get all -n flowagent

# 查看安全配置
kubectl get networkpolicy,pdb -n flowagent

# 查看存儲
kubectl get pvc -n flowagent

# 查看定時任務
kubectl get cronjobs -n flowagent
```

### 查看日誌
```bash
# Module-A
kubectl logs -f deployment/module-a -n flowagent

# Orchestrator
kubectl logs -f deployment/orchestrator -n flowagent

# MongoDB
kubectl logs -f deployment/mongodb -n flowagent

# Registry
kubectl logs -f deployment/registry -n flowagent
```

### Registry 管理
```bash
# 查看 Registry 狀態
kubectl exec -it deployment/registry -n flowagent -- \
  wget -qO- http://localhost:5000/v2/

# 列出所有鏡像
kubectl exec -it deployment/registry -n flowagent -- \
  wget -qO- http://localhost:5000/v2/_catalog

# 手動垃圾回收
kubectl create job --from=cronjob/registry-cleanup \
  registry-cleanup-manual -n flowagent
```

### 備份管理
```bash
# 查看 MongoDB 備份
kubectl exec -it deployment/mongodb -n flowagent -- \
  ls -lh /backup/

# 手動觸發備份
kubectl create job --from=cronjob/mongodb-backup \
  mongodb-backup-manual -n flowagent
```

---

## 📚 完整文檔

### 主要文檔
- **[DEPLOYMENT_OPTIMIZATION.md](./DEPLOYMENT_OPTIMIZATION.md)** - 完整優化報告
- **[apps/registry/README.md](./apps/registry/README.md)** - 私人倉庫完整文檔
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - 詳細部署指南
- **[DEPLOYMENT_QUICK_REFERENCE.md](./DEPLOYMENT_QUICK_REFERENCE.md)** - 快速參考

### 腳本和工具
- **scripts/deploy_private_registry.sh** - 私人倉庫快速部署
- **scripts/oneclick_gke_init.sh** - GKE 集群一鍵初始化
- **scripts/validate_deployment.sh** - 配置驗證

---

## 🎯 重要配置文件位置

### 應用配置
```
apps/
├── module-a/
│   ├── deployment.yaml      # ✅ 優化
│   ├── configmap.yaml       # ⭐ 新增
│   ├── networkpolicy.yaml   # ⭐ 新增
│   ├── pdb.yaml            # ⭐ 新增
│   └── servicemonitor.yaml # ⭐ 新增
├── orchestrator/
│   ├── deployment.yaml      # ✅ 優化
│   ├── configmap.yaml       # ⭐ 新增
│   ├── networkpolicy.yaml   # ⭐ 新增
│   ├── pdb.yaml            # ⭐ 新增
│   └── servicemonitor.yaml # ⭐ 新增
├── mongodb/
│   ├── deployment.yaml      # ✅ 優化
│   ├── networkpolicy.yaml   # ⭐ 新增
│   └── backup-cronjob.yaml # ⭐ 新增
└── registry/               # ⭐⭐⭐ 全新
    ├── deployment.yaml
    ├── pvc.yaml
    ├── secret.yaml
    ├── networkpolicy.yaml
    ├── cleanup-cronjob.yaml
    ├── configmap.yaml
    ├── kustomization.yaml
    └── README.md
```

---

## ⚠️ 重要提示

### 安全警告
1. **立即更改所有預設密碼**
   - Registry: `apps/registry/secret.yaml`
   - MongoDB: `apps/mongodb/secret.yaml`

2. **生產環境建議**
   - 配置 TLS/SSL
   - 啟用審計日誌
   - 設置監控告警
   - 定期安全掃描

3. **備份策略**
   - MongoDB 每日自動備份
   - 手動驗證備份可恢復性
   - 考慮異地備份

---

## 🆘 故障排除

### Registry 無法啟動
```bash
# 檢查 Pod 狀態
kubectl describe pod -l app=registry -n flowagent

# 檢查 PVC
kubectl describe pvc registry-pvc -n flowagent

# 檢查 Secret
kubectl get secret registry-auth registry-secret -n flowagent
```

### 服務無法訪問
```bash
# 檢查 NetworkPolicy
kubectl describe networkpolicy -n flowagent

# 測試連接
kubectl run test --rm -it --image=curlimages/curl -n flowagent -- \
  curl http://module-a:8080/health
```

### 備份失敗
```bash
# 檢查 CronJob
kubectl describe cronjob mongodb-backup -n flowagent

# 查看 Job 日誌
kubectl logs -l app=mongodb-backup -n flowagent
```

---

## 📞 獲取幫助

如有問題，請查看：
1. **完整文檔**: `DEPLOYMENT_OPTIMIZATION.md`
2. **Registry 文檔**: `apps/registry/README.md`
3. **部署指南**: `DEPLOYMENT.md`
4. **故障排除**: 各文檔的故障排除章節

---

## ✅ 下一步

1. [ ] 完成部署
2. [ ] 更改所有預設密碼
3. [ ] 測試私人倉庫功能
4. [ ] 配置 CI/CD 使用私人倉庫
5. [ ] 設置監控告警
6. [ ] 配置 TLS/SSL
7. [ ] 制定災難恢復計劃

---

**版本**: v2.0.0  
**最後更新**: 2026-02-04  
**維護**: FlowAgent Team

🎉 **恭喜！您的專業部署優化已完成！**
