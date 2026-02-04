#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Cold Storage Manager
冷儲存管理器測試套件
"""

import sys
import json
import tempfile
import hashlib
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cold_storage_manager import ColdStorageManager


def test_file_pattern_matching():
    """Test file pattern matching logic"""
    print("\n" + "=" * 60)
    print("Test 1: File Pattern Matching")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        
        # Create test files with various patterns
        (test_dir / "下載 test.txt").write_text("test content")
        (test_dir / "點此下載 file.txt").write_text("test content")
        (test_dir / "temp_file.txt").write_text("test content")
        (test_dir / "file.tmp").write_text("test content")
        (test_dir / "normal_file.txt").write_text("test content")
        (test_dir / ".gitignore").write_text("test content")
        
        manager = ColdStorageManager(source_root=str(test_dir))
        files = manager.scan_files()
        
        # Should match: 下載, 點此下載, temp_, .tmp
        # Should NOT match: normal_file.txt, .gitignore
        filenames = [Path(f).name for f in files]
        
        assert "下載 test.txt" in filenames, "Should match 下載 pattern"
        assert "點此下載 file.txt" in filenames, "Should match 點此下載 pattern"
        assert "temp_file.txt" in filenames, "Should match temp_ pattern"
        assert "file.tmp" in filenames, "Should match .tmp pattern"
        assert "normal_file.txt" not in filenames, "Should not match normal files"
        assert ".gitignore" not in filenames, "Should not match .gitignore"
        
        print(f"  ✓ Matched {len(files)} files correctly")
        print(f"  ✓ File patterns working as expected")
        

def test_checksum_calculation():
    """Test SHA-256 checksum calculation"""
    print("\n" + "=" * 60)
    print("Test 2: Checksum Calculation")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        test_file = test_dir / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        manager = ColdStorageManager(source_root=str(test_dir))
        checksum = manager._calculate_checksum(str(test_file))
        
        # Verify checksum is correct
        expected = hashlib.sha256(content.encode('utf-8')).hexdigest()
        assert checksum == expected, f"Checksum mismatch: {checksum} != {expected}"
        
        print(f"  ✓ Checksum calculated correctly: {checksum[:16]}...")
        

def test_text_file_particlization():
    """Test text file conversion to particle format"""
    print("\n" + "=" * 60)
    print("Test 3: Text File Particlization")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        test_file = test_dir / "下載 test.txt"
        content = "This is a test file for particlization"
        test_file.write_text(content)
        
        manager = ColdStorageManager(
            source_root=str(test_dir),
            cold_storage_root=str(test_dir / "cold_storage"),
            manifest_file=str(test_dir / "cold_storage" / "manifest.json")
        )
        
        # Archive the file
        result = manager.archive_file(str(test_file), keep_original=True)
        
        assert result["status"] == "success", f"Archive failed: {result.get('error')}"
        assert result["action"] in ["archived", "deduplicated"], "Should be archived or deduplicated"
        
        # Verify particle file was created
        checksum = result["checksum"]
        particle_file = test_dir / "cold_storage" / "particles" / f"{checksum[:16]}.particle.json"
        assert particle_file.exists(), "Particle file should be created"
        
        # Verify particle structure
        particle_data = json.loads(particle_file.read_text())
        assert "memory_layers" in particle_data, "Should have memory_layers"
        assert len(particle_data["memory_layers"]) == 5, "Should have 5 memory layers"
        expected_layers = ["structure", "mark", "flow", "recurse", "store"]
        assert particle_data["memory_layers"] == expected_layers, f"Layers should be {expected_layers}"
        assert particle_data["content"] == content, "Content should be preserved"
        
        # Verify original file still exists
        assert test_file.exists(), "Original file should be preserved"
        
        print(f"  ✓ Text file converted to particle format")
        print(f"  ✓ All 5 memory layers present")
        print(f"  ✓ Original file preserved")


def test_binary_file_handling():
    """Test binary file handling"""
    print("\n" + "=" * 60)
    print("Test 4: Binary File Handling")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        test_file = test_dir / "下載 image.bin"
        binary_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        test_file.write_bytes(binary_content)
        
        manager = ColdStorageManager(
            source_root=str(test_dir),
            cold_storage_root=str(test_dir / "cold_storage"),
            manifest_file=str(test_dir / "cold_storage" / "manifest.json")
        )
        
        result = manager.archive_file(str(test_file), keep_original=True)
        
        assert result["status"] == "success", "Binary file archive should succeed"
        
        # Verify binary file was copied
        checksum = result["checksum"]
        binary_copy = test_dir / "cold_storage" / "particles" / f"{checksum[:16]}.bin"
        assert binary_copy.exists(), "Binary file copy should exist"
        assert binary_copy.read_bytes() == binary_content, "Binary content should match"
        
        print(f"  ✓ Binary file handled correctly")
        print(f"  ✓ Binary content preserved")


def test_deduplication():
    """Test file deduplication logic"""
    print("\n" + "=" * 60)
    print("Test 5: Deduplication")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        
        # Create two files with identical content
        content = "Identical content for deduplication test"
        file1 = test_dir / "下載 file1.txt"
        file2 = test_dir / "下載 file2.txt"
        file1.write_text(content)
        file2.write_text(content)
        
        manager = ColdStorageManager(
            source_root=str(test_dir),
            cold_storage_root=str(test_dir / "cold_storage"),
            manifest_file=str(test_dir / "cold_storage" / "manifest.json")
        )
        
        # Archive first file
        result1 = manager.archive_file(str(file1), keep_original=True)
        assert result1["action"] == "archived", "First file should be archived"
        
        # Archive second file (should be deduplicated)
        result2 = manager.archive_file(str(file2), keep_original=True)
        assert result2["action"] == "deduplicated", "Second file should be deduplicated"
        assert result2["checksum"] == result1["checksum"], "Checksums should match"
        
        # Verify both files are tracked in manifest
        checksum = result1["checksum"]
        assert checksum in manager.manifest["checksums"], "Checksum should be in manifest"
        occurrences = manager.manifest["checksums"][checksum]["occurrences"]
        assert len(occurrences) == 2, "Should track both file occurrences"
        
        print(f"  ✓ Deduplication working correctly")
        print(f"  ✓ Both file paths tracked in manifest")


def test_batch_archival():
    """Test batch archival operations"""
    print("\n" + "=" * 60)
    print("Test 6: Batch Archival")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        
        # Create multiple test files
        for i in range(5):
            (test_dir / f"下載 file{i}.txt").write_text(f"Content {i}")
        
        manager = ColdStorageManager(
            source_root=str(test_dir),
            cold_storage_root=str(test_dir / "cold_storage"),
            manifest_file=str(test_dir / "cold_storage" / "manifest.json")
        )
        
        files = manager.scan_files()
        assert len(files) == 5, f"Should find 5 files, found {len(files)}"
        
        results = manager.archive_batch(files, keep_original=True)
        
        assert len(results["archived"]) == 5, "All files should be archived"
        assert len(results["errors"]) == 0, "Should have no errors"
        
        print(f"  ✓ Batch archived {len(results['archived'])} files")
        print(f"  ✓ No errors encountered")


def test_manifest_persistence():
    """Test manifest saving and loading"""
    print("\n" + "=" * 60)
    print("Test 7: Manifest Persistence")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        test_file = test_dir / "下載 test.txt"
        test_file.write_text("Test content")
        
        # Create manager and archive file
        manager1 = ColdStorageManager(
            source_root=str(test_dir),
            cold_storage_root=str(test_dir / "cold_storage"),
            manifest_file=str(test_dir / "cold_storage" / "manifest.json")
        )
        result = manager1.archive_file(str(test_file), keep_original=True)
        checksum = result["checksum"]
        
        # Create new manager instance (should load existing manifest)
        manager2 = ColdStorageManager(
            source_root=str(test_dir),
            cold_storage_root=str(test_dir / "cold_storage"),
            manifest_file=str(test_dir / "cold_storage" / "manifest.json")
        )
        
        # Verify manifest was loaded
        assert checksum in manager2.manifest["checksums"], "Manifest should be loaded"
        assert len(manager2.manifest["checksums"]) == 1, "Should have 1 checksum"
        
        print(f"  ✓ Manifest persisted correctly")
        print(f"  ✓ Manifest loaded on initialization")


def test_statistics():
    """Test statistics calculation"""
    print("\n" + "=" * 60)
    print("Test 8: Statistics")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        
        # Create files with some duplicates
        (test_dir / "下載 file1.txt").write_text("content1")
        (test_dir / "下載 file2.txt").write_text("content1")  # Duplicate
        (test_dir / "下載 file3.txt").write_text("content2")
        
        manager = ColdStorageManager(
            source_root=str(test_dir),
            cold_storage_root=str(test_dir / "cold_storage"),
            manifest_file=str(test_dir / "cold_storage" / "manifest.json")
        )
        
        files = manager.scan_files()
        manager.archive_batch(files, keep_original=True)
        
        stats = manager.get_statistics()
        
        # Total files = unique archived files (not counting duplicates in statistics)
        assert stats["total_files"] == 2, f"Should have 2 unique files, got {stats['total_files']}"
        assert stats["unique_files"] == 2, f"Should have 2 unique checksums, got {stats['unique_files']}"
        # total_archived counts all entries in manifest (including duplicates tracked in occurrences)
        assert stats["total_archived"] >= 2, "Should have at least 2 archived"
        
        print(f"  ✓ Total unique files: {stats['total_files']}")
        print(f"  ✓ Unique checksums: {stats['unique_files']}")
        print(f"  ✓ Total archived entries: {stats['total_archived']}")


def test_error_handling():
    """Test error handling for invalid files"""
    print("\n" + "=" * 60)
    print("Test 9: Error Handling")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        
        manager = ColdStorageManager(
            source_root=str(test_dir),
            cold_storage_root=str(test_dir / "cold_storage"),
            manifest_file=str(test_dir / "cold_storage" / "manifest.json")
        )
        
        # Try to archive non-existent file
        result = manager.archive_file(str(test_dir / "nonexistent.txt"), keep_original=True)
        
        assert result["status"] == "error", "Should return error status"
        assert "error" in result, "Should have error message"
        
        print(f"  ✓ Non-existent file handled gracefully")
        print(f"  ✓ Error message: {result['error'][:50]}...")


def test_redirect_file_creation():
    """Test redirect file creation"""
    print("\n" + "=" * 60)
    print("Test 10: Redirect File Creation")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        test_file = test_dir / "下載 test.txt"
        test_file.write_text("Test content for redirect")
        
        manager = ColdStorageManager(
            source_root=str(test_dir),
            cold_storage_root=str(test_dir / "cold_storage"),
            manifest_file=str(test_dir / "cold_storage" / "manifest.json")
        )
        
        result = manager.archive_file(str(test_file), keep_original=True)
        checksum = result["checksum"]
        
        # Check if redirect file was created
        redirect_file = test_dir / "cold_storage" / "redirects" / f"{checksum[:16]}.redirect.txt"
        assert redirect_file.exists(), "Redirect file should be created"
        
        # Verify redirect content
        redirect_content = redirect_file.read_text()
        assert "原始路徑" in redirect_content, "Should have original path info"
        assert "粒子 ID" in redirect_content, "Should have particle ID"
        
        print(f"  ✓ Redirect file created")
        print(f"  ✓ Redirect content correct")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 70)
    print("Cold Storage Manager Test Suite")
    print("冷儲存管理器測試套件")
    print("=" * 70)
    
    tests = [
        test_file_pattern_matching,
        test_checksum_calculation,
        test_text_file_particlization,
        test_binary_file_handling,
        test_deduplication,
        test_batch_archival,
        test_manifest_persistence,
        test_statistics,
        test_error_handling,
        test_redirect_file_creation,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_func.__name__} PASSED")
        except AssertionError as e:
            failed += 1
            print(f"❌ {test_func.__name__} FAILED: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} ERROR: {e}")
    
    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
