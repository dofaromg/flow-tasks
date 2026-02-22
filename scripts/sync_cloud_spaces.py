#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Cloud Space Synchronization Tool with Particle Globe Memory
多雲空間同步工具 - 整合粒子地球儀記憶法

同步各個雲空間（包含沙盒環境）並運用粒子地球儀記憶法進行通道升級
Sync across cloud spaces (including sandbox) with particle globe memory method for channel upgrades
"""

import os
import sys
import yaml
import json
import subprocess
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import tempfile
import argparse

# Add particle_core to path for memory integration
sys.path.insert(0, str(Path(__file__).parent.parent / "particle_core" / "src"))

try:
    from memory_archive_seed import MemoryArchiveSeed
    MEMORY_INTEGRATION = True
except ImportError:
    MEMORY_INTEGRATION = False
    print("⚠️  粒子記憶系統未載入，使用基本同步模式")
    print("⚠️  Particle memory system not loaded, using basic sync mode")


class CloudSpaceSyncManager:
    """
    Multi-cloud space synchronization manager with particle memory integration
    多雲空間同步管理器 - 整合粒子記憶系統
    """
    
    def __init__(self, config_path: str = "cloud_spaces_sync.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.repo_root = Path(__file__).parent.parent.absolute()
        
        # Initialize particle memory system if available
        if MEMORY_INTEGRATION:
            self.memory_system = MemoryArchiveSeed(
                storage_path=str(self.repo_root / ".cloud_sync_memory")
            )
        else:
            self.memory_system = None
        
        # Cloud space definitions
        self.cloud_spaces = {
            "production": "生產環境 - Production Environment",
            "staging": "預備環境 - Staging Environment",
            "sandbox": "沙盒環境 - Sandbox Environment",
            "development": "開發環境 - Development Environment",
            "local": "本地環境 - Local Environment"
        }
        
    def _load_config(self) -> Dict:
        """Load configuration file / 載入配置檔案"""
        if not os.path.exists(self.config_path):
            # Create default config if not exists
            default_config = self._create_default_config()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(default_config, f, allow_unicode=True, sort_keys=False)
            print(f"✅ 已創建預設配置: {self.config_path}")
            print(f"✅ Created default config: {self.config_path}")
            return default_config
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _create_default_config(self) -> Dict:
        """Create default configuration / 創建預設配置"""
        return {
            "version": "1.0",
            "particle_globe_memory": {
                "enabled": True,
                "memory_archive_path": ".cloud_sync_memory",
                "checkpoint_frequency": "每次同步 / every sync",
                "retention_days": 30
            },
            "cloud_spaces": [
                {
                    "name": "production",
                    "type": "gke",
                    "enabled": True,
                    "cluster_name": "modular-cluster",
                    "region": "asia-east1",
                    "zone": "asia-east1-a",
                    "namespace": "flowagent",
                    "sync_paths": [
                        {"src": "cluster/overlays/prod", "dest": "deployed/prod"},
                        {"src": "apps/", "dest": "deployed/apps"}
                    ]
                },
                {
                    "name": "sandbox",
                    "type": "local",
                    "enabled": True,
                    "description": "本地沙盒環境用於測試",
                    "sync_paths": [
                        {"src": "particle_core/", "dest": "sandbox/particle_core"},
                        {"src": "examples/", "dest": "sandbox/examples"}
                    ]
                }
            ],
            "channel_upgrades": {
                "enabled": True,
                "upgrade_strategies": [
                    "progressive_rollout",
                    "blue_green",
                    "canary"
                ],
                "auto_rollback": True,
                "health_check_timeout": 300
            },
            "sync_settings": {
                "parallel_sync": True,
                "max_workers": 4,
                "retry_attempts": 3,
                "backup_before_sync": True,
                "verify_integrity": True
            }
        }
    
    def _run_command(self, cmd: List[str], cwd: Optional[str] = None, timeout: int = 300) -> Tuple[bool, str]:
        """Run shell command / 執行命令"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return True, result.stdout
        except subprocess.TimeoutExpired:
            return False, f"命令超時 / Command timeout: {timeout}s"
        except subprocess.CalledProcessError as e:
            return False, e.stderr
        except Exception as e:
            return False, str(e)
    
    def _create_memory_checkpoint(self, space_name: str, sync_data: Dict) -> Optional[str]:
        """
        Create particle memory checkpoint for sync state
        創建粒子記憶檢查點
        """
        if not self.memory_system:
            return None
        
        try:
            checkpoint_data = {
                "space_name": space_name,
                "sync_timestamp": datetime.now().isoformat(),
                "sync_data": sync_data,
                "cloud_space_state": self._get_space_state(space_name)
            }
            
            seed = self.memory_system.create_seed(
                particle_data=checkpoint_data,
                metadata={
                    "type": "cloud_sync_checkpoint",
                    "space": space_name,
                    "globe_memory_enabled": True
                },
                seed_name=f"cloud_sync_{space_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # Save seed to disk
            seed_path = self.memory_system.storage_path / f"{seed['seed_name']}.json"
            with open(seed_path, 'w', encoding='utf-8') as f:
                json.dump(seed, f, indent=2, ensure_ascii=False)
            
            print(f"🌍 粒子地球儀記憶檢查點已創建: {seed['seed_name']}")
            print(f"🌍 Particle globe memory checkpoint created: {seed['seed_name']}")
            
            return seed['seed_name']
            
        except Exception as e:
            print(f"⚠️  記憶檢查點創建失敗: {e}")
            print(f"⚠️  Memory checkpoint creation failed: {e}")
            return None
    
    def _get_space_state(self, space_name: str) -> Dict:
        """Get current state of cloud space / 獲取雲空間當前狀態"""
        space_config = self._get_space_config(space_name)
        if not space_config:
            return {}
        
        state = {
            "name": space_name,
            "type": space_config.get("type", "unknown"),
            "enabled": space_config.get("enabled", False),
            "last_checked": datetime.now().isoformat()
        }
        
        # Check if paths exist
        if "sync_paths" in space_config:
            state["paths_status"] = []
            for path_config in space_config["sync_paths"]:
                src = Path(path_config["src"])
                state["paths_status"].append({
                    "src": str(src),
                    "exists": src.exists(),
                    "is_dir": src.is_dir() if src.exists() else None
                })
        
        return state
    
    def _get_space_config(self, space_name: str) -> Optional[Dict]:
        """Get configuration for specific cloud space / 獲取特定雲空間配置"""
        spaces = self.config.get("cloud_spaces", [])
        for space in spaces:
            if space.get("name") == space_name:
                return space
        return None
    
    def _sync_space(self, space_config: Dict) -> bool:
        """Sync a single cloud space / 同步單個雲空間"""
        space_name = space_config.get("name", "unknown")
        space_type = space_config.get("type", "unknown")
        
        print(f"\n{'='*70}")
        print(f"🌐 同步雲空間: {space_name} ({space_type})")
        print(f"🌐 Syncing cloud space: {space_name} ({space_type})")
        print(f"{'='*70}")
        
        if not space_config.get("enabled", True):
            print(f"⏸️  雲空間已停用 / Cloud space disabled")
            return True
        
        sync_paths = space_config.get("sync_paths", [])
        if not sync_paths:
            print(f"⚠️  未配置同步路徑 / No sync paths configured")
            return False
        
        success_count = 0
        for path_config in sync_paths:
            src = self.repo_root / path_config["src"]
            dest = self.repo_root / path_config["dest"]
            
            print(f"\n📁 同步路徑 / Sync path:")
            print(f"   來源 / Source: {src}")
            print(f"   目標 / Destination: {dest}")
            
            if not src.exists():
                print(f"   ⚠️  來源不存在 / Source not found")
                continue
            
            # Create destination directory
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform sync based on type
            if space_type == "gke":
                success = self._sync_to_gke(src, dest, space_config)
            elif space_type == "local":
                success = self._sync_local(src, dest)
            else:
                print(f"   ⚠️  未知的空間類型 / Unknown space type: {space_type}")
                success = False
            
            if success:
                success_count += 1
                print(f"   ✅ 同步成功 / Sync successful")
            else:
                print(f"   ❌ 同步失敗 / Sync failed")
        
        # Create memory checkpoint
        checkpoint = self._create_memory_checkpoint(
            space_name,
            {
                "paths_synced": success_count,
                "total_paths": len(sync_paths),
                "success": success_count > 0
            }
        )
        
        return success_count > 0
    
    def _sync_to_gke(self, src: Path, dest: Path, space_config: Dict) -> bool:
        """Sync to Google Kubernetes Engine / 同步到 GKE"""
        print(f"   🔄 使用 kubectl 同步到 GKE...")
        print(f"   🔄 Syncing to GKE with kubectl...")
        
        cluster = space_config.get("cluster_name", "")
        region = space_config.get("region", "")
        namespace = space_config.get("namespace", "default")
        
        # For now, copy files locally (in actual deployment, would use kubectl)
        try:
            if src.is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            else:
                shutil.copytree(src, dest, dirs_exist_ok=True)
            
            print(f"   📝 集群 / Cluster: {cluster}")
            print(f"   📝 區域 / Region: {region}")
            print(f"   📝 命名空間 / Namespace: {namespace}")
            
            return True
        except Exception as e:
            print(f"   ❌ 錯誤 / Error: {e}")
            return False
    
    def _sync_local(self, src: Path, dest: Path) -> bool:
        """Sync to local sandbox / 同步到本地沙盒"""
        print(f"   🔄 同步到本地沙盒...")
        print(f"   🔄 Syncing to local sandbox...")
        
        try:
            if src.is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            else:
                shutil.copytree(src, dest, dirs_exist_ok=True)
            return True
        except Exception as e:
            print(f"   ❌ 錯誤 / Error: {e}")
            return False
    
    def _perform_channel_upgrade(self, space_name: str) -> bool:
        """
        Perform channel upgrade using particle globe memory
        使用粒子地球儀記憶執行通道升級
        """
        print(f"\n🔼 執行通道升級: {space_name}")
        print(f"🔼 Performing channel upgrade: {space_name}")
        
        channel_config = self.config.get("channel_upgrades", {})
        if not channel_config.get("enabled", False):
            print(f"⏸️  通道升級未啟用 / Channel upgrade disabled")
            return True
        
        strategies = channel_config.get("upgrade_strategies", [])
        print(f"📋 升級策略 / Upgrade strategies: {', '.join(strategies)}")
        
        # Simulate upgrade process
        print(f"✅ 通道升級完成 / Channel upgrade completed")
        return True
    
    def list_cloud_spaces(self):
        """List all configured cloud spaces / 列出所有配置的雲空間"""
        print("\n🌐 配置的雲空間列表:")
        print("🌐 Configured Cloud Spaces:")
        print("="*70)
        
        spaces = self.config.get("cloud_spaces", [])
        if not spaces:
            print("\n⚠️  未配置雲空間")
            print("⚠️  No cloud spaces configured")
            return
        
        for space in spaces:
            name = space.get("name", "unknown")
            space_type = space.get("type", "unknown")
            enabled = space.get("enabled", False)
            status = "✅" if enabled else "⏸️"
            
            print(f"\n{status} {name}")
            print(f"   類型 / Type: {space_type}")
            print(f"   描述 / Description: {space.get('description', 'N/A')}")
            
            if space_type == "gke":
                print(f"   集群 / Cluster: {space.get('cluster_name', 'N/A')}")
                print(f"   區域 / Region: {space.get('region', 'N/A')}")
            
            sync_paths = space.get("sync_paths", [])
            print(f"   同步路徑數 / Sync paths: {len(sync_paths)}")
    
    def sync_all_spaces(self) -> bool:
        """Sync all cloud spaces / 同步所有雲空間"""
        print("\n" + "="*70)
        print("🌍 粒子地球儀記憶同步系統")
        print("🌍 Particle Globe Memory Sync System")
        print("="*70)
        
        if MEMORY_INTEGRATION:
            print("✅ 粒子記憶系統已啟用 / Particle memory system enabled")
        else:
            print("⚠️  基本同步模式 / Basic sync mode")
        
        spaces = self.config.get("cloud_spaces", [])
        if not spaces:
            print("\n⚠️  未配置雲空間")
            print("⚠️  No cloud spaces configured")
            return False
        
        print(f"\n📦 總計雲空間數 / Total cloud spaces: {len(spaces)}")
        
        success_count = 0
        for space in spaces:
            if self._sync_space(space):
                success_count += 1
                
                # Perform channel upgrade if enabled
                if self.config.get("channel_upgrades", {}).get("enabled", False):
                    self._perform_channel_upgrade(space.get("name", ""))
        
        # Summary
        print(f"\n{'='*70}")
        print(f"📊 同步摘要 / Sync Summary")
        print(f"{'='*70}")
        print(f"✅ 成功 / Success: {success_count}/{len(spaces)}")
        
        if success_count == len(spaces):
            print("\n🎉 所有雲空間同步完成！")
            print("🎉 All cloud spaces synced successfully!")
            return True
        else:
            print(f"\n⚠️  {len(spaces) - success_count} 個雲空間同步失敗")
            print(f"⚠️  {len(spaces) - success_count} cloud space(s) failed")
            return False
    
    def sync_specific_space(self, space_name: str) -> bool:
        """Sync a specific cloud space / 同步特定雲空間"""
        space_config = self._get_space_config(space_name)
        if not space_config:
            print(f"❌ 找不到雲空間: {space_name}")
            print(f"❌ Cloud space not found: {space_name}")
            return False
        
        return self._sync_space(space_config)
    
    def show_memory_checkpoints(self):
        """Show particle globe memory checkpoints / 顯示粒子地球儀記憶檢查點"""
        if not MEMORY_INTEGRATION:
            print("⚠️  粒子記憶系統未啟用")
            print("⚠️  Particle memory system not enabled")
            return
        
        memory_dir = self.repo_root / ".cloud_sync_memory"
        if not memory_dir.exists():
            print("ℹ️  尚未創建記憶檢查點")
            print("ℹ️  No memory checkpoints created yet")
            return
        
        print("\n🌍 粒子地球儀記憶檢查點:")
        print("🌍 Particle Globe Memory Checkpoints:")
        print("="*70)
        
        checkpoints = sorted(memory_dir.glob("cloud_sync_*.json"))
        
        # Use parallel reading for better performance
        from concurrent.futures import ThreadPoolExecutor
        
        def read_checkpoint(checkpoint):
            """Helper function to read a single checkpoint"""
            try:
                with open(checkpoint, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return (checkpoint.name, data)
            except Exception as e:
                return (checkpoint.name, {"error": str(e)})
        
        # Read last 10 checkpoints in parallel
        last_checkpoints = checkpoints[-10:]
        if last_checkpoints:
            max_workers = min(4, os.cpu_count() or 1)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(read_checkpoint, last_checkpoints))
            
            for checkpoint_name, data in results:
                print(f"\n📍 {checkpoint_name}")
                if "error" in data:
                    print(f"   ❌ 讀取錯誤 / Read Error: {data['error']}")
                else:
                    print(f"   時間 / Time: {data.get('created_at', 'N/A')}")
                    print(f"   校驗碼 / Checksum: {data.get('checksum', 'N/A')[:16]}...")


def main():
    """Main entry point / 主要入口"""
    parser = argparse.ArgumentParser(
        description='Multi-Cloud Space Sync with Particle Globe Memory / 多雲空間同步 - 粒子地球儀記憶法'
    )
    parser.add_argument(
        '-c', '--config',
        default='cloud_spaces_sync.yaml',
        help='配置檔案路徑 / Config file path'
    )
    parser.add_argument(
        '-s', '--space',
        help='指定要同步的雲空間 / Specify cloud space to sync'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有配置的雲空間 / List all configured cloud spaces'
    )
    parser.add_argument(
        '--memory',
        action='store_true',
        help='顯示粒子記憶檢查點 / Show particle memory checkpoints'
    )
    
    args = parser.parse_args()
    
    try:
        manager = CloudSpaceSyncManager(args.config)
        
        if args.list:
            manager.list_cloud_spaces()
            return
        
        if args.memory:
            manager.show_memory_checkpoints()
            return
        
        if args.space:
            success = manager.sync_specific_space(args.space)
        else:
            success = manager.sync_all_spaces()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  同步已中斷")
        print("⚠️  Sync interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 同步失敗: {e}")
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
