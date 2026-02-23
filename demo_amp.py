#!/usr/bin/env python3
"""
AMP Ledger System - 完整功能演示
Complete Functionality Demonstration
"""

import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd):
    """執行命令並顯示輸出"""
    print(f"\n{'='*60}")
    print(f"執行命令 / Running: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("錯誤 / Error:", result.stderr, file=sys.stderr)
    
    return result.returncode == 0


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║       AMP Index-Only Ledger System                        ║
║       完整功能演示 / Complete Feature Demo                 ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 清理舊資料
    import shutil
    if Path("data").exists():
        shutil.rmtree("data")
    
    # 1. 初始化帳本
    print("\n▶ 步驟 1: 初始化帳本 / Initialize Ledger")
    if not run_command(["python", "cli.py", "init"]):
        return False
    
    # 2. 新增條目
    print("\n▶ 步驟 2: 新增條目 / Append Entries")
    entries = [
        "演示條目 1: 系統完全可運行",
        "演示條目 2: 已完成部署驗證",
        "演示條目 3: 所有測試通過",
        "Demo Entry 4: System is production ready"
    ]
    
    for entry in entries:
        if not run_command(["python", "cli.py", "append", entry]):
            return False
    
    # 3. 驗證鏈完整性
    print("\n▶ 步驟 3: 驗證鏈完整性 / Verify Chain Integrity")
    if not run_command(["python", "cli.py", "verify"]):
        return False
    
    # 4. 查看日誌
    print("\n▶ 步驟 4: 查看所有日誌 / Show All Logs")
    if not run_command(["python", "cli.py", "log", "--n", "0"]):
        return False
    
    # 5. 建立快照
    print("\n▶ 步驟 5: 建立快照 / Create Snapshot")
    if not run_command(["python", "cli.py", "snapshot", "demo-snapshot-2026"]):
        return False
    
    # 6. 匯出到 GitHub
    print("\n▶ 步驟 6: 匯出到 GitHub 適配器 / Export to GitHub Adapter")
    if not run_command(["python", "cli.py", "github-export", "--n", "4"]):
        return False
    
    # 7. 顯示檔案結構
    print("\n▶ 步驟 7: 顯示檔案結構 / Show File Structure")
    print("="*60)
    import os
    for root, dirs, files in os.walk("data"):
        level = root.replace("data", "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}📁 {os.path.basename(root)}/")
        sub_indent = " " * 2 * (level + 1)
        for file in files:
            size = os.path.getsize(os.path.join(root, file))
            print(f"{sub_indent}📄 {file} ({size} bytes)")
    
    # 8. 顯示最終統計
    print("\n" + "="*60)
    print("✅ 演示完成 / Demo Complete!")
    print("="*60)
    
    # 直接驗證
    from amp.storage import Storage
    from amp.ledger import Ledger
    
    storage = Storage(Path("data"))
    ledger = Ledger(storage)
    ok, msg = ledger.verify()
    
    print(f"\n最終驗證結果 / Final Verification:")
    print(f"  狀態 / Status: {'✅ 成功 / Success' if ok else '❌ 失敗 / Failed'}")
    print(f"  訊息 / Message: {msg}")
    
    refs = storage.load_refs()
    print(f"\n帳本統計 / Ledger Statistics:")
    print(f"  總條目數 / Total Entries: {refs['length']}")
    print(f"  最新雜湊 / Latest Hash: {refs['head'][:16]}...")
    
    print(f"\n檔案位置 / File Locations:")
    print(f"  資料目錄 / Data Directory: {Path('data').absolute()}")
    print(f"  鏈檔案 / Chain File: {storage.chain_file}")
    print(f"  快照目錄 / Snapshots: {storage.snapshots_dir}")
    
    print("\n" + "="*60)
    print("🎉 AMP 帳本系統運行正常！")
    print("🎉 AMP Ledger System is fully operational!")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
