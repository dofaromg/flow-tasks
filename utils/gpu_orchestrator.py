"""
GPU Orchestrator - 6卡智能分配系統
Intelligent GPU allocation system for 6x NVIDIA V100 GPUs
"""

import torch
import yaml
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)


@dataclass
class GPUStatus:
    """GPU狀態信息"""
    gpu_id: int
    name: str
    memory_total: float  # GB
    memory_used: float  # GB
    memory_free: float  # GB
    utilization: float  # 0-1
    temperature: float  # Celsius
    processes: List[Dict]


class GPUOrchestrator:
    """GPU編排器 - 智能管理6塊V100顯卡"""
    
    def __init__(self, config_path: str = "configs/gpu_allocation.yaml"):
        """
        初始化GPU編排器
        
        Args:
            config_path: GPU配置文件路徑
        """
        self.config = self._load_config(config_path)
        self.num_gpus = torch.cuda.device_count()
        self.gpu_locks = [threading.Lock() for _ in range(self.num_gpus)]
        self.gpu_assignments = {}  # engine -> gpu_ids mapping
        self._initialize_gpu_assignments()
        
        logger.info(f"GPU Orchestrator initialized with {self.num_gpus} GPUs")
        self._log_gpu_info()
    
    def _load_config(self, config_path: str) -> Dict:
        """加載GPU配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """獲取默認配置"""
        return {
            'gpu_config': {
                'total_gpus': 6,
                'gpu_memory_per_card': 32,
            },
            'allocation_strategy': {
                'digital_human': {'gpu_ids': [0, 1], 'memory_limit': 28},
                'voice_clone': {'gpu_ids': [2], 'memory_limit': 24},
                'photo_video': {'gpu_ids': [3], 'memory_limit': 28},
                'video_enhance': {'gpu_ids': [4], 'memory_limit': 28},
                'auxiliary': {'gpu_ids': [5], 'memory_limit': 24},
            },
            'load_balancing': {
                'enabled': True,
                'check_interval': 5,
                'rebalance_threshold': 0.8,
            }
        }
    
    def _initialize_gpu_assignments(self):
        """初始化GPU分配"""
        strategy = self.config.get('allocation_strategy', {})
        for engine, config in strategy.items():
            self.gpu_assignments[engine] = config.get('gpu_ids', [0])
    
    def _log_gpu_info(self):
        """記錄GPU信息"""
        for i in range(self.num_gpus):
            props = torch.cuda.get_device_properties(i)
            logger.info(f"GPU {i}: {props.name} - {props.total_memory / 1024**3:.1f} GB")
    
    def get_gpu_status(self, gpu_id: int) -> GPUStatus:
        """
        獲取GPU狀態
        
        Args:
            gpu_id: GPU ID
            
        Returns:
            GPUStatus對象
        """
        if not torch.cuda.is_available() or gpu_id >= self.num_gpus:
            raise ValueError(f"Invalid GPU ID: {gpu_id}")
        
        # 獲取GPU屬性
        props = torch.cuda.get_device_properties(gpu_id)
        memory_total = props.total_memory / 1024**3  # Convert to GB
        
        # 獲取記憶體使用情況
        torch.cuda.set_device(gpu_id)
        memory_allocated = torch.cuda.memory_allocated(gpu_id) / 1024**3
        memory_reserved = torch.cuda.memory_reserved(gpu_id) / 1024**3
        memory_free = memory_total - memory_reserved
        
        # 估算使用率 (基於記憶體使用)
        utilization = memory_reserved / memory_total if memory_total > 0 else 0
        
        return GPUStatus(
            gpu_id=gpu_id,
            name=props.name,
            memory_total=memory_total,
            memory_used=memory_reserved,
            memory_free=memory_free,
            utilization=utilization,
            temperature=0.0,  # 需要nvidia-smi來獲取實際溫度
            processes=[]
        )
    
    def allocate_gpu(self, engine_name: str, user_priority: int = 5) -> List[int]:
        """
        為引擎分配GPU
        
        Args:
            engine_name: 引擎名稱
            user_priority: 用戶優先級 (1-10)
            
        Returns:
            分配的GPU ID列表
        """
        # 從配置獲取預設分配
        gpu_ids = self.gpu_assignments.get(engine_name, [0])
        
        # 如果啟用負載均衡，檢查GPU使用情況
        if self.config.get('load_balancing', {}).get('enabled', False):
            gpu_ids = self._balance_load(gpu_ids, engine_name)
        
        logger.info(f"Allocated GPUs {gpu_ids} for engine '{engine_name}' (priority: {user_priority})")
        return gpu_ids
    
    def _balance_load(self, preferred_gpus: List[int], engine_name: str) -> List[int]:
        """
        負載均衡 - 選擇最空閒的GPU
        
        Args:
            preferred_gpus: 首選GPU列表
            engine_name: 引擎名稱
            
        Returns:
            調整後的GPU列表
        """
        threshold = self.config.get('load_balancing', {}).get('rebalance_threshold', 0.8)
        
        # 檢查首選GPU是否過載
        available_gpus = []
        for gpu_id in preferred_gpus:
            try:
                status = self.get_gpu_status(gpu_id)
                if status.utilization < threshold:
                    available_gpus.append(gpu_id)
            except Exception as e:
                logger.warning(f"Failed to check GPU {gpu_id}: {e}")
        
        # 如果首選GPU都可用，直接返回
        if len(available_gpus) == len(preferred_gpus):
            return preferred_gpus
        
        # 否則尋找空閒GPU
        for gpu_id in range(self.num_gpus):
            if gpu_id not in preferred_gpus:
                try:
                    status = self.get_gpu_status(gpu_id)
                    if status.utilization < threshold:
                        available_gpus.append(gpu_id)
                        if len(available_gpus) >= len(preferred_gpus):
                            break
                except Exception:
                    continue
        
        return available_gpus if available_gpus else preferred_gpus
    
    def set_device(self, gpu_ids: List[int]) -> torch.device:
        """
        設置CUDA設備
        
        Args:
            gpu_ids: GPU ID列表
            
        Returns:
            torch.device對象
        """
        if not gpu_ids:
            return torch.device('cpu')
        
        primary_gpu = gpu_ids[0]
        torch.cuda.set_device(primary_gpu)
        return torch.device(f'cuda:{primary_gpu}')
    
    def create_data_parallel(self, model: torch.nn.Module, gpu_ids: List[int]) -> torch.nn.Module:
        """
        創建DataParallel模型用於多GPU
        
        Args:
            model: 原始模型
            gpu_ids: GPU ID列表
            
        Returns:
            並行化後的模型
        """
        if len(gpu_ids) > 1:
            logger.info(f"Creating DataParallel model on GPUs: {gpu_ids}")
            return torch.nn.DataParallel(model, device_ids=gpu_ids)
        return model
    
    def enable_mixed_precision(self) -> bool:
        """
        啟用混合精度訓練
        
        Returns:
            是否成功啟用
        """
        if torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 7:
            logger.info("Mixed precision (FP16) enabled")
            return True
        logger.warning("Mixed precision not available on this GPU")
        return False
    
    def monitor_gpu_health(self):
        """監控GPU健康狀態"""
        health_config = self.config.get('health_monitoring', {})
        if not health_config.get('enabled', True):
            return
        
        temp_warning = health_config.get('temperature_warning', 80)
        temp_critical = health_config.get('temperature_critical', 85)
        memory_warning = health_config.get('memory_warning', 0.9)
        
        for gpu_id in range(self.num_gpus):
            try:
                status = self.get_gpu_status(gpu_id)
                
                # 檢查記憶體使用
                if status.utilization > memory_warning:
                    logger.warning(
                        f"GPU {gpu_id} high memory usage: "
                        f"{status.utilization*100:.1f}% "
                        f"({status.memory_used:.1f}/{status.memory_total:.1f} GB)"
                    )
                
                # 溫度檢查需要nvidia-smi
                # 這裡只是示例結構
                
            except Exception as e:
                logger.error(f"Failed to monitor GPU {gpu_id}: {e}")
    
    def get_available_memory(self, gpu_id: int) -> float:
        """
        獲取GPU可用記憶體
        
        Args:
            gpu_id: GPU ID
            
        Returns:
            可用記憶體 (GB)
        """
        try:
            status = self.get_gpu_status(gpu_id)
            return status.memory_free
        except Exception as e:
            logger.error(f"Failed to get memory for GPU {gpu_id}: {e}")
            return 0.0
    
    def clear_cache(self, gpu_ids: Optional[List[int]] = None):
        """
        清理GPU緩存
        
        Args:
            gpu_ids: 要清理的GPU列表，None表示清理所有
        """
        if gpu_ids is None:
            gpu_ids = list(range(self.num_gpus))
        
        for gpu_id in gpu_ids:
            try:
                torch.cuda.set_device(gpu_id)
                torch.cuda.empty_cache()
                logger.info(f"Cleared cache for GPU {gpu_id}")
            except Exception as e:
                logger.error(f"Failed to clear cache for GPU {gpu_id}: {e}")
    
    def get_optimal_batch_size(self, engine_name: str, base_batch_size: int = 1) -> int:
        """
        根據GPU配置獲取最優批次大小
        
        Args:
            engine_name: 引擎名稱
            base_batch_size: 基礎批次大小
            
        Returns:
            最優批次大小
        """
        strategy = self.config.get('allocation_strategy', {}).get(engine_name, {})
        configured_batch = strategy.get('batch_size', base_batch_size)
        
        # 根據GPU數量調整
        gpu_ids = self.allocate_gpu(engine_name)
        return configured_batch * len(gpu_ids)


# 全局GPU編排器實例
_orchestrator = None


def get_orchestrator() -> GPUOrchestrator:
    """獲取全局GPU編排器實例"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = GPUOrchestrator()
    return _orchestrator
