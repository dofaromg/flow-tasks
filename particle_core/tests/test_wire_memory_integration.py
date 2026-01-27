#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wire-Memory Integration Tests
線協-記憶整合測試

Tests the complete integration between:
- PD_AI wire protocol (C)
- Memory Quick Mount (Python)
- Particle Wire Bridge
"""

import sys
import json
import tempfile
from pathlib import Path

# Add memory module to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'memory'))

from particle_wire_bridge import ParticleWireBridge, WireHeader, sizeof
from memory_quick_mount import MemoryQuickMounter, AdvancedParticleCompressor


def test_round_trip():
    """測試 Python → Wire → Python 完整循環"""
    print("\n" + "=" * 60)
    print("Test 1: Round-trip Conversion")
    print("=" * 60)
    
    original = {
        "主體": "Agent-01",
        "任務": "資料處理",
        "狀態": "執行中",
        "數據": {
            "輸入": 100,
            "輸出": 95,
            "成功率": 0.95
        }
    }
    
    print("\nOriginal data:")
    print(json.dumps(original, ensure_ascii=False, indent=2))
    
    # Create bridge with compression
    bridge = ParticleWireBridge(use_compression=True)
    
    # Python → Wire
    print("\n→ Converting to wire format...")
    wire_data = bridge.python_to_wire(original)
    assert len(wire_data) > sizeof(WireHeader), "Wire data should contain header + payload"
    print(f"  ✓ Wire data size: {len(wire_data)} bytes")
    print(f"    - Header: {sizeof(WireHeader)} bytes")
    print(f"    - Payload: {len(wire_data) - sizeof(WireHeader)} bytes")
    
    # Wire → Python
    print("\n→ Converting back to Python...")
    restored, header = bridge.wire_to_python(wire_data)
    print(f"  ✓ Header: mt=0x{header.mt:02x}, kc=0x{header.kc:02x}, "
          f"ann=0x{header.ann:02x}, rid={header.rid}")
    print(f"\nRestored data:")
    print(json.dumps(restored, ensure_ascii=False, indent=2))
    
    # Verify
    assert restored["主體"] == "Agent-01", "主體 field mismatch"
    assert restored["任務"] == "資料處理", "任務 field mismatch"
    assert restored["狀態"] == "執行中", "狀態 field mismatch"
    
    print("\n✓✓✓ Round-trip test PASSED ✓✓✓")
    return True


def test_compression():
    """測試粒子壓縮功能"""
    print("\n" + "=" * 60)
    print("Test 2: Particle Compression")
    print("=" * 60)
    
    compressor = AdvancedParticleCompressor()
    
    test_data = {
        "agent": "test_agent",
        "status": "active",
        "metrics": {
            "cpu": 45,
            "memory": 2048,
            "tasks": 12
        },
        "history": [
            {"time": "10:00", "event": "start"},
            {"time": "10:30", "event": "process"},
            {"time": "11:00", "event": "complete"}
        ]
    }
    
    print("\nOriginal data:")
    print(json.dumps(test_data, ensure_ascii=False, indent=2))
    
    # Compress
    print("\n→ Compressing...")
    compressed = compressor.compress(test_data)
    stats = compressor.get_stats()
    
    print(f"  ✓ Original size: {stats['original_size']} bytes")
    print(f"  ✓ Compressed size: {stats['compressed_size']} bytes")
    print(f"  ✓ Compression ratio: {stats['ratio']:.2%}")
    
    # Decompress
    print("\n→ Decompressing...")
    decompressed = compressor.decompress(compressed)
    
    print(f"\nDecompressed data:")
    print(json.dumps(decompressed, ensure_ascii=False, indent=2))
    
    # Verify
    assert decompressed["agent"] == test_data["agent"], "Agent field mismatch"
    assert decompressed["status"] == test_data["status"], "Status field mismatch"
    
    print("\n✓✓✓ Compression test PASSED ✓✓✓")
    return True


def test_memory_mount_with_wire():
    """測試記憶掛載與 wire 格式整合"""
    print("\n" + "=" * 60)
    print("Test 3: Memory Mount with Wire Integration")
    print("=" * 60)
    
    # Create temporary config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "context_dir": "/tmp/test_context",
            "snapshot_dir": "/tmp/test_snapshots",
            "seeds": []
        }
        json.dump(config, f)
        config_path = f.name
    
    print(f"\nUsing temporary config: {config_path}")
    
    # Initialize mounter
    mqm = MemoryQuickMounter(config_path)
    bridge = ParticleWireBridge(use_compression=True)
    
    # Create test state
    state = {
        "agent": "integration_test",
        "step": 1,
        "context": {
            "scene": "roomA",
            "objects": ["table", "chair", "lamp"],
            "temperature": 22.5
        }
    }
    
    print("\nTest state:")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    
    # Create snapshot
    print("\n→ Creating snapshot...")
    snapshot_path = mqm.snapshot("integration_test", state)
    assert Path(snapshot_path).exists(), "Snapshot file should exist"
    print(f"  ✓ Snapshot saved: {snapshot_path}")
    
    # Convert to wire format
    print("\n→ Converting snapshot to wire format...")
    wire_data = bridge.python_to_wire(state)
    print(f"  ✓ Wire format size: {len(wire_data)} bytes")
    print(f"    - Header: {sizeof(WireHeader)} bytes")
    print(f"    - Payload: {len(wire_data) - sizeof(WireHeader)} bytes")
    
    # Restore from snapshot
    print("\n→ Rehydrating from snapshot...")
    restored = mqm.rehydrate(snapshot_path)
    print(f"\nRestored state:")
    print(json.dumps(restored, ensure_ascii=False, indent=2))
    
    # Verify
    assert restored["agent"] == state["agent"], "Agent mismatch in restored state"
    assert restored["step"] == state["step"], "Step mismatch in restored state"
    
    # Clean up
    Path(config_path).unlink()
    
    print("\n✓✓✓ Memory mount integration test PASSED ✓✓✓")
    return True


def test_snapshot_message():
    """測試快照訊息建立"""
    print("\n" + "=" * 60)
    print("Test 4: Snapshot Message Creation")
    print("=" * 60)
    
    bridge = ParticleWireBridge(use_compression=True)
    
    state = {
        "agent": "snapshot_test",
        "data": {
            "value1": 42,
            "value2": "test"
        }
    }
    
    print("\nState to snapshot:")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    
    # Create snapshot message
    print("\n→ Creating snapshot message...")
    snapshot_msg = bridge.create_snapshot_message("snapshot_test", state)
    
    print(f"  ✓ Snapshot message size: {len(snapshot_msg)} bytes")
    
    # Parse message back
    print("\n→ Parsing snapshot message...")
    restored, header = bridge.wire_to_python(snapshot_msg)
    
    print(f"  ✓ Message type: 0x{header.mt:02x} (should be 0x05 for M_SNAPSHOT)")
    print(f"  ✓ Key class: 0x{header.kc:02x}")
    print(f"  ✓ Record ID: 0x{header.rid:08x}")
    
    assert header.mt == 0x05, "Message type should be M_SNAPSHOT"
    assert "state" in restored, "Restored message should contain state"
    
    print("\n✓✓✓ Snapshot message test PASSED ✓✓✓")
    return True


def test_query_message():
    """測試查詢訊息建立"""
    print("\n" + "=" * 60)
    print("Test 5: Query Message Creation")
    print("=" * 60)
    
    bridge = ParticleWireBridge(use_compression=False)
    
    query_params = {
        "agent": "test_agent",
        "filters": {
            "status": "active",
            "priority": "high"
        }
    }
    
    print("\nQuery parameters:")
    print(json.dumps(query_params, ensure_ascii=False, indent=2))
    
    # Create query message
    print("\n→ Creating query message...")
    query_msg = bridge.create_query_message(query_params, record_id=0x00100001)
    
    print(f"  ✓ Query message size: {len(query_msg)} bytes")
    
    # Parse message back
    print("\n→ Parsing query message...")
    restored, header = bridge.wire_to_python(query_msg)
    
    print(f"  ✓ Message type: 0x{header.mt:02x} (should be 0x03 for M_QUERY)")
    print(f"  ✓ Annotation: 0x{header.ann:02x} (should be 0x01 for read-only)")
    print(f"  ✓ Record ID: 0x{header.rid:08x}")
    
    assert header.mt == 0x03, "Message type should be M_QUERY"
    assert header.ann == 0x01, "Annotation should be read-only"
    
    print("\n✓✓✓ Query message test PASSED ✓✓✓")
    return True


def run_all_tests():
    """Run all integration tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Wire-Memory Integration Test Suite" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    
    tests = [
        ("Round-trip Conversion", test_round_trip),
        ("Particle Compression", test_compression),
        ("Memory Mount Integration", test_memory_mount_with_wire),
        ("Snapshot Message", test_snapshot_message),
        ("Query Message", test_query_message)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n✗ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} FAILED with exception:")
            print(f"  {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n")
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓✓✓ ALL INTEGRATION TESTS PASSED ✓✓✓")
        return 0
    else:
        print(f"\n✗✗✗ {failed} TEST(S) FAILED ✗✗✗")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
