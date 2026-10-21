
# qflpkg_manager.py - qflpkg 模組升級與批次註冊系統

import os
import json
from datetime import datetime
import shutil

QFLPKG_DIR = "seedpacks"
REGISTRY_FILE = "log/flowseed_registry.json"
BACKUP_DIR = "log/registry_backups"

def backup_registry():
    if not os.path.exists(REGISTRY_FILE):
        print("⚠️ 無註冊紀錄可備份")
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"registry_backup_{timestamp}.json")
    shutil.copy(REGISTRY_FILE, backup_path)
    print(f"📦 已備份 registry：{backup_path}")

def batch_register():
    files = [f for f in os.listdir(QFLPKG_DIR) if f.endswith(".qflpkg")]
    if not files:
        print("⚠️ 無 qflpkg 檔案可註冊")
        return

    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            registry = json.load(f)
    else:
        registry = []

    filenames = [r["filename"] for r in registry]
    new_entries = []

    for f in files:
        if f not in filenames:
            entry = {
                "filename": f,
                "registered_at": datetime.now().isoformat()
            }
            registry.append(entry)
            new_entries.append(entry)

    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    if new_entries:
        print(f"✅ 註冊完成：{len(new_entries)} 筆")
        for e in new_entries:
            print(f"  ➕ {e['filename']}")
    else:
        print("✅ 所有模組皆已註冊，無新增項目")

if __name__ == "__main__":
    print("📊 FlowSeed 模組總管系統")
    print("1. 備份目前 registry")
    print("2. 批次掃描並註冊 seedpacks 中的 .qflpkg")
    choice = input("請輸入選項（1 或 2）：")
    if choice == "1":
        backup_registry()
    elif choice == "2":
        batch_register()
    else:
        print("❌ 無效選項")
