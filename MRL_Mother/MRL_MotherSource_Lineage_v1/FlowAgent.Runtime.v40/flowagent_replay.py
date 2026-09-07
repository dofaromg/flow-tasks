
# flowagent_replay.py - FlowReplay 模組：從指定 snapshot 快照還原 CLI 執行環境

import os
import shutil

SNAPSHOT_ROOT = "snapshot_log"
RUNTIME_ROOT = "/mnt/data/FlowAgent.Runtime"

def list_snapshots():
    return sorted([
        d for d in os.listdir(SNAPSHOT_ROOT)
        if d.startswith("snapshot_")
    ])

def restore_snapshot(snap_name):
    snap_path = os.path.join(SNAPSHOT_ROOT, snap_name)
    if not os.path.exists(snap_path):
        print(f"❌ 找不到快照資料夾：{snap_path}")
        return

    print(f"🧬 從 {snap_name} 還原模組到執行環境...")
    for sub in os.listdir(snap_path):
        src = os.path.join(snap_path, sub)
        dst = os.path.join(RUNTIME_ROOT, sub)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        elif os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    print(f"✅ 已還原 snapshot → FlowAgent.Runtime")

def main():
    snaps = list_snapshots()
    if not snaps:
        print("❌ 沒有可用的 snapshot")
        return

    print("🌀 FlowReplay - 快照重建執行器")
    for i, snap in enumerate(snaps):
        print(f"{i+1}. {snap}")
    sel = input("請選擇要還原的 snapshot 編號：").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(snaps):
        restore_snapshot(snaps[int(sel)-1])
    else:
        print("❌ 無效輸入")

if __name__ == "__main__":
    main()
