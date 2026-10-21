#!/usr/bin/env python3
"""
Demo script for MrLiou AI SuperComputer with AI providers
演示 MrLiou AI 超級電腦的 AI 提供商功能
"""

import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8787"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def health_check():
    """Check server health"""
    print_section("1. Health Check / 健康檢查")
    
    try:
        req = urllib.request.Request(f"{BASE_URL}/judge/health")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"✓ Server is healthy")
            print(f"✓ Merkle anchor: {data.get('anchor', 'N/A')[:16]}...")
            return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def list_providers():
    """List all available AI providers"""
    print_section("2. List AI Providers / 列出 AI 提供商")
    
    try:
        req = urllib.request.Request(f"{BASE_URL}/ai/providers")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            if data.get("ok") and "providers" in data:
                providers = data["providers"]
                print(f"Found {len(providers)} configured providers:\n")
                
                for i, provider in enumerate(providers, 1):
                    status = "✓ Available" if provider["available"] else "✗ Unavailable (missing API key or unreachable)"
                    print(f"{i}. {provider['provider']}")
                    print(f"   Model: {provider['model']}")
                    print(f"   Status: {status}\n")
                
                return providers
            else:
                print(f"✗ Unexpected response: {data}")
                return []
                
    except Exception as e:
        print(f"✗ Failed to list providers: {e}")
        return []


def test_ai_completion():
    """Test AI completion endpoint"""
    print_section("3. AI Completion Test / AI 完成測試")
    
    print("Note: This will only work if you have configured API keys")
    print("注意：這只有在您設定了 API 金鑰後才能運作\n")
    
    # Test data
    test_prompt = "Explain in one sentence what a computer is."
    
    print(f"Prompt: {test_prompt}\n")
    
    try:
        # Prepare request
        data = {
            "prompt": test_prompt,
            "options": {
                "max_tokens": 100,
                "temperature": 0.7
            }
        }
        
        req = urllib.request.Request(
            f"{BASE_URL}/ai/complete",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            
            if result.get("ok"):
                print("✓ AI Completion Successful!\n")
                print(f"Provider: {result.get('provider')}")
                print(f"Model: {result.get('model')}")
                print(f"Request ID: {result.get('request_id')}\n")
                print(f"Response:\n{result.get('content', 'N/A')}\n")
                
                # Show cost
                cost = result.get('cost', {})
                
                print(f"Token Usage:")
                print(f"  - Input: {cost.get('input_tokens', 0)}")
                print(f"  - Output: {cost.get('output_tokens', 0)}")
                print(f"  - Total: {cost.get('total_tokens', 0)}")
                print(f"  - Estimated Cost: ${cost.get('estimated_cost_usd', 0):.6f}")
                
                print(f"\nResponse saved to: {result.get('response_path')}")
                print(f"Merkle root: {result.get('merkle_root', 'N/A')[:16]}...")
                
                return True
            else:
                print(f"✗ Completion failed: {result}")
                return False
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"✗ HTTP Error {e.code}: {error_body}")
        
        if e.code == 503:
            print("\nThis is expected if no API keys are configured.")
            print("這在沒有設定 API 金鑰時是正常的。")
        
        return False
        
    except Exception as e:
        print(f"✗ Completion test failed: {e}")
        return False


def demo_vault_write():
    """Demonstrate vault write functionality"""
    print_section("4. Vault Write Demo / 資料庫寫入演示")
    
    try:
        # Prepare request
        data = {
            "path": "memory/ingest/raw/demo_test.txt",
            "text": f"Demo test at {json.dumps({'timestamp': 'now'})}"
        }
        
        req = urllib.request.Request(
            f"{BASE_URL}/vault/write_text",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            
            if result.get("ok"):
                print(f"✓ File written successfully")
                print(f"  Path: {data['path']}")
                print(f"  SHA256: {result['res']['sha256'][:16]}...")
                
                if result.get('snapshot'):
                    print(f"  Snapshot: {result['snapshot']['snapshot']}")
                
                return True
            else:
                print(f"✗ Write failed: {result}")
                return False
                
    except Exception as e:
        print(f"✗ Vault write test failed: {e}")
        return False


def demo_search():
    """Demonstrate L1 search functionality"""
    print_section("5. L1 Search Demo / L1 搜尋演示")
    
    try:
        query = "demo"
        req = urllib.request.Request(f"{BASE_URL}/l1/search?q={query}")
        
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            
            if result.get("ok"):
                hits = result.get("hits", [])
                print(f"✓ Search completed")
                print(f"  Query: {query}")
                print(f"  Hits: {len(hits)}")
                
                for hit in hits[:5]:  # Show top 5
                    print(f"    - {hit['file']} (score: {hit['score']})")
                
                return True
            else:
                print(f"✗ Search failed: {result}")
                return False
                
    except Exception as e:
        print(f"✗ Search test failed: {e}")
        return False


def show_usage_instructions():
    """Show instructions for setting up API keys"""
    print_section("Setup Instructions / 設定說明")
    
    print("To use AI providers, you need to configure API keys:")
    print("要使用 AI 提供商，您需要設定 API 金鑰：\n")
    
    print("1. Copy the environment template:")
    print("   複製環境變數範本：")
    print("   $ cp MrLiou_AI_SuperComputer/config/env_template.txt .env\n")
    
    print("2. Edit .env and add your API keys:")
    print("   編輯 .env 並新增您的 API 金鑰：")
    print("   OPENAI_API_KEY=sk-...")
    print("   ANTHROPIC_API_KEY=sk-ant-...")
    print("   etc.\n")
    
    print("3. Load environment variables:")
    print("   載入環境變數：")
    print("   $ export $(cat .env | xargs)\n")
    
    print("4. Restart the server:")
    print("   重新啟動伺服器：")
    print("   $ cd MrLiou_AI_SuperComputer && ./run.sh\n")


def main():
    """Run all demos"""
    print("=" * 60)
    print("  MrLiou AI SuperComputer - Demo Script")
    print("  MrLiou AI 超級電腦 - 演示腳本")
    print("=" * 60)
    
    # Check if server is running
    if not health_check():
        print("\n⚠ Please start the server first:")
        print("請先啟動伺服器：")
        print("$ cd MrLiou_AI_SuperComputer && ./run.sh\n")
        return
    
    # List providers
    providers = list_providers()
    
    # Check if any provider is available
    has_available = any(p["available"] for p in providers)
    
    if not has_available:
        print("\n⚠ No AI providers are currently available.")
        print("沒有可用的 AI 提供商。\n")
        show_usage_instructions()
    
    # Run other demos
    demo_vault_write()
    demo_search()
    
    # Try AI completion (will fail gracefully if no API keys)
    test_ai_completion()
    
    print("\n" + "=" * 60)
    print("  Demo Complete / 演示完成")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
