"""
MRL Runtime Snapshot Generator
Runs actual MRL components and writes runtime state to JSON.
Next.js API routes read this file for real data.
"""

import sys
import json
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from MrLiou_AI_SuperComputer.ai_fusion_core import (
    AIParticle as FusionParticle,
    FusionStack,
    MobiusLoop,
    BaseAIProvider,
)
from MrLiou_AI_SuperComputer.runtime.particle_registry import ParticleRegistry
from MrLiou_AI_SuperComputer.runtime.fusion_engine import FusionEngine
from MrLiou_AI_SuperComputer.runtime.ai_stack_runtime import AIStackRuntime
from MrLiou_AI_SuperComputer.ai_primitives.base_particle import AIParticle
from core.memory_system import FlowMemoryCore, MemoryType

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mrl_runtime_state.json")


def run_particle_registry():
    registry = ParticleRegistry()
    particles = [
        AIParticle("mrl-reasoning-v1", ai_provider="openai"),
        AIParticle("mrl-analysis-v1", ai_provider="claude"),
        AIParticle("mrl-creative-v1", ai_provider="gemini"),
        AIParticle("mrl-distillation-v1", ai_provider="claude"),
        AIParticle("mrl-fusion-v1", ai_provider="openai"),
    ]
    tags_map = {
        "mrl-reasoning-v1": ["core", "reasoning", "layer_a"],
        "mrl-analysis-v1": ["core", "analysis", "layer_a"],
        "mrl-creative-v1": ["core", "creative"],
        "mrl-distillation-v1": ["distillation", "knowledge_transfer"],
        "mrl-fusion-v1": ["fusion", "lora_composition"],
    }
    for p in particles:
        registry.register(p, tags=tags_map.get(p.particle_id, []))
    return {
        "stats": registry.get_stats(),
        "particles": [p.particle_id for p in particles],
    }


def run_fusion_engine():
    engine = FusionEngine()
    p1 = AIParticle("mrl-reasoning-v1", ai_provider="openai")
    p2 = AIParticle("mrl-analysis-v1", ai_provider="claude")
    p3 = AIParticle("mrl-creative-v1", ai_provider="gemini")

    engine.fuse([p1, p2], mode="sequential")
    engine.fuse([p1, p2, p3], mode="parallel")
    engine.fuse([p2, p3], mode="weighted")

    return {"fusion_history": engine.get_fusion_history()}


def run_ai_stack_runtime():
    runtime = AIStackRuntime()
    p1 = AIParticle("mrl-reasoning-v1", ai_provider="openai")
    p2 = AIParticle("mrl-analysis-v1", ai_provider="claude")
    p3 = AIParticle("mrl-creative-v1", ai_provider="gemini")
    runtime.register_particle(p1)
    runtime.register_particle(p2)
    runtime.register_particle(p3)
    return {"metrics": runtime.get_metrics()}


def run_convergence():
    provider_a = BaseAIProvider("openai", "gpt-4")
    provider_b = BaseAIProvider("claude", "claude-3-opus")
    provider_c = BaseAIProvider("gemini", "gemini-pro")

    pa = FusionParticle(provider_a, weight=1.0, role="reasoning")
    pb = FusionParticle(provider_b, weight=1.2, role="analysis")
    pc = FusionParticle(provider_c, weight=0.8, role="creative")

    stack = FusionStack()
    stack.add_particle(pa)
    stack.add_particle(pb)
    stack.add_particle(pc)
    stack.set_mode("sequential")

    fusion_result = stack.execute("MRL convergence runtime check")

    loop = MobiusLoop(stack)
    loop_result = loop.run(
        "MRL MobiusLoop convergence verification",
        convergence_threshold=0.9,
        max_cycles=5,
    )

    return {
        "fusion_result": fusion_result,
        "mobius_loop": loop_result,
        "particles": [p.to_dict() for p in [pa, pb, pc]],
    }


def run_memory():
    mem = FlowMemoryCore()
    mem.commit(
        "MRL Layer A ACTIVE_CPP_V1 initialized",
        MemoryType.SEMANTIC,
        tags=["layer_a", "runtime"],
    )
    mem.commit(
        "DL580 canonical runtime boot sequence",
        MemoryType.EPISODIC,
        tags=["dl580", "boot"],
    )
    mem.commit(
        "PersistentLoop ORCHESTRATION_COLLECTOR started",
        MemoryType.PROCEDURAL,
        tags=["persistent_loop", "orchestration"],
    )
    mem.commit(
        "BaseWorld runtime_state_ledger online",
        MemoryType.SEMANTIC,
        tags=["baseworld", "ledger"],
    )
    mem.commit(
        "EntryGateway external_read_interface ready",
        MemoryType.SEMANTIC,
        tags=["entry_gateway", "interface"],
    )
    return {"memory_status": mem.get_status()}


def main():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[MRL Runtime] Generating snapshot at {ts}")

    snapshot = {
        "generated_at": ts,
        "source": "mrl_runtime_snapshot.py",
        "canonical_runtime": "DL580",
        "layer_a": "ACTIVE_CPP_V1",
    }

    print("[MRL Runtime] Running particle registry...")
    snapshot["particle_registry"] = run_particle_registry()

    print("[MRL Runtime] Running fusion engine...")
    snapshot["fusion_engine"] = run_fusion_engine()

    print("[MRL Runtime] Running AI stack runtime...")
    snapshot["ai_stack_runtime"] = run_ai_stack_runtime()

    print("[MRL Runtime] Running convergence (MobiusLoop)...")
    snapshot["convergence"] = run_convergence()

    print("[MRL Runtime] Running memory system...")
    snapshot["memory"] = run_memory()

    with open(OUTPUT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    print(f"[MRL Runtime] Snapshot written to {OUTPUT_PATH}")
    print(f"[MRL Runtime] Keys: {list(snapshot.keys())}")


if __name__ == "__main__":
    main()
