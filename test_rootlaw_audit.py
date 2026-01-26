#!/usr/bin/env python3
"""
Test script for RootLaw Symbiosis Audit
Validates the workflow and script functionality
"""

import subprocess
import sys
from pathlib import Path


def test_grep_pattern():
    """Test that grep finds exactly 42 laws with the 第.*條 pattern."""
    print("Testing grep pattern for Chinese law numbering...")
    result = subprocess.run(
        ["grep", "-c", "第.*條", "RootLaw_Package_v1.midlock/RootLaws_v1.md"],
        capture_output=True,
        text=True
    )
    
    count = int(result.stdout.strip())
    assert count == 42, f"Expected 42 laws, found {count}"
    print(f"✅ Grep test passed: Found {count} laws")
    return True


def test_symbiosis_audit():
    """Test the symbiosis audit script."""
    print("\nTesting symbiosis audit script...")
    result = subprocess.run(
        ["python3", "scripts/symbiosis_audit.py", "--map", "RootLaw_Package_v1.midlock/Absorption_Map.md"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed with exit code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
    assert "All symbiosis checks PASSED" in result.stdout, "Expected success message not found"
    print("✅ Symbiosis audit test passed")
    return True


def test_workflow_yaml():
    """Test that the workflow YAML is valid."""
    print("\nTesting workflow YAML validity...")
    import yaml
    
    workflow_path = Path(".github/workflows/rootlaw-symbiosis-audit.yml")
    assert workflow_path.exists(), f"Workflow file not found: {workflow_path}"
    
    with open(workflow_path) as f:
        workflow = yaml.safe_load(f)
    
    assert workflow['name'] == 'RootLaw Symbiosis Audit', "Workflow name mismatch"
    # YAML 'on' field is loaded with 'on' as key or True depending on YAML parser
    assert 'on' in workflow or True in workflow, "Workflow trigger not found"
    assert 'jobs' in workflow and 'audit' in workflow['jobs'], "Audit job not found"
    print("✅ Workflow YAML test passed")
    return True


def test_file_integrity():
    """Test that all required files exist."""
    print("\nTesting file integrity...")
    required_files = [
        "RootLaw_Package_v1.midlock/RootLaws_v1.md",
        "RootLaw_Package_v1.midlock/Absorption_Map.md",
        "RootLaw_Package_v1.midlock/Execution_Laws.md",
        "RootLaw_Package_v1.midlock/Evidence_Index.md",
        "RootLaw_Package_v1.midlock/Progress_Snapshot.md",
        "scripts/symbiosis_audit.py",
        ".github/workflows/rootlaw-symbiosis-audit.yml"
    ]
    
    for filepath in required_files:
        path = Path(filepath)
        assert path.exists(), f"Required file not found: {filepath}"
        print(f"  ✅ {filepath}")
    
    print("✅ File integrity test passed")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("RootLaw Symbiosis Audit - Test Suite")
    print("=" * 60)
    
    try:
        test_file_integrity()
        test_grep_pattern()
        test_symbiosis_audit()
        test_workflow_yaml()
        
        print("\n" + "=" * 60)
        print("✅ All tests PASSED")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
