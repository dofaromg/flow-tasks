#!/bin/bash
# Ultimate AI Video System - One-Click Deployment Script
# 小影AI終極版 - 一鍵部署腳本

set -e

echo "🚀 Starting Ultimate AI Video System Deployment..."
echo "=================================================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查是否為root
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${YELLOW}⚠️  建議使用root權限運行此腳本${NC}"
        echo "請使用: sudo bash $0"
        read -p "是否繼續？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 檢查系統要求
check_requirements() {
    echo -e "\n${GREEN}📋 檢查系統要求...${NC}"
    
    # 檢查GPU
    if ! command -v nvidia-smi &> /dev/null; then
        echo -e "${RED}❌ 未檢測到NVIDIA GPU或驅動${NC}"
        exit 1
    fi
    
    GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
    echo -e "${GREEN}✅ 檢測到 $GPU_COUNT 塊GPU${NC}"
    
    # 檢查記憶體
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    echo -e "${GREEN}✅ 總記憶體: ${TOTAL_MEM}GB${NC}"
    
    if [ "$TOTAL_MEM" -lt 500 ]; then
        echo -e "${YELLOW}⚠️  記憶體少於500GB，建議使用3TB以獲得最佳性能${NC}"
    fi
    
    # 檢查磁碟空間
    DISK_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    echo -e "${GREEN}✅ 可用磁碟空間: ${DISK_SPACE}GB${NC}"
    
    if [ "$DISK_SPACE" -lt 500 ]; then
        echo -e "${RED}❌ 磁碟空間不足，建議至少500GB用於模型存儲${NC}"
        exit 1
    fi
}

# 安裝Python依賴
install_python_deps() {
    echo -e "\n${GREEN}📦 安裝Python依賴...${NC}"
    
    # 檢查Python版本
    if ! command -v python3.10 &> /dev/null; then
        echo -e "${YELLOW}⚠️  未檢測到Python 3.10，嘗試使用系統Python${NC}"
        PYTHON_CMD=python3
    else
        PYTHON_CMD=python3.10
    fi
    
    echo "使用Python: $PYTHON_CMD"
    $PYTHON_CMD --version
    
    # 升級pip
    $PYTHON_CMD -m pip install --upgrade pip
    
    # 安裝基礎依賴
    $PYTHON_CMD -m pip install -r requirements.txt
    
    # 安裝PyTorch (CUDA 11.8)
    $PYTHON_CMD -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    
    # 安裝額外依賴
    $PYTHON_CMD -m pip install \
        fastapi uvicorn[standard] \
        python-multipart websockets \
        pyyaml psutil \
        numpy pillow opencv-python \
        librosa soundfile scipy
    
    echo -e "${GREEN}✅ Python依賴安裝完成${NC}"
}

# 創建目錄結構
setup_directories() {
    echo -e "\n${GREEN}📁 創建目錄結構...${NC}"
    
    mkdir -p models/{checkpoints,cache}
    mkdir -p workspaces/{admin,parent1,parent2,child1,child2}/{uploads,outputs}
    mkdir -p shared/{templates,music,effects,fonts,family_album}
    mkdir -p logs
    
    echo -e "${GREEN}✅ 目錄結構創建完成${NC}"
}

# 下載模型（占位符）
download_models() {
    echo -e "\n${GREEN}📥 準備模型下載...${NC}"
    echo -e "${YELLOW}⚠️  注意：實際部署時需要下載約200GB的AI模型${NC}"
    echo -e "${YELLOW}⚠️  此腳本僅創建占位符，真實模型需要從HuggingFace等平台下載${NC}"
    
    # 創建模型目錄占位符
    MODELS=(
        "SadTalker_V2"
        "MuseTalk"
        "LivePortrait"
        "GeneFacePlusPlus"
        "F5-TTS-V2"
        "CosyVoice"
        "GPT-SoVITS-V2"
        "XTTS-V3"
        "Real-ESRGAN"
        "GFPGAN"
    )
    
    for model in "${MODELS[@]}"; do
        mkdir -p "models/checkpoints/$model"
        echo "Placeholder for $model" > "models/checkpoints/$model/README.txt"
    done
    
    echo -e "${GREEN}✅ 模型目錄準備完成${NC}"
}

# 配置環境變量
setup_env() {
    echo -e "\n${GREEN}⚙️  配置環境變量...${NC}"
    
    cat > .env.ultimate <<EOF
# Ultimate AI Video System Environment Variables
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
MODEL_BASE_PATH=./models
WORKSPACE_BASE_PATH=./workspaces
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
EOF
    
    echo -e "${GREEN}✅ 環境變量配置完成${NC}"
}

# 啟動服務
start_service() {
    echo -e "\n${GREEN}🚀 啟動服務...${NC}"
    
    # 檢查端口
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  端口8000已被佔用${NC}"
        read -p "是否停止現有服務並重啟？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pkill -f "main_ultimate.py" || true
            sleep 2
        else
            exit 1
        fi
    fi
    
    # 啟動FastAPI服務
    echo "正在啟動Ultimate AI Video System..."
    nohup python3 main_ultimate.py > logs/ultimate_system.log 2>&1 &
    
    echo $! > logs/ultimate_system.pid
    
    sleep 5
    
    # 檢查服務是否啟動
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✅ 服務已成功啟動！${NC}"
        echo -e "\n${GREEN}================================================${NC}"
        echo -e "${GREEN}🎉 部署完成！${NC}"
        echo -e "${GREEN}================================================${NC}"
        echo -e "\n訪問地址："
        echo -e "  ${GREEN}http://localhost:8000${NC}"
        echo -e "  ${GREEN}http://$(hostname -I | awk '{print $1}'):8000${NC}"
        echo -e "\nAPI文檔："
        echo -e "  ${GREEN}http://localhost:8000/docs${NC}"
        echo -e "\n查看日誌："
        echo -e "  ${YELLOW}tail -f logs/ultimate_system.log${NC}"
        echo -e "\n停止服務："
        echo -e "  ${YELLOW}kill \$(cat logs/ultimate_system.pid)${NC}"
    else
        echo -e "${RED}❌ 服務啟動失敗，請查看日誌：${NC}"
        echo -e "  ${YELLOW}tail logs/ultimate_system.log${NC}"
        exit 1
    fi
}

# 主函數
main() {
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║      Ultimate AI Video System - Deployment Script    ║"
    echo "║                小影AI終極版 - 部署腳本               ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    check_root
    check_requirements
    install_python_deps
    setup_directories
    download_models
    setup_env
    start_service
    
    echo -e "\n${GREEN}🎊 祝您使用愉快！過年快樂！🎊${NC}\n"
}

# 運行主函數
main "$@"
