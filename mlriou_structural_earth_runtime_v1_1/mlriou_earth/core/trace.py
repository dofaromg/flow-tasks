"""
trace.py - 運轉軌跡記錄
Trace Recording

記錄系統運轉的完整軌跡，支持前進/後退回放
輸出格式：JSONL (每行一個 JSON 對象)
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class TraceRecord:
    """軌跡記錄項"""
    tick: int  # 時間步
    event_type: str  # 事件類型：projection, jump, structure_change 等
    node_id: str  # 相關節點 ID
    data: Dict[str, Any]  # 事件數據
    
    def to_dict(self) -> Dict:
        """轉為字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """轉為 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class TraceRecorder:
    """
    軌跡記錄器
    
    功能：
    1. 記錄所有系統事件（壓力投影、跳層、結構變化）
    2. 支持流式寫入 JSONL 文件
    3. 提供回放數據的查詢接口
    """
    
    def __init__(self, output_file: Optional[str] = None):
        """
        初始化軌跡記錄器
        
        Args:
            output_file: 輸出文件路徑（JSONL 格式）
        """
        self.output_file = output_file
        self.records: List[TraceRecord] = []
        self.file_handle = None
        
        if output_file:
            self.open_file(output_file)
    
    def open_file(self, filepath: str) -> None:
        """打開輸出文件"""
        self.output_file = filepath
        self.file_handle = open(filepath, 'w', encoding='utf-8')
    
    def close_file(self) -> None:
        """關閉輸出文件"""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
    
    def record_projection(
        self,
        tick: int,
        node_id: str,
        pressure_before: float,
        pressure_after: float,
        energy: float,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        記錄壓力投影事件
        
        Args:
            tick: 時間步
            node_id: 節點 ID
            pressure_before: 投影前壓力
            pressure_after: 投影後壓力
            energy: 能量值
            metadata: 附加元數據
        """
        record = TraceRecord(
            tick=tick,
            event_type="projection",
            node_id=node_id,
            data={
                "pressure_before": pressure_before,
                "pressure_after": pressure_after,
                "pressure_delta": pressure_after - pressure_before,
                "energy": energy,
                "metadata": metadata or {},
            }
        )
        self._write_record(record)
    
    def record_jump(
        self,
        tick: int,
        source_node_id: str,
        jump_node_id: str,
        pressure: float,
        target_ring: int,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        記錄跳層事件
        
        Args:
            tick: 時間步
            source_node_id: 源節點 ID
            jump_node_id: 跳層節點 ID
            pressure: 觸發壓力
            target_ring: 目標環層
            metadata: 附加元數據
        """
        record = TraceRecord(
            tick=tick,
            event_type="jump",
            node_id=source_node_id,
            data={
                "jump": True,
                "jump_node_id": jump_node_id,
                "pressure": pressure,
                "target_ring": target_ring,
                "metadata": metadata or {},
            }
        )
        self._write_record(record)
    
    def record_structure_change(
        self,
        tick: int,
        change_type: str,
        node_id: str,
        details: Dict
    ) -> None:
        """
        記錄結構變化事件（ring lift, sector shift 等）
        
        Args:
            tick: 時間步
            change_type: 變化類型（ring_lift, sector_shift 等）
            node_id: 相關節點 ID
            details: 變化詳情
        """
        record = TraceRecord(
            tick=tick,
            event_type="structure_change",
            node_id=node_id,
            data={
                "change_type": change_type,
                "details": details,
            }
        )
        self._write_record(record)
    
    def _write_record(self, record: TraceRecord) -> None:
        """寫入記錄"""
        self.records.append(record)
        
        # 如果有文件句柄，立即寫入
        if self.file_handle:
            self.file_handle.write(record.to_json() + '\n')
            self.file_handle.flush()
    
    def get_records_up_to_tick(self, tick: int) -> List[TraceRecord]:
        """獲取到指定時間步為止的所有記錄"""
        return [r for r in self.records if r.tick <= tick]
    
    def get_records_at_tick(self, tick: int) -> List[TraceRecord]:
        """獲取指定時間步的所有記錄"""
        return [r for r in self.records if r.tick == tick]
    
    def get_records_by_node(self, node_id: str) -> List[TraceRecord]:
        """獲取特定節點的所有記錄"""
        return [r for r in self.records if r.node_id == node_id]
    
    def get_records_by_type(self, event_type: str) -> List[TraceRecord]:
        """獲取特定類型的所有記錄"""
        return [r for r in self.records if r.event_type == event_type]
    
    def get_max_tick(self) -> int:
        """獲取最大時間步"""
        return max((r.tick for r in self.records), default=0)
    
    def save_to_file(self, filepath: str) -> None:
        """保存所有記錄到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for record in self.records:
                f.write(record.to_json() + '\n')
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "TraceRecorder":
        """從文件加載軌跡記錄"""
        recorder = cls()
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    record = TraceRecord(**data)
                    recorder.records.append(record)
        return recorder
    
    def get_statistics(self) -> Dict:
        """獲取統計信息"""
        return {
            "total_records": len(self.records),
            "max_tick": self.get_max_tick(),
            "event_types": {
                event_type: len(self.get_records_by_type(event_type))
                for event_type in set(r.event_type for r in self.records)
            },
            "unique_nodes": len(set(r.node_id for r in self.records)),
        }
    
    def __repr__(self):
        return f"TraceRecorder(records={len(self.records)}, max_tick={self.get_max_tick()})"
    
    def __del__(self):
        """析構時關閉文件"""
        self.close_file()
