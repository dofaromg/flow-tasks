
# flowpkg_patch_installer.py - 將 .patch.fltnz 補丁安裝到原始 .fltnz 上，產生新版語場模組

import os
from datetime import datetime

def apply_patch(base_path, patch_path, out_dir="memory"):
    with open(base_path, "r", encoding="utf-8") as f:
        base_lines = set(l.strip() for l in f if l.strip())

    with open(patch_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            if line.startswith("+ "):
                base_lines.add(line[2:].strip())
            elif line.startswith("- "):
                base_lines.discard(line[2:].strip())

    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    new_file = os.path.join(out_dir, f"patched_{ts}.fltnz")
    with open(new_file, "w", encoding="utf-8") as f:
        for l in sorted(base_lines):
            f.write(l + "\n")

    print(f"✅ 已套用補丁，產生新模組：{new_file}")

if __name__ == "__main__":
    print("🧱 MrLiouAI 語場補丁套用器")
    base = input("請輸入 base .fltnz 路徑：").strip()
    patch = input("請輸入 patch .patch.fltnz 檔案：").strip()
    if not os.path.exists(base) or not os.path.exists(patch):
        print("❌ 檔案無效")
    else:
        apply_patch(base, patch)
