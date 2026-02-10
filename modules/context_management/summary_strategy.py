"""
Summary Strategy for Context Management
摘要壓縮策略

Long conversation compression with key information retention.
長對話壓縮，保留關鍵資訊。

Integrates with particle compression logic from particle_core.
整合粒子壓縮核心邏輯。
"""

from typing import List, Optional, Dict, Any, Set
from datetime import datetime
import re
import sys
from pathlib import Path

from .base_strategy import BaseStrategy, ContextItem


class SummaryStrategy(BaseStrategy):
    """
    摘要壓縮策略 (Summary Compression Strategy)
    
    Compresses long conversations into summaries while preserving key information.
    將長對話壓縮為摘要，同時保留關鍵資訊。
    
    Key features:
    - Sliding window segmentation
    - Key information extraction (names, dates, decisions)
    - Multi-level summarization (summary of summaries)
    - Integration with particle compressor logic
    """
    
    def __init__(
        self,
        max_tokens: int = 4096,
        summary_ratio: float = 0.3,
        segment_size: int = 10,
        preserve_recent: int = 5
    ):
        """
        Initialize summary strategy
        
        Args:
            max_tokens: Maximum tokens to maintain
            summary_ratio: Target ratio for compression (0.3 = 30% of original)
            segment_size: Number of items per segment for summarization
            preserve_recent: Number of recent items to keep uncompressed
        """
        super().__init__(max_tokens)
        
        if not 0 < summary_ratio <= 1:
            raise ValueError("summary_ratio must be between 0 and 1")
        if segment_size <= 0:
            raise ValueError("segment_size must be positive")
        if preserve_recent < 0:
            raise ValueError("preserve_recent must be non-negative")
        
        self.summary_ratio = summary_ratio
        self.segment_size = segment_size
        self.preserve_recent = preserve_recent
        
        # Storage for summaries and original items
        self.summaries: List[ContextItem] = []
        self.recent_items: List[ContextItem] = []
        
        # Load particle compression if available
        self._init_particle_compressor()
    
    def _init_particle_compressor(self):
        """
        Initialize particle compressor from particle_core
        初始化粒子壓縮器
        """
        try:
            # Add particle_core to path
            particle_core_path = Path(__file__).parent.parent.parent / "particle_core" / "src"
            if particle_core_path.exists() and str(particle_core_path) not in sys.path:
                sys.path.insert(0, str(particle_core_path))
            
            from logic_pipeline import LogicPipeline
            self.particle_pipeline = LogicPipeline()
            self.use_particle = True
        except ImportError:
            self.particle_pipeline = None
            self.use_particle = False
    
    def add(self, item: ContextItem) -> None:
        """
        新增上下文項目 (Add context item)
        
        Adds item to recent items. Triggers compression if needed.
        """
        self.recent_items.append(item)
        self.context_items.append(item)
        
        # Trigger compression if we have enough items
        if len(self.recent_items) >= self.segment_size + self.preserve_recent:
            self._compress_segment()
        
        # Check token limit
        while self.get_total_tokens() > self.max_tokens:
            if len(self.summaries) > 1:
                # Merge oldest summaries
                self._merge_summaries()
            elif len(self.recent_items) > self.preserve_recent:
                # Compress more recent items
                self._compress_segment()
            else:
                # Last resort: remove oldest summary
                if self.summaries:
                    self.summaries.pop(0)
                else:
                    break
    
    def _compress_segment(self) -> None:
        """
        Compress a segment of recent items into a summary
        將最近項目的片段壓縮為摘要
        """
        if len(self.recent_items) <= self.preserve_recent:
            return
        
        # Take items to compress (all except preserve_recent)
        items_to_compress = self.recent_items[:-self.preserve_recent] if self.preserve_recent > 0 else self.recent_items
        
        if not items_to_compress:
            return
        
        # Create summary
        summary_content = self._create_summary(items_to_compress)
        
        # Extract metadata from items
        start_time = items_to_compress[0].timestamp
        end_time = items_to_compress[-1].timestamp
        avg_priority = sum(item.priority for item in items_to_compress) / len(items_to_compress)
        
        # Create summary item
        summary_item = ContextItem(
            id=f"summary_{start_time.isoformat()}_{end_time.isoformat()}",
            content=summary_content,
            metadata={
                'type': 'summary',
                'original_count': len(items_to_compress),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'compression_method': 'particle' if self.use_particle else 'extractive',
                'key_entities': self._extract_key_entities(items_to_compress)
            },
            timestamp=datetime.now(),
            priority=int(avg_priority)
        )
        
        self.summaries.append(summary_item)
        
        # Remove compressed items from recent_items
        self.recent_items = self.recent_items[-self.preserve_recent:] if self.preserve_recent > 0 else []
        
        # Update context_items
        self.context_items = self.summaries + self.recent_items
    
    def _create_summary(self, items: List[ContextItem]) -> str:
        """
        Create summary from items
        從項目建立摘要
        
        Uses particle compression if available, otherwise uses extractive method.
        """
        if self.use_particle and self.particle_pipeline:
            # Use particle compression logic
            combined_content = "\n".join(item.content for item in items)
            
            # Apply particle compression principles
            # Structure -> Mark -> Flow -> Recurse -> Store
            compressed_result = self.particle_pipeline.compress_logic(
                self.particle_pipeline.pipeline_steps
            )
            
            # Create human-readable summary
            summary = f"【粒子摘要】({len(items)} 項目)\n"
            summary += f"壓縮形式: {compressed_result}\n"
            summary += f"關鍵內容: {self._extract_key_content(combined_content)}"
            
            return summary
        else:
            # Use extractive summarization
            return self._extractive_summary(items)
    
    def _extractive_summary(self, items: List[ContextItem]) -> str:
        """
        Create extractive summary (simple version)
        建立抽取式摘要（簡化版）
        """
        # Combine all content
        all_content = " ".join(item.content for item in items)
        
        # Extract key sentences
        sentences = re.split(r'[。！？\.\!\?]\s*', all_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        # Calculate target length
        target_count = max(1, int(len(sentences) * self.summary_ratio))
        
        # Score sentences by importance
        scored_sentences = []
        for sentence in sentences:
            score = self._score_sentence(sentence)
            scored_sentences.append((score, sentence))
        
        # Sort by score and take top sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        top_sentences = [s for _, s in scored_sentences[:target_count]]
        
        summary = f"【摘要】({len(items)} 項目壓縮)\n"
        summary += " ".join(top_sentences)
        
        return summary
    
    def _score_sentence(self, sentence: str) -> float:
        """
        Score sentence importance
        評分句子重要性
        """
        score = 0.0
        
        # Check for key indicators
        key_patterns = [
            (r'\d{4}-\d{2}-\d{2}', 2.0),  # Dates
            (r'\d+:\d+', 1.5),  # Times
            (r'[A-Z][a-z]+', 1.0),  # Proper nouns (English)
            (r'決定|決策|完成|實作|建立|創建', 2.0),  # Decision/action words
            (r'重要|關鍵|必須|需要', 1.5),  # Importance markers
            (r'\d+', 0.5),  # Numbers
        ]
        
        for pattern, weight in key_patterns:
            matches = len(re.findall(pattern, sentence))
            score += matches * weight
        
        # Longer sentences (up to a point) are more informative
        score += min(len(sentence) / 50, 2.0)
        
        return score
    
    def _extract_key_content(self, text: str, max_length: int = 200) -> str:
        """Extract key content from text"""
        # Extract first sentence and key entities
        sentences = re.split(r'[。！？\.\!\?]\s*', text)
        first_sentence = sentences[0] if sentences else text[:100]
        
        entities = self._extract_entities(text)
        entities_str = ", ".join(entities[:5]) if entities else ""
        
        result = first_sentence
        if entities_str:
            result += f" | 關鍵: {entities_str}"
        
        if len(result) > max_length:
            result = result[:max_length] + "..."
        
        return result
    
    def _extract_key_entities(self, items: List[ContextItem]) -> List[str]:
        """
        Extract key entities from items
        從項目中提取關鍵實體
        """
        combined_text = " ".join(item.content for item in items)
        return self._extract_entities(combined_text)
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract entities from text (simple version)
        從文本中提取實體（簡化版）
        """
        entities: Set[str] = set()
        
        # Extract dates
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', text)
        entities.update(dates)
        
        # Extract times
        times = re.findall(r'\d{1,2}:\d{2}', text)
        entities.update(times)
        
        # Extract capitalized words (likely proper nouns)
        proper_nouns = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
        entities.update(proper_nouns[:10])  # Limit to 10
        
        # Extract Chinese names (simplified)
        chinese_names = re.findall(r'[\u4e00-\u9fff]{2,4}(?:先生|女士|老師|博士)?', text)
        entities.update(chinese_names[:5])
        
        return list(entities)
    
    def _merge_summaries(self) -> None:
        """
        Merge multiple summaries into a higher-level summary
        將多個摘要合併為更高層次的摘要
        """
        if len(self.summaries) < 2:
            return
        
        # Take first two summaries
        items_to_merge = self.summaries[:2]
        merged_content = self._create_summary(items_to_merge)
        
        # Create merged summary
        start_time = items_to_merge[0].timestamp
        end_time = items_to_merge[-1].timestamp
        
        merged_item = ContextItem(
            id=f"merged_summary_{start_time.isoformat()}",
            content=merged_content,
            metadata={
                'type': 'merged_summary',
                'original_summaries': len(items_to_merge),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'level': 2
            },
            timestamp=datetime.now(),
            priority=max(item.priority for item in items_to_merge)
        )
        
        # Replace first two summaries with merged one
        self.summaries = [merged_item] + self.summaries[2:]
        
        # Update context_items
        self.context_items = self.summaries + self.recent_items
    
    def retrieve(self, query: Optional[str] = None, limit: int = 10) -> List[ContextItem]:
        """
        檢索相關上下文 (Retrieve relevant context)
        
        Returns summaries and recent items, optionally filtered by query.
        """
        all_items = self.summaries + self.recent_items
        
        if not query:
            # Return most recent items
            return all_items[-limit:]
        
        # Search with query
        query_lower = query.lower()
        scored_items = []
        
        for item in all_items:
            score = 0
            
            # Match in content
            if query_lower in item.content.lower():
                score += 5
            
            # Match in key entities
            if 'key_entities' in item.metadata:
                for entity in item.metadata['key_entities']:
                    if query_lower in entity.lower():
                        score += 3
            
            # Recent items get priority boost
            if item in self.recent_items:
                score += 2
            
            if score > 0:
                scored_items.append((score, item))
        
        # Sort by score
        scored_items.sort(reverse=True, key=lambda x: x[0])
        
        return [item for _, item in scored_items[:limit]]
    
    def compress(self) -> List[ContextItem]:
        """
        壓縮上下文 (Compress context)
        
        Triggers aggressive compression of all items.
        """
        # Compress all recent items
        while len(self.recent_items) > self.preserve_recent:
            self._compress_segment()
        
        # Merge summaries if needed
        while len(self.summaries) > 5:
            self._merge_summaries()
        
        return self.summaries + self.recent_items
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """
        Get compression statistics
        取得壓縮統計資訊
        """
        total_items = len(self.context_items)
        summary_count = len(self.summaries)
        recent_count = len(self.recent_items)
        
        original_count = sum(
            item.metadata.get('original_count', 1)
            for item in self.summaries
        ) + recent_count
        
        compression_ratio = total_items / original_count if original_count > 0 else 1.0
        
        return {
            'total_items': total_items,
            'summaries': summary_count,
            'recent_items': recent_count,
            'original_count': original_count,
            'compression_ratio': compression_ratio,
            'use_particle_compression': self.use_particle,
            'total_tokens': self.get_total_tokens()
        }
