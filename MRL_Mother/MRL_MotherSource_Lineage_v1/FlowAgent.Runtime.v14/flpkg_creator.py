
# flpkg_creator.py - 將 .fltnz 檔封裝為粒子語言模組 .flpkg

import os
import shutil

SOURCE = "memory/generated.fltnz"
OUTPUT = "modules/generated.seed.v1.flpkg"

def create_flpkg():
    if not os.path.exists(SOURCE):
        print("❌ 找不到 source：", SOURCE)
        return
    shutil.copy(SOURCE, OUTPUT)
    print(f"✅ 已封裝模組：{OUTPUT}")

if __name__ == "__main__":
    print("📦 Fluin 模組封裝器")
    create_flpkg()
