"""
AI Stack Runtime - Runtime where code is AI data stacks
AI 堆疊運行時 - 代碼即 AI 數據堆疊的運行時

This is the execution environment where AI particles compose into
runnable systems.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

# Import from parent directory
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_primitives.base_particle import AIParticle
from .fusion_engine import FusionEngine
from .particle_registry import ParticleRegistry


class AIStack:
    """
    A stack of AI particles that execute sequentially or in parallel
    順序或並行執行的 AI 粒子堆疊
    """
    
    def __init__(self, stack_name: str, particles: List[AIParticle], mode: str = "sequential"):
        """
        Initialize AI Stack
        
        Args:
            stack_name: Name of this stack
            particles: List of AI particles to execute
            mode: Execution mode (sequential, parallel, recursive)
        """
        self.stack_name = stack_name
        self.particles = particles
        self.mode = mode
        self.execution_history = []
        
    def execute(self, input_data: Any) -> Any:
        """
        Execute all particles in the stack
        執行堆疊中的所有粒子
        
        Args:
            input_data: Initial input data
            
        Returns:
            Final output after all particles execute
        """
        current_data = input_data
        
        if self.mode == "sequential":
            for particle in self.particles:
                result = particle.execute(current_data)
                current_data = result["result"]
                self.execution_history.append(result)
        
        elif self.mode == "parallel":
            # All particles execute with same input
            results = [p.execute(input_data) for p in self.particles]
            self.execution_history.extend(results)
            # Combine results (implementation depends on use case)
            current_data = [r["result"] for r in results]
        
        elif self.mode == "recursive":
            # Particles execute in cycles until convergence
            max_cycles = 10
            for cycle in range(max_cycles):
                for particle in self.particles:
                    result = particle.execute(current_data)
                    current_data = result["result"]
                    self.execution_history.append(result)
                
                # Check convergence (simplified)
                if cycle > 0 and current_data == input_data:
                    break
        
        return current_data


class AIStackRuntime:
    """
    Runtime where code is AI data stacks
    代碼即 AI 數據堆疊的運行時
    
    This runtime manages AI particles and their execution.
    Everything is an AI stack - there is no hardcoded logic.
    """
    
    def __init__(self, root_dir: Optional[str] = None):
        """
        Initialize AI Stack Runtime
        
        Args:
            root_dir: Root directory for runtime storage
        """
        self.root_dir = root_dir or os.getcwd()
        self.particle_registry = ParticleRegistry()
        self.fusion_engine = FusionEngine()
        self.live_stacks = {}
        self.memory_dir = os.path.join(self.root_dir, "memory")
        
        # Ensure directories exist
        self._ensure_directories()
        
    def _ensure_directories(self) -> None:
        """Create necessary directories"""
        dirs = [
            os.path.join(self.memory_dir, "generated_code"),
            os.path.join(self.memory_dir, "particle_states"),
            os.path.join(self.memory_dir, "evolution_history"),
            os.path.join(self.memory_dir, "stack_snapshots")
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def register_particle(self, particle: AIParticle) -> None:
        """
        Register AI particle into runtime
        將 AI 粒子註冊到運行時
        
        Args:
            particle: AI particle to register
        """
        self.particle_registry.register(particle)
        
        # Save particle state
        self._save_particle_state(particle)
    
    def register_stack(self, stack: AIStack) -> None:
        """
        Register AI stack for execution
        註冊 AI 堆疊以供執行
        
        Args:
            stack: AI stack to register
        """
        self.live_stacks[stack.stack_name] = stack
        
        # Save stack configuration
        self._save_stack_config(stack)
    
    def execute_stack(self, stack_name: str, input_data: Any) -> Any:
        """
        Execute a stack of AI particles
        執行 AI 粒子堆疊
        
        Args:
            stack_name: Name of the stack to execute
            input_data: Input data for the stack
            
        Returns:
            Result from stack execution
        """
        if stack_name not in self.live_stacks:
            raise ValueError(f"Stack '{stack_name}' not found")
        
        stack = self.live_stacks[stack_name]
        result = stack.execute(input_data)
        
        # Record execution
        self._record_execution(stack_name, input_data, result)
        
        return result
    
    def get_stack(self, stack_name: str) -> Optional[AIStack]:
        """Get a registered stack by name"""
        return self.live_stacks.get(stack_name)
    
    def fuse_particles(
        self,
        particle_ids: List[str],
        fusion_mode: str = "sequential"
    ) -> AIParticle:
        """
        Fuse multiple particles using fusion engine
        使用融合引擎融合多個粒子
        
        Args:
            particle_ids: IDs of particles to fuse
            fusion_mode: How to fuse (sequential, parallel, weighted)
            
        Returns:
            Fused composite particle
        """
        particles = [
            self.particle_registry.get(pid)
            for pid in particle_ids
        ]
        
        return self.fusion_engine.fuse(particles, mode=fusion_mode)
    
    def self_modify(self, optimization_goal: str) -> Dict[str, Any]:
        """
        AI runtime modifies itself
        AI 運行時自我修改
        
        AI analyzes current stack performance and generates
        optimized particle configurations, then swaps particles dynamically.
        
        Args:
            optimization_goal: What to optimize for
            
        Returns:
            Self-modification result
        """
        # Get current metrics
        metrics = self.get_metrics()
        
        # AI would analyze and generate new configurations
        # For now, simulate the process
        modification_plan = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "goal": optimization_goal,
            "current_metrics": metrics,
            "modifications": [
                "Replace slow particles with optimized versions",
                "Adjust fusion modes for better parallelism",
                "Reorder stack execution for efficiency"
            ]
        }
        
        # Save modification history
        self._save_modification(modification_plan)
        
        return modification_plan
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get runtime performance metrics"""
        return {
            "total_particles": self.particle_registry.count(),
            "active_stacks": len(self.live_stacks),
            "total_executions": sum(
                len(stack.execution_history)
                for stack in self.live_stacks.values()
            )
        }
    
    def replace_particles(self, new_code: str) -> None:
        """
        Hot-swap particles with new implementations
        熱插拔粒子，使用新實現
        
        Args:
            new_code: New particle implementation code
        """
        # Save new code
        code_path = os.path.join(
            self.memory_dir,
            "generated_code",
            f"evolved_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.py"
        )
        
        with open(code_path, 'w', encoding='utf-8') as f:
            f.write(new_code)
        
        # In production, would dynamically load and swap particles
        print(f"New particle code saved to: {code_path}")
    
    def _save_particle_state(self, particle: AIParticle) -> None:
        """Save particle state to disk"""
        state_path = os.path.join(
            self.memory_dir,
            "particle_states",
            f"{particle.particle_id}.json"
        )
        
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(particle.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _save_stack_config(self, stack: AIStack) -> None:
        """Save stack configuration"""
        config_path = os.path.join(
            self.memory_dir,
            "stack_snapshots",
            f"{stack.stack_name}.json"
        )
        
        config = {
            "stack_name": stack.stack_name,
            "mode": stack.mode,
            "particle_count": len(stack.particles),
            "particle_ids": [p.particle_id for p in stack.particles]
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _record_execution(self, stack_name: str, input_data: Any, result: Any) -> None:
        """Record stack execution for audit"""
        record_path = os.path.join(
            self.memory_dir,
            "evolution_history",
            f"exec_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        record = {
            "stack_name": stack_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input": str(input_data)[:100],  # Truncate for storage
            "result": str(result)[:100]
        }
        
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
    
    def _save_modification(self, plan: Dict[str, Any]) -> None:
        """Save self-modification plan"""
        plan_path = os.path.join(
            self.memory_dir,
            "evolution_history",
            f"modification_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
