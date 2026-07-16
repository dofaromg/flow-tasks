"""
Model Cache System - 模型快取系統
Intelligent model caching and preloading for zero cold start
"""

import torch
import logging
import yaml
from typing import Dict, Optional, Any, Callable
from pathlib import Path
import threading
import time
from collections import OrderedDict

logger = logging.getLogger(__name__)


class ModelCache:
    """模型緩存系統 - 實現模型常駐記憶體"""
    
    def __init__(self, config_path: str = "configs/model_config.yaml"):
        """
        初始化模型緩存
        
        Args:
            config_path: 模型配置文件路徑
        """
        self.config = self._load_config(config_path)
        self.models = OrderedDict()  # model_name -> model object
        self.model_configs = {}  # model_name -> config
        self.lock = threading.Lock()
        self.preload_enabled = self.config.get('model_storage', {}).get('preload_all', True)
        
        logger.info(f"Model Cache initialized (preload: {self.preload_enabled})")
    
    def _load_config(self, config_path: str) -> Dict:
        """加載配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            return {}
    
    def register_model(
        self,
        model_name: str,
        model: Any,
        config: Dict,
        memory_size_gb: float
    ):
        """
        註冊模型到緩存
        
        Args:
            model_name: 模型名稱
            model: 模型對象
            config: 模型配置
            memory_size_gb: 模型佔用記憶體 (GB)
        """
        with self.lock:
            self.models[model_name] = model
            self.model_configs[model_name] = {
                **config,
                'memory_size': memory_size_gb,
                'load_time': time.time()
            }
            logger.info(f"Model '{model_name}' registered in cache ({memory_size_gb:.1f} GB)")
    
    def get_model(self, model_name: str) -> Optional[Any]:
        """
        從緩存獲取模型
        
        Args:
            model_name: 模型名稱
            
        Returns:
            模型對象，如果不存在返回None
        """
        with self.lock:
            if model_name in self.models:
                # 移到最後表示最近使用
                self.models.move_to_end(model_name)
                logger.debug(f"Model '{model_name}' retrieved from cache")
                return self.models[model_name]
            
            logger.warning(f"Model '{model_name}' not found in cache")
            return None
    
    def has_model(self, model_name: str) -> bool:
        """
        檢查模型是否在緩存中
        
        Args:
            model_name: 模型名稱
            
        Returns:
            是否存在
        """
        return model_name in self.models
    
    def remove_model(self, model_name: str) -> bool:
        """
        從緩存移除模型
        
        Args:
            model_name: 模型名稱
            
        Returns:
            是否成功移除
        """
        with self.lock:
            if model_name in self.models:
                model = self.models.pop(model_name)
                config = self.model_configs.pop(model_name)
                
                # 清理GPU記憶體
                if hasattr(model, 'to'):
                    try:
                        model.to('cpu')
                    except:
                        pass
                
                del model
                torch.cuda.empty_cache()
                
                logger.info(f"Model '{model_name}' removed from cache")
                return True
            
            return False
    
    def get_cache_stats(self) -> Dict:
        """
        獲取緩存統計信息
        
        Returns:
            統計信息字典
        """
        with self.lock:
            total_models = len(self.models)
            total_memory = sum(
                cfg.get('memory_size', 0) 
                for cfg in self.model_configs.values()
            )
            
            return {
                'total_models': total_models,
                'total_memory_gb': total_memory,
                'models': list(self.models.keys())
            }
    
    def clear_cache(self):
        """清空所有緩存"""
        with self.lock:
            model_names = list(self.models.keys())
            for name in model_names:
                self.remove_model(name)
            
            logger.info("Model cache cleared")
    
    def preload_all_models(self, loader_func: Callable[[str, Dict], Any]):
        """
        預加載所有配置的模型
        
        Args:
            loader_func: 模型加載函數 (model_name, config) -> model
        """
        if not self.preload_enabled:
            logger.info("Model preloading is disabled")
            return
        
        logger.info("Starting to preload all models...")
        
        # 收集所有需要預加載的模型
        models_to_load = []
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
                    full_name = f"{category}.{model_name}"
                    models_to_load.append((full_name, model_config))
        
        logger.info(f"Found {len(models_to_load)} models to preload")
        
        # 加載模型
        loaded = 0
        failed = 0
        
        for model_name, config in models_to_load:
            try:
                logger.info(f"Loading model: {model_name}")
                model = loader_func(model_name, config)
                
                if model is not None:
                    memory_size = config.get('memory_required', 0)
                    self.register_model(model_name, model, config, memory_size)
                    loaded += 1
                else:
                    logger.warning(f"Failed to load model: {model_name}")
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Error loading model '{model_name}': {e}")
                failed += 1
        
        logger.info(
            f"Model preloading complete: {loaded} loaded, {failed} failed"
        )
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """
        獲取模型信息
        
        Args:
            model_name: 模型名稱
            
        Returns:
            模型配置信息
        """
        return self.model_configs.get(model_name)
    
    def list_models(self) -> list:
        """
        列出所有緩存的模型
        
        Returns:
            模型名稱列表
        """
        return list(self.models.keys())
    
    def optimize_cache(self, max_memory_gb: Optional[float] = None):
        """
        優化緩存 - 移除最少使用的模型
        
        Args:
            max_memory_gb: 最大記憶體限制 (GB)
        """
        if max_memory_gb is None:
            return
        
        with self.lock:
            total_memory = sum(
                cfg.get('memory_size', 0) 
                for cfg in self.model_configs.values()
            )
            
            if total_memory <= max_memory_gb:
                return
            
            logger.info(f"Optimizing cache: {total_memory:.1f} GB > {max_memory_gb:.1f} GB")
            
            # 移除最少使用的模型直到滿足限制
            while total_memory > max_memory_gb and self.models:
                # OrderedDict的第一個是最舊的
                oldest_name = next(iter(self.models))
                config = self.model_configs[oldest_name]
                memory_size = config.get('memory_size', 0)
                
                self.remove_model(oldest_name)
                total_memory -= memory_size
                
                logger.info(
                    f"Removed '{oldest_name}' ({memory_size:.1f} GB), "
                    f"remaining: {total_memory:.1f} GB"
                )


# 全局模型緩存實例
_model_cache = None


def get_model_cache() -> ModelCache:
    """獲取全局模型緩存實例"""
    global _model_cache
    if _model_cache is None:
        _model_cache = ModelCache()
    return _model_cache


def load_model_lazy(
    model_name: str,
    loader_func: Callable[[], Any],
    memory_size_gb: float = 0
) -> Any:
    """
    懶加載模型 - 如果緩存中沒有則加載
    
    Args:
        model_name: 模型名稱
        loader_func: 模型加載函數
        memory_size_gb: 預估記憶體大小
        
    Returns:
        模型對象
    """
    cache = get_model_cache()
    
    # 先檢查緩存
    model = cache.get_model(model_name)
    if model is not None:
        return model
    
    # 緩存中沒有，加載模型
    logger.info(f"Loading model '{model_name}' on demand")
    model = loader_func()
    
    if model is not None:
        cache.register_model(
            model_name,
            model,
            {'on_demand': True},
            memory_size_gb
        )
    
    return model
