#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冷儲存歸檔工具 (Cold Storage Archival Tool)
將檔案歸檔到冷儲存，同時保留原始檔案
"""

import sys
import os
from pathlib import Path

# 添加 particle_core/src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "particle_core" / "src"))

from cold_storage_manager import ColdStorageManager


def main():
    """主程式"""
    print("=" * 70)
    print("冷儲存歸檔工具 (Cold Storage Archival Tool)")
    print("=" * 70)
    print()
    print("此工具會將臨時和下載檔案轉換為粒子格式並歸檔到冷儲存。")
    print("原始檔案將被保留，不會被刪除。")
    print()
    
    # 初始化管理器
    manager = ColdStorageManager(
        source_root=".",
        cold_storage_root="cold_storage",
        manifest_file="cold_storage_manifest.json"
    )
    
    print("步驟 1: 掃描需要歸檔的檔案...")
    print("-" * 70)
    
    # 掃描檔案
    files = manager.scan_files()
    
    if not files:
        print("✓ 沒有需要歸檔的檔案。")
        return
    
    print(f"✓ 找到 {len(files)} 個檔案需要歸檔:\n")
    
    # 按目錄分組顯示
    from collections import defaultdict
    files_by_dir = defaultdict(list)
    for file in files:
        rel_path = file.relative_to(manager.source_root)
        parent = str(rel_path.parent) if rel_path.parent != Path('.') else '.'
        files_by_dir[parent].append(rel_path.name)
    
    for directory, filenames in sorted(files_by_dir.items()):
        print(f"  {directory}/")
        for filename in sorted(filenames):
            print(f"    - {filename}")
        print()
    
    # 計算總大小
    total_size = sum(f.stat().st_size for f in files)
    print(f"總大小: {total_size / 1024 / 1024:.2f} MB")
    print()
    
    # 確認
    print("步驟 2: 確認歸檔操作")
    print("-" * 70)
    confirm = input("確定要將這些檔案歸檔到冷儲存嗎？(y/n): ")
    
    if confirm.lower() != 'y':
        print("✗ 已取消歸檔操作。")
        return
    
    print()
    print("步驟 3: 執行歸檔...")
    print("-" * 70)
    
    # 執行歸檔
    results = manager.archive_batch(
        files,
        keep_original=True,  # 保留原始檔案
        create_redirect=True  # 創建重定向檔案
    )
    
    print()
    print("=" * 70)
    print("歸檔完成！")
    print("=" * 70)
    print()
    print(f"✓ 新歸檔檔案: {len(results['archived'])}")
    print(f"✓ 去重檔案: {len(results['deduplicated'])}")
    
    if results['errors']:
        print(f"✗ 錯誤: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error['file']}: {error['error']}")
    
    # 顯示統計
    print()
    stats = manager.get_statistics()
    print("冷儲存統計:")
    print(f"  總歸檔檔案: {stats['total_archived']}")
    print(f"  唯一檔案: {stats['unique_files']}")
    print(f"  總大小: {stats['total_size'] / 1024 / 1024:.2f} MB")
    print(f"  去重節省: {stats['deduplicated_size'] / 1024 / 1024:.2f} MB")
    print(f"  去重率: {stats['deduplication_ratio'] * 100:.2f}%")
    print()
    
    print("檔案位置:")
    print(f"  冷儲存目錄: cold_storage/")
    print(f"  粒子檔案: cold_storage/particles/")
    print(f"  重定向檔案: cold_storage/redirects/")
    print(f"  清單檔案: cold_storage_manifest.json")
    print()
    
    print("✓ 所有原始檔案已保留在原位置。")
    print("✓ 檔案記錄已保存到清單中。")
    print()


if __name__ == "__main__":
    main()
