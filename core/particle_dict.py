#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Particle Dictionary Module
粒子字典模組 - 用於管理粒子及其模式匹配
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Particle:
    """粒子資料類別"""
    fx_code: str
    human_view: str
    description: str = ""
    
    def __repr__(self):
        return f"Particle({self.fx_code}: {self.human_view})"


@dataclass
class ParticleChain:
    """粒子鏈資料類別"""
    name: str
    particles: List[Particle]
    
    def __repr__(self):
        return f"ParticleChain({self.name}, {len(self.particles)} particles)"


class ParticleDictionary:
    """
    粒子字典 - 管理粒子及其模式匹配
    """
    
    def __init__(self):
        """初始化粒子字典"""
        self._particles: Dict[str, Particle] = {}
        self._patterns: Dict[str, List[str]] = {}
        self._initialize_default_particles()
    
    def _initialize_default_particles(self):
        """初始化預設粒子"""
        # 基本功能粒子
        default_particles = [
            Particle("FX.01", "記住", "記憶功能"),
            Particle("FX.02", "分析", "分析功能"),
            Particle("FX.03", "回憶", "回憶功能"),
            Particle("FX.04", "理解", "理解功能"),
            Particle("FX.05", "創造", "創造功能"),
        ]
        
        for particle in default_particles:
            self._particles[particle.fx_code] = particle
        
        # 建立模式映射
        self._patterns = {
            r"記住|記憶": ["FX.01"],
            r"分析": ["FX.02"],
            r"回憶|回想": ["FX.03"],
            r"理解|明白": ["FX.04"],
            r"創造|生成": ["FX.05"],
        }
    
    def add_particle(self, particle: Particle):
        """新增粒子"""
        self._particles[particle.fx_code] = particle
    
    def get_particle(self, fx_code: str) -> Optional[Particle]:
        """取得粒子"""
        return self._particles.get(fx_code)
    
    def add_pattern(self, pattern: str, fx_codes: List[str]):
        """新增模式映射"""
        self._patterns[pattern] = fx_codes
    
    def get_patterns(self) -> Dict[str, List[str]]:
        """取得所有模式"""
        return self._patterns
