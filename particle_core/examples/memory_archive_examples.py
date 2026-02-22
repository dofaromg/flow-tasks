#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
記憶封存種子系統 - 實用範例
展示各種實際應用場景
"""

import sys
import os

# 添加路徑以便導入模組
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from memory_archive_seed import MemoryArchiveSeed
from logic_pipeline import LogicPipeline
from rebuild_fn import FunctionRestorer


def example_1_basic_usage():
    """範例 1: 基本使用"""
    print("=== 範例 1: 基本記憶封存與還原 ===\n")
    
    archive = MemoryArchiveSeed()
    
    # 創建記憶種子
    result = archive.create_seed(
        particle_data="第一個測試資料",
        seed_name="example_001"
    )
    print(f"✅ 種子已創建: {result['seed_name']}")
    print(f"   檔案位置: {result['seed_file']}\n")
    
    # 還原記憶種子
    restored = archive.restore_seed("example_001")
    print(f"✅ 記憶已還原: {restored['particle_data']}\n")


def example_2_with_metadata():
    """範例 2: 帶元資料的記憶封存"""
    print("=== 範例 2: 帶元資料的記憶封存 ===\n")
    
    archive = MemoryArchiveSeed()
    
    # 創建帶有豐富元資料的種子
    result = archive.create_seed(
        particle_data={
            "task_id": "TASK-001",
            "task_name": "資料處理任務",
            "status": "completed",
            "output": "處理完成，共處理 1000 筆資料"
        },
        metadata={
            "author": "MRLiou",
            "department": "AI Research",
            "priority": "high",
            "tags": ["production", "important"]
        },
        seed_name="task_001_result"
    )
    
    print(f"✅ 任務結果已封存: {result['seed_name']}")
    
    # 還原並查看完整資訊
    restored = archive.restore_seed("task_001_result")
    print(f"\n📋 任務資訊:")
    print(f"   任務 ID: {restored['particle_data']['task_id']}")
    print(f"   任務名稱: {restored['particle_data']['task_name']}")
    print(f"   狀態: {restored['particle_data']['status']}")
    print(f"   作者: {restored['metadata']['author']}")
    print(f"   優先級: {restored['metadata']['priority']}\n")


def example_3_logic_pipeline_integration():
    """範例 3: 與邏輯管線整合"""
    print("=== 範例 3: 邏輯管線結果封存 ===\n")
    
    # 執行邏輯管線
    pipeline = LogicPipeline()
    logic_result = pipeline.simulate("處理客戶資料：張三")
    
    print(f"邏輯處理結果:")
    print(f"   輸入: {logic_result['input']}")
    print(f"   處理鏈: {' → '.join(logic_result['steps'])}")
    print(f"   結果: {logic_result['result']}\n")
    
    # 封存邏輯處理結果
    archive = MemoryArchiveSeed()
    seed_result = archive.create_seed(
        particle_data={
            "input": logic_result['input'],
            "steps": logic_result['steps'],
            "result": logic_result['result'],
            "compressed": logic_result['compressed']
        },
        metadata={
            "type": "logic_pipeline_result",
            "customer": "張三"
        },
        seed_name="customer_zhang_logic"
    )
    
    print(f"✅ 邏輯結果已封存: {seed_result['seed_name']}")
    
    # 壓縮種子
    compressed = archive.compress_seed("customer_zhang_logic")
    print(f"   壓縮格式: {compressed}\n")


def example_4_batch_processing():
    """範例 4: 批次處理與封存"""
    print("=== 範例 4: 批次資料處理與封存 ===\n")
    
    archive = MemoryArchiveSeed()
    pipeline = LogicPipeline()
    
    # 批次處理資料
    customers = ["客戶A", "客戶B", "客戶C", "客戶D", "客戶E"]
    
    print("批次處理中...")
    for i, customer in enumerate(customers):
        # 處理資料
        result = pipeline.simulate(f"處理{customer}的訂單")
        
        # 封存結果
        archive.create_seed(
            particle_data=result,
            metadata={"batch_id": "BATCH-001", "customer": customer},
            seed_name=f"batch_001_customer_{i+1:02d}"
        )
        print(f"  ✓ {customer} 處理完成並封存")
    
    print("\n所有批次資料已處理完成！")
    
    # 列出所有種子
    seeds = archive.list_seeds()
    batch_seeds = [s for s in seeds if 'batch_001' in s['seed_name']]
    print(f"\n批次種子數量: {len(batch_seeds)}")
    for seed in batch_seeds[:3]:  # 只顯示前3個
        print(f"  - {seed['seed_name']}")
    print()


def example_5_seed_merging():
    """範例 5: 種子合併"""
    print("=== 範例 5: 合併多個記憶種子 ===\n")
    
    archive = MemoryArchiveSeed()
    
    # 創建多個種子
    print("創建測試種子...")
    archive.create_seed("資料片段 A", seed_name="fragment_a")
    archive.create_seed("資料片段 B", seed_name="fragment_b")
    archive.create_seed("資料片段 C", seed_name="fragment_c")
    print("✓ 已創建 3 個資料片段\n")
    
    # 合併種子
    print("合併種子中...")
    merged_result = archive.merge_seeds(
        seed_names=["fragment_a", "fragment_b", "fragment_c"],
        merged_name="complete_data"
    )
    
    print(f"✅ 種子已合併: {merged_result['seed_name']}")
    print(f"   檔案: {merged_result['seed_file']}\n")
    
    # 查看合併結果
    merged = archive.restore_seed("complete_data")
    print(f"合併後的資料:")
    print(f"   來源: {merged['particle_data']['merged_from']}")
    print(f"   粒子數量: {len(merged['particle_data']['particles'])}")
    print()


def example_6_export_import():
    """範例 6: 匯出與匯入"""
    print("=== 範例 6: 種子匯出與匯入 ===\n")
    
    archive = MemoryArchiveSeed()
    
    # 創建種子
    archive.create_seed(
        particle_data="重要的專案資料",
        metadata={"project": "ProjectX", "version": "2.0"},
        seed_name="project_x_data"
    )
    print("✓ 專案資料種子已創建\n")
    
    # 匯出種子（用於備份或分享）
    export_path = archive.export_seed("project_x_data")
    print(f"✅ 種子已匯出至: {export_path}")
    print("   可用於備份或分享給其他系統\n")
    
    # 模擬在另一個系統匯入
    print("模擬匯入流程...")
    imported = archive.import_seed(export_path)
    print(f"✅ 種子已匯入: {imported['seed_name']}")
    print()


def example_7_compression_comparison():
    """範例 7: 壓縮格式比較"""
    print("=== 範例 7: 壓縮格式比較 ===\n")
    
    archive = MemoryArchiveSeed()
    restorer = FunctionRestorer()
    
    # 創建測試種子
    test_data = {
        "logic_chain": ["structure", "mark", "flow", "recurse", "store"],
        "description": "標準邏輯鏈測試"
    }
    
    archive.create_seed(
        particle_data=test_data,
        seed_name="compression_test"
    )
    
    # 不同壓縮方式
    print("壓縮格式比較:")
    
    # 1. 記憶種子壓縮
    memory_compressed = archive.compress_seed("compression_test")
    print(f"1. 記憶種子格式:")
    print(f"   {memory_compressed}\n")
    
    # 2. 函數還原器壓縮
    fn_compressed = restorer.compress_fn(test_data["logic_chain"])
    print(f"2. 函數鏈格式:")
    print(f"   {fn_compressed}\n")
    
    # 3. 人類可讀格式
    readable = restorer.to_human_readable(test_data["logic_chain"])
    print(f"3. 人類可讀格式:")
    for i, desc in enumerate(readable, 1):
        print(f"   {i}. {desc}")
    print()


def example_8_version_control():
    """範例 8: 版本控制"""
    print("=== 範例 8: 資料版本控制 ===\n")
    
    archive = MemoryArchiveSeed()
    
    # 創建不同版本
    versions = [
        {"version": "v1.0", "data": "初始版本資料"},
        {"version": "v1.1", "data": "修正錯誤後的資料"},
        {"version": "v2.0", "data": "重大更新版本資料"}
    ]
    
    print("創建版本歷史...")
    for ver in versions:
        archive.create_seed(
            particle_data=ver["data"],
            metadata={"version": ver["version"]},
            seed_name=f"data_{ver['version'].replace('.', '_')}"
        )
        print(f"  ✓ {ver['version']} 已創建")
    
    print("\n版本列表:")
    seeds = archive.list_seeds()
    version_seeds = [s for s in seeds if 'data_v' in s['seed_name']]
    for seed in version_seeds:
        print(f"  - {seed['seed_name']} (創建於 {seed['created_at'][:19]})")
    print()


def run_all_examples():
    """執行所有範例"""
    examples = [
        example_1_basic_usage,
        example_2_with_metadata,
        example_3_logic_pipeline_integration,
        example_4_batch_processing,
        example_5_seed_merging,
        example_6_export_import,
        example_7_compression_comparison,
        example_8_version_control
    ]
    
    for i, example in enumerate(examples, 1):
        example()
        if i < len(examples):
            input("\n按 Enter 繼續下一個範例...")
            print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print("=" * 60)
    print("記憶封存種子系統 - 實用範例集")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        examples = {
            "1": example_1_basic_usage,
            "2": example_2_with_metadata,
            "3": example_3_logic_pipeline_integration,
            "4": example_4_batch_processing,
            "5": example_5_seed_merging,
            "6": example_6_export_import,
            "7": example_7_compression_comparison,
            "8": example_8_version_control,
            "all": run_all_examples
        }
        
        if example_num in examples:
            examples[example_num]()
        else:
            print(f"未知的範例編號: {example_num}")
            print("\n可用範例:")
            print("  1 - 基本使用")
            print("  2 - 帶元資料的封存")
            print("  3 - 邏輯管線整合")
            print("  4 - 批次處理")
            print("  5 - 種子合併")
            print("  6 - 匯出與匯入")
            print("  7 - 壓縮格式比較")
            print("  8 - 版本控制")
            print("  all - 執行所有範例")
    else:
        print("使用方式: python memory_archive_examples.py [範例編號]")
        print("\n可用範例:")
        print("  1 - 基本使用")
        print("  2 - 帶元資料的封存")
        print("  3 - 邏輯管線整合")
        print("  4 - 批次處理")
        print("  5 - 種子合併")
        print("  6 - 匯出與匯入")
        print("  7 - 壓縮格式比較")
        print("  8 - 版本控制")
        print("  all - 執行所有範例")
        print("\n範例: python memory_archive_examples.py 1")
