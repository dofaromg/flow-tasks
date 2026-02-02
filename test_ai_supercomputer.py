#!/usr/bin/env python3
"""
Integration tests for MrLiou AI SuperComputer with multi-provider support
測試 MrLiou AI 超級電腦的多提供商支援
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error

def test_file_structure():
    """Test that all required files are in place"""
    print("\n=== Testing File Structure ===")
    
    required_files = [
        "MrLiou_AI_SuperComputer/flowcore_loop.py",
        "MrLiou_AI_SuperComputer/ai_providers.py",
        "MrLiou_AI_SuperComputer/config/ai_providers.json",
        "MrLiou_AI_SuperComputer/config/env_template.txt",
        "MrLiou_AI_SuperComputer/docs/SUPERCOMPUTER_QUICKSTART.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False
    
    return all_exist


def test_ai_providers_import():
    """Test that ai_providers module can be imported"""
    print("\n=== Testing AI Providers Import ===")
    
    # Add MrLiou_AI_SuperComputer to path
    sys.path.insert(0, os.path.join(os.getcwd(), "MrLiou_AI_SuperComputer"))
    
    try:
        from ai_providers import (
            BaseAIProvider,
            OpenAIProvider,
            ClaudeProvider,
            GeminiProvider,
            OllamaProvider,
            AzureOpenAIProvider,
            AIProviderManager
        )
        print("✓ All AI provider classes imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_provider_manager_config():
    """Test AIProviderManager configuration loading"""
    print("\n=== Testing Provider Manager Configuration ===")
    
    sys.path.insert(0, os.path.join(os.getcwd(), "MrLiou_AI_SuperComputer"))
    
    try:
        from ai_providers import AIProviderManager
        
        config_path = "MrLiou_AI_SuperComputer/config/ai_providers.json"
        
        # Test config loading
        manager = AIProviderManager(config_path)
        print(f"✓ Configuration loaded from {config_path}")
        
        # Check default provider
        default = manager.config.get("default_provider")
        print(f"✓ Default provider: {default}")
        
        # Check fallback settings
        fallback_enabled = manager.config.get("fallback_enabled")
        fallback_order = manager.config.get("fallback_order", [])
        print(f"✓ Fallback enabled: {fallback_enabled}")
        print(f"✓ Fallback order: {fallback_order}")
        
        # List initialized providers
        providers = manager.list_providers()
        print(f"✓ Initialized providers: {len(providers)}")
        for p in providers:
            status = "✓ available" if p["available"] else "✗ unavailable"
            print(f"  - {p['provider']}: {p['model']} ({status})")
        
        return True
        
    except Exception as e:
        print(f"✗ Provider manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_provider_availability():
    """Test provider availability checks"""
    print("\n=== Testing Provider Availability ===")
    
    sys.path.insert(0, os.path.join(os.getcwd(), "MrLiou_AI_SuperComputer"))
    
    try:
        from ai_providers import (
            OpenAIProvider,
            ClaudeProvider,
            OllamaProvider
        )
        
        # Test OpenAI provider (without API key)
        openai_config = {
            "api_key": "",
            "model": "gpt-4",
            "base_url": "https://api.openai.com/v1"
        }
        openai = OpenAIProvider(openai_config)
        available = openai.is_available()
        print(f"OpenAI provider (no key): {'✓ correctly unavailable' if not available else '✗ should be unavailable'}")
        
        # Test with mock API key
        openai_config["api_key"] = "sk-test-key"
        openai = OpenAIProvider(openai_config)
        available = openai.is_available()
        print(f"OpenAI provider (with key): {'✓ correctly available' if available else '✗ should be available'}")
        
        # Test Ollama provider (local)
        ollama_config = {
            "base_url": "http://localhost:11434",
            "model": "llama2"
        }
        ollama = OllamaProvider(ollama_config)
        available = ollama.is_available()
        status = "available (server running)" if available else "unavailable (server not running)"
        print(f"Ollama provider: {status}")
        
        return True
        
    except Exception as e:
        print(f"✗ Availability test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_env_variable_substitution():
    """Test environment variable substitution"""
    print("\n=== Testing Environment Variable Substitution ===")
    
    sys.path.insert(0, os.path.join(os.getcwd(), "MrLiou_AI_SuperComputer"))
    
    try:
        from ai_providers import AIProviderManager
        
        # Set test environment variables
        os.environ["TEST_API_KEY"] = "test-key-12345"
        
        # Create a test config
        test_config = {
            "default_provider": "test",
            "providers": {
                "test": {
                    "enabled": True,
                    "api_key": "${TEST_API_KEY}",
                    "other_value": "static-value"
                }
            }
        }
        
        # Save test config
        test_config_path = "/tmp/test_ai_config.json"
        with open(test_config_path, "w") as f:
            json.dump(test_config, f)
        
        # Load and check substitution
        manager = AIProviderManager(test_config_path)
        
        test_provider_config = manager.config["providers"]["test"]
        substituted_key = test_provider_config["api_key"]
        
        if substituted_key == "test-key-12345":
            print("✓ Environment variable substitution works correctly")
            return True
        else:
            print(f"✗ Substitution failed: expected 'test-key-12345', got '{substituted_key}'")
            return False
            
    except Exception as e:
        print(f"✗ Environment variable test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if "TEST_API_KEY" in os.environ:
            del os.environ["TEST_API_KEY"]
        if os.path.exists("/tmp/test_ai_config.json"):
            os.remove("/tmp/test_ai_config.json")


def test_server_startup():
    """Test that the server can start with AI providers"""
    print("\n=== Testing Server Startup ===")
    
    try:
        # Change to the SuperComputer directory
        original_dir = os.getcwd()
        os.chdir("MrLiou_AI_SuperComputer")
        
        # Start server in background
        print("Starting server...")
        server_process = subprocess.Popen(
            ["python3", "flowcore_loop.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        time.sleep(3)
        
        # Check if server is running
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            print(f"✗ Server failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            os.chdir(original_dir)
            return False
        
        print("✓ Server started successfully")
        
        # Test health endpoint
        try:
            req = urllib.request.Request("http://127.0.0.1:8787/judge/health")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get("ok"):
                    print("✓ Health endpoint responding")
                else:
                    print("✗ Health endpoint returned error")
        except Exception as e:
            print(f"✗ Health endpoint failed: {e}")
        
        # Test AI providers endpoint
        try:
            req = urllib.request.Request("http://127.0.0.1:8787/ai/providers")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get("ok") and "providers" in data:
                    print(f"✓ AI providers endpoint responding ({len(data['providers'])} providers)")
                    for provider in data['providers']:
                        status = "available" if provider["available"] else "unavailable"
                        print(f"  - {provider['provider']}: {status}")
                else:
                    print("✗ AI providers endpoint returned unexpected data")
        except Exception as e:
            print(f"Note: AI providers endpoint: {e} (expected if no API keys configured)")
        
        # Stop server
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("✓ Server stopped cleanly")
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("✓ Server killed after timeout")
        
        os.chdir(original_dir)
        return True
        
    except Exception as e:
        print(f"✗ Server test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up
        try:
            if 'server_process' in locals():
                server_process.kill()
        except Exception as cleanup_error:
            # Ignore cleanup errors - process may already be terminated
            print(f"Note: failed to kill server process during cleanup: {cleanup_error}")
        
        os.chdir(original_dir)
        return False


def test_cost_calculation():
    """Test cost calculation logic"""
    print("\n=== Testing Cost Calculation ===")
    
    sys.path.insert(0, os.path.join(os.getcwd(), "MrLiou_AI_SuperComputer"))
    
    try:
        # Import the function
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "flowcore_loop",
            "MrLiou_AI_SuperComputer/flowcore_loop.py"
        )
        flowcore = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(flowcore)
        
        # Test OpenAI GPT-4 cost calculation
        usage = {
            "prompt_tokens": 1000,
            "completion_tokens": 500
        }
        cost = flowcore._calculate_cost("openai", "gpt-4", usage)
        
        expected_cost = (1000/1000 * 0.03) + (500/1000 * 0.06)  # $0.03 + $0.03 = $0.06
        
        if abs(cost["estimated_cost_usd"] - expected_cost) < 0.0001:
            print(f"✓ Cost calculation correct: ${cost['estimated_cost_usd']}")
        else:
            print(f"✗ Cost calculation incorrect: expected ${expected_cost}, got ${cost['estimated_cost_usd']}")
            return False
        
        # Test Claude cost calculation
        usage = {
            "input_tokens": 1000,
            "output_tokens": 1000
        }
        cost = flowcore._calculate_cost("claude", "claude-3-opus-20240229", usage)
        
        expected_cost = (1000/1000 * 0.015) + (1000/1000 * 0.075)  # $0.015 + $0.075 = $0.09
        
        if abs(cost["estimated_cost_usd"] - expected_cost) < 0.0001:
            print(f"✓ Claude cost calculation correct: ${cost['estimated_cost_usd']}")
        else:
            print(f"✗ Claude cost calculation incorrect: expected ${expected_cost}, got ${cost['estimated_cost_usd']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Cost calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("MrLiou AI SuperComputer - Integration Tests")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("File Structure", test_file_structure()))
    results.append(("AI Providers Import", test_ai_providers_import()))
    results.append(("Provider Manager Config", test_provider_manager_config()))
    results.append(("Provider Availability", test_provider_availability()))
    results.append(("Environment Variables", test_env_variable_substitution()))
    results.append(("Cost Calculation", test_cost_calculation()))
    results.append(("Server Startup", test_server_startup()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {test_name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
