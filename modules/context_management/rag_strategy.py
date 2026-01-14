"""
RAG Strategy for Context Management
RAG 檢索增強生成策略

Retrieval-Augmented Generation for large document retrieval.
大量文件檢索的檢索增強生成。

Note: This is a lightweight implementation without heavy ML dependencies.
For production use with large datasets, consider integrating sentence-transformers
or other vector database solutions.

注意：這是輕量級實作，不含重型機器學習依賴。
生產環境中處理大型資料集時，建議整合 sentence-transformers 或其他向量資料庫。
"""

from typing import List, Optional, Dict, Any, Tuple
import re
from collections import Counter
import math

from .base_strategy import BaseStrategy, ContextItem


class RAGStrategy(BaseStrategy):
    """
    檢索增強生成策略 (RAG Strategy)
    
    Semantic search and retrieval with hybrid keyword + similarity matching.
    語義搜尋和檢索，混合關鍵字 + 相似度匹配。
    
    Key features:
    - TF-IDF based similarity (lightweight)
    - Hybrid retrieval (keyword + semantic)
    - Reranking mechanism
    - Optional vector database integration (if available)
    
    For better performance, install sentence-transformers:
    pip install sentence-transformers
    """
    
    def __init__(
        self,
        max_tokens: int = 4096,
        use_vector_db: bool = False,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize RAG strategy
        
        Args:
            max_tokens: Maximum tokens to maintain
            use_vector_db: Whether to use vector embeddings (requires sentence-transformers)
            model_name: Name of the sentence transformer model
        """
        super().__init__(max_tokens)
        
        self.use_vector_db = use_vector_db
        self.model_name = model_name
        
        # Document index
        self.doc_index: Dict[str, Dict[str, Any]] = {}
        
        # TF-IDF data
        self.vocabulary: Dict[str, int] = {}  # word -> document frequency
        self.idf_scores: Dict[str, float] = {}
        
        # Vector embeddings (if available)
        self.embeddings: List[List[float]] = []
        self.embedding_model = None
        
        if use_vector_db:
            self._init_vector_db()
    
    def _init_vector_db(self):
        """
        Initialize vector database (sentence-transformers)
        初始化向量資料庫
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(self.model_name)
            print(f"✓ Loaded sentence transformer model: {self.model_name}")
        except ImportError:
            print("Warning: sentence-transformers not available, using TF-IDF fallback")
            self.use_vector_db = False
            self.embedding_model = None
    
    def add(self, item: ContextItem) -> None:
        """
        新增項目並生成嵌入向量 (Add item and generate embeddings)
        
        Adds item to the index and updates TF-IDF or vector embeddings.
        """
        # Add to context items
        self.context_items.append(item)
        
        # Tokenize content
        tokens = self._tokenize(item.content)
        
        # Update vocabulary and document frequency
        unique_tokens = set(tokens)
        for token in unique_tokens:
            self.vocabulary[token] = self.vocabulary.get(token, 0) + 1
        
        # Calculate TF (term frequency) for this document
        tf = Counter(tokens)
        total_terms = len(tokens)
        tf_normalized = {term: count / total_terms for term, count in tf.items()}
        
        # Store in document index
        self.doc_index[item.id] = {
            'item': item,
            'tokens': tokens,
            'tf': tf_normalized,
            'token_count': total_terms
        }
        
        # Generate vector embedding if available
        if self.use_vector_db and self.embedding_model:
            try:
                embedding = self.embedding_model.encode(item.content).tolist()
                self.embeddings.append(embedding)
                self.doc_index[item.id]['embedding_index'] = len(self.embeddings) - 1
            except Exception as e:
                print(f"Warning: Failed to generate embedding: {e}")
        
        # Update IDF scores
        self._update_idf()
        
        # Check token limit
        while self.get_total_tokens() > self.max_tokens and self.context_items:
            # Remove oldest item
            oldest_item = self.context_items.pop(0)
            if oldest_item.id in self.doc_index:
                del self.doc_index[oldest_item.id]
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for indexing
        分詞處理
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Extract words (English and numbers)
        english_words = re.findall(r'\b[a-z0-9]+\b', text)
        
        # Extract Chinese characters
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        
        # Combine and filter
        tokens = english_words + chinese_chars
        
        # Remove stop words (simple version)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                      '的', '了', '是', '在', '有', '和', '與', '或'}
        tokens = [t for t in tokens if t not in stop_words and len(t) > 1]
        
        return tokens
    
    def _update_idf(self):
        """
        Update IDF (Inverse Document Frequency) scores
        更新 IDF 分數
        """
        total_docs = len(self.doc_index)
        
        if total_docs == 0:
            return
        
        for term, doc_freq in self.vocabulary.items():
            # IDF = log(N / df)
            self.idf_scores[term] = math.log(total_docs / doc_freq)
    
    def _calculate_tfidf_similarity(self, query_tokens: List[str], doc_id: str) -> float:
        """
        Calculate TF-IDF similarity between query and document
        計算查詢和文檔之間的 TF-IDF 相似度
        
        Args:
            query_tokens: Tokenized query
            doc_id: Document ID
            
        Returns:
            Similarity score
        """
        if doc_id not in self.doc_index:
            return 0.0
        
        doc_data = self.doc_index[doc_id]
        doc_tf = doc_data['tf']
        
        # Calculate query TF
        query_tf = Counter(query_tokens)
        query_total = len(query_tokens)
        query_tf_normalized = {term: count / query_total for term, count in query_tf.items()}
        
        # Calculate TF-IDF vectors
        score = 0.0
        query_norm = 0.0
        doc_norm = 0.0
        
        for term in set(query_tokens) | set(doc_tf.keys()):
            q_tfidf = query_tf_normalized.get(term, 0) * self.idf_scores.get(term, 0)
            d_tfidf = doc_tf.get(term, 0) * self.idf_scores.get(term, 0)
            
            score += q_tfidf * d_tfidf
            query_norm += q_tfidf ** 2
            doc_norm += d_tfidf ** 2
        
        # Cosine similarity
        if query_norm > 0 and doc_norm > 0:
            return score / (math.sqrt(query_norm) * math.sqrt(doc_norm))
        
        return 0.0
    
    def _calculate_vector_similarity(self, query: str, doc_id: str) -> float:
        """
        Calculate vector embedding similarity
        計算向量嵌入相似度
        
        Args:
            query: Query string
            doc_id: Document ID
            
        Returns:
            Similarity score (cosine similarity)
        """
        if not self.use_vector_db or not self.embedding_model:
            return 0.0
        
        if doc_id not in self.doc_index:
            return 0.0
        
        doc_data = self.doc_index[doc_id]
        if 'embedding_index' not in doc_data:
            return 0.0
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            doc_embedding = self.embeddings[doc_data['embedding_index']]
            
            # Calculate cosine similarity
            dot_product = sum(a * b for a, b in zip(query_embedding, doc_embedding))
            query_norm = math.sqrt(sum(a ** 2 for a in query_embedding))
            doc_norm = math.sqrt(sum(b ** 2 for b in doc_embedding))
            
            if query_norm > 0 and doc_norm > 0:
                return dot_product / (query_norm * doc_norm)
            
        except Exception as e:
            print(f"Warning: Vector similarity calculation failed: {e}")
        
        return 0.0
    
    def _hybrid_search(self, query: str, limit: int = 10) -> List[Tuple[float, str]]:
        """
        Hybrid search combining keyword and semantic similarity
        混合搜尋，結合關鍵字和語義相似度
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of (score, doc_id) tuples
        """
        query_tokens = self._tokenize(query)
        
        scored_docs = []
        
        for doc_id in self.doc_index:
            # TF-IDF score (keyword-based)
            tfidf_score = self._calculate_tfidf_similarity(query_tokens, doc_id)
            
            # Vector similarity score (semantic)
            vector_score = self._calculate_vector_similarity(query, doc_id) if self.use_vector_db else 0.0
            
            # Combine scores (weighted average)
            if self.use_vector_db:
                combined_score = 0.4 * tfidf_score + 0.6 * vector_score
            else:
                combined_score = tfidf_score
            
            # Boost for exact keyword matches
            doc_content_lower = self.doc_index[doc_id]['item'].content.lower()
            if query.lower() in doc_content_lower:
                combined_score += 0.2
            
            scored_docs.append((combined_score, doc_id))
        
        # Sort by score
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        
        return scored_docs[:limit]
    
    def retrieve(self, query: Optional[str] = None, limit: int = 10) -> List[ContextItem]:
        """
        基於語義相似度檢索 (Retrieve by semantic similarity)
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of relevant context items
        """
        if not query:
            # Return most recent items
            return self.context_items[-limit:]
        
        # Perform hybrid search
        scored_docs = self._hybrid_search(query, limit)
        
        # Convert to context items
        results = []
        for score, doc_id in scored_docs:
            if doc_id in self.doc_index:
                item = self.doc_index[doc_id]['item']
                # Update priority based on retrieval score
                item.priority = int(score * 100)
                results.append(item)
        
        # Rerank if needed
        results = self._rerank(results, query)
        
        return results[:limit]
    
    def _rerank(self, items: List[ContextItem], query: str) -> List[ContextItem]:
        """
        Rerank results for better relevance
        重新排序結果以提高相關性
        
        Args:
            items: List of items to rerank
            query: Original query
            
        Returns:
            Reranked list of items
        """
        # Simple reranking: boost items with query in title/metadata
        query_lower = query.lower()
        
        scored_items = []
        for item in items:
            score = item.priority
            
            # Boost for metadata matches
            if 'title' in item.metadata and query_lower in item.metadata['title'].lower():
                score += 20
            
            if 'tags' in item.metadata:
                for tag in item.metadata['tags']:
                    if query_lower in tag.lower():
                        score += 10
            
            scored_items.append((score, item))
        
        # Sort by reranked score
        scored_items.sort(reverse=True, key=lambda x: x[0])
        
        return [item for _, item in scored_items]
    
    def compress(self) -> List[ContextItem]:
        """
        壓縮上下文 (Compress context)
        
        For RAG, compression removes low-priority documents.
        """
        if len(self.context_items) <= 10:
            return self.context_items
        
        # Sort by priority and keep top items
        sorted_items = sorted(self.context_items, key=lambda x: x.priority, reverse=True)
        compressed = sorted_items[:len(sorted_items) // 2]
        
        # Update indices
        self.context_items = compressed
        self.doc_index = {item.id: self.doc_index[item.id] for item in compressed if item.id in self.doc_index}
        
        return compressed
    
    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search statistics
        取得搜尋統計資訊
        """
        return {
            'total_documents': len(self.doc_index),
            'vocabulary_size': len(self.vocabulary),
            'use_vector_db': self.use_vector_db,
            'model_name': self.model_name if self.use_vector_db else None,
            'total_tokens': self.get_total_tokens(),
            'avg_doc_length': sum(d['token_count'] for d in self.doc_index.values()) / len(self.doc_index) if self.doc_index else 0
        }
