"""
Latency Optimizer
延遲優化器

優化網路延遲，實現超低延遲通訊
Optimizes network latency for ultra-low latency communication
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
from rich.console import Console

console = Console()


@dataclass
class LatencyMeasurement:
    """延遲測量"""
    source: str
    destination: str
    latency_ms: float
    timestamp: float
    path: List[str]


class LatencyOptimizer:
    """
    延遲優化器
    
    特性：
    - 實時延遲監控
    - 延遲預測
    - 路徑優化建議
    - 緩存策略
    - 預測性切換
    """
    
    def __init__(self, target_latency_ms: float = 50.0):
        self.target_latency_ms = target_latency_ms
        
        # Latency measurements (sliding window)
        self.measurements: Dict[Tuple[str, str], deque] = {}
        self.measurement_window_size = 100
        
        # Optimized paths cache
        self.optimized_paths: Dict[Tuple[str, str], List[str]] = {}
        
        # Statistics
        self.total_measurements = 0
        self.optimizations_applied = 0
        self.avg_latency_reduction_ms = 0.0
        
        console.print(f"[bold blue]Latency Optimizer initialized (target: {target_latency_ms}ms)[/bold blue]")
    
    def record_latency(
        self,
        source: str,
        destination: str,
        latency_ms: float,
        path: List[str]
    ) -> None:
        """
        記錄延遲測量
        
        Args:
            source: 源節點
            destination: 目標節點
            latency_ms: 延遲（毫秒）
            path: 路徑
        """
        key = (source, destination)
        
        if key not in self.measurements:
            self.measurements[key] = deque(maxlen=self.measurement_window_size)
        
        measurement = LatencyMeasurement(
            source=source,
            destination=destination,
            latency_ms=latency_ms,
            timestamp=time.time(),
            path=path
        )
        
        self.measurements[key].append(measurement)
        self.total_measurements += 1
        
        # Check if latency exceeds target
        if latency_ms > self.target_latency_ms:
            console.print(f"[yellow]⚠️  Latency {source} → {destination}: {latency_ms:.2f}ms (target: {self.target_latency_ms}ms)[/yellow]")
    
    def get_average_latency(self, source: str, destination: str) -> Optional[float]:
        """
        獲取平均延遲
        
        Args:
            source: 源節點
            destination: 目標節點
            
        Returns:
            平均延遲（毫秒），如果沒有數據返回None
        """
        key = (source, destination)
        
        if key not in self.measurements or not self.measurements[key]:
            return None
        
        measurements = list(self.measurements[key])
        avg_latency = sum(m.latency_ms for m in measurements) / len(measurements)
        
        return avg_latency
    
    def get_latency_percentile(
        self,
        source: str,
        destination: str,
        percentile: float = 95.0
    ) -> Optional[float]:
        """
        獲取延遲百分位數
        
        Args:
            source: 源節點
            destination: 目標節點
            percentile: 百分位數 (0-100)
            
        Returns:
            延遲百分位數，如果沒有數據返回None
        """
        key = (source, destination)
        
        if key not in self.measurements or not self.measurements[key]:
            return None
        
        measurements = list(self.measurements[key])
        latencies = sorted([m.latency_ms for m in measurements])
        
        index = int(len(latencies) * percentile / 100)
        return latencies[min(index, len(latencies) - 1)]
    
    def predict_latency(
        self,
        source: str,
        destination: str,
        path: List[str]
    ) -> Optional[float]:
        """
        預測延遲
        
        Args:
            source: 源節點
            destination: 目標節點
            path: 路徑
            
        Returns:
            預測延遲（毫秒）
        """
        key = (source, destination)
        
        if key not in self.measurements or not self.measurements[key]:
            # No historical data, use simple hop-based estimation
            return len(path) * 30.0  # Assume 30ms per hop
        
        # Use average of recent measurements
        recent_measurements = list(self.measurements[key])[-10:]  # Last 10 measurements
        avg_recent = sum(m.latency_ms for m in recent_measurements) / len(recent_measurements)
        
        return avg_recent
    
    def suggest_optimization(
        self,
        source: str,
        destination: str,
        current_path: List[str],
        alternative_paths: List[List[str]]
    ) -> Optional[Tuple[List[str], float]]:
        """
        建議優化方案
        
        Args:
            source: 源節點
            destination: 目標節點
            current_path: 當前路徑
            alternative_paths: 可選路徑列表
            
        Returns:
            (推薦路徑, 預期延遲改善), 如果無需優化返回None
        """
        current_latency = self.get_average_latency(source, destination)
        
        if current_latency is None or current_latency <= self.target_latency_ms:
            return None  # No optimization needed
        
        best_alternative = None
        best_predicted_latency = float('inf')
        
        for path in alternative_paths:
            if path == current_path:
                continue
            
            predicted_latency = self.predict_latency(source, destination, path)
            
            if predicted_latency and predicted_latency < best_predicted_latency:
                best_predicted_latency = predicted_latency
                best_alternative = path
        
        if best_alternative and best_predicted_latency < current_latency:
            improvement = current_latency - best_predicted_latency
            console.print(f"[green]💡 Optimization suggested: {improvement:.2f}ms improvement[/green]")
            self.optimizations_applied += 1
            self.avg_latency_reduction_ms = (
                (self.avg_latency_reduction_ms * (self.optimizations_applied - 1) + improvement) /
                self.optimizations_applied
            )
            return (best_alternative, improvement)
        
        return None
    
    def analyze_latency_distribution(self, source: str, destination: str) -> dict:
        """
        分析延遲分布
        
        Args:
            source: 源節點
            destination: 目標節點
            
        Returns:
            延遲分布統計
        """
        key = (source, destination)
        
        if key not in self.measurements or not self.measurements[key]:
            return {
                "status": "no_data",
                "measurements": 0
            }
        
        measurements = list(self.measurements[key])
        latencies = [m.latency_ms for m in measurements]
        
        return {
            "status": "available",
            "measurements": len(measurements),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "p50_latency_ms": self.get_latency_percentile(source, destination, 50),
            "p95_latency_ms": self.get_latency_percentile(source, destination, 95),
            "p99_latency_ms": self.get_latency_percentile(source, destination, 99),
            "target_met": sum(1 for lat in latencies if lat <= self.target_latency_ms) / len(latencies)
        }
    
    def get_statistics(self) -> dict:
        """獲取統計信息"""
        all_latencies = []
        for measurements in self.measurements.values():
            all_latencies.extend([m.latency_ms for m in measurements])
        
        avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0
        
        return {
            "total_measurements": self.total_measurements,
            "tracked_paths": len(self.measurements),
            "optimizations_applied": self.optimizations_applied,
            "avg_latency_reduction_ms": self.avg_latency_reduction_ms,
            "overall_avg_latency_ms": avg_latency,
            "target_latency_ms": self.target_latency_ms,
            "target_achievement_rate": sum(1 for lat in all_latencies if lat <= self.target_latency_ms) / len(all_latencies) if all_latencies else 0
        }


# 示例使用
if __name__ == "__main__":
    def demo():
        # 創建延遲優化器
        optimizer = LatencyOptimizer(target_latency_ms=50.0)
        
        # 記錄一些延遲測量
        paths = [
            ["geo-001", "meo-001", "leo-001", "ground-001"],
            ["geo-001", "meo-002", "leo-002", "ground-001"],
        ]
        
        # Simulate measurements
        for i in range(20):
            latency = 45 + i * 2  # Increasing latency
            optimizer.record_latency("geo-001", "ground-001", latency, paths[i % 2])
        
        # Get average latency
        avg_lat = optimizer.get_average_latency("geo-001", "ground-001")
        console.print(f"[bold blue]Average Latency:[/bold blue] {avg_lat:.2f}ms")
        
        # Get percentiles
        p95 = optimizer.get_latency_percentile("geo-001", "ground-001", 95)
        console.print(f"[bold blue]P95 Latency:[/bold blue] {p95:.2f}ms")
        
        # Predict latency
        predicted = optimizer.predict_latency("geo-001", "ground-001", paths[0])
        console.print(f"[bold blue]Predicted Latency:[/bold blue] {predicted:.2f}ms")
        
        # Suggest optimization
        alternative_paths = [
            ["geo-001", "meo-003", "leo-003", "ground-001"],
            ["geo-001", "leo-001", "ground-001"],
        ]
        suggestion = optimizer.suggest_optimization("geo-001", "ground-001", paths[0], alternative_paths)
        if suggestion:
            console.print(f"[bold blue]Optimization Suggestion:[/bold blue] {suggestion}")
        
        # Analyze distribution
        distribution = optimizer.analyze_latency_distribution("geo-001", "ground-001")
        console.print("[bold blue]Latency Distribution:[/bold blue]", distribution)
        
        # Get statistics
        stats = optimizer.get_statistics()
        console.print("[bold blue]Optimizer Statistics:[/bold blue]", stats)
    
    demo()
