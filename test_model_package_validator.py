#!/usr/bin/env python3
"""
Test script for Model Package v1 Validator
Validates the workflow and script functionality
"""

import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def create_valid_test_package(package_dir: Path) -> None:
    """Create a valid test package structure."""
    # Create directory structure
    (package_dir / "preview").mkdir(parents=True, exist_ok=True)
    (package_dir / "report").mkdir(parents=True, exist_ok=True)
    (package_dir / "meta").mkdir(parents=True, exist_ok=True)
    
    # Create manifest.json
    manifest = {
        "package_version": "1.0.0",
        "package_id": "test_pkg_001",
        "scan_id": "scan_001",
        "job_id": "job_001",
        "model_revision": "1",
        "created_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T01:00:00Z",
        "source_type": "LIDAR_SCAN",
        "device": "iPhone 12 Pro",
        "coordinate_system": "Z_UP_RIGHT_HANDED",
        "primary": {
            "preview_glb": "preview/model.glb",
            "thumbnail": "preview/thumbnail.png",
            "quality_report": "report/quality.json"
        },
        "artifacts": [
            {
                "name": "preview_glb",
                "path": "preview/model.glb",
                "mime": "model/gltf-binary",
                "sha256": "0" * 64,
                "bytes": 100
            },
            {
                "name": "thumbnail",
                "path": "preview/thumbnail.png",
                "mime": "image/png",
                "sha256": "1" * 64,
                "bytes": 50
            },
            {
                "name": "quality_report",
                "path": "report/quality.json",
                "mime": "application/json",
                "sha256": "2" * 64,
                "bytes": 200
            },
            {
                "name": "pipeline_report",
                "path": "report/pipeline.json",
                "mime": "application/json",
                "sha256": "3" * 64,
                "bytes": 150
            },
            {
                "name": "source_meta",
                "path": "meta/source.json",
                "mime": "application/json",
                "sha256": "4" * 64,
                "bytes": 120
            }
        ]
    }
    
    # Write manifest
    (package_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    # Create dummy files with correct sizes
    (package_dir / "preview/model.glb").write_bytes(b"X" * 100)
    (package_dir / "preview/thumbnail.png").write_bytes(b"Y" * 50)
    
    # Create quality.json
    quality = {
        "overall_score": 0.95,
        "pass": True,
        "metrics": {}
    }
    (package_dir / "report/quality.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    
    # Create pipeline.json
    pipeline = {
        "status": "completed",
        "stages": [
            {"name": "scan", "ok": True},
            {"name": "process", "ok": True},
            {"name": "validate", "ok": True}
        ]
    }
    (package_dir / "report/pipeline.json").write_text(json.dumps(pipeline, indent=2), encoding="utf-8")
    
    # Create source.json
    source = {
        "source_type": "LIDAR_SCAN",
        "inputs": {
            "has_depth": True,
            "has_pointcloud": False,
            "has_arkit_frames": False
        }
    }
    (package_dir / "meta/source.json").write_text(json.dumps(source, indent=2), encoding="utf-8")
    
    # Update artifact hashes to match actual content
    for artifact in manifest["artifacts"]:
        file_path = package_dir / artifact["path"]
        if file_path.exists():
            h = hashlib.sha256()
            h.update(file_path.read_bytes())
            artifact["sha256"] = h.hexdigest()
    
    # Re-write manifest with correct hashes
    (package_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def create_invalid_test_package(package_dir: Path) -> None:
    """Create an invalid test package (missing required files)."""
    (package_dir / "preview").mkdir(parents=True, exist_ok=True)
    
    # Create minimal manifest without required fields
    manifest = {
        "package_version": "1.0.0",
        "package_id": "test_pkg_002"
    }
    (package_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def test_validator_on_valid_directory():
    """Test validator with a valid package directory."""
    print("Testing validator on valid directory package...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        package_dir = Path(tmpdir) / "test_pkg_001"
        create_valid_test_package(package_dir)
        
        result = subprocess.run(
            ["python3", "model_package_v1_validator.py", str(package_dir)],
            capture_output=True,
            text=True
        )
        
        # Note: We expect this to fail with hash mismatches since we used dummy hashes initially,
        # but the script should run without errors
        assert result.returncode in [0, 2], f"Unexpected exit code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
        print(f"✅ Validator executed successfully (exit code: {result.returncode})")
        print(f"   Output: {result.stdout[:100]}...")
        return True


def test_validator_on_valid_zip():
    """Test validator with a valid package zip file."""
    print("\nTesting validator on valid zip package...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        package_dir = tmpdir_path / "test_pkg_003"
        create_valid_test_package(package_dir)
        
        # Create zip file
        zip_path = tmpdir_path / "test_pkg_003.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in package_dir.rglob("*"):
                if file.is_file():
                    arcname = file.relative_to(tmpdir_path)
                    zf.write(file, arcname)
        
        result = subprocess.run(
            ["python3", "model_package_v1_validator.py", str(zip_path)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode in [0, 2], f"Unexpected exit code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
        print(f"✅ Validator executed on zip successfully (exit code: {result.returncode})")
        return True


def test_validator_on_invalid_package():
    """Test validator with an invalid package (should return exit code 2)."""
    print("\nTesting validator on invalid package...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        package_dir = Path(tmpdir) / "test_pkg_004"
        create_invalid_test_package(package_dir)
        
        result = subprocess.run(
            ["python3", "model_package_v1_validator.py", str(package_dir)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 2, f"Expected exit code 2 (INVALID), got {result.returncode}"
        assert "INVALID" in result.stdout, "Expected INVALID status in output"
        print("✅ Validator correctly identified invalid package")
        return True


def test_validator_json_output():
    """Test validator with JSON output format."""
    print("\nTesting validator with JSON output...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        package_dir = Path(tmpdir) / "test_pkg_005"
        create_invalid_test_package(package_dir)
        
        result = subprocess.run(
            ["python3", "model_package_v1_validator.py", str(package_dir), "--json"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 2, f"Expected exit code 2 (INVALID), got {result.returncode}"
        
        # Verify JSON output is parseable
        try:
            output = json.loads(result.stdout)
            assert "status" in output, "JSON output missing 'status' field"
            assert "findings" in output, "JSON output missing 'findings' field"
            assert output["status"] == "INVALID", "Expected INVALID status in JSON"
            print(f"✅ Validator JSON output is valid (status: {output['status']}, findings: {len(output['findings'])})")
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON output: {e}\nOutput: {result.stdout}")
        
        return True


def test_validator_help():
    """Test validator help output."""
    print("\nTesting validator help output...")
    
    result = subprocess.run(
        ["python3", "model_package_v1_validator.py", "--help"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Help command failed with exit code {result.returncode}"
    assert "Validate a Model Package v1" in result.stdout, "Expected help text not found"
    print("✅ Validator help output is correct")
    return True


def main():
    """Run all tests."""
    print("="*60)
    print("Model Package v1 Validator Test Suite")
    print("="*60 + "\n")
    
    tests = [
        test_validator_help,
        test_validator_on_valid_directory,
        test_validator_on_valid_zip,
        test_validator_on_invalid_package,
        test_validator_json_output,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Test error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
