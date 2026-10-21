"""
Self-Modification System - AI evolves its own code
自我修改系統 - AI 演化自己的代碼

This module provides the infrastructure for AI-driven code evolution
and self-optimization.
"""

from .code_evolver import CodeEvolver
from .ai_optimizer import AIPerformanceOptimizer
from .performance_analyzer import PerformanceAnalyzer

__all__ = [
    'CodeEvolver',
    'AIPerformanceOptimizer',
    'PerformanceAnalyzer',
]

__version__ = '1.0.0'
