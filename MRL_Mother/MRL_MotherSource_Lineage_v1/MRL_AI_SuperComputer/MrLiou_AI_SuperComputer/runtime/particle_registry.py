"""
Particle Registry - Registry for managing AI particles
粒子註冊表 - 管理 AI 粒子的註冊表

Centralized registry for all AI particles in the runtime.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class ParticleRegistry:
    """
    Registry for managing AI particles
    管理 AI 粒子的註冊表
    
    Keeps track of all particles in the system and provides
    lookup, search, and management capabilities.
    """
    
    def __init__(self):
        """Initialize Particle Registry"""
        self._particles: Dict[str, Any] = {}
        self._tags: Dict[str, List[str]] = {}
        self._creation_order: List[str] = []
        
    def register(self, particle: Any, tags: Optional[List[str]] = None) -> None:
        """
        Register a particle in the registry
        在註冊表中註冊粒子
        
        Args:
            particle: AI particle to register
            tags: Optional tags for categorization
        """
        particle_id = particle.particle_id
        
        if particle_id in self._particles:
            raise ValueError(f"Particle {particle_id} already registered")
        
        self._particles[particle_id] = particle
        self._creation_order.append(particle_id)
        
        # Register tags
        if tags:
            for tag in tags:
                if tag not in self._tags:
                    self._tags[tag] = []
                self._tags[tag].append(particle_id)
    
    def get(self, particle_id: str) -> Optional[Any]:
        """
        Get a particle by ID
        根據 ID 獲取粒子
        
        Args:
            particle_id: ID of the particle
            
        Returns:
            Particle or None if not found
        """
        return self._particles.get(particle_id)
    
    def unregister(self, particle_id: str) -> bool:
        """
        Remove a particle from the registry
        從註冊表中移除粒子
        
        Args:
            particle_id: ID of particle to remove
            
        Returns:
            True if removed, False if not found
        """
        if particle_id not in self._particles:
            return False
        
        del self._particles[particle_id]
        self._creation_order.remove(particle_id)
        
        # Remove from tags
        for tag_list in self._tags.values():
            if particle_id in tag_list:
                tag_list.remove(particle_id)
        
        return True
    
    def find_by_tag(self, tag: str) -> List[Any]:
        """
        Find all particles with a specific tag
        查找具有特定標籤的所有粒子
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of particles with that tag
        """
        particle_ids = self._tags.get(tag, [])
        return [self._particles[pid] for pid in particle_ids if pid in self._particles]
    
    def find_by_provider(self, provider: str) -> List[Any]:
        """
        Find all particles using a specific AI provider
        查找使用特定 AI 提供者的所有粒子
        
        Args:
            provider: AI provider name (openai, claude, gemini)
            
        Returns:
            List of particles using that provider
        """
        return [
            particle for particle in self._particles.values()
            if hasattr(particle, 'provider') and particle.provider == provider
        ]
    
    def list_all(self) -> List[Any]:
        """
        Get all registered particles in creation order
        按創建順序獲取所有註冊的粒子
        
        Returns:
            List of all particles
        """
        return [self._particles[pid] for pid in self._creation_order]
    
    def count(self) -> int:
        """Get total number of registered particles"""
        return len(self._particles)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about registered particles
        獲取註冊粒子的統計信息
        
        Returns:
            Dictionary with stats
        """
        provider_counts = {}
        for particle in self._particles.values():
            if hasattr(particle, 'provider'):
                provider = particle.provider
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        return {
            "total_particles": len(self._particles),
            "providers": provider_counts,
            "tags": {tag: len(pids) for tag, pids in self._tags.items()},
            "creation_order_length": len(self._creation_order)
        }
    
    def search(self, query: str) -> List[Any]:
        """
        Search for particles by ID substring
        通過 ID 子字符串搜索粒子
        
        Args:
            query: Search query
            
        Returns:
            List of matching particles
        """
        query_lower = query.lower()
        return [
            particle for pid, particle in self._particles.items()
            if query_lower in pid.lower()
        ]
    
    def clear(self) -> None:
        """Clear all particles from registry (use with caution!)"""
        self._particles.clear()
        self._tags.clear()
        self._creation_order.clear()
    
    def __len__(self) -> int:
        """Get number of registered particles"""
        return len(self._particles)
    
    def __contains__(self, particle_id: str) -> bool:
        """Check if a particle ID is registered"""
        return particle_id in self._particles
    
    def __repr__(self) -> str:
        return f"ParticleRegistry(particles={len(self._particles)}, tags={len(self._tags)})"
