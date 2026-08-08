
# flpkg_autopack.py - 自動將 merged fltnz 封裝為 .flpkg 與 .qflpkg，並註冊

import os
import shutil
import json
from datetime import datetime

MERGE_DIR = "diffpacks"
MODULES_DIR = "modules"
SEEDPACKS_DIR = "seedpacks"
LOG_FILE = "log/flowseed_registry.json"

def find_latest_merged():
    files = sorted([
        f for f in os.listdir(MERGE_DIR) 
        if f.startswith("merged_") and f.endswith(".fltnz")
    ], reverse=True)
    return files[0] if files else None

def seal_and_register(base_name, source_path):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    flpkg_name = f"{base_name}.{timestamp}.flpkg"
    qflpkg_name = f"{base_name}.{timestamp}.qflpkg"

    flpkg_path = os.path.join(MODULES_DIR, flpkg_name)
    qflpkg_path = os.path.join(SEEDPACKS_DIR, qflpkg_name)

    shutil.copy(source_path, flpkg_path)
    shutil.copy(source_path, qflpkg_path)

    print(f"✅ 封裝完成：{flpkg_path}")
    print(f"✅ 可攜種子：{qflpkg_path}")

    # 註冊到 registry
    entry = {
        "filename": flpkg_name,
        "registered_at": datetime.now().isoformat()
    }

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            registry = json.load(f)
    else:
        registry = []

    registry.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"🧾 記錄已更新：flowseed_registry.json")

if __name__ == "__main__":
    print("🌀 FlowSeed 自動封裝器")
    filename = find_latest_merged()
    if not filename:
        print("❌ 找不到合併語場檔案")
    else:
        base = os.path.splitext(filename)[0]
        path = os.path.join(MERGE_DIR, filename)
        seal_and_register(base, path)
