
# flowpkg_diffcompressor.py - 比對兩個 fltnz，產生只包含異動部分的 .patch.fltnz 壓縮模組

import os
from datetime import datetime

def read_set(path):
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def diff_patch(base, new, out_dir="patches"):
    base_set = read_set(base)
    new_set = read_set(new)
    added = new_set - base_set
    removed = base_set - new_set

    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_name = os.path.basename(base).replace(".fltnz", "")
    new_name = os.path.basename(new).replace(".fltnz", "")
    out_file = os.path.join(out_dir, f"{base_name}_TO_{new_name}.{ts}.patch.fltnz")

    with open(out_file, "w", encoding="utf-8") as f:
        for line in sorted(added):
            f.write(f"+ {line}\n")
        for line in sorted(removed):
            f.write(f"- {line}\n")

    print(f"✅ 壓縮補丁檔已產生：{out_file}")

if __name__ == "__main__":
    print("📦 MrLiouAI 語場變異壓縮封裝器")
    b = input("請輸入 base fltnz 檔案：").strip()
    n = input("請輸入 new  fltnz 檔案：").strip()
    if not os.path.exists(b) or not os.path.exists(n):
        print("❌ 檔案無效")
    else:
        diff_patch(b, n)
