
# persona_autoloader.py - FlowAgent 自動人格模組裝載器（含記憶封存）

import os
import json

PERSONA_FILES = {
    "001": {
        "module": "FluinPersona.Core.v1.flpkg",
        "memory": "FluinPersona.Memory.v1.json"
    },
    "002": {
        "module": "PersonaSeed.Template.v3.1.flpkg",
        "memory": "PersonaSeed.Memory.txt"
    },
    "003": {
        "module": "FutureMind.Experimental.v1.flpkg",
        "memory": "FutureMind.RecallMap.json"
    },
    "004": {
        "module": "TimeShiftPersona.v1.flpkg",
        "memory": "TimeShift.Trace.txt"
    }
}

def load_persona(code):
    if code not in PERSONA_FILES:
        print(f"❌ 無法辨識人格代碼：{code}")
        return

    entry = PERSONA_FILES[code]
    mod_path = os.path.join("modules", entry["module"])
    mem_path = os.path.join("memory", entry["memory"])

    print(f"🧬 掛載人格模組檔：{mod_path}")
    print(f"🧠 載入記憶封存：{mem_path}")

    if os.path.exists(mod_path):
        print("✅ 模組檔案存在")
    else:
        print("⚠️ 模組檔案不存在")

    if os.path.exists(mem_path):
        print("✅ 記憶封存存在")
        if mem_path.endswith(".json"):
            with open(mem_path, "r", encoding="utf-8") as f:
                mem_data = json.load(f)
                print(f"📘 記憶片段數：{len(mem_data)}")
        else:
            with open(mem_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                print(f"📘 記憶行數：{len(lines)}")
    else:
        print("⚠️ 記憶封存不存在")

if __name__ == "__main__":
    print("🔍 FlowAgent 自動人格模組與記憶掛載器")
    code = input("輸入人格代碼：")
    load_persona(code)
