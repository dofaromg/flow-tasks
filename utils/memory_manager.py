"""
Memory Manager - 3TB記憶體管理系統
Memory management system for 3TB RAM
"""

import psutil
import logging
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """記憶體統計信息"""
    total: float  # GB
    available: float  # GB
    used: float  # GB
    percent: float  # 0-100
    cached: float  # GB
    buffers: float  # GB


class MemoryManager:
    """記憶體管理器 - 智能管理3TB RAM"""
    
    def __init__(self, config_path: str = "configs/model_config.yaml"):
        """
        初始化記憶體管理器
        
        Args:
            config_path: 模型配置文件路徑
        """
        self.config = self._load_config(config_path)
        self.total_memory_gb = psutil.virtual_memory().total / 1024**3
        self.model_memory_usage = {}  # model_name -> memory_gb
        self.lock = threading.Lock()
        
        logger.info(f"Memory Manager initialized with {self.total_memory_gb:.1f} GB total RAM")
        self._log_memory_budget()
    
    def _load_config(self, config_path: str) -> Dict:
        """加載配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            return {}
    
    def _log_memory_budget(self):
        """記錄記憶體預算"""
        budget = self.config.get('memory_budget', {})
        total_required = budget.get('total_required', 120)
        max_allowed = budget.get('max_allowed', 180)
        
        logger.info(f"Memory budget: {total_required} GB required, {max_allowed} GB max")
        
        if self.total_memory_gb < max_allowed:
            logger.warning(
                f"System memory ({self.total_memory_gb:.1f} GB) is less than "
                f"recommended ({max_allowed} GB)"
            )
    
    def get_memory_stats(self) -> MemoryStats:
        """
        獲取當前記憶體統計
        
        Returns:
            MemoryStats對象
        """
        mem = psutil.virtual_memory()
        
        return MemoryStats(
            total=mem.total / 1024**3,
            available=mem.available / 1024**3,
            used=mem.used / 1024**3,
            percent=mem.percent,
            cached=getattr(mem, 'cached', 0) / 1024**3,
            buffers=getattr(mem, 'buffers', 0) / 1024**3
        )
    
    def check_memory_availability(self, required_gb: float) -> bool:
        """
        檢查是否有足夠的記憶體
        
        Args:
            required_gb: 需要的記憶體 (GB)
            
        Returns:
            是否有足夠記憶體
        """
        stats = self.get_memory_stats()
        available = stats.available
        
        # 保留10%的記憶體作為系統緩衝
        buffer = self.total_memory_gb * 0.1
        usable = available - buffer
        
        if usable >= required_gb:
            logger.debug(f"Memory check passed: {usable:.1f} GB available, {required_gb:.1f} GB required")
            return True
        else:
            logger.warning(f"Insufficient memory: {usable:.1f} GB available, {required_gb:.1f} GB required")
            return False
    
    def register_model(self, model_name: str, memory_gb: float):
        """
        註冊模型記憶體使用
        
        Args:
            model_name: 模型名稱
            memory_gb: 記憶體使用量 (GB)
        """
        with self.lock:
            self.model_memory_usage[model_name] = memory_gb
            total_model_memory = sum(self.model_memory_usage.values())
            logger.info(
                f"Model '{model_name}' registered: {memory_gb:.1f} GB "
                f"(Total models: {total_model_memory:.1f} GB)"
            )
    
    def unregister_model(self, model_name: str):
        """
        取消註冊模型
        
        Args:
            model_name: 模型名稱
        """
        with self.lock:
            if model_name in self.model_memory_usage:
                memory_gb = self.model_memory_usage.pop(model_name)
                logger.info(f"Model '{model_name}' unregistered: freed {memory_gb:.1f} GB")
    
    def get_model_memory_usage(self) -> Dict[str, float]:
        """
        獲取所有模型的記憶體使用情況
        
        Returns:
            模型名稱 -> 記憶體使用量 (GB)
        """
        with self.lock:
            return self.model_memory_usage.copy()
    
    def get_total_model_memory(self) -> float:
        """
        獲取所有模型的總記憶體使用
        
        Returns:
            總記憶體使用 (GB)
        """
        with self.lock:
            return sum(self.model_memory_usage.values())
    
    def preload_models_check(self) -> bool:
        """
        檢查是否可以預加載所有模型
        
        Returns:
            是否可以預加載
        """
        # 計算所有需要預加載的模型的記憶體需求
        total_required = 0
        model_categories = [
            'digital_human_models',
            'voice_clone_models',
            'photo_to_video_models',
            'video_enhancement_models',
            'face_swap_models',
            'motion_transfer_models',
            'music_generation_models',
            'smart_editing_models',
            'vfx_models'
        ]
        
        for category in model_categories:
            models = self.config.get(category, {})
            for model_name, model_config in models.items():
                if model_config.get('preload', False):
                    memory_required = model_config.get('memory_required', 0)
                    total_required += memory_required
        
        logger.info(f"Total memory required for preload: {total_required:.1f} GB")
        
        # 檢查是否超過預算
        budget = self.config.get('memory_budget', {})
        max_allowed = budget.get('max_allowed', 180)
        
        if total_required > max_allowed:
            logger.error(
                f"Cannot preload all models: {total_required:.1f} GB required, "
                f"but only {max_allowed:.1f} GB allowed"
            )
            return False
        
        # 檢查系統是否有足夠記憶體
        return self.check_memory_availability(total_required)
    
    def optimize_memory(self):
        """優化記憶體使用"""
        stats = self.get_memory_stats()
        
        # 如果記憶體使用超過80%，觸發優化
        if stats.percent > 80:
            logger.warning(f"High memory usage: {stats.percent:.1f}%")
            
            # 清理Python垃圾回收
            import gc
            gc.collect()
            
            logger.info("Memory optimization triggered")
    
    def get_cache_size(self) -> float:
        """
        獲取可用於緩存的記憶體大小
        
        Returns:
            可用緩存大小 (GB)
        """
        stats = self.get_memory_stats()
        model_memory = self.get_total_model_memory()
        
        # 總記憶體 - 已使用 - 模型記憶體 - 20%緩衝
        cache_size = stats.total - stats.used - model_memory - (stats.total * 0.2)
        return max(0, cache_size)
    
    def monitor_memory(self):
        """監控記憶體使用"""
        stats = self.get_memory_stats()
        model_memory = self.get_total_model_memory()
        
        logger.info(
            f"Memory Status: "
            f"{stats.used:.1f}/{stats.total:.1f} GB used ({stats.percent:.1f}%), "
            f"Models: {model_memory:.1f} GB, "
            f"Available: {stats.available:.1f} GB"
        )
        
        # 檢查警告閾值
        budget = self.config.get('memory_budget', {})
        warning_threshold = budget.get('warning_threshold', 150)
        
        if stats.used > warning_threshold:
            logger.warning(
                f"Memory usage ({stats.used:.1f} GB) exceeds warning threshold ({warning_threshold} GB)"
            )
    
    def estimate_task_memory(self, task_type: str, input_size_mb: float) -> float:
        """
        估算任務所需記憶體
        
        Args:
            task_type: 任務類型
            input_size_mb: 輸入大小 (MB)
            
        Returns:
            估算的記憶體需求 (GB)
        """
        # 基於任務類型的記憶體倍數
        memory_multipliers = {
            'digital_human': 20,  # 20x輸入大小
            'voice_clone': 10,
            'photo_video': 30,
            'video_enhance': 40,
            'face_swap': 15,
            'motion_transfer': 25,
            'virtual_human_3d': 50,
            'music_generation': 15,
            'smart_editing': 20,
            'vfx': 30
        }
        
        multiplier = memory_multipliers.get(task_type, 20)
        estimated = (input_size_mb / 1024) * multiplier
        
        logger.debug(f"Estimated memory for {task_type}: {estimated:.2f} GB")
        return estimated
    
    def can_handle_task(self, task_type: str, input_size_mb: float) -> bool:
        """
        檢查是否可以處理任務
        
        Args:
            task_type: 任務類型
            input_size_mb: 輸入大小 (MB)
            
        Returns:
            是否可以處理
        """
        required_memory = self.estimate_task_memory(task_type, input_size_mb)
        return self.check_memory_availability(required_memory)


# 全局記憶體管理器實例
_memory_manager = None


def get_memory_manager() -> MemoryManager:
    """獲取全局記憶體管理器實例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
