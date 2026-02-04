# 🏗️ FlowAgent 私人容器倉庫
# FlowAgent Private Container Registry

這是 FlowAgent 專案的私人容器鏡像倉庫部署配置，使用 Docker Registry v2.8。

## 📦 組件說明

### 核心組件
- **Registry Service**: Docker Registry v2.8
- **Storage**: 100Gi 持久化存儲 (PVC)
- **Authentication**: Basic Auth (htpasswd)
- **Security**: NetworkPolicy + SecurityContext
- **Cleanup**: 每週自動垃圾回收 (CronJob)
- **Access**: NodePort 30500

### 檔案結構
```
apps/registry/
├── deployment.yaml        # Registry 部署和服務
├── pvc.yaml              # 持久化存儲聲明 (100Gi)
├── secret.yaml           # 認證和密鑰配置
├── networkpolicy.yaml    # 網絡安全策略
├── cleanup-cronjob.yaml  # 定期清理任務
├── configmap.yaml        # Registry 配置
├── kustomization.yaml    # Kustomize 配置
└── README.md             # 本文檔
```

## 🚀 快速部署

### 1. 部署私人倉庫

```bash
# 部署 Registry
kubectl apply -k apps/registry/

# 驗證部署狀態
kubectl get pods -n flowagent -l app=registry
kubectl get svc -n flowagent -l app=registry
kubectl get pvc -n flowagent -l app=registry

# 等待 Pod 就緒
kubectl wait --for=condition=ready pod -l app=registry -n flowagent --timeout=300s
```

### 2. 檢查服務狀態

```bash
# 查看 Registry 日誌
kubectl logs -f deployment/registry -n flowagent

# 測試 Registry 健康狀態
kubectl exec -it deployment/registry -n flowagent -- wget -qO- http://localhost:5000/v2/
```

## 🔐 訪問配置

### 預設認證信息
- **用戶名**: `admin`
- **密碼**: `FlowAgent2026!`

⚠️ **重要**: 生產環境務必修改預設密碼！

### 從集群內訪問

Registry 服務地址：`registry.flowagent.svc.cluster.local:5000`

```bash
# 登入 Registry（在 Pod 內）
docker login registry.flowagent.svc.cluster.local:5000 \
  -u admin -p FlowAgent2026!

# 推送鏡像
docker tag myapp:latest registry.flowagent.svc.cluster.local:5000/myapp:latest
docker push registry.flowagent.svc.cluster.local:5000/myapp:latest

# 拉取鏡像
docker pull registry.flowagent.svc.cluster.local:5000/myapp:latest
```

### 從集群外訪問（使用 NodePort）

⚠️ **安全警告**: NodePort 暴露在 30500 端口，使用 HTTP 未加密連接。

**生產環境建議**:
1. 使用 Ingress 並配置 TLS/SSL
2. 或限制 NodePort 訪問僅限內部網絡
3. 或配置防火牆規則限制訪問源

Registry 通過 NodePort 30500 暴露（僅用於開發/測試）。

```bash
# 獲取節點 IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')

# 如果沒有 ExternalIP，使用 InternalIP
if [ -z "$NODE_IP" ]; then
  NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
fi

echo "Registry URL: ${NODE_IP}:30500"

# ⚠️ 注意: 以下命令通過 HTTP 傳輸憑證，僅用於開發環境
# 登入 Registry（請先更改預設密碼！）
docker login ${NODE_IP}:30500 -u admin -p YourNewPassword

# 推送鏡像
docker tag myapp:latest ${NODE_IP}:30500/myapp:latest
docker push ${NODE_IP}:30500/myapp:latest
```

**生產環境配置 TLS**:
建議使用 Ingress Controller 配置 HTTPS:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: registry-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - registry.yourdomain.com
    secretName: registry-tls
  rules:
  - host: registry.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: registry
            port:
              number: 5000
```

## 🔑 配置 ImagePullSecret

為了讓 Kubernetes 能夠從私人倉庫拉取鏡像，需要創建 ImagePullSecret：

```bash
# 創建 ImagePullSecret
kubectl create secret docker-registry registry-cred \
  --docker-server=registry.flowagent.svc.cluster.local:5000 \
  --docker-username=admin \
  --docker-password=FlowAgent2026! \
  --namespace=flowagent

# 驗證 Secret
kubectl get secret registry-cred -n flowagent
```

### 在 Deployment 中使用

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: flowagent
spec:
  template:
    spec:
      containers:
      - name: myapp
        image: registry.flowagent.svc.cluster.local:5000/myapp:latest
      imagePullSecrets:
      - name: registry-cred
```

## 🔧 安全配置

### 更改預設密碼

```bash
# 安裝 htpasswd 工具
# Ubuntu/Debian: apt-get install apache2-utils
# CentOS/RHEL: yum install httpd-tools
# macOS: brew install httpd

# 生成新的 htpasswd
htpasswd -Bbn admin your-new-password

# 輸出範例:
# admin:$2y$05$...hash...

# 更新 apps/registry/secret.yaml 中的 htpasswd 欄位
# 然後重新部署
kubectl apply -f apps/registry/secret.yaml
kubectl rollout restart deployment/registry -n flowagent
```

### 更改 HTTP Secret

```bash
# 生成新的隨機密鑰
openssl rand -hex 32

# 更新 apps/registry/secret.yaml 中的 http-secret
# 然後重新部署
kubectl apply -f apps/registry/secret.yaml
kubectl rollout restart deployment/registry -n flowagent
```

## 📊 管理操作

### 查看倉庫內容

```bash
# 方法 1: 使用 curl（從集群內）
kubectl exec -it deployment/module-a -n flowagent -- \
  curl -u admin:FlowAgent2026! \
  http://registry.flowagent.svc.cluster.local:5000/v2/_catalog

# 方法 2: Port forward 到本地
kubectl port-forward svc/registry 5000:5000 -n flowagent &
curl -u admin:FlowAgent2026! http://localhost:5000/v2/_catalog

# 列出特定倉庫的標籤
curl -u admin:FlowAgent2026! \
  http://localhost:5000/v2/<repo-name>/tags/list
```

### 存儲管理

```bash
# 檢查存儲使用情況
kubectl exec -it deployment/registry -n flowagent -- df -h /var/lib/registry

# 查看詳細使用情況
kubectl exec -it deployment/registry -n flowagent -- du -sh /var/lib/registry/*

# 統計鏡像數量
kubectl exec -it deployment/registry -n flowagent -- \
  find /var/lib/registry/docker/registry/v2/repositories -maxdepth 1 -type d | wc -l
```

### 手動執行垃圾回收

```bash
# 方法 1: 通過 CronJob 手動創建 Job
kubectl create job --from=cronjob/registry-cleanup \
  registry-cleanup-manual -n flowagent

# 查看 Job 狀態
kubectl get jobs -n flowagent -l app=registry-cleanup

# 查看 Job 日誌
kubectl logs -l job-name=registry-cleanup-manual -n flowagent

# 方法 2: 直接在 Pod 中執行
kubectl exec -it deployment/registry -n flowagent -- \
  /bin/registry garbage-collect /etc/docker/registry/config.yml --delete-untagged
```

## 🔄 集成到 CI/CD

### 更新 CI/CD 配置使用私人倉庫

編輯 `.github/workflows/ci-build.yml`:

```yaml
env:
  PROJECT_ID: flowmemorysync
  REGION: asia-east1
  # 使用私人倉庫
  PRIVATE_REGISTRY: registry.flowagent.svc.cluster.local:5000
  # 或使用 NodePort (需要配置 NODE_IP)
  # PRIVATE_REGISTRY: ${NODE_IP}:30500

jobs:
  build-and-push:
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Build
      uses: docker/setup-buildx-action@v3

    # 選項 1: 推送到 GCP Artifact Registry (現有)
    - name: Push to GCP Registry
      run: |
        docker build -t asia-east1-docker.pkg.dev/$PROJECT_ID/flowagent/module-a:latest .
        docker push asia-east1-docker.pkg.dev/$PROJECT_ID/flowagent/module-a:latest

    # 選項 2: 同時推送到私人倉庫
    - name: Push to Private Registry
      run: |
        # Port forward to access registry
        kubectl port-forward svc/registry 5000:5000 -n flowagent &
        sleep 5
        
        # Login
        echo "${{ secrets.REGISTRY_PASSWORD }}" | docker login localhost:5000 \
          -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin
        
        # Tag and push
        docker tag asia-east1-docker.pkg.dev/$PROJECT_ID/flowagent/module-a:latest \
          localhost:5000/module-a:latest
        docker push localhost:5000/module-a:latest
```

### 設置 GitHub Secrets

在 GitHub repository settings 中添加：

```
REGISTRY_USERNAME=admin
REGISTRY_PASSWORD=FlowAgent2026!
```

## 📈 監控和日誌

### 查看 Registry 日誌

```bash
# 實時日誌
kubectl logs -f deployment/registry -n flowagent

# 最近 100 行日誌
kubectl logs --tail=100 deployment/registry -n flowagent

# 查看清理任務日誌
kubectl logs -l app=registry-cleanup -n flowagent

# 查看所有與 registry 相關的日誌
kubectl logs -l app=registry -n flowagent --all-containers=true
```

### 健康檢查

```bash
# 檢查 Registry 健康狀態
kubectl exec -it deployment/registry -n flowagent -- \
  wget -qO- http://localhost:5000/v2/

# 應該返回: {}

# 檢查 Pod 健康
kubectl get pods -l app=registry -n flowagent
kubectl describe pod -l app=registry -n flowagent
```

## 🛠️ 故障排除

### Registry Pod 無法啟動

```bash
# 檢查 Pod 狀態
kubectl describe pod -l app=registry -n flowagent

# 檢查事件
kubectl get events -n flowagent --sort-by='.lastTimestamp' | grep registry

# 檢查 PVC 狀態
kubectl describe pvc registry-pvc -n flowagent

# 檢查 Secret
kubectl get secret registry-secret registry-auth -n flowagent
```

### 認證失敗

```bash
# 驗證 Secret 內容
kubectl get secret registry-auth -n flowagent -o jsonpath='{.data.htpasswd}' | base64 -d

# 測試登入（從集群內）
kubectl run test-registry --rm -it --image=docker:latest -n flowagent -- sh
# 在容器內執行:
docker login registry.flowagent.svc.cluster.local:5000 -u admin -p FlowAgent2026!
```

### 無法推送/拉取鏡像

```bash
# 檢查 Service
kubectl get svc registry -n flowagent
kubectl describe svc registry -n flowagent

# 檢查 Endpoints
kubectl get endpoints registry -n flowagent

# 測試連接
kubectl run test-curl --rm -it --image=curlimages/curl -n flowagent -- \
  curl -u admin:FlowAgent2026! http://registry:5000/v2/_catalog
```

### 存儲空間不足

```bash
# 檢查存儲使用
kubectl exec -it deployment/registry -n flowagent -- df -h /var/lib/registry

# 選項 1: 運行垃圾回收
kubectl create job --from=cronjob/registry-cleanup registry-cleanup-now -n flowagent

# 選項 2: 擴展 PVC（如果 StorageClass 支持）
kubectl edit pvc registry-pvc -n flowagent
# 修改 storage size，例如從 100Gi 改為 200Gi

# 選項 3: 手動刪除舊鏡像
# 先標記要刪除的鏡像，然後運行垃圾回收
```

## 🔄 遷移現有鏡像

### 從 GCP Artifact Registry 遷移到私人倉庫

```bash
#!/bin/bash
# migrate-images.sh - 遷移鏡像腳本

SOURCE_REGISTRY="asia-east1-docker.pkg.dev/flowmemorysync/flowagent"
TARGET_REGISTRY="registry.flowagent.svc.cluster.local:5000"

# 鏡像列表
IMAGES=("module-a" "orchestrator")

# 登入目標倉庫
docker login ${TARGET_REGISTRY} -u admin -p FlowAgent2026!

for image in "${IMAGES[@]}"; do
  echo "Migrating ${image}..."
  
  # 拉取源鏡像
  docker pull ${SOURCE_REGISTRY}/${image}:latest
  
  # 重新標記
  docker tag ${SOURCE_REGISTRY}/${image}:latest ${TARGET_REGISTRY}/${image}:latest
  
  # 推送到私人倉庫
  docker push ${TARGET_REGISTRY}/${image}:latest
  
  echo "${image} migrated successfully"
done

echo "Migration completed!"
```

## 📚 相關文檔

- [Docker Registry 官方文檔](https://docs.docker.com/registry/)
- [Registry 配置參考](https://docs.docker.com/registry/configuration/)
- [垃圾回收機制](https://docs.docker.com/registry/garbage-collection/)
- [Registry API 規範](https://docs.docker.com/registry/spec/api/)
- [DEPLOYMENT.md](../../DEPLOYMENT.md) - 完整部署指南
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - 系統架構說明

## ⚠️ 生產環境注意事項

### 必須完成的安全配置

1. ✅ **立即更改預設密碼** - 修改 `secret.yaml` 中的認證信息
2. ✅ **更改 HTTP Secret** - 使用安全的隨機密鑰
3. ✅ **配置 TLS/SSL** - 為生產環境啟用 HTTPS（使用 Ingress + cert-manager）
4. ✅ **設置備份策略** - 定期備份 registry PVC
5. ✅ **監控存儲使用** - 設置告警防止存儲耗盡
6. ✅ **訪問控制** - 根據需要調整 NetworkPolicy
7. ✅ **定期清理** - 確保垃圾回收 CronJob 正常運行

### 建議的進階配置

1. **使用對象存儲** - 用 GCS/S3 替代 PVC 以提高可靠性
2. **啟用鏡像掃描** - 使用 Trivy 或 Clair 掃描漏洞
3. **設置配額** - 限制單個用戶/項目的存儲使用
4. **配置鏡像簽名** - 使用 Cosign 或 Notary 驗證鏡像
5. **高可用部署** - 多副本 + 對象存儲後端
6. **訪問日誌** - 啟用詳細的訪問日誌用於審計

## 🎯 部署檢查清單

部署私人倉庫前的檢查清單：

- [ ] 已部署 Kubernetes 集群
- [ ] 已創建 flowagent namespace
- [ ] 已更改預設密碼和密鑰
- [ ] 已配置存儲類（StorageClass）
- [ ] 已部署私人倉庫
- [ ] 已驗證 Registry Pod 正常運行
- [ ] 已測試推送/拉取鏡像
- [ ] 已創建 ImagePullSecret
- [ ] 已更新應用部署使用私人倉庫
- [ ] 已配置 CI/CD 流程
- [ ] 已設置監控告警
- [ ] 已配置備份策略
- [ ] 已記錄訪問憑證（安全存儲）

## 📞 支持

如有問題或需要幫助，請查看：
- 項目主文檔: `README.md`
- 部署指南: `DEPLOYMENT.md`
- 架構說明: `ARCHITECTURE.md`
- 快速參考: `DEPLOYMENT_QUICK_REFERENCE.md`

---

**版本**: v1.0.0  
**最後更新**: 2026-02-04  
**維護者**: FlowAgent Team
