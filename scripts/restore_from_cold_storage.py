#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冷儲存還原工具 (Cold Storage Restoration Tool)
從冷儲存還原檔案
"""

import sys
from pathlib import Path

# 添加 particle_core/src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "particle_core" / "src"))

from cold_storage_manager import ColdStorageManager


def main():
    """主程式"""
    print("=" * 70)
    print("冷儲存還原工具 (Cold Storage Restoration Tool)")
    print("=" * 70)
    print()
    
    # 初始化管理器
    manager = ColdStorageManager(
        source_root=".",
        cold_storage_root="cold_storage",
        manifest_file="cold_storage_manifest.json"
    )
    
    # 列出可還原的檔案
    files = manager.list_archived_files()
    
    if not files:
        print("冷儲存中沒有檔案。")
        return
    
    print(f"冷儲存中有 {len(files)} 個檔案:\n")
    
    for i, file in enumerate(files, 1):
        print(f"{i:3d}. {file['path']}")
        print(f"     大小: {file['size']} bytes")
        print(f"     校驗碼: {file['checksum'][:16]}...")
        print(f"     歸檔時間: {file['archived_at']}")
        print()
    
    # 詢問要還原的檔案
    print("輸入要還原的檔案編號（或 'all' 還原全部，'q' 退出）:")
    choice = input("> ").strip()
    
    if choice.lower() == 'q':
        print("已取消。")
        return
    
    if choice.lower() == 'all':
        # 還原全部
        confirm = input(f"\n確定要還原全部 {len(files)} 個檔案嗎？(y/n): ")
        if confirm.lower() != 'y':
            print("已取消。")
            return
        
        print("\n開始還原...")
        for file in files:
            try:
                restored_path = manager.restore_file(file['path'])
                print(f"✓ 已還原: {restored_path}")
            except Exception as e:
                print(f"✗ 還原失敗 {file['path']}: {e}")
    else:
        # 還原單一檔案
        try:
            index = int(choice) - 1
            if 0 <= index < len(files):
                file = files[index]
                restored_path = manager.restore_file(file['path'])
                print(f"\n✓ 檔案已還原到: {restored_path}")
            else:
                print("無效的編號。")
        except ValueError:
            print("無效的輸入。")
    
    print()


if __name__ == "__main__":
    main()
