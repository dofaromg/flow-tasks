#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 超級電腦結構表情索引代理系統 - 主入口
運行完整的掃描、索引生成流程
"""

import sys
from pathlib import Path

# 添加 .copilot 目錄到 Python 路徑
copilot_dir = Path(__file__).parent / '.copilot'
sys.path.insert(0, str(copilot_dir))

from scanner.structure_scanner import StructureScanner
from generator.emoji_indexer import EmojiIndexer
from triggers.smart_updater import SmartUpdater


def run_full_scan(root_path: str = '.', max_depth: int = 8, check_triggers: bool = False):
    """
    執行完整的結構掃描和索引生成
    
    Args:
        root_path: 專案根目錄
        max_depth: 掃描深度
        check_triggers: 是否檢查觸發條件
    """
    print("=" * 60)
    print("🧠 AI 超級電腦結構表情索引代理系統")
    print("=" * 60)
    print()
    
    # 檢查是否需要更新（如果啟用）
    if check_triggers:
        print("🔍 檢查更新觸發條件...")
        updater = SmartUpdater(root_path=root_path)
        should_trigger, reasons = updater.should_trigger_update()
        
        if not should_trigger:
            print("✅ 未達到觸發閾值，跳過更新")
            return
        
        print("🚨 觸發更新:")
        for reason in reasons:
            print(f"  - {reason}")
        print()
    
    # 步驟 1: 結構掃描
    print("=" * 60)
    print("第 1 步: 結構掃描")
    print("=" * 60)
    print()
    
    scanner = StructureScanner(root_path=root_path, max_depth=max_depth)
    scan_results = scanner.scan()
    scanner.save_json('.copilot/structure-scan.json')
    
    # 步驟 2: 生成索引
    print("=" * 60)
    print("第 2 步: 生成表情符號索引")
    print("=" * 60)
    print()
    
    indexer = EmojiIndexer(scan_data=scan_results)
    indexer.generate_all(base_dir=root_path)
    
    # 完成
    print("=" * 60)
    print("✅ 所有步驟完成！")
    print("=" * 60)
    print()
    print("生成的檔案:")
    print("  - .copilot/structure-scan.json (原始掃描結果)")
    print("  - .copilot/structure-index.json (JSON 索引)")
    print("  - STRUCTURE.md (Markdown 文檔)")
    print("  - .copilot/structure.fltnz (Fluin 粒子格式)")
    print()


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AI 超級電腦結構表情索引代理系統',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 執行完整掃描（8 層深度）
  python run_structure_index.py
  
  # 指定掃描深度
  python run_structure_index.py --depth 5
  
  # 檢查觸發條件
  python run_structure_index.py --check-triggers
  
  # 指定專案目錄
  python run_structure_index.py --root /path/to/project
        """
    )
    
    parser.add_argument(
        '--root', 
        default='.', 
        help='專案根目錄 (預設: 當前目錄)'
    )
    parser.add_argument(
        '--depth', 
        type=int, 
        default=8, 
        help='掃描深度 (預設: 8 層)'
    )
    parser.add_argument(
        '--check-triggers', 
        action='store_true',
        help='檢查觸發條件，只在達到閾值時執行'
    )
    
    args = parser.parse_args()
    
    try:
        run_full_scan(
            root_path=args.root,
            max_depth=args.depth,
            check_triggers=args.check_triggers
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 執行失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
