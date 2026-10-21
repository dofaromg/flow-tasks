"""
Hybrid Strategy for Context Management
混合策略

Stackable combination of multiple strategies for flexible context management.
可堆疊組合多種策略，靈活管理上下文。
"""

from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict

from .base_strategy import BaseStrategy, ContextItem


class HybridStrategy(BaseStrategy):
    """
    混合策略 (Hybrid Strategy)
    
    Combines multiple strategies with configurable weights and routing.
    組合多種策略，可配置權重和路由。
    
    Key features:
    - Strategy pipeline (chaining)
    - Dynamic weight adjustment
    - Strategy routing based on query type
    - Fallback mechanisms
    """
    
    def __init__(
        self,
        strategies: List[BaseStrategy],
        weights: Optional[List[float]] = None,
        routing_rules: Optional[Dict[str, str]] = None
    ):
        """
        Initialize hybrid strategy
        
        Args:
            strategies: List of strategies to combine
            weights: Optional weights for each strategy (default: equal weights)
            routing_rules: Optional routing rules (query_pattern -> strategy_name)
        """
        if not strategies:
            raise ValueError("At least one strategy must be provided")
        
        # Use max_tokens from first strategy
        super().__init__(strategies[0].max_tokens)
        
        self.strategies = strategies
        
        # Set weights (default to equal weights)
        if weights is None:
            weights = [1.0] * len(strategies)
        
        if len(weights) != len(strategies):
            raise ValueError("Number of weights must match number of strategies")
        
        # Normalize weights
        total_weight = sum(weights)
        self.weights = [w / total_weight for w in weights]
        
        # Routing rules (optional)
        self.routing_rules = routing_rules or {}
        
        # Track which strategy each item came from
        self.item_sources: Dict[str, int] = {}  # item_id -> strategy_index
    
    def add(self, item: ContextItem) -> None:
        """
        新增上下文項目 (Add context item)
        
        Adds item to all strategies (or routes to specific strategy).
        將項目新增到所有策略（或路由到特定策略）。
        """
        # Add to all strategies
        for strategy in self.strategies:
            strategy.add(item)
        
        # Also add to our own list
        self.context_items.append(item)
        
        # Track total tokens across all strategies
        while self.get_total_tokens() > self.max_tokens:
            # Trigger compression on all strategies
            for strategy in self.strategies:
                strategy.compress()
            
            # If still over limit, remove oldest item
            if self.context_items:
                oldest = self.context_items.pop(0)
                if oldest.id in self.item_sources:
                    del self.item_sources[oldest.id]
    
    def retrieve(self, query: Optional[str] = None, limit: int = 10) -> List[ContextItem]:
        """
        從多個策略檢索並合併結果 (Retrieve from multiple strategies and merge)
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Merged and ranked results from all strategies
        """
        # Route to specific strategy if rule matches
        if query and self.routing_rules:
            for pattern, strategy_name in self.routing_rules.items():
                if pattern.lower() in query.lower():
                    # Find matching strategy
                    for i, strategy in enumerate(self.strategies):
                        if strategy.__class__.__name__ == strategy_name:
                            return strategy.retrieve(query, limit)
        
        # Retrieve from all strategies
        all_results: List[Tuple[int, ContextItem]] = []
        
        for i, (strategy, weight) in enumerate(zip(self.strategies, self.weights)):
            try:
                results = strategy.retrieve(query, limit)
                
                # Add weighted results
                for j, item in enumerate(results):
                    # Calculate score: weight * position_score
                    position_score = (limit - j) / limit
                    final_score = weight * position_score * 100
                    
                    # Track source
                    self.item_sources[item.id] = i
                    
                    all_results.append((final_score, item))
                    
            except Exception as e:
                print(f"Warning: Strategy {strategy.__class__.__name__} failed: {e}")
                continue
        
        # Merge results by ID (avoid duplicates)
        merged: Dict[str, Tuple[float, ContextItem]] = {}
        
        for score, item in all_results:
            if item.id in merged:
                # Keep higher score
                if score > merged[item.id][0]:
                    merged[item.id] = (score, item)
            else:
                merged[item.id] = (score, item)
        
        # Sort by score and return top items
        sorted_results = sorted(merged.values(), key=lambda x: x[0], reverse=True)
        
        return [item for _, item in sorted_results[:limit]]
    
    def compress(self) -> List[ContextItem]:
        """
        壓縮上下文 (Compress context)
        
        Triggers compression on all strategies and merges results.
        觸發所有策略的壓縮並合併結果。
        """
        compressed_results: List[ContextItem] = []
        
        for strategy in self.strategies:
            try:
                compressed = strategy.compress()
                compressed_results.extend(compressed)
            except Exception as e:
                print(f"Warning: Strategy {strategy.__class__.__name__} compression failed: {e}")
        
        # Remove duplicates by ID
        seen_ids = set()
        unique_results = []
        
        for item in compressed_results:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                unique_results.append(item)
        
        # Update context_items
        self.context_items = unique_results
        
        return unique_results
    
    def adjust_weights(self, new_weights: List[float]) -> None:
        """
        動態調整權重 (Dynamically adjust weights)
        
        Args:
            new_weights: New weights for strategies
        """
        if len(new_weights) != len(self.strategies):
            raise ValueError("Number of weights must match number of strategies")
        
        # Normalize weights
        total_weight = sum(new_weights)
        self.weights = [w / total_weight for w in new_weights]
    
    def add_strategy(self, strategy: BaseStrategy, weight: float = 1.0) -> None:
        """
        新增策略 (Add a new strategy)
        
        Args:
            strategy: Strategy to add
            weight: Weight for the new strategy
        """
        self.strategies.append(strategy)
        
        # Recalculate weights
        current_total = sum(self.weights) * len(self.weights)
        new_total = current_total + weight
        
        self.weights = [w * (current_total / new_total) for w in self.weights]
        self.weights.append(weight / new_total)
    
    def remove_strategy(self, index: int) -> None:
        """
        移除策略 (Remove a strategy)
        
        Args:
            index: Index of strategy to remove
        """
        if index < 0 or index >= len(self.strategies):
            raise ValueError(f"Invalid strategy index: {index}")
        
        self.strategies.pop(index)
        self.weights.pop(index)
        
        # Renormalize weights
        if self.weights:
            total_weight = sum(self.weights)
            self.weights = [w / total_weight for w in self.weights]
    
    def get_strategy_performance(self) -> Dict[str, Any]:
        """
        Get performance metrics for each strategy
        取得各策略的效能指標
        
        Returns:
            Dictionary with performance metrics
        """
        performance = {}
        
        for i, strategy in enumerate(self.strategies):
            strategy_name = strategy.__class__.__name__
            
            # Count items from this strategy
            item_count = sum(1 for source_idx in self.item_sources.values() if source_idx == i)
            
            performance[strategy_name] = {
                'weight': self.weights[i],
                'items_retrieved': item_count,
                'total_items': len(strategy.context_items),
                'total_tokens': strategy.get_total_tokens(),
                'utilization': item_count / len(strategy.context_items) if strategy.context_items else 0
            }
        
        return performance
    
    def get_strategy_by_name(self, name: str) -> Optional[BaseStrategy]:
        """
        Get strategy by class name
        根據類別名稱取得策略
        
        Args:
            name: Strategy class name
            
        Returns:
            Strategy instance or None
        """
        for strategy in self.strategies:
            if strategy.__class__.__name__ == name:
                return strategy
        return None
    
    def clear_all(self) -> None:
        """
        Clear all strategies
        清空所有策略
        """
        for strategy in self.strategies:
            strategy.clear()
        
        self.context_items.clear()
        self.item_sources.clear()
    
    def get_total_tokens(self) -> int:
        """
        Get total tokens across all strategies
        取得所有策略的總 token 數
        
        Returns:
            Total tokens (may include duplicates)
        """
        # Return unique tokens from context_items
        return sum(self.estimate_tokens(item.content) for item in self.context_items)
    
    def __repr__(self) -> str:
        """String representation"""
        strategy_names = [s.__class__.__name__ for s in self.strategies]
        return (f"HybridStrategy(strategies={strategy_names}, "
                f"weights={[f'{w:.2f}' for w in self.weights]}, "
                f"items={len(self.context_items)})")
