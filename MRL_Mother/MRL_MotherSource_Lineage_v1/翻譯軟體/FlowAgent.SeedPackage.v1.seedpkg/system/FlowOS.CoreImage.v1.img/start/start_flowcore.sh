#!/bin/bash

echo "🌐 啟動 FlowAgent 推理核心模組 FlowCore v1 ..."
echo "🧠 掛載核心模組：FlowCore.v1.flcore.zip"
echo "📦 掛載模組：guardian.mirror.trace.loop.bundle.v2.flpkg.zip"
echo "🔁 載入工具：FluinTraceInterpreter + loop.player"

# 解壓模組以模擬初始化（假設於 local 作業環境）
unzip -o FlowCore.v1.flcore.zip -d ./FlowCoreRuntime

# 執行測試模擬器（或可替換成 flow_cli.py 呼叫模組）
echo "▶️ 執行 trace 回放模擬器 ..."
python3 ./FlowCoreRuntime/tools/loop.player.py --input ./FlowCoreRuntime/modules/guardian.mirror.trace.loop.bundle.v2.flpkg.zip

echo "✅ FlowCore 啟動完畢！"
