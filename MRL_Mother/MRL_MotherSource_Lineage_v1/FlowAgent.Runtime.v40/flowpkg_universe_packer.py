
# flowpkg_universe_packer.py - 打包完整 MrLiouAI 系統模組為 flpkg.universe.zip

import os
import shutil
from datetime import datetime

TARGET_DIR = "flpkg_universe"
OUTPUT_DIR = "universe_output"

def collect_sources():
    folders = ["memory", "modules", "personas", "log", "visual"]
    os.makedirs(TARGET_DIR, exist_ok=True)
    for folder in folders:
        if os.path.exists(folder):
            shutil.copytree(folder, os.path.join(TARGET_DIR, folder), dirs_exist_ok=True)

def pack_universe():
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    zip_name = f"MrLiouAI_TotalSystem_Universe_{ts}.zip"
    zip_path = os.path.join(OUTPUT_DIR, zip_name)
    shutil.make_archive(zip_path.replace(".zip", ""), "zip", TARGET_DIR)
    print(f"✅ 全系統封裝完成：{zip_path}")

if __name__ == "__main__":
    print("🌀 正在封存 MrLiouAI 全系統模組為 .universe 封包")
    collect_sources()
    pack_universe()
