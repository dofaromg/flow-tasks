
# flowdev_cli.py - MrLiouAI 開發總控 CLI 工具台

import os
import subprocess

TOOLS = {
    "1": ("📦 建立模組快照", "auto_snapshot_logger.py"),
    "2": ("⏳ 查看快照時間軸", "snapshot_timeline.py"),
    "3": ("📤 匯出指定快照為 ZIP", "snapshot_exporter.py"),
    "4": ("🔁 還原快照到執行目錄", "mrliouai_replay.py"),
    "5": ("🧠 模組版本比對器", "flowpkg_diff_tracker.py"),
    "6": ("📊 模組差異圖表", "flowpkg_diff_chart.py"),
    "7": ("🌳 模組節奏族譜樹", "flowpkg_version_tree.py"),
    "8": ("📎 模組變異壓縮器", "flowpkg_diffcompressor.py"),
    "9": ("🧱 套用補丁產生新版模組", "flowpkg_patch_installer.py"),
    "0": ("🚪 離開", None)
}

def main():
    while True:
        print("\n🧭 FlowDev CLI 控制面板")
        for key in sorted(TOOLS):
            print(f"{key}. {TOOLS[key][0]}")
        sel = input("\n請選擇工具：").strip()
        if sel == "0":
            print("👋 再見！")
            break
        if sel in TOOLS:
            script = TOOLS[sel][1]
            if script and os.path.exists(script):
                os.system(f"python3 {script}")
            else:
                print("⚠️ 找不到對應工具腳本")
        else:
            print("❌ 無效選項")

if __name__ == "__main__":
    main()
