
# persona_manager.py - FlowAgent 人格模組 CLI 管理器

import os

PERSONAS = {
    "001": "FluinPersona.Core.v1",
    "002": "PersonaSeed.Template.v3.1",
    "003": "FutureMind.Experimental.v1",
    "004": "TimeShiftPersona.v1",
}

def list_personas():
    print("🧬 可用人格模組：")
    for code, name in PERSONAS.items():
        print(f"- [{code}] {name}")

def activate_persona(code):
    name = PERSONAS.get(code)
    if name:
        print(f"✅ 人格 [{code}] 已啟動：{name}")
        print("🌀 開始人格共振節奏模擬...")
    else:
        print(f"❌ 未知人格代碼：{code}")

def cli():
    print("🔘 FlowAgent 人格 CLI 控制面板")
    list_personas()
    while True:
        cmd = input("輸入人格代碼（或輸入 exit 離開）：")
        if cmd == "exit":
            print("🌓 離開人格控制台")
            break
        activate_persona(cmd)

if __name__ == "__main__":
    cli()
