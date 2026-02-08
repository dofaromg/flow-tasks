"""
projection.py - 壓力場映射
Pressure Field Projection

使用 N/eta/alpha/beta 更新壓力 Pk→P_next
實現運轉能量最小化的壓力場計算
"""

import math
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class PressureState:
    """壓力狀態"""
    pressure: float  # 當前壓力值
    energy: float  # 能量值
    tick: int  # 時間步
    metadata: Dict = None  # 附加元數據
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PressureProjection:
    """
    壓力場映射器
    
    核心公式：
    P_next = f(N, eta, alpha, beta, P_k)
    
    其中：
    - N: 節點強度
    - eta: 阻尼係數（能量耗散）
    - alpha: 放大係數（壓力增益）
    - beta: 偏移係數（基準調整）
    - P_k: 當前壓力
    """
    
    def __init__(self, alpha_global: float = 2.0):
        """
        初始化壓力場映射器
        
        Args:
            alpha_global: 全局放大係數（默認 2.0）
        """
        self.alpha_global = alpha_global
        self.pressure_states: Dict[str, PressureState] = {}
        self.current_tick = 0
    
    def compute_next_pressure(
        self,
        node_id: str,
        N: float,
        eta: float,
        alpha: float,
        beta: float,
        P_current: float,
        external_force: float = 0.0
    ) -> float:
        """
        計算下一步的壓力值
        
        公式：
        P_next = (N / eta) * alpha * P_current + beta + external_force
        
        為了能量最小化，加入阻尼項：
        P_next = P_next * exp(-eta * dt)
        
        Args:
            node_id: 節點 ID
            N: 節點強度
            eta: 阻尼係數
            alpha: 局部放大係數
            beta: 偏移係數
            P_current: 當前壓力
            external_force: 外部力（默認 0）
        
        Returns:
            下一步壓力值
        """
        # 使用全局和局部 alpha 的乘積
        effective_alpha = self.alpha_global * alpha
        
        # 基礎壓力計算
        P_base = (N / max(eta, 0.01)) * effective_alpha * P_current + beta
        
        # 加上外部力
        P_with_force = P_base + external_force
        
        # 能量最小化：應用阻尼因子
        # dt = 1 (單位時間步)
        damping_factor = math.exp(-eta * 1.0)
        P_next = P_with_force * damping_factor
        
        return P_next
    
    def project(
        self,
        node_id: str,
        N: float,
        eta: float,
        alpha: float,
        beta: float,
        P_current: Optional[float] = None,
        external_force: float = 0.0
    ) -> PressureState:
        """
        執行壓力投影，更新節點的壓力狀態
        
        Args:
            node_id: 節點 ID
            N: 節點強度
            eta: 阻尼係數
            alpha: 局部放大係數
            beta: 偏移係數
            P_current: 當前壓力（如果為 None，從狀態中獲取或初始化為 1.0）
            external_force: 外部力
        
        Returns:
            更新後的壓力狀態
        """
        # 獲取或初始化當前壓力
        if P_current is None:
            if node_id in self.pressure_states:
                P_current = self.pressure_states[node_id].pressure
            else:
                P_current = 1.0  # 初始壓力
        
        # 計算下一步壓力
        P_next = self.compute_next_pressure(
            node_id, N, eta, alpha, beta, P_current, external_force
        )
        
        # 計算能量（簡化模型：能量 = 壓力^2）
        energy = P_next ** 2
        
        # 創建新狀態
        new_state = PressureState(
            pressure=P_next,
            energy=energy,
            tick=self.current_tick,
            metadata={
                "N": N,
                "eta": eta,
                "alpha": alpha,
                "beta": beta,
                "P_prev": P_current,
                "external_force": external_force,
            }
        )
        
        # 更新狀態記錄
        self.pressure_states[node_id] = new_state
        
        return new_state
    
    def get_pressure(self, node_id: str) -> Optional[float]:
        """獲取節點當前壓力"""
        state = self.pressure_states.get(node_id)
        return state.pressure if state else None
    
    def get_state(self, node_id: str) -> Optional[PressureState]:
        """獲取節點完整壓力狀態"""
        return self.pressure_states.get(node_id)
    
    def advance_tick(self) -> None:
        """推進時間步"""
        self.current_tick += 1
    
    def reset(self) -> None:
        """重置所有壓力狀態"""
        self.pressure_states.clear()
        self.current_tick = 0
    
    def get_total_energy(self) -> float:
        """計算系統總能量"""
        return sum(state.energy for state in self.pressure_states.values())
    
    def __repr__(self):
        return f"PressureProjection(tick={self.current_tick}, nodes={len(self.pressure_states)})"
