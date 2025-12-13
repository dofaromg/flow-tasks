#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Monitoring Utilities
用於監控和測量函數執行效能

This module provides decorators and utilities for monitoring function performance,
collecting statistics, and identifying bottlenecks.
"""

import functools
import time
import logging
import threading
from typing import Any, Callable, TypeVar, Optional
from collections import defaultdict

F = TypeVar('F', bound=Callable[..., Any])

# Thread-safe global performance statistics
_stats_lock = threading.Lock()


def _create_stats_dict():
    """Factory function for creating new statistics dictionaries."""
    return {
        'count': 0,
        'total_time': 0.0,
        'min_time': float('inf'),
        'max_time': 0.0
    }


_performance_stats = defaultdict(_create_stats_dict)


def timing_decorator(log_level: str = 'INFO', threshold_ms: Optional[float] = None) -> Callable[[F], F]:
    """
    Decorator to measure and log function execution time.
    
    Args:
        log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        threshold_ms: Only log if execution time exceeds this threshold (milliseconds)
        
    Usage:
        @timing_decorator()
        def my_function():
            pass
            
        @timing_decorator(threshold_ms=100.0)  # Only log if > 100ms
        def slow_function():
            pass
    
    Returns:
        Decorated function that tracks execution time
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            
            elapsed_ms = (end - start) * 1000
            
            # Update statistics (thread-safe)
            with _stats_lock:
                stats = _performance_stats[func.__name__]
                stats['count'] += 1
                stats['total_time'] += elapsed_ms
                stats['min_time'] = min(stats['min_time'], elapsed_ms)
                stats['max_time'] = max(stats['max_time'], elapsed_ms)
            
            # Log if threshold is met or not set
            if threshold_ms is None or elapsed_ms >= threshold_ms:
                logger = logging.getLogger(func.__module__)
                log_method = getattr(logger, log_level.lower(), logger.info)
                log_method(f"{func.__name__} took {elapsed_ms:.2f}ms")
            
            return result
        return wrapper  # type: ignore
    return decorator


def get_performance_stats(func_name: Optional[str] = None) -> dict:
    """
    Get performance statistics for functions.
    
    Args:
        func_name: Specific function name, or None for all functions
        
    Returns:
        Dictionary of performance statistics with average times calculated
    """
    if func_name:
        stats = _performance_stats.get(func_name)
        if stats:
            return {
                func_name: {
                    **stats,
                    'avg_time': stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
                }
            }
        return {}
    
    return {
        name: {
            **stats,
            'avg_time': stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
        }
        for name, stats in _performance_stats.items()
    }


def reset_performance_stats() -> None:
    """Reset all performance statistics (thread-safe)."""
    with _stats_lock:
        _performance_stats.clear()


def print_performance_report() -> None:
    """Print a formatted performance report to stdout."""
    stats = get_performance_stats()
    
    if not stats:
        print("No performance data collected.")
        return
    
    print("\n=== Performance Report ===")
    print(f"{'Function':<40} {'Calls':>8} {'Avg (ms)':>12} {'Min (ms)':>12} {'Max (ms)':>12} {'Total (s)':>12}")
    print("-" * 100)
    
    # Sort by total time (descending) to show most expensive functions first
    for func_name, data in sorted(stats.items(), key=lambda x: x[1]['total_time'], reverse=True):
        print(f"{func_name:<40} {data['count']:>8} {data['avg_time']:>12.2f} "
              f"{data['min_time']:>12.2f} {data['max_time']:>12.2f} {data['total_time']/1000:>12.2f}")
    
    print("=" * 100)


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    print("Performance Monitor Demo")
    print("=" * 50)
    
    @timing_decorator()
    def test_function_fast():
        """Fast function for testing."""
        time.sleep(0.001)
        return "fast"
    
    @timing_decorator(threshold_ms=10.0)
    def test_function_slow():
        """Slow function that triggers logging."""
        time.sleep(0.015)
        return "slow"
    
    @timing_decorator(log_level='WARNING', threshold_ms=50.0)
    def test_function_very_slow():
        """Very slow function with warning level."""
        time.sleep(0.055)
        return "very slow"
    
    # Run tests
    print("\nRunning test functions...")
    for i in range(10):
        test_function_fast()
    
    for i in range(5):
        test_function_slow()
    
    for i in range(3):
        test_function_very_slow()
    
    # Print report
    print_performance_report()
    
    # Test getting specific stats
    print("\nStats for 'test_function_fast':")
    print(get_performance_stats('test_function_fast'))
    
    sys.exit(0)
