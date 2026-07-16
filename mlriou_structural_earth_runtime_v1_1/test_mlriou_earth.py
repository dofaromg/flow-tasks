#!/usr/bin/env python3
"""
測試腳本：驗證 MRLiou Structural Earth Runtime v1.1 的所有功能
"""

import os
import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """運行命令並顯示結果"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"命令: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 成功")
        if result.stdout:
            print(result.stdout)
    else:
        print("❌ 失敗")
        if result.stderr:
            print(result.stderr)
        return False
    
    return True


def verify_file_exists(filepath, description):
    """驗證文件存在"""
    if Path(filepath).exists():
        size = Path(filepath).stat().st_size
        print(f"✅ {description}: {filepath} ({size} bytes)")
        return True
    else:
        print(f"❌ {description} 文件不存在: {filepath}")
        return False


def main():
    print("\n" + "="*60)
    print("🌍 MRLiou Structural Earth Runtime v1.1 測試")
    print("="*60)
    
    base_dir = Path(__file__).parent
    os.chdir(base_dir)
    
    all_passed = True
    
    # 測試 1: 驗證安裝
    print("\n📦 測試 1: 驗證安裝")
    if not run_command(["mlriou-earth", "--help"], "檢查 CLI 安裝"):
        all_passed = False
    
    # 測試 2: 運轉測試（小規模）
    print("\n🚀 測試 2: 運轉測試")
    test_outdir = base_dir / "test_out"
    if test_outdir.exists():
        import shutil
        shutil.rmtree(test_outdir)
    
    if not run_command([
        "mlriou-earth", "run",
        "--input", str(base_dir / "examples" / "sample_nodes.json"),
        "--outdir", str(test_outdir),
        "--alpha", "2.0",
        "--threshold", "20",
        "--max-ticks", "10"
    ], "執行運轉（10 ticks）"):
        all_passed = False
    else:
        # 驗證輸出文件
        print("\n📁 驗證輸出文件:")
        all_passed &= verify_file_exists(test_outdir / "trace.jsonl", "軌跡文件")
        all_passed &= verify_file_exists(test_outdir / "final_structure.json", "最終結構")
        all_passed &= verify_file_exists(test_outdir / "jump_statistics.json", "跳層統計")
        all_passed &= verify_file_exists(test_outdir / "trace_statistics.json", "軌跡統計")
    
    # 測試 3: 回放測試
    if (test_outdir / "trace.jsonl").exists():
        print("\n📹 測試 3: 回放測試")
        
        # 前進回放
        if not run_command([
            "mlriou-earth", "replay",
            "--trace", str(test_outdir / "trace.jsonl"),
            "--tick", "5"
        ], "前進回放到 tick 5"):
            all_passed = False
        
        # 後退回放（從較大的 tick）
        if not run_command([
            "mlriou-earth", "replay",
            "--trace", str(test_outdir / "trace.jsonl"),
            "--tick", "3"
        ], "後退回放到 tick 3"):
            all_passed = False
        
        # 導出快照
        snapshot_file = test_outdir / "test_snapshot.json"
        if not run_command([
            "mlriou-earth", "replay",
            "--trace", str(test_outdir / "trace.jsonl"),
            "--tick", "5",
            "--output", str(snapshot_file)
        ], "導出快照到文件"):
            all_passed = False
        else:
            all_passed &= verify_file_exists(snapshot_file, "快照文件")
    
    # 測試 4: 驗證數據格式
    print("\n📊 測試 4: 驗證數據格式")
    
    # 驗證 trace.jsonl 格式
    trace_file = test_outdir / "trace.jsonl"
    if trace_file.exists():
        try:
            with open(trace_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                record_count = 0
                for line in lines[:5]:  # 檢查前5條
                    data = json.loads(line)
                    assert 'tick' in data
                    assert 'event_type' in data
                    assert 'node_id' in data
                    assert 'data' in data
                    record_count += 1
                
                print(f"✅ trace.jsonl 格式正確（檢查 {record_count} 條記錄）")
        except Exception as e:
            print(f"❌ trace.jsonl 格式錯誤: {e}")
            all_passed = False
    
    # 驗證統計文件格式
    stats_file = test_outdir / "jump_statistics.json"
    if stats_file.exists():
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert 'total_jumps' in data
                assert 'threshold' in data
                print(f"✅ jump_statistics.json 格式正確（跳層數: {data['total_jumps']}）")
        except Exception as e:
            print(f"❌ jump_statistics.json 格式錯誤: {e}")
            all_passed = False
    
    # 最終結果
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有測試通過！")
        print("="*60)
        return 0
    else:
        print("❌ 部分測試失敗")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
