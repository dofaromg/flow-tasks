
# flowpersona_bundle_exporter.py - 導出完整系統為 flpkg.universe.bundle 模組包

import os
import shutil
from datetime import datetime

SOURCE_DIRS = ["memory", "modules", "personas", "qflpkg_output", "kernel_output", "log"]
BUNDLE_OUTPUT_DIR = "universe_bundle"

def export_bundle():
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bundle_name = f"FlowAgent_ResonantBundle_{ts}.flpkg.universe.bundle"
    bundle_path = os.path.join(BUNDLE_OUTPUT_DIR, bundle_name)
    os.makedirs(BUNDLE_OUTPUT_DIR, exist_ok=True)

    temp_dir = os.path.join(BUNDLE_OUTPUT_DIR, "temp_universe")
    os.makedirs(temp_dir, exist_ok=True)

    for folder in SOURCE_DIRS:
        if os.path.exists(folder):
            shutil.copytree(folder, os.path.join(temp_dir, folder), dirs_exist_ok=True)

    shutil.make_archive(bundle_path.replace(".flpkg.universe.bundle", ""), "zip", temp_dir)
    shutil.rmtree(temp_dir)

    print(f"✅ 全模組語場封包已完成：{bundle_path}")

if __name__ == "__main__":
    print("📦 建構 FlowAgent 語場模組總包 (.flpkg.universe.bundle)")
    export_bundle()
