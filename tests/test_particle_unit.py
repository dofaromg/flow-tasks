#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
粒子執行單元測試 / Particle Execution Unit Tests

此測試模組測試粒子執行單元的初始化與基本功能。
This test module tests the initialization and basic functionality of particle execution units.
"""

import pytest
import sys
import os
from typing import Dict, Any

# 添加專案根目錄到路徑 / Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 導入核心模組 / Import core modules
from core.memory_system import FlowMemoryCore, MemoryType, MemoryEntry
from core.particle_dict import ParticleDictionary, Particle, ParticleChain


class TestParticleExecutionUnit:
    """
    粒子執行單元測試類別 / Particle Execution Unit Test Class
    
    測試粒子執行單元的初始化、執行與狀態管理。
    Tests initialization, execution, and state management of particle execution units.
    """
    
    def setup_method(self):
        """
        測試設置 - 在每個測試方法前執行
        Test setup - runs before each test method
        """
        self.memory_core = FlowMemoryCore()
        self.particle_dict = ParticleDictionary()
    
    def teardown_method(self):
        """
        測試清理 - 在每個測試方法後執行
        Test cleanup - runs after each test method
        """
        self.memory_core = None
        self.particle_dict = None
    
    @pytest.mark.unit
    @pytest.mark.particle
    def test_particle_unit_initialization(self):
        """
        測試 1: 粒子執行單元初始化
        Test 1: Particle execution unit initialization
        
        驗證粒子字典與記憶系統能正確初始化。
        Verifies that particle dictionary and memory system initialize correctly.
        """
        # 驗證記憶核心初始化 / Verify memory core initialization
        assert self.memory_core is not None, "記憶核心應成功初始化"
        assert isinstance(self.memory_core, FlowMemoryCore), "應為 FlowMemoryCore 實例"
        assert len(self.memory_core.long_term_memory) == 0, "長期記憶應為空"
        assert len(self.memory_core.short_term_memory) == 0, "短期記憶應為空"
        assert len(self.memory_core.working_memory) == 0, "工作記憶應為空"
        
        # 驗證粒子字典初始化 / Verify particle dictionary initialization
        assert self.particle_dict is not None, "粒子字典應成功初始化"
        assert isinstance(self.particle_dict, ParticleDictionary), "應為 ParticleDictionary 實例"
        
        print("✓ 粒子執行單元初始化測試通過")
    
    @pytest.mark.unit
    @pytest.mark.particle
    def test_particle_registration(self):
        """
        測試 2: 粒子註冊功能
        Test 2: Particle registration functionality
        
        驗證能正確註冊和檢索粒子。
        Verifies correct particle registration and retrieval.
        """
        # 註冊新粒子 / Register new particle
        test_particle = Particle(
            fx_code="FX.TEST.001",
            human_view="測試粒子",
            description="用於單元測試的粒子"
        )
        
        self.particle_dict.add_particle(test_particle)
        
        # 檢索粒子 / Retrieve particle
        retrieved = self.particle_dict.get_particle("FX.TEST.001")
        
        assert retrieved is not None, "應能檢索到已註冊的粒子"
        assert retrieved.fx_code == "FX.TEST.001", "粒子代碼應匹配"
        assert retrieved.human_view == "測試粒子", "粒子名稱應匹配"
        assert retrieved.description == "用於單元測試的粒子", "粒子描述應匹配"
        
        print("✓ 粒子註冊功能測試通過")
    
    @pytest.mark.unit
    @pytest.mark.memory
    def test_memory_commit(self):
        """
        測試 3: 記憶提交功能
        Test 3: Memory commit functionality
        
        驗證能正確提交記憶到記憶系統。
        Verifies correct memory commit to memory system.
        """
        # 提交語義記憶 / Commit semantic memory
        result = self.memory_core.commit(
            content="粒子語言是創新的邏輯執行框架",
            memory_type=MemoryType.SEMANTIC,
            tags=["粒子語言", "定義"]
        )
        
        assert result is not None, "記憶提交應返回結果"
        assert len(self.memory_core.long_term_memory) > 0, "長期記憶應包含新記憶"
        
        # 檢索記憶 / Retrieve memory (using query string)
        memories = self.memory_core.recall(query="粒子語言")
        assert len(memories) > 0, "應能檢索到相關記憶"
        assert "粒子語言是創新的邏輯執行框架" in memories[0].content, "記憶內容應匹配"
        
        print("✓ 記憶提交功能測試通過")
    
    @pytest.mark.unit
    @pytest.mark.particle
    def test_particle_chain_creation(self):
        """
        測試 4: 粒子鏈創建
        Test 4: Particle chain creation
        
        驗證能正確創建和管理粒子鏈。
        Verifies correct creation and management of particle chains.
        """
        # 創建粒子鏈 / Create particle chain
        particles = [
            Particle("FX.01", "記住", "記憶功能"),
            Particle("FX.02", "分析", "分析功能"),
            Particle("FX.03", "回憶", "回憶功能")
        ]
        
        chain = ParticleChain(
            name="基本記憶鏈",
            particles=particles
        )
        
        assert chain is not None, "粒子鏈應成功創建"
        assert chain.name == "基本記憶鏈", "粒子鏈名稱應匹配"
        assert len(chain.particles) == 3, "粒子鏈應包含 3 個粒子"
        assert chain.particles[0].fx_code == "FX.01", "第一個粒子應為 FX.01"
        
        print("✓ 粒子鏈創建測試通過")
    
    @pytest.mark.unit
    @pytest.mark.core
    def test_particle_execution_lifecycle(self):
        """
        測試 5: 粒子執行生命週期
        Test 5: Particle execution lifecycle
        
        驗證粒子執行的完整生命週期：初始化 -> 執行 -> 存儲。
        Verifies complete particle execution lifecycle: init -> execute -> store.
        """
        # 階段 1: 初始化 / Phase 1: Initialization
        particle = self.particle_dict.get_particle("FX.01")  # 記住
        assert particle is not None, "應能取得預設粒子"
        
        # 階段 2: 模擬執行 / Phase 2: Simulate execution
        execution_data = {
            "particle": particle.fx_code,
            "action": particle.human_view,
            "input": "測試資料",
            "timestamp": "2026-02-05"
        }
        
        # 階段 3: 存儲結果 / Phase 3: Store result
        self.memory_core.commit(
            content=f"執行粒子: {particle.human_view}",
            memory_type=MemoryType.PROCEDURAL,
            tags=["執行記錄", particle.fx_code]
        )
        
        # 驗證 / Verify (using query string)
        memories = self.memory_core.recall(query="執行粒子")
        assert len(memories) > 0, "應記錄執行歷史"
        assert particle.human_view in memories[0].content, "記憶內容應包含粒子名稱"
        
        print("✓ 粒子執行生命週期測試通過")
    
    @pytest.mark.unit
    @pytest.mark.memory
    def test_memory_types(self):
        """
        測試 6: 多種記憶類型
        Test 6: Multiple memory types
        
        驗證支援所有記憶類型（語義、情節、程序、工作）。
        Verifies support for all memory types (semantic, episodic, procedural, working).
        """
        # 測試所有記憶類型 / Test all memory types
        memory_tests = [
            (MemoryType.SEMANTIC, "知識：粒子是最小執行單元"),
            (MemoryType.EPISODIC, "事件：2026-02-05 完成測試"),
            (MemoryType.PROCEDURAL, "流程：STRUCTURE -> MARK -> FLOW"),
            (MemoryType.WORKING, "暫存：當前測試執行中")
        ]
        
        for memory_type, content in memory_tests:
            result = self.memory_core.commit(
                content=content,
                memory_type=memory_type,
                tags=["測試", memory_type.value]
            )
            assert result is not None, f"{memory_type.value} 記憶應成功提交"
        
        # 驗證不同記憶類型的存儲 / Verify storage of different memory types
        total_memories = (
            len(self.memory_core.long_term_memory) +
            len(self.memory_core.short_term_memory) +
            len(self.memory_core.working_memory)
        )
        assert total_memories >= 4, "應至少有 4 條記憶"
        
        print("✓ 多種記憶類型測試通過")


class TestParticleIntegration:
    """
    粒子整合測試類別 / Particle Integration Test Class
    
    測試粒子系統與記憶系統的整合。
    Tests integration between particle system and memory system.
    """
    
    @pytest.mark.integration
    @pytest.mark.particle
    @pytest.mark.memory
    def test_particle_memory_integration(self):
        """
        測試 7: 粒子與記憶系統整合
        Test 7: Particle and memory system integration
        
        驗證粒子執行結果能正確保存到記憶系統。
        Verifies particle execution results are correctly saved to memory system.
        """
        memory = FlowMemoryCore()
        particles = ParticleDictionary()
        
        # 執行粒子並記錄 / Execute particle and record
        particle = particles.get_particle("FX.01")
        
        memory.commit(
            content=f"粒子 {particle.human_view} 執行成功",
            memory_type=MemoryType.PROCEDURAL,
            tags=["執行", particle.fx_code]
        )
        
        # 驗證整合 / Verify integration (using query string)
        recalled = memory.recall(query=particle.human_view)
        assert len(recalled) > 0, "應能從記憶中檢索粒子執行記錄"
        assert particle.human_view in recalled[0].content, "記憶應包含粒子資訊"
        
        print("✓ 粒子與記憶系統整合測試通過")


# 測試運行入口 / Test entry point
if __name__ == "__main__":
    print("=" * 60)
    print("FlowAgent 粒子執行單元測試 / Particle Execution Unit Tests")
    print("=" * 60)
    
    # 運行測試 / Run tests
    pytest.main([
        __file__,
        "-v",                    # 詳細輸出 / Verbose output
        "-s",                    # 顯示 print 輸出 / Show print output
        "--tb=short",            # 簡短的錯誤追蹤 / Short traceback
        "-m", "unit or integration"  # 運行單元與整合測試 / Run unit and integration tests
    ])
