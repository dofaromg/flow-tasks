#!/bin/bash
# RootLaw Package 快速部署腳本
# Quick deployment script for RootLaw Package

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 顯示橫幅
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║        RootLaw Package 快速部署工具 v1.0                    ║
║        Quick Deployment Tool for RootLaw Package            ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 未安裝${NC}"
    exit 1
fi

# 檢查 Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git 未安裝${NC}"
    exit 1
fi

# 顯示菜單
echo -e "${GREEN}請選擇部署模式：${NC}"
echo "1) 部署到單個倉庫 (測試模式 - 不提交)"
echo "2) 部署到單個倉庫 (完整模式 - 提交但不推送)"
echo "3) 部署到單個倉庫 (自動模式 - 提交並推送)"
echo "4) 批次部署 (從配置檔案)"
echo "5) 創建配置檔案範本"
echo "6) 查看使用說明"
echo "0) 退出"
echo ""
read -p "請輸入選項 [0-6]: " choice

case $choice in
    1)
        echo -e "${YELLOW}模式 1: 測試部署（僅複製檔案）${NC}"
        read -p "請輸入目標倉庫 URL: " repo_url
        read -p "請輸入目標分支 [main]: " branch
        branch=${branch:-main}
        
        echo -e "${BLUE}開始部署...${NC}"
        python3 scripts/deploy_rootlaw_package.py \
            --url "$repo_url" \
            --branch "$branch" \
            --verbose
        ;;
    
    2)
        echo -e "${YELLOW}模式 2: 完整部署（提交但不推送）${NC}"
        read -p "請輸入目標倉庫 URL: " repo_url
        read -p "請輸入目標分支 [main]: " branch
        branch=${branch:-main}
        
        echo -e "${BLUE}開始部署...${NC}"
        python3 scripts/deploy_rootlaw_package.py \
            --url "$repo_url" \
            --branch "$branch" \
            --commit \
            --verbose
        ;;
    
    3)
        echo -e "${YELLOW}模式 3: 自動部署（提交並推送）${NC}"
        echo -e "${RED}⚠️  警告：這將自動推送變更到遠端！${NC}"
        read -p "確定要繼續嗎？ [y/N]: " confirm
        
        if [[ $confirm == [yY] ]]; then
            read -p "請輸入目標倉庫 URL: " repo_url
            read -p "請輸入目標分支 [main]: " branch
            branch=${branch:-main}
            
            echo -e "${BLUE}開始部署...${NC}"
            python3 scripts/deploy_rootlaw_package.py \
                --url "$repo_url" \
                --branch "$branch" \
                --commit \
                --push \
                --verbose
        else
            echo -e "${YELLOW}已取消${NC}"
        fi
        ;;
    
    4)
        echo -e "${YELLOW}模式 4: 批次部署${NC}"
        read -p "請輸入配置檔案路徑 [rootlaw_deploy_config.json]: " config_file
        config_file=${config_file:-rootlaw_deploy_config.json}
        
        if [ ! -f "$config_file" ]; then
            echo -e "${RED}❌ 配置檔案不存在: $config_file${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}開始批次部署...${NC}"
        python3 scripts/deploy_rootlaw_package.py \
            --config "$config_file" \
            --verbose
        ;;
    
    5)
        echo -e "${YELLOW}模式 5: 創建配置檔案範本${NC}"
        read -p "請輸入配置檔案名稱 [my_deploy_config.json]: " config_name
        config_name=${config_name:-my_deploy_config.json}
        
        if [ -f "$config_name" ]; then
            echo -e "${RED}❌ 檔案已存在: $config_name${NC}"
            read -p "是否覆蓋？ [y/N]: " overwrite
            if [[ $overwrite != [yY] ]]; then
                echo -e "${YELLOW}已取消${NC}"
                exit 0
            fi
        fi
        
        cp rootlaw_deploy_config.example.json "$config_name"
        echo -e "${GREEN}✅ 配置檔案已創建: $config_name${NC}"
        echo -e "${BLUE}請編輯此檔案並添加您的倉庫資訊${NC}"
        ;;
    
    6)
        echo -e "${BLUE}查看完整使用說明...${NC}"
        if [ -f "ROOTLAW_DEPLOYMENT_GUIDE.md" ]; then
            less ROOTLAW_DEPLOYMENT_GUIDE.md
        else
            echo -e "${YELLOW}使用說明檔案不存在${NC}"
            echo "請參閱: https://github.com/dofaromg/FlowAgent.Runtime/blob/main/ROOTLAW_DEPLOYMENT_GUIDE.md"
        fi
        ;;
    
    0)
        echo -e "${GREEN}再見！${NC}"
        exit 0
        ;;
    
    *)
        echo -e "${RED}❌ 無效的選項${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              部署完成 / Deployment Complete       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 下一步：${NC}"
echo "1. 查看部署報告: RootLaw_Package_v1.midlock/DEPLOYMENT_REPORT.md"
echo "2. 審閱客製化的 Absorption_Map.md"
echo "3. 根據倉庫更新 Evidence_Index.md"
echo "4. 配置 CI/CD 執行自動合規檢查 (E-1)"
echo ""
echo -e "${YELLOW}🫶 怎麼過去，就怎麼回來${NC}"
