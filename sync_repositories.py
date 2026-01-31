#!/usr/bin/env python3
"""
Repository Sync Tool for Mrl_Zero System
Auto-sync configurations from claude-cookbooks and flowhub
Created by: MR.liou
"""

import os
import subprocess
import json
import shutil
import tempfile
from pathlib import Path
from fnmatch import fnmatch

def run_command(cmd, cwd=None):
    """執行命令並返回結果"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def sync_files_by_pattern(src_dir, dest_dir, patterns):
    """根據模式同步檔案"""
    src_path = Path(src_dir)
    dest_path = Path(dest_dir)
    synced_count = 0
    
    for pattern in patterns:
        for file_path in src_path.rglob(pattern):
            if file_path.is_file():
                # 計算相對路徑
                rel_path = file_path.relative_to(src_path)
                dest_file = dest_path / rel_path
                
                # 創建目標目錄
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 複製檔案
                shutil.copy2(file_path, dest_file)
                synced_count += 1
                print(f"   ✓ {rel_path}")
    
    return synced_count

def sync_repositories():
    """同步外部倉庫到本地系統"""
    
    # 定義同步配置
    sync_config = {
        "anthropics/claude-cookbooks": {
            "url": "https://github.com/anthropics/anthropic-cookbook.git",
            "branch": "main",
            "target_dir": "particle_core/examples/claude_recipes/",
            "patterns": ["*.ipynb", "*.py", "*.md"],
            "description": "AI學習與示例資源"
        },
        "dofaromg/flowhub": {
            "url": "https://github.com/dofaromg/flowhub.git",
            "branch": "master",
            "target_dir": "cluster/configs/google_templates/", 
            "patterns": ["*.yaml", "*.yml", "*.json", "*.md"],
            "description": "Google標準配置模板"
        }
    }
    
    print("🌱 Mrl_Zero Repository Sync Tool")
    print("=" * 50)
    
    success_count = 0
    total_count = len(sync_config)
    
    for repo, config in sync_config.items():
        print(f"\n📥 同步 {repo}...")
        print(f"   目標: {config['target_dir']}")
        print(f"   用途: {config['description']}")
        
        # 創建目標目錄
        os.makedirs(config['target_dir'], exist_ok=True)
        
        # 使用臨時目錄進行克隆
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 克隆倉庫
            print(f"   🔄 克隆倉庫...")
            success, output = run_command([
                'git', 'clone',
                '--depth', '1',
                '--branch', config['branch'],
                config['url'],
                str(temp_path)
            ])
            
            if not success:
                print(f"   ❌ 克隆失敗: {output}")
                continue
            
            # 同步匹配的檔案
            print(f"   📋 同步檔案 (patterns: {', '.join(config['patterns'])})")
            synced = sync_files_by_pattern(
                temp_path, 
                config['target_dir'],
                config['patterns']
            )
            
            if synced > 0:
                print(f"   ✅ 成功同步 {synced} 個檔案")
                success_count += 1
            else:
                print(f"   ⚠️  沒有找到匹配的檔案")
    
    print("\n" + "=" * 50)
    print(f"📊 同步摘要: {success_count}/{total_count} 個倉庫成功")
    print("✅ 同步完成")
    print("🫶 怎麼過去，就怎麼回來")
    
    return success_count == total_count

if __name__ == "__main__":
    import sys
    success = sync_repositories()
    sys.exit(0 if success else 1)