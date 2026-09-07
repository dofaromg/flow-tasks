#!/bin/bash
# FlowAgent 實際部署腳本 (Actual Deployment Script)
# 
# 此腳本將執行完整的生產環境部署流程
# This script performs a complete production deployment
#
# 使用方法 / Usage:
# bash scripts/actual_deploy.sh [--skip-cluster-init] [--skip-monitoring] [--dry-run]

set -e

# 顏色輸出 / Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置參數 / Configuration
export PROJECT_ID=${PROJECT_ID:-flowmemorysync}
export REGION=${REGION:-asia-east1}
export ZONE=${ZONE:-asia-east1-a}
export CLUSTER_NAME=${CLUSTER_NAME:-modular-cluster}
export NS=${NS:-flowagent}

# 解析命令行參數 / Parse command line arguments
SKIP_CLUSTER_INIT=false
SKIP_MONITORING=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-cluster-init)
            SKIP_CLUSTER_INIT=true
            shift
            ;;
        --skip-monitoring)
            SKIP_MONITORING=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "未知參數: $1"
            echo "用法: $0 [--skip-cluster-init] [--skip-monitoring] [--dry-run]"
            exit 1
            ;;
    esac
done

# 日誌函數 / Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

# 檢查必要工具 / Check required tools
check_prerequisites() {
    log_step "檢查前置需求 / Checking Prerequisites"
    
    local missing_tools=()
    
    if ! command -v gcloud &> /dev/null; then
        missing_tools+=("gcloud")
    fi
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v kustomize &> /dev/null; then
        missing_tools+=("kustomize")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "缺少必要工具: ${missing_tools[*]}"
        log_info "請安裝缺少的工具後再試"
        exit 1
    fi
    
    log_success "所有必要工具已就緒"
}

# 驗證配置文件 / Validate configuration files
validate_configs() {
    log_step "驗證配置文件 / Validating Configuration Files"
    
    log_info "執行配置驗證腳本..."
    if bash scripts/validate_deployment.sh; then
        log_success "配置文件驗證通過"
    else
        log_error "配置文件驗證失敗"
        exit 1
    fi
}

# 初始化 GKE 叢集 / Initialize GKE cluster
init_cluster() {
    if [ "$SKIP_CLUSTER_INIT" = true ]; then
        log_warning "跳過叢集初始化"
        return
    fi
    
    log_step "初始化 GKE 叢集 / Initializing GKE Cluster"
    
    log_info "設定 GCP 專案: $PROJECT_ID"
    gcloud config set project $PROJECT_ID
    
    log_info "啟用必要的 API..."
    gcloud services enable container.googleapis.com \
        artifactregistry.googleapis.com \
        compute.googleapis.com
    
    # 檢查叢集是否存在
    if gcloud container clusters describe $CLUSTER_NAME --zone $ZONE &> /dev/null; then
        log_success "叢集 $CLUSTER_NAME 已存在"
    else
        log_warning "叢集不存在，需要建立新叢集"
        log_info "建立叢集可能需要 5-10 分鐘..."
        
        if [ "$DRY_RUN" = true ]; then
            log_info "[DRY RUN] 將建立叢集: $CLUSTER_NAME"
        else
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
            
            log_success "叢集建立完成"
        fi
    fi
    
    log_info "取得叢集憑證..."
    gcloud container clusters get-credentials $CLUSTER_NAME \
        --zone $ZONE \
        --project $PROJECT_ID
    
    log_success "叢集初始化完成"
}

# 建立命名空間 / Create namespaces
create_namespaces() {
    log_step "建立命名空間 / Creating Namespaces"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] 將建立命名空間: $NS, monitoring"
    else
        kubectl create namespace $NS --dry-run=client -o yaml | kubectl apply -f -
        kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
        log_success "命名空間建立完成"
    fi
}

# 部署應用程式 / Deploy applications
deploy_applications() {
    log_step "部署應用程式 / Deploying Applications"
    
    log_info "使用 Kustomize 建置清單..."
    kustomize build cluster/overlays/prod > /tmp/prod-manifests.yaml
    
    log_info "清單摘要:"
    echo "  - Deployments: $(grep -c 'kind: Deployment' /tmp/prod-manifests.yaml || echo 0)"
    echo "  - Services: $(grep -c 'kind: Service' /tmp/prod-manifests.yaml || echo 0)"
    echo "  - ConfigMaps: $(grep -c 'kind: ConfigMap' /tmp/prod-manifests.yaml || echo 0)"
    echo "  - Secrets: $(grep -c 'kind: Secret' /tmp/prod-manifests.yaml || echo 0)"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] 清單已生成至 /tmp/prod-manifests.yaml"
        log_info "使用以下命令查看: cat /tmp/prod-manifests.yaml"
    else
        log_info "部署到 GKE..."
        kubectl apply -f /tmp/prod-manifests.yaml
        log_success "應用程式部署完成"
    fi
}

# 部署監控 / Deploy monitoring
deploy_monitoring() {
    if [ "$SKIP_MONITORING" = true ]; then
        log_warning "跳過監控部署"
        return
    fi
    
    log_step "部署監控系統 / Deploying Monitoring"
    
    log_info "使用 Kustomize 建置監控清單..."
    kustomize build cluster/overlays/monitoring > /tmp/monitoring-manifests.yaml
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] 監控清單已生成至 /tmp/monitoring-manifests.yaml"
    else
        log_info "部署監控到 GKE..."
        kubectl apply -f /tmp/monitoring-manifests.yaml
        log_success "監控系統部署完成"
    fi
}

# 等待部署完成 / Wait for deployments
wait_for_deployments() {
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] 將等待部署完成"
        return
    fi
    
    log_step "等待部署完成 / Waiting for Deployments"
    
    local deployments=("mongodb" "module-a" "orchestrator" "nextjs-frontend")
    
    for deployment in "${deployments[@]}"; do
        log_info "等待 $deployment 部署完成..."
        if kubectl rollout status deployment/$deployment -n $NS --timeout=5m; then
            log_success "$deployment 部署成功"
        else
            log_error "$deployment 部署失敗"
            kubectl get pods -l app=$deployment -n $NS
            kubectl describe deployment/$deployment -n $NS
            exit 1
        fi
    done
    
    log_success "所有部署完成"
}

# 驗證部署 / Verify deployment
verify_deployment() {
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] 將驗證部署"
        return
    fi
    
    log_step "驗證部署 / Verifying Deployment"
    
    log_info "檢查 Pods 狀態..."
    kubectl get pods -n $NS
    
    log_info "檢查 Services..."
    kubectl get svc -n $NS
    
    log_info "檢查 Deployments..."
    kubectl get deployments -n $NS
    
    # 檢查是否有失敗的 Pods
    local failed_pods=$(kubectl get pods -n $NS --field-selector=status.phase!=Running,status.phase!=Succeeded --no-headers 2>/dev/null | wc -l)
    
    if [ "$failed_pods" -gt 0 ]; then
        log_warning "發現 $failed_pods 個非運行狀態的 Pods"
        kubectl get pods -n $NS --field-selector=status.phase!=Running,status.phase!=Succeeded
    else
        log_success "所有 Pods 運行正常"
    fi
}

# 獲取訪問資訊 / Get access information
get_access_info() {
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] 將顯示訪問資訊"
        return
    fi
    
    log_step "獲取訪問資訊 / Getting Access Information"
    
    log_info "等待 LoadBalancer 分配外部 IP..."
    sleep 10
    
    # Next.js Frontend
    local nextjs_ip=$(kubectl get svc nextjs-frontend -n $NS -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    if [ "$nextjs_ip" != "pending" ] && [ -n "$nextjs_ip" ]; then
        log_success "Next.js Frontend: http://$nextjs_ip"
    else
        log_warning "Next.js Frontend IP 尚未分配，請稍後使用以下命令查看:"
        echo "  kubectl get svc nextjs-frontend -n $NS"
    fi
    
    # Orchestrator
    local orch_ip=$(kubectl get svc orchestrator -n $NS -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    if [ "$orch_ip" != "pending" ] && [ -n "$orch_ip" ]; then
        log_success "Orchestrator: http://$orch_ip"
    else
        log_warning "Orchestrator IP 尚未分配，請稍後使用以下命令查看:"
        echo "  kubectl get svc orchestrator -n $NS"
    fi
}

# 生成部署報告 / Generate deployment report
generate_report() {
    log_step "生成部署報告 / Generating Deployment Report"
    
    local report_file="/tmp/flowagent-deployment-report-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "FlowAgent 實際部署報告"
        echo "======================================"
        echo "部署時間: $(date)"
        echo "專案 ID: $PROJECT_ID"
        echo "叢集名稱: $CLUSTER_NAME"
        echo "區域: $REGION"
        echo "可用區: $ZONE"
        echo "======================================"
        echo ""
        
        if [ "$DRY_RUN" = false ]; then
            echo "部署狀態:"
            kubectl get all -n $NS
            echo ""
            
            echo "服務端點:"
            kubectl get svc -n $NS
            echo ""
            
            echo "Pod 詳情:"
            kubectl get pods -n $NS -o wide
            echo ""
        else
            echo "模式: DRY RUN"
            echo "未執行實際部署"
        fi
        
    } > "$report_file"
    
    log_success "部署報告已生成: $report_file"
    
    if [ "$DRY_RUN" = false ]; then
        cat "$report_file"
    fi
}

# 主流程 / Main flow
main() {
    log_step "FlowAgent 實際部署開始 / Starting FlowAgent Actual Deployment"
    
    log_info "配置參數:"
    echo "  專案 ID: $PROJECT_ID"
    echo "  區域: $REGION"
    echo "  可用區: $ZONE"
    echo "  叢集名稱: $CLUSTER_NAME"
    echo "  命名空間: $NS"
    echo "  跳過叢集初始化: $SKIP_CLUSTER_INIT"
    echo "  跳過監控: $SKIP_MONITORING"
    echo "  Dry Run: $DRY_RUN"
    echo ""
    
    if [ "$DRY_RUN" = false ]; then
        read -p "確認繼續部署？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_warning "部署已取消"
            exit 0
        fi
    fi
    
    # 執行部署步驟
    check_prerequisites
    validate_configs
    init_cluster
    create_namespaces
    deploy_applications
    deploy_monitoring
    wait_for_deployments
    verify_deployment
    get_access_info
    generate_report
    
    log_step "部署完成 / Deployment Complete"
    
    if [ "$DRY_RUN" = false ]; then
        log_success "✅ FlowAgent 已成功部署到 GKE!"
        echo ""
        log_info "後續步驟:"
        echo "  1. 配置域名和 DNS (可選)"
        echo "  2. 設定 SSL/TLS 證書 (可選)"
        echo "  3. 配置備份策略"
        echo "  4. 設定監控告警"
        echo "  5. 查看日誌: kubectl logs -f -l app=<service-name> -n $NS"
        echo ""
        log_info "有用的命令:"
        echo "  查看所有資源: kubectl get all -n $NS"
        echo "  查看日誌: kubectl logs -f deployment/<name> -n $NS"
        echo "  擴展副本: kubectl scale deployment/<name> --replicas=N -n $NS"
        echo "  更新映像: kubectl set image deployment/<name> <container>=<image>:<tag> -n $NS"
    else
        log_info "這是 DRY RUN 模式，未執行實際部署"
        log_info "要執行實際部署，請移除 --dry-run 參數"
    fi
}

# 執行主流程 / Execute main flow
main "$@"
