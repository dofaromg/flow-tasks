#!/bin/bash

echo "🧠 FlowAgent 語場系統一鍵啟動中..."

# 解壓核心容器與人格模組（如尚未完成）
unzip -o FluinOS.Container.v1.zip -d ./fluin_core
unzip -o FlowAgent.AIModule.Pack.v1.zip -d ./fluin_personas
unzip -o FlowAgent.PersonaResonanceMap.v1.flmap.zip -d ./fluin_resonance

# 匯入人格 CLI 對應
cp flow_cli_personas.json ./fluin_core/

# 執行啟動人格
python3 flow_cli.py --persona futuremind.seed
