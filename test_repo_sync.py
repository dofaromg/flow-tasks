#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for External Repository Sync System
外部倉庫同步系統測試腳本
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd):
    """Run command and return success status"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def test_script_exists():
    """Test if sync script exists"""
    print("\n📋 測試 1: 檢查同步腳本是否存在 / Test 1: Check if sync script exists")
    script_path = Path("scripts/sync_external_repos.py")
    
    if script_path.exists() and os.access(script_path, os.X_OK):
        print("✅ 同步腳本存在且可執行 / Sync script exists and is executable")
        return True
    else:
        print("❌ 同步腳本不存在或無執行權限 / Sync script not found or not executable")
        return False

def test_config_exists():
    """Test if config file exists"""
    print("\n📋 測試 2: 檢查配置檔案 / Test 2: Check config file")
    config_path = Path("repos_sync.yaml")
    example_config_path = Path("repos_sync.example.yaml")
    
    results = []
    
    if config_path.exists():
        print("✅ repos_sync.yaml 存在 / repos_sync.yaml exists")
        results.append(True)
    else:
        print("⚠️  repos_sync.yaml 不存在 / repos_sync.yaml not found")
        results.append(False)
    
    if example_config_path.exists():
        print("✅ repos_sync.example.yaml 存在 / repos_sync.example.yaml exists")
        results.append(True)
    else:
        print("❌ repos_sync.example.yaml 不存在 / repos_sync.example.yaml not found")
        results.append(False)
    
    return all(results)

def test_help_command():
    """Test help command"""
    print("\n📋 測試 3: 測試幫助命令 / Test 3: Test help command")
    success, output = run_command("python scripts/sync_external_repos.py --help")
    
    if success and "Repository File Synchronization Tool" in output:
        print("✅ 幫助命令正常運作 / Help command works")
        return True
    else:
        print("❌ 幫助命令失敗 / Help command failed")
        print(output)
        return False

def test_list_command():
    """Test list command"""
    print("\n📋 測試 4: 測試列表命令 / Test 4: Test list command")
    success, output = run_command("python scripts/sync_external_repos.py --list")
    
    if success:
        print("✅ 列表命令正常運作 / List command works")
        print(f"輸出 / Output:\n{output}")
        return True
    else:
        print("❌ 列表命令失敗 / List command failed")
        print(output)
        return False

def test_yaml_syntax():
    """Test YAML syntax"""
    print("\n📋 測試 5: 驗證 YAML 語法 / Test 5: Validate YAML syntax")
    
    yaml_files = [
        "repos_sync.yaml",
        "repos_sync.example.yaml",
        ".github/workflows/sync-external-repos.yml"
    ]
    
    all_valid = True
    for yaml_file in yaml_files:
        if not Path(yaml_file).exists():
            print(f"⚠️  {yaml_file} 不存在 / {yaml_file} not found")
            continue
            
        success, _ = run_command(f"python -c \"import yaml; yaml.safe_load(open('{yaml_file}'))\"")
        
        if success:
            print(f"✅ {yaml_file} 語法正確 / {yaml_file} syntax valid")
        else:
            print(f"❌ {yaml_file} 語法錯誤 / {yaml_file} syntax error")
            all_valid = False
    
    return all_valid

def test_documentation_exists():
    """Test if documentation exists"""
    print("\n📋 測試 6: 檢查文檔檔案 / Test 6: Check documentation files")
    
    docs = [
        "docs/EXTERNAL_REPO_SYNC.md",
        "docs/REPO_SYNC_EXAMPLES.md",
        "docs/REPO_SYNC_QUICKREF.md"
    ]
    
    all_exist = True
    for doc in docs:
        if Path(doc).exists():
            print(f"✅ {doc} 存在 / {doc} exists")
        else:
            print(f"❌ {doc} 不存在 / {doc} not found")
            all_exist = False
    
    return all_exist

def test_workflow_exists():
    """Test if GitHub Actions workflow exists"""
    print("\n📋 測試 7: 檢查 GitHub Actions workflow / Test 7: Check GitHub Actions workflow")
    workflow_path = Path(".github/workflows/sync-external-repos.yml")
    
    if workflow_path.exists():
        print("✅ GitHub Actions workflow 存在 / GitHub Actions workflow exists")
        return True
    else:
        print("❌ GitHub Actions workflow 不存在 / GitHub Actions workflow not found")
        return False

def test_gitignore_updated():
    """Test if .gitignore includes backup directory"""
    print("\n📋 測試 8: 檢查 .gitignore 更新 / Test 8: Check .gitignore update")
    gitignore_path = Path(".gitignore")
    
    if not gitignore_path.exists():
        print("❌ .gitignore 不存在 / .gitignore not found")
        return False
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    if ".sync_backups/" in content:
        print("✅ .gitignore 包含備份目錄 / .gitignore includes backup directory")
        return True
    else:
        print("❌ .gitignore 未包含備份目錄 / .gitignore doesn't include backup directory")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("🧪 外部倉庫同步系統測試 / External Repo Sync System Tests")
    print("="*60)
    
    tests = [
        ("腳本存在 / Script exists", test_script_exists),
        ("配置存在 / Config exists", test_config_exists),
        ("幫助命令 / Help command", test_help_command),
        ("列表命令 / List command", test_list_command),
        ("YAML 語法 / YAML syntax", test_yaml_syntax),
        ("文檔存在 / Docs exist", test_documentation_exists),
        ("Workflow 存在 / Workflow exists", test_workflow_exists),
        (".gitignore 更新 / .gitignore updated", test_gitignore_updated),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ 測試失敗 / Test failed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 測試摘要 / Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} / {'PASS' if result else 'FAIL'}: {name}")
    
    print(f"\n總計 / Total: {passed}/{total} 測試通過 / tests passed")
    
    if passed == total:
        print("\n🎉 所有測試通過！ / All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 個測試失敗 / {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
