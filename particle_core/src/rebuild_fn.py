# MRLiou flpkg/fn 壓縮還原重建器
# Compression and restoration system for .flpkg and .fn formats

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

class FunctionRestorer:
    """MRLiou 函數還原重建器"""
    
    def __init__(self):
        self.restore_map = {
            "SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))": [
                "structure",
                "mark", 
                "flow",
                "recurse",
                "store"
            ],
            "COMPACT_SEED": [
                "structure",
                "mark",
                "flow", 
                "recurse",
                "store"
            ]
        }
        
        self.explanations = {
            "structure": "定義輸入資料結構",
            "mark": "建立邏輯跳點標記",
            "flow": "轉換為流程結構節奏",
            "recurse": "遞歸展開為細部結構",
            "store": "封存至模組記憶結構"
        }
    
    def decompress_fn(self, compressed_code: str) -> List[str]:
        """解壓縮 .flpkg 格式至函數步驟"""
        # 標準化處理
        normalized = compressed_code.strip()
        
        # 檢查已知的壓縮格式
        for pattern, steps_list in self.restore_map.items():
            if pattern in normalized:
                return steps_list
        
        # 嘗試解析其他格式
        if "SEED" in normalized:
            return ["structure", "mark", "flow", "recurse", "store"]
        
        return ["UNKNOWN_LOGIC"]
    
    def compress_fn(self, function_steps: List[str]) -> str:
        """壓縮函數步驟為 .flpkg 格式"""
        standard_steps = ["structure", "mark", "flow", "recurse", "store"]
        
        if function_steps == standard_steps:
            return "SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))"
        
        # 建構動態壓縮
        if len(function_steps) > 0:
            nested = function_steps[0].upper() + "(X)"
            for step in function_steps[1:]:
                nested = f"{step.upper()}({nested})"
            return f"CUSTOM_SEED(X) = {nested}"
        
        return "EMPTY_LOGIC"
    
    def to_human_readable(self, function_steps: List[str]) -> List[str]:
        """轉換為人類可讀說明"""
        return [self.explanations.get(step, f"未知步驟: {step}") for step in function_steps]
    
    def simulate_execution(self, function_steps: List[str], input_data: str = "X") -> str:
        """模擬執行函數鏈"""
        current_output = input_data
        for step in function_steps:
            current_output = f"[{step.upper()} → {current_output}]"
        return current_output
    
    def create_flpkg_package(self, function_steps: List[str], metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """建立 .flpkg 封包格式"""
        if metadata is None:
            metadata = {}
        
        package = {
            "package_type": "flpkg",
            "version": "1.0",
            "created": datetime.utcnow().isoformat(),
            "compressed": self.compress_fn(function_steps),
            "functions": function_steps,
            "human_readable": self.to_human_readable(function_steps),
            "signature": f"MRLSIG-{hash(str(function_steps)) % 10000:04d}",
            "metadata": metadata
        }
        
        return package
    
    def save_flpkg(self, package: Dict[str, Any], filename: str) -> str:
        """儲存 .flpkg 檔案"""
        output_filepath = filename if filename.endswith('.flpkg.json') else f"{filename}.flpkg.json"
        
        with open(output_filepath, 'w', encoding='utf-8') as output_file:
            json.dump(package, output_file, ensure_ascii=False, indent=2)
        
        return output_filepath
    
    def load_flpkg(self, filename: str) -> Dict[str, Any]:
        """載入 .flpkg 檔案"""
        with open(filename, 'r', encoding='utf-8') as input_file:
            return json.load(input_file)
    
    def validate_flpkg(self, package: Dict[str, Any]) -> bool:
        """驗證 .flpkg 封包完整性"""
        required_fields = ["package_type", "compressed", "functions"]
        return all(field in package for field in required_fields)

def interactive_demo():
    """互動式示範"""
    print("== MRLiou 模組壓縮/還原重建器 ==")
    restorer = FunctionRestorer()
    
    while True:
        print("\n選項:")
        print("1. 解壓縮邏輯")
        print("2. 壓縮函數鏈")
        print("3. 建立 .flpkg 封包")
        print("4. 模擬執行")
        print("q. 離開")
        
        choice = input("\n請選擇功能: ").strip()
        
        if choice == "1":
            compressed = input("請輸入壓縮邏輯 (如 SEED(...)): ")
            function_steps = restorer.decompress_fn(compressed)
            print(f"\n還原步驟: {' → '.join(function_steps)}")
            print("\n人類可讀解釋:")
            for line in restorer.to_human_readable(function_steps):
                print(f"  - {line}")
                
        elif choice == "2":
            steps_input = input("請輸入函數步驟 (用逗號分隔): ")
            function_steps = [s.strip() for s in steps_input.split(",")]
            compressed = restorer.compress_fn(function_steps)
            print(f"\n壓縮結果: {compressed}")
            
        elif choice == "3":
            steps_input = input("請輸入函數步驟 (用逗號分隔): ")
            function_steps = [s.strip() for s in steps_input.split(",")]
            package = restorer.create_flpkg_package(function_steps)
            filename = input("輸入檔案名稱 (不含副檔名): ")
            
            if not os.path.exists("examples"):
                os.makedirs("examples")
            
            filepath = restorer.save_flpkg(package, f"examples/{filename}")
            print(f"\n封包已儲存至: {filepath}")
            
        elif choice == "4":
            steps_input = input("請輸入函數步驟 (用逗號分隔): ")
            function_steps = [s.strip() for s in steps_input.split(",")]
            input_data = input("請輸入測試資料: ")
            result = restorer.simulate_execution(function_steps, input_data)
            print(f"\n模擬執行結果: {result}")
            
        elif choice.lower() == "q":
            print("程式結束")
            break
        else:
            print("無效選項，請重新選擇")

def main():
    """主函數，用於命令列執行"""
    import sys
    
    if len(sys.argv) > 1:
        # 命令列模式
        compressed = sys.argv[1]
        restorer = FunctionRestorer()
        function_steps = restorer.decompress_fn(compressed)
        
        print("還原步驟:")
        for step in function_steps:
            print(f"- {step}")
        
        print("\n人類可讀解釋:")
        for line in restorer.to_human_readable(function_steps):
            print(f"- {line}")
        
        print("\n模擬執行流程:")
        print(restorer.simulate_execution(function_steps))
    else:
        # 互動模式
        interactive_demo()

if __name__ == "__main__":
    main()