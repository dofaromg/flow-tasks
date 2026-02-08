"""
player.py - 回放播放器
Replay Player

支持前進/後退回放 trace.jsonl 記錄
可以輸出任意 tick 的狀態快照
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class SnapshotState:
    """快照狀態"""
    tick: int
    node_states: Dict[str, Dict[str, Any]]  # node_id -> state data
    jump_nodes: List[Dict[str, Any]]
    statistics: Dict[str, Any]


class ReplayPlayer:
    """
    回放播放器
    
    功能：
    1. 讀取 trace.jsonl 文件
    2. 支持前進/後退到任意 tick
    3. 生成狀態快照
    4. 支持過濾和查詢
    """
    
    def __init__(self, trace_file: str):
        """
        初始化回放播放器
        
        Args:
            trace_file: trace.jsonl 文件路徑
        """
        self.trace_file = trace_file
        self.records: List[Dict] = []
        self.max_tick = 0
        self._load_trace()
    
    def _load_trace(self) -> None:
        """加載軌跡文件"""
        with open(self.trace_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    self.records.append(record)
                    self.max_tick = max(self.max_tick, record.get('tick', 0))
        
        print(f"✓ 已加載 {len(self.records)} 條記錄，時間範圍: 0 - {self.max_tick}")
    
    def get_snapshot_at_tick(self, tick: int) -> SnapshotState:
        """
        獲取指定 tick 的狀態快照
        
        Args:
            tick: 時間步（可以是任意值，支持前進和後退）
        
        Returns:
            狀態快照
        """
        # 過濾到指定 tick 為止的記錄
        records_up_to_tick = [r for r in self.records if r['tick'] <= tick]
        
        # 構建節點狀態（最新狀態覆蓋舊狀態）
        node_states: Dict[str, Dict[str, Any]] = {}
        jump_nodes: List[Dict[str, Any]] = []
        
        for record in records_up_to_tick:
            node_id = record['node_id']
            event_type = record['event_type']
            
            if event_type == 'projection':
                # 更新節點壓力狀態
                data = record['data']
                node_states[node_id] = {
                    'tick': record['tick'],
                    'pressure': data['pressure_after'],
                    'energy': data['energy'],
                    'pressure_delta': data.get('pressure_delta', 0),
                    'metadata': data.get('metadata', {}),
                }
            
            elif event_type == 'jump':
                # 記錄跳層節點
                data = record['data']
                jump_nodes.append({
                    'tick': record['tick'],
                    'source_node_id': node_id,
                    'jump_node_id': data['jump_node_id'],
                    'pressure': data['pressure'],
                    'target_ring': data['target_ring'],
                    'metadata': data.get('metadata', {}),
                })
        
        # 計算統計信息
        statistics = {
            'tick': tick,
            'total_nodes': len(node_states),
            'total_jumps': len(jump_nodes),
            'total_energy': sum(s['energy'] for s in node_states.values()),
            'avg_pressure': sum(s['pressure'] for s in node_states.values()) / len(node_states) if node_states else 0,
            'max_pressure': max((s['pressure'] for s in node_states.values()), default=0),
        }
        
        return SnapshotState(
            tick=tick,
            node_states=node_states,
            jump_nodes=jump_nodes,
            statistics=statistics
        )
    
    def replay_forward(self, start_tick: int, end_tick: int, step: int = 1) -> List[SnapshotState]:
        """
        前進回放
        
        Args:
            start_tick: 起始時間步
            end_tick: 結束時間步
            step: 步長
        
        Returns:
            快照列表
        """
        snapshots = []
        for tick in range(start_tick, end_tick + 1, step):
            snapshots.append(self.get_snapshot_at_tick(tick))
        return snapshots
    
    def replay_backward(self, start_tick: int, end_tick: int, step: int = 1) -> List[SnapshotState]:
        """
        後退回放
        
        Args:
            start_tick: 起始時間步（較大）
            end_tick: 結束時間步（較小）
            step: 步長
        
        Returns:
            快照列表
        """
        snapshots = []
        for tick in range(start_tick, end_tick - 1, -step):
            snapshots.append(self.get_snapshot_at_tick(tick))
        return snapshots
    
    def print_snapshot(self, snapshot: SnapshotState, verbose: bool = False) -> None:
        """
        打印快照信息
        
        Args:
            snapshot: 快照狀態
            verbose: 是否顯示詳細信息
        """
        print(f"\n{'='*60}")
        print(f"  📸 Tick {snapshot.tick} 快照")
        print(f"{'='*60}")
        
        stats = snapshot.statistics
        print(f"\n📊 統計信息:")
        print(f"  • 節點數量: {stats['total_nodes']}")
        print(f"  • 跳層數量: {stats['total_jumps']}")
        print(f"  • 總能量: {stats['total_energy']:.2f}")
        print(f"  • 平均壓力: {stats['avg_pressure']:.2f}")
        print(f"  • 最大壓力: {stats['max_pressure']:.2f}")
        
        if verbose:
            print(f"\n🔹 節點狀態:")
            for node_id, state in list(snapshot.node_states.items())[:10]:  # 最多顯示10個
                print(f"  • {node_id}: P={state['pressure']:.2f}, E={state['energy']:.2f}")
            
            if len(snapshot.node_states) > 10:
                print(f"  ... 還有 {len(snapshot.node_states) - 10} 個節點")
            
            if snapshot.jump_nodes:
                print(f"\n⚡ 跳層事件:")
                for jump in snapshot.jump_nodes[:5]:  # 最多顯示5個
                    print(f"  • {jump['source_node_id']} -> {jump['jump_node_id']}")
                    print(f"    壓力: {jump['pressure']:.2f}, 目標環: {jump['target_ring']}")
                
                if len(snapshot.jump_nodes) > 5:
                    print(f"  ... 還有 {len(snapshot.jump_nodes) - 5} 個跳層")
        
        print(f"{'='*60}\n")
    
    def export_snapshot_to_file(self, snapshot: SnapshotState, filepath: str) -> None:
        """
        導出快照到 JSON 文件
        
        Args:
            snapshot: 快照狀態
            filepath: 輸出文件路徑
        """
        data = {
            'tick': snapshot.tick,
            'node_states': snapshot.node_states,
            'jump_nodes': snapshot.jump_nodes,
            'statistics': snapshot.statistics,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 快照已導出到 {filepath}")
    
    def get_info(self) -> Dict:
        """獲取回放信息"""
        return {
            'trace_file': self.trace_file,
            'total_records': len(self.records),
            'max_tick': self.max_tick,
            'event_types': list(set(r['event_type'] for r in self.records)),
        }
    
    def __repr__(self):
        return f"ReplayPlayer(records={len(self.records)}, max_tick={self.max_tick})"
