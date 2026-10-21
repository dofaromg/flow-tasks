"""
Routing Engine
智能路由引擎

實現動態路由選擇、負載均衡、QoS保證
Implements dynamic routing, load balancing, QoS guarantee
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from rich.console import Console

console = Console()


class RoutingStrategy(Enum):
    """路由策略"""
    SHORTEST_PATH = "shortest_path"
    LEAST_LOADED = "least_loaded"
    HIGHEST_BANDWIDTH = "highest_bandwidth"
    LOWEST_LATENCY = "lowest_latency"
    BALANCED = "balanced"


@dataclass
class RoutingMetrics:
    """路由指標"""
    latency_ms: float
    bandwidth_available_gbps: float
    reliability: float
    hop_count: int
    load: float
    
    def calculate_score(self, weights: dict) -> float:
        """
        計算路由得分
        
        Args:
            weights: 各指標權重
            
        Returns:
            綜合得分（越低越好）
        """
        score = (
            self.latency_ms * weights.get("latency", 0.4) +
            (100 - self.bandwidth_available_gbps) * weights.get("bandwidth", 0.3) +
            (1.0 - self.reliability) * 100 * weights.get("reliability", 0.2) +
            self.hop_count * 10 * weights.get("hop_count", 0.1) +
            self.load * 50 * weights.get("load", 0.3)
        )
        return score


class RoutingEngine:
    """
    智能路由引擎
    
    特性：
    - 多種路由策略
    - 動態權重調整
    - QoS 保證
    - 路徑緩存
    - 負載感知
    """
    
    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.BALANCED):
        self.strategy = strategy
        self.path_cache: Dict[Tuple[str, str], Tuple[List[str], float]] = {}  # (source, dest) -> (path, timestamp)
        self.cache_ttl = 30  # seconds
        
        # Routing weights for balanced strategy
        self.routing_weights = {
            "latency": 0.4,
            "bandwidth": 0.3,
            "reliability": 0.2,
            "hop_count": 0.1,
            "load": 0.3
        }
        
        # Statistics
        self.total_routes_calculated = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        console.print(f"[bold blue]Routing Engine initialized with strategy: {strategy.value}[/bold blue]")
    
    def calculate_best_route(
        self,
        source: str,
        destination: str,
        available_paths: List[List[str]],
        path_metrics: Dict[str, RoutingMetrics]
    ) -> Optional[List[str]]:
        """
        計算最佳路由
        
        Args:
            source: 源節點
            destination: 目標節點
            available_paths: 可用路徑列表
            path_metrics: 每條路徑的指標
            
        Returns:
            最佳路徑，如果沒有返回None
        """
        # Check cache first
        cache_key = (source, destination)
        if cache_key in self.path_cache:
            cached_path, cached_time = self.path_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                self.cache_hits += 1
                console.print(f"[dim]Using cached route for {source} → {destination}[/dim]")
                return cached_path
        
        self.cache_misses += 1
        
        if not available_paths:
            return None
        
        # Select best path based on strategy
        best_path = None
        best_score = float('inf')
        
        for path in available_paths:
            path_key = "->".join(path)
            if path_key not in path_metrics:
                continue
            
            metrics = path_metrics[path_key]
            
            if self.strategy == RoutingStrategy.SHORTEST_PATH:
                score = metrics.hop_count
            elif self.strategy == RoutingStrategy.LEAST_LOADED:
                score = metrics.load
            elif self.strategy == RoutingStrategy.HIGHEST_BANDWIDTH:
                score = -metrics.bandwidth_available_gbps  # Negative for maximization
            elif self.strategy == RoutingStrategy.LOWEST_LATENCY:
                score = metrics.latency_ms
            else:  # BALANCED
                score = metrics.calculate_score(self.routing_weights)
            
            if score < best_score:
                best_score = score
                best_path = path
        
        # Cache the result
        if best_path:
            self.path_cache[cache_key] = (best_path, time.time())
            self.total_routes_calculated += 1
            console.print(f"[green]Calculated best route: {' → '.join(best_path)} (score: {best_score:.2f})[/green]")
        
        return best_path
    
    def update_routing_weights(self, weights: dict) -> None:
        """
        更新路由權重
        
        Args:
            weights: 新的權重配置
        """
        self.routing_weights.update(weights)
        # Clear cache when weights change
        self.path_cache.clear()
        console.print(f"[yellow]Routing weights updated: {self.routing_weights}[/yellow]")
    
    def set_strategy(self, strategy: RoutingStrategy) -> None:
        """
        設置路由策略
        
        Args:
            strategy: 新策略
        """
        self.strategy = strategy
        self.path_cache.clear()
        console.print(f"[yellow]Routing strategy changed to: {strategy.value}[/yellow]")
    
    def invalidate_cache(self, source: Optional[str] = None, destination: Optional[str] = None) -> int:
        """
        使緩存失效
        
        Args:
            source: 源節點（可選）
            destination: 目標節點（可選）
            
        Returns:
            清除的緩存條目數
        """
        if source is None and destination is None:
            count = len(self.path_cache)
            self.path_cache.clear()
            console.print(f"[yellow]Cleared all {count} cached routes[/yellow]")
            return count
        
        keys_to_remove = []
        for key in self.path_cache:
            src, dst = key
            if (source is None or src == source) and (destination is None or dst == destination):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.path_cache[key]
        
        console.print(f"[yellow]Invalidated {len(keys_to_remove)} cached routes[/yellow]")
        return len(keys_to_remove)
    
    def get_statistics(self) -> dict:
        """獲取統計信息"""
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "strategy": self.strategy.value,
            "total_routes_calculated": self.total_routes_calculated,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "cached_routes": len(self.path_cache),
            "routing_weights": self.routing_weights
        }


# 示例使用
if __name__ == "__main__":
    def demo():
        # 創建路由引擎
        router = RoutingEngine(strategy=RoutingStrategy.BALANCED)
        
        # 定義可用路徑
        available_paths = [
            ["geo-001", "meo-001", "leo-001", "ground-001"],
            ["geo-001", "meo-002", "leo-002", "ground-001"],
            ["geo-001", "meo-001", "meo-002", "leo-001", "ground-001"],
        ]
        
        # 定義路徑指標
        path_metrics = {
            "geo-001->meo-001->leo-001->ground-001": RoutingMetrics(
                latency_ms=155, bandwidth_available_gbps=5, reliability=0.99, hop_count=4, load=0.3
            ),
            "geo-001->meo-002->leo-002->ground-001": RoutingMetrics(
                latency_ms=160, bandwidth_available_gbps=8, reliability=0.98, hop_count=4, load=0.5
            ),
            "geo-001->meo-001->meo-002->leo-001->ground-001": RoutingMetrics(
                latency_ms=185, bandwidth_available_gbps=10, reliability=0.995, hop_count=5, load=0.2
            ),
        }
        
        # 計算最佳路由
        best_route = router.calculate_best_route("geo-001", "ground-001", available_paths, path_metrics)
        console.print(f"[bold blue]Best Route:[/bold blue] {best_route}")
        
        # 再次計算（應該命中緩存）
        best_route_2 = router.calculate_best_route("geo-001", "ground-001", available_paths, path_metrics)
        
        # 獲取統計
        stats = router.get_statistics()
        console.print("[bold blue]Routing Statistics:[/bold blue]", stats)
        
        # 更改策略
        router.set_strategy(RoutingStrategy.LOWEST_LATENCY)
        best_route_3 = router.calculate_best_route("geo-001", "ground-001", available_paths, path_metrics)
        console.print(f"[bold blue]Best Route (Lowest Latency):[/bold blue] {best_route_3}")
    
    demo()
