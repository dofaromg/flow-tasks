"""
Fusion Engine - Multi-AI particle fusion and composition
融合引擎 - 多 AI 粒子融合與組合

Combines multiple AI particles into composite particles using
different fusion strategies.
"""

import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime


class FusionEngine:
    """
    Engine for fusing multiple AI particles
    融合多個 AI 粒子的引擎
    
    Supports different fusion modes:
    - Sequential: Output of one feeds into next
    - Parallel: All execute simultaneously, results merged
    - Weighted: Results combined with weights
    - Consensus: Multiple AIs vote on best result
    """
    
    def __init__(self):
        """Initialize Fusion Engine"""
        self.fusion_history = []
        
    def fuse(
        self,
        particles: List,
        mode: str = "sequential",
        weights: Optional[List[float]] = None
    ):
        """
        Fuse multiple particles into a composite
        將多個粒子融合成複合粒子
        
        Args:
            particles: List of AIParticle objects to fuse
            mode: Fusion mode (sequential, parallel, weighted, consensus)
            weights: Optional weights for weighted fusion
            
        Returns:
            Composite particle or fused result
        """
        if not particles:
            raise ValueError("Cannot fuse empty particle list")
        
        if len(particles) == 1:
            return particles[0]
        
        fusion_id = f"fusion_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Import here to avoid circular dependency
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from ai_primitives.base_particle import AIParticle
        
        if mode == "sequential":
            return self._fuse_sequential(particles, fusion_id)
        elif mode == "parallel":
            return self._fuse_parallel(particles, fusion_id)
        elif mode == "weighted":
            return self._fuse_weighted(particles, weights or [], fusion_id)
        elif mode == "consensus":
            return self._fuse_consensus(particles, fusion_id)
        else:
            raise ValueError(f"Unknown fusion mode: {mode}")
    
    def _fuse_sequential(self, particles: List, fusion_id: str):
        """
        Sequential fusion - output chains through particles
        順序融合 - 輸出通過粒子鏈式傳遞
        """
        # Start with first particle
        composite = particles[0]
        
        # Fuse each subsequent particle
        for particle in particles[1:]:
            composite = composite.fuse_with(particle, fusion_mode="sequential")
        
        self._record_fusion(fusion_id, "sequential", [p.particle_id for p in particles])
        return composite
    
    def _fuse_parallel(self, particles: List, fusion_id: str):
        """
        Parallel fusion - all particles execute simultaneously
        並行融合 - 所有粒子同時執行
        """
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from ai_primitives.base_particle import AIParticle
        
        # Create composite particle that executes all in parallel
        composite_id = "⊕".join(p.particle_id for p in particles)
        composite = AIParticle(
            particle_id=f"parallel_{composite_id}",
            manifest={
                "fusion_mode": "parallel",
                "particles": [p.particle_id for p in particles],
                "fusion_id": fusion_id
            }
        )
        
        # Store reference to source particles
        composite.state["source_particles"] = particles
        
        self._record_fusion(fusion_id, "parallel", [p.particle_id for p in particles])
        return composite
    
    def _fuse_weighted(self, particles: List, weights: List[float], fusion_id: str):
        """
        Weighted fusion - combine results with weights
        加權融合 - 使用權重組合結果
        """
        if weights and len(weights) != len(particles):
            raise ValueError("Weights must match particle count")
        
        if not weights:
            weights = [1.0 / len(particles)] * len(particles)
        
        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from ai_primitives.base_particle import AIParticle
        
        composite = AIParticle(
            particle_id=f"weighted_{'⊕'.join(p.particle_id for p in particles)}",
            manifest={
                "fusion_mode": "weighted",
                "particles": [p.particle_id for p in particles],
                "weights": normalized_weights,
                "fusion_id": fusion_id
            }
        )
        
        composite.state["source_particles"] = particles
        composite.state["weights"] = normalized_weights
        
        self._record_fusion(
            fusion_id,
            "weighted",
            [p.particle_id for p in particles],
            {"weights": normalized_weights}
        )
        return composite
    
    def _fuse_consensus(self, particles: List, fusion_id: str):
        """
        Consensus fusion - multiple AIs vote on best result
        共識融合 - 多個 AI 對最佳結果投票
        """
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from ai_primitives.base_particle import AIParticle
        
        composite = AIParticle(
            particle_id=f"consensus_{'⊕'.join(p.particle_id for p in particles)}",
            manifest={
                "fusion_mode": "consensus",
                "particles": [p.particle_id for p in particles],
                "fusion_id": fusion_id
            }
        )
        
        composite.state["source_particles"] = particles
        composite.state["consensus_strategy"] = "majority_vote"
        
        self._record_fusion(fusion_id, "consensus", [p.particle_id for p in particles])
        return composite
    
    def _record_fusion(
        self,
        fusion_id: str,
        mode: str,
        particle_ids: List[str],
        metadata: Optional[Dict] = None
    ) -> None:
        """Record fusion event in history"""
        record = {
            "fusion_id": fusion_id,
            "mode": mode,
            "particle_ids": particle_ids,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {}
        }
        self.fusion_history.append(record)
    
    def get_fusion_history(self) -> List[Dict[str, Any]]:
        """Get complete fusion history"""
        return self.fusion_history.copy()
