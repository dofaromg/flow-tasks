import json
import zipfile
import os

def load_fluinhub_registry(registry_path):
    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    print(f"🧠 FluinHub Registry: {registry['hub_id']}")
    print(f"📦 Core Image: {registry['core_image']}")
    print(f"🗂️  Registered Personas:")

    for p in registry["personas_registered"]:
        print(f"  - {p['id']} (v{p['version']})")
        if os.path.exists(p["bundle"]):
            print(f"    ✅ Bundle found: {p['bundle']}")
            try:
                with zipfile.ZipFile(p["bundle"], 'r') as zipf:
                    print(f"    🔍 Contents:")
                    for name in zipf.namelist():
                        print(f"      • {name}")
            except Exception as e:
                print(f"    ⚠️ Failed to read: {e}")
        else:
            print(f"    ❌ Bundle not found: {p['bundle']}")

if __name__ == "__main__":
    load_fluinhub_registry("FluinHub.CenterRegistry.v1.json")
