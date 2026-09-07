#!/bin/bash
# MongoDB 密碼生成與更新腳本 / MongoDB Password Generation and Update Script
#
# 此腳本用於生成安全的 MongoDB 密碼並更新相關配置
# This script generates secure MongoDB passwords and updates related configurations
#
# 使用方法 / Usage:
#   bash scripts/generate_password.sh          # 生成新密碼並顯示
#   bash scripts/generate_password.sh --apply  # 生成並應用到本地檔案

set -e

# 顏色輸出 / Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 生成安全密碼 / Generate secure password
generate_password() {
    # 使用 openssl 生成 32 字節的隨機密碼
    # Generate 32-byte random password using openssl
    openssl rand -base64 32 | tr -d '\n'
}

# 顯示標題 / Display header
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║        MongoDB 密碼生成工具 / Password Generator              ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 生成新密碼 / Generate new password
NEW_PASSWORD=$(generate_password)

log_info "已生成新的 MongoDB 密碼 / New MongoDB password generated"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}新密碼 / New Password:${NC}"
echo ""
echo "  $NEW_PASSWORD"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 如果使用 --apply 參數，則應用到檔案 / Apply to files if --apply flag is used
if [ "$1" == "--apply" ]; then
    log_warning "⚠️  此操作將更新本地配置檔案（不會提交到 Git）"
    log_warning "⚠️  This will update local config files (NOT committed to Git)"
    echo ""
    read -p "確定要繼續嗎？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "正在更新配置檔案..."
        
        # 創建 .env 檔案 / Create .env file
        if [ -f .env ]; then
            log_warning ".env 檔案已存在，創建備份..."
            cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        fi
        
        cat > .env << EOF
# FlowAgent MongoDB 密碼配置 / MongoDB Password Configuration
# 生成日期 / Generated: $(date +"%Y-%m-%d %H:%M:%S")
# 
# ⚠️  重要：此檔案包含敏感資訊，請勿提交到 Git！
# ⚠️  IMPORTANT: This file contains sensitive data, DO NOT commit to Git!

MONGODB_PASSWORD=$NEW_PASSWORD
MONGODB_URI=mongodb://admin:$NEW_PASSWORD@mongodb:27017
EOF
        
        log_success "已創建 .env 檔案"
        
        # 確保 .env 在 .gitignore 中 / Ensure .env is in .gitignore
        if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
            echo ".env" >> .gitignore
            log_success "已添加 .env 到 .gitignore"
        fi
        
        log_success "配置已更新！"
        echo ""
        log_info "下一步操作 / Next Steps:"
        echo ""
        echo "  1. Kubernetes 部署 / For Kubernetes deployment:"
        echo "     kubectl create secret generic mongodb-secret \\"
        echo "       --from-literal=password='$NEW_PASSWORD' \\"
        echo "       --namespace=flowagent \\"
        echo "       --dry-run=client -o yaml | kubectl apply -f -"
        echo ""
        echo "  2. Docker Compose 本地測試 / For local Docker Compose:"
        echo "     docker-compose --env-file .env up -d"
        echo ""
        echo "  3. Google Secret Manager (生產環境推薦 / Recommended for production):"
        echo "     echo '$NEW_PASSWORD' | gcloud secrets create mongodb-password --data-file=-"
        echo ""
    else
        log_info "操作已取消 / Operation cancelled"
    fi
else
    log_info "使用方法 / Usage Instructions:"
    echo ""
    echo "  1. 複製上方密碼並安全保存 / Copy the password above and store it securely"
    echo ""
    echo "  2. 應用到 Kubernetes / Apply to Kubernetes:"
    echo "     kubectl create secret generic mongodb-secret \\"
    echo "       --from-literal=password='$NEW_PASSWORD' \\"
    echo "       --namespace=flowagent \\"
    echo "       --dry-run=client -o yaml | kubectl apply -f -"
    echo ""
    echo "  3. 或使用 --apply 參數自動更新本地配置 / Or use --apply to update local config:"
    echo "     bash scripts/generate_password.sh --apply"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log_warning "安全提醒 / Security Reminder:"
echo "  • 請勿將密碼提交到 Git / Do not commit passwords to Git"
echo "  • 使用 Secret Manager 管理生產環境密碼 / Use Secret Manager for production"
echo "  • 定期輪換密碼 / Rotate passwords regularly"
echo ""
