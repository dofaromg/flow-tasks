#!/bin/bash
# 快速部署私人容器倉庫
# Quick Deploy Private Container Registry

set -e

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FlowAgent 私人倉庫快速部署${NC}"
echo -e "${GREEN}FlowAgent Private Registry Quick Deploy${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 配置
NS=flowagent

echo -e "${YELLOW}[1/5] 確認命名空間...${NC}"
kubectl create namespace $NS --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✅ 命名空間就緒${NC}"
echo ""

echo -e "${YELLOW}[2/5] 部署私人倉庫...${NC}"
kubectl apply -k apps/registry/
echo -e "${GREEN}✅ 私人倉庫部署完成${NC}"
echo ""

echo -e "${YELLOW}[3/5] 等待 Registry Pod 就緒...${NC}"
kubectl wait --for=condition=ready pod -l app=registry -n $NS --timeout=300s || {
    echo -e "${RED}❌ Registry Pod 啟動超時${NC}"
    echo "檢查 Pod 狀態:"
    kubectl get pods -l app=registry -n $NS
    kubectl describe pod -l app=registry -n $NS
    exit 1
}
echo -e "${GREEN}✅ Registry Pod 就緒${NC}"
echo ""

echo -e "${YELLOW}[4/5] 驗證 Registry 服務...${NC}"
sleep 5
kubectl exec -it deployment/registry -n $NS -- wget -qO- http://localhost:5000/v2/ || {
    echo -e "${RED}❌ Registry 健康檢查失敗${NC}"
    kubectl logs deployment/registry -n $NS --tail=50
    exit 1
}
echo -e "${GREEN}✅ Registry 服務正常${NC}"
echo ""

echo -e "${YELLOW}[5/5] 創建 ImagePullSecret...${NC}"

# Check if password is still the default
DEFAULT_PASSWORD="FlowAgent2026!"
if kubectl get secret registry-auth -n $NS -o jsonpath='{.data.htpasswd}' 2>/dev/null | base64 -d | grep -q "\$2y\$05\$HqvOB0fOkH1ZZ1xd6QbaQ"; then
  echo -e "${RED}⚠️  警告: 檢測到使用預設密碼！${NC}"
  echo -e "${RED}⚠️  生產環境中必須更改密碼！${NC}"
  echo ""
  read -p "輸入新密碼（或按 Enter 繼續使用預設密碼 - 僅用於開發）: " NEW_PASSWORD
  if [ ! -z "$NEW_PASSWORD" ]; then
    DEFAULT_PASSWORD="$NEW_PASSWORD"
  fi
fi

kubectl create secret docker-registry registry-cred \
  --docker-server=registry.flowagent.svc.cluster.local:5000 \
  --docker-username=admin \
  --docker-password="${DEFAULT_PASSWORD}" \
  --namespace=$NS \
  --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✅ ImagePullSecret 創建完成${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 私人倉庫部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 顯示部署信息
echo -e "${YELLOW}📊 部署信息:${NC}"
echo ""
echo "Registry 服務:"
kubectl get svc registry -n $NS -o wide
echo ""
echo "Registry Pod:"
kubectl get pods -l app=registry -n $NS -o wide
echo ""
echo "Storage:"
kubectl get pvc registry-pvc -n $NS
echo ""

# 顯示訪問信息
echo -e "${YELLOW}🔐 訪問信息:${NC}"
echo ""
echo "集群內地址:"
echo "  registry.flowagent.svc.cluster.local:5000"
echo ""
echo "NodePort 訪問 (僅用於開發/測試):"
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
echo "  ${NODE_IP}:30500"
echo ""
echo "認證信息:"
echo "  用戶名: admin"
echo "  密碼: [請查看 Secret 或使用您設置的密碼]"
echo ""
echo -e "${RED}⚠️  安全提醒:${NC}"
echo -e "${RED}  1. 立即更改預設密碼（生產環境）${NC}"
echo -e "${RED}  2. NodePort 使用 HTTP 未加密，僅用於內部網絡${NC}"
echo -e "${RED}  3. 生產環境請配置 TLS/SSL (使用 Ingress)${NC}"
echo ""

# 顯示使用範例
echo -e "${YELLOW}📝 使用範例:${NC}"
echo ""
echo "# 登入 Registry (集群內):"
echo "docker login registry.flowagent.svc.cluster.local:5000 -u admin -p <your-password>"
echo ""
echo "# 推送鏡像:"
echo "docker tag myapp:latest registry.flowagent.svc.cluster.local:5000/myapp:latest"
echo "docker push registry.flowagent.svc.cluster.local:5000/myapp:latest"
echo ""
echo "# 在 Deployment 中使用:"
echo "kubectl patch deployment myapp -n $NS -p '{\"spec\":{\"template\":{\"spec\":{\"imagePullSecrets\":[{\"name\":\"registry-cred\"}]}}}}'"
echo ""

# 顯示下一步
echo -e "${YELLOW}🎯 下一步:${NC}"
echo "1. 更改預設密碼: 編輯 apps/registry/secret.yaml"
echo "2. 推送鏡像到私人倉庫"
echo "3. 更新應用部署使用私人倉庫"
echo "4. 配置 CI/CD 流程"
echo "5. 查看完整文檔: apps/registry/README.md"
echo ""

echo -e "${GREEN}✨ 部署完成！${NC}"
