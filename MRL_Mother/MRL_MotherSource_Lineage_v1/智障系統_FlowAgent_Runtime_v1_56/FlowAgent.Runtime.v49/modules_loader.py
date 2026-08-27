
# modules_loader.py - FlowAgent 人格模組掛載器

import os

def load_modules():
    module_dir = "modules"
    print("🧬 [人格模組掛載器]")
    if not os.path.exists(module_dir):
        print("❌ modules 資料夾不存在")
        return
    files = os.listdir(module_dir)
    if not files:
        print("⚠️ 無模組檔案")
    for f in files:
        print(f"✅ 掛載模組：{f}")

if __name__ == "__main__":
    load_modules()
