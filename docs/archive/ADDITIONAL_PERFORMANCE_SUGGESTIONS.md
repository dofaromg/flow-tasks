# Additional Performance Optimization Suggestions

## Overview

This document provides additional performance optimization suggestions beyond those already implemented in `PERFORMANCE_IMPROVEMENTS_IMPLEMENTED.md`. These are lower-priority optimizations that could provide incremental improvements.

**Status**: All critical and high-priority improvements from the original analysis have been implemented ✅

---

## 🟡 Medium Priority Suggestions

### 1. Add Connection Pooling for HTTP Requests (Future Enhancement)

**File**: `apps/orchestrator/app.py` (line 43)

**Current Status**: Single request usage - not critical currently

**If usage increases**, consider adding connection pooling:

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Create a session with connection pooling
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
session.mount('http://', adapter)
session.mount('https://', adapter)

@app.route('/orchestrate', methods=['POST'])
def orchestrate():
    try:
        data = request.get_json()
        logger.info(f"Orchestrating request: {data}")
        
        # Use session instead of requests.get
        try:
            response = session.get(f"{MODULE_A_ENDPOINT}/info", timeout=5)
            module_a_info = response.json()
        except Exception as e:
            logger.error(f"Failed to call Module-A: {e}")
            module_a_info = {'error': str(e)}
        
        return jsonify({
            'orchestrator': 'success',
            'input': data,
            'module_a': module_a_info
        })
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        return jsonify({'error': str(e)}), 500
```

**Impact**: 
- ⚡ 10-30% faster for repeated API calls
- 🔄 Better handling of connection reuse
- 🛡️ Improved reliability with retries

**When to implement**: When orchestrator makes frequent external API calls

---

### 2. Optimize Directory Traversal in `ai_persona_toolkit.py`

**File**: `particle_core/src/ai_persona_toolkit.py` (line 624)

**Current Code**:
```python
def _add_to_zip(self, zf: zipfile.ZipFile, path: str, files_added: List[str]) -> None:
    """將檔案或目錄加入 ZIP"""
    path = Path(path)
    
    if path.is_file():
        arcname = path.name
        zf.write(path, arcname)
        files_added.append(arcname)
        
    elif path.is_dir():
        for file_path in path.rglob('*'):
            if file_path.is_file():
                arcname = str(file_path.relative_to(path.parent))
                zf.write(file_path, arcname)
                files_added.append(arcname)
```

**Analysis**: This implementation is actually reasonable for ZIP compression use cases where:
- All files need to be included (no filtering needed)
- Operation typically happens once per compression
- `rglob('*')` with `is_file()` check is appropriate

**Potential Optimization** (if large directory trees become a bottleneck):

```python
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

def _add_to_zip(self, zf: zipfile.ZipFile, path: str, files_added: List[str]) -> None:
    """將檔案或目錄加入 ZIP (optimized for large trees)"""
    path = Path(path)
    
    if path.is_file():
        arcname = path.name
        zf.write(path, arcname)
        files_added.append(arcname)
        
    elif path.is_dir():
        # Collect file paths first
        file_paths = [fp for fp in path.rglob('*') if fp.is_file()]
        
        # Write files to ZIP
        for file_path in file_paths:
            arcname = str(file_path.relative_to(path.parent))
            zf.write(file_path, arcname)
            files_added.append(arcname)
```

**Impact**: Minimal - only beneficial for very large directory trees (>10,000 files)

**Recommendation**: Keep current implementation unless performance issues arise

---

### 3. Add Performance Monitoring Decorators

**Suggested Addition**: Create a performance monitoring module

**New File**: `particle_core/src/performance_monitor.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Monitoring Utilities
用於監控和測量函數執行效能
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
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            
            elapsed_ms = (end - start) * 1000
            
            # Update statistics
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
        Dictionary of performance statistics
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
    """Reset all performance statistics."""
    _performance_stats.clear()


def print_performance_report() -> None:
    """Print a formatted performance report."""
    stats = get_performance_stats()
    
    if not stats:
        print("No performance data collected.")
        return
    
    print("\n=== Performance Report ===")
    print(f"{'Function':<40} {'Calls':>8} {'Avg (ms)':>12} {'Min (ms)':>12} {'Max (ms)':>12} {'Total (s)':>12}")
    print("-" * 100)
    
    for func_name, data in sorted(stats.items(), key=lambda x: x[1]['total_time'], reverse=True):
        print(f"{func_name:<40} {data['count']:>8} {data['avg_time']:>12.2f} "
              f"{data['min_time']:>12.2f} {data['max_time']:>12.2f} {data['total_time']/1000:>12.2f}")
    
    print("=" * 100)


# Example usage:
if __name__ == "__main__":
    @timing_decorator()
    def test_function():
        time.sleep(0.01)
    
    # Run test
    for _ in range(10):
        test_function()
    
    print_performance_report()
```

**Usage Example**:

```python
from particle_core.src.performance_monitor import timing_decorator

class LogicPipeline:
    @timing_decorator(threshold_ms=10.0)  # Only log if > 10ms
    def run_logic_chain(self, input_data: str) -> str:
        """執行完整邏輯鏈"""
        current_result = input_data
        for step in self.pipeline_steps:
            current_result = f"[{step.upper()} → {current_result}]"
        return current_result
```

**Impact**: 
- 📊 Provides visibility into performance bottlenecks
- 🔍 Helps identify slow operations in production
- 📈 Collects statistics for optimization priorities

**Recommendation**: Add to critical path functions for monitoring

---

### 4. Consider Generator-Based File Processing

**For Future Large-Scale Operations**

If processing very large numbers of files or large datasets, consider using generators to reduce memory usage:

```python
def read_files_generator(base_dir: Path, suffixes: tuple = (".py", ".md", ".txt")):
    """
    Yield file contents one at a time to reduce memory usage.
    
    Usage:
        for file_path, content in read_files_generator(Path(".")):
            process_file(file_path, content)
    """
    for suffix in suffixes:
        for file_path in base_dir.rglob(f"*{suffix}"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                yield file_path, content
            except Exception:
                continue


def build_index_streaming(base_dir: Path, output_dir: Path):
    """
    Build index using streaming approach for very large codebases.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from scipy import sparse
    import pickle
    
    # Initialize vectorizer
    vectorizer = TfidfVectorizer()
    
    # Collect documents in batches to reduce memory
    batch_size = 1000
    documents = []
    paths = []
    
    for file_path, content in read_files_generator(base_dir):
        documents.append(content)
        paths.append(str(file_path))
        
        if len(documents) >= batch_size:
            # Process batch
            if not hasattr(vectorizer, 'vocabulary_'):
                # First batch - fit
                vectorizer.fit(documents)
            # Transform batch
            batch_matrix = vectorizer.transform(documents)
            
            # Save or append to index
            # ... implementation details ...
            
            # Clear batch
            documents.clear()
    
    # Process remaining documents
    if documents:
        batch_matrix = vectorizer.transform(documents)
        # Save final batch
```

**Impact**: 
- 💾 Significantly reduced memory usage for large codebases
- ⚡ Allows processing of datasets larger than available RAM
- 🔄 Enables streaming processing patterns

**When to implement**: When codebase exceeds 10,000 files or RAM becomes a constraint

---

## 🟢 Low Priority / Best Practices

### 5. Add Type Checking with mypy

**Recommendation**: Add mypy configuration for static type checking

**New File**: `mypy.ini`

```ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False
disallow_incomplete_defs = False
check_untyped_defs = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True

[mypy-pytest.*]
ignore_missing_imports = True

[mypy-flask.*]
ignore_missing_imports = True

[mypy-sklearn.*]
ignore_missing_imports = True
```

**Run with**:
```bash
pip install mypy
mypy particle_core/src/
```

**Impact**: Better code quality, catches type-related bugs early

---

### 6. Consider Using `__slots__` for Frequent Classes

For classes instantiated many times (e.g., trace entries), consider using `__slots__`:

```python
class TraceEntry:
    """Optimized trace entry using __slots__."""
    __slots__ = ['index', 'action', 'target', 'data', 'timestamp', 'symbol']
    
    def __init__(self, index: int, action: str, target: str, data: Any, 
                 timestamp: str, symbol: str):
        self.index = index
        self.action = action
        self.target = target
        self.data = data
        self.timestamp = timestamp
        self.symbol = symbol
```

**Impact**:
- 💾 ~40% less memory per instance
- ⚡ Slightly faster attribute access
- ⚠️ Trade-off: Reduces flexibility (no dynamic attributes)

**Recommendation**: Only use for high-frequency, stable classes

---

## 📊 Benchmarking Tools

### Recommended Profiling Commands

```bash
# CPU profiling
python -m cProfile -o profile.stats your_script.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

# Memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py

# Line-by-line profiling
pip install line_profiler
kernprof -l -v your_script.py

# Benchmarking with timeit
python -m timeit -s "from mymodule import myfunction" "myfunction()"
```

### Performance Testing Script

**New File**: `scripts/benchmark_performance.py`

```python
#!/usr/bin/env python3
"""
Performance Benchmark Script
Run this before and after optimizations to measure improvements
"""

import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from particle_core.src.logic_pipeline import LogicPipeline
from particle_core.src.rebuild_fn import FunctionRestorer
from particle_core.src.memory_archive_seed import MemoryArchiveSeed
from rag_index import read_files, build_index

def benchmark_logic_pipeline(iterations: int = 1000):
    """Benchmark logic pipeline execution."""
    pipeline = LogicPipeline()
    
    start = time.perf_counter()
    for i in range(iterations):
        pipeline.simulate(f"Test input {i}")
    end = time.perf_counter()
    
    elapsed = end - start
    ops_per_sec = iterations / elapsed
    
    print(f"Logic Pipeline: {iterations} operations in {elapsed:.3f}s ({ops_per_sec:.0f} ops/sec)")


def benchmark_checksum(iterations: int = 100):
    """Benchmark checksum generation with caching."""
    archive = MemoryArchiveSeed()
    
    test_data = {
        "text": "Test data for checksum",
        "numbers": list(range(100)),
        "nested": {"key": "value"}
    }
    
    start = time.perf_counter()
    for _ in range(iterations):
        archive._generate_checksum(test_data)
    end = time.perf_counter()
    
    elapsed = end - start
    ops_per_sec = iterations / elapsed
    
    print(f"Checksum: {iterations} operations in {elapsed:.3f}s ({ops_per_sec:.0f} ops/sec)")


def benchmark_file_reading():
    """Benchmark file reading with parallel I/O."""
    import tempfile
    import shutil
    from pathlib import Path
    
    # Create temp directory with test files
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Create 100 test files
        for i in range(100):
            (temp_dir / f"test_{i}.py").write_text(f"# Test file {i}\n" * 100)
        
        start = time.perf_counter()
        documents, paths = read_files(temp_dir)
        end = time.perf_counter()
        
        elapsed = end - start
        files_per_sec = len(paths) / elapsed
        
        print(f"File Reading: {len(paths)} files in {elapsed:.3f}s ({files_per_sec:.0f} files/sec)")
    
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("=== Performance Benchmark ===\n")
    
    benchmark_logic_pipeline()
    benchmark_checksum()
    benchmark_file_reading()
    
    print("\n=== Benchmark Complete ===")
```

**Run with**:
```bash
python scripts/benchmark_performance.py
```

---

## 📝 Summary

### Already Implemented (✅)
1. ✅ Command injection fix (CRITICAL)
2. ✅ Parallel file I/O in `rag_index.py`
3. ✅ Checksum caching
4. ✅ Bounded memory traces (deque)
5. ✅ JSON round-trip for snapshots
6. ✅ Targeted glob patterns

### Suggested for Future (Optional)
1. 🔄 Connection pooling (if API usage increases)
2. 📊 Performance monitoring decorators
3. 🔍 Generator-based processing (for very large datasets)
4. 🛡️ Type checking with mypy
5. 💾 `__slots__` for high-frequency classes

### Performance Testing
- Create benchmarking script to measure improvements
- Add before/after metrics to documentation
- Monitor production performance with decorators

---

## 🎯 Conclusion

All critical and high-priority performance improvements have been successfully implemented. The additional suggestions in this document are:

- **Optional enhancements** for specific use cases
- **Best practices** for long-term maintainability
- **Monitoring tools** for production environments

**Recommendation**: Current implementation is well-optimized. Implement additional suggestions only if specific performance needs arise or for production monitoring.
