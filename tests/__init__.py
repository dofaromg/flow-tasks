"""
FlowAgent Tests Package

此包包含 FlowAgent 專案的所有測試。
This package contains all tests for the FlowAgent project.

測試結構 / Test Structure:
- test_particle_unit.py: 粒子執行單元測試
- test_integration.py: 集成測試（已在根目錄）
- test_comprehensive.py: 綜合測試（已在根目錄）

使用方式 / Usage:
    pytest tests/                    # 執行所有測試
    pytest tests/test_particle_unit.py  # 執行特定測試
    pytest -v tests/                 # 詳細輸出
"""

__version__ = "1.0.0"
__author__ = "FlowAgent Team"

# 測試配置 / Test Configuration
PYTEST_PLUGINS = []

# 測試標記 / Test Markers
"""
可用的測試標記 / Available test markers:
- unit: 單元測試
- integration: 集成測試
- slow: 慢速測試
- particle: 粒子系統相關測試
- memory: 記憶系統相關測試
- core: 核心模組測試

使用方式 / Usage:
    pytest -m unit        # 只執行單元測試
    pytest -m "not slow"  # 跳過慢速測試
"""
