#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
冷儲存管理系統 (Cold Storage Manager)
用於檔案去重、粒子化轉換和冷儲存管理

功能：
- 掃描和識別需要歸檔的檔案
- 檔案內容去重和粒子化轉換
- 創建導引/重定向機制
- 保存完整的檔案記錄
- 不刪除原始檔案
"""

import json
import os
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import re


class ColdStorageManager:
    """冷儲存管理器 - 管理檔案歸檔、去重和粒子化"""
    
    def __init__(
        self,
        source_root: str = ".",
        cold_storage_root: str = "cold_storage",
        manifest_file: str = "cold_storage_manifest.json"
    ):
        """
        初始化冷儲存管理器
        
        Args:
            source_root: 源檔案根目錄
            cold_storage_root: 冷儲存根目錄
            manifest_file: 清單檔案路徑
        """
        self.source_root = Path(source_root).resolve()
        self.cold_storage_root = Path(cold_storage_root).resolve()
        self.manifest_file = Path(manifest_file).resolve()
        
        # 創建冷儲存目錄結構
        self.cold_storage_root.mkdir(parents=True, exist_ok=True)
        (self.cold_storage_root / "particles").mkdir(exist_ok=True)
        (self.cold_storage_root / "metadata").mkdir(exist_ok=True)
        (self.cold_storage_root / "redirects").mkdir(exist_ok=True)
        
        # 載入或創建清單
        self.manifest = self._load_manifest()
        
    def _load_manifest(self) -> Dict[str, Any]:
        """載入檔案清單"""
        if self.manifest_file.exists():
            with open(self.manifest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "files": {},
            "checksums": {},
            "statistics": {
                "total_files": 0,
                "total_size": 0,
                "deduplicated_size": 0
            }
        }
    
    def _save_manifest(self):
        """儲存檔案清單"""
        self.manifest["updated_at"] = datetime.now().isoformat()
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """計算檔案 SHA-256 校驗碼"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _is_archived_file(self, file_path: Path) -> bool:
        """判斷檔案是否需要歸檔（下載檔案、臨時檔案等）"""
        filename = file_path.name
        
        # 檔案名稱模式匹配
        patterns = [
            r'^下載',  # 下載開頭
            r'^點此下載',  # 點此下載開頭
            r'\.tmp$',  # 臨時檔案
            r'\.temp$',
            r'^temp_',
            r'^\.',  # 隱藏檔案（排除 .git 等）
        ]
        
        for pattern in patterns:
            if re.match(pattern, filename):
                return True
        
        return False
    
    def scan_files(self, directory: Optional[Path] = None) -> List[Path]:
        """
        掃描需要歸檔的檔案
        
        Args:
            directory: 要掃描的目錄（預設為 source_root）
            
        Returns:
            需要歸檔的檔案列表
        """
        if directory is None:
            directory = self.source_root
        
        archived_files = []
        
        # 遍歷目錄
        for root, dirs, files in os.walk(directory):
            # 排除特定目錄
            dirs[:] = [d for d in dirs if d not in {
                '.git', 'node_modules', '__pycache__', 
                '.venv', 'venv', 'cold_storage'
            }]
            
            for filename in files:
                file_path = Path(root) / filename
                
                # 檢查是否需要歸檔
                if self._is_archived_file(file_path):
                    archived_files.append(file_path)
        
        return archived_files
    
    def particlize_file(self, file_path: Path) -> Dict[str, Any]:
        """
        將檔案粒子化（轉換為粒子格式）
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            粒子化的檔案資訊
        """
        # 計算校驗碼
        checksum = self._calculate_checksum(file_path)
        
        # 讀取檔案內容
        try:
            if file_path.suffix in {'.txt', '.md', '.json', '.py', '.yaml', '.yml'}:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content_type = 'text'
            else:
                # 對於二進制檔案，不讀取內容到內存（會直接複製檔案）
                content = None
                content_type = 'binary'
        except Exception as e:
            content = None
            content_type = 'error'
            print(f"⚠️  無法讀取檔案 {file_path}: {e}")
        
        # 建立粒子結構
        particle = {
            "particle_id": checksum[:16],
            "checksum": checksum,
            "original_path": str(file_path.relative_to(self.source_root)),
            "filename": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_type": file_path.suffix,
            "content_type": content_type,
            "content": content if content_type == 'text' else None,
            "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            "archived_at": datetime.now().isoformat(),
            "memory_layers": ["structure", "mark", "flow", "recurse", "store"]
        }
        
        return particle
    
    def archive_file(
        self,
        file_path: Path,
        keep_original: bool = True,
        create_redirect: bool = True
    ) -> Dict[str, Any]:
        """
        歸檔單一檔案到冷儲存
        
        Args:
            file_path: 檔案路徑
            keep_original: 是否保留原始檔案（預設 True）
            create_redirect: 是否創建重定向檔案（預設 True）
            
        Returns:
            歸檔結果資訊
        """
        if not file_path.exists():
            raise FileNotFoundError(f"檔案不存在: {file_path}")
        
        # 粒子化檔案
        particle = self.particlize_file(file_path)
        checksum = particle["checksum"]
        
        # 檢查是否已存在（去重）
        if checksum in self.manifest["checksums"]:
            existing_record = self.manifest["checksums"][checksum]
            # 添加到去重記錄中
            if relative_path not in existing_record["occurrences"]:
                existing_record["occurrences"].append(relative_path)
                self._save_manifest()
            result = {
                "status": "deduplicated",
                "checksum": checksum,
                "existing_particle": existing_record["particle_file"],
                "original_path": str(file_path.relative_to(self.source_root))
            }
        else:
            # 儲存粒子到冷儲存
            particle_filename = f"{particle['particle_id']}.particle.json"
            particle_path = self.cold_storage_root / "particles" / particle_filename
            
            # 如果是二進制檔案，複製原始檔案
            if particle["content_type"] == "binary":
                binary_filename = f"{particle['particle_id']}{particle['file_type']}"
                binary_path = self.cold_storage_root / "particles" / binary_filename
                shutil.copy2(file_path, binary_path)
                particle["binary_file"] = str(binary_path.relative_to(self.cold_storage_root))
            
            # 儲存粒子 JSON
            with open(particle_path, 'w', encoding='utf-8') as f:
                json.dump(particle, f, indent=2, ensure_ascii=False)
            
            # 更新清單
            relative_path = str(file_path.relative_to(self.source_root))
            self.manifest["files"][relative_path] = {
                "checksum": checksum,
                "particle_file": str(particle_path.relative_to(self.cold_storage_root)),
                "archived_at": particle["archived_at"],
                "file_size": particle["file_size"]
            }
            
            self.manifest["checksums"][checksum] = {
                "particle_file": str(particle_path.relative_to(self.cold_storage_root)),
                "occurrences": [relative_path]
            }
            
            # 更新統計
            self.manifest["statistics"]["total_files"] += 1
            self.manifest["statistics"]["total_size"] += particle["file_size"]
            
            result = {
                "status": "archived",
                "checksum": checksum,
                "particle_file": str(particle_path.relative_to(self.cold_storage_root)),
                "original_path": relative_path
            }
        
        # 創建重定向檔案
        if create_redirect:
            redirect_path = self.cold_storage_root / "redirects" / f"{particle['particle_id']}.redirect.txt"
            redirect_info = {
                "original_path": str(file_path.relative_to(self.source_root)),
                "particle_id": particle["particle_id"],
                "checksum": checksum,
                "archived_at": datetime.now().isoformat(),
                "note": "此檔案已歸檔至冷儲存。原始檔案保留在源位置。"
            }
            
            with open(redirect_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("冷儲存重定向檔案 (Cold Storage Redirect)\n")
                f.write("=" * 60 + "\n\n")
                for key, value in redirect_info.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
                f.write("如需還原此檔案，請使用冷儲存管理工具。\n")
                f.write("To restore this file, use the cold storage management tool.\n")
        
        # 儲存清單
        self._save_manifest()
        
        return result
    
    def archive_batch(
        self,
        file_paths: List[Path],
        keep_original: bool = True,
        create_redirect: bool = True
    ) -> Dict[str, Any]:
        """
        批次歸檔多個檔案
        
        Args:
            file_paths: 檔案路徑列表
            keep_original: 是否保留原始檔案
            create_redirect: 是否創建重定向檔案
            
        Returns:
            批次歸檔結果
        """
        results = {
            "archived": [],
            "deduplicated": [],
            "errors": []
        }
        
        for file_path in file_paths:
            try:
                result = self.archive_file(file_path, keep_original, create_redirect)
                if result["status"] == "archived":
                    results["archived"].append(result)
                elif result["status"] == "deduplicated":
                    results["deduplicated"].append(result)
            except Exception as e:
                results["errors"].append({
                    "file": str(file_path),
                    "error": str(e)
                })
        
        # 計算去重節省的空間
        deduplicated_size = sum(
            self.manifest["files"][r["original_path"]]["file_size"]
            for r in results["deduplicated"]
            if r["original_path"] in self.manifest["files"]
        )
        
        self.manifest["statistics"]["deduplicated_size"] = deduplicated_size
        self._save_manifest()
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取冷儲存統計資訊"""
        stats = self.manifest["statistics"].copy()
        stats["unique_files"] = len(self.manifest["checksums"])
        stats["total_archived"] = len(self.manifest["files"])
        stats["deduplication_ratio"] = (
            stats["deduplicated_size"] / stats["total_size"]
            if stats["total_size"] > 0 else 0
        )
        return stats
    
    def restore_file(self, original_path: str, target_path: Optional[Path] = None) -> Path:
        """
        從冷儲存還原檔案
        
        Args:
            original_path: 原始檔案路徑（相對於 source_root）
            target_path: 目標還原路徑（可選）
            
        Returns:
            還原的檔案路徑
        """
        if original_path not in self.manifest["files"]:
            raise ValueError(f"檔案未在冷儲存中: {original_path}")
        
        file_info = self.manifest["files"][original_path]
        particle_file = self.cold_storage_root / file_info["particle_file"]
        
        # 載入粒子
        with open(particle_file, 'r', encoding='utf-8') as f:
            particle = json.load(f)
        
        # 確定目標路徑
        if target_path is None:
            target_path = self.source_root / original_path
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 還原檔案
        if particle["content_type"] == "text":
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(particle["content"])
        elif particle["content_type"] == "binary" and "binary_file" in particle:
            binary_path = self.cold_storage_root / particle["binary_file"]
            shutil.copy2(binary_path, target_path)
        else:
            raise ValueError(f"無法還原檔案: {original_path}")
        
        return target_path
    
    def list_archived_files(self) -> List[Dict[str, Any]]:
        """列出所有已歸檔的檔案"""
        files = []
        for path, info in self.manifest["files"].items():
            files.append({
                "path": path,
                "checksum": info["checksum"],
                "size": info["file_size"],
                "archived_at": info["archived_at"]
            })
        return files


def main():
    """主程式：執行互動式冷儲存管理"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方式:")
        print("  python cold_storage_manager.py scan          # 掃描需要歸檔的檔案")
        print("  python cold_storage_manager.py archive       # 歸檔所有掃描到的檔案")
        print("  python cold_storage_manager.py stats         # 顯示統計資訊")
        print("  python cold_storage_manager.py list          # 列出已歸檔檔案")
        return
    
    command = sys.argv[1]
    manager = ColdStorageManager()
    
    if command == "scan":
        print("掃描需要歸檔的檔案...")
        files = manager.scan_files()
        print(f"\n找到 {len(files)} 個檔案需要歸檔:\n")
        for file in files:
            print(f"  - {file.relative_to(manager.source_root)}")
    
    elif command == "archive":
        print("開始歸檔流程...")
        files = manager.scan_files()
        print(f"找到 {len(files)} 個檔案")
        
        if files:
            confirm = input(f"\n確定要歸檔這些檔案嗎？(y/n): ")
            if confirm.lower() == 'y':
                results = manager.archive_batch(files)
                print(f"\n歸檔完成:")
                print(f"  新歸檔: {len(results['archived'])}")
                print(f"  去重: {len(results['deduplicated'])}")
                print(f"  錯誤: {len(results['errors'])}")
    
    elif command == "stats":
        stats = manager.get_statistics()
        print("\n冷儲存統計資訊:")
        print(f"  總檔案數: {stats['total_archived']}")
        print(f"  唯一檔案數: {stats['unique_files']}")
        print(f"  總大小: {stats['total_size'] / 1024 / 1024:.2f} MB")
        print(f"  去重節省: {stats['deduplicated_size'] / 1024 / 1024:.2f} MB")
        print(f"  去重率: {stats['deduplication_ratio'] * 100:.2f}%")
    
    elif command == "list":
        files = manager.list_archived_files()
        print(f"\n已歸檔檔案 ({len(files)} 個):\n")
        for file in files:
            print(f"  - {file['path']}")
            print(f"    大小: {file['size']} bytes")
            print(f"    歸檔時間: {file['archived_at']}")
            print()


if __name__ == "__main__":
    main()
