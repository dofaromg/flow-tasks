# modules_loader.py
import os, json

def load_modules():
    module_dir = "modules"
    print("[modules_loader]")
    mods = []
    if not os.path.isdir(module_dir):
        print("modules directory missing")
        return mods
    for fn in sorted(os.listdir(module_dir)):
        if fn.endswith(".manifest.json"):
            try:
                with open(os.path.join(module_dir, fn), "r", encoding="utf-8") as f:
                    m = json.load(f)
                mods.append(m)
                print(f"✅ {m.get('module_name')} ({m.get('fusion_state')})")
            except Exception as e:
                print(f"⚠️ manifest parse failed: {fn} ({e})")
    return mods

if __name__ == "__main__":
    load_modules()
