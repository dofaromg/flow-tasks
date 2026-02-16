#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表情索引生成器 (Emoji Index Generator)
讀取掃描結果並生成三種格式的輸出
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class EmojiIndexer:
    """表情符號索引生成器"""
    
    # 模組分類規則
    MODULE_CATEGORIES = {
        '🧠 AI 核心': ['ai_', 'particle_', 'neural_', 'fusion_', 'MrLiou_AI'],
        '⚙️ 系統核心': ['runtime/', 'core/', 'engine/', 'particle_core'],
        '🐍 Python 模組': ['*.py'],
        '📜 Scripts': ['*.ts', '*.js', '*.jsx', '*.tsx'],
        '📝 文件': ['docs/', '*.md', 'README'],
        '🧪 測試': ['tests/', 'test_', '*.test.'],
        '🔧 配置': ['*.yml', '*.yaml', '*.json', '*.toml', '.github/', 'config'],
        '📦 套件': ['package.json', 'pyproject.toml', 'requirements.txt'],
        '🗂️ 資料': ['data/', 'seeds/', 'memory/'],
        '🎨 UI': ['ui/', 'frontend/', 'components/', 'pages/'],
        '🔐 安全': ['.env', 'secrets/', 'auth/'],
        '📊 報表': ['reports/', 'logs/', 'metrics/'],
    }
    
    def __init__(self, scan_data: Dict = None, scan_json_path: str = None):
        """
        初始化索引生成器
        
        Args:
            scan_data: 掃描數據字典
            scan_json_path: 掃描結果 JSON 檔案路徑
        """
        if scan_data:
            self.scan_data = scan_data
        elif scan_json_path:
            with open(scan_json_path, 'r', encoding='utf-8') as f:
                self.scan_data = json.load(f)
        else:
            raise ValueError("必須提供 scan_data 或 scan_json_path")
        
        self.categorized_modules = {}
        self.index_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': 'v1.0.0',
                'source': self.scan_data.get('metadata', {})
            },
            'categories': {},
            'statistics': self.scan_data.get('statistics', {})
        }
    
    def matches_pattern(self, path: str, pattern: str) -> bool:
        """檢查路徑是否匹配模式"""
        if pattern.startswith('*.'):
            # 檔案副檔名匹配
            return path.endswith(pattern[1:])
        elif pattern.endswith('/'):
            # 目錄匹配
            return pattern[:-1] in path
        else:
            # 名稱匹配
            return pattern in path
    
    def categorize_module(self, node: Dict, path_prefix: str = '') -> Dict:
        """分類模組"""
        if not node:
            return {}
        
        module_info = {
            'name': node.get('name', ''),
            'emoji': node.get('emoji', '📁'),
            'path': node.get('path', path_prefix),
            'type': node.get('type', 'directory'),
            'stats': node.get('stats', {}),
            'files': [],
            'submodules': []
        }
        
        # 收集檔案
        for file in node.get('files', []):
            module_info['files'].append({
                'name': file.get('name', ''),
                'emoji': file.get('emoji', '📄'),
                'path': file.get('path', ''),
                'lines': file.get('lines', 0),
                'size': file.get('size_bytes', 0)
            })
        
        # 遞迴處理子目錄
        for child in node.get('children', []):
            submodule = self.categorize_module(child, child.get('path', ''))
            if submodule:
                module_info['submodules'].append(submodule)
        
        return module_info
    
    def categorize_all(self):
        """對所有模組進行分類"""
        structure = self.scan_data.get('structure', {})
        
        # 遍歷所有節點並分類
        self._categorize_node(structure)
        
        # 整理到 index_data
        self.index_data['categories'] = self.categorized_modules
    
    def _categorize_node(self, node: Dict, parent_path: str = ''):
        """遞迴分類節點"""
        if not node:
            return
        
        node_path = node.get('path', parent_path)
        node_name = node.get('name', '')
        
        # 檢查此節點屬於哪個類別
        for category, patterns in self.MODULE_CATEGORIES.items():
            for pattern in patterns:
                if self.matches_pattern(node_path, pattern) or self.matches_pattern(node_name, pattern):
                    if category not in self.categorized_modules:
                        self.categorized_modules[category] = []
                    
                    module_info = self.categorize_module(node)
                    self.categorized_modules[category].append(module_info)
                    break
        
        # 遞迴處理子節點
        for child in node.get('children', []):
            self._categorize_node(child, node_path)
    
    def generate_markdown(self, output_path: str = 'STRUCTURE.md'):
        """生成 Markdown 格式索引"""
        lines = []
        
        # 標題和元數據
        lines.append('# 🗂️ Flow-Tasks 專案結構索引\n')
        lines.append(f"**生成時間**: {self.index_data['metadata']['generated_at']}\n")
        
        scan_meta = self.scan_data.get('metadata', {})
        lines.append(f"**索引深度**: {scan_meta.get('max_depth', 8)} 層\n")
        lines.append(f"**掃描版本**: {scan_meta.get('version', 'v1.0.0')}\n")
        lines.append('\n---\n\n')
        
        # 專案統計
        stats = self.scan_data.get('statistics', {})
        lines.append('## 📊 專案統計\n\n')
        lines.append(f"- **總檔案數**: {stats.get('total_files', 0):,}\n")
        lines.append(f"- **總目錄數**: {stats.get('total_dirs', 0):,}\n")
        lines.append(f"- **總代碼行數**: {stats.get('total_lines', 0):,}\n")
        
        total_size_mb = stats.get('total_size_bytes', 0) / 1024 / 1024
        lines.append(f"- **總大小**: {total_size_mb:.2f} MB\n")
        
        # 語言分佈
        file_types = stats.get('file_types', {})
        if file_types:
            lines.append('\n### 📋 檔案類型分佈\n\n')
            sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
            for file_type, count in sorted_types[:10]:
                lines.append(f"- `{file_type}`: {count} 個檔案\n")
        
        lines.append('\n---\n\n')
        
        # 模組分類
        for category, modules in self.categorized_modules.items():
            if not modules:
                continue
            
            lines.append(f'## {category}\n\n')
            
            for module in modules[:5]:  # 只顯示前 5 個模組
                name = module.get('name', '')
                path = module.get('path', '')
                stats = module.get('stats', {})
                
                lines.append(f"### {module.get('emoji', '📁')} {name}\n\n")
                lines.append(f"- **路徑**: `{path}`\n")
                lines.append(f"- **檔案數**: {stats.get('file_count', 0)}\n")
                lines.append(f"- **代碼行數**: {stats.get('total_lines', 0):,}\n")
                
                # 列出主要檔案
                files = module.get('files', [])
                if files:
                    lines.append('\n**主要檔案**:\n')
                    for file in files[:5]:
                        lines.append(f"- {file.get('emoji', '📄')} `{file.get('name', '')}` ")
                        lines.append(f"({file.get('lines', 0):,} 行)\n")
                
                lines.append('\n')
            
            if len(modules) > 5:
                lines.append(f'*... 還有 {len(modules) - 5} 個模組*\n\n')
            
            lines.append('---\n\n')
        
        # 寫入檔案
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"📝 已生成 Markdown 格式: {output_path}")
        return output_file
    
    def generate_json(self, output_path: str = '.copilot/structure-index.json'):
        """生成 JSON 格式索引"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.index_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 已生成 JSON 格式: {output_path}")
        return output_file
    
    def generate_fltnz(self, output_path: str = '.copilot/structure.fltnz'):
        """生成 Fluin 粒子格式索引"""
        lines = []
        
        # Fluin 標記語言格式
        lines.append('✦Seed:⊕StructureIndex/▽Depth8.0001→⚙Analysis\n')
        lines.append(f'∞Trace → ζGenerated[{datetime.now().isoformat()}]\n')
        lines.append('⊕Metadata:\n')
        
        stats = self.scan_data.get('statistics', {})
        lines.append(f'  ⊗Files[{stats.get("total_files", 0)}]\n')
        lines.append(f'  ⊗Dirs[{stats.get("total_dirs", 0)}]\n')
        lines.append(f'  ⊗Lines[{stats.get("total_lines", 0)}]\n')
        lines.append(f'  ⊗Size[{stats.get("total_size_bytes", 0)}]\n')
        lines.append('\n')
        
        # 模組分類（粒子格式）
        lines.append('⊕Categories:\n')
        for category, modules in self.categorized_modules.items():
            if not modules:
                continue
            
            lines.append(f'  ▽{category}:\n')
            lines.append(f'    ⊗Count[{len(modules)}]\n')
            
            for module in modules[:3]:
                name = module.get('name', '')
                path = module.get('path', '')
                stats = module.get('stats', {})
                
                lines.append(f'    →Module[{name}]:\n')
                lines.append(f'      ⊗Path[{path}]\n')
                lines.append(f'      ⊗Files[{stats.get("file_count", 0)}]\n')
                lines.append(f'      ⊗Lines[{stats.get("total_lines", 0)}]\n')
            
            if len(modules) > 3:
                lines.append(f'    ⊗More[{len(modules) - 3}]\n')
            
            lines.append('\n')
        
        lines.append('∞EndTrace\n')
        
        # 寫入檔案
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"⚛️  已生成 Fluin 格式: {output_path}")
        return output_file
    
    def generate_all(self, base_dir: str = '.'):
        """生成所有格式的索引"""
        print("\n🎨 開始生成表情符號索引...")
        
        # 分類模組
        self.categorize_all()
        
        # 生成三種格式
        self.generate_json(f'{base_dir}/.copilot/structure-index.json')
        self.generate_markdown(f'{base_dir}/STRUCTURE.md')
        self.generate_fltnz(f'{base_dir}/.copilot/structure.fltnz')
        
        print("✅ 所有格式已生成完成！\n")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='表情符號索引生成器')
    parser.add_argument('--input', default='.copilot/structure-scan.json', 
                       help='掃描結果 JSON 檔案')
    parser.add_argument('--output-dir', default='.', help='輸出目錄')
    
    args = parser.parse_args()
    
    # 創建生成器並生成索引
    indexer = EmojiIndexer(scan_json_path=args.input)
    indexer.generate_all(base_dir=args.output_dir)


if __name__ == '__main__':
    main()
