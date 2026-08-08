"""
Tests for Base Strategy
基礎策略測試
"""

import pytest
from datetime import datetime
from modules.context_management.base_strategy import BaseStrategy, ContextItem


class MockStrategy(BaseStrategy):
    """Mock implementation for testing BaseStrategy"""
    
    def add(self, item: ContextItem) -> None:
        self.context_items.append(item)
    
    def retrieve(self, query=None, limit=10):
        return self.context_items[:limit]
    
    def compress(self):
        # Keep only half of items
        self.context_items = self.context_items[len(self.context_items)//2:]
        return self.context_items


class TestContextItem:
    """Test ContextItem dataclass"""
    
    def test_create_context_item(self):
        """Test creating a context item"""
        item = ContextItem(
            id="test-1",
            content="Test content",
            metadata={"type": "test"},
            priority=5
        )
        
        assert item.id == "test-1"
        assert item.content == "Test content"
        assert item.metadata["type"] == "test"
        assert item.priority == 5
        assert isinstance(item.timestamp, datetime)
    
    def test_context_item_defaults(self):
        """Test default values"""
        item = ContextItem(id="test-2", content="Content")
        
        assert item.metadata == {}
        assert item.priority == 0
        assert isinstance(item.timestamp, datetime)
    
    def test_context_item_validation(self):
        """Test validation"""
        with pytest.raises(ValueError):
            ContextItem(id="", content="test")
        
        with pytest.raises(ValueError):
            ContextItem(id="test", content="")
        
        with pytest.raises(TypeError):
            ContextItem(id="test", content="test", priority="high")


class TestBaseStrategy:
    """Test BaseStrategy abstract class"""
    
    def test_create_strategy(self):
        """Test creating a strategy"""
        strategy = MockStrategy(max_tokens=1000)
        
        assert strategy.max_tokens == 1000
        assert len(strategy.context_items) == 0
    
    def test_invalid_max_tokens(self):
        """Test invalid max_tokens"""
        with pytest.raises(ValueError):
            MockStrategy(max_tokens=0)
        
        with pytest.raises(ValueError):
            MockStrategy(max_tokens=-100)
    
    def test_estimate_tokens(self):
        """Test token estimation"""
        strategy = MockStrategy()
        
        # English text
        english_text = "Hello world, this is a test."
        tokens = strategy.estimate_tokens(english_text)
        assert tokens > 0
        assert tokens < len(english_text)
        
        # Chinese text
        chinese_text = "這是一個測試文本"
        tokens = strategy.estimate_tokens(chinese_text)
        assert tokens > 0
        
        # Mixed text
        mixed_text = "Hello 世界 test 測試"
        tokens = strategy.estimate_tokens(mixed_text)
        assert tokens > 0
    
    def test_add_items(self):
        """Test adding items"""
        strategy = MockStrategy()
        
        item1 = ContextItem(id="1", content="First item")
        item2 = ContextItem(id="2", content="Second item")
        
        strategy.add(item1)
        strategy.add(item2)
        
        assert len(strategy) == 2
        assert strategy.context_items[0] == item1
        assert strategy.context_items[1] == item2
    
    def test_retrieve_items(self):
        """Test retrieving items"""
        strategy = MockStrategy()
        
        items = [
            ContextItem(id=f"{i}", content=f"Content {i}")
            for i in range(5)
        ]
        
        for item in items:
            strategy.add(item)
        
        retrieved = strategy.retrieve(limit=3)
        assert len(retrieved) == 3
    
    def test_compress(self):
        """Test compression"""
        strategy = MockStrategy()
        
        items = [
            ContextItem(id=f"{i}", content=f"Content {i}")
            for i in range(10)
        ]
        
        for item in items:
            strategy.add(item)
        
        assert len(strategy) == 10
        
        compressed = strategy.compress()
        assert len(compressed) == 5
        assert len(strategy) == 5
    
    def test_get_total_tokens(self):
        """Test getting total tokens"""
        strategy = MockStrategy()
        
        strategy.add(ContextItem(id="1", content="Short"))
        strategy.add(ContextItem(id="2", content="This is a longer piece of text"))
        
        total = strategy.get_total_tokens()
        assert total > 0
    
    def test_clear(self):
        """Test clearing all items"""
        strategy = MockStrategy()
        
        for i in range(5):
            strategy.add(ContextItem(id=f"{i}", content=f"Content {i}"))
        
        assert len(strategy) == 5
        
        strategy.clear()
        assert len(strategy) == 0
    
    def test_get_item_by_id(self):
        """Test getting item by ID"""
        strategy = MockStrategy()
        
        item = ContextItem(id="test-123", content="Test content")
        strategy.add(item)
        
        retrieved = strategy.get_item_by_id("test-123")
        assert retrieved == item
        
        not_found = strategy.get_item_by_id("nonexistent")
        assert not_found is None
    
    def test_remove_item(self):
        """Test removing item by ID"""
        strategy = MockStrategy()
        
        item1 = ContextItem(id="1", content="First")
        item2 = ContextItem(id="2", content="Second")
        
        strategy.add(item1)
        strategy.add(item2)
        
        assert len(strategy) == 2
        
        removed = strategy.remove_item("1")
        assert removed is True
        assert len(strategy) == 1
        assert strategy.context_items[0] == item2
        
        not_removed = strategy.remove_item("nonexistent")
        assert not_removed is False
    
    def test_repr(self):
        """Test string representation"""
        strategy = MockStrategy(max_tokens=2000)
        strategy.add(ContextItem(id="1", content="Test"))
        
        repr_str = repr(strategy)
        assert "MockStrategy" in repr_str
        assert "max_tokens=2000" in repr_str
        assert "items=1" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
