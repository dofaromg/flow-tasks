
# flowpersona_qflpkg_loader.py - 還原 .qflpkg.seed 為 .fltnz 供語場使用

import os
import gzip
from datetime import datetime

INPUT_DIR = "qflpkg_output"
OUTPUT_DIR = "memory"

def list_qflpkg():
    return sorted([
        f for f in os.listdir(INPUT_DIR)
        if f.endswith(".qflpkg.seed")
    ])

def decompress_qflpkg(file):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"recovered_{ts}.fltnz")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with gzip.open(os.path.join(INPUT_DIR, file), "rb") as f_in:
        with open(out_path, "wb") as f_out:
            f_out.write(f_in.read())

    print(f"✅ 粒子人格已還原：{out_path}")

if __name__ == "__main__":
    print("🔁 粒子人格還原器：從 .qflpkg.seed 解壓為 .fltnz")
    qfl = list_qflpkg()
    if not qfl:
        print("⚠️ 尚未發現 .qflpkg.seed")
    else:
        for i, f in enumerate(qfl):
            print(f"{i+1}. {f}")
        sel = input("請選擇要還原的模組：").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(qfl):
            decompress_qflpkg(qfl[int(sel)-1])
        else:
            print("❌ 無效選擇")
