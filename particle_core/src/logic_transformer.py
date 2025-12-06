# MRLiou 壓縮/還原轉化器
# Logic compression and transformation utilities

import json
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime

class LogicTransformer:
    """MRLiou 邏輯轉化器"""
    
    def __init__(self):
        # 簡易對應映射
        self.compress_map = {
            "structure": "S",
            "mark": "M", 
            "flow": "F",
            "recurse": "R",
            "store": "ST"
        }
        
        self.expand_map = {v: k for k, v in self.compress_map.items()}
        
        # 預定義轉換規則
        self.transformation_rules = {
            "standard": ["structure", "mark", "flow", "recurse", "store"],
            "minimal": ["structure", "store"],
            "extended": ["structure", "mark", "flow", "recurse", "generate_persona", "store"],
            "debug": ["structure", "mark", "debug", "flow", "recurse", "store"]
        }
    
    def compress_to_symbols(self, function_list: List[str]) -> str:
        """壓縮函數列表為符號表示"""
        symbols = []
        for function_name in function_list:
            symbol = self.compress_map.get(function_name, function_name[0].upper())
            symbols.append(symbol)
        return "(" + "→".join(symbols) + ")"
    
    def expand_from_symbols(self, symbol_string: str) -> List[str]:
        """從符號表示展開函數列表"""
        # 移除括號並分割
        clean_string = symbol_string.strip("()")
        symbols = clean_string.split("→")
        
        expanded = []
        for symbol in symbols:
            expanded_name = self.expand_map.get(symbol.strip(), symbol.lower())
            expanded.append(expanded_name)
        
        return expanded
    
    def compress_to_flpkg(self, function_list: List[str], compact: bool = False) -> str:
        """壓縮函數鏈為 .flpkg 形式"""
        if compact:
            # 緊湊模式
            return self.compress_to_symbols(function_list)
        
        # 標準模式
        if function_list == self.transformation_rules["standard"]:
            return "SEED(X) = ST(R(F(M(S(X)))))"
        
        # 動態建構
        if len(function_list) > 0:
            nested = "X"
            for function_name in function_list:
                symbol = self.compress_map.get(function_name, function_name[0].upper())
                nested = f"{symbol}({nested})"
            return f"CUSTOM_SEED(X) = {nested}"
        
        return "EMPTY(X)"
    
    def expand_from_flpkg(self, flpkg_string: str) -> List[str]:
        """從 .flpkg 形式還原函數鏈"""
        # 處理標準格式
        if "SEED(X)" in flpkg_string and "ST(R(F(M(S(X)))))" in flpkg_string:
            return self.transformation_rules["standard"]
        
        # 處理自定義格式
        if "CUSTOM_SEED(X)" in flpkg_string:
            # 解析巢狀結構
            return self._parse_nested_structure(flpkg_string)
        
        # 處理符號格式
        if "→" in flpkg_string:
            return self.expand_from_symbols(flpkg_string)
        
        return ["UNKNOWN"]
    
    def _parse_nested_structure(self, custom_seed: str) -> List[str]:
        """解析自定義巢狀結構"""
        # 簡化解析：找到等號後的部分
        if "=" in custom_seed:
            right_side = custom_seed.split("=", 1)[1].strip()
            # 這裡可以實作更複雜的解析邏輯
            # 目前返回標準序列
            return self.transformation_rules["standard"]
        
        return ["PARSE_ERROR"]
    
    def transform_to_preset(self, preset_name: str) -> List[str]:
        """轉換為預設規則"""
        return self.transformation_rules.get(preset_name, [])
    
    def create_transformation_map(self, function_list: List[str]) -> Dict[str, Any]:
        """建立轉換映射表"""
        return {
            "original": function_list,
            "symbols": self.compress_to_symbols(function_list),
            "flpkg_standard": self.compress_to_flpkg(function_list, compact=False),
            "flpkg_compact": self.compress_to_flpkg(function_list, compact=True),
            "length": len(function_list),
            "complexity": self._calculate_complexity(function_list)
        }
    
    def _calculate_complexity(self, function_list: List[str]) -> str:
        """計算邏輯複雜度"""
        length = len(function_list)
        if length <= 2:
            return "simple"
        elif length <= 5:
            return "standard"
        elif length <= 8:
            return "complex"
        else:
            return "advanced"
    
    def export_to_json(self, function_list: List[str], metadata: Dict = None) -> Dict[str, Any]:
        """匯出為 JSON 模組描述"""
        if metadata is None:
            metadata = {}
        
        transformation_map = self.create_transformation_map(function_list)
        
        return {
            "module_type": "logic_function_chain",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "functions": function_list,
            "transformations": transformation_map,
            "compressed": transformation_map["flpkg_standard"],
            "signature": f"MRLSIG-TRANSFORM-{hash(str(function_list)) % 10000:04d}",
            "recursive": True,
            "metadata": metadata
        }
    
    def batch_transform(self, preset_names: List[str]) -> Dict[str, Dict]:
        """批次轉換多個預設規則"""
        results = {}
        for preset in preset_names:
            function_list = self.transform_to_preset(preset)
            results[preset] = self.create_transformation_map(function_list)
        return results
    
    def validate_transformation(self, original: List[str], transformed: str) -> bool:
        """驗證轉換正確性"""
        try:
            restored = self.expand_from_flpkg(transformed)
            return original == restored
        except:
            return False

def demo_transformations():
    """示範轉換功能"""
    print("== MRLiou 壓縮與展開轉化器 ==")
    transformer = LogicTransformer()
    
    # 示範各種轉換
    test_functions = ["structure", "mark", "flow", "recurse", "store"]
    
    print(f"原始函數: {test_functions}")
    
    # 符號壓縮
    symbols = transformer.compress_to_symbols(test_functions)
    print(f"符號表示: {symbols}")
    
    # FLPKG 壓縮
    flpkg_standard = transformer.compress_to_flpkg(test_functions, compact=False)
    flpkg_compact = transformer.compress_to_flpkg(test_functions, compact=True)
    print(f"FLPKG 標準: {flpkg_standard}")
    print(f"FLPKG 緊湊: {flpkg_compact}")
    
    # 還原測試
    restored = transformer.expand_from_flpkg(flpkg_standard)
    print(f"還原結果: {restored}")
    
    # JSON 匯出
    json_export = transformer.export_to_json(test_functions)
    print("\nJSON 匯出:")
    print(json.dumps(json_export, indent=2, ensure_ascii=False))
    
    # 批次轉換
    batch_results = transformer.batch_transform(["standard", "minimal", "extended"])
    print(f"\n批次轉換結果:")
    for preset, result in batch_results.items():
        print(f"{preset}: {result['original']} -> {result['symbols']}")

def interactive_transformer():
    """互動式轉化器"""
    transformer = LogicTransformer()
    
    while True:
        print("\n=== 轉化器選項 ===")
        print("1. 函數鏈壓縮")
        print("2. 壓縮格式還原")
        print("3. 預設規則轉換")
        print("4. 批次轉換測試")
        print("5. JSON 匯出")
        print("q. 離開")
        
        choice = input("\n請選擇功能: ").strip()
        
        if choice == "1":
            functions_input = input("請輸入函數 (用逗號分隔): ")
            function_list = [f.strip() for f in functions_input.split(",")]
            
            symbols = transformer.compress_to_symbols(function_list)
            flpkg = transformer.compress_to_flpkg(function_list)
            
            print(f"符號表示: {symbols}")
            print(f"FLPKG 格式: {flpkg}")
            
        elif choice == "2":
            compressed = input("請輸入壓縮格式: ")
            restored = transformer.expand_from_flpkg(compressed)
            print(f"還原結果: {' → '.join(restored)}")
            
        elif choice == "3":
            print("可用預設: standard, minimal, extended, debug")
            preset = input("請選擇預設規則: ")
            function_list = transformer.transform_to_preset(preset)
            print(f"{preset} 規則: {' → '.join(function_list)}")
            
        elif choice == "4":
            results = transformer.batch_transform(["standard", "minimal", "extended"])
            for preset, result in results.items():
                print(f"{preset}: {result['symbols']}")
                
        elif choice == "5":
            functions_input = input("請輸入函數 (用逗號分隔): ")
            function_list = [f.strip() for f in functions_input.split(",")]
            
            json_export = transformer.export_to_json(function_list)
            
            filename = input("輸入檔案名稱 (不含副檔名): ")
            if not os.path.exists("examples"):
                os.makedirs("examples")
            
            filepath = f"examples/{filename}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_export, f, ensure_ascii=False, indent=2)
            
            print(f"JSON 已儲存至: {filepath}")
            
        elif choice.lower() == "q":
            print("轉化器結束")
            break
        else:
            print("無效選項")

def main():
    """主函數"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_transformations()
    else:
        interactive_transformer()

if __name__ == "__main__":
    main()