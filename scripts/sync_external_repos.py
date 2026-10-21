#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository File Synchronization Tool
倉庫檔案同步工具

從其他 GitHub 倉庫拉取指定的檔案和目錄到本地倉庫
Pull specified files and directories from other GitHub repositories to local repository
"""

import os
import sys
import yaml
import subprocess
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import tempfile
import argparse
import json


class RepoSyncManager:
    """Repository synchronization manager / 倉庫同步管理器"""
    
    def __init__(self, config_path: str = "repos_sync.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.repo_root = Path(__file__).parent.parent.absolute()
        self.receipt = {"schema": "Mrliou_MRL_Sync_Receipt_v1",
                        "origin_signature": "MrLiouWord",
                        "tool_role": "engineering_transport",
                        "rights_transfer": "NOT_GRANTED",
                        "commercial_release": "NOT_APPROVED_BY_SYNC",
                        "repositories": [], "files": [], "errors": []}
        self.source_commit = None

    def _safe_path(self, root: Path, relative: str) -> Path:
        """Reject traversal, Git metadata and symlinks before copying or staging."""
        path = Path(relative)
        if (path.is_absolute() or not path.parts or
                any(p in {'.', '..', '.git', '.github'} for p in path.parts)):
            raise ValueError(f"Unsafe sync path: {relative}")
        candidate = root / path
        if root.resolve() == self.repo_root.resolve() and (
                path.as_posix() in {'scripts/sync_external_repos.py',
                                    'scripts/mrliou_publish_sync.sh', 'repos_sync.yaml'} or
                any(p.startswith('.env') for p in path.parts)):
            raise ValueError(f"Protected sync control or environment path: {relative}")
        if not candidate.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Sync path escapes its root: {relative}")
        if any(p.is_symlink() for p in [candidate, *candidate.parents] if p != root):
            raise ValueError(f"Symlink sync path: {relative}")
        return candidate

    def _copy_recorded(self, repo_config: Dict, src: Path, dest: Path,
                       source_path: str) -> bool:
        """Preserve source identity and apply the existing conflict policy uniformly."""
        source_hash = hashlib.sha256(src.read_bytes()).hexdigest()
        record = {"repository": repo_config['name'], "source_url": repo_config['url'],
                  "source_branch": repo_config.get('branch', 'main'),
                  "source_commit": self.source_commit, "source_path": source_path,
                  "destination": dest.relative_to(self.repo_root).as_posix(),
                  "source_sha256": source_hash, "size_bytes": src.stat().st_size}
        self.receipt['files'].append(record)
        if dest.exists():
            destination_hash = hashlib.sha256(dest.read_bytes()).hexdigest()
            record['destination_sha256'] = destination_hash
            if destination_hash == source_hash:
                record['status'] = 'unchanged'
                return True
            strategy = self.config.get('settings', {}).get('conflict_strategy', 'skip')
            if strategy == 'skip':
                record['status'] = 'skipped_conflict'
                return True
            if strategy == 'prompt' and input(f"Overwrite {dest}? (y/n): ").lower() != 'y':
                record['status'] = 'skipped_conflict'
                return True
            if strategy not in {'overwrite', 'prompt'}:
                raise ValueError(f"Unknown conflict strategy: {strategy}")
            self._create_backup(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        record['destination_sha256'] = hashlib.sha256(dest.read_bytes()).hexdigest()
        record['status'] = ('copied' if record['destination_sha256'] == source_hash
                            else 'integrity_failed')
        return record['status'] == 'copied'

    def write_receipt(self, path: str, success: bool) -> None:
        """Write a run-local receipt; publishing never treats it as a rights grant."""
        self.receipt['success'] = success
        self.receipt['observed_at_utc'] = datetime.now(timezone.utc).isoformat()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.receipt, ensure_ascii=False, indent=2) + '\n',
                          encoding='utf-8')
        
    def _load_config(self) -> Dict:
        """Load configuration file / 載入配置檔案"""
        if not os.path.exists(self.config_path):
            print(f"❌ 配置檔案不存在: {self.config_path}")
            print(f"❌ Config file not found: {self.config_path}")
            sys.exit(1)
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _run_command(self, cmd: List[str], cwd: Optional[str] = None) -> tuple:
        """Run shell command / 執行 shell 命令"""
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
    
    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create backup of existing file / 建立現有檔案的備份"""
        if not file_path.exists():
            return None
            
        settings = self.config.get('settings', {})
        if not settings.get('backup_before_sync', True):
            return None
            
        backup_dir = Path(settings.get('backup_dir', '.sync_backups'))
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f"{file_path.name}.{timestamp}.bak"
        
        shutil.copy2(file_path, backup_path)
        print(f"📦 已備份: {file_path} -> {backup_path}")
        print(f"📦 Backed up: {file_path} -> {backup_path}")
        
        return backup_path
    
    def _verify_file_integrity(self, file_path: Path, expected_hash: Optional[str] = None) -> bool:
        """Verify file integrity using SHA-256 / 使用 SHA-256 驗證檔案完整性"""
        if not self.config.get('settings', {}).get('verify_integrity', True):
            return True
            
        if not file_path.exists():
            return False
            
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        file_hash = sha256_hash.hexdigest()
        
        if expected_hash:
            return file_hash == expected_hash
        
        print(f"🔐 檔案雜湊值: {file_hash}")
        print(f"🔐 File hash: {file_hash}")
        return True
    
    def _should_exclude(self, path: str, exclude_patterns: List[str]) -> bool:
        """Check if path should be excluded / 檢查路徑是否應該被排除"""
        from fnmatch import fnmatch
        
        for pattern in exclude_patterns:
            if fnmatch(path, pattern):
                return True
        return False
    
    def _clone_repo(self, repo_config: Dict, temp_dir: Path) -> bool:
        """Clone repository to temporary directory / 複製倉庫到臨時目錄"""
        url = repo_config['url']
        branch = repo_config.get('branch', 'main')
        
        print(f"\n🔄 正在複製倉庫: {url}")
        print(f"🔄 Cloning repository: {url}")
        print(f"📌 分支: {branch}")
        print(f"📌 Branch: {branch}")
        
        success, output = self._run_command([
            'git', 'clone', 
            '--depth', '1', 
            '--branch', branch,
            url, 
            str(temp_dir)
        ])
        
        if not success:
            print(f"❌ 複製失敗: {output}")
            print(f"❌ Clone failed: {output}")
            return False
        
        print("✅ 複製成功")
        print("✅ Clone successful")
        ok, commit = self._run_command(['git', 'rev-parse', 'HEAD'], cwd=str(temp_dir))
        if not ok:
            return False
        self.source_commit = commit.strip()
        self.receipt['repositories'].append({
            'name': repo_config['name'], 'url': url, 'branch': branch,
            'commit': self.source_commit, 'role': 'source_material',
            'license_status': 'UNRESOLVED_NOT_INFERRED_FROM_ACCESS'})
        return True
    
    def _sync_files(self, repo_config: Dict, temp_dir: Path) -> bool:
        """Sync individual files / 同步個別檔案"""
        files = repo_config.get('files', [])
        if not files:
            return True
            
        success = True
        
        for file_config in files:
            src = self._safe_path(temp_dir, file_config['src'])
            dest = self._safe_path(self.repo_root, file_config['dest'])
            
            if not src.is_file():
                print(f"⚠️  來源檔案不存在: {src}")
                print(f"⚠️  Source file not found: {src}")
                self.receipt['errors'].append(f"Missing source: {file_config['src']}")
                success = False
                continue
            
            success = self._copy_recorded(repo_config, src, dest, file_config['src']) and success
        
        return success
    
    def _sync_directories(self, repo_config: Dict, temp_dir: Path) -> bool:
        """Sync directories / 同步目錄"""
        directories = repo_config.get('directories', [])
        if not directories:
            return True
            
        exclude_patterns = self.config.get('exclude_patterns', [])
        success = True
        
        for dir_config in directories:
            src = self._safe_path(temp_dir, dir_config['src'])
            dest = self._safe_path(self.repo_root, dir_config['dest'])
            
            if not src.is_dir():
                print(f"⚠️  來源目錄不存在: {src}")
                print(f"⚠️  Source directory not found: {src}")
                self.receipt['errors'].append(f"Missing directory: {dir_config['src']}")
                success = False
                continue
            
            # Additional exclude patterns for this directory
            local_exclude = dir_config.get('exclude', [])
            all_excludes = exclude_patterns + local_exclude
            
            print(f"\n📁 正在同步目錄: {dir_config['src']} -> {dir_config['dest']}")
            print(f"📁 Syncing directory: {dir_config['src']} -> {dir_config['dest']}")
            
            # Create destination directory
            dest.mkdir(parents=True, exist_ok=True)
            
            # Copy directory contents (optimized: collect files first, then create dirs once)
            files_to_copy = []
            dirs_to_create = set()
            
            for item in sorted(src.rglob('*')):
                if item.is_symlink():
                    raise ValueError(f"Symlink in source directory: {item.relative_to(src)}")
                if item.is_file():
                    rel_path = item.relative_to(src)
                    
                    # Check exclusions
                    if (self._should_exclude(str(rel_path), all_excludes) or
                            any(self._should_exclude(p, all_excludes) for p in rel_path.parts)):
                        print(f"⏭️  排除: {rel_path}")
                        continue
                    
                    dest_file = self._safe_path(self.repo_root, str(Path(dir_config['dest']) / rel_path))
                    files_to_copy.append((item, dest_file, rel_path))
                    # Collect unique parent directories
                    dirs_to_create.add(dest_file.parent)
            
            # Create all directories once (batch operation)
            for dir_path in dirs_to_create:
                dir_path.mkdir(parents=True, exist_ok=True)
            
            # Copy all files
            for src_file, dest_file, rel_path in files_to_copy:
                success = self._copy_recorded(repo_config, src_file, dest_file,
                                             str(Path(dir_config['src']) / rel_path)) and success
        
        return success
    
    def _add_submodule(self, repo_config: Dict) -> bool:
        """Add repository as Git submodule / 將倉庫加入為 Git 子模組"""
        url = repo_config['url']
        dest = repo_config['dest']
        branch = repo_config.get('branch', 'main')
        
        print(f"\n🔗 正在添加子模組: {url}")
        print(f"🔗 Adding submodule: {url}")
        print(f"📍 位置: {dest}")
        print(f"📍 Location: {dest}")
        
        # Check if submodule already exists
        if os.path.exists(dest):
            print(f"⚠️  目錄已存在: {dest}")
            print(f"⚠️  Directory already exists: {dest}")
            return False
        
        success, output = self._run_command([
            'git', 'submodule', 'add',
            '-b', branch,
            url, dest
        ], cwd=str(self.repo_root))
        
        if not success:
            print(f"❌ 添加子模組失敗: {output}")
            print(f"❌ Failed to add submodule: {output}")
            return False
        
        print("✅ 子模組添加成功")
        print("✅ Submodule added successfully")
        return True
    
    def _run_post_sync_commands(self) -> bool:
        """Run post-sync commands / 執行同步後命令"""
        commands = self.config.get('settings', {}).get('post_sync_commands', [])
        if not commands:
            return True
        
        print("\n🔧 正在執行同步後命令...")
        print("🔧 Running post-sync commands...")
        
        for cmd in commands:
            print(f"\n▶ {cmd}")
            success, output = self._run_command(cmd.split(), cwd=str(self.repo_root))
            if success:
                print(f"✅ 成功")
                if output:
                    print(output)
            else:
                print(f"❌ 失敗: {output}")
                self.receipt['errors'].append('Post-sync command failed')
                return False
        return True
    
    def sync(self, repo_name: Optional[str] = None) -> bool:
        """Main synchronization method / 主要同步方法"""
        repositories = self.config.get('repositories', [])
        
        if not repositories:
            print("⚠️  沒有配置任何倉庫")
            print("⚠️  No repositories configured")
            return False
        
        # Filter by repository name if specified
        if repo_name:
            repositories = [r for r in repositories if r.get('name') == repo_name]
            if not repositories:
                print(f"❌ 找不到倉庫: {repo_name}")
                print(f"❌ Repository not found: {repo_name}")
                return False
        
        # Disabled sources are not attempted; one success cannot hide another failure.
        enabled_count = sum(bool(r.get('enabled', True)) for r in repositories)
        success_count = 0
        for repo_config in repositories:
            name = repo_config.get('name', 'unnamed')
            
            # Check if enabled
            if not repo_config.get('enabled', True):
                print(f"\n⏭️  跳過已停用的倉庫: {name}")
                print(f"⏭️  Skipping disabled repository: {name}")
                continue
            
            print(f"\n{'='*60}")
            print(f"📦 處理倉庫: {name}")
            print(f"📦 Processing repository: {name}")
            print(f"{'='*60}")
            
            # Handle submodules differently
            if repo_config.get('submodule', False):
                if self._add_submodule(repo_config):
                    success_count += 1
                else:
                    self.receipt['errors'].append(f"Submodule failed: {name}")
                continue
            
            # Clone to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                if not self._clone_repo(repo_config, temp_path):
                    self.receipt['errors'].append(f"Source clone failed: {name}")
                    continue
                
                # Sync files and directories
                files_ok = self._sync_files(repo_config, temp_path)
                dirs_ok = self._sync_directories(repo_config, temp_path)
                
                if files_ok and dirs_ok:
                    success_count += 1
                    print(f"\n✅ 倉庫 {name} 同步完成")
                    print(f"✅ Repository {name} synced successfully")
        
        # Run post-sync commands
        commands_ok = True
        if enabled_count > 0 and success_count == enabled_count:
            commands_ok = self._run_post_sync_commands()
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 同步摘要 / Sync Summary")
        print(f"{'='*60}")
        print(f"✅ 成功: {success_count}")
        print(f"✅ Success: {success_count}")
        print(f"📦 總計: {len(repositories)}")
        print(f"📦 Total: {len(repositories)}")
        
        return success_count == enabled_count and commands_ok


def main():
    """Main entry point / 主要入口"""
    parser = argparse.ArgumentParser(
        description='Repository File Synchronization Tool / 倉庫檔案同步工具'
    )
    parser.add_argument(
        '-c', '--config',
        default='repos_sync.yaml',
        help='配置檔案路徑 / Configuration file path'
    )
    parser.add_argument(
        '-r', '--repo',
        help='指定要同步的倉庫名稱 / Specify repository name to sync'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有配置的倉庫 / List all configured repositories'
    )
    
    parser.add_argument('--report', help='Run-local JSON provenance receipt path')
    args = parser.parse_args()
    
    # Load manager
    try:
        manager = RepoSyncManager(args.config)
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        print(f"❌ Initialization failed: {e}")
        sys.exit(1)
    
    # List repositories
    if args.list:
        repositories = manager.config.get('repositories', [])
        if not repositories:
            print("\n⚠️  沒有配置任何倉庫")
            print("⚠️  No repositories configured")
            print("\n請編輯 repos_sync.yaml 檔案來添加倉庫配置")
            print("Please edit repos_sync.yaml file to add repository configuration")
            return
        
        print("\n📋 配置的倉庫列表:")
        print("📋 Configured Repositories:")
        print(f"{'='*60}")
        for repo in repositories:
            name = repo.get('name', 'unnamed')
            url = repo.get('url', 'N/A')
            enabled = repo.get('enabled', True)
            status = '✅' if enabled else '⏸️'
            print(f"{status} {name}")
            print(f"   URL: {url}")
            print(f"   Branch: {repo.get('branch', 'main')}")
            print()
        return
    
    # Run synchronization
    success = False
    try:
        success = manager.sync(args.repo)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  同步已中斷")
        print("⚠️  Sync interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 同步失敗: {e}")
        manager.receipt['errors'].append(str(e))
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if args.report:
            manager.write_receipt(args.report, success)


if __name__ == '__main__':
    main()
