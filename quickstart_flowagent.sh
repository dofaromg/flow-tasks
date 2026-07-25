#!/bin/bash
# MrLiouAI Docker 快速啟動腳本
# Quick start script for MrLiouAI Docker container

set -e

echo "🧠 MrLiouAI Docker 快速部署"
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
echo "📦 正在建構 MrLiouAI Docker 映像..."
docker build -f Dockerfile.mrliouai -t mrliouai:v1 .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ MrLiouAI Docker 映像建構成功！"
    echo ""
    echo "🚀 啟動方式："
    echo "   基本啟動：        docker run -it mrliouai:v1"
    echo "   指定人格：        docker run -it mrliouai:v1 --persona wild.seed"
    echo "   回顧模式：        docker run -it mrliouai:v1 --review-mode"
    echo "   掛載數據目錄：     docker run -it -v \$(pwd)/mrliouai_data:/mrliouai/persona_data mrliouai:v1"
    echo ""
    echo "📖 完整說明請查看：MrLiouAI_Docker_Installation_Guide.md"
    echo ""
    
    # 詢問是否立即啟動
    read -p "是否立即啟動 MrLiouAI？ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🧠 啟動 MrLiouAI..."
        docker run -it mrliouai:v1
    fi
else
    echo ""
    echo "❌ 建構失敗！請檢查錯誤訊息。"
    exit 1
fi
