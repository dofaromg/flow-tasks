"""
Context Management Module
上下文管理模組

Provides various strategies for managing AI conversation context,
including RAG, summary compression, sliding window, workspace mode, and hybrid approaches.

提供多種 AI 對話上下文管理策略，包括 RAG 檢索、摘要壓縮、
滑動視窗、工作桌面模式和混合策略。
"""

from .base_strategy import BaseStrategy, ContextItem
from .workspace_strategy import WorkspaceStrategy
from .sliding_window_strategy import SlidingWindowStrategy
from .summary_strategy import SummaryStrategy
from .rag_strategy import RAGStrategy
from .hybrid_strategy import HybridStrategy

__all__ = [
    'BaseStrategy',
    'ContextItem',
    'WorkspaceStrategy',
    'SlidingWindowStrategy',
    'SummaryStrategy',
    'RAGStrategy',
    'HybridStrategy',
]

__version__ = '1.0.0'
