#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Quick Mount System
記憶快速掛載系統

Provides particle compression and memory state management
for cross-language persistence framework.

Features:
- Particle-level data compression
- Memory snapshot/restore
- Context mounting and management
- Integration with wire protocol
"""

import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import cache system
try:
    # Prefer absolute import to avoid context-dependent relative import issues
    from particle_core.src.memory.memory_cache_disk import MemoryCacheDiskMapper
    CACHE_AVAILABLE = True
except ImportError:
    try:
        # Fallback to local-style import for backward compatibility
        from memory_cache_disk import MemoryCacheDiskMapper
        CACHE_AVAILABLE = True
    except ImportError:
        CACHE_AVAILABLE = False


class ParticleCompressor:
    """
    基礎粒子壓縮器 (Basic Particle Compressor)
    
    Provides foundational particle-based compression logic
    for reducing data footprint while maintaining semantic integrity.
    """
    
    def __init__(self):
        self.compression_stats = {
            "original_size": 0,
            "compressed_size": 0,
            "ratio": 0.0
        }
    
    def compress(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress data using particle logic
        
        Args:
            data: Dictionary to compress
            
        Returns:
            Compressed representation
        """
        if not isinstance(data, dict):
            return data
        
        # Calculate original size
        original = json.dumps(data, ensure_ascii=False)
        self.compression_stats["original_size"] = len(original)
        
        # Basic compression: Extract keys and values
        compressed = {
            "_particle_type": "basic",
            "_keys": list(data.keys()),
            "_values": list(data.values()),
            "_timestamp": datetime.now().isoformat()
        }
        
        # Calculate compressed size
        compressed_str = json.dumps(compressed, ensure_ascii=False)
        self.compression_stats["compressed_size"] = len(compressed_str)
        self.compression_stats["ratio"] = (
            1.0 - (self.compression_stats["compressed_size"] / 
                   self.compression_stats["original_size"])
        ) if self.compression_stats["original_size"] > 0 else 0.0
        
        return compressed
    
    def decompress(self, compressed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompress particle data back to original structure
        
        Args:
            compressed: Compressed particle representation
            
        Returns:
            Original data structure
        """
        if not isinstance(compressed, dict):
            return compressed
        
        if compressed.get("_particle_type") == "basic":
            # Reconstruct from keys and values
            keys = compressed.get("_keys", [])
            values = compressed.get("_values", [])
            return dict(zip(keys, values))
        
        return compressed
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        return self.compression_stats.copy()


class AdvancedParticleCompressor(ParticleCompressor):
    """
    進階遞迴壓縮器 (Advanced Recursive Compressor)
    
    Extends basic compression with recursive particle logic
    and semantic preservation.
    """
    
    def __init__(self):
        super().__init__()
        self.particle_registry = {}
    
    def compress(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Advanced compression with recursive particle extraction
        
        Args:
            data: Dictionary to compress
            
        Returns:
            Advanced compressed representation
        """
        if not isinstance(data, dict):
            return data
        
        # Calculate original size
        original = json.dumps(data, ensure_ascii=False)
        self.compression_stats["original_size"] = len(original)
        
        # Generate particle hash
        particle_hash = hashlib.sha256(original.encode('utf-8')).hexdigest()[:16]
        
        # Advanced compression with nested structure handling
        particles = []
        for key, value in data.items():
            particle = {
                "k": key,
                "v": value if not isinstance(value, dict) else self._compress_nested(value),
                "t": type(value).__name__
            }
            particles.append(particle)
        
        compressed = {
            "_particle_type": "advanced",
            "_hash": particle_hash,
            "_particles": particles,
            "_timestamp": datetime.now().isoformat()
        }
        
        # Store in registry
        self.particle_registry[particle_hash] = compressed
        
        # Calculate compressed size
        compressed_str = json.dumps(compressed, ensure_ascii=False)
        self.compression_stats["compressed_size"] = len(compressed_str)
        self.compression_stats["ratio"] = (
            1.0 - (self.compression_stats["compressed_size"] / 
                   self.compression_stats["original_size"])
        ) if self.compression_stats["original_size"] > 0 else 0.0
        
        return compressed
    
    def _compress_nested(self, data: Dict[str, Any]) -> str:
        """Recursively compress nested structures"""
        return json.dumps(data, ensure_ascii=False)
    
    def decompress(self, compressed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompress advanced particle data
        
        Args:
            compressed: Compressed particle representation
            
        Returns:
            Original data structure
        """
        if not isinstance(compressed, dict):
            return compressed
        
        if compressed.get("_particle_type") == "advanced":
            # Reconstruct from particles
            result = {}
            for particle in compressed.get("_particles", []):
                key = particle["k"]
                value = particle["v"]
                value_type = particle.get("t", "str")
                
                # Handle nested structures
                if value_type == "dict" and isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except:
                        pass
                
                result[key] = value
            
            return result
        
        # Fallback to basic decompression
        return super().decompress(compressed)


class MemoryQuickMounter:
    """
    記憶快速掛載管理器 (Memory Quick Mount Manager)
    
    Manages memory seeds, snapshots, and context mounting
    for persistent state management.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Memory Quick Mounter
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.compressor = AdvancedParticleCompressor()
        self.context_dir = Path(self.config.get("context_dir", "particle_core/context"))
        self.snapshot_dir = Path(self.config.get("snapshot_dir", "particle_core/snapshots"))
        
        # Create directories if they don't exist
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        self.mounted_seeds = []
        
        # Initialize cache system
        if CACHE_AVAILABLE:
            self.cache_mapper = MemoryCacheDiskMapper(self.config)
        else:
            self.cache_mapper = None
            print("⚠ Cache system not available")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.json'):
                    return json.load(f)
                elif config_path.endswith(('.yaml', '.yml')):
                    try:
                        import yaml
                        return yaml.safe_load(f)
                    except ImportError:
                        print("⚠ YAML support requires PyYAML. Using defaults.")
                        return {}
        
        # Default configuration
        return {
            "context_dir": "particle_core/context",
            "snapshot_dir": "particle_core/snapshots",
            "seeds": []
        }
    
    def mount(self, seed_paths: Optional[List[str]] = None):
        """
        掛載記憶種子 (Mount memory seeds)
        
        Args:
            seed_paths: List of seed file paths to mount
        """
        if seed_paths is None:
            seed_paths = self.config.get("seeds", [])
        
        print(f"📌 Mounting {len(seed_paths)} memory seed(s)...")
        
        for seed_path in seed_paths:
            path = Path(seed_path)
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        seed_data = json.load(f)
                    
                    self.mounted_seeds.append({
                        "path": str(path),
                        "data": seed_data,
                        "mounted_at": datetime.now().isoformat()
                    })
                    
                    print(f"  ✓ Mounted: {path.name}")
                except Exception as e:
                    print(f"  ✗ Failed to mount {path.name}: {e}")
            else:
                print(f"  ⚠ Seed not found: {seed_path}")
        
        print(f"✓ Total mounted seeds: {len(self.mounted_seeds)}")
    
    def snapshot(self, agent_name: str, state: Dict[str, Any]) -> str:
        """
        建立狀態快照 (Create state snapshot)
        
        Args:
            agent_name: Name of the agent
            state: Current state to snapshot
            
        Returns:
            Path to the snapshot file
        """
        print(f"📸 Creating snapshot for agent: {agent_name}")
        
        # Compress state
        compressed = self.compressor.compress(state)
        
        # Generate snapshot filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = f"{agent_name}_{timestamp}.snapshot.json"
        snapshot_path = self.snapshot_dir / snapshot_name
        
        # Save snapshot
        snapshot_data = {
            "agent": agent_name,
            "timestamp": timestamp,
            "state": state,
            "compressed": compressed,
            "stats": self.compressor.get_stats()
        }
        
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
        
        stats = self.compressor.get_stats()
        print(f"  ✓ Snapshot saved: {snapshot_path.name}")
        print(f"  📊 Compression ratio: {stats['ratio']:.2%}")
        
        return str(snapshot_path)
    
    def rehydrate(self, snapshot_path: Optional[str] = None) -> Dict[str, Any]:
        """
        恢復上下文 (Rehydrate context from snapshot)
        
        Args:
            snapshot_path: Path to snapshot file (uses latest if None)
            
        Returns:
            Restored state
        """
        if snapshot_path is None:
            # Find latest snapshot
            snapshots = list(self.snapshot_dir.glob("*.snapshot.json"))
            if not snapshots:
                print("⚠ No snapshots found")
                return {}
            snapshot_path = max(snapshots, key=lambda p: p.stat().st_mtime)
        
        print(f"💧 Rehydrating from: {Path(snapshot_path).name}")
        
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            snapshot_data = json.load(f)
        
        # Decompress state
        compressed = snapshot_data.get("compressed", {})
        restored_state = self.compressor.decompress(compressed)
        
        print(f"  ✓ Restored state for agent: {snapshot_data.get('agent', 'unknown')}")
        print(f"  📅 Snapshot timestamp: {snapshot_data.get('timestamp', 'unknown')}")
        
        return restored_state
    
    def get_cached_state(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get state from cache (cache-aware access)
        從快取取得狀態
        
        Args:
            key: State identifier
            
        Returns:
            Cached state or None
        """
        if not self.cache_mapper:
            return None
        
        cached = self.cache_mapper.get_state(key)
        if cached:
            print(f"💾 Cache hit: {key}")
        else:
            print(f"⚠ Cache miss: {key}")
        
        return cached
    
    def set_cached_state(self, key: str, state: Dict[str, Any]):
        """
        Set state in cache
        設定快取狀態
        
        Args:
            key: State identifier
            state: State data
        """
        if not self.cache_mapper:
            print("⚠ Cache not available")
            return
        
        self.cache_mapper.set_state(key, state)
        print(f"💾 Cached: {key}")
    
    def snapshot_with_cache(self, agent_name: str, state: Dict[str, Any]) -> str:
        """
        Create snapshot and cache it
        建立快照並快取
        
        Args:
            agent_name: Name of the agent
            state: Current state to snapshot
            
        Returns:
            Path to the snapshot file
        """
        # Create snapshot
        snapshot_path = self.snapshot(agent_name, state)
        
        # Cache the state
        if self.cache_mapper:
            cache_key = f"agent:{agent_name}"
            self.cache_mapper.set_state(cache_key, state)
            print(f"  💾 State cached for quick access")
        
        return snapshot_path
    
    def rehydrate_with_cache(self, snapshot_path: Optional[str] = None, 
                            agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Rehydrate with cache lookup
        從快取或快照恢復
        
        Args:
            snapshot_path: Path to snapshot file (uses latest if None)
            agent_name: Agent name for cache lookup
            
        Returns:
            Restored state
        """
        # Try cache first if agent_name provided
        if agent_name and self.cache_mapper:
            cache_key = f"agent:{agent_name}"
            cached_state = self.cache_mapper.get_state(cache_key)
            if cached_state:
                print(f"💾 Restored from cache: {agent_name}")
                return cached_state
        
        # Fall back to snapshot
        restored = self.rehydrate(snapshot_path)
        
        # Cache for next time
        if agent_name and self.cache_mapper and restored:
            cache_key = f"agent:{agent_name}"
            self.cache_mapper.set_state(cache_key, restored)
        
        return restored
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        取得快取統計
        
        Returns:
            Cache statistics dictionary
        """
        if not self.cache_mapper:
            return {"enabled": False, "message": "Cache not available"}
        
        return self.cache_mapper.get_cache_stats()
    
    def persist_cache(self):
        """
        Manually persist cache to disk
        手動持久化快取
        """
        if self.cache_mapper:
            self.cache_mapper.persist()
        else:
            print("⚠ Cache not available")
    
    def shutdown(self):
        """
        Shutdown and cleanup
        關閉並清理
        """
        if self.cache_mapper:
            print("🛑 Shutting down cache system...")
            self.cache_mapper.shutdown()


def main():
    """CLI entry point for Memory Quick Mount"""
    parser = argparse.ArgumentParser(
        description="Memory Quick Mount System - 記憶快速掛載系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mount memory seeds
  python memory_quick_mount.py --config config.yaml mount
  
  # Create snapshot
  python memory_quick_mount.py snapshot --agent test_agent --state '{"key": "value"}'
  
  # Rehydrate latest snapshot
  python memory_quick_mount.py rehydrate
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Mount command
    mount_parser = subparsers.add_parser('mount', help='Mount memory seeds')
    
    # Snapshot command
    snapshot_parser = subparsers.add_parser('snapshot', help='Create state snapshot')
    snapshot_parser.add_argument('--agent', required=True, help='Agent name')
    snapshot_parser.add_argument('--state', required=True, help='State data (JSON string)')
    
    # Rehydrate command
    rehydrate_parser = subparsers.add_parser('rehydrate', help='Restore from snapshot')
    rehydrate_parser.add_argument('--snapshot', help='Snapshot file path (uses latest if not specified)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize mounter
    mqm = MemoryQuickMounter(args.config)
    
    # Execute command
    if args.command == 'mount':
        mqm.mount()
    elif args.command == 'snapshot':
        try:
            state = json.loads(args.state)
        except json.JSONDecodeError:
            print("✗ Invalid JSON state")
            return
        mqm.snapshot(args.agent, state)
    elif args.command == 'rehydrate':
        restored = mqm.rehydrate(args.snapshot)
        print(f"\nRestored state:")
        print(json.dumps(restored, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
