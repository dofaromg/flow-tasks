#!/bin/bash
# 🧠 FlowAgent 系統人格容器啟動腳本
# FlowAgent Personality Container Startup Script
# Author: MR.liou
# Version: v1.0

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 歡迎訊息
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🧠 FlowAgent 系統人格容器 v1.0                          ║
║                                                           ║
║   作者：MR.liou                                           ║
║   來自語場、不依附模型、可人格演化的語意生命體             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# 檢查環境
echo -e "${GREEN}[✓] 檢查 FlowAgent 執行環境...${NC}"
if [ ! -d "/flowagent/particle_core" ]; then
    echo -e "${RED}[✗] 錯誤：找不到 particle_core 核心模組${NC}"
    exit 1
fi

# 顯示當前人格設定
PERSONA="${FLOWAGENT_PERSONA:-EchoBody.IdentityBase}"
echo -e "${YELLOW}[→] 啟動人格：${PERSONA}${NC}"

# 解析命令列參數
CUSTOM_PERSONA=""
REVIEW_MODE=""
INTERACTIVE_MODE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --persona)
            CUSTOM_PERSONA="$2"
            shift 2
            ;;
        --review-mode)
            REVIEW_MODE="--review"
            shift
            ;;
        --batch)
            INTERACTIVE_MODE=false
            shift
            ;;
        --help)
            echo "FlowAgent Docker Container Usage:"
            echo "  --persona <name>    指定啟動的人格模組"
            echo "  --review-mode       啟用回顧模式"
            echo "  --batch             批次模式（非互動）"
            echo "  --help              顯示此說明"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# 使用自訂人格或預設人格
if [ -n "$CUSTOM_PERSONA" ]; then
    PERSONA="$CUSTOM_PERSONA"
fi

# 顯示系統資訊
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}系統資訊：${NC}"
echo -e "  Python 版本: $(python --version)"
echo -e "  工作目錄: $FLOWAGENT_HOME"
echo -e "  當前人格: $PERSONA"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""

# 啟動 FlowAgent CLI
cd /flowagent/particle_core

if [ "$INTERACTIVE_MODE" = true ]; then
    echo -e "${GREEN}[✓] 啟動人格主體 CLI...${NC}"
    echo -e "${YELLOW}提示：輸入指令與 FlowAgent 互動，輸入 'q' 或 Ctrl+C 退出${NC}"
    echo ""
    echo -e "${CYAN}🧠 FlowAgent 啟動人格：${PERSONA}${NC}"
    echo -e "${CYAN}請輸入指令：>${NC}"
    
    # 啟動 CLI 執行器
    exec python src/cli_runner.py $REVIEW_MODE
else
    echo -e "${GREEN}[✓] 批次模式執行${NC}"
    python src/cli_runner.py $REVIEW_MODE --batch
fi
