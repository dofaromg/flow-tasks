"""
Workspace Strategy for Context Management
工作桌面模式策略

File-based context management using filesystem monitoring.
基於檔案系統監控的上下文管理。

This is the RECOMMENDED strategy: "檔案放工作環境，用「看」不用「記」"
推薦策略：檔案放工作環境，用「看」不用「記」
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import fnmatch
import hashlib

from .base_strategy import BaseStrategy, ContextItem


class WorkspaceStrategy(BaseStrategy):
    """
    工作桌面模式策略 (Workspace Strategy)
    
    Manages context by monitoring and indexing files in a workspace directory.
    透過監控和索引工作區目錄中的檔案來管理上下文。
    
    Key features:
    - File system integration (local + cloud ready)
    - Real-time file monitoring (optional)
    - Smart indexing by file type and modification time
    - Multi-workspace support
    """
    
    def __init__(
        self,
        workspace_path: str,
        max_tokens: int = 4096,
        watch_enabled: bool = False,
        file_patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None
    ):
        """
        Initialize workspace strategy
        
        Args:
            workspace_path: Path to workspace directory
            max_tokens: Maximum tokens to maintain
            watch_enabled: Enable real-time file watching (requires watchdog)
            file_patterns: File patterns to include (e.g., ['*.py', '*.md'])
            ignore_patterns: Patterns to ignore (e.g., ['.*', '__pycache__'])
        """
        super().__init__(max_tokens)
        
        self.workspace_path = Path(workspace_path)
        if not self.workspace_path.exists():
            self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        self.watch_enabled = watch_enabled
        self.file_patterns = file_patterns or ['*']
        self.ignore_patterns = ignore_patterns or [
            '.*', '__pycache__', '*.pyc', 'node_modules', '.git'
        ]
        
        # File index: path -> metadata
        self.file_index: Dict[str, Dict[str, Any]] = {}
        
        # Initial scan
        self.scan_workspace()
        
        # Setup file watcher if enabled
        if watch_enabled:
            self._setup_watcher()
    
    def _setup_watcher(self):
        """
        設定檔案監控 (Setup file watcher)
        
        Note: Requires watchdog library. Falls back gracefully if not available.
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class WorkspaceHandler(FileSystemEventHandler):
                def __init__(self, strategy):
                    self.strategy = strategy
                
                def on_modified(self, event):
                    if not event.is_directory:
                        self.strategy._update_file_index(Path(event.src_path))
                
                def on_created(self, event):
                    if not event.is_directory:
                        self.strategy._update_file_index(Path(event.src_path))
                
                def on_deleted(self, event):
                    if not event.is_directory:
                        rel_path = str(Path(event.src_path).relative_to(self.strategy.workspace_path))
                        if rel_path in self.strategy.file_index:
                            del self.strategy.file_index[rel_path]
            
            self.observer = Observer()
            self.observer.schedule(
                WorkspaceHandler(self),
                str(self.workspace_path),
                recursive=True
            )
            self.observer.start()
            
        except ImportError:
            # Watchdog not available, disable watching
            self.watch_enabled = False
            print("Warning: watchdog library not available, file watching disabled")
    
    def _should_include_file(self, file_path: Path) -> bool:
        """
        Check if file should be included based on patterns
        檢查檔案是否應根據模式包含
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file should be included
        """
        rel_path = str(file_path.relative_to(self.workspace_path))
        
        # Check ignore patterns first
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(file_path.name, pattern):
                return False
        
        # Check include patterns
        for pattern in self.file_patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        
        return False
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file content"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _update_file_index(self, file_path: Path):
        """
        Update index for a single file
        更新單個檔案的索引
        """
        if not file_path.exists() or not file_path.is_file():
            return
        
        if not self._should_include_file(file_path):
            return
        
        try:
            stat = file_path.stat()
            rel_path = str(file_path.relative_to(self.workspace_path))
            
            self.file_index[rel_path] = {
                'absolute_path': str(file_path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': file_path.suffix,
                'hash': self._get_file_hash(file_path)
            }
        except Exception as e:
            print(f"Error indexing file {file_path}: {e}")
    
    def scan_workspace(self) -> None:
        """
        掃描工作區檔案 (Scan workspace files)
        
        Updates the file index with all matching files in the workspace.
        更新檔案索引，包含工作區中所有匹配的檔案。
        """
        self.file_index.clear()
        
        for file_path in self.workspace_path.rglob('*'):
            if file_path.is_file():
                self._update_file_index(file_path)
    
    def add(self, item: ContextItem) -> None:
        """
        新增上下文項目 (Add context item)
        
        In workspace mode, items are typically added via file system.
        This method allows manual addition of virtual context items.
        """
        # Add to context items
        self.context_items.append(item)
        
        # Check if we exceed max tokens
        while self.get_total_tokens() > self.max_tokens and self.context_items:
            # Remove oldest item
            self.context_items.pop(0)
    
    def retrieve(self, query: Optional[str] = None, limit: int = 10) -> List[ContextItem]:
        """
        檢索工作區檔案 (Retrieve workspace files)
        
        Searches for relevant files based on query.
        根據查詢搜尋相關檔案。
        
        Args:
            query: Search query (matches filename, path, or content)
            limit: Maximum number of items to return
            
        Returns:
            List of context items representing files
        """
        results = []
        
        # If no query, return most recently modified files
        if not query:
            sorted_files = sorted(
                self.file_index.items(),
                key=lambda x: x[1]['modified'],
                reverse=True
            )
            
            for rel_path, metadata in sorted_files[:limit]:
                content = self._read_file_content(Path(metadata['absolute_path']))
                if content:
                    results.append(ContextItem(
                        id=f"file:{rel_path}",
                        content=content,
                        metadata={
                            'type': 'file',
                            'path': rel_path,
                            'extension': metadata['extension'],
                            'size': metadata['size'],
                            'modified': metadata['modified'].isoformat()
                        },
                        timestamp=metadata['modified'],
                        priority=1
                    ))
            
            return results
        
        # Search with query
        query_lower = query.lower()
        scored_files = []
        
        # First pass: Score based on filename and extension only
        for rel_path, metadata in self.file_index.items():
            score = 0
            
            # Match filename
            if query_lower in rel_path.lower():
                score += 10
            
            # Match extension
            if query_lower == metadata['extension'].lower().strip('.'):
                score += 5
            
            if score > 0:
                scored_files.append((score, rel_path, metadata))
        
        # Sort by preliminary score
        scored_files.sort(reverse=True, key=lambda x: x[0])
        
        # Second pass: Read content only for top candidates (limit * 2 to account for content matches)
        final_scored_files = []
        for score, rel_path, metadata in scored_files[:limit * 2]:
            content = self._read_file_content(Path(metadata['absolute_path']))
            if content and query_lower in content.lower():
                score += 3
            
            if content:  # Only include if we successfully read content
                final_scored_files.append((score, rel_path, metadata, content))
        
        # Final sort by updated score
        final_scored_files.sort(reverse=True, key=lambda x: x[0])
        
        # Convert to context items
        for score, rel_path, metadata, content in final_scored_files[:limit]:
            if content:
                results.append(ContextItem(
                    id=f"file:{rel_path}",
                    content=content,
                    metadata={
                        'type': 'file',
                        'path': rel_path,
                        'extension': metadata['extension'],
                        'size': metadata['size'],
                        'modified': metadata['modified'].isoformat(),
                        'score': score
                    },
                    timestamp=metadata['modified'],
                    priority=score
                ))
        
        return results
    
    def _read_file_content(self, file_path: Path, max_size: int = 1024 * 100) -> Optional[str]:
        """
        Read file content safely
        安全讀取檔案內容
        
        Args:
            file_path: Path to file
            max_size: Maximum file size to read (bytes)
            
        Returns:
            File content or None if unable to read
        """
        try:
            file_size = file_path.stat().st_size
            if file_size > max_size:
                # File too large, return truncated content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_size)
                    return content + f"\n... (truncated, total size: {file_size} bytes)"
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception:
            return None
    
    def compress(self) -> List[ContextItem]:
        """
        壓縮上下文 (Compress context)
        
        For workspace strategy, compression means keeping only file metadata
        without full content.
        """
        compressed = []
        
        for rel_path, metadata in self.file_index.items():
            # Create lightweight reference without full content
            compressed.append(ContextItem(
                id=f"file:{rel_path}",
                content=f"File: {rel_path} ({metadata['size']} bytes)",
                metadata={
                    'type': 'file_reference',
                    'path': rel_path,
                    'extension': metadata['extension'],
                    'size': metadata['size'],
                    'modified': metadata['modified'].isoformat(),
                    'hash': metadata['hash']
                },
                timestamp=metadata['modified'],
                priority=0
            ))
        
        return compressed
    
    def get_file_count(self) -> int:
        """Get total number of indexed files"""
        return len(self.file_index)
    
    def get_workspace_stats(self) -> Dict[str, Any]:
        """
        Get workspace statistics
        取得工作區統計資訊
        
        Returns:
            Dictionary with workspace statistics
        """
        total_size = sum(meta['size'] for meta in self.file_index.values())
        extensions = {}
        
        for meta in self.file_index.values():
            ext = meta['extension'] or 'no_extension'
            extensions[ext] = extensions.get(ext, 0) + 1
        
        return {
            'total_files': len(self.file_index),
            'total_size_bytes': total_size,
            'file_types': extensions,
            'workspace_path': str(self.workspace_path),
            'watch_enabled': self.watch_enabled
        }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'observer') and self.watch_enabled:
            try:
                self.observer.stop()
                self.observer.join()
            except Exception:
                pass
