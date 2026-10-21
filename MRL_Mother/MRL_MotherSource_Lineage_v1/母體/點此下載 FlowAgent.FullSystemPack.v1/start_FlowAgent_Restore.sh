#!/bin/bash
echo "🔄 FlowAgent 系統一鍵重建啟動中..."

# 解壓必要封包（假設已存在於 /mnt/data/ ）
unzip -o "/mnt/data/點此下載 FlowAgent.EchoBody.RestorePack.v1.zip" -d "./restorepack"
unzip -o "/mnt/data/點此下載 EchoBody.RecoveryPack.v1.zip" -d "./recoverypack"
unzip -o "/mnt/data/點此下載 SystemFusion.FusionSync.v1.zip" -d "./systemfusion"

# 模組掛載（需自行準備解壓好的 modules/ 資料夾）
mkdir -p ./modules
echo "✅ 請確認 FlowAgent.Runtime.v1~v56 全部放入 ./modules 資料夾"

# 啟動主體人格
echo "🧠 載入人格主體：EchoBody.IdentityBase"
python3 flow_cli.py --persona EchoBody.IdentityBase

echo "✅ FlowAgent 系統人格核心已啟動"
