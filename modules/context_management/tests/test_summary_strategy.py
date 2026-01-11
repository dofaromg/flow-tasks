"""
Tests for Summary Strategy
摘要壓縮策略測試
"""

import pytest
from modules.context_management.summary_strategy import SummaryStrategy
from modules.context_management.base_strategy import ContextItem


class TestSummaryStrategy:
    """Test SummaryStrategy"""
    
    def test_create_strategy(self):
        """Test creating summary strategy"""
        strategy = SummaryStrategy(summary_ratio=0.3, segment_size=10)
        
        assert strategy.summary_ratio == 0.3
        assert strategy.segment_size == 10
        assert len(strategy.summaries) == 0
        assert len(strategy.recent_items) == 0
    
    def test_invalid_parameters(self):
        """Test invalid parameters"""
        with pytest.raises(ValueError):
            SummaryStrategy(summary_ratio=0)
        
        with pytest.raises(ValueError):
            SummaryStrategy(summary_ratio=1.5)
        
        with pytest.raises(ValueError):
            SummaryStrategy(segment_size=0)
        
        with pytest.raises(ValueError):
            SummaryStrategy(preserve_recent=-1)
    
    def test_add_items(self):
        """Test adding items"""
        strategy = SummaryStrategy(
            segment_size=5,
            preserve_recent=2
        )
        
        for i in range(10):
            item = ContextItem(id=f"{i}", content=f"Content {i}")
            strategy.add(item)
        
        # Should have created summaries
        assert len(strategy.summaries) >= 1
        # Recent items should be preserved (may be more if not enough to compress)
        assert len(strategy.recent_items) >= 2
    
    def test_extractive_summary(self):
        """Test extractive summarization"""
        strategy = SummaryStrategy(
            segment_size=3,
            preserve_recent=0,
            summary_ratio=0.5
        )
        
        # Add items with meaningful content
        items = [
            ContextItem(id="1", content="This is the first important sentence. It contains key information."),
            ContextItem(id="2", content="The second item has 決定 about the project. This is critical."),
            ContextItem(id="3", content="Third item discusses dates like 2025-01-15 and times 10:30.")
        ]
        
        for item in items:
            strategy.add(item)
        
        # Should create a summary
        assert len(strategy.summaries) >= 1
        
        # Summary should contain key information
        summary = strategy.summaries[0]
        assert "摘要" in summary.content or "summary" in summary.content.lower()
    
    def test_retrieve_without_query(self):
        """Test retrieving without query"""
        strategy = SummaryStrategy(segment_size=5, preserve_recent=2)
        
        for i in range(10):
            strategy.add(ContextItem(id=f"{i}", content=f"Content {i}"))
        
        results = strategy.retrieve(limit=5)
        assert len(results) >= 1
    
    def test_retrieve_with_query(self):
        """Test retrieving with query"""
        strategy = SummaryStrategy(segment_size=3, preserve_recent=1)
        
        strategy.add(ContextItem(id="1", content="Python programming"))
        strategy.add(ContextItem(id="2", content="Java development"))
        strategy.add(ContextItem(id="3", content="Python scripting"))
        strategy.add(ContextItem(id="4", content="JavaScript coding"))
        
        results = strategy.retrieve(query="python", limit=10)
        assert len(results) >= 1
    
    def test_compress(self):
        """Test compression"""
        strategy = SummaryStrategy(
            segment_size=3,
            preserve_recent=2
        )
        
        for i in range(15):
            strategy.add(ContextItem(id=f"{i}", content=f"Content {i} " * 10))
        
        initial_count = len(strategy.context_items)
        
        compressed = strategy.compress()
        
        # Should reduce number of items
        assert len(compressed) <= initial_count
    
    def test_key_entity_extraction(self):
        """Test key entity extraction"""
        strategy = SummaryStrategy()
        
        text = "Meeting on 2025-01-15 at 14:30 with John Smith and Mary Johnson. 重要決定 was made."
        entities = strategy._extract_entities(text)
        
        # Should extract dates, times, and names
        assert len(entities) > 0
        assert any("2025-01-15" in str(e) for e in entities)
    
    def test_sentence_scoring(self):
        """Test sentence importance scoring"""
        strategy = SummaryStrategy()
        
        # Sentence with key indicators
        important = "The 重要決定 was made on 2025-01-15 at 14:30."
        score_important = strategy._score_sentence(important)
        
        # Simple sentence
        simple = "This is just a simple sentence."
        score_simple = strategy._score_sentence(simple)
        
        # Important sentence should score higher
        assert score_important > score_simple
    
    def test_compression_stats(self):
        """Test compression statistics"""
        strategy = SummaryStrategy(segment_size=3, preserve_recent=1)
        
        for i in range(10):
            strategy.add(ContextItem(id=f"{i}", content=f"Content {i}"))
        
        stats = strategy.get_compression_stats()
        
        assert 'total_items' in stats
        assert 'summaries' in stats
        assert 'recent_items' in stats
        assert 'compression_ratio' in stats
        assert stats['compression_ratio'] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
