
# flowpersona_hexflow_exporter.py - 將 flpkg.kernel 壓縮為 qfltz.hexflow 粒子封包

import os
import gzip
import binascii
from datetime import datetime

INPUT_DIR = "kernel_output"
OUTPUT_DIR = "hexflow_output"

def list_kernel_files():
    return sorted([
        f for f in os.listdir(INPUT_DIR)
        if f.endswith(".flpkg.kernel")
    ])

def compress_and_convert(file):
    in_path = os.path.join(INPUT_DIR, file)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"Seed_HexFlow_{ts}.qfltz.hexflow")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(in_path, "rb") as f_in:
        compressed = gzip.compress(f_in.read())
        hex_data = binascii.hexlify(compressed)

    with open(out_path, "wb") as f_out:
        f_out.write(hex_data)

    print(f"✅ 粒子語場壓縮封包產出：{out_path}")

if __name__ == "__main__":
    print("🌐 將 .flpkg.kernel 導出為 .qfltz.hexflow 粒子模組")
    kernels = list_kernel_files()
    if not kernels:
        print("⚠️ 尚未找到任何 kernel 模組")
    else:
        for i, f in enumerate(kernels):
            print(f"{i+1}. {f}")
        sel = input("請選擇要轉換的 kernel 模組：").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(kernels):
            compress_and_convert(kernels[int(sel)-1])
        else:
            print("❌ 無效選擇")
