#!/bin/bash
# Particle Satellite Network System Startup Script
# 粒子AI未來星鏈平行粒子雲網路系統啟動腳本

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}🚀 粒子AI未來星鏈平行粒子雲網路系統${NC}"
echo -e "${CYAN}   Particle AI Satellite Network System${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# Check if we're in the correct directory
if [ ! -d "particle_satellite_network" ]; then
    echo -e "${RED}Error: particle_satellite_network directory not found${NC}"
    echo -e "${YELLOW}Please run this script from the repository root${NC}"
    exit 1
fi

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -q -r particle_satellite_network/requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Start system components
echo -e "${MAGENTA}Starting system components...${NC}"
echo ""

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start GEO Layer
echo -e "${GREEN}📡 Starting GEO Layer - 語場核心層...${NC}"
python3 -m particle_satellite_network.core.satellite_layers.geo_layer &
GEO_PID=$!
echo -e "${GREEN}   PID: $GEO_PID${NC}"
sleep 1

# Start MEO Layer
echo -e "${YELLOW}🛰️  Starting MEO Layer - 邏輯管道層...${NC}"
python3 -m particle_satellite_network.core.satellite_layers.meo_layer &
MEO_PID=$!
echo -e "${YELLOW}   PID: $MEO_PID${NC}"
sleep 1

# Start LEO Layer
echo -e "${CYAN}✨ Starting LEO Layer - 粒子執行層...${NC}"
python3 -m particle_satellite_network.core.satellite_layers.leo_layer &
LEO_PID=$!
echo -e "${CYAN}   PID: $LEO_PID${NC}"
sleep 1

# Start Ground Layer
echo -e "${BLUE}🌍 Starting Ground Layer - 地面介面層...${NC}"
python3 -m particle_satellite_network.core.satellite_layers.ground_layer &
GROUND_PID=$!
echo -e "${BLUE}   PID: $GROUND_PID${NC}"
sleep 1

echo ""
echo -e "${GREEN}✅ All satellite layers started successfully!${NC}"
echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}System Information${NC}"
echo -e "${CYAN}================================================${NC}"
echo -e "${GREEN}GEO Layer PID:    $GEO_PID${NC}"
echo -e "${YELLOW}MEO Layer PID:    $MEO_PID${NC}"
echo -e "${CYAN}LEO Layer PID:    $LEO_PID${NC}"
echo -e "${BLUE}Ground Layer PID: $GROUND_PID${NC}"
echo ""
echo -e "${MAGENTA}📊 To view logs: tail -f *.log${NC}"
echo -e "${MAGENTA}🛑 To stop: kill $GEO_PID $MEO_PID $LEO_PID $GROUND_PID${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for interrupt signal
trap "kill $GEO_PID $MEO_PID $LEO_PID $GROUND_PID 2>/dev/null; echo -e '\n${RED}System stopped${NC}'; exit" INT TERM

# Keep script running
wait
