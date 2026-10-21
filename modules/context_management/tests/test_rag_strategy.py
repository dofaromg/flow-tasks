"""
Tests for RAG Strategy
RAG 策略測試
"""

import pytest
from modules.context_management.rag_strategy import RAGStrategy
from modules.context_management.base_strategy import ContextItem


class TestRAGStrategy:
    """Test RAGStrategy"""
    
    def test_create_strategy(self):
        """Test creating RAG strategy"""
        strategy = RAGStrategy(use_vector_db=False)
        
        assert strategy.use_vector_db is False
        assert len(strategy.doc_index) == 0
    
    def test_add_items(self):
        """Test adding items"""
        strategy = RAGStrategy(use_vector_db=False)
        
        item1 = ContextItem(id="1", content="Python programming language")
        item2 = ContextItem(id="2", content="Java development framework")
        
        strategy.add(item1)
        strategy.add(item2)
        
        assert len(strategy.doc_index) == 2
        assert "1" in strategy.doc_index
        assert "2" in strategy.doc_index
    
    def test_tokenization(self):
        """Test text tokenization"""
        strategy = RAGStrategy()
        
        # English text
        english = "Hello world, this is a test."
        tokens = strategy._tokenize(english)
        assert len(tokens) > 0
        assert "hello" in tokens
        assert "world" in tokens
        
        # Chinese text
        chinese = "這是一個測試文本"
        tokens = strategy._tokenize(chinese)
        assert len(tokens) > 0
        
        # Mixed text
        mixed = "Hello 世界 test 測試"
        tokens = strategy._tokenize(mixed)
        assert len(tokens) > 0
    
    def test_tfidf_similarity(self):
        """Test TF-IDF similarity calculation"""
        strategy = RAGStrategy(use_vector_db=False)
        
        strategy.add(ContextItem(id="1", content="Python programming language"))
        strategy.add(ContextItem(id="2", content="Java programming language"))
        strategy.add(ContextItem(id="3", content="Machine learning with Python"))
        
        # Calculate similarity
        query_tokens = strategy._tokenize("Python programming")
        similarity = strategy._calculate_tfidf_similarity(query_tokens, "1")
        
        assert 0 <= similarity <= 1
    
    def test_retrieve_without_query(self):
        """Test retrieving without query"""
        strategy = RAGStrategy(use_vector_db=False)
        
        for i in range(5):
            strategy.add(ContextItem(id=f"{i}", content=f"Document {i} content"))
        
        results = strategy.retrieve(limit=3)
        assert len(results) == 3
    
    def test_retrieve_with_query(self):
        """Test retrieving with query"""
        strategy = RAGStrategy(use_vector_db=False)
        
        strategy.add(ContextItem(id="1", content="Python programming tutorial"))
        strategy.add(ContextItem(id="2", content="Java development guide"))
        strategy.add(ContextItem(id="3", content="Python data science"))
        strategy.add(ContextItem(id="4", content="JavaScript web development"))
        
        results = strategy.retrieve(query="Python", limit=10)
        
        # Should return Python-related items first
        assert len(results) >= 2
        # Check if Python items are ranked higher
        python_items = [r for r in results if "Python" in r.content]
        assert len(python_items) >= 2
    
    def test_hybrid_search(self):
        """Test hybrid search"""
        strategy = RAGStrategy(use_vector_db=False)
        
        strategy.add(ContextItem(id="1", content="Machine learning algorithms"))
        strategy.add(ContextItem(id="2", content="Deep learning networks"))
        strategy.add(ContextItem(id="3", content="Reinforcement learning"))
        
        results = strategy._hybrid_search("learning", limit=10)
        
        # All documents contain "learning"
        assert len(results) == 3
        
        # Results should be sorted by score
        scores = [score for score, _ in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_compress(self):
        """Test compression"""
        strategy = RAGStrategy(use_vector_db=False)
        
        for i in range(20):
            item = ContextItem(
                id=f"{i}",
                content=f"Document {i}",
                priority=i  # Increasing priority
            )
            strategy.add(item)
        
        assert len(strategy.context_items) == 20
        
        compressed = strategy.compress()
        
        # Should reduce number of items
        assert len(compressed) < 20
        assert len(strategy.context_items) == len(compressed)
    
    def test_reranking(self):
        """Test reranking mechanism"""
        strategy = RAGStrategy(use_vector_db=False)
        
        item1 = ContextItem(
            id="1",
            content="Content about Python",
            metadata={"title": "Python Guide"}
        )
        item2 = ContextItem(
            id="2",
            content="Content about Python",
            metadata={"title": "Other Topic"}
        )
        
        item1.priority = 50
        item2.priority = 50
        
        # Rerank with query "Python"
        reranked = strategy._rerank([item1, item2], "Python")
        
        # Item with "Python" in title should rank higher
        assert reranked[0].id == "1"
    
    def test_search_stats(self):
        """Test search statistics"""
        strategy = RAGStrategy(use_vector_db=False)
        
        for i in range(5):
            strategy.add(ContextItem(id=f"{i}", content=f"Document {i} with content"))
        
        stats = strategy.get_search_stats()
        
        assert stats['total_documents'] == 5
        assert stats['vocabulary_size'] > 0
        assert stats['use_vector_db'] is False
        assert stats['avg_doc_length'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
