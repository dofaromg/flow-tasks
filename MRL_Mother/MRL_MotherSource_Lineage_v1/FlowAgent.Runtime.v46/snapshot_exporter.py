
# snapshot_exporter.py - 將指定 snapshot_XXXX 打包成可攜 .zip 檔

import os
import shutil

SNAPSHOT_ROOT = "snapshot_log"
EXPORT_DIR = "snapshot_exports"

def export_snapshot():
    snaps = sorted([d for d in os.listdir(SNAPSHOT_ROOT) if d.startswith("snapshot_")])
    if not snaps:
        print("❌ 沒有找到任何快照")
        return

    print("📦 可輸出快照列表：")
    for i, snap in enumerate(snaps):
        print(f"{i+1}. {snap}")

    choice = input("請輸入要匯出的快照編號：").strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(snaps):
        print("❌ 選擇無效")
        return

    selected = snaps[int(choice)-1]
    src = os.path.join(SNAPSHOT_ROOT, selected)
    os.makedirs(EXPORT_DIR, exist_ok=True)
    out_path = os.path.join(EXPORT_DIR, f"{selected}.zip")

    shutil.make_archive(out_path.replace(".zip", ""), 'zip', src)
    print(f"✅ 已成功匯出快照：{out_path}")

if __name__ == "__main__":
    print("🌀 FlowSnapshot 快照匯出工具")
    export_snapshot()
