#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能更新觸發系統 (Smart Update Trigger)
監控專案變更並根據閾值自動觸發結構索引更新
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class SmartUpdater:
    """智能更新觸發系統"""
    
    # 觸發閾值配置
    TRIGGER_THRESHOLDS = {
        'error_rate': 0.15,         # 錯誤率 > 15%
        'failed_builds': 3,          # 連續 3 次失敗
        'structure_changes': 10,     # 單日結構變更 > 10 個檔案
        'new_files': 5,              # 新增檔案 > 5 個
        'deleted_files': 3,          # 刪除檔案 > 3 個
        'complexity_spike': 1.5,     # 複雜度增長 > 150%
    }
    
    def __init__(self, root_path: str = '.', config_path: str = None):
        """
        初始化更新觸發器
        
        Args:
            root_path: 專案根目錄
            config_path: 配置檔案路徑（可選）
        """
        self.root_path = Path(root_path).resolve()
        self.config_path = config_path
        
        # 載入或使用預設閾值
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                self.thresholds = json.load(f).get('thresholds', self.TRIGGER_THRESHOLDS)
        else:
            self.thresholds = self.TRIGGER_THRESHOLDS.copy()
        
        self.metrics = {
            'git_changes': {},
            'build_status': {},
            'complexity': {},
            'should_trigger': False,
            'trigger_reasons': []
        }
    
    def check_git_changes(self) -> Dict:
        """檢查 Git 變更"""
        try:
            # 獲取最近的提交
            result = subprocess.run(
                ['git', 'diff', '--stat', 'HEAD~1', 'HEAD'],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout
                lines = output.strip().split('\n')
                
                files_changed = 0
                insertions = 0
                deletions = 0
                
                for line in lines:
                    if 'files changed' in line or 'file changed' in line:
                        parts = line.split(',')
                        for part in parts:
                            if 'file' in part:
                                files_changed = int(part.split()[0])
                            elif 'insertion' in part:
                                insertions = int(part.split()[0])
                            elif 'deletion' in part:
                                deletions = int(part.split()[0])
                
                self.metrics['git_changes'] = {
                    'files_changed': files_changed,
                    'insertions': insertions,
                    'deletions': deletions,
                    'timestamp': datetime.now().isoformat()
                }
                
                return self.metrics['git_changes']
        
        except Exception as e:
            print(f"⚠️  無法檢查 Git 變更: {e}")
            return {}
        
        return {}
    
    def check_new_and_deleted_files(self) -> Tuple[int, int]:
        """檢查新增和刪除的檔案"""
        try:
            # 獲取新增的檔案
            result_new = subprocess.run(
                ['git', 'diff', '--name-only', '--diff-filter=A', 'HEAD~1', 'HEAD'],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            new_files = len(result_new.stdout.strip().split('\n')) if result_new.stdout.strip() else 0
            
            # 獲取刪除的檔案
            result_deleted = subprocess.run(
                ['git', 'diff', '--name-only', '--diff-filter=D', 'HEAD~1', 'HEAD'],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            deleted_files = len(result_deleted.stdout.strip().split('\n')) if result_deleted.stdout.strip() else 0
            
            return new_files, deleted_files
        
        except Exception as e:
            print(f"⚠️  無法檢查檔案變更: {e}")
            return 0, 0
    
    def check_complexity_changes(self) -> float:
        """檢查複雜度變化"""
        try:
            # 讀取舊的索引（如果存在）
            old_index_path = self.root_path / '.copilot' / 'structure-index.json'
            if old_index_path.exists():
                with open(old_index_path, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                    old_lines = old_data.get('statistics', {}).get('total_lines', 0)
                
                # 執行新的掃描（簡化版）
                import sys
                from pathlib import Path as PathLib
                
                # 添加 .copilot 目錄到 Python 路徑
                copilot_dir = PathLib(__file__).parent.parent
                if str(copilot_dir) not in sys.path:
                    sys.path.insert(0, str(copilot_dir))
                
                from scanner.structure_scanner import StructureScanner
                scanner = StructureScanner(root_path=str(self.root_path), max_depth=8)
                scanner.scan()
                new_lines = scanner.scan_results['statistics']['total_lines']
                
                if old_lines > 0:
                    growth_rate = new_lines / old_lines
                    self.metrics['complexity'] = {
                        'old_lines': old_lines,
                        'new_lines': new_lines,
                        'growth_rate': growth_rate
                    }
                    return growth_rate
        
        except Exception as e:
            print(f"⚠️  無法檢查複雜度變化: {e}")
        
        return 1.0
    
    def should_trigger_update(self) -> Tuple[bool, List[str]]:
        """檢查是否應該觸發更新"""
        reasons = []
        
        # 1. 檢查 Git 變更
        git_changes = self.check_git_changes()
        if git_changes:
            files_changed = git_changes.get('files_changed', 0)
            if files_changed >= self.thresholds['structure_changes']:
                reasons.append(f"結構變更過多: {files_changed} 個檔案")
        
        # 2. 檢查新增和刪除的檔案
        new_files, deleted_files = self.check_new_and_deleted_files()
        if new_files >= self.thresholds['new_files']:
            reasons.append(f"新增檔案過多: {new_files} 個")
        if deleted_files >= self.thresholds['deleted_files']:
            reasons.append(f"刪除檔案過多: {deleted_files} 個")
        
        # 3. 檢查複雜度激增
        growth_rate = self.check_complexity_changes()
        if growth_rate >= self.thresholds['complexity_spike']:
            reasons.append(f"複雜度激增: {growth_rate:.2%}")
        
        should_trigger = len(reasons) > 0
        self.metrics['should_trigger'] = should_trigger
        self.metrics['trigger_reasons'] = reasons
        
        return should_trigger, reasons
    
    def trigger_update(self, force: bool = False):
        """觸發結構索引更新"""
        if force:
            print("🔄 強制觸發結構索引更新...")
        else:
            should_trigger, reasons = self.should_trigger_update()
            
            if not should_trigger:
                print("✅ 未達到觸發閾值，無需更新")
                return False
            
            print("🚨 觸發更新條件滿足:")
            for reason in reasons:
                print(f"  - {reason}")
        
        print("\n開始更新結構索引...")
        
        # 執行掃描
        try:
            import sys
            from pathlib import Path
            
            # 添加 .copilot 目錄到 Python 路徑
            copilot_dir = Path(__file__).parent.parent
            if str(copilot_dir) not in sys.path:
                sys.path.insert(0, str(copilot_dir))
            
            from scanner.structure_scanner import StructureScanner
            scanner = StructureScanner(root_path=str(self.root_path), max_depth=8)
            scanner.scan()
            scanner.save_json('.copilot/structure-scan.json')
            
            # 生成索引
            from generator.emoji_indexer import EmojiIndexer
            indexer = EmojiIndexer(scan_data=scanner.scan_results)
            indexer.generate_all()
            
            print("✅ 結構索引更新完成！")
            return True
        
        except Exception as e:
            print(f"❌ 更新失敗: {e}")
            return False
    
    def save_metrics(self, output_path: str = '.copilot/update-metrics.json'):
        """儲存監控指標"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, ensure_ascii=False, indent=2)
        
        print(f"📊 已儲存監控指標: {output_path}")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='智能更新觸發系統')
    parser.add_argument('--root', default='.', help='專案根目錄')
    parser.add_argument('--config', help='配置檔案路徑')
    parser.add_argument('--check', action='store_true', help='僅檢查是否需要更新')
    parser.add_argument('--force', action='store_true', help='強制觸發更新')
    parser.add_argument('--save-metrics', action='store_true', help='儲存監控指標')
    
    args = parser.parse_args()
    
    # 創建更新觸發器
    updater = SmartUpdater(root_path=args.root, config_path=args.config)
    
    if args.check:
        # 僅檢查
        should_trigger, reasons = updater.should_trigger_update()
        if should_trigger:
            print("🚨 建議觸發更新:")
            for reason in reasons:
                print(f"  - {reason}")
        else:
            print("✅ 無需更新")
    else:
        # 執行更新
        updater.trigger_update(force=args.force)
    
    if args.save_metrics:
        updater.save_metrics()


if __name__ == '__main__':
    main()
