#!/bin/bash
# FlowAgent GKE 叢集一鍵初始化腳本
# 
# 使用方法：
# 1. 在 Google Cloud Shell 中執行此腳本
# 2. 或在本地安裝 gcloud CLI 後執行
#
# bash scripts/oneclick_gke_init.sh

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FlowAgent GKE 叢集初始化${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 配置參數（可修改）
export PROJECT_ID=${PROJECT_ID:-flowmemorysync}
export REGION=${REGION:-asia-east1}
export ZONE=${ZONE:-asia-east1-a}
export CLUSTER_NAME=${CLUSTER_NAME:-modular-cluster}
export NS=${NS:-flowagent}

echo -e "${YELLOW}配置參數：${NC}"
echo "  PROJECT_ID: $PROJECT_ID"
echo "  REGION: $REGION"
echo "  ZONE: $ZONE"
echo "  CLUSTER_NAME: $CLUSTER_NAME"
echo "  NAMESPACE: $NS"
echo ""

# 設定 GCP 專案
echo -e "${YELLOW}[1/8] 設定 GCP 專案...${NC}"
gcloud config set project $PROJECT_ID

# 啟用必要的 API
echo -e "${YELLOW}[2/8] 啟用必要的 Google Cloud APIs...${NC}"
gcloud services enable container.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable compute.googleapis.com

# 檢查叢集是否存在
echo -e "${YELLOW}[3/8] 檢查 GKE 叢集...${NC}"
if gcloud container clusters describe $CLUSTER_NAME --zone $ZONE --project $PROJECT_ID &> /dev/null; then
    echo -e "${GREEN}叢集 $CLUSTER_NAME 已存在${NC}"
else
    echo -e "${YELLOW}叢集不存在，建立新叢集可能需要 5-10 分鐘...${NC}"
    read -p "是否要建立新的 GKE 叢集？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud container clusters create $CLUSTER_NAME \
            --zone $ZONE \
            --num-nodes 3 \
            --machine-type e2-standard-2 \
            --enable-autoscaling \
            --min-nodes 2 \
            --max-nodes 10 \
            --enable-autorepair \
            --enable-autoupgrade \
            --release-channel regular
    else
        echo -e "${RED}已取消叢集建立${NC}"
        exit 1
    fi
fi

# 取得叢集憑證
echo -e "${YELLOW}[4/8] 取得 GKE 叢集憑證...${NC}"
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE --project $PROJECT_ID

# 建立命名空間
echo -e "${YELLOW}[5/8] 建立 Kubernetes 命名空間...${NC}"
kubectl create namespace $NS --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# 安裝 Prometheus Operator（可選）
echo -e "${YELLOW}[6/8] 安裝 Prometheus Operator...${NC}"
read -p "是否要安裝 Prometheus Operator？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -n monitoring -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml || echo "Prometheus Operator 安裝失敗或已存在"
fi

# 安裝 KEDA（可選）
echo -e "${YELLOW}[7/8] 安裝 KEDA...${NC}"
read -p "是否要安裝 KEDA (Kubernetes Event Driven Autoscaling)？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -f https://github.com/kedacore/keda/releases/download/v2.13.1/keda-2.13.1.yaml || echo "KEDA 安裝失敗或已存在"
fi

# 驗證安裝
echo -e "${YELLOW}[8/8] 驗證安裝...${NC}"
echo ""
echo -e "${GREEN}叢集資訊：${NC}"
kubectl cluster-info
echo ""
echo -e "${GREEN}節點狀態：${NC}"
kubectl get nodes
echo ""
echo -e "${GREEN}命名空間：${NC}"
kubectl get namespaces
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 初始化完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}下一步：${NC}"
echo "1. 使用 Kustomize 部署應用："
echo "   kubectl apply -k cluster/overlays/prod"
echo ""
echo "2. 或使用 ArgoCD GitOps 部署："
echo "   kubectl create namespace argocd"
echo "   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
echo "   kubectl apply -f argocd/app.yaml"
echo ""
echo "3. 查看部署狀態："
echo "   kubectl get all -n $NS"
echo ""
echo -e "${YELLOW}GCP 控制台連結：${NC}"
echo "  GKE: https://console.cloud.google.com/kubernetes/list?project=$PROJECT_ID"
echo "  Artifact Registry: https://console.cloud.google.com/artifacts?project=$PROJECT_ID"
echo ""
