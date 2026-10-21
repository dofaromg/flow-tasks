"""
AI Fusion Core - Particle-based AI Provider Composition System
粒子語言啟發的 AI 融合引擎

Based on the MRLiou particle system architecture:
- Particles can stack and superpose
- Each particle maintains state
- Fusion follows the logic chain pattern: STRUCTURE → MARK → FLOW → RECURSE → STORE
"""

import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher


class BaseAIProvider:
    """Base class for AI provider implementations"""
    
    def __init__(self, provider_name: str, model: str):
        self.provider_name = provider_name
        self.model = model
    
    def generate(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Generate response from AI provider
        In production, this would call actual API (OpenAI, Claude, Gemini)
        For now, returns simulated response
        """
        # Simulated response for zero external dependencies
        return f"[{self.provider_name}/{self.model}] Response to: {prompt[:50]}..."


class AIParticle:
    """
    Each AI provider as a particle with state
    AI 提供者作為粒子，具有狀態
    """
    
    def __init__(self, provider: BaseAIProvider, weight: float = 1.0, role: str = ""):
        self.provider = provider
        self.weight = weight  # Fusion weight for weighted merge
        self.role = role  # Role in the fusion pipeline
        self.state = {}  # Particle state storage
        self.history = []  # Execution history
    
    def process(self, input_data: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process input and update state
        處理輸入並更新狀態
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Generate response
        output = self.provider.generate(input_data, context)
        
        # Update state
        self.state["last_input"] = input_data
        self.state["last_output"] = output
        self.state["last_timestamp"] = timestamp
        
        # Record in history
        execution_record = {
            "timestamp": timestamp,
            "input": input_data,
            "output": output,
            "provider": self.provider.provider_name,
            "model": self.provider.model,
            "role": self.role
        }
        self.history.append(execution_record)
        
        return execution_record
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize particle to dictionary"""
        return {
            "provider": self.provider.provider_name,
            "model": self.provider.model,
            "weight": self.weight,
            "role": self.role,
            "state": self.state
        }


class FusionStack:
    """
    Stack of AI particles that can superpose
    AI 粒子堆疊，可進行疊加
    
    Supports 4 fusion modes:
    - sequential: Chain outputs (A → B → C)
    - parallel: Process simultaneously and merge
    - recursive: Möbius loop (output becomes input)
    - weighted: Blend responses with weights
    """
    
    def __init__(self, fusion_id: Optional[str] = None):
        self.fusion_id = fusion_id or uuid.uuid4().hex[:8]
        self.particles: List[AIParticle] = []
        self.fusion_mode = "sequential"  # default mode
        self.execution_history = []
    
    def add_particle(self, particle: AIParticle):
        """Add AI particle to stack"""
        self.particles.append(particle)
    
    def set_mode(self, mode: str):
        """Set fusion mode"""
        if mode not in ["sequential", "parallel", "recursive", "weighted"]:
            raise ValueError(f"Invalid fusion mode: {mode}")
        self.fusion_mode = mode
    
    def execute(self, prompt: str, max_cycles: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute fusion based on mode
        根據模式執行融合
        """
        if not self.particles:
            raise RuntimeError("No particles in fusion stack")
        
        if self.fusion_mode == "sequential":
            return self._execute_sequential(prompt)
        elif self.fusion_mode == "parallel":
            return self._execute_parallel(prompt)
        elif self.fusion_mode == "weighted":
            return self._execute_weighted(prompt)
        elif self.fusion_mode == "recursive":
            # Recursive mode handled by MobiusLoop
            raise RuntimeError("Use MobiusLoop for recursive fusion")
        else:
            raise RuntimeError(f"Unknown fusion mode: {self.fusion_mode}")
    
    def _execute_sequential(self, prompt: str) -> Dict[str, Any]:
        """
        Sequential fusion: chain outputs
        順序融合：串聯輸出
        """
        current_input = prompt
        all_outputs = []
        
        for i, particle in enumerate(self.particles):
            result = particle.process(current_input)
            all_outputs.append(result)
            # Output becomes next input
            current_input = result["output"]
        
        return {
            "fusion_id": self.fusion_id,
            "mode": "sequential",
            "prompt": prompt,
            "outputs": all_outputs,
            "final_result": current_input,
            "particle_count": len(self.particles)
        }
    
    def _execute_parallel(self, prompt: str) -> Dict[str, Any]:
        """
        Parallel fusion: all process simultaneously
        並行融合：所有粒子同時處理
        """
        all_outputs = []
        
        for particle in self.particles:
            result = particle.process(prompt)
            all_outputs.append(result)
        
        # Merge outputs
        merged = self.merge_outputs(all_outputs)
        
        return {
            "fusion_id": self.fusion_id,
            "mode": "parallel",
            "prompt": prompt,
            "outputs": all_outputs,
            "final_result": merged,
            "particle_count": len(self.particles)
        }
    
    def _execute_weighted(self, prompt: str) -> Dict[str, Any]:
        """
        Weighted fusion: blend with weights
        加權融合：按權重混合
        """
        all_outputs = []
        
        for particle in self.particles:
            result = particle.process(prompt)
            result["weight"] = particle.weight
            all_outputs.append(result)
        
        # Weighted merge
        merged = self._weighted_merge(all_outputs)
        
        return {
            "fusion_id": self.fusion_id,
            "mode": "weighted",
            "prompt": prompt,
            "outputs": all_outputs,
            "final_result": merged,
            "particle_count": len(self.particles)
        }
    
    def merge_outputs(self, outputs: List[Dict]) -> str:
        """
        Merge multiple AI outputs intelligently
        智能合併多個 AI 輸出
        
        Uses consensus approach: keep common parts, note differences
        """
        if not outputs:
            return ""
        
        if len(outputs) == 1:
            return outputs[0]["output"]
        
        # Simple consensus: concatenate with markers
        merged = "=== Consensus Merge ===\n\n"
        
        for i, output in enumerate(outputs):
            provider = output.get("provider", "Unknown")
            merged += f"[{provider}]: {output['output']}\n\n"
        
        merged += "=== End Merge ==="
        return merged
    
    def _weighted_merge(self, outputs: List[Dict]) -> str:
        """
        Weighted merge based on particle weights
        基於粒子權重的加權合併
        """
        if not outputs:
            return ""
        
        total_weight = sum(o.get("weight", 1.0) for o in outputs)
        
        merged = "=== Weighted Merge ===\n\n"
        
        for output in outputs:
            weight = output.get("weight", 1.0)
            percentage = (weight / total_weight) * 100
            provider = output.get("provider", "Unknown")
            merged += f"[{provider} - {percentage:.1f}%]: {output['output']}\n\n"
        
        merged += "=== End Weighted Merge ==="
        return merged


class MobiusLoop:
    """
    Recursive AI loop that cycles like Möbius strip
    遞歸 AI 循環，如莫比烏斯帶般循環
    
    Output cycles back as input until convergence
    """
    
    def __init__(self, stack: FusionStack):
        self.stack = stack
        self.cycle_history = []
        self.loop_id = uuid.uuid4().hex[:8]
    
    def run(self, 
            initial_prompt: str, 
            convergence_threshold: float = 0.9, 
            max_cycles: int = 10,
            transform_prompt: str = "Improve and expand: {output}") -> Dict[str, Any]:
        """
        Run Möbius loop until:
        - Convergence detected (output similarity > threshold)
        - Max cycles reached
        
        運行莫比烏斯循環直到：
        - 檢測到收斂（輸出相似度 > 閾值）
        - 達到最大循環次數
        """
        cycle = 0
        current_input = initial_prompt
        converged = False
        
        while cycle < max_cycles:
            # Execute fusion stack in sequential mode
            self.stack.set_mode("sequential")
            result = self.stack.execute(current_input)
            
            output = result["final_result"]
            
            # Calculate similarity with previous output
            similarity = 0.0
            if cycle > 0:
                prev_output = self.cycle_history[-1]["output"]
                similarity = self._calculate_similarity(prev_output, output)
            
            # Record cycle
            cycle_record = {
                "cycle": cycle,
                "input": current_input,
                "output": output,
                "similarity": similarity,
                "outputs": result["outputs"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.cycle_history.append(cycle_record)
            
            # Check convergence
            if similarity >= convergence_threshold and cycle > 0:
                converged = True
                break
            
            # Output becomes next input (Möbius twist)
            current_input = transform_prompt.format(output=output)
            cycle += 1
        
        return {
            "loop_id": self.loop_id,
            "initial_prompt": initial_prompt,
            "converged": converged,
            "total_cycles": len(self.cycle_history),
            "convergence_threshold": convergence_threshold,
            "final_output": self.cycle_history[-1]["output"] if self.cycle_history else "",
            "cycle_history": self.cycle_history
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts
        計算兩個文本之間的相似度
        """
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _has_converged(self) -> bool:
        """Check if loop has converged"""
        if len(self.cycle_history) < 2:
            return False
        
        last_similarity = self.cycle_history[-1]["similarity"]
        return last_similarity >= 0.9  # Default threshold


def load_fusion_manifest(manifest_path: str) -> Dict[str, Any]:
    """
    Load fusion configuration from manifest file
    從清單檔案載入融合配置
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_stack_from_manifest(manifest: Dict[str, Any]) -> FusionStack:
    """
    Create FusionStack from manifest configuration
    從清單配置創建 FusionStack
    """
    stack = FusionStack(fusion_id=manifest.get("fusion_name", ""))
    stack.set_mode(manifest.get("fusion_mode", "sequential"))
    
    for particle_config in manifest.get("particles", []):
        provider_name = particle_config.get("provider", "mock")
        model = particle_config.get("model", "default")
        weight = particle_config.get("weight", 1.0)
        role = particle_config.get("role", "")
        
        # Create provider (in production, this would create actual API clients)
        provider = BaseAIProvider(provider_name, model)
        
        # Create particle
        particle = AIParticle(provider, weight=weight, role=role)
        stack.add_particle(particle)
    
    return stack


if __name__ == "__main__":
    # Demo usage
    print("=== AI Fusion Core Demo ===\n")
    
    # Create particles
    openai_provider = BaseAIProvider("openai", "gpt-4")
    claude_provider = BaseAIProvider("claude", "claude-3-opus")
    gemini_provider = BaseAIProvider("gemini", "gemini-pro")
    
    # Sequential fusion demo
    print("1. Sequential Fusion Demo:")
    stack_seq = FusionStack()
    stack_seq.add_particle(AIParticle(openai_provider, role="initial_draft"))
    stack_seq.add_particle(AIParticle(claude_provider, role="critic_refine"))
    stack_seq.add_particle(AIParticle(gemini_provider, role="final_polish"))
    stack_seq.set_mode("sequential")
    
    result_seq = stack_seq.execute("Explain quantum entanglement")
    print(f"Final result: {result_seq['final_result'][:100]}...\n")
    
    # Parallel fusion demo
    print("2. Parallel Fusion Demo:")
    stack_par = FusionStack()
    stack_par.add_particle(AIParticle(openai_provider, weight=0.4))
    stack_par.add_particle(AIParticle(claude_provider, weight=0.4))
    stack_par.add_particle(AIParticle(gemini_provider, weight=0.2))
    stack_par.set_mode("parallel")
    
    result_par = stack_par.execute("Should AI be regulated?")
    print(f"Merged result: {result_par['final_result'][:100]}...\n")
    
    # Möbius loop demo
    print("3. Möbius Loop Demo:")
    stack_mobius = FusionStack()
    stack_mobius.add_particle(AIParticle(openai_provider, role="expander"))
    stack_mobius.add_particle(AIParticle(claude_provider, role="critic"))
    
    mobius = MobiusLoop(stack_mobius)
    result_mobius = mobius.run("Design a sustainable city", max_cycles=3)
    print(f"Converged: {result_mobius['converged']}")
    print(f"Total cycles: {result_mobius['total_cycles']}")
    print(f"Final output: {result_mobius['final_output'][:100]}...\n")
    
    print("=== Demo Complete ===")
