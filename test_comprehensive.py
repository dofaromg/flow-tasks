#!/usr/bin/env python3
"""
Comprehensive test script for FlowAgent task system
Tests both the task processing system and Flask API functionality
"""

import os
import sys
import time
import json
import requests
import subprocess
import threading
from pathlib import Path

import pytest

def test_task_processor():
    """Test the task processing system"""
    print("=== Testing Task Processor ===")
    
    # Run task processor
    process_result = subprocess.run([sys.executable, "process_tasks.py"],
                          capture_output=True, text=True)
    
    print(f"Exit code: {process_result.returncode}")
    print("STDOUT:")
    print(process_result.stdout)
    
    if process_result.stderr:
        print("STDERR:")
        print(process_result.stderr)
    
    # Check if results were created
    results_dir = Path("tasks/results")
    assert results_dir.exists(), "Results directory missing"
    print(f"✓ Results directory exists: {results_dir}")

    # List result files
    result_files = list(results_dir.glob("*.json"))
    print(f"✓ Found {len(result_files)} result files:")
    for result_file in result_files:
        print(f"  - {result_file.name}")

    assert process_result.returncode == 0, "Task processor exited with errors"

def test_flask_api():
    """Test the Flask API by starting it and making requests"""
    print("\n=== Testing Flask API ===")
    
    # Start Flask server in background
    print("Starting Flask server...")
    server_process = subprocess.Popen([
        sys.executable, "flow_code/hello_api.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test main endpoint
        print("Testing main endpoint (/)...")
        response = requests.get("http://localhost:5000/", timeout=10)
        assert response.status_code == 200, f"Main endpoint failed: {response.status_code}"
        data = response.json()
        expected_message = "你好，世界"
        assert data.get("message") == expected_message, \
            f"Wrong message: expected '{expected_message}', got '{data.get('message')}'"
        print(f"✓ Main endpoint working: {data['message']}")

        # Test health endpoint
        print("Testing health endpoint (/health)...")
        response = requests.get("http://localhost:5000/health", timeout=10)
        assert response.status_code == 200, f"Health endpoint failed: {response.status_code}"
        data = response.json()
        assert data.get("status") == "healthy", f"Health check failed: {data}"
        print(f"✓ Health endpoint working: {data}")

        # Test info endpoint
        print("Testing info endpoint (/info)...")
        response = requests.get("http://localhost:5000/info", timeout=10)
        assert response.status_code == 200, f"Info endpoint failed: {response.status_code}"
        data = response.json()
        assert data.get("task_id") == "hello-world-api", f"Info endpoint incorrect: {data}"
        print(f"✓ Info endpoint working: task_id = {data['task_id']}")

        print("✓ All Flask API tests passed!")

    except requests.exceptions.RequestException as request_error:
        pytest.fail(f"Request failed: {request_error}")
    except Exception as test_error:
        pytest.fail(f"Test failed: {test_error}")
    finally:
        # Stop server
        print("Stopping Flask server...")
        server_process.terminate()
        server_process.wait()

def test_particle_core():
    """Test the particle core system"""
    print("\n=== Testing Particle Core System ===")
    
    try:
        # Run the existing integration test
        process_result = subprocess.run([sys.executable, "test_integration.py"],
                              capture_output=True, text=True)

        print(f"Exit code: {process_result.returncode}")
        print("STDOUT:")
        print(process_result.stdout)

        if process_result.stderr:
            print("STDERR:")
            print(process_result.stderr)

        assert process_result.returncode == 0, "Particle core integration test failed"
    except Exception as test_error:
        pytest.fail(f"Particle core test failed: {test_error}")

def test_system_integration():
    """Test overall system integration"""
    print("\n=== Testing System Integration ===")
    
    # Check that all required components exist
    required_files = [
        "flow_code/hello_api.py",
        "particle_core/src/logic_pipeline.py",
        "process_tasks.py",
        "test_integration.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    assert not missing_files, f"Missing required files: {missing_files}"
    print("✓ All required files present")
    
    # Check task definitions
    task_files = [
        "tasks/2025-06-29_hello-world-api.yaml",
        "tasks/2025-07-31_particle-language-core.yaml"
    ]

    for task_file in task_files:
        if Path(task_file).exists():
            print(f"✓ Task definition exists: {task_file}")
        else:
            pytest.fail(f"Task definition missing: {task_file}")

    print("✓ System integration checks passed!")

def main():
    """Run all tests"""
    print("FlowAgent Comprehensive Test Suite")
    print("=" * 50)
    
    os.chdir(Path(__file__).parent)
    
    tests = [
        ("System Integration", test_system_integration),
        ("Task Processor", test_task_processor),
        ("Particle Core", test_particle_core),
        ("Flask API", test_flask_api),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
            results[test_name] = True
        except AssertionError as assertion_error:
            print(f"✗ {test_name} assertion failed: {assertion_error}")
            results[test_name] = False
        except Exception as test_error:
            print(f"✗ {test_name} test crashed: {test_error}")
            results[test_name] = False
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        icon = "✓" if passed else "✗"
        print(f"{icon} {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! FlowAgent system is fully functional.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. System needs attention.")
        sys.exit(1)

if __name__ == "__main__":
    main()
