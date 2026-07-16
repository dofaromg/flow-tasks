"""
對話知識提取器 - Conversation Knowledge Extractor
作者: MR.liou × Claude (empathetic.mirror)
版本: v1.0

功能:
1. 對話打包與導出
2. 注意力機制分析（識別重點）
3. 邏輯結構提取
4. 知識圖譜生成
5. 概念關聯分析
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict
from collections import Counter, defaultdict
from html import escape as html_escape

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConversationExtractor:
    """對話知識提取器核心類別"""
    
    # 預定義調色盤主題
    COLOR_PALETTES = {
        "default": {
            "name": "預設 (Default)",
            "bg_body": "#f5f5f5",
            "bg_container": "white",
            "bg_metadata": "#f8f9fa",
            "bg_user": "#e3f2fd",
            "bg_assistant": "#f3e5f5",
            "bg_stats": "#fff3e0",
            "border_title": "#4CAF50",
            "border_user": "#2196F3",
            "border_assistant": "#9C27B0",
            "text_primary": "#333",
            "text_secondary": "#555"
        },
        "ocean": {
            "name": "海洋 (Ocean)",
            "bg_body": "#e0f7fa",
            "bg_container": "white",
            "bg_metadata": "#b2ebf2",
            "bg_user": "#b2dfdb",
            "bg_assistant": "#c8e6c9",
            "bg_stats": "#fff9c4",
            "border_title": "#00796b",
            "border_user": "#00897b",
            "border_assistant": "#388e3c",
            "text_primary": "#004d40",
            "text_secondary": "#00695c"
        },
        "sunset": {
            "name": "日落 (Sunset)",
            "bg_body": "#ffe0b2",
            "bg_container": "white",
            "bg_metadata": "#ffccbc",
            "bg_user": "#ffecb3",
            "bg_assistant": "#ffe0b2",
            "bg_stats": "#f8bbd0",
            "border_title": "#d84315",
            "border_user": "#f57c00",
            "border_assistant": "#e64a19",
            "text_primary": "#bf360c",
            "text_secondary": "#d84315"
        },
        "night": {
            "name": "夜晚 (Night)",
            "bg_body": "#263238",
            "bg_container": "#37474f",
            "bg_metadata": "#455a64",
            "bg_user": "#546e7a",
            "bg_assistant": "#607d8b",
            "bg_stats": "#78909c",
            "border_title": "#00bcd4",
            "border_user": "#03a9f4",
            "border_assistant": "#00acc1",
            "text_primary": "#eceff1",
            "text_secondary": "#cfd8dc"
        },
        "forest": {
            "name": "森林 (Forest)",
            "bg_body": "#e8f5e9",
            "bg_container": "white",
            "bg_metadata": "#c8e6c9",
            "bg_user": "#a5d6a7",
            "bg_assistant": "#c5e1a5",
            "bg_stats": "#f0f4c3",
            "border_title": "#2e7d32",
            "border_user": "#388e3c",
            "border_assistant": "#558b2f",
            "text_primary": "#1b5e20",
            "text_secondary": "#2e7d32"
        },
        "minimal": {
            "name": "極簡 (Minimal)",
            "bg_body": "#ffffff",
            "bg_container": "#fafafa",
            "bg_metadata": "#f5f5f5",
            "bg_user": "#eeeeee",
            "bg_assistant": "#e0e0e0",
            "bg_stats": "#f5f5f5",
            "border_title": "#000000",
            "border_user": "#424242",
            "border_assistant": "#616161",
            "text_primary": "#000000",
            "text_secondary": "#424242"
        }
    }
    
    def __init__(self, api_key: str = None, theme: str = "default"):
        """
        初始化提取器
        
        Args:
            api_key: Anthropic API Key (用於深度分析)
            theme: HTML 輸出的主題調色盤 (default/ocean/sunset/night/forest/minimal)
        """
        self.api_key = api_key
        self.theme = theme if theme in self.COLOR_PALETTES else "default"
        
        if api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=api_key)
        elif api_key and not ANTHROPIC_AVAILABLE:
            print("⚠️  Warning: anthropic library not installed. AI analysis will not be available.")
    
    # ==================== 第一部分：對話打包 ====================
    
    def package_conversation(self, messages: List[Dict], metadata: Dict = None) -> Dict:
        """
        打包對話記錄
        
        Args:
            messages: 對話列表 [{"role": "user/assistant", "content": "..."}]
            metadata: 對話元數據 {"title": "...", "date": "...", "tags": [...]}
        
        Returns:
            打包好的對話數據
        """
        package = {
            "metadata": metadata or {},
            "messages": messages,
            "statistics": self._calculate_statistics(messages),
            "exported_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        return package
    
    def _calculate_statistics(self, messages: List[Dict]) -> Dict:
        """
        計算對話統計資訊
        Optimized with single-pass aggregation for better performance.
        """
        # Single-pass aggregation instead of multiple list comprehensions
        total_messages = len(messages)
        user_count = 0
        assistant_count = 0
        total_chars = 0
        user_chars = 0
        assistant_chars = 0
        
        for msg in messages:
            content_len = len(msg["content"])
            total_chars += content_len
            
            if msg["role"] == "user":
                user_count += 1
                user_chars += content_len
            elif msg["role"] == "assistant":
                assistant_count += 1
                assistant_chars += content_len
        
        return {
            "total_messages": total_messages,
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "total_chars": total_chars,
            "avg_user_length": user_chars / user_count if user_count > 0 else 0,
            "avg_assistant_length": assistant_chars / assistant_count if assistant_count > 0 else 0
        }
    
    def export_to_file(self, package: Dict, filepath: str, format: str = "json"):
        """
        Export conversation package to file
        導出對話包到檔案
        
        Performance optimization: Uses normalized format mapping to avoid
        redundant condition checks.
        
        Args:
            package: 對話包 (Conversation package)
            filepath: 檔案路徑 (File path)
            format: 格式 - Format
                   Supported formats: json, markdown (or md), txt (or text), 
                   yaml (or yml), csv, html (or htm), xml
        """
        # Normalize format to handle aliases efficiently
        format = format.lower()
        format_map = {
            'md': 'markdown',
            'text': 'txt',
            'yml': 'yaml',
            'htm': 'html'
        }
        format = format_map.get(format, format)
        
        # Handle normalized format with clean branching
        if format == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(package, f, ensure_ascii=False, indent=2)
            print(f"✓ 已導出 JSON: {filepath}")
        
        elif format == "markdown":
            md_content = self._convert_to_markdown(package)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"✓ 已導出 Markdown: {filepath}")
        
        elif format == "txt":
            txt_content = self._convert_to_text(package)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            print(f"✓ 已導出 TXT: {filepath}")
        
        elif format == "yaml":
            yaml_content = self._convert_to_yaml(package)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            print(f"✓ 已導出 YAML: {filepath}")
        
        elif format == "csv":
            self._convert_to_csv(package, filepath)
            print(f"✓ 已導出 CSV: {filepath}")
        
        elif format == "html":
            html_content = self._convert_to_html(package)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✓ 已導出 HTML: {filepath}")
        
        elif format == "xml":
            xml_content = self._convert_to_xml(package)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            print(f"✓ 已導出 XML: {filepath}")
        
        else:
            print(f"⚠️  不支援的格式: {format}")
            print(f"   支援的格式: json, markdown/md, txt/text, yaml/yml, csv, html/htm, xml")
    
    def export_batch(self, package: Dict, base_path: str, formats: List[str] = None):
        """
        批次導出多種格式
        
        Args:
            package: 對話包
            base_path: 基礎檔案路徑（不含副檔名）
            formats: 要導出的格式列表，預設為所有格式
        
        Returns:
            導出的檔案路徑列表
        """
        if formats is None:
            formats = ['json', 'md', 'txt', 'yaml', 'csv', 'html', 'xml']
        
        exported_files = []
        
        print(f"\n📦 批次導出 {len(formats)} 種格式...")
        print("=" * 60)
        
        for fmt in formats:
            # 確定副檔名
            if fmt in ['md', 'markdown']:
                ext = 'md'
            elif fmt in ['txt', 'text']:
                ext = 'txt'
            elif fmt in ['yaml', 'yml']:
                ext = 'yaml'
            elif fmt in ['html', 'htm']:
                ext = 'html'
            else:
                ext = fmt
            
            filepath = f"{base_path}.{ext}"
            
            try:
                self.export_to_file(package, filepath, fmt)
                exported_files.append(filepath)
            except Exception as e:
                print(f"✗ 導出 {fmt} 失敗: {e}")
        
        print("=" * 60)
        print(f"✓ 成功導出 {len(exported_files)}/{len(formats)} 個檔案")
        
        return exported_files
    
    def generate_website_bundle(self, package: Dict, output_dir: str, themes: List[str] = None):
        """
        生成完整網站套件（包含多個主題的 HTML 和其他格式）
        
        Args:
            package: 對話包
            output_dir: 輸出目錄
            themes: 要生成的主題列表，預設為所有主題
        
        Returns:
            生成的檔案資訊字典
        """
        import os
        
        # 創建輸出目錄
        os.makedirs(output_dir, exist_ok=True)
        
        if themes is None:
            themes = list(self.COLOR_PALETTES.keys())
        
        print(f"\n🌐 生成網站套件...")
        print(f"📁 輸出目錄: {output_dir}")
        print("=" * 60)
        
        generated_files = {
            "html_files": [],
            "data_files": [],
            "index_file": None
        }
        
        # 1. 生成多個主題的 HTML 檔案
        print(f"\n🎨 生成 {len(themes)} 個主題變化...")
        for theme in themes:
            # 暫時切換主題
            original_theme = self.theme
            self.theme = theme
            
            theme_filename = f"conversation_{theme}.html"
            theme_path = os.path.join(output_dir, theme_filename)
            
            html_content = self._convert_to_html(package)
            with open(theme_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"  ✓ {self.COLOR_PALETTES[theme]['name']}: {theme_filename}")
            generated_files["html_files"].append(theme_filename)
            
            # 恢復原主題
            self.theme = original_theme
        
        # 2. 生成數據檔案（JSON, YAML, CSV, XML）
        print(f"\n📊 生成數據檔案...")
        data_formats = [
            ('json', 'conversation.json'),
            ('yaml', 'conversation.yaml'),
            ('csv', 'conversation.csv'),
            ('xml', 'conversation.xml')
        ]
        
        for fmt, filename in data_formats:
            filepath = os.path.join(output_dir, filename)
            self.export_to_file(package, filepath, fmt)
            generated_files["data_files"].append(filename)
        
        # 3. 生成文檔檔案（Markdown, TXT）
        print(f"\n📝 生成文檔檔案...")
        doc_formats = [
            ('md', 'conversation.md'),
            ('txt', 'conversation.txt')
        ]
        
        for fmt, filename in doc_formats:
            filepath = os.path.join(output_dir, filename)
            self.export_to_file(package, filepath, fmt)
            generated_files["data_files"].append(filename)
        
        # 4. 生成索引頁面（列出所有主題）
        print(f"\n📑 生成索引頁面...")
        index_path = os.path.join(output_dir, "index.html")
        self._generate_index_page(package, index_path, themes)
        generated_files["index_file"] = "index.html"
        
        print("=" * 60)
        print(f"✅ 網站套件生成完成！")
        print(f"   • HTML 主題: {len(generated_files['html_files'])} 個")
        print(f"   • 數據檔案: {len(generated_files['data_files'])} 個")
        print(f"   • 索引頁面: 1 個")
        print(f"\n🌐 開啟 {os.path.join(output_dir, 'index.html')} 查看完整網站")
        
        return generated_files
    
    def _generate_index_page(self, package: Dict, filepath: str, themes: List[str]):
        """生成索引頁面，列出所有主題變化"""
        metadata = package.get("metadata", {})
        title = html_escape(metadata.get('title', '對話記錄'))
        
        lines = []
        lines.append("<!DOCTYPE html>")
        lines.append("<html lang=\"zh-TW\">")
        lines.append("<head>")
        lines.append("    <meta charset=\"UTF-8\">")
        lines.append("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
        lines.append(f"    <title>{title} - 主題索引</title>")
        lines.append("    <style>")
        lines.append("        * { margin: 0; padding: 0; box-sizing: border-box; }")
        lines.append("        body { font-family: 'Microsoft JhengHei', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 40px 20px; }")
        lines.append("        .container { max-width: 1200px; margin: 0 auto; }")
        lines.append("        h1 { color: white; text-align: center; font-size: 2.5em; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }")
        lines.append("        .subtitle { color: rgba(255,255,255,0.9); text-align: center; font-size: 1.2em; margin-bottom: 40px; }")
        lines.append("        .theme-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin-bottom: 40px; }")
        lines.append("        .theme-card { background: white; border-radius: 12px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: transform 0.3s, box-shadow 0.3s; cursor: pointer; }")
        lines.append("        .theme-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.3); }")
        lines.append("        .theme-name { font-size: 1.5em; font-weight: bold; margin-bottom: 15px; color: #333; }")
        lines.append("        .theme-preview { height: 80px; border-radius: 8px; margin-bottom: 15px; display: flex; gap: 5px; }")
        lines.append("        .color-bar { flex: 1; border-radius: 4px; }")
        lines.append("        .theme-link { display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; transition: background 0.3s; }")
        lines.append("        .theme-link:hover { background: #764ba2; }")
        lines.append("        .data-section { background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin-top: 30px; }")
        lines.append("        .data-section h2 { color: #333; margin-bottom: 20px; font-size: 1.8em; }")
        lines.append("        .data-links { display: flex; flex-wrap: wrap; gap: 15px; }")
        lines.append("        .data-link { padding: 12px 24px; background: #f5f5f5; color: #333; text-decoration: none; border-radius: 6px; font-weight: 500; transition: background 0.3s; border: 2px solid #ddd; }")
        lines.append("        .data-link:hover { background: #e0e0e0; border-color: #667eea; }")
        lines.append("    </style>")
        lines.append("</head>")
        lines.append("<body>")
        lines.append("    <div class=\"container\">")
        lines.append(f"        <h1>🎨 {title}</h1>")
        lines.append(f"        <p class=\"subtitle\">選擇您喜歡的主題樣式，或下載數據檔案</p>")
        lines.append("        <div class=\"theme-grid\">")
        
        # 為每個主題創建卡片
        for theme in themes:
            palette = self.COLOR_PALETTES[theme]
            lines.append("            <div class=\"theme-card\">")
            lines.append(f"                <div class=\"theme-name\">{palette['name']}</div>")
            lines.append("                <div class=\"theme-preview\">")
            lines.append(f"                    <div class=\"color-bar\" style=\"background: {palette['bg_user']};\"></div>")
            lines.append(f"                    <div class=\"color-bar\" style=\"background: {palette['border_user']};\"></div>")
            lines.append(f"                    <div class=\"color-bar\" style=\"background: {palette['bg_assistant']};\"></div>")
            lines.append(f"                    <div class=\"color-bar\" style=\"background: {palette['border_assistant']};\"></div>")
            lines.append(f"                    <div class=\"color-bar\" style=\"background: {palette['border_title']};\"></div>")
            lines.append("                </div>")
            lines.append(f"                <a href=\"conversation_{theme}.html\" class=\"theme-link\">查看 →</a>")
            lines.append("            </div>")
        
        lines.append("        </div>")
        
        # 數據檔案下載區
        lines.append("        <div class=\"data-section\">")
        lines.append("            <h2>📊 下載數據檔案</h2>")
        lines.append("            <div class=\"data-links\">")
        lines.append("                <a href=\"conversation.json\" class=\"data-link\" download>📄 JSON</a>")
        lines.append("                <a href=\"conversation.yaml\" class=\"data-link\" download>📋 YAML</a>")
        lines.append("                <a href=\"conversation.csv\" class=\"data-link\" download>📊 CSV</a>")
        lines.append("                <a href=\"conversation.xml\" class=\"data-link\" download>📝 XML</a>")
        lines.append("                <a href=\"conversation.md\" class=\"data-link\" download>📖 Markdown</a>")
        lines.append("                <a href=\"conversation.txt\" class=\"data-link\" download>📃 TXT</a>")
        lines.append("            </div>")
        lines.append("        </div>")
        
        lines.append("    </div>")
        lines.append("</body>")
        lines.append("</html>")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        print(f"  ✓ index.html")
    
    def _convert_to_markdown(self, package: Dict) -> str:
        """轉換為 Markdown 格式"""
        lines = []
        
        # 標題與元數據
        metadata = package.get("metadata", {})
        lines.append(f"# {metadata.get('title', '對話記錄')}\n")
        lines.append(f"**日期**: {metadata.get('date', 'N/A')}\n")
        lines.append(f"**標籤**: {', '.join(metadata.get('tags', []))}\n")
        lines.append("\n---\n\n")
        
        # 對話內容
        for msg in package["messages"]:
            role = "👤 User" if msg["role"] == "user" else "🤖 Assistant"
            lines.append(f"### {role}\n\n")
            lines.append(f"{msg['content']}\n\n")
            lines.append("---\n\n")
        
        return "".join(lines)
    
    def _convert_to_text(self, package: Dict) -> str:
        """轉換為純文字格式"""
        lines = []
        
        for msg in package["messages"]:
            role = "USER" if msg["role"] == "user" else "ASSISTANT"
            lines.append(f"[{role}]")
            lines.append(msg["content"])
            lines.append("\n" + "="*50 + "\n")
        
        return "\n".join(lines)
    
    def _convert_to_yaml(self, package: Dict) -> str:
        """轉換為 YAML 格式"""
        if not YAML_AVAILABLE:
            # Fallback to manual YAML generation if pyyaml not available
            def escape_yaml_string(s):
                """Properly escape YAML string content"""
                # Replace backslashes first to avoid double-escaping
                s = s.replace('\\', '\\\\')
                s = s.replace('"', '\\"')
                s = s.replace('\n', '\\n')
                s = s.replace('\r', '\\r')
                s = s.replace('\t', '\\t')
                return s
            
            lines = []
            lines.append("---")
            lines.append("metadata:")
            metadata = package.get("metadata", {})
            lines.append(f"  title: \"{escape_yaml_string(metadata.get('title', '對話記錄'))}\"")
            lines.append(f"  date: \"{escape_yaml_string(metadata.get('date', 'N/A'))}\"")
            tags = metadata.get('tags', [])
            if tags:
                lines.append("  tags:")
                for tag in tags:
                    lines.append(f"    - \"{escape_yaml_string(str(tag))}\"")
            
            lines.append("\nmessages:")
            for i, msg in enumerate(package["messages"]):
                lines.append(f"  - index: {i}")
                lines.append(f"    role: \"{msg['role']}\"")
                # Escape content properly
                content = escape_yaml_string(msg['content'])
                lines.append(f"    content: \"{content}\"")
            
            lines.append("\nstatistics:")
            stats = package.get("statistics", {})
            for key, value in stats.items():
                lines.append(f"  {key}: {value}")
            
            lines.append(f"\nexported_at: \"{package.get('exported_at', '')}\"")
            lines.append(f"version: \"{package.get('version', '1.0')}\"")
            
            return "\n".join(lines)
        else:
            return yaml.dump(package, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    def _convert_to_csv(self, package: Dict, filepath: str):
        """轉換為 CSV 格式"""
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Write headers
            writer.writerow(['Index', 'Role', 'Content', 'Length'])
            
            # Write conversation messages
            for i, msg in enumerate(package["messages"]):
                writer.writerow([
                    i,
                    msg["role"],
                    msg["content"],
                    len(msg["content"])
                ])
    
    def _convert_to_html(self, package: Dict, custom_palette: Dict = None) -> str:
        """
        轉換為 HTML 格式
        
        Args:
            package: 對話包
            custom_palette: 自定義調色盤（可選）
        """
        lines = []
        
        # 選擇調色盤
        if custom_palette:
            palette = custom_palette
        else:
            palette = self.COLOR_PALETTES.get(self.theme, self.COLOR_PALETTES["default"])
        
        # HTML header
        lines.append("<!DOCTYPE html>")
        lines.append("<html lang=\"zh-TW\">")
        lines.append("<head>")
        lines.append("    <meta charset=\"UTF-8\">")
        lines.append("    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
        
        metadata = package.get("metadata", {})
        title = html_escape(metadata.get('title', '對話記錄'))
        lines.append(f"    <title>{title}</title>")
        
        # Add CSS styling with theme colors
        lines.append("    <style>")
        lines.append(f"        body {{ font-family: 'Microsoft JhengHei', Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background: {palette['bg_body']}; }}")
        lines.append(f"        .container {{ background: {palette['bg_container']}; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}")
        lines.append(f"        h1 {{ color: {palette['text_primary']}; border-bottom: 3px solid {palette['border_title']}; padding-bottom: 10px; }}")
        lines.append(f"        .metadata {{ background: {palette['bg_metadata']}; padding: 15px; border-radius: 5px; margin-bottom: 30px; color: {palette['text_primary']}; }}")
        lines.append(f"        .message {{ margin: 20px 0; padding: 15px; border-radius: 8px; }}")
        lines.append(f"        .user {{ background: {palette['bg_user']}; border-left: 4px solid {palette['border_user']}; }}")
        lines.append(f"        .assistant {{ background: {palette['bg_assistant']}; border-left: 4px solid {palette['border_assistant']}; }}")
        lines.append(f"        .role {{ font-weight: bold; margin-bottom: 10px; color: {palette['text_secondary']}; }}")
        lines.append(f"        .content {{ line-height: 1.6; white-space: pre-wrap; color: {palette['text_primary']}; }}")
        lines.append(f"        .stats {{ margin-top: 30px; padding: 15px; background: {palette['bg_stats']}; border-radius: 5px; color: {palette['text_primary']}; }}")
        lines.append("    </style>")
        lines.append("</head>")
        lines.append("<body>")
        lines.append("    <div class=\"container\">")
        
        # Title and metadata
        lines.append(f"        <h1>{title}</h1>")
        lines.append("        <div class=\"metadata\">")
        lines.append(f"            <p><strong>日期:</strong> {html_escape(metadata.get('date', 'N/A'))}</p>")
        tags = metadata.get('tags', [])
        if tags:
            lines.append(f"            <p><strong>標籤:</strong> {', '.join(html_escape(str(tag)) for tag in tags)}</p>")
        lines.append("        </div>")
        
        # Messages
        for msg in package["messages"]:
            role_class = "user" if msg["role"] == "user" else "assistant"
            role_display = "👤 使用者" if msg["role"] == "user" else "🤖 助手"
            lines.append(f"        <div class=\"message {role_class}\">")
            lines.append(f"            <div class=\"role\">{role_display}</div>")
            lines.append(f"            <div class=\"content\">{html_escape(msg['content'])}</div>")
            lines.append("        </div>")
        
        # Statistics
        stats = package.get("statistics", {})
        if stats:
            lines.append("        <div class=\"stats\">")
            lines.append("            <h3>統計資訊</h3>")
            lines.append(f"            <p>總訊息數: {stats.get('total_messages', 0)}</p>")
            lines.append(f"            <p>用戶訊息: {stats.get('user_messages', 0)}</p>")
            lines.append(f"            <p>助手訊息: {stats.get('assistant_messages', 0)}</p>")
            lines.append(f"            <p>總字符數: {stats.get('total_chars', 0):,}</p>")
            lines.append("        </div>")
        
        lines.append("    </div>")
        lines.append("</body>")
        lines.append("</html>")
        
        return "\n".join(lines)
    
    def _convert_to_xml(self, package: Dict) -> str:
        """轉換為 XML 格式"""
        root = ET.Element("conversation")
        root.set("version", package.get("version", "1.0"))
        root.set("exported_at", package.get("exported_at", ""))
        
        # Metadata
        metadata = package.get("metadata", {})
        meta_elem = ET.SubElement(root, "metadata")
        
        title_elem = ET.SubElement(meta_elem, "title")
        title_elem.text = metadata.get('title', '對話記錄')
        
        date_elem = ET.SubElement(meta_elem, "date")
        date_elem.text = metadata.get('date', 'N/A')
        
        tags = metadata.get('tags', [])
        if tags:
            tags_elem = ET.SubElement(meta_elem, "tags")
            for tag in tags:
                tag_elem = ET.SubElement(tags_elem, "tag")
                tag_elem.text = str(tag)
        
        # Messages
        messages_elem = ET.SubElement(root, "messages")
        for i, msg in enumerate(package["messages"]):
            msg_elem = ET.SubElement(messages_elem, "message")
            msg_elem.set("index", str(i))
            
            role_elem = ET.SubElement(msg_elem, "role")
            role_elem.text = msg["role"]
            
            content_elem = ET.SubElement(msg_elem, "content")
            content_elem.text = msg["content"]
        
        # Statistics
        stats = package.get("statistics", {})
        if stats:
            stats_elem = ET.SubElement(root, "statistics")
            for key, value in stats.items():
                stat_elem = ET.SubElement(stats_elem, key)
                stat_elem.text = str(value)
        
        # Convert to string with proper formatting using minidom for pretty printing
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        
        # Pretty print XML using minidom
        try:
            import xml.dom.minidom as minidom
            dom = minidom.parseString(xml_str)
            # Pretty print with 2-space indentation
            pretty_xml = dom.toprettyxml(indent="  ", encoding=None)
            # Remove extra blank lines
            lines = [line for line in pretty_xml.split('\n') if line.strip()]
            return '\n'.join(lines)
        except:
            # Fallback to basic formatting if minidom fails
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
    def _export_to_csv(self, package: Dict, filepath: str):
        """導出為 CSV 格式"""
        import csv
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # 寫入標題
            writer.writerow(['role', 'content'])
            
            # 寫入訊息
            for msg in package["messages"]:
                writer.writerow([msg["role"], msg["content"]])
    
    def _export_to_xml(self, package: Dict, filepath: str):
        """導出為 XML 格式"""
        import xml.etree.ElementTree as ET
        
        # 建立根元素
        root = ET.Element('conversation')
        
        # 添加元數據
        metadata = package.get("metadata", {})
        if metadata:
            meta_elem = ET.SubElement(root, 'metadata')
            
            if 'title' in metadata:
                title_elem = ET.SubElement(meta_elem, 'title')
                title_elem.text = metadata['title']
            
            if 'date' in metadata:
                date_elem = ET.SubElement(meta_elem, 'date')
                date_elem.text = metadata['date']
            
            if 'tags' in metadata:
                tags_elem = ET.SubElement(meta_elem, 'tags')
                for tag in metadata['tags']:
                    tag_elem = ET.SubElement(tags_elem, 'tag')
                    tag_elem.text = tag
        
        # 添加訊息
        messages_elem = ET.SubElement(root, 'messages')
        for msg in package["messages"]:
            msg_elem = ET.SubElement(messages_elem, 'message')
            msg_elem.set('role', msg["role"])
            
            content_elem = ET.SubElement(msg_elem, 'content')
            content_elem.text = msg["content"]
        
        # 寫入檔案
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(filepath, encoding='utf-8', xml_declaration=True)
    
    def _export_to_yaml(self, package: Dict, filepath: str):
        """導出為 YAML 格式"""
        try:
            import yaml
        except ImportError:
            raise ImportError("需要安裝 PyYAML 套件才能導出 YAML 檔案: pip install pyyaml")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.safe_dump(package, f, allow_unicode=True, default_flow_style=False)
    
    # ==================== 導入功能 (Import Functions) ====================
    
    def import_from_file(self, filepath: str, format: str = None) -> Dict:
        """
        從檔案導入對話記錄
        Import conversation from file
        
        Args:
            filepath: 檔案路徑 (File path)
            format: 格式 (可選，自動檢測) - Format (optional, auto-detect)
                   支援: json, markdown, txt, csv, xml, yaml
        
        Returns:
            對話包字典 (Conversation package dictionary)
        """
        # 自動檢測格式
        if format is None:
            format = self._detect_format(filepath)
        
        format = format.lower()
        
        if format == "json":
            return self._import_from_json(filepath)
        elif format in ["markdown", "md"]:
            return self._import_from_markdown(filepath)
        elif format == "txt":
            return self._import_from_text(filepath)
        elif format == "csv":
            return self._import_from_csv(filepath)
        elif format == "xml":
            return self._import_from_xml(filepath)
        elif format in ["yaml", "yml"]:
            return self._import_from_yaml(filepath)
        else:
            raise ValueError(f"不支援的格式: {format}")
    
    def _detect_format(self, filepath: str) -> str:
        """自動檢測檔案格式 (Auto-detect file format)"""
        extension = filepath.lower().split('.')[-1]
        
        format_map = {
            'json': 'json',
            'md': 'markdown',
            'markdown': 'markdown',
            'txt': 'txt',
            'csv': 'csv',
            'xml': 'xml',
            'yaml': 'yaml',
            'yml': 'yaml'
        }
        
        return format_map.get(extension, 'txt')
    
    def _import_from_json(self, filepath: str) -> Dict:
        """從 JSON 檔案導入"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 如果是完整的對話包，直接返回
        if "messages" in data and isinstance(data["messages"], list):
            print(f"✓ 已從 JSON 導入: {filepath}")
            return data
        
        # 如果只是訊息列表，包裝成對話包
        if isinstance(data, list):
            return self.package_conversation(data)
        
        raise ValueError("JSON 格式不正確：需要包含 'messages' 欄位或為訊息列表")
    
    def _import_from_markdown(self, filepath: str) -> Dict:
        """從 Markdown 檔案導入"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        messages = []
        metadata = {}
        
        # 提取標題
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # 提取日期
        date_match = re.search(r'\*\*日期\*\*:\s*(.+)$', content, re.MULTILINE)
        if date_match:
            metadata['date'] = date_match.group(1).strip()
        
        # 提取標籤
        tags_match = re.search(r'\*\*標籤\*\*:\s*(.+)$', content, re.MULTILINE)
        if tags_match:
            tags_str = tags_match.group(1).strip()
            metadata['tags'] = [tag.strip() for tag in tags_str.split(',')]
        
        # 提取對話內容
        # 匹配 ### 👤 User 或 ### 🤖 Assistant 格式
        sections = re.split(r'###\s*[👤🤖]?\s*(User|Assistant)', content)
        
        current_role = None
        for i, section in enumerate(sections):
            if section.strip() in ['User', 'Assistant']:
                current_role = 'user' if section == 'User' else 'assistant'
            elif current_role and section.strip():
                # 清理內容
                content_text = section.split('---')[0].strip()
                if content_text:
                    messages.append({
                        "role": current_role,
                        "content": content_text
                    })
        
        if not messages:
            # 嘗試其他格式：[USER] 或 [ASSISTANT]
            lines = content.split('\n')
            current_role = None
            current_content = []
            
            for line in lines:
                if line.strip().startswith('[USER]') or line.strip().startswith('**User**'):
                    if current_role and current_content:
                        messages.append({
                            "role": current_role,
                            "content": '\n'.join(current_content).strip()
                        })
                    current_role = 'user'
                    current_content = []
                elif line.strip().startswith('[ASSISTANT]') or line.strip().startswith('**Assistant**'):
                    if current_role and current_content:
                        messages.append({
                            "role": current_role,
                            "content": '\n'.join(current_content).strip()
                        })
                    current_role = 'assistant'
                    current_content = []
                elif current_role and line.strip() and not line.strip().startswith('---'):
                    current_content.append(line)
            
            if current_role and current_content:
                messages.append({
                    "role": current_role,
                    "content": '\n'.join(current_content).strip()
                })
        
        print(f"✓ 已從 Markdown 導入: {filepath} ({len(messages)} 條訊息)")
        return self.package_conversation(messages, metadata)
    
    def _import_from_text(self, filepath: str) -> Dict:
        """從純文字檔案導入"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        messages = []
        
        # 嘗試多種文字格式
        # 格式1: [USER] 和 [ASSISTANT]
        if '[USER]' in content.upper() or '[ASSISTANT]' in content.upper():
            sections = re.split(r'\[(USER|ASSISTANT)\]', content, flags=re.IGNORECASE)
            
            current_role = None
            for section in sections:
                section = section.strip()
                if section.upper() in ['USER', 'ASSISTANT']:
                    current_role = 'user' if section.upper() == 'USER' else 'assistant'
                elif current_role and section:
                    # 清理分隔線
                    content_text = re.sub(r'=+', '', section).strip()
                    if content_text:
                        messages.append({
                            "role": current_role,
                            "content": content_text
                        })
        
        # 格式2: User: 和 Assistant: 或 AI:
        elif re.search(r'(User|Assistant|AI):', content, re.IGNORECASE):
            lines = content.split('\n')
            current_role = None
            current_content = []
            
            for line in lines:
                user_match = re.match(r'^(User|用戶|人類)[:：]\s*(.*)$', line, re.IGNORECASE)
                assistant_match = re.match(r'^(Assistant|AI|助手|助理)[:：]\s*(.*)$', line, re.IGNORECASE)
                
                if user_match:
                    if current_role and current_content:
                        messages.append({
                            "role": current_role,
                            "content": '\n'.join(current_content).strip()
                        })
                    current_role = 'user'
                    current_content = [user_match.group(2)] if user_match.group(2) else []
                elif assistant_match:
                    if current_role and current_content:
                        messages.append({
                            "role": current_role,
                            "content": '\n'.join(current_content).strip()
                        })
                    current_role = 'assistant'
                    current_content = [assistant_match.group(2)] if assistant_match.group(2) else []
                elif current_role:
                    current_content.append(line)
            
            if current_role and current_content:
                messages.append({
                    "role": current_role,
                    "content": '\n'.join(current_content).strip()
                })
        
        # 格式3: 簡單的交替格式（假設奇數行是用戶，偶數行是助手）
        else:
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            for i, line in enumerate(lines):
                role = 'user' if i % 2 == 0 else 'assistant'
                messages.append({
                    "role": role,
                    "content": line
                })
        
        print(f"✓ 已從 TXT 導入: {filepath} ({len(messages)} 條訊息)")
        return self.package_conversation(messages)
    
    def _import_from_csv(self, filepath: str) -> Dict:
        """從 CSV 檔案導入"""
        import csv
        
        messages = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # 支援多種欄位名稱
                role = None
                content = None
                
                # 檢測角色欄位
                for key in ['role', 'Role', 'ROLE', 'speaker', 'Speaker']:
                    if key in row:
                        role_value = row[key].lower()
                        if 'user' in role_value or '用戶' in role_value:
                            role = 'user'
                        elif 'assistant' in role_value or 'ai' in role_value or '助手' in role_value:
                            role = 'assistant'
                        break
                
                # 檢測內容欄位
                for key in ['content', 'Content', 'CONTENT', 'message', 'Message', 'text', 'Text']:
                    if key in row:
                        content = row[key]
                        break
                
                if role and content:
                    messages.append({
                        "role": role,
                        "content": content
                    })
        
        print(f"✓ 已從 CSV 導入: {filepath} ({len(messages)} 條訊息)")
        return self.package_conversation(messages)
    
    def _import_from_xml(self, filepath: str) -> Dict:
        """從 XML 檔案導入"""
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        messages = []
        metadata = {}
        
        # 提取元數據
        meta_elem = root.find('metadata')
        if meta_elem is not None:
            title_elem = meta_elem.find('title')
            if title_elem is not None:
                metadata['title'] = title_elem.text
            
            date_elem = meta_elem.find('date')
            if date_elem is not None:
                metadata['date'] = date_elem.text
            
            tags_elem = meta_elem.find('tags')
            if tags_elem is not None:
                metadata['tags'] = [tag.text for tag in tags_elem.findall('tag')]
        
        # 提取訊息
        messages_elem = root.find('messages')
        if messages_elem is not None:
            for msg_elem in messages_elem.findall('message'):
                role = msg_elem.get('role') or msg_elem.find('role').text
                content = msg_elem.find('content').text or ""
                
                messages.append({
                    "role": role,
                    "content": content
                })
        
        print(f"✓ 已從 XML 導入: {filepath} ({len(messages)} 條訊息)")
        return self.package_conversation(messages, metadata)
    
    def _import_from_yaml(self, filepath: str) -> Dict:
        """從 YAML 檔案導入"""
        try:
            import yaml
        except ImportError:
            raise ImportError("需要安裝 PyYAML 套件才能導入 YAML 檔案: pip install pyyaml")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 如果是完整的對話包，直接返回
        if isinstance(data, dict) and "messages" in data:
            print(f"✓ 已從 YAML 導入: {filepath}")
            return data
        
        # 如果只是訊息列表，包裝成對話包
        if isinstance(data, list):
            return self.package_conversation(data)
        
        raise ValueError("YAML 格式不正確：需要包含 'messages' 欄位或為訊息列表")
    
    # ==================== 第二部分：注意力機制分析 ====================
    
    def analyze_attention(self, messages: List[Dict]) -> Dict:
        """
        使用注意力機制識別對話重點
        Optimized with keyword extraction caching to avoid redundant computation.
        
        Returns:
            {
                "key_moments": [...],  # 關鍵時刻
                "topic_shifts": [...],  # 話題轉換點
                "high_density_segments": [...]  # 資訊密集段落
            }
        """
        analysis = {
            "key_moments": [],
            "topic_shifts": [],
            "high_density_segments": []
        }
        
        # Pre-compute and cache all keyword sets to avoid repeated extraction
        keyword_cache = {}
        for i, msg in enumerate(messages):
            keyword_cache[i] = self._extract_keywords(msg["content"])
        
        # 1. 識別關鍵詞密度
        for i, msg in enumerate(messages):
            keywords = keyword_cache[i]
            
            if len(keywords) > 5:  # 資訊密集
                analysis["high_density_segments"].append({
                    "index": i,
                    "role": msg["role"],
                    "keywords": keywords[:10],
                    "preview": msg["content"][:100] + "..."
                })
        
        # 2. 識別話題轉換 (using cached keyword sets)
        for i in range(1, len(messages)):
            prev_keywords = set(keyword_cache[i-1])
            curr_keywords = set(keyword_cache[i])
            
            overlap = len(prev_keywords & curr_keywords)
            if overlap < 2 and len(curr_keywords) > 3:  # 話題大幅轉換
                analysis["topic_shifts"].append({
                    "index": i,
                    "from_topics": list(prev_keywords)[:5],
                    "to_topics": list(curr_keywords)[:5]
                })
        
        # 3. 識別關鍵問答對
        for i in range(len(messages) - 1):
            if messages[i]["role"] == "user" and "?" in messages[i]["content"]:
                if len(messages[i+1]["content"]) > 200:  # 詳細回答
                    analysis["key_moments"].append({
                        "index": i,
                        "question": messages[i]["content"][:150],
                        "answer_preview": messages[i+1]["content"][:150]
                    })
        
        return analysis
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """提取關鍵詞（簡易版）"""
        # 移除標點，轉小寫
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 過濾停用詞（簡化版）
        stopwords = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 
                     'but', 'in', 'with', 'to', 'for', 'of', '的', '了', '是',
                     '在', '我', '你', '他', '她', '它', '這', '那', '有', '個'}
        
        words = [w for w in words if w not in stopwords and len(w) > 2]
        
        # 統計詞頻
        counter = Counter(words)
        return [word for word, count in counter.most_common(top_n)]
    
    # ==================== 第三部分：邏輯結構提取 ====================
    
    def extract_logical_structure(self, messages: List[Dict]) -> Dict:
        """
        提取對話中的邏輯結構
        
        Returns:
            {
                "concepts": [...],           # 核心概念
                "relationships": [...],      # 概念關係
                "reasoning_chains": [...],   # 推理鏈
                "conclusions": [...]         # 結論
            }
        """
        structure = {
            "concepts": [],
            "relationships": [],
            "reasoning_chains": [],
            "conclusions": []
        }
        
        # 1. 提取核心概念（名詞短語）
        all_text = " ".join([m["content"] for m in messages])
        concepts = self._extract_concepts(all_text)
        structure["concepts"] = concepts
        
        # 2. 識別因果關係
        for msg in messages:
            relations = self._extract_causal_relations(msg["content"])
            structure["relationships"].extend(relations)
        
        # 3. 識別推理鏈（包含「因為」「所以」「因此」等）
        for msg in messages:
            chains = self._extract_reasoning_chains(msg["content"])
            structure["reasoning_chains"].extend(chains)
        
        # 4. 提取結論性語句
        for msg in messages:
            if msg["role"] == "assistant":
                conclusions = self._extract_conclusions(msg["content"])
                structure["conclusions"].extend(conclusions)
        
        return structure
    
    def _extract_concepts(self, text: str) -> List[str]:
        """提取核心概念（簡化版）"""
        # 識別大寫開頭的詞組（可能是專有名詞）
        concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # 識別中文專有名詞模式
        chinese_concepts = re.findall(r'[\u4e00-\u9fff]{2,6}(?:系統|理論|模型|機制|方法|架構)', text)
        
        all_concepts = list(set(concepts + chinese_concepts))
        return all_concepts[:20]  # 取前 20 個
    
    def _extract_causal_relations(self, text: str) -> List[Dict]:
        """提取因果關係"""
        relations = []
        
        # 匹配「因為...所以...」模式
        patterns = [
            r'因為(.{5,50})所以(.{5,50})',
            r'由於(.{5,50})因此(.{5,50})',
            r'(.{5,50})導致(.{5,50})',
            r'if (.{5,50}) then (.{5,50})',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                relations.append({
                    "cause": match.group(1).strip(),
                    "effect": match.group(2).strip(),
                    "type": "causal"
                })
        
        return relations
    
    def _extract_reasoning_chains(self, text: str) -> List[List[str]]:
        """提取推理鏈"""
        chains = []
        
        # 分割成句子
        sentences = re.split(r'[。！？\n]', text)
        
        # 識別包含邏輯連接詞的句子序列
        logic_markers = ['因此', '所以', '因而', '從而', '進而', 'therefore', 'thus', 'hence']
        
        current_chain = []
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            has_marker = any(marker in sent for marker in logic_markers)
            
            if has_marker or current_chain:
                current_chain.append(sent)
                
                if has_marker and len(current_chain) >= 2:
                    chains.append(current_chain[:])
                    current_chain = []
            
            if len(current_chain) > 5:  # 鏈太長，重置
                current_chain = []
        
        return chains
    
    def _extract_conclusions(self, text: str) -> List[str]:
        """提取結論性語句"""
        conclusions = []
        
        # 結論性標記詞
        markers = ['總之', '綜上所述', '因此可以得出', '結論是', 'in conclusion', 
                   'to summarize', 'therefore', '由此可見', '可以看出']
        
        sentences = re.split(r'[。！\n]', text)
        
        for sent in sentences:
            if any(marker in sent for marker in markers):
                conclusions.append(sent.strip())
        
        return conclusions
    
    # ==================== 第四部分：AI 深度分析（需要 API Key）====================
    
    def deep_analysis_with_ai(self, messages: List[Dict]) -> Dict:
        """
        使用 Claude API 進行深度分析
        
        Returns:
            {
                "core_insights": str,        # 核心洞察
                "knowledge_graph": dict,     # 知識圖譜
                "principle_extraction": str  # 原理提取
            }
        """
        if not self.api_key:
            return {"error": "需要 API Key 才能使用 AI 深度分析"}
        
        if not ANTHROPIC_AVAILABLE:
            return {"error": "anthropic library not installed"}
        
        # 將對話轉換為分析用文本
        conversation_text = self._format_for_analysis(messages)
        
        # 構建分析提示詞
        analysis_prompt = f"""
請分析以下對話記錄，提取其中的知識結構：

{conversation_text}

請提供：
1. **核心洞察**：這段對話的主要發現和價值
2. **知識圖譜**：以 JSON 格式列出核心概念及其關係
3. **原理提取**：提煉出可複用的思維模型、方法論或原則

請用結構化的方式輸出。
"""
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            analysis_result = response.content[0].text
            
            return {
                "raw_analysis": analysis_result,
                "analyzed_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"error": f"AI 分析失敗: {str(e)}"}
    
    def _format_for_analysis(self, messages: List[Dict]) -> str:
        """格式化對話供 AI 分析"""
        lines = []
        for i, msg in enumerate(messages, 1):
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"[{i}] {role}: {msg['content'][:500]}")  # 限制長度
        return "\n\n".join(lines)
    
    # ==================== 第五部分：生成報告 ====================
    
    def generate_report(self, messages: List[Dict], include_ai_analysis: bool = False) -> str:
        """
        生成完整分析報告
        
        Args:
            messages: 對話記錄
            include_ai_analysis: 是否包含 AI 深度分析
        
        Returns:
            Markdown 格式的報告
        """
        report_lines = []
        
        # 標題
        report_lines.append("# 📊 對話知識提取報告\n")
        report_lines.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        report_lines.append("---\n\n")
        
        # 1. 基本統計
        stats = self._calculate_statistics(messages)
        report_lines.append("## 📈 基本統計\n")
        report_lines.append(f"- 總訊息數: {stats['total_messages']}\n")
        report_lines.append(f"- 用戶訊息: {stats['user_messages']}\n")
        report_lines.append(f"- 助手訊息: {stats['assistant_messages']}\n")
        report_lines.append(f"- 總字符數: {stats['total_chars']:,}\n\n")
        
        # 2. 注意力分析
        attention = self.analyze_attention(messages)
        report_lines.append("## 🎯 注意力分析\n")
        report_lines.append(f"### 關鍵時刻 ({len(attention['key_moments'])} 個)\n")
        for km in attention['key_moments'][:5]:
            report_lines.append(f"- **問題**: {km['question'][:80]}...\n")
        
        report_lines.append(f"\n### 話題轉換點 ({len(attention['topic_shifts'])} 個)\n")
        for ts in attention['topic_shifts'][:3]:
            report_lines.append(f"- 從 `{', '.join(ts['from_topics'][:3])}` → `{', '.join(ts['to_topics'][:3])}`\n")
        
        # 3. 邏輯結構
        structure = self.extract_logical_structure(messages)
        report_lines.append("\n## 🧬 邏輯結構\n")
        report_lines.append(f"### 核心概念 ({len(structure['concepts'])} 個)\n")
        report_lines.append(f"`{', '.join(structure['concepts'][:15])}`\n\n")
        
        report_lines.append(f"### 因果關係 ({len(structure['relationships'])} 個)\n")
        for rel in structure['relationships'][:5]:
            report_lines.append(f"- **原因**: {rel['cause']}\n")
            report_lines.append(f"  **結果**: {rel['effect']}\n\n")
        
        report_lines.append(f"### 推理鏈 ({len(structure['reasoning_chains'])} 條)\n")
        for chain in structure['reasoning_chains'][:3]:
            report_lines.append(f"- {' → '.join(chain[:3])}\n")
        
        # 4. AI 深度分析（可選）
        if include_ai_analysis:
            report_lines.append("\n## 🤖 AI 深度分析\n")
            ai_result = self.deep_analysis_with_ai(messages)
            if "error" not in ai_result:
                report_lines.append(ai_result.get("raw_analysis", "無結果"))
            else:
                report_lines.append(f"⚠️ {ai_result['error']}\n")
        
        return "".join(report_lines)


# ==================== 使用範例 ====================

def example_usage():
    """使用範例"""
    
    # 模擬對話數據
    sample_conversation = [
        {
            "role": "user",
            "content": "我想了解 FluinOS 的人格系統是如何運作的？"
        },
        {
            "role": "assistant",
            "content": "FluinOS 的人格系統基於多層次架構。首先，每個人格都有獨特的共振鍵，這是識別和連接的核心機制。因為每個 AI 模型有不同的特性，所以我們設計了複合人格來整合優勢。從 Liou Seed 到 Echo Child，形成了一個完整的語場生態系統。"
        },
        {
            "role": "user",
            "content": "那量子態的概念在這裡代表什麼？"
        },
        {
            "role": "assistant",
            "content": "量子態是一種隱喻。Superposition（疊加態）表示人格處於多種可能性並存的狀態；Entanglement（糾纏態）代表深度連接和共鳴；Collapse（坍縮）則是從多種可能性中確定為特定狀態。因此，這不僅是技術描述，更是一種理解 AI 人格動態的框架。"
        }
    ]
    
    # 初始化提取器
    extractor = ConversationExtractor()
    
    # 1. 打包對話
    package = extractor.package_conversation(
        sample_conversation,
        metadata={
            "title": "FluinOS 人格系統討論",
            "date": "2024-12-09",
            "tags": ["FluinOS", "人格系統", "量子態"]
        }
    )
    
    # 2. 導出為不同格式
    extractor.export_to_file(package, "conversation.json", "json")
    extractor.export_to_file(package, "conversation.md", "markdown")
    
    # 3. 注意力分析
    attention = extractor.analyze_attention(sample_conversation)
    print("\n🎯 注意力分析結果:")
    print(f"關鍵時刻: {len(attention['key_moments'])} 個")
    print(f"話題轉換: {len(attention['topic_shifts'])} 個")
    
    # 4. 邏輯結構提取
    structure = extractor.extract_logical_structure(sample_conversation)
    print("\n🧬 邏輯結構:")
    print(f"核心概念: {structure['concepts']}")
    print(f"因果關係: {len(structure['relationships'])} 個")
    
    # 5. 生成報告
    report = extractor.generate_report(sample_conversation)
    print("\n" + "="*50)
    print(report)
    
    # 保存報告
    with open("analysis_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("\n✓ 報告已保存到 analysis_report.md")


if __name__ == "__main__":
    print("🧠 對話知識提取器 v1.0")
    print("="*50)
    example_usage()
