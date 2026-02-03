#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
結構掃描系統 (Structure Scanner)
掃描專案目錄至第 8 層深度，識別檔案類型並生成結構樹狀圖
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import hashlib


class StructureScanner:
    """專案結構掃描器"""
    
    # 檔案類型表情符號映射
    FILE_TYPE_EMOJIS = {
        '.py': '🐍',
        '.ts': '📜',
        '.tsx': '📜',
        '.js': '📜',
        '.jsx': '📜',
        '.md': '📝',
        '.yml': '⚙️',
        '.yaml': '⚙️',
        '.json': '⚙️',
        '.toml': '⚙️',
    }
    
    # 目錄類型表情符號映射
    DIRECTORY_EMOJIS = {
        'docs': '📚',
        'test': '🧪',
        'tests': '🧪',
        'ai_': '🧠',
        'particle_': '🧠',
        'neural_': '🧠',
        'fusion_': '🧠',
        'runtime': '⚙️',
        'core': '⚙️',
        'engine': '⚙️',
        'ui': '🎨',
        'frontend': '🎨',
        'components': '🎨',
        'data': '🗂️',
        'seeds': '🗂️',
        'memory': '🗂️',
        'config': '🔧',
        '.github': '🔄',
        'workflows': '🔄',
        'security': '🔐',
        'auth': '🔐',
        'reports': '📊',
        'logs': '📊',
        'metrics': '📊',
    }
    
    # 忽略的目錄
    IGNORE_DIRS = {
        '.git', '__pycache__', 'node_modules', '.next', 'dist',
        'build', '.venv', 'venv', '.vercel', '.cache', 'coverage',
        '.pytest_cache', '.tox', '.egg-info', 'eggs', 'lib', 'lib64',
        'parts', 'sdist', 'var', 'wheels', '*.egg', '.installed.cfg'
    }
    
    def __init__(self, root_path: str = '.', max_depth: int = 8):
        """
        初始化掃描器
        
        Args:
            root_path: 專案根目錄路徑
            max_depth: 最大掃描深度
        """
        self.root_path = Path(root_path).resolve()
        self.max_depth = max_depth
        self.scan_results = {
            'metadata': {
                'scan_time': datetime.now().isoformat(),
                'root_path': str(self.root_path),
                'max_depth': max_depth,
                'version': 'v1.0.0'
            },
            'statistics': {
                'total_files': 0,
                'total_dirs': 0,
                'total_lines': 0,
                'file_types': {},
                'total_size_bytes': 0
            },
            'structure': {}
        }
    
    def should_ignore(self, path: Path) -> bool:
        """檢查是否應該忽略此路徑"""
        name = path.name
        # 檢查忽略列表
        for ignore_pattern in self.IGNORE_DIRS:
            if ignore_pattern.startswith('*'):
                if name.endswith(ignore_pattern[1:]):
                    return True
            else:
                if name == ignore_pattern or name.startswith(ignore_pattern):
                    return True
        # 忽略隱藏目錄（除了 .github, .copilot）
        if name.startswith('.') and name not in {'.github', '.copilot', '.flowcore'}:
            return True
        return False
    
    def get_emoji_for_file(self, file_path: Path) -> str:
        """獲取檔案的表情符號"""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()
        
        # 特殊檔案名稱檢查
        if name.startswith('test_') or name.endswith('.test.ts') or name.endswith('.test.js'):
            return '🧪'
        if any(prefix in name for prefix in ['ai_', 'particle_', 'neural_', 'fusion_']):
            return '🧠'
        
        # 根據副檔名返回
        return self.FILE_TYPE_EMOJIS.get(suffix, '📄')
    
    def get_emoji_for_directory(self, dir_path: Path) -> str:
        """獲取目錄的表情符號"""
        name = dir_path.name.lower()
        
        # 檢查完全匹配
        if name in self.DIRECTORY_EMOJIS:
            return self.DIRECTORY_EMOJIS[name]
        
        # 檢查前綴匹配
        for prefix, emoji in self.DIRECTORY_EMOJIS.items():
            if name.startswith(prefix):
                return emoji
        
        return '📁'
    
    def count_lines(self, file_path: Path) -> int:
        """計算檔案行數"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return len(f.readlines())
        except Exception:
            return 0
    
    def scan_directory(self, path: Path, current_depth: int = 0) -> Dict:
        """
        遞迴掃描目錄
        
        Args:
            path: 要掃描的路徑
            current_depth: 當前深度
            
        Returns:
            目錄結構字典
        """
        if current_depth > self.max_depth:
            return {}
        
        if not path.is_dir():
            return {}
        
        result = {
            'type': 'directory',
            'name': path.name,
            'emoji': self.get_emoji_for_directory(path),
            'path': str(path.relative_to(self.root_path)),
            'depth': current_depth,
            'children': [],
            'files': [],
            'stats': {
                'file_count': 0,
                'dir_count': 0,
                'total_lines': 0,
                'size_bytes': 0
            }
        }
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            for item in items:
                if self.should_ignore(item):
                    continue
                
                if item.is_dir():
                    # 遞迴掃描子目錄
                    child_result = self.scan_directory(item, current_depth + 1)
                    if child_result:
                        result['children'].append(child_result)
                        # 累加統計
                        result['stats']['file_count'] += child_result['stats']['file_count']
                        result['stats']['dir_count'] += 1 + child_result['stats']['dir_count']
                        result['stats']['total_lines'] += child_result['stats']['total_lines']
                        result['stats']['size_bytes'] += child_result['stats']['size_bytes']
                        
                        self.scan_results['statistics']['total_dirs'] += 1
                
                elif item.is_file():
                    # 處理檔案
                    lines = self.count_lines(item)
                    size = item.stat().st_size
                    
                    file_info = {
                        'type': 'file',
                        'name': item.name,
                        'emoji': self.get_emoji_for_file(item),
                        'path': str(item.relative_to(self.root_path)),
                        'suffix': item.suffix,
                        'lines': lines,
                        'size_bytes': size
                    }
                    
                    result['files'].append(file_info)
                    
                    # 更新統計
                    result['stats']['file_count'] += 1
                    result['stats']['total_lines'] += lines
                    result['stats']['size_bytes'] += size
                    
                    self.scan_results['statistics']['total_files'] += 1
                    self.scan_results['statistics']['total_lines'] += lines
                    self.scan_results['statistics']['total_size_bytes'] += size
                    
                    # 更新檔案類型統計
                    suffix = item.suffix or 'no-extension'
                    if suffix in self.scan_results['statistics']['file_types']:
                        self.scan_results['statistics']['file_types'][suffix] += 1
                    else:
                        self.scan_results['statistics']['file_types'][suffix] = 1
        
        except PermissionError:
            pass
        
        return result
    
    def scan(self) -> Dict:
        """執行完整掃描"""
        print(f"🔍 開始掃描專案結構...")
        print(f"📂 根目錄: {self.root_path}")
        print(f"📊 最大深度: {self.max_depth} 層")
        print()
        
        # 掃描根目錄
        self.scan_results['structure'] = self.scan_directory(self.root_path)
        
        print(f"✅ 掃描完成!")
        print(f"📁 總目錄數: {self.scan_results['statistics']['total_dirs']}")
        print(f"📄 總檔案數: {self.scan_results['statistics']['total_files']}")
        print(f"📏 總代碼行數: {self.scan_results['statistics']['total_lines']:,}")
        print(f"💾 總大小: {self.scan_results['statistics']['total_size_bytes'] / 1024 / 1024:.2f} MB")
        print()
        
        return self.scan_results
    
    def save_json(self, output_path: str = '.copilot/structure-scan.json'):
        """儲存 JSON 格式結果"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.scan_results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 已儲存 JSON 格式: {output_path}")
        return output_file
    
    def generate_tree_view(self, node: Dict, prefix: str = '', is_last: bool = True) -> List[str]:
        """生成樹狀視圖"""
        lines = []
        
        if node.get('type') == 'directory':
            connector = '└── ' if is_last else '├── '
            emoji = node.get('emoji', '📁')
            name = node.get('name', '')
            stats = node.get('stats', {})
            
            line = f"{prefix}{connector}{emoji} {name}/"
            if stats.get('file_count', 0) > 0:
                line += f" ({stats['file_count']} files, {stats['total_lines']:,} lines)"
            lines.append(line)
            
            # 準備子項目的前綴
            child_prefix = prefix + ('    ' if is_last else '│   ')
            
            # 處理子目錄
            children = node.get('children', [])
            files = node.get('files', [])
            all_items = children + files
            
            for i, item in enumerate(all_items):
                is_last_item = (i == len(all_items) - 1)
                
                if item.get('type') == 'directory':
                    lines.extend(self.generate_tree_view(item, child_prefix, is_last_item))
                elif item.get('type') == 'file':
                    connector = '└── ' if is_last_item else '├── '
                    emoji = item.get('emoji', '📄')
                    name = item.get('name', '')
                    lines_count = item.get('lines', 0)
                    
                    file_line = f"{child_prefix}{connector}{emoji} {name}"
                    if lines_count > 0:
                        file_line += f" ({lines_count:,} lines)"
                    lines.append(file_line)
        
        return lines
    
    def print_tree(self):
        """列印樹狀結構"""
        print("🌳 專案結構樹:")
        print()
        tree_lines = self.generate_tree_view(self.scan_results['structure'])
        for line in tree_lines[:100]:  # 限制輸出行數
            print(line)
        
        if len(tree_lines) > 100:
            print(f"... (還有 {len(tree_lines) - 100} 行)")
        print()


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='專案結構掃描器')
    parser.add_argument('--root', default='.', help='專案根目錄')
    parser.add_argument('--depth', type=int, default=8, help='最大掃描深度')
    parser.add_argument('--output', default='.copilot/structure-scan.json', help='輸出檔案路徑')
    parser.add_argument('--tree', action='store_true', help='顯示樹狀結構')
    
    args = parser.parse_args()
    
    # 創建掃描器並執行掃描
    scanner = StructureScanner(root_path=args.root, max_depth=args.depth)
    scanner.scan()
    
    # 儲存結果
    scanner.save_json(args.output)
    
    # 顯示樹狀結構
    if args.tree:
        scanner.print_tree()


if __name__ == '__main__':
    main()
