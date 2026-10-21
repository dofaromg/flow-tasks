"""
Test performance improvements to amp/storage.py
"""
import json
import tempfile
import time
from pathlib import Path
from amp.storage import Storage


def test_tail_chain_small_file():
    """Test tail_chain with small file (should read all)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = Storage(Path(tmpdir))
        storage.ensure_structure()
        
        # Add some entries
        for i in range(10):
            storage.append_chain_entry({"id": i, "data": f"entry_{i}"})
        
        # Get last 5
        tail = storage.tail_chain(5)
        assert len(tail) == 5
        assert tail[0]["id"] == 5
        assert tail[-1]["id"] == 9
        print("✓ Small file tail_chain works correctly")


def test_tail_chain_large_file():
    """Test tail_chain with larger file (should optimize)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = Storage(Path(tmpdir))
        storage.ensure_structure()
        
        # Add many entries to create a larger file
        num_entries = 1000
        for i in range(num_entries):
            storage.append_chain_entry({
                "id": i,
                "data": f"entry_{i}_" + "x" * 100  # Make entries bigger
            })
        
        # Measure time for tail operation
        start = time.time()
        tail = storage.tail_chain(10)
        elapsed = time.time() - start
        
        assert len(tail) == 10
        assert tail[0]["id"] == 990
        assert tail[-1]["id"] == 999
        
        print(f"✓ Large file tail_chain works correctly in {elapsed*1000:.2f}ms")
        print(f"  Retrieved last 10 of {num_entries} entries")


def test_tail_chain_all_entries():
    """Test tail_chain requesting all entries (n <= 0)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = Storage(Path(tmpdir))
        storage.ensure_structure()
        
        # Add entries
        for i in range(20):
            storage.append_chain_entry({"id": i, "data": f"entry_{i}"})
        
        # Get all entries
        all_entries = storage.tail_chain(0)
        assert len(all_entries) == 20
        assert all_entries[0]["id"] == 0
        assert all_entries[-1]["id"] == 19
        print("✓ tail_chain(0) returns all entries")


def test_tail_chain_more_than_available():
    """Test tail_chain requesting more entries than available"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = Storage(Path(tmpdir))
        storage.ensure_structure()
        
        # Add only 5 entries
        for i in range(5):
            storage.append_chain_entry({"id": i, "data": f"entry_{i}"})
        
        # Request 10 entries (more than available)
        tail = storage.tail_chain(10)
        assert len(tail) == 5
        assert tail[0]["id"] == 0
        assert tail[-1]["id"] == 4
        print("✓ tail_chain handles requesting more entries than available")


def test_tail_chain_empty_file():
    """Test tail_chain with empty chain"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = Storage(Path(tmpdir))
        storage.ensure_structure()
        
        # Don't add any entries
        tail = storage.tail_chain(5)
        assert len(tail) == 0
        print("✓ tail_chain handles empty chain correctly")


if __name__ == "__main__":
    print("Running amp/storage.py performance tests...\n")
    test_tail_chain_small_file()
    test_tail_chain_large_file()
    test_tail_chain_all_entries()
    test_tail_chain_more_than_available()
    test_tail_chain_empty_file()
    print("\n✅ All amp/storage tests passed!")
