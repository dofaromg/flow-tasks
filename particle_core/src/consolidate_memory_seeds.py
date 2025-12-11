#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
記憶種子合併工具 (Memory Seeds Consolidation Tool)
自動將多個記憶種子合併為指定數量的種子
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# 添加路徑以便導入模組
sys.path.insert(0, os.path.dirname(__file__))

from memory_archive_seed import MemoryArchiveSeed


class MemorySeedConsolidator:
    """記憶種子合併器"""
    
    def __init__(self, storage_path: str = "memory_seeds"):
        """
        初始化合併器
        
        Args:
            storage_path: 記憶種子儲存路徑
        """
        self.archive = MemoryArchiveSeed(storage_path)
        
    def get_all_seeds(self) -> List[Dict[str, Any]]:
        """取得所有記憶種子"""
        return self.archive.list_seeds()
    
    def consolidate_to_target(
        self,
        target_count: int = 10,
        strategy: str = "auto",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        合併記憶種子至目標數量
        
        Args:
            target_count: 目標種子數量（預設 10）
            strategy: 合併策略 ('auto', 'by_date', 'by_size', 'even')
            dry_run: 是否只模擬不實際執行
            
        Returns:
            合併結果報告
        """
        seeds = self.get_all_seeds()
        current_count = len(seeds)
        
        print(f"\n{'='*60}")
        print(f"記憶種子合併工具 - Memory Seeds Consolidation")
        print(f"{'='*60}\n")
        print(f"📊 當前種子數量: {current_count}")
        print(f"🎯 目標種子數量: {target_count}")
        print(f"📋 合併策略: {strategy}")
        print(f"🔍 模擬模式: {'是' if dry_run else '否'}\n")
        
        if current_count <= target_count:
            print(f"✅ 當前種子數量（{current_count}）已小於或等於目標數量（{target_count}）")
            print(f"   無需合併！\n")
            return {
                "status": "no_merge_needed",
                "current_count": current_count,
                "target_count": target_count,
                "seeds": seeds
            }
        
        # 計算需要合併的種子
        seeds_to_merge = current_count - target_count
        print(f"🔄 需要減少 {seeds_to_merge} 個種子\n")
        
        # 根據策略分組
        groups = self._create_merge_groups(seeds, target_count, strategy)
        
        # 顯示合併計劃
        print(f"📦 合併計劃:")
        for i, group in enumerate(groups, 1):
            print(f"   組 {i}: {len(group)} 個種子 → 合併為 1 個")
            for seed in group[:3]:  # 只顯示前 3 個
                print(f"      - {seed['seed_name']}")
            if len(group) > 3:
                print(f"      ... 還有 {len(group) - 3} 個")
        print()
        
        if dry_run:
            print("🔍 模擬模式：不執行實際合併\n")
            return {
                "status": "dry_run",
                "current_count": current_count,
                "target_count": target_count,
                "groups": groups,
                "would_merge": seeds_to_merge
            }
        
        # 執行合併
        print("🚀 開始合併...\n")
        merged_seeds = []
        
        for i, group in enumerate(groups, 1):
            if len(group) > 1:
                # 需要合併
                seed_names = [s['seed_name'] for s in group]
                merged_name = f"consolidated_{i:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                print(f"合併組 {i}...")
                result = self.archive.merge_seeds(seed_names, merged_name)
                
                print(f"  ✅ 已合併為: {result['seed_name']}")
                merged_seeds.append(result)
                
                # 刪除原始種子（可選）
                # 注意：這裡暫不刪除，保留原始資料的安全性
                
            else:
                # 單一種子，不需合併
                print(f"保留組 {i}: {group[0]['seed_name']}")
                merged_seeds.append(group[0])
        
        print(f"\n✅ 合併完成！")
        print(f"   原始數量: {current_count}")
        print(f"   最終數量: {len(merged_seeds)}")
        print()
        
        return {
            "status": "success",
            "original_count": current_count,
            "final_count": len(merged_seeds),
            "target_count": target_count,
            "merged_seeds": merged_seeds
        }
    
    def _create_merge_groups(
        self,
        seeds: List[Dict[str, Any]],
        target_count: int,
        strategy: str
    ) -> List[List[Dict[str, Any]]]:
        """
        根據策略創建合併組
        
        Args:
            seeds: 所有種子
            target_count: 目標數量
            strategy: 合併策略
            
        Returns:
            種子分組列表
        """
        if strategy == "by_date":
            # 按日期排序，相近的合併
            seeds = sorted(seeds, key=lambda x: x['created_at'])
        elif strategy == "by_size":
            # 按大小排序（需要讀取文件大小）
            seeds = sorted(seeds, key=lambda x: Path(x['file']).stat().st_size)
        elif strategy == "even":
            # 平均分配
            pass
        else:  # auto
            # 自動策略：按創建時間分組
            seeds = sorted(seeds, key=lambda x: x['created_at'])
        
        # 計算每組的平均大小
        total_seeds = len(seeds)
        group_size = total_seeds // target_count
        remainder = total_seeds % target_count
        
        groups = []
        idx = 0
        
        for i in range(target_count):
            # 前 remainder 組多分配一個種子
            current_group_size = group_size + (1 if i < remainder else 0)
            
            group = seeds[idx:idx + current_group_size]
            if group:
                groups.append(group)
            idx += current_group_size
        
        return groups
    
    def cleanup_old_seeds(self, keep_merged: bool = True) -> Dict[str, Any]:
        """
        清理舊的種子文件
        
        Args:
            keep_merged: 是否保留已合併的種子
            
        Returns:
            清理報告
        """
        print("\n⚠️  警告：此操作將刪除舊的種子文件！")
        print("建議先備份重要資料。\n")
        
        seeds = self.get_all_seeds()
        
        if keep_merged:
            # 只保留 consolidated_ 開頭的種子
            to_delete = [s for s in seeds if not s['seed_name'].startswith('consolidated_')]
        else:
            print("此功能需要謹慎使用，暫不提供自動刪除。")
            return {"status": "skipped"}
        
        print(f"將刪除 {len(to_delete)} 個舊種子")
        for seed in to_delete[:5]:
            print(f"  - {seed['seed_name']}")
        if len(to_delete) > 5:
            print(f"  ... 還有 {len(to_delete) - 5} 個")
        
        confirm = input("\n確定要刪除嗎？(yes/no): ")
        
        if confirm.lower() == 'yes':
            deleted = []
            for seed in to_delete:
                try:
                    Path(seed['file']).unlink()
                    deleted.append(seed['seed_name'])
                    print(f"  ✓ 已刪除: {seed['seed_name']}")
                except Exception as e:
                    print(f"  ✗ 刪除失敗: {seed['seed_name']} - {e}")
            
            print(f"\n✅ 清理完成，已刪除 {len(deleted)} 個種子")
            return {
                "status": "success",
                "deleted_count": len(deleted),
                "deleted_seeds": deleted
            }
        else:
            print("\n取消刪除操作")
            return {"status": "cancelled"}


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="記憶種子合併工具 - 將多個記憶種子合併為指定數量"
    )
    parser.add_argument(
        "--target",
        type=int,
        default=10,
        help="目標種子數量（預設: 10）"
    )
    parser.add_argument(
        "--strategy",
        choices=["auto", "by_date", "by_size", "even"],
        default="auto",
        help="合併策略（預設: auto）"
    )
    parser.add_argument(
        "--storage",
        type=str,
        default="memory_seeds",
        help="種子儲存路徑（預設: memory_seeds）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只模擬不實際執行"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有種子"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="清理舊的種子（保留合併後的）"
    )
    
    args = parser.parse_args()
    
    consolidator = MemorySeedConsolidator(args.storage)
    
    if args.list:
        # 列出所有種子
        seeds = consolidator.get_all_seeds()
        print(f"\n記憶種子列表 (共 {len(seeds)} 個):\n")
        for seed in seeds:
            print(f"  📦 {seed['seed_name']}")
            print(f"     建立時間: {seed['created_at']}")
            print(f"     檢查碼: {seed['checksum'][:16]}...")
            print()
    elif args.cleanup:
        # 清理舊種子
        result = consolidator.cleanup_old_seeds(keep_merged=True)
    else:
        # 執行合併
        result = consolidator.consolidate_to_target(
            target_count=args.target,
            strategy=args.strategy,
            dry_run=args.dry_run
        )
        
        # 顯示最終狀態
        if result['status'] == 'success':
            print("="*60)
            print("最終種子列表:")
            print("="*60 + "\n")
            for i, seed in enumerate(result['merged_seeds'], 1):
                print(f"{i:2d}. {seed.get('seed_name', 'Unknown')}")
            print()


if __name__ == "__main__":
    main()
