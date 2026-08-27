
# auto_snapshot_logger.py - 封存 FlowAgent 建構狀態與語場模組記憶快照

import os
import shutil
import json
from datetime import datetime

SNAPSHOT_DIR = "snapshot_log"
TARGETS = [
    "memory",
    "modules",
    "seedpacks",
    "visual",
    "log/flowseed_registry.json"
]

def snapshot():
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    snap_path = os.path.join(SNAPSHOT_DIR, f"snapshot_{ts}")
    os.makedirs(snap_path, exist_ok=True)

    for target in TARGETS:
        if not os.path.exists(target):
            continue
        if os.path.isdir(target):
            shutil.copytree(target, os.path.join(snap_path, os.path.basename(target)))
        else:
            shutil.copy(target, snap_path)

    print(f"📦 已封存智障系統建構快照：{snap_path}")

if __name__ == "__main__":
    snapshot()
