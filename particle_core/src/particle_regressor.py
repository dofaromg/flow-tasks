#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MrLioū.Particle.Mrlword.v1 - 粒子回溯/迴歸模組
Particle Regression Module for reverse-tracing particle states

公式: P_{k-1} = P_k / (N_{k-1} * η_{k-1})
用途: 用於反推、回溯粒子狀態，幫助記憶還原
備註: 對應 Growth 粒子，形成正向/逆向一對
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import os


class ParticleRegressor:
    """
    MrLioū 粒子回溯器 (Particle Regressor)
    
    用於反向追蹤粒子狀態，實現記憶還原功能。
    與 Growth 粒子形成正向/逆向一對。
    """
    
    def __init__(self):
        """初始化粒子回溯器"""
        self.version = "v1"
        self.particle_id = f"MrLioū.Particle.Mrlword.{self.version}"
        
        # 標準邏輯管線步驟（正向）
        self.forward_steps = ["structure", "mark", "flow", "recurse", "store"]
        
        # 逆向邏輯管線步驟（回溯）
        self.backward_steps = ["store", "recurse", "flow", "mark", "structure"]
        
        # 逆向符號映射（避免首字母碰撞）
        self.regress_symbol_map = {
            "store": "STR",
            "recurse": "RCR",
            "flow": "FLR",
            "mark": "MKR",
            "structure": "STR_R"
        }
        
        # 步驟解釋（回溯模式）
        self.backward_explanations = {
            "store": "從封存狀態提取記憶",
            "recurse": "收縮遞歸展開結構",
            "flow": "逆轉流程結構節奏",
            "mark": "解除邏輯跳點標記",
            "structure": "還原為原始資料結構"
        }
    
    def regress_state(
        self,
        p_k: float,
        n_k_minus_1: float,
        eta_k_minus_1: float
    ) -> float:
        """
        執行粒子狀態回歸計算
        
        公式: P_{k-1} = P_k / (N_{k-1} * η_{k-1})
        
        Args:
            p_k: 當前粒子狀態值 P_k
            n_k_minus_1: 前一層的數量因子 N_{k-1}
            eta_k_minus_1: 前一層的效率因子 η_{k-1}
            
        Returns:
            回歸後的粒子狀態值 P_{k-1}
            
        Raises:
            ValueError: 當 n_k_minus_1 或 eta_k_minus_1 為零時
        """
        if n_k_minus_1 == 0:
            raise ValueError("數量因子 N_{k-1} 不能為零")
        if eta_k_minus_1 == 0:
            raise ValueError("效率因子 η_{k-1} 不能為零")
        
        p_k_minus_1 = p_k / (n_k_minus_1 * eta_k_minus_1)
        return p_k_minus_1
    
    def growth_state(
        self,
        p_k_minus_1: float,
        n_k_minus_1: float,
        eta_k_minus_1: float
    ) -> float:
        """
        執行粒子狀態成長計算（正向，與回歸互補）
        
        公式: P_k = P_{k-1} * N_{k-1} * η_{k-1}
        
        Args:
            p_k_minus_1: 前一層粒子狀態值 P_{k-1}
            n_k_minus_1: 當前層的數量因子 N_{k-1}
            eta_k_minus_1: 當前層的效率因子 η_{k-1}
            
        Returns:
            成長後的粒子狀態值 P_k
        """
        p_k = p_k_minus_1 * n_k_minus_1 * eta_k_minus_1
        return p_k
    
    def regress_logic_chain(self, input_data: str) -> str:
        """
        執行完整的逆向邏輯鏈
        
        Args:
            input_data: 輸入資料
            
        Returns:
            逆向處理結果
        """
        result = input_data
        for step in self.backward_steps:
            result = f"[{step.upper()}_REGRESS → {result}]"
        return result
    
    def backtrack_memory(
        self,
        memory_state: Dict[str, Any],
        steps_to_backtrack: int = 1
    ) -> List[Dict[str, Any]]:
        """
        回溯記憶狀態
        
        Args:
            memory_state: 當前記憶狀態
            steps_to_backtrack: 要回溯的步數
            
        Returns:
            回溯歷史列表
        """
        backtrack_history = []
        current_state = memory_state.copy()
        
        for i in range(steps_to_backtrack):
            # 模擬回溯過程
            backtracked = {
                "step": i + 1,
                "operation": "REGRESS",
                "from_state": current_state.copy(),
                "backward_step": self.backward_steps[i % len(self.backward_steps)],
                "explanation": self.backward_explanations.get(
                    self.backward_steps[i % len(self.backward_steps)],
                    "未知操作"
                ),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # 更新狀態
            current_state["regress_count"] = current_state.get("regress_count", 0) + 1
            backtracked["to_state"] = current_state.copy()
            
            backtrack_history.append(backtracked)
        
        return backtrack_history
    
    def trace_particle_path(
        self,
        states: List[float],
        n_factors: List[float],
        eta_factors: List[float]
    ) -> Dict[str, Any]:
        """
        追蹤粒子路徑（正向與逆向）
        
        Args:
            states: 粒子狀態列表
            n_factors: 數量因子列表
            eta_factors: 效率因子列表
            
        Returns:
            追蹤結果，包含正向和逆向路徑
        """
        if not states or not n_factors or not eta_factors:
            raise ValueError("輸入列表不能為空")
        
        if len(n_factors) != len(eta_factors):
            raise ValueError("n_factors 和 eta_factors 長度必須相同")
        
        # 正向追蹤 (Growth)
        forward_path = []
        current = states[0]
        forward_path.append({"step": 0, "value": current, "operation": "initial"})
        
        for i, (n, eta) in enumerate(zip(n_factors, eta_factors)):
            current = self.growth_state(current, n, eta)
            forward_path.append({
                "step": i + 1,
                "value": current,
                "operation": "growth",
                "n_factor": n,
                "eta_factor": eta
            })
        
        # 逆向追蹤 (Regress)
        backward_path = []
        backward_path.append({"step": 0, "value": current, "operation": "initial"})
        
        for i in range(len(n_factors) - 1, -1, -1):
            n, eta = n_factors[i], eta_factors[i]
            current = self.regress_state(current, n, eta)
            backward_path.append({
                "step": len(n_factors) - i,
                "value": current,
                "operation": "regress",
                "n_factor": n,
                "eta_factor": eta
            })
        
        start_value = states[0]
        return {
            "particle_id": self.particle_id,
            "forward_path": forward_path,
            "backward_path": backward_path,
            "start_value": start_value,
            "verified": abs(backward_path[-1]["value"] - start_value) < 1e-10
        }
    
    def compress_regress_chain(self) -> str:
        """
        壓縮逆向邏輯鏈為 .flpkg 格式
        
        Returns:
            壓縮後的邏輯鏈字串
        """
        # 建構巢狀結構（逆向），使用定義的符號映射避免碰撞
        nested = "X"
        for step in self.backward_steps:
            symbol = self.regress_symbol_map.get(step, step[0].upper() + "R")
            nested = f"{symbol}({nested})"
        
        return f"REGRESS_SEED(X) = {nested}"
    
    def decompress_regress_chain(self, compressed: str) -> List[str]:
        """
        解壓縮逆向邏輯鏈
        
        Args:
            compressed: 壓縮的邏輯鏈字串
            
        Returns:
            解壓縮後的步驟列表
        """
        if "REGRESS_SEED" in compressed:
            return self.backward_steps
        return ["UNKNOWN"]
    
    def simulate(self, input_data: str) -> Dict[str, Any]:
        """
        完整模擬回歸執行流程
        
        Args:
            input_data: 輸入資料
            
        Returns:
            模擬結果字典
        """
        result = self.regress_logic_chain(input_data)
        
        return {
            "particle_id": self.particle_id,
            "version": self.version,
            "input": input_data,
            "backward_steps": self.backward_steps,
            "explanations": [
                self.backward_explanations.get(step, step) 
                for step in self.backward_steps
            ],
            "result": result,
            "compressed": self.compress_regress_chain(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def store_result(
        self,
        input_value: str,
        result: str,
        output_dir: str = "examples"
    ) -> str:
        """
        儲存執行結果
        
        Args:
            input_value: 輸入值
            result: 執行結果
            output_dir: 輸出目錄
            
        Returns:
            儲存的檔案路徑
        """
        os.makedirs(output_dir, exist_ok=True)
        
        data = {
            "particle_id": self.particle_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input": input_value,
            "backward_chain": self.backward_steps,
            "explanations": [
                self.backward_explanations.get(step, step) 
                for step in self.backward_steps
            ],
            "result": result,
            "compressed": self.compress_regress_chain()
        }
        
        filename = os.path.join(
            output_dir,
            f"regress_result_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filename


def demo_regressor():
    """示範粒子回溯器功能"""
    print("=== MrLioū.Particle.Mrlword.v1 - 粒子回溯器 ===\n")
    
    regressor = ParticleRegressor()
    
    # 1. 基本回歸計算示範
    print("1. 粒子狀態回歸計算:")
    p_k = 100.0
    n = 2.0
    eta = 0.5
    p_k_minus_1 = regressor.regress_state(p_k, n, eta)
    print(f"   P_k = {p_k}")
    print(f"   N_{{k-1}} = {n}, η_{{k-1}} = {eta}")
    print(f"   P_{{k-1}} = P_k / (N_{{k-1}} * η_{{k-1}}) = {p_k_minus_1}\n")
    
    # 2. 正向/逆向互補驗證
    print("2. Growth/Regress 互補驗證:")
    initial = 50.0
    grown = regressor.growth_state(initial, n, eta)
    regressed = regressor.regress_state(grown, n, eta)
    print(f"   初始值: {initial}")
    print(f"   Growth 後: {grown}")
    print(f"   Regress 後: {regressed}")
    print(f"   驗證一致: {abs(initial - regressed) < 1e-10}\n")
    
    # 3. 逆向邏輯鏈執行
    print("3. 逆向邏輯鏈執行:")
    simulation = regressor.simulate("MRLiou 記憶資料")
    print(f"   粒子 ID: {simulation['particle_id']}")
    print(f"   逆向步驟: {' → '.join(simulation['backward_steps'])}")
    print(f"   壓縮格式: {simulation['compressed']}\n")
    
    # 4. 粒子路徑追蹤
    print("4. 粒子路徑追蹤:")
    trace = regressor.trace_particle_path(
        states=[10.0],
        n_factors=[2.0, 3.0, 1.5],
        eta_factors=[0.8, 0.9, 1.0]
    )
    print(f"   起始值: {trace['start_value']}")
    print(f"   正向路徑終點: {trace['forward_path'][-1]['value']:.4f}")
    print(f"   逆向路徑終點: {trace['backward_path'][-1]['value']:.4f}")
    print(f"   完整驗證: {trace['verified']}\n")
    
    print("=== 示範完成 ===")


def main():
    """主函數"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_regressor()
    else:
        # 互動模式
        print("MrLioū.Particle.Mrlword.v1 - 粒子回溯器")
        print("使用方式: python particle_regressor.py demo")
        print("\n可用功能:")
        print("  - regress_state(): 執行粒子狀態回歸")
        print("  - growth_state(): 執行粒子狀態成長")
        print("  - regress_logic_chain(): 執行逆向邏輯鏈")
        print("  - trace_particle_path(): 追蹤粒子路徑")
        print("  - simulate(): 完整模擬回歸流程")


if __name__ == "__main__":
    main()
