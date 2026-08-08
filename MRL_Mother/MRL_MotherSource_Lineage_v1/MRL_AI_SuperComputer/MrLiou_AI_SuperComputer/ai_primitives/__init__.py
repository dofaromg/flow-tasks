"""
AI Primitives - Base particle system for AI-native computation
AI 原語 - AI 原生計算的基礎粒子系統

This module provides the foundational AI particles that form the building blocks
of the AI SuperComputer architecture.
"""

from .base_particle import AIParticle
from .function_particle import AIFunctionParticle
from .module_particle import AIModuleParticle
from .class_particle import AIClassParticle

__all__ = [
    'AIParticle',
    'AIFunctionParticle',
    'AIModuleParticle',
    'AIClassParticle',
]

__version__ = '1.0.0'
