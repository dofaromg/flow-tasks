"""
Sliding Window Strategy for Context Management
滑動視窗策略

FIFO-based context management for real-time data streams.
基於 FIFO 的即時資料流上下文管理。
"""

from collections import deque
from typing import List, Optional, Deque
from datetime import datetime

from .base_strategy import BaseStrategy, ContextItem


class SlidingWindowStrategy(BaseStrategy):
    """
    滑動視窗策略 (Sliding Window Strategy)
    
    Maintains a fixed-size window of recent context items.
    維護固定大小的最近上下文項目視窗。
    
    Key features:
    - FIFO queue mechanism
    - Configurable window size
    - Support for overlapping windows
    - Priority-based retention
    """
    
    def __init__(
        self,
        max_tokens: int = 4096,
        window_size: int = 50,
        overlap_size: int = 0,
        prioritize_important: bool = True
    ):
        """
        Initialize sliding window strategy
        
        Args:
            max_tokens: Maximum tokens to maintain
            window_size: Maximum number of items in window
            overlap_size: Number of items to keep when window slides (0 = no overlap)
            prioritize_important: If True, keep high-priority items longer
        """
        super().__init__(max_tokens)
        
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if overlap_size < 0 or overlap_size >= window_size:
            raise ValueError("overlap_size must be between 0 and window_size-1")
        
        self.window_size = window_size
        self.overlap_size = overlap_size
        self.prioritize_important = prioritize_important
        
        # Use deque for efficient FIFO operations
        self.window: Deque[ContextItem] = deque(maxlen=window_size)
    
    def add(self, item: ContextItem) -> None:
        """
        新增上下文項目 (Add context item)
        
        Adds item to window. If window is full, removes oldest item.
        If prioritize_important is True, may keep high-priority items longer.
        """
        if not self.prioritize_important:
            # Simple FIFO
            self.window.append(item)
            self.context_items = list(self.window)
        else:
            # Priority-aware addition
            if len(self.window) < self.window_size:
                self.window.append(item)
            else:
                # Find lowest priority item to remove
                # But prefer older items with same priority
                min_priority = min(i.priority for i in self.window)
                
                # Find oldest item with minimum priority
                for i, existing_item in enumerate(self.window):
                    if existing_item.priority == min_priority:
                        # Remove this item
                        temp_list = list(self.window)
                        temp_list.pop(i)
                        self.window = deque(temp_list, maxlen=self.window_size)
                        break
                
                # Add new item
                self.window.append(item)
            
            self.context_items = list(self.window)
        
        # Check token limit
        while self.get_total_tokens() > self.max_tokens and self.window:
            self.window.popleft()
            self.context_items = list(self.window)
    
    def retrieve(self, query: Optional[str] = None, limit: int = 10) -> List[ContextItem]:
        """
        檢索相關上下文 (Retrieve relevant context)
        
        Returns most recent items, optionally filtered by query.
        返回最近的項目，可選擇按查詢過濾。
        
        Args:
            query: Optional query string for filtering
            limit: Maximum number of items to return
            
        Returns:
            List of context items (most recent first)
        """
        items = list(self.window)
        
        if query:
            # Filter by query
            query_lower = query.lower()
            items = [
                item for item in items
                if query_lower in item.content.lower() or
                   query_lower in str(item.metadata).lower()
            ]
        
        # Return most recent items first
        items.reverse()
        return items[:limit]
    
    def compress(self) -> List[ContextItem]:
        """
        壓縮上下文 (Compress context)
        
        For sliding window, compression keeps only the overlap_size most recent items.
        對於滑動視窗，壓縮僅保留 overlap_size 個最近的項目。
        
        Returns:
            Compressed list of context items
        """
        if self.overlap_size == 0:
            # No overlap, clear all except most recent
            return [list(self.window)[-1]] if self.window else []
        
        # Keep overlap_size most recent items
        items = list(self.window)
        compressed = items[-self.overlap_size:] if len(items) >= self.overlap_size else items
        
        # Update window
        self.window = deque(compressed, maxlen=self.window_size)
        self.context_items = list(self.window)
        
        return compressed
    
    def slide_window(self) -> None:
        """
        手動滑動視窗 (Manually slide window)
        
        Triggers compression to slide the window forward,
        keeping only overlap_size items.
        """
        self.compress()
    
    def get_window_stats(self) -> dict:
        """
        Get window statistics
        取得視窗統計資訊
        
        Returns:
            Dictionary with window statistics
        """
        if not self.window:
            return {
                'size': 0,
                'capacity': self.window_size,
                'utilization': 0.0,
                'total_tokens': 0,
                'avg_priority': 0.0
            }
        
        return {
            'size': len(self.window),
            'capacity': self.window_size,
            'utilization': len(self.window) / self.window_size,
            'total_tokens': self.get_total_tokens(),
            'avg_priority': sum(item.priority for item in self.window) / len(self.window),
            'oldest_timestamp': self.window[0].timestamp.isoformat() if self.window else None,
            'newest_timestamp': self.window[-1].timestamp.isoformat() if self.window else None
        }
    
    def get_items_by_timerange(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[ContextItem]:
        """
        Get items within a time range
        取得時間範圍內的項目
        
        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
            
        Returns:
            List of items within the time range
        """
        results = []
        
        for item in self.window:
            if start_time and item.timestamp < start_time:
                continue
            if end_time and item.timestamp > end_time:
                continue
            results.append(item)
        
        return results
    
    def clear(self) -> None:
        """
        清空視窗 (Clear window)
        
        Removes all items from the window.
        """
        self.window.clear()
        self.context_items.clear()
    
    def __len__(self) -> int:
        """Return number of items in window"""
        return len(self.window)
    
    def __repr__(self) -> str:
        """String representation of strategy"""
        return (f"SlidingWindowStrategy(window_size={self.window_size}, "
                f"items={len(self.window)}, "
                f"tokens={self.get_total_tokens()}, "
                f"overlap={self.overlap_size})")
