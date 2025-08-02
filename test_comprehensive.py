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

def test_task_processor():
    """Test the task processing system"""
    print("=== Testing Task Processor ===")
    
    # Run task processor
    result = subprocess.run([sys.executable, "process_tasks.py"], 
                          capture_output=True, text=True)
    
    print(f"Exit code: {result.returncode}")
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    # Check if results were created
    results_dir = Path("tasks/results")
    if results_dir.exists():
        print(f"✓ Results directory exists: {results_dir}")
        
        # List result files
        result_files = list(results_dir.glob("*.json"))
        print(f"✓ Found {len(result_files)} result files:")
        for f in result_files:
            print(f"  - {f.name}")
    else:
        print("✗ Results directory missing")
        return False
    
    return result.returncode == 0

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
        if response.status_code == 200:
            data = response.json()
            expected_message = "你好，世界"
            if data.get("message") == expected_message:
                print(f"✓ Main endpoint working: {data['message']}")
            else:
                print(f"✗ Wrong message: expected '{expected_message}', got '{data.get('message')}'")
                return False
        else:
            print(f"✗ Main endpoint failed: {response.status_code}")
            return False
        
        # Test health endpoint
        print("Testing health endpoint (/health)...")
        response = requests.get("http://localhost:5000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print(f"✓ Health endpoint working: {data}")
            else:
                print(f"✗ Health check failed: {data}")
                return False
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
            return False
        
        # Test info endpoint
        print("Testing info endpoint (/info)...")
        response = requests.get("http://localhost:5000/info", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("task_id") == "hello-world-api":
                print(f"✓ Info endpoint working: task_id = {data['task_id']}")
            else:
                print(f"✗ Info endpoint incorrect: {data}")
                return False
        else:
            print(f"✗ Info endpoint failed: {response.status_code}")
            return False
            
        print("✓ All Flask API tests passed!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
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
        result = subprocess.run([sys.executable, "test_integration.py"], 
                              capture_output=True, text=True)
        
        print(f"Exit code: {result.returncode}")
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"✗ Particle core test failed: {e}")
        return False

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
    
    if missing_files:
        print(f"✗ Missing required files: {missing_files}")
        return False
    else:
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
            print(f"✗ Task definition missing: {task_file}")
            return False
    
    print("✓ System integration checks passed!")
    return True

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
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
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