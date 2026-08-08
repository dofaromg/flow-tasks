#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
創建範例記憶種子工具
用於測試記憶種子合併功能
"""

import os
import sys
from datetime import datetime, timedelta
import random

# 添加路徑以便導入模組
sys.path.insert(0, os.path.dirname(__file__))

from memory_archive_seed import MemoryArchiveSeed


def create_sample_seeds(count: int = 25, storage_path: str = "memory_seeds"):
    """
    創建範例記憶種子
    
    Args:
        count: 要創建的種子數量
        storage_path: 儲存路徑
    """
    archive = MemoryArchiveSeed(storage_path)
    
    print(f"\n{'='*60}")
    print(f"創建範例記憶種子")
    print(f"{'='*60}\n")
    print(f"目標數量: {count} 個種子")
    print(f"儲存路徑: {storage_path}\n")
    
    # 範例資料類型
    data_types = [
        "客戶資料",
        "訂單記錄",
        "產品資訊",
        "交易日誌",
        "系統日誌",
        "分析報告",
        "用戶行為",
        "庫存資料",
        "財務記錄",
        "專案資料"
    ]
    
    created_seeds = []
    
    print("開始創建種子...\n")
    
    for i in range(count):
        # 產生隨機資料
        data_type = random.choice(data_types)
        
        particle_data = {
            "id": f"DATA-{i+1:04d}",
            "type": data_type,
            "content": f"這是第 {i+1} 個 {data_type} 範例",
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 720))).isoformat(),
            "status": random.choice(["active", "archived", "processed"]),
            "size": random.randint(100, 10000),
            "tags": random.sample(["重要", "緊急", "待處理", "已完成", "測試"], k=min(random.randint(1, 3), 5))
        }
        
        metadata = {
            "source": "sample_generator",
            "batch": "test_batch_001",
            "priority": random.choice(["low", "medium", "high"]),
            "department": random.choice(["研發部", "業務部", "財務部", "人資部"])
        }
        
        seed_name = f"sample_seed_{i+1:03d}"
        
        try:
            result = archive.create_seed(
                particle_data=particle_data,
                metadata=metadata,
                seed_name=seed_name
            )
            created_seeds.append(result)
            print(f"  ✓ 已創建: {seed_name} ({data_type})")
        except Exception as e:
            print(f"  ✗ 創建失敗: {seed_name} - {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ 完成！")
    print(f"{'='*60}\n")
    print(f"成功創建: {len(created_seeds)} 個種子")
    print(f"儲存位置: {storage_path}/\n")
    
    # 列出所有種子
    all_seeds = archive.list_seeds()
    print(f"當前總共有: {len(all_seeds)} 個種子\n")
    
    return created_seeds


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="創建範例記憶種子用於測試合併功能"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=25,
        help="要創建的種子數量（預設: 25）"
    )
    parser.add_argument(
        "--storage",
        type=str,
        default="memory_seeds",
        help="種子儲存路徑（預設: memory_seeds）"
    )
    
    args = parser.parse_args()
    
    create_sample_seeds(count=args.count, storage_path=args.storage)


if __name__ == "__main__":
    main()
