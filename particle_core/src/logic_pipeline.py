# MRLiou Logic Pipeline 統合執行模組
# 邏輯管線核心執行系統

import json
from datetime import datetime, timezone
from typing import List, Dict, Any
import os

class LogicPipeline:
    """MRLiou 邏輯管線核心類別"""
    
    def __init__(self):
        self.fn_steps = ["structure", "mark", "flow", "recurse", "store"]
        self.explanations = {
            "structure": "定義輸入資料結構",
            "mark": "建立邏輯跳點標記", 
            "flow": "轉換為流程結構節奏",
            "recurse": "遞歸展開為細部結構",
            "store": "封存至邏輯記憶模組"
        }
    
    def run_logic_chain(self, input_data: str) -> str:
        """執行完整邏輯鏈"""
        result = input_data
        for step in self.fn_steps:
            result = f"[{step.upper()} → {result}]"
        return result
    
    def process_step(self, step: str, data: str) -> str:
        """處理單一邏輯步驟"""
        return f"[{step.upper()} → {data}]"
    
    def get_human_readable(self) -> List[str]:
        """取得人類可讀的步驟說明"""
        return [self.explanations.get(step, step) for step in self.fn_steps]
    
    def compress_logic(self, steps: List[str]) -> str:
        """壓縮邏輯鏈為 .flpkg 格式"""
        if steps == self.fn_steps:
            return "SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))"
        return "UNSUPPORTED_LOGIC_CHAIN"
    
    def decompress_logic(self, compressed: str) -> List[str]:
        """解壓縮邏輯鏈"""
        if "SEED(X)" in compressed and "STORE(RECURSE(FLOW(MARK(STRUCTURE" in compressed:
            return self.fn_steps
        return ["UNKNOWN"]
    
    def store_result(self, input_val: str, result: str, output_dir: str = "examples") -> str:
        """儲存執行結果"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Use the same timestamp for both filename and content to ensure consistency
        now = datetime.now(timezone.utc)
        
        data = {
            "timestamp": now.isoformat(),
            "input": input_val,
            "logic_chain": self.fn_steps,
            "human_readable": self.get_human_readable(),
            "result": result,
            "compressed": self.compress_logic(self.fn_steps)
        }
        
        filename = os.path.join(output_dir, f"logic_result_{now.strftime('%Y%m%d_%H%M%S')}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def simulate(self, input_data: str) -> Dict[str, Any]:
        """完整模擬執行流程"""
        result = self.run_logic_chain(input_data)
        
        return {
            "input": input_data,
            "steps": self.fn_steps,
            "explanations": self.get_human_readable(),
            "result": result,
            "compressed": self.compress_logic(self.fn_steps)
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