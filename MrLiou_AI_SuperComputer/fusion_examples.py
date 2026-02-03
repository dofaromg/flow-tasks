#!/usr/bin/env python3
"""
AI Fusion Stack Examples
示範所有四種融合模式的完整範例

Run this after starting the server:
  python3 flowcore_loop.py

Then run:
  python3 fusion_examples.py
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8787"

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def test_health():
    """Test server health"""
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/judge/health")
    data = response.json()
    print(f"Status: {data.get('ok')}")
    print(f"Merkle Anchor: {data.get('anchor', '')[:16]}...")

def list_manifests():
    """List available fusion manifests"""
    print_section("2. List Available Fusion Manifests")
    response = requests.get(f"{BASE_URL}/ai/fusion/manifests")
    data = response.json()
    
    if data.get('ok'):
        manifests = data.get('manifests', [])
        print(f"Found {len(manifests)} manifests:\n")
        for m in manifests:
            print(f"  • {m['name']} ({m['mode']})")
            print(f"    {m['description']}")
            print()

def test_sequential_fusion():
    """Test sequential fusion"""
    print_section("3. Sequential Fusion - Each AI refines the previous output")
    
    payload = {
        "prompt": "Explain quantum entanglement in simple terms",
        "manifest": "sequential_refine"
    }
    
    print(f"Prompt: {payload['prompt']}")
    print(f"Manifest: {payload['manifest']}\n")
    
    response = requests.post(
        f"{BASE_URL}/ai/fusion/execute",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    
    data = response.json()
    if data.get('ok'):
        result = data['result']
        print(f"Fusion ID: {result['fusion_id']}")
        print(f"Mode: {result['mode']}")
        print(f"Particles: {result['particle_count']}")
        print(f"\nOutputs chain:")
        for i, output in enumerate(result['outputs']):
            print(f"  {i+1}. {output['provider']} ({output['role']})")
            print(f"     {output['output'][:80]}...")
        print(f"\nFinal result: {result['final_result'][:100]}...")

def test_parallel_fusion():
    """Test parallel fusion"""
    print_section("4. Parallel Fusion - All AIs process simultaneously")
    
    payload = {
        "prompt": "What are the benefits and risks of artificial intelligence?",
        "manifest": "parallel_consensus"
    }
    
    print(f"Prompt: {payload['prompt']}")
    print(f"Manifest: {payload['manifest']}\n")
    
    response = requests.post(
        f"{BASE_URL}/ai/fusion/execute",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    
    data = response.json()
    if data.get('ok'):
        result = data['result']
        print(f"Fusion ID: {result['fusion_id']}")
        print(f"Mode: {result['mode']}")
        print(f"Particles: {result['particle_count']}")
        print(f"\nParallel outputs:")
        for i, output in enumerate(result['outputs']):
            print(f"  {i+1}. {output['provider']} ({output['role']})")
            print(f"     {output['output'][:80]}...")
        print(f"\nMerged result:\n{result['final_result'][:200]}...")

def test_mobius_loop():
    """Test Möbius loop (recursive fusion)"""
    print_section("5. Möbius Loop - Output cycles back as input")
    
    payload = {
        "prompt": "Design a sustainable city of the future",
        "max_cycles": 4,
        "convergence_threshold": 0.85
    }
    
    print(f"Prompt: {payload['prompt']}")
    print(f"Max Cycles: {payload['max_cycles']}")
    print(f"Convergence Threshold: {payload['convergence_threshold']}\n")
    
    response = requests.post(
        f"{BASE_URL}/ai/fusion/mobius",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    
    data = response.json()
    if data.get('ok'):
        result = data['result']
        print(f"Loop ID: {result['loop_id']}")
        print(f"Converged: {result['converged']}")
        print(f"Total Cycles: {result['total_cycles']}")
        print(f"\nCycle evolution:")
        for cycle in result['cycle_history']:
            print(f"  Cycle {cycle['cycle']}: Similarity = {cycle['similarity']:.2%}")
        print(f"\nFinal output: {result['final_output'][:100]}...")

def test_custom_fusion():
    """Test custom fusion on-the-fly"""
    print_section("6. Custom Fusion - Weighted blend of 2 AIs")
    
    payload = {
        "prompt": "Write a haiku about artificial intelligence",
        "mode": "weighted",
        "particles": [
            {"provider": "claude", "weight": 0.6, "role": "poet"},
            {"provider": "gemini", "weight": 0.4, "role": "critic"}
        ]
    }
    
    print(f"Prompt: {payload['prompt']}")
    print(f"Mode: {payload['mode']}")
    print(f"Particles: 2 (Claude 60%, Gemini 40%)\n")
    
    response = requests.post(
        f"{BASE_URL}/ai/fusion/custom",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    
    data = response.json()
    if data.get('ok'):
        result = data['result']
        print(f"Fusion ID: {result['fusion_id']}")
        print(f"Mode: {result['mode']}")
        print(f"\nWeighted outputs:")
        for i, output in enumerate(result['outputs']):
            weight = output.get('weight', 1.0)
            print(f"  {i+1}. {output['provider']} (weight: {weight*100:.0f}%)")
        print(f"\nWeighted merge:\n{result['final_result'][:200]}...")

def main():
    """Run all examples"""
    print("\n" + "🌀" * 40)
    print("  AI Fusion Stack - Complete Examples")
    print("  基於粒子語言核心的 AI 融合系統")
    print("🌀" * 40)
    
    try:
        test_health()
        time.sleep(0.5)
        
        list_manifests()
        time.sleep(0.5)
        
        test_sequential_fusion()
        time.sleep(0.5)
        
        test_parallel_fusion()
        time.sleep(0.5)
        
        test_mobius_loop()
        time.sleep(0.5)
        
        test_custom_fusion()
        
        print_section("✅ All Examples Completed")
        print("Check memory/ingest/fusion/ and memory/ingest/mobius/ for outputs")
        print("Check log/trace.jsonl for Merkle chain audit trail")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Server not running!")
        print("Start the server first: python3 flowcore_loop.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
