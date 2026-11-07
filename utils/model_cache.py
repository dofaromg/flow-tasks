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
from MRL_Products.MRL_APIWorks_BYOH_Deployment_Product_v1.scripts import (
    MRL_hardware_admission_v1 as admission,
)

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
        self.lock = threading.RLock()
        self._admitted_provenance = {}
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
            self._admitted_provenance.pop(model_name, None)
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

    def _model_identity(self, model_name, workload):
        model = workload['model']
        components = model.get('components', [])
        if (not isinstance(components, list)
                or any(not isinstance(name, str) or not name for name in components)):
            raise admission.AdmissionError('model components must be explicit cache names')
        if model_name != model['id'] and model_name not in components:
            raise admission.AdmissionError('cache model name is not bound to the workload')

    def load_admitted_model(self, model_name, loader, *, host, workload,
                            artifact_root, artifact_paths, memory_size_gb=0):
        """Register a model only from verified, path-free snapshot streams.

        Trusted loaders accept a read-only mapping of shard names to seekable
        streams ('.' for a single file). They must not reopen original paths,
        download weights, run remote code, or substitute a different model.
        """
        with self.lock:
            self._model_identity(model_name, workload)
            result = admission.require_admission(host, workload, artifact_root, artifact_paths)
            with admission.verified_model_streams(workload, artifact_root, artifact_paths) as streams:
                model = loader(streams)
                if model is None:
                    raise admission.AdmissionError('admitted model loader returned no model')
            # Recheck release policy and all artifacts after the loader returns.
            after = admission.require_admission(host, workload, artifact_root, artifact_paths)
            if after['configuration_digest'] != result['configuration_digest']:
                raise admission.AdmissionError('configuration changed while loading model')
            self.register_model(model_name, model, {}, memory_size_gb)
            self._admitted_provenance[model_name] = (model, result['configuration_digest'])
            return model

    def get_admitted_model(self, model_name, *, host, workload, artifact_root, artifact_paths):
        """Fail closed for legacy/unbound cache objects; no placeholder fallback."""
        with self.lock:
            self._model_identity(model_name, workload)
            result = admission.require_admission(host, workload, artifact_root, artifact_paths)
            model = self.models.get(model_name)
            prior = self._admitted_provenance.get(model_name)
            if (model is None or prior is None or prior[0] is not model
                    or prior[1] != result['configuration_digest']):
                raise admission.AdmissionError('cached model has no matching controlled-load provenance')
            self.models.move_to_end(model_name)
            return model
    
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
                self._admitted_provenance.pop(model_name, None)
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
