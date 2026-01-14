#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRLiou 記憶封存種子系統 (Memory Archive Seed System)
用於封存、壓縮與還原粒子語言記憶狀態
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from functools import lru_cache


# Checksum caching helpers
def _make_hashable_mas(obj: Any) -> Union[Tuple, Any]:
    """Convert an object to a hashable representation for caching."""
    if isinstance(obj, dict):
        return tuple(sorted((k, _make_hashable_mas(v)) for k, v in obj.items()))
    elif isinstance(obj, list):
        return tuple(_make_hashable_mas(item) for item in obj)
    return obj


def _reconstruct_mas(hashable_data: Union[Tuple, Any]) -> Any:
    """Reconstruct original data structure from hashable format."""
    if isinstance(hashable_data, tuple):
        # Check if it looks like dict items (tuple of key-value pairs)
        if hashable_data and isinstance(hashable_data[0], tuple) and len(hashable_data[0]) == 2:
            return {k: _reconstruct_mas(v) for k, v in hashable_data}
        else:
            return [_reconstruct_mas(item) for item in hashable_data]
    return hashable_data


@lru_cache(maxsize=256)
def _cached_checksum_mas(hashable_data: Tuple) -> str:
    """Cached checksum calculation for repeated data."""
    # Reconstruct data from hashable format for JSON serialization
    reconstructed = _reconstruct_mas(hashable_data)
    data_str = json.dumps(reconstructed, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()


class MemoryArchiveSeed:
    """記憶封存種子核心類別"""
    
    def __init__(self, storage_path: str = "memory_seeds"):
        """
        初始化記憶封存系統
        
        Args:
            storage_path: 記憶種子儲存路徑
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # 記憶層級定義
        self.memory_layers = {
            "structure": "結構層 - 基礎資料結構定義",
            "mark": "標記層 - 邏輯跳點與節奏標記",
            "flow": "流程層 - 執行流程與節奏結構",
            "recurse": "遞歸層 - 細部展開與嵌套邏輯",
            "store": "封存層 - 最終記憶封存狀態"
        }
        
    def create_seed(
        self,
        particle_data: Any,
        metadata: Optional[Dict] = None,
        seed_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        創建記憶封存種子
        
        Args:
            particle_data: 要封存的粒子資料
            metadata: 額外的元資料
            seed_name: 種子名稱（可選）
            
        Returns:
            記憶種子資訊
        """
        timestamp = datetime.now()
        
        # 生成種子名稱
        if seed_name is None:
            seed_name = f"memory_seed_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # 創建記憶種子結構
        seed = {
            "seed_name": seed_name,
            "version": "1.0",
            "created_at": timestamp.isoformat(),
            "particle_data": particle_data,
            "metadata": metadata or {},
            "memory_layers": self._compress_to_layers(particle_data),
            "checksum": self._generate_checksum(particle_data)
        }
        
        # 儲存種子
        seed_file = self.storage_path / f"{seed_name}.mseed.json"
        with open(seed_file, 'w', encoding='utf-8') as seed_output_file:
            json.dump(seed, seed_output_file, indent=2, ensure_ascii=False)
        
        return {
            "seed_name": seed_name,
            "seed_file": str(seed_file),
            "checksum": seed["checksum"],
            "created_at": seed["created_at"]
        }
    
    def restore_seed(self, seed_name: str) -> Dict[str, Any]:
        """
        還原記憶封存種子
        
        Args:
            seed_name: 種子名稱
            
        Returns:
            還原的記憶資料
        """
        seed_file = self.storage_path / f"{seed_name}.mseed.json"
        
        if not seed_file.exists():
            raise FileNotFoundError(f"記憶種子不存在: {seed_name}")
        
        with open(seed_file, 'r', encoding='utf-8') as seed_input_file:
            seed = json.load(seed_input_file)
        
        # 驗證完整性
        current_checksum = self._generate_checksum(seed["particle_data"])
        if current_checksum != seed["checksum"]:
            raise ValueError(f"記憶種子完整性驗證失敗: {seed_name}")
        
        return seed
    
    def compress_seed(self, seed_name: str) -> str:
        """
        壓縮記憶種子為 .flpkg 格式
        
        Args:
            seed_name: 種子名稱
            
        Returns:
            壓縮後的種子字串
        """
        seed = self.restore_seed(seed_name)
        layers = seed["memory_layers"]
        
        # 建構壓縮格式
        compressed = f"MEMORY_SEED({seed_name}) = "
        nested = "X"
        
        for layer in layers:
            nested = f"{layer.upper()}({nested})"
        
        compressed += nested
        
        return compressed
    
    def list_seeds(self) -> List[Dict[str, Any]]:
        """
        列出所有記憶種子
        
        Returns:
            種子資訊列表
        """
        seeds = []
        
        for seed_file in self.storage_path.glob("*.mseed.json"):
            with open(seed_file, 'r', encoding='utf-8') as f:
                seed = json.load(f)
                seeds.append({
                    "seed_name": seed["seed_name"],
                    "created_at": seed["created_at"],
                    "checksum": seed["checksum"],
                    "file": str(seed_file)
                })
        
        return sorted(seeds, key=lambda x: x["created_at"], reverse=True)
    
    def merge_seeds(
        self,
        seed_names: List[str],
        merged_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        合併多個記憶種子
        
        Args:
            seed_names: 要合併的種子名稱列表
            merged_name: 合併後的種子名稱
            
        Returns:
            合併後的種子資訊
        """
        if not seed_names:
            raise ValueError("至少需要一個種子來合併")
        
        # 載入所有種子
        seeds = [self.restore_seed(name) for name in seed_names]
        
        # 合併粒子資料
        merged_data = {
            "merged_from": seed_names,
            "merged_at": datetime.now().isoformat(),
            "particles": []
        }
        
        for seed in seeds:
            if isinstance(seed["particle_data"], list):
                merged_data["particles"].extend(seed["particle_data"])
            else:
                merged_data["particles"].append(seed["particle_data"])
        
        # 創建合併後的種子
        if merged_name is None:
            merged_name = f"merged_seed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return self.create_seed(
            particle_data=merged_data,
            metadata={"type": "merged", "source_count": len(seed_names)},
            seed_name=merged_name
        )
    
    def export_seed(self, seed_name: str, export_path: Optional[str] = None) -> str:
        """
        匯出記憶種子為可分享格式
        
        Args:
            seed_name: 種子名稱
            export_path: 匯出路徑
            
        Returns:
            匯出檔案路徑
        """
        seed = self.restore_seed(seed_name)
        
        if export_path is None:
            export_path = f"{seed_name}_export.json"
        
        # 加入匯出資訊
        export_data = {
            **seed,
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "format_version": "1.0",
                "compatible_with": "MRLiou Particle Language Core v1.0+"
            }
        }
        
        with open(export_path, 'w', encoding='utf-8') as export_output_file:
            json.dump(export_data, export_output_file, indent=2, ensure_ascii=False)
        
        return export_path
    
    def import_seed(self, import_path: str) -> Dict[str, Any]:
        """
        匯入記憶種子
        
        Args:
            import_path: 匯入檔案路徑
            
        Returns:
            匯入的種子資訊
        """
        with open(import_path, 'r', encoding='utf-8') as import_input_file:
            import_data = json.load(import_input_file)
        
        # 驗證格式
        if "seed_name" not in import_data:
            raise ValueError("無效的記憶種子格式")
        
        # 重新創建種子
        return self.create_seed(
            particle_data=import_data["particle_data"],
            metadata=import_data.get("metadata", {}),
            seed_name=import_data["seed_name"]
        )
    
    def _compress_to_layers(self, particle_data: Any) -> List[str]:
        """
        將粒子資料壓縮為記憶層級
        
        Args:
            particle_data: 粒子資料
            
        Returns:
            記憶層級列表
        """
        # 標準五層結構
        return ["structure", "mark", "flow", "recurse", "store"]
    
    def _generate_checksum(self, data: Any) -> str:
        """
        生成資料校驗碼（帶快取優化）
        
        Args:
            data: 要校驗的資料
            
        Returns:
            校驗碼
        """
        try:
            hashable = _make_hashable_mas(data)
            return _cached_checksum_mas(hashable)
        except (TypeError, AttributeError):
            # Fallback for non-hashable or complex data
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
            return hashlib.sha256(data_str.encode('utf-8')).hexdigest()


def interactive_demo():
    """互動式示範"""
    print("=== MRLiou 記憶封存種子系統 ===\n")
    
    archive = MemoryArchiveSeed()
    
    while True:
        print("\n選項:")
        print("1. 創建記憶種子")
        print("2. 還原記憶種子")
        print("3. 列出所有種子")
        print("4. 壓縮種子")
        print("5. 合併種子")
        print("6. 匯出種子")
        print("7. 匯入種子")
        print("q. 離開")
        
        choice = input("\n請選擇功能: ").strip()
        
        if choice == "1":
            data = input("請輸入要封存的資料: ")
            seed_name = input("請輸入種子名稱（留空自動生成）: ").strip() or None
            result = archive.create_seed(data, seed_name=seed_name)
            print(f"\n✅ 記憶種子已創建:")
            print(f"   名稱: {result['seed_name']}")
            print(f"   檔案: {result['seed_file']}")
            print(f"   校驗碼: {result['checksum'][:16]}...")
            
        elif choice == "2":
            seed_name = input("請輸入種子名稱: ").strip()
            try:
                seed = archive.restore_seed(seed_name)
                print(f"\n✅ 記憶種子已還原:")
                print(f"   名稱: {seed['seed_name']}")
                print(f"   創建時間: {seed['created_at']}")
                print(f"   資料: {seed['particle_data']}")
            except (FileNotFoundError, ValueError) as e:
                print(f"\n❌ 錯誤: {e}")
            
        elif choice == "3":
            seeds = archive.list_seeds()
            if not seeds:
                print("\n目前沒有記憶種子")
            else:
                print(f"\n找到 {len(seeds)} 個記憶種子:")
                for seed in seeds:
                    print(f"  - {seed['seed_name']} (創建於 {seed['created_at']})")
            
        elif choice == "4":
            seed_name = input("請輸入種子名稱: ").strip()
            try:
                compressed = archive.compress_seed(seed_name)
                print(f"\n✅ 壓縮結果:")
                print(f"   {compressed}")
            except (FileNotFoundError, ValueError) as e:
                print(f"\n❌ 錯誤: {e}")
            
        elif choice == "5":
            seeds_input = input("請輸入要合併的種子名稱（用逗號分隔）: ").strip()
            seed_names = [s.strip() for s in seeds_input.split(",") if s.strip()]
            merged_name = input("請輸入合併後的名稱（留空自動生成）: ").strip() or None
            try:
                result = archive.merge_seeds(seed_names, merged_name)
                print(f"\n✅ 種子已合併:")
                print(f"   名稱: {result['seed_name']}")
                print(f"   檔案: {result['seed_file']}")
            except (FileNotFoundError, ValueError) as e:
                print(f"\n❌ 錯誤: {e}")
            
        elif choice == "6":
            seed_name = input("請輸入種子名稱: ").strip()
            try:
                export_path = archive.export_seed(seed_name)
                print(f"\n✅ 種子已匯出至: {export_path}")
            except (FileNotFoundError, ValueError) as e:
                print(f"\n❌ 錯誤: {e}")
            
        elif choice == "7":
            import_path = input("請輸入匯入檔案路徑: ").strip()
            try:
                result = archive.import_seed(import_path)
                print(f"\n✅ 種子已匯入:")
                print(f"   名稱: {result['seed_name']}")
                print(f"   檔案: {result['seed_file']}")
            except (FileNotFoundError, ValueError) as e:
                print(f"\n❌ 錯誤: {e}")
            
        elif choice == "q":
            print("\n感謝使用！")
            break
        else:
            print("\n❌ 無效的選項")


def main():
    """主函數"""
    print("=== MRLiou 記憶封存種子系統示範 ===\n")
    
    # 創建記憶封存系統
    archive = MemoryArchiveSeed()
    
    # 示範：創建記憶種子
    print("1. 創建記憶種子:")
    test_data = {
        "text": "Hello, MRLiou Particle Language!",
        "logic_chain": ["structure", "mark", "flow", "recurse", "store"],
        "metadata": {
            "author": "MRLiou",
            "purpose": "記憶封存測試"
        }
    }
    
    result1 = archive.create_seed(
        particle_data=test_data,
        metadata={"type": "test", "version": "1.0"},
        seed_name="test_seed_001"
    )
    print(f"   ✅ 種子已創建: {result1['seed_name']}")
    print(f"   檔案: {result1['seed_file']}")
    print(f"   校驗碼: {result1['checksum'][:16]}...\n")
    
    # 示範：還原記憶種子
    print("2. 還原記憶種子:")
    restored = archive.restore_seed("test_seed_001")
    print(f"   ✅ 種子已還原: {restored['seed_name']}")
    print(f"   資料: {restored['particle_data']['text']}\n")
    
    # 示範：壓縮種子
    print("3. 壓縮記憶種子:")
    compressed = archive.compress_seed("test_seed_001")
    print(f"   ✅ 壓縮格式: {compressed}\n")
    
    # 示範：列出所有種子
    print("4. 列出所有記憶種子:")
    seeds = archive.list_seeds()
    for seed in seeds:
        print(f"   - {seed['seed_name']} (創建於 {seed['created_at']})")
    print()
    
    # 示範：匯出種子
    print("5. 匯出記憶種子:")
    export_path = archive.export_seed("test_seed_001")
    print(f"   ✅ 已匯出至: {export_path}\n")
    
    print("=== 示範完成 ===")
    print("\n執行 'python memory_archive_seed.py' 進入互動模式")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_demo()
    else:
        main()
