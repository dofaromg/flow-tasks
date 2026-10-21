
# snapshot_timeline.py - 顯示 snapshot_log 中的所有封存快照時間軸與內容摘要

import os
import datetime

SNAPSHOT_ROOT = "snapshot_log"

def list_snapshots():
    if not os.path.exists(SNAPSHOT_ROOT):
        print("❌ 尚未建立任何快照")
        return

    snapshots = sorted(os.listdir(SNAPSHOT_ROOT))
    if not snapshots:
        print("⚠️ 尚未建立快照")
        return

    print("📅 系統封存快照時間軸：\n")
    for snap in snapshots:
        path = os.path.join(SNAPSHOT_ROOT, snap)
        if not os.path.isdir(path):
            continue
        ts = snap.replace("snapshot_", "")
        try:
            dt = datetime.datetime.strptime(ts, "%Y%m%d-%H%M%S")
            readable_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            readable_time = ts
        print(f"🕓 {readable_time}  →  📂 {snap}")
        # 顯示內含模組數量簡略
        contents = os.listdir(path)
        for item in contents:
            sub = os.path.join(path, item)
            if os.path.isdir(sub):
                count = len(os.listdir(sub))
                print(f"   └─ 📁 {item:<10}  [{count:>2} 檔案]")
            elif os.path.isfile(sub):
                print(f"   └─ 📄 {item}")
        print()

if __name__ == "__main__":
    print("🌀 FlowSnapshot 快照時間場域導覽器")
    list_snapshots()
