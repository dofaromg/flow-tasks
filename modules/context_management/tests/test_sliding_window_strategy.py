"""
Tests for Sliding Window Strategy
滑動視窗策略測試
"""

import pytest
from datetime import datetime, timedelta
from modules.context_management.sliding_window_strategy import SlidingWindowStrategy
from modules.context_management.base_strategy import ContextItem


class TestSlidingWindowStrategy:
    """Test SlidingWindowStrategy"""
    
    def test_create_strategy(self):
        """Test creating sliding window strategy"""
        strategy = SlidingWindowStrategy(window_size=10)
        
        assert strategy.window_size == 10
        assert len(strategy.window) == 0
    
    def test_invalid_parameters(self):
        """Test invalid parameters"""
        with pytest.raises(ValueError):
            SlidingWindowStrategy(window_size=0)
        
        with pytest.raises(ValueError):
            SlidingWindowStrategy(window_size=10, overlap_size=10)
        
        with pytest.raises(ValueError):
            SlidingWindowStrategy(window_size=10, overlap_size=-1)
    
    def test_add_items_simple(self):
        """Test adding items (simple FIFO)"""
        strategy = SlidingWindowStrategy(
            window_size=3,
            prioritize_important=False
        )
        
        for i in range(5):
            item = ContextItem(id=f"{i}", content=f"Content {i}")
            strategy.add(item)
        
        # Should only keep last 3 items
        assert len(strategy.window) == 3
        assert strategy.window[-1].id == "4"
        assert strategy.window[0].id == "2"
    
    def test_add_items_priority(self):
        """Test adding items with priority"""
        strategy = SlidingWindowStrategy(
            window_size=3,
            prioritize_important=True
        )
        
        # Add items with different priorities
        strategy.add(ContextItem(id="1", content="Low", priority=1))
        strategy.add(ContextItem(id="2", content="High", priority=10))
        strategy.add(ContextItem(id="3", content="Medium", priority=5))
        strategy.add(ContextItem(id="4", content="Low", priority=1))
        
        # Should keep high priority item
        assert len(strategy.window) == 3
        item_ids = [item.id for item in strategy.window]
        assert "2" in item_ids  # High priority should be kept
    
    def test_retrieve_without_query(self):
        """Test retrieving without query"""
        strategy = SlidingWindowStrategy(window_size=10)
        
        for i in range(5):
            strategy.add(ContextItem(id=f"{i}", content=f"Content {i}"))
        
        results = strategy.retrieve(limit=3)
        assert len(results) == 3
        
        # Should return most recent first
        assert results[0].id == "4"
        assert results[1].id == "3"
    
    def test_retrieve_with_query(self):
        """Test retrieving with query"""
        strategy = SlidingWindowStrategy(window_size=10)
        
        strategy.add(ContextItem(id="1", content="Python code"))
        strategy.add(ContextItem(id="2", content="Java code"))
        strategy.add(ContextItem(id="3", content="Python script"))
        
        results = strategy.retrieve(query="python", limit=10)
        assert len(results) == 2
        assert all("python" in item.content.lower() for item in results)
    
    def test_compress(self):
        """Test compression"""
        strategy = SlidingWindowStrategy(
            window_size=10,
            overlap_size=3
        )
        
        for i in range(10):
            strategy.add(ContextItem(id=f"{i}", content=f"Content {i}"))
        
        assert len(strategy.window) == 10
        
        compressed = strategy.compress()
        assert len(compressed) == 3
        assert len(strategy.window) == 3
    
    def test_compress_no_overlap(self):
        """Test compression with no overlap"""
        strategy = SlidingWindowStrategy(
            window_size=10,
            overlap_size=0
        )
        
        for i in range(5):
            strategy.add(ContextItem(id=f"{i}", content=f"Content {i}"))
        
        compressed = strategy.compress()
        assert len(compressed) == 1
        assert compressed[0].id == "4"  # Most recent
    
    def test_slide_window(self):
        """Test manual window sliding"""
        strategy = SlidingWindowStrategy(
            window_size=10,
            overlap_size=2
        )
        
        for i in range(5):
            strategy.add(ContextItem(id=f"{i}", content=f"Content {i}"))
        
        strategy.slide_window()
        assert len(strategy.window) == 2
    
    def test_get_window_stats(self):
        """Test window statistics"""
        strategy = SlidingWindowStrategy(window_size=10)
        
        for i in range(5):
            strategy.add(ContextItem(
                id=f"{i}",
                content=f"Content {i}",
                priority=i
            ))
        
        stats = strategy.get_window_stats()
        assert stats['size'] == 5
        assert stats['capacity'] == 10
        assert stats['utilization'] == 0.5
        assert stats['avg_priority'] == 2.0
    
    def test_get_items_by_timerange(self):
        """Test getting items by time range"""
        strategy = SlidingWindowStrategy(window_size=10)
        
        now = datetime.now()
        
        for i in range(5):
            item = ContextItem(id=f"{i}", content=f"Content {i}")
            item.timestamp = now + timedelta(hours=i)
            strategy.add(item)
        
        # Get items from hour 2 to 4
        start = now + timedelta(hours=2)
        end = now + timedelta(hours=4)
        
        results = strategy.get_items_by_timerange(start, end)
        assert len(results) == 3  # Hours 2, 3, 4
    
    def test_clear(self):
        """Test clearing window"""
        strategy = SlidingWindowStrategy(window_size=10)
        
        for i in range(5):
            strategy.add(ContextItem(id=f"{i}", content=f"Content {i}"))
        
        assert len(strategy.window) == 5
        
        strategy.clear()
        assert len(strategy.window) == 0
        assert len(strategy.context_items) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
