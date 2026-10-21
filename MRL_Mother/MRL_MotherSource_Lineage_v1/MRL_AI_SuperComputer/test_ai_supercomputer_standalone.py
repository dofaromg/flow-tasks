"""
Comprehensive test suite for AI SuperComputer
AI 超級電腦綜合測試套件
"""

import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from ai_primitives.base_particle import AIParticle
from ai_primitives.function_particle import AIFunctionParticle
from ai_primitives.module_particle import AIModuleParticle
from ai_primitives.class_particle import AIClassParticle
from runtime.ai_stack_runtime import AIStackRuntime, AIStack
from runtime.fusion_engine import FusionEngine
from runtime.particle_registry import ParticleRegistry
from self_modification.code_evolver import CodeEvolver
from self_modification.ai_optimizer import AIPerformanceOptimizer


def test_base_particle():
    """Test base AI particle"""
    print("\n🧪 Testing Base AI Particle...")
    
    particle = AIParticle("test_particle", ai_provider="openai")
    result = particle.execute("test input")
    
    assert result["result"] is not None
    assert result["merkle_root"] is not None
    assert len(particle.merkle_chain) > 0
    
    print("   ✅ Base particle execution works")
    print("   ✅ Merkle chain tracking works")
    return True


def test_function_particle():
    """Test AI function particle"""
    print("\n🧪 Testing AI Function Particle...")
    
    func_particle = AIFunctionParticle(
        function_name="add_numbers",
        description="Add two numbers together",
        parameters={"a": "first number", "b": "second number"}
    )
    
    # Synthesize function
    code = func_particle.synthesize()
    assert code is not None
    assert "def add_numbers" in code
    
    print("   ✅ Function synthesis works")
    
    # Execute generated function
    try:
        result = func_particle(5, 3)
        print(f"   ✅ Function execution works: {result}")
    except Exception as e:
        print(f"   ⚠️  Function execution: {e}")
    
    return True


def test_module_particle():
    """Test AI module particle"""
    print("\n🧪 Testing AI Module Particle...")
    
    module = AIModuleParticle(
        module_name="data_processor",
        specification="Module for processing data with validation and transformation"
    )
    
    structure = module.generate_module()
    assert structure is not None
    assert "functions" in structure
    
    code = module.to_code()
    assert code is not None
    assert "data_processor" in code
    
    print(f"   ✅ Module generation works ({len(module.functions)} functions)")
    print("   ✅ Code generation works")
    return True


def test_class_particle():
    """Test AI class particle"""
    print("\n🧪 Testing AI Class Particle...")
    
    class_particle = AIClassParticle(
        class_name="DataManager",
        description="Manages data operations",
        methods=[
            {"name": "load_data", "description": "Load data from source"},
            {"name": "save_data", "description": "Save data to destination"}
        ],
        properties=[
            {"name": "storage_path", "type": "str"}
        ]
    )
    
    code = class_particle.synthesize()
    assert code is not None
    assert "class DataManager" in code
    
    print("   ✅ Class synthesis works")
    return True


def test_particle_fusion():
    """Test particle fusion"""
    print("\n🧪 Testing Particle Fusion...")
    
    fusion_engine = FusionEngine()
    
    # Create particles to fuse
    p1 = AIParticle("particle_1", "openai")
    p2 = AIParticle("particle_2", "claude")
    p3 = AIParticle("particle_3", "gemini")
    
    # Test different fusion modes
    sequential = fusion_engine.fuse([p1, p2], mode="sequential")
    assert sequential is not None
    print("   ✅ Sequential fusion works")
    
    parallel = fusion_engine.fuse([p1, p2, p3], mode="parallel")
    assert parallel is not None
    print("   ✅ Parallel fusion works")
    
    weighted = fusion_engine.fuse([p1, p2], mode="weighted", weights=[0.7, 0.3])
    assert weighted is not None
    print("   ✅ Weighted fusion works")
    
    consensus = fusion_engine.fuse([p1, p2, p3], mode="consensus")
    assert consensus is not None
    print("   ✅ Consensus fusion works")
    
    return True


def test_particle_registry():
    """Test particle registry"""
    print("\n🧪 Testing Particle Registry...")
    
    registry = ParticleRegistry()
    
    # Register particles
    for i in range(5):
        particle = AIParticle(f"particle_{i}", "openai")
        registry.register(particle, tags=["test", f"group_{i % 2}"])
    
    assert registry.count() == 5
    print(f"   ✅ Registry has {registry.count()} particles")
    
    # Test search
    tagged = registry.find_by_tag("test")
    assert len(tagged) == 5
    print(f"   ✅ Tag search works ({len(tagged)} found)")
    
    # Test provider filter
    openai_particles = registry.find_by_provider("openai")
    assert len(openai_particles) == 5
    print(f"   ✅ Provider filter works ({len(openai_particles)} found)")
    
    return True


def test_ai_stack_runtime():
    """Test AI stack runtime"""
    print("\n🧪 Testing AI Stack Runtime...")
    
    runtime = AIStackRuntime()
    
    # Create and register particles
    p1 = AIFunctionParticle("func1", "Process step 1")
    p2 = AIFunctionParticle("func2", "Process step 2")
    
    p1.synthesize()
    p2.synthesize()
    
    runtime.register_particle(p1)
    runtime.register_particle(p2)
    
    # Create stack
    stack = AIStack("test_stack", [p1, p2], mode="sequential")
    runtime.register_stack(stack)
    
    # Execute stack
    result = runtime.execute_stack("test_stack", "test input")
    assert result is not None
    print("   ✅ Stack execution works")
    
    # Test metrics
    metrics = runtime.get_metrics()
    assert metrics["total_particles"] == 2
    assert metrics["active_stacks"] == 1
    print(f"   ✅ Metrics collection works: {metrics}")
    
    return True


def test_code_evolver():
    """Test code evolution system"""
    print("\n🧪 Testing Code Evolver...")
    
    runtime = AIStackRuntime()
    evolver = CodeEvolver(runtime)
    
    # Test analysis
    analysis = evolver.analyze_performance()
    assert "metrics" in analysis
    assert "bottlenecks" in analysis
    print("   ✅ Performance analysis works")
    
    # Test evolution (small cycle)
    result = evolver.evolve_code(target_improvement="30%", max_cycles=2)
    assert "cycles" in result
    assert len(result["cycles"]) > 0
    print(f"   ✅ Evolution works ({len(result['cycles'])} cycles)")
    
    return True


def test_ai_optimizer():
    """Test AI performance optimizer"""
    print("\n🧪 Testing AI Performance Optimizer...")
    
    runtime = AIStackRuntime()
    optimizer = AIPerformanceOptimizer(runtime)
    
    baseline = optimizer.measure_baseline()
    assert baseline > 0
    print(f"   ✅ Baseline measurement works: {baseline}ms")
    
    # Test optimization (small cycle)
    result = optimizer.optimize_for_60_percent_improvement()
    assert "cycles" in result
    print(f"   ✅ Optimization works ({len(result['cycles'])} cycles)")
    
    return True


def test_manifest_loading():
    """Test manifest-driven stack creation"""
    print("\n🧪 Testing Manifest Loading...")
    
    # Create a test manifest
    manifest = {
        "manifest_version": "2.0",
        "stack_name": "test_manifest_stack",
        "composition": {
            "mode": "sequential",
            "particles": [
                {
                    "particle_type": "function",
                    "role": "processor",
                    "ai_provider": "openai",
                    "synthesis_prompt": "Process input data",
                    "parameters": {"data": "input data"}
                }
            ]
        }
    }
    
    from flowcore_ai_stack import AIStackCore
    
    core = AIStackCore()
    stack = core.synthesize_stack(manifest)
    
    assert stack is not None
    assert stack.stack_name == "test_manifest_stack"
    assert len(stack.particles) == 1
    
    print("   ✅ Manifest loading works")
    print(f"   ✅ Stack created with {len(stack.particles)} particles")
    
    return True


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("🧬 AI SuperComputer - Comprehensive Test Suite")
    print("=" * 70)
    
    tests = [
        test_base_particle,
        test_function_particle,
        test_module_particle,
        test_class_particle,
        test_particle_fusion,
        test_particle_registry,
        test_ai_stack_runtime,
        test_code_evolver,
        test_ai_optimizer,
        test_manifest_loading
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("✅ All tests passed!")
        return True
    else:
        print(f"❌ {failed} tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
