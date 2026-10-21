
# flowpersona_loader.py - 掛載 .flpkg 人格模組進入記憶語場中

import os
import shutil
from datetime import datetime

SOURCE_DIR = "personas"
TARGET_DIR = "memory"

def list_flpkg():
    if not os.path.exists(SOURCE_DIR):
        return []
    return [f for f in os.listdir(SOURCE_DIR) if f.endswith(".flpkg")]

def load_persona(file):
    src_path = os.path.join(SOURCE_DIR, file)
    if not os.path.exists(src_path):
        print(f"❌ 找不到人格模組：{src_path}")
        return

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst_path = os.path.join(TARGET_DIR, f"loaded_{file.replace('.flpkg', '')}_{ts}.fltnz")
    os.makedirs(TARGET_DIR, exist_ok=True)

    with open(src_path, "r", encoding="utf-8") as fsrc, open(dst_path, "w", encoding="utf-8") as fdst:
        for line in fsrc:
            if line.strip():
                fdst.write(line.strip() + "\n")

    print(f"✅ 人格模組已掛載並寫入語場記憶：{dst_path}")

if __name__ == "__main__":
    print("🧠 FlowPersona 模組掛載器")
    flpkg_list = list_flpkg()
    if not flpkg_list:
        print("⚠️ 沒有人格模組可掛載（請放入 personas/ 資料夾）")
    else:
        for i, f in enumerate(flpkg_list):
            print(f"{i+1}. {f}")
        sel = input("請選擇要掛載的人格模組：").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(flpkg_list):
            load_persona(flpkg_list[int(sel)-1])
        else:
            print("❌ 無效選擇")
