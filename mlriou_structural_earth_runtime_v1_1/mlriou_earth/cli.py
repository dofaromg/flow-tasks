"""
cli.py - MRLiou Earth Runtime CLI
命令列介面：mlriou-earth run / replay

支持的命令：
  mlriou-earth run --input <file> --outdir <dir> [options]
  mlriou-earth replay --trace <file> --tick <n> [options]
"""

import argparse
import json
import os
import sys
from pathlib import Path

from .core.structure import EarthStructure, StructureNode
from .core.projection import PressureProjection
from .core.jump import JumpManager
from .core.trace import TraceRecorder
from .replay.player import ReplayPlayer


def cmd_run(args):
    """執行運轉命令"""
    print("🌍 MRLiou Structural Earth Runtime v1.1")
    print("=" * 60)
    
    # 讀取輸入節點數據
    print(f"\n📂 讀取輸入文件: {args.input}")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    except Exception as e:
        print(f"❌ 錯誤: 無法讀取輸入文件 - {e}")
        return 1
    
    # 創建輸出目錄
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"📁 輸出目錄: {outdir}")
    
    # 初始化結構
    print("\n🏗️  初始化結構...")
    structure = EarthStructure()
    
    # 加載節點
    nodes_data = input_data.get('nodes', [])
    print(f"  • 加載 {len(nodes_data)} 個節點")
    for node_data in nodes_data:
        node = StructureNode.from_dict(node_data)
        structure.add_node(node)
    
    # 加載邊
    edges_data = input_data.get('edges', [])
    print(f"  • 加載 {len(edges_data)} 條邊")
    for src, dst in edges_data:
        structure.add_edge(src, dst)
    
    # 應用結構變換
    if args.ring_lift != 0:
        print(f"  • 應用 ring lift: {args.ring_lift}")
        structure.apply_ring_lift(args.ring_lift)
    
    if args.sector_shift != 0:
        print(f"  • 應用 sector shift: {args.sector_shift}")
        structure.apply_sector_shift(args.sector_shift)
    
    # 初始化壓力投影
    print(f"\n⚡ 初始化壓力場 (alpha={args.alpha}, threshold={args.threshold})...")
    projection = PressureProjection(alpha_global=args.alpha)
    jump_manager = JumpManager(pressure_threshold=args.threshold)
    
    # 初始化軌跡記錄
    trace_file = outdir / "trace.jsonl"
    trace_recorder = TraceRecorder(str(trace_file))
    print(f"  • 軌跡記錄: {trace_file}")
    
    # 運轉模擬
    print(f"\n🚀 開始運轉 (最大 {args.max_ticks} 步)...")
    for tick in range(args.max_ticks):
        projection.advance_tick()
        
        # 對每個節點執行壓力投影（創建快照避免運行時修改）
        nodes_snapshot = list(structure.nodes.values())
        for node in nodes_snapshot:
            # 獲取前一步壓力
            prev_pressure = projection.get_pressure(node.node_id) or 1.0
            
            # 執行投影
            state = projection.project(
                node.node_id,
                node.N,
                node.eta,
                node.alpha,
                node.beta,
                prev_pressure
            )
            
            # 記錄投影
            trace_recorder.record_projection(
                tick=tick,
                node_id=node.node_id,
                pressure_before=prev_pressure,
                pressure_after=state.pressure,
                energy=state.energy,
                metadata=state.metadata
            )
            
            # 檢查是否需要跳層
            jump_node = jump_manager.check_and_create_jump(
                node, state.pressure, tick
            )
            
            if jump_node:
                # 記錄跳層
                trace_recorder.record_jump(
                    tick=tick,
                    source_node_id=node.node_id,
                    jump_node_id=jump_node.jump_id,
                    pressure=state.pressure,
                    target_ring=jump_node.target_ring,
                    metadata=jump_node.metadata
                )
                
                # 創建合成節點並加入結構
                synthetic_node = jump_manager.create_synthetic_node(jump_node, node)
                structure.add_node(synthetic_node)
                structure.add_edge(node.node_id, synthetic_node.node_id)
        
        # 每10步輸出進度
        if (tick + 1) % 10 == 0 or tick == args.max_ticks - 1:
            total_energy = projection.get_total_energy()
            print(f"  Tick {tick:3d}: 節點={len(structure.nodes):3d}, "
                  f"跳層={len(jump_manager.jump_nodes):3d}, "
                  f"能量={total_energy:8.2f}")
    
    # 關閉軌跡記錄
    trace_recorder.close_file()
    
    # 保存最終結構
    structure_file = outdir / "final_structure.json"
    structure.save_to_file(str(structure_file))
    print(f"\n💾 結構已保存: {structure_file}")
    
    # 保存跳層統計
    jump_stats_file = outdir / "jump_statistics.json"
    with open(jump_stats_file, 'w', encoding='utf-8') as f:
        json.dump(jump_manager.get_statistics(), f, ensure_ascii=False, indent=2)
    print(f"💾 跳層統計已保存: {jump_stats_file}")
    
    # 保存軌跡統計
    trace_stats_file = outdir / "trace_statistics.json"
    with open(trace_stats_file, 'w', encoding='utf-8') as f:
        json.dump(trace_recorder.get_statistics(), f, ensure_ascii=False, indent=2)
    print(f"💾 軌跡統計已保存: {trace_stats_file}")
    
    print("\n✅ 運轉完成!")
    print("=" * 60)
    
    return 0


def cmd_replay(args):
    """執行回放命令"""
    print("📹 MRLiou Earth Replay v1.1")
    print("=" * 60)
    
    # 檢查軌跡文件
    if not os.path.exists(args.trace):
        print(f"❌ 錯誤: 軌跡文件不存在 - {args.trace}")
        return 1
    
    # 初始化回放器
    print(f"\n📂 加載軌跡文件: {args.trace}")
    try:
        player = ReplayPlayer(args.trace)
    except Exception as e:
        print(f"❌ 錯誤: 無法加載軌跡文件 - {e}")
        return 1
    
    # 顯示回放信息
    info = player.get_info()
    print(f"\n📊 回放信息:")
    print(f"  • 總記錄數: {info['total_records']}")
    print(f"  • 時間範圍: 0 - {info['max_tick']}")
    print(f"  • 事件類型: {', '.join(info['event_types'])}")
    
    # 獲取快照
    tick = args.tick
    if tick > info['max_tick']:
        print(f"\n⚠️  警告: 請求的 tick ({tick}) 超過最大值 ({info['max_tick']})")
        tick = info['max_tick']
    
    print(f"\n🎬 回放到 tick {tick}...")
    snapshot = player.get_snapshot_at_tick(tick)
    
    # 顯示快照
    player.print_snapshot(snapshot, verbose=args.verbose)
    
    # 導出快照（如果指定）
    if args.output:
        player.export_snapshot_to_file(snapshot, args.output)
    
    print("\n✅ 回放完成!")
    print("=" * 60)
    
    return 0


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="MRLiou Structural Earth Runtime v1.1 - 中心不變的骨架定義與壓力場映射"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # run 命令
    run_parser = subparsers.add_parser('run', help='執行運轉')
    run_parser.add_argument('--input', required=True, help='輸入節點數據文件 (JSON)')
    run_parser.add_argument('--outdir', required=True, help='輸出目錄')
    run_parser.add_argument('--alpha', type=float, default=2.0, help='全局放大係數 (默認: 2.0)')
    run_parser.add_argument('--threshold', type=float, default=20.0, help='跳層壓力閾值 (默認: 20.0)')
    run_parser.add_argument('--ring-lift', type=int, default=0, help='環層提升 (默認: 0)')
    run_parser.add_argument('--sector-shift', type=int, default=0, help='扇區旋轉 (默認: 0)')
    run_parser.add_argument('--max-ticks', type=int, default=100, help='最大時間步 (默認: 100)')
    
    # replay 命令
    replay_parser = subparsers.add_parser('replay', help='回放軌跡')
    replay_parser.add_argument('--trace', required=True, help='軌跡文件 (trace.jsonl)')
    replay_parser.add_argument('--tick', type=int, required=True, help='回放到指定時間步')
    replay_parser.add_argument('--output', help='導出快照到 JSON 文件')
    replay_parser.add_argument('--verbose', action='store_true', help='顯示詳細信息')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 執行命令
    if args.command == 'run':
        return cmd_run(args)
    elif args.command == 'replay':
        return cmd_replay(args)
    else:
        print(f"❌ 未知命令: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
