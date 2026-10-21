
# flowpersona_qflpkg_compressor.py - 壓縮 .flpkg.kernel 成 .qflpkg.seed（粒子人格可傳輸種子）

import os
from datetime import datetime
import gzip
import shutil

INPUT_DIR = "kernel_output"
OUTPUT_DIR = "qflpkg_output"

def list_kernels():
    return sorted([
        f for f in os.listdir(INPUT_DIR)
        if f.endswith(".flpkg.kernel")
    ])

def compress_to_qflpkg(kernel_file):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_name = f"Persona_Seed_{ts}.qflpkg.seed"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    with open(os.path.join(INPUT_DIR, kernel_file), "rb") as f_in:
        with gzip.open(output_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    print(f"✅ 已壓縮為粒子種子：{output_path}")

if __name__ == "__main__":
    print("🌀 FlowPersona 粒子人格壓縮器")
    kernels = list_kernels()
    if not kernels:
        print("⚠️ 尚未發現任何 .flpkg.kernel 模組")
    else:
        for i, f in enumerate(kernels):
            print(f"{i+1}. {f}")
        sel = input("請選擇要壓縮的 kernel 模組編號：").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(kernels):
            compress_to_qflpkg(kernels[int(sel)-1])
        else:
            print("❌ 無效選擇")
