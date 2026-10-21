"""
Base AI Particle - Smallest unit of AI computation
基礎 AI 粒子 - AI 計算的最小單位

Every function, module, and class in the AI SuperComputer is an AI particle.
"""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class AIParticle:
    """
    Base AI particle - smallest unit of AI computation
    基礎 AI 粒子 - AI 計算的最小單位
    
    Philosophy: Everything is an AI particle that can be:
    - Executed (run AI computation)
    - Fused (combined with other particles)
    - Evolved (self-modified through AI)
    - Traced (Merkle chain audit)
    """
    
    def __init__(
        self,
        particle_id: str,
        ai_provider: Optional[str] = None,
        manifest: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an AI particle
        
        Args:
            particle_id: Unique identifier for this particle
            ai_provider: AI provider to use (openai, claude, gemini)
            manifest: Configuration manifest for this particle
        """
        self.particle_id = particle_id
        self.provider = ai_provider or "openai"
        self.manifest = manifest or {}
        self.state = {}
        self.fusion_history = []
        self.creation_time = datetime.utcnow().isoformat() + "Z"
        self.merkle_chain = []
        
    def execute(self, input_data: Any, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute this AI particle
        執行此 AI 粒子
        
        Every execution is an AI call. Results are stacked into history.
        每次執行都是一次 AI 呼叫，結果堆疊到歷史記錄中
        
        Args:
            input_data: Input data for execution
            context: Optional execution context
            
        Returns:
            Execution result with metadata
        """
        execution_id = uuid.uuid4().hex
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Record execution in Merkle chain
        execution_record = {
            "execution_id": execution_id,
            "particle_id": self.particle_id,
            "timestamp": timestamp,
            "input_hash": self._hash_data(input_data),
            "provider": self.provider
        }
        
        # Simulate AI execution (to be replaced with actual AI calls)
        result = self._simulate_execution(input_data, context)
        
        execution_record["output_hash"] = self._hash_data(result)
        execution_record["status"] = "success"
        
        # Add to Merkle chain
        self._add_to_merkle_chain(execution_record)
        
        return {
            "result": result,
            "execution_id": execution_id,
            "merkle_root": self.get_merkle_root(),
            "timestamp": timestamp
        }
    
    def fuse_with(self, other_particle: 'AIParticle', fusion_mode: str = "sequential") -> 'AIParticle':
        """
        Fuse with another AI particle
        與另一個 AI 粒子融合
        
        Creates a composite particle that combines capabilities.
        創建結合兩者能力的複合粒子
        
        Args:
            other_particle: Another AI particle to fuse with
            fusion_mode: How to fuse (sequential, parallel, weighted)
            
        Returns:
            New composite AI particle
        """
        fusion_id = f"fusion_{uuid.uuid4().hex[:8]}"
        composite_id = f"{self.particle_id}⊕{other_particle.particle_id}"
        
        # Create composite particle
        composite = AIParticle(
            particle_id=composite_id,
            ai_provider=self.provider,
            manifest={
                "fusion_mode": fusion_mode,
                "particles": [self.particle_id, other_particle.particle_id],
                "fusion_id": fusion_id
            }
        )
        
        # Record fusion in history
        fusion_record = {
            "fusion_id": fusion_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mode": fusion_mode,
            "particles": [self.particle_id, other_particle.particle_id]
        }
        
        composite.fusion_history.append(fusion_record)
        self.fusion_history.append(fusion_record)
        other_particle.fusion_history.append(fusion_record)
        
        return composite
    
    def to_code(self) -> str:
        """
        Generate executable code from AI particle state
        從 AI 粒子狀態生成可執行代碼
        
        AI generates its own implementation based on particle state.
        AI 根據粒子狀態生成自己的實現
        
        Returns:
            Python code string
        """
        # This would call AI to generate code
        # For now, return a template
        return f"""
# Auto-generated from AI Particle: {self.particle_id}
# Provider: {self.provider}
# Generated: {datetime.utcnow().isoformat()}Z

class GeneratedParticle:
    def __init__(self):
        self.particle_id = "{self.particle_id}"
        self.provider = "{self.provider}"
    
    def execute(self, input_data):
        # AI-generated implementation
        return f"Processed: {{input_data}}"
"""
    
    def get_merkle_root(self) -> str:
        """Get current Merkle root for audit trail"""
        if not self.merkle_chain:
            return "0" * 64
        return self.merkle_chain[-1]["merkle_root"]
    
    def _simulate_execution(self, input_data: Any, context: Optional[Dict]) -> Any:
        """
        Simulate AI execution (to be replaced with actual AI provider calls)
        模擬 AI 執行（將被實際 AI 提供者呼叫取代）
        """
        # This is where actual AI provider integration would happen
        return f"AI_RESULT[{self.particle_id}]({input_data})"
    
    def _hash_data(self, data: Any) -> str:
        """Create SHA-256 hash of data"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _add_to_merkle_chain(self, record: Dict) -> None:
        """Add record to Merkle chain"""
        if not self.merkle_chain:
            prev_root = "0" * 64
        else:
            prev_root = self.merkle_chain[-1]["merkle_root"]
        
        record_hash = self._hash_data(record)
        combined = (prev_root + record_hash).encode()
        new_root = hashlib.sha256(combined).hexdigest()
        
        record["merkle_root"] = new_root
        self.merkle_chain.append(record)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export particle state as dictionary"""
        return {
            "particle_id": self.particle_id,
            "provider": self.provider,
            "manifest": self.manifest,
            "state": self.state,
            "fusion_history": self.fusion_history,
            "creation_time": self.creation_time,
            "merkle_root": self.get_merkle_root(),
            "chain_length": len(self.merkle_chain)
        }
    
    def __repr__(self) -> str:
        return f"AIParticle(id={self.particle_id}, provider={self.provider})"
