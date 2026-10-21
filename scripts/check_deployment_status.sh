#!/bin/bash
# FlowAgent 部署狀態檢查腳本
# Check FlowAgent Deployment Status
#
# 使用方法 / Usage:
# bash scripts/check_deployment_status.sh

set -e

# 顏色輸出 / Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置參數 / Configuration
PROJECT_ID=${PROJECT_ID:-flowmemorysync}
ZONE=${ZONE:-asia-east1-a}
CLUSTER_NAME=${CLUSTER_NAME:-modular-cluster}
NS=${NS:-flowagent}

# 日誌函數 / Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 檢查 kubectl 是否可用
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安裝或不在 PATH 中"
        return 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "無法連接到 Kubernetes 叢集"
        log_info "請先執行: gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE --project $PROJECT_ID"
        return 1
    fi
    
    return 0
}

# 檢查命名空間
check_namespace() {
    log_section "檢查命名空間 / Checking Namespaces"
    
    if kubectl get namespace $NS &> /dev/null; then
        log_success "命名空間 '$NS' 存在"
    else
        log_error "命名空間 '$NS' 不存在"
        return 1
    fi
    
    if kubectl get namespace monitoring &> /dev/null; then
        log_success "命名空間 'monitoring' 存在"
    else
        log_warning "命名空間 'monitoring' 不存在"
    fi
}

# 檢查部署狀態
check_deployments() {
    log_section "檢查部署狀態 / Checking Deployments"
    
    local deployments=("mongodb" "module-a" "orchestrator" "nextjs-frontend")
    local all_ready=true
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment $deployment -n $NS &> /dev/null; then
            local ready=$(kubectl get deployment $deployment -n $NS -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
            local desired=$(kubectl get deployment $deployment -n $NS -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
            
            if [ "$ready" = "$desired" ] && [ "$ready" != "0" ]; then
                log_success "$deployment: $ready/$desired 副本就緒"
            else
                log_error "$deployment: $ready/$desired 副本就緒"
                all_ready=false
            fi
        else
            log_error "$deployment: 部署不存在"
            all_ready=false
        fi
    done
    
    if [ "$all_ready" = false ]; then
        return 1
    fi
}

# 檢查 Pod 狀態
check_pods() {
    log_section "檢查 Pod 狀態 / Checking Pod Status"
    
    local total_pods=$(kubectl get pods -n $NS --no-headers 2>/dev/null | wc -l)
    local running_pods=$(kubectl get pods -n $NS --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    
    log_info "總 Pod 數: $total_pods"
    log_info "運行中: $running_pods"
    
    echo ""
    kubectl get pods -n $NS -o wide
    echo ""
    
    # 檢查是否有問題的 Pods
    local problem_pods=$(kubectl get pods -n $NS --field-selector=status.phase!=Running,status.phase!=Succeeded --no-headers 2>/dev/null || true)
    
    if [ -n "$problem_pods" ]; then
        log_warning "發現非運行狀態的 Pods:"
        echo "$problem_pods"
        return 1
    else
        log_success "所有 Pods 運行正常"
    fi
}

# 檢查服務
check_services() {
    log_section "檢查服務 / Checking Services"
    
    kubectl get svc -n $NS
    echo ""
    
    # 檢查 LoadBalancer 服務的外部 IP
    local services=("orchestrator" "nextjs-frontend")
    
    for service in "${services[@]}"; do
        if kubectl get svc $service -n $NS &> /dev/null; then
            local external_ip=$(kubectl get svc $service -n $NS -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
            
            if [ -n "$external_ip" ]; then
                log_success "$service 外部 IP: http://$external_ip"
            else
                log_warning "$service 外部 IP 尚未分配 (pending)"
            fi
        fi
    done
}

# 檢查持久化存儲
check_pvc() {
    log_section "檢查持久化存儲 / Checking Persistent Volume Claims"
    
    if kubectl get pvc -n $NS &> /dev/null; then
        kubectl get pvc -n $NS
        echo ""
        
        local bound_pvcs=$(kubectl get pvc -n $NS --field-selector=status.phase=Bound --no-headers 2>/dev/null | wc -l)
        local total_pvcs=$(kubectl get pvc -n $NS --no-headers 2>/dev/null | wc -l)
        
        if [ "$bound_pvcs" = "$total_pvcs" ]; then
            log_success "所有 PVC 已綁定 ($bound_pvcs/$total_pvcs)"
        else
            log_warning "部分 PVC 未綁定 ($bound_pvcs/$total_pvcs)"
        fi
    else
        log_info "沒有 PVC"
    fi
}

# 檢查資源使用
check_resources() {
    log_section "檢查資源使用 / Checking Resource Usage"
    
    if kubectl top nodes &> /dev/null; then
        log_info "節點資源使用:"
        kubectl top nodes
        echo ""
    else
        log_warning "無法獲取節點資源使用 (metrics-server 可能未安裝)"
    fi
    
    if kubectl top pods -n $NS &> /dev/null; then
        log_info "Pod 資源使用:"
        kubectl top pods -n $NS
        echo ""
    else
        log_warning "無法獲取 Pod 資源使用 (metrics-server 可能未安裝)"
    fi
}

# 檢查最近的事件
check_events() {
    log_section "最近的事件 / Recent Events"
    
    log_info "最近 10 個事件:"
    kubectl get events -n $NS --sort-by='.lastTimestamp' | tail -10
}

# 健康檢查總結
health_summary() {
    log_section "健康檢查總結 / Health Check Summary"
    
    local status="healthy"
    
    # 檢查部署
    if ! check_deployments &> /dev/null; then
        status="unhealthy"
        log_error "部署狀態: 異常"
    else
        log_success "部署狀態: 正常"
    fi
    
    # 檢查 Pods
    local problem_pods=$(kubectl get pods -n $NS --field-selector=status.phase!=Running,status.phase!=Succeeded --no-headers 2>/dev/null | wc -l)
    if [ "$problem_pods" -gt 0 ]; then
        status="unhealthy"
        log_error "Pod 狀態: $problem_pods 個異常"
    else
        log_success "Pod 狀態: 正常"
    fi
    
    # 檢查服務
    local services_count=$(kubectl get svc -n $NS --no-headers 2>/dev/null | wc -l)
    if [ "$services_count" -eq 0 ]; then
        status="unhealthy"
        log_error "服務狀態: 無服務"
    else
        log_success "服務狀態: $services_count 個服務運行中"
    fi
    
    echo ""
    if [ "$status" = "healthy" ]; then
        log_success "整體狀態: 健康 ✓"
        return 0
    else
        log_error "整體狀態: 異常 ✗"
        return 1
    fi
}

# 快速診斷
quick_diagnosis() {
    log_section "快速診斷 / Quick Diagnosis"
    
    # 檢查失敗的 Pods
    local failed_pods=$(kubectl get pods -n $NS --field-selector=status.phase=Failed --no-headers 2>/dev/null || true)
    if [ -n "$failed_pods" ]; then
        log_warning "失敗的 Pods:"
        echo "$failed_pods"
        echo ""
    fi
    
    # 檢查 Pending 的 Pods
    local pending_pods=$(kubectl get pods -n $NS --field-selector=status.phase=Pending --no-headers 2>/dev/null || true)
    if [ -n "$pending_pods" ]; then
        log_warning "等待中的 Pods:"
        echo "$pending_pods"
        echo ""
    fi
    
    # 檢查最近的錯誤事件
    local error_events=$(kubectl get events -n $NS --field-selector type=Warning --sort-by='.lastTimestamp' 2>/dev/null | tail -5 || true)
    if [ -n "$error_events" ]; then
        log_warning "最近的警告事件:"
        echo "$error_events"
        echo ""
    fi
}

# 主流程
main() {
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  FlowAgent 部署狀態檢查              ║${NC}"
    echo -e "${GREEN}║  FlowAgent Deployment Status Check   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    
    log_info "專案: $PROJECT_ID"
    log_info "叢集: $CLUSTER_NAME"
    log_info "命名空間: $NS"
    echo ""
    
    # 檢查 kubectl
    if ! check_kubectl; then
        exit 1
    fi
    
    # 執行各項檢查
    check_namespace || true
    check_deployments || true
    check_pods || true
    check_services || true
    check_pvc || true
    check_resources || true
    check_events || true
    quick_diagnosis || true
    
    # 總結
    if health_summary; then
        exit 0
    else
        exit 1
    fi
}

# 執行主流程
main "$@"
