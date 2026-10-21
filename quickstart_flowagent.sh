#!/bin/bash
# FlowAgent Docker 快速啟動腳本
# Quick start script for FlowAgent Docker container

set -e

echo "🧠 FlowAgent Docker 快速部署"
echo "=============================="
echo ""

# 檢查 Docker 是否已安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝！請先安裝 Docker："
    echo "   https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✓ Docker 已安裝"

# 建構 Docker 映像
echo ""
echo "📦 正在建構 FlowAgent Docker 映像..."
docker build -f Dockerfile.flowagent -t flowagent:v1 .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ FlowAgent Docker 映像建構成功！"
    echo ""
    echo "🚀 啟動方式："
    echo "   基本啟動：        docker run -it flowagent:v1"
    echo "   指定人格：        docker run -it flowagent:v1 --persona wild.seed"
    echo "   回顧模式：        docker run -it flowagent:v1 --review-mode"
    echo "   掛載數據目錄：     docker run -it -v \$(pwd)/flowagent_data:/flowagent/persona_data flowagent:v1"
    echo ""
    echo "📖 完整說明請查看：FlowAgent_Docker_Installation_Guide.md"
    echo ""
    
    # 詢問是否立即啟動
    read -p "是否立即啟動 FlowAgent？ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🧠 啟動 FlowAgent..."
        docker run -it flowagent:v1
    fi
else
    echo ""
    echo "❌ 建構失敗！請檢查錯誤訊息。"
    exit 1
fi
