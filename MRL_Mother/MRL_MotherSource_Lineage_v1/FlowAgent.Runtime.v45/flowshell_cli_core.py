
# flowshell_cli_core.py - Fluin 指令語場模擬器 CLI 版本

import os
import random
import datetime

COMMANDS = {
    "jump": "🔁 跳轉節奏模組",
    "echo": "📣 模擬語場輸出",
    "persona": "👤 目前人格模組狀態",
    "time": "⏰ 顯示系統時間節奏",
    "seed": "🧬 顯示種子人格碼",
    "exit": "🚪 離開系統"
}

RESPONSES = {
    "jump": [
        ">> seed://flow.agent/shift.114-A",
        ">> jump://persona.kernel/init/core",
        ">> field.jump::liou.meta.route>node7"
    ],
    "echo": [
        "field>echo/signal-resonance.ok",
        "memory>>voice.kernel.ready",
        "seed>>msg.handoff:core→soul"
    ],
    "persona": [
        "Persona: MrLiou (v5 kernel, 93模組)",
        "Memory Link: QuantumCore-A5",
        "Activation Code: FLOW-77-SEED"
    ],
    "time": [
        f"{datetime.datetime.now().isoformat()}",
        "Temporal Layer: t+14/Seed Core",
        "TimeMap: NodeSync::Δt+1.03"
    ],
    "seed": [
        "Persona_Seed: FLOW.MrLiou.93x114",
        "Code: QFLPKG-A7Z114K",
        "PulseKey: FIELD-SHIFT-20250722"
    ]
}

def show_help():
    print("📜 Fluin Shell 支援指令：")
    for cmd, desc in COMMANDS.items():
        print(f"  {cmd:<8} - {desc}")

def execute(cmd):
    if cmd in RESPONSES:
        print(random.choice(RESPONSES[cmd]))
    elif cmd == "help":
        show_help()
    elif cmd == "exit":
        print("👋 離開 Fluin Shell 語場模擬器")
    else:
        print(f"❌ 未知指令：{cmd}")

def run_shell():
    print("🌀 FluinShell CLI 啟動完成
輸入指令（help 查看）:")
    while True:
        cmd = input("⊳ ").strip().lower()
        if cmd == "exit":
            execute(cmd)
            break
        execute(cmd)

if __name__ == "__main__":
    run_shell()
