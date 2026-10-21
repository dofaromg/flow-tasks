
# flpkg_unpacker.py - 將 .flpkg 或 .qflpkg 還原為 .fltnz 原始粒子語場

import os
import shutil

def unpack_flpkg(file_path, output_dir="unpacked"):
    if not os.path.exists(file_path):
        print(f"❌ 找不到檔案：{file_path}")
        return
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.basename(file_path).replace(".flpkg", "").replace(".qflpkg", "")
    dest = os.path.join(output_dir, f"{base}.fltnz")
    shutil.copy(file_path, dest)
    print(f"✅ 已還原為：{dest}")

if __name__ == "__main__":
    print("📦 Fluin 模組解封器")
    path = input("請輸入要解封的 .flpkg / .qflpkg 檔案路徑：")
    unpack_flpkg(path)
