"""
structure.py - 中心不變的骨架定義
Central Invariant Structure Definition

定義 ring/sector/cell 三層結構骨架，保持中心不變性
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class StructureNode:
    """結構節點 - 包含 ring/sector/cell 位置信息"""
    
    node_id: str
    ring: int  # 環層編號 (0 = 中心)
    sector: int  # 扇區編號
    cell: int  # 單元編號
    data: Dict = field(default_factory=dict)  # 節點附加資料
    
    # Pressure field properties
    N: float = 1.0  # 節點強度
    eta: float = 1.0  # 阻尼係數
    alpha: float = 1.0  # 放大係數
    beta: float = 1.0  # 偏移係數
    
    def __repr__(self):
        return f"Node({self.node_id}, R{self.ring}S{self.sector}C{self.cell})"
    
    def to_dict(self) -> Dict:
        """轉為字典格式"""
        return {
            "node_id": self.node_id,
            "ring": self.ring,
            "sector": self.sector,
            "cell": self.cell,
            "N": self.N,
            "eta": self.eta,
            "alpha": self.alpha,
            "beta": self.beta,
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "StructureNode":
        """從字典創建節點"""
        return cls(
            node_id=data["node_id"],
            ring=data.get("ring", 0),
            sector=data.get("sector", 0),
            cell=data.get("cell", 0),
            N=data.get("N", 1.0),
            eta=data.get("eta", 1.0),
            alpha=data.get("alpha", 1.0),
            beta=data.get("beta", 1.0),
            data=data.get("data", {}),
        )


class EarthStructure:
    """
    Earth Structure - 地球結構骨架
    中心不變的三層結構：ring → sector → cell
    """
    
    def __init__(self, center_node: Optional[StructureNode] = None):
        """初始化結構，可選中心節點"""
        self.nodes: Dict[str, StructureNode] = {}
        self.edges: List[Tuple[str, str]] = []  # (src_id, dst_id)
        
        # 設定中心節點 (ring=0, sector=0, cell=0)
        if center_node is None:
            center_node = StructureNode(
                node_id="center",
                ring=0,
                sector=0,
                cell=0,
                data={"is_center": True}
            )
        self.center_id = center_node.node_id
        self.add_node(center_node)
    
    def add_node(self, node: StructureNode) -> None:
        """添加節點到結構"""
        self.nodes[node.node_id] = node
    
    def add_edge(self, src_id: str, dst_id: str) -> None:
        """添加邊連接"""
        if src_id in self.nodes and dst_id in self.nodes:
            self.edges.append((src_id, dst_id))
    
    def get_node(self, node_id: str) -> Optional[StructureNode]:
        """獲取節點"""
        return self.nodes.get(node_id)
    
    def get_nodes_by_ring(self, ring: int) -> List[StructureNode]:
        """獲取指定環層的所有節點"""
        return [n for n in self.nodes.values() if n.ring == ring]
    
    def get_nodes_by_sector(self, ring: int, sector: int) -> List[StructureNode]:
        """獲取指定扇區的所有節點"""
        return [n for n in self.nodes.values() if n.ring == ring and n.sector == sector]
    
    def apply_ring_lift(self, lift: int) -> None:
        """
        對所有非中心節點應用 ring lift（環層提升）
        lift > 0: 向外擴展
        lift < 0: 向內收縮（但不會小於1）
        """
        for node in self.nodes.values():
            if node.ring > 0:  # 不改變中心節點
                node.ring = max(1, node.ring + lift)
    
    def apply_sector_shift(self, shift: int) -> None:
        """
        對所有節點應用 sector shift（扇區旋轉）
        shift > 0: 順時針旋轉
        shift < 0: 逆時針旋轉
        """
        max_sector = max(n.sector for n in self.nodes.values())
        for node in self.nodes.values():
            if node.ring > 0:  # 只旋轉非中心節點
                node.sector = (node.sector + shift) % (max_sector + 1)
    
    def to_dict(self) -> Dict:
        """導出為字典格式"""
        return {
            "center_id": self.center_id,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": self.edges,
        }
    
    def save_to_file(self, filepath: str) -> None:
        """保存結構到 JSON 文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EarthStructure":
        """從字典加載結構"""
        center_id = data["center_id"]
        center_data = data["nodes"][center_id]
        center_node = StructureNode.from_dict(center_data)
        
        structure = cls(center_node=center_node)
        
        # 添加其他節點
        for node_id, node_data in data["nodes"].items():
            if node_id != center_id:
                structure.add_node(StructureNode.from_dict(node_data))
        
        # 添加邊
        for src, dst in data["edges"]:
            structure.add_edge(src, dst)
        
        return structure
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "EarthStructure":
        """從 JSON 文件加載結構"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def __repr__(self):
        return f"EarthStructure(nodes={len(self.nodes)}, edges={len(self.edges)})"
