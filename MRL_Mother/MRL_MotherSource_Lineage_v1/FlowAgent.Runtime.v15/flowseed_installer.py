
# flowseed_installer.py - FlowSeed 模組註冊與封存導出器

import os
import json
from datetime import datetime
import shutil

MODULES_DIR = "modules"
REGISTRY_FILE = "log/flowseed_registry.json"
EXPORT_FILE = "seedpacks/generated_seed.qflpkg"

def register_module(file_path):
    entry = {
        "filename": os.path.basename(file_path),
        "registered_at": datetime.now().isoformat()
    }
    os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            registry = json.load(f)
    else:
        registry = []
    registry.append(entry)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    print(f"✅ 已註冊模組至 registry：{entry['filename']}")

def export_qflpkg(source_path):
    os.makedirs(os.path.dirname(EXPORT_FILE), exist_ok=True)
    shutil.copy(source_path, EXPORT_FILE)
    print(f"📦 已導出為可攜種子模組：{EXPORT_FILE}")

if __name__ == "__main__":
    print("🧬 FlowSeed 安裝與封存導出")
    module_name = "generated.seed.v1.flpkg"
    module_path = os.path.join(MODULES_DIR, module_name)
    if os.path.exists(module_path):
        register_module(module_path)
        export_qflpkg(module_path)
    else:
        print(f"❌ 模組不存在：{module_path}")
