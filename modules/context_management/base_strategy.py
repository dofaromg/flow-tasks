"""
Base Strategy for Context Management
上下文管理基礎策略

Defines the abstract interface and data structures for all context management strategies.
定義所有上下文管理策略的抽象介面和資料結構。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass
class ContextItem:
    """
    上下文項目 (Context Item)
    
    Represents a single piece of context with metadata and priority.
    代表單一上下文片段，包含元資料和優先級。
    
    Attributes:
        id: Unique identifier for the context item
        content: The actual content/text
        metadata: Additional metadata (type, tags, source, etc.)
        timestamp: When this item was created
        priority: Priority level (higher = more important)
    """
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0
    
    def __post_init__(self):
        """Validate and normalize fields after initialization"""
        if not self.id:
            raise ValueError("ContextItem id cannot be empty")
        if not self.content:
            raise ValueError("ContextItem content cannot be empty")
        if not isinstance(self.priority, int):
            raise TypeError("Priority must be an integer")


class BaseStrategy(ABC):
    """
    上下文管理策略基礎類別 (Base Context Management Strategy)
    
    Abstract base class defining the interface for all context management strategies.
    抽象基礎類別，定義所有上下文管理策略的介面。
    """
    
    def __init__(self, max_tokens: int = 4096):
        """
        Initialize base strategy
        
        Args:
            max_tokens: Maximum number of tokens to maintain in context
        """
        if max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        self.max_tokens = max_tokens
        self.context_items: List[ContextItem] = []
        self._total_tokens = 0
    
    @abstractmethod
    def add(self, item: ContextItem) -> None:
        """
        新增上下文項目 (Add context item)
        
        Args:
            item: Context item to add
        """
        pass
    
    @abstractmethod
    def retrieve(self, query: Optional[str] = None, limit: int = 10) -> List[ContextItem]:
        """
        檢索相關上下文 (Retrieve relevant context)
        
        Args:
            query: Optional query string for filtering/ranking
            limit: Maximum number of items to return
            
        Returns:
            List of context items, sorted by relevance
        """
        pass
    
    @abstractmethod
    def compress(self) -> List[ContextItem]:
        """
        壓縮上下文 (Compress context)
        
        Reduce the number of context items while preserving important information.
        減少上下文項目數量，同時保留重要資訊。
        
        Returns:
            Compressed list of context items
        """
        pass
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算 token 數量 (Estimate token count)
        
        Simplified token estimation based on character count.
        基於字元數量的簡化 token 估算。
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English
        # For Chinese, 1 token ≈ 1.5-2 characters
        # Use a mixed approach
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        
        # Chinese: ~1.5 chars per token, English: ~4 chars per token
        estimated = (chinese_chars / 1.5) + (other_chars / 4)
        return int(estimated)
    
    def get_total_tokens(self) -> int:
        """
        Get total token count of all context items
        取得所有上下文項目的總 token 數
        
        Returns:
            Total estimated tokens
        """
        return sum(self.estimate_tokens(item.content) for item in self.context_items)
    
    def clear(self) -> None:
        """
        清空所有上下文項目 (Clear all context items)
        """
        self.context_items.clear()
        self._total_tokens = 0
    
    def get_item_by_id(self, item_id: str) -> Optional[ContextItem]:
        """
        通過 ID 取得上下文項目 (Get context item by ID)
        
        Args:
            item_id: ID of the context item
            
        Returns:
            Context item if found, None otherwise
        """
        for item in self.context_items:
            if item.id == item_id:
                return item
        return None
    
    def remove_item(self, item_id: str) -> bool:
        """
        移除指定 ID 的上下文項目 (Remove context item by ID)
        
        Args:
            item_id: ID of the context item to remove
            
        Returns:
            True if item was removed, False if not found
        """
        for i, item in enumerate(self.context_items):
            if item.id == item_id:
                self.context_items.pop(i)
                return True
        return False
    
    def __len__(self) -> int:
        """Return number of context items"""
        return len(self.context_items)
    
    def __repr__(self) -> str:
        """String representation of strategy"""
        return (f"{self.__class__.__name__}(max_tokens={self.max_tokens}, "
                f"items={len(self.context_items)}, "
                f"tokens={self.get_total_tokens()})")
