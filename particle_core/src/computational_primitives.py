"""
Computational Primitives for Enhanced System Computation
計算原語模組 - 增強系統演算能力

提供矩陣運算、統計分析、圖算法等基礎計算功能
"""

from typing import List, Dict, Any, Optional, Tuple, Callable
import math
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from functools import reduce


class MatrixOperations:
    """矩陣運算模組 - Matrix computation primitives"""
    
    @staticmethod
    def add(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """矩陣加法 - Matrix addition"""
        if len(a) != len(b) or len(a[0]) != len(b[0]):
            raise ValueError("Matrix dimensions must match")
        
        return [
            [a[i][j] + b[i][j] for j in range(len(a[0]))]
            for i in range(len(a))
        ]
    
    @staticmethod
    def multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """矩陣乘法 - Matrix multiplication"""
        if len(a[0]) != len(b):
            raise ValueError("Invalid matrix dimensions for multiplication")
        
        result = [[0] * len(b[0]) for _ in range(len(a))]
        
        for i in range(len(a)):
            for j in range(len(b[0])):
                for k in range(len(b)):
                    result[i][j] += a[i][k] * b[k][j]
        
        return result
    
    @staticmethod
    def transpose(matrix: List[List[float]]) -> List[List[float]]:
        """矩陣轉置 - Matrix transpose"""
        return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0]))]
    
    @staticmethod
    def scalar_multiply(matrix: List[List[float]], scalar: float) -> List[List[float]]:
        """純量乘法 - Scalar multiplication"""
        return [[element * scalar for element in row] for row in matrix]
    
    @staticmethod
    def dot_product(a: List[float], b: List[float]) -> float:
        """向量點積 - Dot product"""
        if len(a) != len(b):
            raise ValueError("Vector dimensions must match")
        return sum(x * y for x, y in zip(a, b))
    
    @staticmethod
    def determinant(matrix: List[List[float]]) -> float:
        """計算行列式 (僅支援 2x2 和 3x3) - Determinant"""
        n = len(matrix)
        if n == 2:
            return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
        elif n == 3:
            return (
                matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1]) -
                matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0]) +
                matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
            )
        else:
            raise ValueError("Determinant only supported for 2x2 and 3x3 matrices")


class StatisticalOperations:
    """統計運算模組 - Statistical computation primitives"""
    
    @staticmethod
    def mean(data: List[float]) -> float:
        """平均值 - Mean"""
        if not data:
            raise ValueError("Data cannot be empty")
        return sum(data) / len(data)
    
    @staticmethod
    def median(data: List[float]) -> float:
        """中位數 - Median"""
        if not data:
            raise ValueError("Data cannot be empty")
        sorted_data = sorted(data)
        n = len(sorted_data)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_data[mid - 1] + sorted_data[mid]) / 2
        return sorted_data[mid]
    
    @staticmethod
    def variance(data: List[float]) -> float:
        """變異數 - Variance"""
        if len(data) < 2:
            raise ValueError("Need at least 2 data points")
        m = StatisticalOperations.mean(data)
        return sum((x - m) ** 2 for x in data) / (len(data) - 1)
    
    @staticmethod
    def std_dev(data: List[float]) -> float:
        """標準差 - Standard deviation"""
        return math.sqrt(StatisticalOperations.variance(data))
    
    @staticmethod
    def correlation(x: List[float], y: List[float]) -> float:
        """相關係數 - Correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            raise ValueError("Invalid data for correlation")
        
        n = len(x)
        mean_x = StatisticalOperations.mean(x)
        mean_y = StatisticalOperations.mean(y)
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = math.sqrt(
            sum((x[i] - mean_x) ** 2 for i in range(n)) *
            sum((y[i] - mean_y) ** 2 for i in range(n))
        )
        
        return numerator / denominator if denominator != 0 else 0
    
    @staticmethod
    def percentile(data: List[float], p: float) -> float:
        """百分位數 - Percentile"""
        if not data or not (0 <= p <= 100):
            raise ValueError("Invalid data or percentile")
        
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        
        if f == c:
            return sorted_data[int(k)]
        
        d0 = sorted_data[int(f)] * (c - k)
        d1 = sorted_data[int(c)] * (k - f)
        return d0 + d1


class GraphAlgorithms:
    """圖算法模組 - Graph algorithms for logic chains"""
    
    @staticmethod
    def shortest_path(graph: Dict[str, List[str]], start: str, end: str) -> Optional[List[str]]:
        """最短路徑 (BFS) - Shortest path using BFS"""
        if start not in graph:
            return None
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            node, path = queue.popleft()
            
            if node == end:
                return path
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    @staticmethod
    def find_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
        """尋找循環 - Find cycles in directed graph"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)
            
            rec_stack.remove(node)
            path.pop()
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    @staticmethod
    def topological_sort(graph: Dict[str, List[str]]) -> Optional[List[str]]:
        """拓撲排序 - Topological sort"""
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph.get(node, []):
                if neighbor not in in_degree:
                    in_degree[neighbor] = 0
                in_degree[neighbor] += 1
        
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check if all nodes are processed (no cycles)
        if len(result) != len(in_degree):
            return None  # Graph has cycles
        
        return result


class ParallelComputations:
    """並行計算模組 - Parallel computation utilities"""
    
    @staticmethod
    def parallel_map(func: Callable, data: List[Any], max_workers: int = 4) -> List[Any]:
        """並行映射 - Parallel map operation"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(func, data))
    
    @staticmethod
    def parallel_reduce(func: Callable, data: List[Any], initial: Any = None, max_workers: int = 4) -> Any:
        """並行歸約 - Parallel reduce operation"""
        if not data:
            return initial
        
        # Divide data into chunks
        chunk_size = max(1, len(data) // max_workers)
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
        
        # Reduce each chunk in parallel (without initial value)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            partial_results = list(executor.map(
                lambda chunk: reduce(func, chunk),
                chunks
            ))
        
        # Combine partial results with initial value if provided
        if initial is not None:
            return reduce(func, partial_results, initial)
        return reduce(func, partial_results)
    
    @staticmethod
    def parallel_filter(predicate: Callable, data: List[Any], max_workers: int = 4) -> List[Any]:
        """並行過濾 - Parallel filter operation"""
        def chunk_filter(chunk: List[Any]) -> List[Any]:
            return [item for item in chunk if predicate(item)]
        
        chunk_size = max(1, len(data) // max_workers)
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            filtered_chunks = list(executor.map(chunk_filter, chunks))
        
        # Flatten results
        return [item for chunk in filtered_chunks for item in chunk]


class TensorOperations:
    """張量運算模組 - Tensor operations (simplified)"""
    
    @staticmethod
    def reshape(data: List[Any], shape: Tuple[int, ...]) -> List[Any]:
        """重塑張量 - Reshape tensor"""
        flat = TensorOperations._flatten(data)
        total = reduce(lambda x, y: x * y, shape, 1)
        
        if len(flat) != total:
            raise ValueError(f"Cannot reshape {len(flat)} elements into shape {shape}")
        
        return TensorOperations._unflatten(flat, shape)
    
    @staticmethod
    def _flatten(data: List[Any]) -> List[Any]:
        """展平張量 - Flatten tensor"""
        result = []
        for item in data:
            if isinstance(item, list):
                result.extend(TensorOperations._flatten(item))
            else:
                result.append(item)
        return result
    
    @staticmethod
    def _unflatten(flat: List[Any], shape: Tuple[int, ...]) -> List[Any]:
        """反展平張量 - Unflatten tensor"""
        if len(shape) == 1:
            return flat[:shape[0]]
        
        size = reduce(lambda x, y: x * y, shape[1:], 1)
        return [
            TensorOperations._unflatten(flat[i * size:(i + 1) * size], shape[1:])
            for i in range(shape[0])
        ]
    
    @staticmethod
    def element_wise_operation(
        a: List[Any],
        b: List[Any],
        operation: Callable[[float, float], float]
    ) -> List[Any]:
        """元素級運算 - Element-wise operation"""
        if not isinstance(a, list) or not isinstance(b, list):
            return operation(a, b)
        
        if len(a) != len(b):
            raise ValueError("Tensors must have the same shape")
        
        return [
            TensorOperations.element_wise_operation(x, y, operation)
            for x, y in zip(a, b)
        ]


# Convenience function for common operations
def compute_statistics(data: List[float]) -> Dict[str, float]:
    """計算統計摘要 - Compute statistical summary"""
    stats = StatisticalOperations()
    return {
        "count": len(data),
        "mean": stats.mean(data),
        "median": stats.median(data),
        "std_dev": stats.std_dev(data),
        "variance": stats.variance(data),
        "min": min(data),
        "max": max(data),
        "p25": stats.percentile(data, 25),
        "p75": stats.percentile(data, 75)
    }
