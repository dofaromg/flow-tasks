"""
Tests for Ultimate AI Video System
小影AI終極版測試
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_import_modules():
    """測試模組導入"""
    try:
        from utils.gpu_orchestrator import GPUOrchestrator, get_orchestrator
        from utils.memory_manager import MemoryManager, get_memory_manager
        from utils.model_cache import ModelCache, get_model_cache
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import modules: {e}")


def test_gpu_orchestrator_init():
    """測試GPU編排器初始化"""
    from utils.gpu_orchestrator import GPUOrchestrator
    
    try:
        orchestrator = GPUOrchestrator()
        assert orchestrator is not None
        assert orchestrator.num_gpus >= 0  # 0 if no GPU available
    except Exception as e:
        # 沒有GPU環境時跳過
        pytest.skip(f"No GPU environment: {e}")


def test_memory_manager_init():
    """測試記憶體管理器初始化"""
    from utils.memory_manager import MemoryManager
    
    manager = MemoryManager()
    assert manager is not None
    assert manager.total_memory_gb > 0
    
    # 測試記憶體統計
    stats = manager.get_memory_stats()
    assert stats.total > 0
    assert stats.available >= 0
    assert 0 <= stats.percent <= 100


def test_model_cache_init():
    """測試模型緩存初始化"""
    from utils.model_cache import ModelCache
    
    cache = ModelCache()
    assert cache is not None
    
    # 測試緩存統計
    stats = cache.get_cache_stats()
    assert 'total_models' in stats
    assert 'total_memory_gb' in stats
    assert stats['total_models'] >= 0


def test_digital_human_config():
    """測試數字人配置"""
    from ultimate_engines.digital_human_ultra import DigitalHumanConfig
    
    config = DigitalHumanConfig(
        resolution="4k",
        fps=60,
        quality="balanced"
    )
    
    assert config.resolution == "4k"
    assert config.fps == 60
    assert config.quality == "balanced"
    assert config.enable_blink == True


def test_voice_clone_config():
    """測試聲音克隆配置"""
    from ultimate_engines.voice_clone_unlimited import VoiceCloneConfig
    
    config = VoiceCloneConfig(
        model="f5_tts_v2",
        language="zh",
        emotion="neutral"
    )
    
    assert config.model == "f5_tts_v2"
    assert config.language == "zh"
    assert config.emotion == "neutral"


def test_configs_exist():
    """測試配置文件存在"""
    config_dir = Path(__file__).parent.parent / "configs"
    
    assert (config_dir / "gpu_allocation.yaml").exists()
    assert (config_dir / "model_config.yaml").exists()
    assert (config_dir / "family_users.yaml").exists()


def test_web_files_exist():
    """測試Web文件存在"""
    web_dir = Path(__file__).parent.parent / "web_ultimate"
    
    assert (web_dir / "index.html").exists()
    assert (web_dir / "css" / "style.css").exists()
    assert (web_dir / "js" / "app.js").exists()


def test_main_service_exists():
    """測試主服務文件存在"""
    main_file = Path(__file__).parent.parent / "main_ultimate.py"
    assert main_file.exists()


def test_deployment_script_exists():
    """測試部署腳本存在"""
    script_file = Path(__file__).parent.parent / "scripts" / "deploy_ultimate.sh"
    assert script_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
