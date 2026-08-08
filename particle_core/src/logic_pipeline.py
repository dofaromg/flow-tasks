# MRLiou Logic Pipeline 統合執行模組
# 邏輯管線核心執行系統

import json
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import threading
from pipeline_constants import PIPELINE_STEPS, STEP_EXPLANATIONS, COMPRESSED_SEED

class LogicPipeline:
    """MRLiou 邏輯管線核心類別 - Enhanced with parallel execution and caching"""
    
    # Use Python's built-in hash for faster caching (non-cryptographic)
    # For production use with security requirements, switch to hashlib.sha256
    USE_FAST_HASH = True
    
    def __init__(self, enable_cache: bool = True, max_workers: int = 4):
        self.pipeline_steps = list(PIPELINE_STEPS)
        self.explanations = dict(STEP_EXPLANATIONS)
        self.enable_cache = enable_cache
        self.max_workers = max_workers
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._metrics = {
            "total_executions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "parallel_executions": 0
        }
    
    def _compute_cache_key(self, input_data: str, steps: Optional[List[str]] = None) -> str:
        """計算快取鍵值"""
        steps_str = ",".join(steps) if steps else ",".join(self.pipeline_steps)
        content = f"{input_data}:{steps_str}"
        
        if self.USE_FAST_HASH:
            # Use built-in hash for speed (not cryptographically secure)
            return str(hash(content))
        else:
            # Use SHA-256 for security (slower)
            return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """從快取取得結果"""
        if not self.enable_cache:
            return None
        with self._cache_lock:
            if cache_key in self._cache:
                self._metrics["cache_hits"] += 1
                return self._cache[cache_key]
            self._metrics["cache_misses"] += 1
            return None
    
    def _put_to_cache(self, cache_key: str, value: Any):
        """將結果放入快取"""
        if not self.enable_cache:
            return
        with self._cache_lock:
            self._cache[cache_key] = value
    
    def clear_cache(self):
        """清除快取"""
        with self._cache_lock:
            self._cache.clear()
    
    def get_metrics(self) -> Dict[str, Any]:
        """取得效能指標"""
        cache_hit_rate = (
            self._metrics["cache_hits"] / 
            (self._metrics["cache_hits"] + self._metrics["cache_misses"])
            if (self._metrics["cache_hits"] + self._metrics["cache_misses"]) > 0 
            else 0
        )
        return {
            **self._metrics,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self._cache)
        }
    
    def run_logic_chain(self, input_data: str) -> str:
        """執行完整邏輯鏈"""
        self._metrics["total_executions"] += 1
        
        # Check cache
        cache_key = self._compute_cache_key(input_data)
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute logic chain
        current_result = input_data
        for step in self.pipeline_steps:
            current_result = f"[{step.upper()} → {current_result}]"
        
        # Store in cache
        self._put_to_cache(cache_key, current_result)
        return current_result
    
    def run_logic_chain_parallel(self, input_batch: List[str]) -> List[str]:
        """並行執行多個邏輯鏈 - Enhanced computational capacity"""
        self._metrics["parallel_executions"] += 1
        
        results = [None] * len(input_batch)
        
        def process_item(idx: int, data: str) -> tuple:
            result = self.run_logic_chain(data)
            return idx, result
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(process_item, idx, data): idx 
                for idx, data in enumerate(input_batch)
            }
            
            for future in as_completed(futures):
                idx, result = future.result()
                results[idx] = result
        
        return results
    
    def batch_simulate(self, input_batch: List[str], parallel: bool = True) -> List[Dict[str, Any]]:
        """批次模擬執行 - Enhanced for batch processing"""
        if parallel and len(input_batch) > 1:
            execution_results = self.run_logic_chain_parallel(input_batch)
        else:
            execution_results = [self.run_logic_chain(data) for data in input_batch]
        
        return [
            {
                "input": input_data,
                "steps": self.pipeline_steps,
                "explanations": self.get_human_readable(),
                "result": result,
                "compressed": self.compress_logic(self.pipeline_steps)
            }
            for input_data, result in zip(input_batch, execution_results)
        ]
    
    def process_step(self, step: str, data: str) -> str:
        """處理單一邏輯步驟"""
        return f"[{step.upper()} → {data}]"
    
    def get_human_readable(self) -> List[str]:
        """取得人類可讀的步驟說明"""
        return [self.explanations.get(step, step) for step in self.pipeline_steps]
    
    def compress_logic(self, steps: List[str]) -> str:
        """壓縮邏輯鏈為 .flpkg 格式"""
        if steps == self.pipeline_steps:
            return COMPRESSED_SEED
        return "UNSUPPORTED_LOGIC_CHAIN"
    
    def decompress_logic(self, compressed: str) -> List[str]:
        """解壓縮邏輯鏈"""
        if "SEED(X)" in compressed and "STORE(RECURSE(FLOW(MARK(STRUCTURE" in compressed:
            return self.pipeline_steps
        return ["UNKNOWN"]
    
    def store_result(self, input_value: str, result: str, output_dir: str = "examples") -> str:
        """儲存執行結果"""
        os.makedirs(output_dir, exist_ok=True)
        
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "input": input_value,
            "logic_chain": self.pipeline_steps,
            "human_readable": self.get_human_readable(),
            "result": result,
            "compressed": self.compress_logic(self.pipeline_steps)
        }
        
        filename = os.path.join(output_dir, f"logic_result_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
        with open(filename, "w", encoding="utf-8") as output_file:
            json.dump(data, output_file, ensure_ascii=False, indent=2)
        
        return filename
    
    def simulate(self, input_data: str) -> Dict[str, Any]:
        """完整模擬執行流程"""
        execution_result = self.run_logic_chain(input_data)
        
        return {
            "input": input_data,
            "steps": self.pipeline_steps,
            "explanations": self.get_human_readable(),
            "result": execution_result,
            "compressed": self.compress_logic(self.pipeline_steps)
        }

def main():
    """主執行函數"""
    print("== MRLiou Logic Pipeline 統合執行系統 ==")
    pipeline = LogicPipeline()
    
    # 取得使用者輸入
    user_input = input("請輸入要處理的資料： ")
    
    # 執行模擬
    simulation = pipeline.simulate(user_input)
    
    # 顯示結果
    print("\n=== 執行結果 ===")
    print(f"輸入: {simulation['input']}")
    print(f"邏輯鏈: {' → '.join(simulation['steps'])}")
    print(f"結果: {simulation['result']}")
    print(f"壓縮形式: {simulation['compressed']}")
    
    print("\n=== 步驟說明 ===")
    for i, (step, explanation) in enumerate(zip(simulation['steps'], simulation['explanations'])):
        print(f"{i+1}. {step}: {explanation}")
    
    # 儲存結果
    filename = pipeline.store_result(user_input, simulation['result'])
    print(f"\n結果已儲存至: {filename}")

if __name__ == "__main__":
    main()