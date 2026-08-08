# origin_signature: MrLiouWord
# AI Fusion Core — Multi-provider particle fusion stack
# Four modes: Sequential / Parallel / Weighted / Möbius Loop

import hashlib, json, time
from datetime import datetime, timezone

ORIGIN = "MrLiouWord"

class BaseAIProvider:
    def __init__(self, name, config=None):
        self.name = name
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
    def call(self, prompt, **kwargs):
        return {"provider": self.name, "response": f"[{self.name}] {prompt[:100]}", "origin_signature": ORIGIN}

class AIParticle:
    def __init__(self, content, provider=None):
        self.id = f"fp.{hashlib.md5(str(content).encode()).hexdigest()[:8]}"
        self.content = content
        self.provider = provider or "local"
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.origin_signature = ORIGIN
    def to_dict(self):
        return {"id": self.id, "content": self.content, "provider": self.provider,
                "timestamp": self.timestamp, "origin_signature": self.origin_signature}

class FusionStack:
    def __init__(self, providers=None):
        self.providers = providers or [BaseAIProvider("local")]
        self.history = []
    def sequential(self, prompt):
        results = []
        current = prompt
        for p in self.providers:
            if p.enabled:
                r = p.call(current)
                results.append(r)
                current = r.get("response", current)
        self.history.append({"mode": "sequential", "steps": len(results)})
        return {"mode": "sequential", "results": results, "final": current, "origin_signature": ORIGIN}
    def parallel(self, prompt):
        results = [p.call(prompt) for p in self.providers if p.enabled]
        self.history.append({"mode": "parallel", "count": len(results)})
        return {"mode": "parallel", "results": results, "origin_signature": ORIGIN}
    def weighted(self, prompt, weights=None):
        results = []
        for i, p in enumerate(self.providers):
            if p.enabled:
                r = p.call(prompt)
                w = (weights or [1.0] * len(self.providers))[i] if weights and i < len(weights) else 1.0
                r["weight"] = w
                results.append(r)
        self.history.append({"mode": "weighted", "count": len(results)})
        return {"mode": "weighted", "results": results, "origin_signature": ORIGIN}

class MobiusLoop:
    def __init__(self, stack, max_iterations=5, convergence_threshold=0.9):
        self.stack = stack
        self.max_iterations = max_iterations
        self.threshold = convergence_threshold
    def run(self, prompt):
        current = prompt
        iterations = []
        for i in range(self.max_iterations):
            result = self.stack.sequential(current)
            iterations.append({"iteration": i + 1, "output_len": len(str(result.get("final", "")))})
            new = result.get("final", current)
            if new == current:
                break
            current = new
        return {"mode": "mobius", "iterations": iterations, "final": current,
                "converged": len(iterations) < self.max_iterations, "origin_signature": ORIGIN}
