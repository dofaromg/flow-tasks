#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flow Memory Core Module
記憶系統模組 - 用於管理長期及短期記憶
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import uuid


class MemoryType(Enum):
    """記憶類型"""
    SEMANTIC = "semantic"      # 語義記憶
    EPISODIC = "episodic"      # 情節記憶
    PROCEDURAL = "procedural"  # 程序記憶
    WORKING = "working"        # 工作記憶


@dataclass
class MemoryEntry:
    """記憶條目"""
    entry_id: str
    content: str
    memory_type: MemoryType
    timestamp: str
    tags: List[str]
    metadata: Dict[str, Any]
    
    def __repr__(self):
        return f"MemoryEntry({self.entry_id[:8]}..., {self.memory_type.value})"


class FlowMemoryCore:
    """
    記憶核心系統 - 管理長期記憶、短期記憶及工作記憶
    """
    
    def __init__(self):
        """初始化記憶系統"""
        self.long_term_memory: List[MemoryEntry] = []
        self.short_term_memory: List[MemoryEntry] = []
        self.working_memory: List[MemoryEntry] = []
    
    def commit(
        self, 
        content: str, 
        memory_type: MemoryType = MemoryType.SEMANTIC,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        提交記憶到系統
        
        Args:
            content: 記憶內容
            memory_type: 記憶類型
            tags: 標籤列表
            metadata: 附加元資料
            
        Returns:
            包含 entry_id 的字典
        """
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        entry = MemoryEntry(
            entry_id=entry_id,
            content=content,
            memory_type=memory_type,
            timestamp=timestamp,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # 根據記憶類型存儲
        if memory_type == MemoryType.WORKING:
            self.working_memory.append(entry)
        else:
            self.long_term_memory.append(entry)
        
        return {
            'entry_id': entry_id,
            'timestamp': timestamp,
            'memory_type': memory_type.value
        }
    
    def recall(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """
        回憶搜索
        
        Args:
            query: 搜索查詢
            limit: 返回結果數量上限
            
        Returns:
            匹配的記憶條目列表
        """
        results = []
        query_lower = query.lower()
        
        # 搜索長期記憶
        for entry in self.long_term_memory:
            if query_lower in entry.content.lower():
                results.append(entry)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """
        獲取記憶系統狀態
        
        Returns:
            包含系統狀態的字典
        """
        return {
            'long_term_memory_size': len(self.long_term_memory),
            'short_term_memory_size': len(self.short_term_memory),
            'working_memory_size': len(self.working_memory),
            'total_entries': len(self.long_term_memory) + len(self.short_term_memory) + len(self.working_memory)
        }
    
    def clear_working_memory(self):
        """清除工作記憶"""
        self.working_memory.clear()
    
    def consolidate_short_term(self):
        """將短期記憶整合到長期記憶"""
        self.long_term_memory.extend(self.short_term_memory)
        self.short_term_memory.clear()
