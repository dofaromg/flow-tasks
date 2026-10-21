"""
jump.py - 跳層衍生
Jump Layer Derivation

當 pressure >= threshold 時，自動生成 synthetic jump node
實現跨層級的壓力傳遞機制
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from .structure import StructureNode


@dataclass
class JumpNode:
    """跳層節點"""
    jump_id: str
    source_node_id: str
    target_ring: int
    pressure: float
    created_at_tick: int
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self):
        return {
            "jump_id": self.jump_id,
            "source_node_id": self.source_node_id,
            "target_ring": self.target_ring,
            "pressure": self.pressure,
            "created_at_tick": self.created_at_tick,
            "metadata": self.metadata,
        }


class JumpManager:
    """
    跳層管理器
    
    功能：
    1. 監測節點壓力
    2. 當 pressure >= threshold 時創建 synthetic jump node
    3. 記錄跳層邊 (source → jump_node)
    4. 管理跳層節點生命週期
    """
    
    def __init__(self, pressure_threshold: float = 20.0):
        """
        初始化跳層管理器
        
        Args:
            pressure_threshold: 壓力閾值（超過此值觸發跳層）
        """
        self.pressure_threshold = pressure_threshold
        self.jump_nodes: List[JumpNode] = []
        self.jump_edges: List[Tuple[str, str]] = []  # (source_id, jump_id)
        self.jump_counter = 0
    
    def check_and_create_jump(
        self,
        source_node: StructureNode,
        pressure: float,
        current_tick: int
    ) -> Optional[JumpNode]:
        """
        檢查是否需要創建跳層節點
        
        Args:
            source_node: 源節點
            pressure: 當前壓力值
            current_tick: 當前時間步
        
        Returns:
            如果創建了跳層節點，返回 JumpNode；否則返回 None
        """
        if pressure < self.pressure_threshold:
            return None
        
        # 計算目標環層：跳到更外層
        # 跳躍距離與壓力超過閾值的程度成正比
        excess_pressure = pressure - self.pressure_threshold
        jump_distance = max(1, int(excess_pressure / self.pressure_threshold))
        target_ring = source_node.ring + jump_distance
        
        # 創建跳層節點
        self.jump_counter += 1
        jump_id = f"jump_{source_node.node_id}_{self.jump_counter}"
        
        jump_node = JumpNode(
            jump_id=jump_id,
            source_node_id=source_node.node_id,
            target_ring=target_ring,
            pressure=pressure,
            created_at_tick=current_tick,
            metadata={
                "excess_pressure": excess_pressure,
                "jump_distance": jump_distance,
                "source_ring": source_node.ring,
                "source_sector": source_node.sector,
            }
        )
        
        # 記錄跳層節點和邊
        self.jump_nodes.append(jump_node)
        self.jump_edges.append((source_node.node_id, jump_id))
        
        return jump_node
    
    def create_synthetic_node(
        self,
        jump_node: JumpNode,
        source_node: StructureNode
    ) -> StructureNode:
        """
        基於跳層信息創建合成結構節點
        
        Args:
            jump_node: 跳層節點信息
            source_node: 源節點
        
        Returns:
            合成的結構節點
        """
        synthetic_node = StructureNode(
            node_id=jump_node.jump_id,
            ring=jump_node.target_ring,
            sector=source_node.sector,  # 保持相同扇區
            cell=source_node.cell,  # 保持相同單元
            N=source_node.N * 0.5,  # 降低強度（能量分散）
            eta=source_node.eta * 1.5,  # 增加阻尼（穩定性）
            alpha=source_node.alpha,
            beta=source_node.beta,
            data={
                "synthetic": True,
                "jump_source": source_node.node_id,
                "created_at_tick": jump_node.created_at_tick,
            }
        )
        
        return synthetic_node
    
    def get_jump_nodes_for_source(self, source_node_id: str) -> List[JumpNode]:
        """獲取特定源節點的所有跳層節點"""
        return [j for j in self.jump_nodes if j.source_node_id == source_node_id]
    
    def get_jump_nodes_at_tick(self, tick: int) -> List[JumpNode]:
        """獲取特定時間步創建的跳層節點"""
        return [j for j in self.jump_nodes if j.created_at_tick == tick]
    
    def get_all_jump_edges(self) -> List[Tuple[str, str]]:
        """獲取所有跳層邊"""
        return self.jump_edges.copy()
    
    def reset(self) -> None:
        """重置跳層管理器"""
        self.jump_nodes.clear()
        self.jump_edges.clear()
        self.jump_counter = 0
    
    def get_statistics(self) -> dict:
        """獲取跳層統計信息"""
        return {
            "total_jumps": len(self.jump_nodes),
            "total_edges": len(self.jump_edges),
            "threshold": self.pressure_threshold,
            "avg_pressure": sum(j.pressure for j in self.jump_nodes) / len(self.jump_nodes) if self.jump_nodes else 0,
            "max_pressure": max((j.pressure for j in self.jump_nodes), default=0),
        }
    
    def __repr__(self):
        return f"JumpManager(threshold={self.pressure_threshold}, jumps={len(self.jump_nodes)})"
