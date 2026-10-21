#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository Stability Checker
倉庫穩定性檢查工具

檢查配置的倉庫是否可訪問和穩定
Check if configured repositories are accessible and stable
"""

import os
import sys
import yaml
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class RepoStabilityChecker:
    """Repository stability checker / 倉庫穩定性檢查器"""
    
    def __init__(self, config_path: str = "repos_sync.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.results = []
        
    def _load_config(self) -> Dict:
        """Load configuration file / 載入配置檔案"""
        if not os.path.exists(self.config_path):
            print(f"❌ 配置檔案不存在: {self.config_path}")
            print(f"❌ Config file not found: {self.config_path}")
            sys.exit(1)
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[bool, str, float]:
        """
        Run shell command with timeout / 執行 shell 命令並設置超時
        Returns: (success, output, elapsed_time)
        """
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            elapsed = time.time() - start_time
            return True, result.stdout, elapsed
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            return False, f"Timeout after {timeout}s", elapsed
        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start_time
            return False, e.stderr, elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            return False, str(e), elapsed
    
    def _check_repo_accessibility(self, repo_config: Dict) -> Dict:
        """
        Check if repository is accessible / 檢查倉庫是否可訪問
        """
        name = repo_config.get('name', 'unnamed')
        url = repo_config['url']
        branch = repo_config.get('branch', 'main')
        enabled = repo_config.get('enabled', True)
        
        result = {
            'name': name,
            'url': url,
            'branch': branch,
            'enabled': enabled,
            'accessible': False,
            'response_time': 0,
            'branch_exists': False,
            'error': None,
            'status': 'unknown'
        }
        
        if not enabled:
            result['status'] = 'disabled'
            result['accessible'] = True  # Not checked, but not an error
            return result
        
        print(f"\n🔍 檢查倉庫: {name}")
        print(f"🔍 Checking repository: {name}")
        print(f"   URL: {url}")
        print(f"   分支 / Branch: {branch}")
        
        # Check if repository is accessible via git ls-remote
        print("   ⏳ 檢查連線性... / Testing connectivity...")
        success, output, elapsed = self._run_command([
            'git', 'ls-remote', '--heads', url, f'refs/heads/{branch}'
        ], timeout=30)
        
        result['response_time'] = elapsed
        
        if success:
            result['accessible'] = True
            # Check if the specific branch exists
            if branch in output or f'refs/heads/{branch}' in output:
                result['branch_exists'] = True
                result['status'] = 'healthy'
                print(f"   ✅ 倉庫可訪問 / Repository accessible ({elapsed:.2f}s)")
                print(f"   ✅ 分支存在 / Branch exists")
            else:
                result['branch_exists'] = False
                result['status'] = 'branch_missing'
                result['error'] = f"Branch '{branch}' not found"
                print(f"   ⚠️  倉庫可訪問但分支不存在 / Repository accessible but branch missing")
                print(f"   ⚠️  分支 '{branch}' 未找到 / Branch '{branch}' not found")
        else:
            result['accessible'] = False
            result['status'] = 'unreachable'
            result['error'] = output.strip()
            print(f"   ❌ 倉庫無法訪問 / Repository unreachable ({elapsed:.2f}s)")
            print(f"   ❌ 錯誤 / Error: {output.strip()[:100]}")
        
        return result
    
    def _check_repo_health(self, repo_config: Dict) -> Dict:
        """
        Perform deeper health check on repository / 對倉庫進行深度健康檢查
        """
        name = repo_config.get('name', 'unnamed')
        url = repo_config['url']
        branch = repo_config.get('branch', 'main')
        
        health = {
            'has_commits': False,
            'last_commit_age': None,
            'commit_count': 0
        }
        
        print(f"   🏥 健康檢查... / Health check...")
        
        # Get recent commits to check activity
        success, output, elapsed = self._run_command([
            'git', 'ls-remote', '--heads', '--refs', url
        ], timeout=30)
        
        if success and output:
            refs = output.strip().split('\n')
            health['commit_count'] = len(refs)
            health['has_commits'] = len(refs) > 0
            print(f"   ✅ 找到 {len(refs)} 個分支 / Found {len(refs)} branches")
        else:
            print(f"   ⚠️  無法獲取提交資訊 / Cannot get commit info")
        
        return health
    
    def check_all_repositories(self) -> bool:
        """
        Check all configured repositories / 檢查所有配置的倉庫
        """
        repositories = self.config.get('repositories', [])
        
        if not repositories:
            print("⚠️  沒有配置任何倉庫")
            print("⚠️  No repositories configured")
            return False
        
        print("\n" + "="*70)
        print("🏥 倉庫穩定性檢查 / Repository Stability Check")
        print("="*70)
        print(f"⏰ 檢查時間 / Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📦 總計倉庫數 / Total repositories: {len(repositories)}")
        
        for repo_config in repositories:
            try:
                # Basic accessibility check
                result = self._check_repo_accessibility(repo_config)
                
                # If accessible, do health check
                if result['accessible'] and result['branch_exists']:
                    health = self._check_repo_health(repo_config)
                    result['health'] = health
                
                self.results.append(result)
                
            except Exception as e:
                print(f"   ❌ 檢查失敗 / Check failed: {e}")
                self.results.append({
                    'name': repo_config.get('name', 'unnamed'),
                    'status': 'error',
                    'error': str(e)
                })
        
        return True
    
    def print_summary(self):
        """Print summary of all checks / 打印所有檢查的摘要"""
        print("\n" + "="*70)
        print("📊 穩定性檢查摘要 / Stability Check Summary")
        print("="*70)
        
        healthy = sum(1 for r in self.results if r.get('status') == 'healthy')
        disabled = sum(1 for r in self.results if r.get('status') == 'disabled')
        unreachable = sum(1 for r in self.results if r.get('status') == 'unreachable')
        branch_missing = sum(1 for r in self.results if r.get('status') == 'branch_missing')
        errors = sum(1 for r in self.results if r.get('status') == 'error')
        
        total = len(self.results)
        
        print(f"\n📈 狀態統計 / Status Statistics:")
        print(f"   ✅ 健康 / Healthy: {healthy}")
        print(f"   ⏸️  停用 / Disabled: {disabled}")
        print(f"   ❌ 無法訪問 / Unreachable: {unreachable}")
        print(f"   ⚠️  分支缺失 / Branch Missing: {branch_missing}")
        print(f"   🔥 錯誤 / Errors: {errors}")
        print(f"   📦 總計 / Total: {total}")
        
        print(f"\n📋 詳細結果 / Detailed Results:")
        for result in self.results:
            name = result.get('name', 'unknown')
            status = result.get('status', 'unknown')
            
            status_icon = {
                'healthy': '✅',
                'disabled': '⏸️',
                'unreachable': '❌',
                'branch_missing': '⚠️',
                'error': '🔥',
                'unknown': '❓'
            }.get(status, '❓')
            
            print(f"\n{status_icon} {name}")
            print(f"   狀態 / Status: {status}")
            
            if result.get('enabled') is False:
                print(f"   ℹ️  已停用 / Disabled in config")
            
            if result.get('response_time'):
                print(f"   ⏱️  回應時間 / Response time: {result['response_time']:.2f}s")
            
            if result.get('error'):
                error_msg = result['error'][:100]
                print(f"   ⚠️  錯誤 / Error: {error_msg}")
            
            if result.get('health'):
                health = result['health']
                if health.get('commit_count'):
                    print(f"   🔢 分支數 / Branch count: {health['commit_count']}")
        
        # Overall health assessment
        print("\n" + "="*70)
        if healthy > 0 and unreachable == 0 and errors == 0:
            print("🎉 所有啟用的倉庫都健康！ / All enabled repositories are healthy!")
            return True
        elif unreachable > 0 or errors > 0:
            print("⚠️  部分倉庫存在問題，請檢查配置")
            print("⚠️  Some repositories have issues, please check configuration")
            return False
        else:
            print("ℹ️  檢查完成 / Check completed")
            return True
    
    def generate_report(self, output_file: str = None):
        """Generate detailed report / 生成詳細報告"""
        if output_file is None:
            output_file = f"repo_stability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report = []
        report.append("# 倉庫穩定性檢查報告 / Repository Stability Check Report\n")
        report.append(f"\n**檢查時間 / Check Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**配置檔案 / Config File**: `{self.config_path}`\n")
        
        report.append("\n## 摘要 / Summary\n")
        healthy = sum(1 for r in self.results if r.get('status') == 'healthy')
        total = len(self.results)
        report.append(f"- 健康倉庫 / Healthy: {healthy}/{total}\n")
        
        report.append("\n## 詳細結果 / Detailed Results\n")
        for result in self.results:
            name = result.get('name', 'unknown')
            status = result.get('status', 'unknown')
            report.append(f"\n### {name}\n")
            report.append(f"- **狀態 / Status**: {status}\n")
            report.append(f"- **URL**: {result.get('url', 'N/A')}\n")
            report.append(f"- **分支 / Branch**: {result.get('branch', 'N/A')}\n")
            
            if result.get('response_time'):
                report.append(f"- **回應時間 / Response Time**: {result['response_time']:.2f}s\n")
            
            if result.get('error'):
                report.append(f"- **錯誤 / Error**: `{result['error']}`\n")
        
        report_text = ''.join(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"\n📄 報告已生成 / Report generated: {output_file}")
        return output_file


def main():
    """Main entry point / 主要入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Repository Stability Checker / 倉庫穩定性檢查工具'
    )
    parser.add_argument(
        '-c', '--config',
        default='repos_sync.yaml',
        help='配置檔案路徑 / Configuration file path'
    )
    parser.add_argument(
        '-r', '--report',
        action='store_true',
        help='生成報告檔案 / Generate report file'
    )
    parser.add_argument(
        '-o', '--output',
        help='報告輸出路徑 / Report output path'
    )
    
    args = parser.parse_args()
    
    try:
        checker = RepoStabilityChecker(args.config)
        checker.check_all_repositories()
        is_healthy = checker.print_summary()
        
        if args.report:
            checker.generate_report(args.output)
        
        sys.exit(0 if is_healthy else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  檢查已中斷")
        print("⚠️  Check interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 檢查失敗: {e}")
        print(f"❌ Check failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
