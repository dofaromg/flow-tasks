
# flowpkg_registry_builder.py - 建立 memory/ 與 personas/ 中模組的註冊表 JSON

import os
import json
from datetime import datetime

MEMORY_DIR = "memory"
PERSONAS_DIR = "personas"
REGISTRY_FILE = "log/flpkg.registry.json"

def list_files(directory, suffix):
    return sorted([
        f for f in os.listdir(directory)
        if f.endswith(suffix)
    ])

def build_registry():
    memory_files = list_files(MEMORY_DIR, ".fltnz")
    persona_files = list_files(PERSONAS_DIR, ".flpkg")

    registry = {
        "generated_at": datetime.now().isoformat(),
        "memory_modules": [],
        "persona_modules": []
    }

    for fname in memory_files:
        registry["memory_modules"].append({
            "file": fname,
            "path": os.path.join(MEMORY_DIR, fname)
        })

    for fname in persona_files:
        registry["persona_modules"].append({
            "file": fname,
            "path": os.path.join(PERSONAS_DIR, fname)
        })

    os.makedirs("log", exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"✅ 模組註冊表已建立：{REGISTRY_FILE}")

if __name__ == "__main__":
    print("🧾 MrLiouAI 模組註冊紀錄器")
    build_registry()
