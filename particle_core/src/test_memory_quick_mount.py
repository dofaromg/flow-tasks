#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Quick Mount (MQM) 模組測試
Test suite for Memory Quick Mount module
"""

import unittest
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

from memory_quick_mount import (
    ParticleCompressor,
    AdvancedParticleCompressor,
    MemoryQuickMounter
)


class TestParticleCompressor(unittest.TestCase):
    """測試基礎粒子壓縮器 / Test basic particle compressor"""
    
    def setUp(self):
        self.compressor = ParticleCompressor()
    
    def test_compress_basic(self):
        """測試基礎壓縮 / Test basic compression"""
        data = {
            'time': '2025-12-31',
            'subject': 'Agent',
            'action': 'execute'
        }
        
        compressed = self.compressor.compress(data)
        
        # 驗證壓縮結果包含預期符號
        # Verify compressed result contains expected symbols
        self.assertIn('⏰[2025-12-31]', compressed)
        self.assertIn('👤[Agent]', compressed)
        self.assertIn('⚡[execute]', compressed)
        self.assertIn('→', compressed)
    
    def test_compress_with_custom_keys(self):
        """測試自訂鍵壓縮 / Test compression with custom keys"""
        data = {
            'time': '2025-12-31',
            'custom_key': 'custom_value'
        }
        
        compressed = self.compressor.compress(data)
        
        # 驗證標準鍵和自訂鍵都被壓縮
        # Verify both standard and custom keys are compressed
        self.assertIn('⏰[2025-12-31]', compressed)
        self.assertIn('⊕custom_key:custom_value', compressed)
    
    def test_decompress_basic(self):
        """測試基礎解壓縮 / Test basic decompression"""
        compressed = "⏰[2025-12-31]→👤[Agent]→⚡[execute]"
        
        decompressed = self.compressor.decompress(compressed)
        
        # 驗證解壓縮結果
        # Verify decompressed result
        self.assertEqual(decompressed['time'], '2025-12-31')
        self.assertEqual(decompressed['subject'], 'Agent')
        self.assertEqual(decompressed['action'], 'execute')
    
    def test_compress_decompress_roundtrip(self):
        """測試壓縮解壓縮往返 / Test compress-decompress roundtrip"""
        original = {
            'time': '2025-12-31',
            'subject': 'TestAgent',
            'action': 'process',
            'item': 'task_123'
        }
        
        compressed = self.compressor.compress(original)
        decompressed = self.compressor.decompress(compressed)
        
        # 驗證往返後資料一致
        # Verify data consistency after roundtrip
        self.assertEqual(original, decompressed)
    
    def test_all_encodings(self):
        """測試所有編碼類型 / Test all encoding types"""
        data = {
            'time': 'T',
            'subject': 'S',
            'partner': 'P',
            'action': 'A',
            'item': 'I',
            'location': 'L',
            'state': 'ST',
            'result': 'R'
        }
        
        compressed = self.compressor.compress(data)
        
        # 驗證所有符號都出現
        # Verify all symbols appear
        self.assertIn('⏰', compressed)
        self.assertIn('👤', compressed)
        self.assertIn('🤝', compressed)
        self.assertIn('⚡', compressed)
        self.assertIn('📦', compressed)
        self.assertIn('📍', compressed)
        self.assertIn('🔄', compressed)
        self.assertIn('✅', compressed)


class TestAdvancedParticleCompressor(unittest.TestCase):
    """測試進階粒子壓縮器 / Test advanced particle compressor"""
    
    def setUp(self):
        self.compressor = AdvancedParticleCompressor()
    
    def test_compress_nested_dict(self):
        """測試巢狀字典壓縮 / Test nested dictionary compression"""
        data = {
            'agent': 'FlowAgent',
            'config': {
                'mode': 'production',
                'enabled': True
            }
        }
        
        compressed = self.compressor.compress_nested(data)
        
        # 驗證巢狀結構符號
        # Verify nested structure symbols
        self.assertIn('⊕agent:FlowAgent', compressed)
        self.assertIn('⊕config⟨', compressed)
        self.assertIn('⊕mode:production', compressed)
        self.assertIn('⟩', compressed)
    
    def test_compress_nested_list(self):
        """測試巢狀列表壓縮 / Test nested list compression"""
        data = {
            'tasks': ['task1', 'task2', 'task3']
        }
        
        compressed = self.compressor.compress_nested(data)
        
        # 驗證列表項目
        # Verify list items
        self.assertIn('⊕tasks⟨', compressed)
        self.assertIn('⊕[0]:task1', compressed)
        self.assertIn('⊕[1]:task2', compressed)
        self.assertIn('⊕[2]:task3', compressed)
    
    def test_compress_deeply_nested(self):
        """測試深度巢狀壓縮 / Test deeply nested compression"""
        data = {
            'level1': {
                'level2': {
                    'level3': 'deep_value'
                }
            }
        }
        
        compressed = self.compressor.compress_nested(data)
        
        # 驗證多層巢狀
        # Verify multiple nesting levels
        self.assertIn('⊕level1⟨', compressed)
        self.assertIn('⊕level2⟨', compressed)
        self.assertIn('⊕level3:deep_value', compressed)
    
    def test_compress_mixed_structure(self):
        """測試混合結構壓縮 / Test mixed structure compression"""
        data = {
            'tasks': [
                {'id': 'task_1', 'priority': 'high'},
                {'id': 'task_2', 'priority': 'low'}
            ]
        }
        
        compressed = self.compressor.compress_nested(data)
        
        # 驗證混合結構
        # Verify mixed structure
        self.assertIn('⊕tasks⟨', compressed)
        self.assertIn('⊕[0]⟨', compressed)
        self.assertIn('⊕id:task_1', compressed)
        self.assertIn('⊕priority:high', compressed)


class TestMemoryQuickMounter(unittest.TestCase):
    """測試記憶快速掛載器 / Test memory quick mounter"""
    
    def setUp(self):
        """設定測試環境 / Set up test environment"""
        # 創建臨時目錄
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.test_dir) / 'config'
        self.examples_dir = Path(self.test_dir) / 'examples'
        self.context_dir = Path(self.test_dir) / 'context'
        self.snapshot_dir = Path(self.test_dir) / 'snapshots'
        
        self.config_dir.mkdir()
        self.examples_dir.mkdir()
        
        # 創建測試種子檔案
        # Create test seed file
        self.seed_data = {
            'structure': {
                'core_persona': 'TestAgent',
                'semantic_roles': {
                    'tester': 'Test Role'
                }
            },
            'metadata': {
                'version': '1.0.0',
                'created_at': '2025-12-31T00:00:00Z'
            }
        }
        
        self.seed_path = self.examples_dir / 'test_seed.json'
        with open(self.seed_path, 'w', encoding='utf-8') as f:
            json.dump(self.seed_data, f, ensure_ascii=False, indent=2)
        
        # 創建配置檔案
        # Create config file
        self.config_data = {
            'context_dir': str(self.context_dir),
            'snapshot_dir': str(self.snapshot_dir),
            'seeds': [str(self.seed_path)]
        }
        
        self.config_path = self.config_dir / 'test_config.json'
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f)
    
    def tearDown(self):
        """清理測試環境 / Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """測試初始化 / Test initialization"""
        mounter = MemoryQuickMounter(config_path=str(self.config_path))
        
        # 驗證目錄已創建
        # Verify directories are created
        self.assertTrue(mounter.context_dir.exists())
        self.assertTrue(mounter.snapshot_dir.exists())
    
    def test_load_seed_json(self):
        """測試載入 JSON 種子 / Test load JSON seed"""
        mounter = MemoryQuickMounter(config_path=str(self.config_path))
        
        seed_data = mounter.load_seed(str(self.seed_path))
        
        # 驗證種子資料
        # Verify seed data
        self.assertIsNotNone(seed_data)
        self.assertEqual(seed_data['structure']['core_persona'], 'TestAgent')
        self.assertEqual(seed_data['metadata']['version'], '1.0.0')
    
    def test_load_seed_nonexistent(self):
        """測試載入不存在的種子 / Test load nonexistent seed"""
        mounter = MemoryQuickMounter(config_path=str(self.config_path))
        
        seed_data = mounter.load_seed('nonexistent.json')
        
        # 驗證返回 None
        # Verify returns None
        self.assertIsNone(seed_data)
    
    def test_mount(self):
        """測試掛載功能 / Test mount function"""
        mounter = MemoryQuickMounter(config_path=str(self.config_path))
        
        success = mounter.mount()
        
        # 驗證掛載成功
        # Verify mount success
        self.assertTrue(success)
        self.assertEqual(len(mounter.loaded_seeds), 1)
        self.assertIn('core_persona', mounter.mounted_context)
        
        # 驗證上下文檔案已創建
        # Verify context file is created
        context_file = mounter.context_dir / 'mounted_context.json'
        self.assertTrue(context_file.exists())
    
    def test_snapshot(self):
        """測試快照功能 / Test snapshot function"""
        mounter = MemoryQuickMounter(config_path=str(self.config_path))
        mounter.mount()
        
        state = {
            'scene': '測試場景',
            'status': 'running',
            'progress': 0.5
        }
        
        success = mounter.snapshot('TestAgent', state)
        
        # 驗證快照成功
        # Verify snapshot success
        self.assertTrue(success)
        
        # 驗證快照檔案存在
        # Verify snapshot file exists
        snapshots = list(mounter.snapshot_dir.glob('snapshot_TestAgent_*.json'))
        self.assertEqual(len(snapshots), 1)
        
        # 驗證最新快照指標存在
        # Verify latest snapshot pointer exists
        latest_file = mounter.snapshot_dir / 'latest_TestAgent.json'
        self.assertTrue(latest_file.exists())
    
    def test_rehydrate(self):
        """測試重新載入功能 / Test rehydrate function"""
        mounter = MemoryQuickMounter(config_path=str(self.config_path))
        mounter.mount()
        
        # 先創建快照
        # Create snapshot first
        original_state = {
            'scene': '測試場景',
            'status': 'completed',
            'progress': 1.0
        }
        mounter.snapshot('TestAgent', original_state)
        
        # 重新載入
        # Rehydrate
        snapshot_data = mounter.rehydrate('TestAgent')
        
        # 驗證重新載入成功
        # Verify rehydrate success
        self.assertIsNotNone(snapshot_data)
        self.assertEqual(snapshot_data['agent'], 'TestAgent')
        self.assertEqual(snapshot_data['state'], original_state)
    
    def test_rehydrate_nonexistent_agent(self):
        """測試重新載入不存在的代理 / Test rehydrate nonexistent agent"""
        mounter = MemoryQuickMounter(config_path=str(self.config_path))
        
        snapshot_data = mounter.rehydrate('NonExistentAgent')
        
        # 驗證返回 None
        # Verify returns None
        self.assertIsNone(snapshot_data)
    
    def test_multiple_snapshots(self):
        """測試多次快照 / Test multiple snapshots"""
        mounter = MemoryQuickMounter(config_path=str(self.config_path))
        mounter.mount()
        
        # 創建多個快照
        # Create multiple snapshots
        for i in range(3):
            state = {'iteration': i, 'progress': i / 3}
            mounter.snapshot('TestAgent', state)
        
        # 驗證所有快照都被創建
        # Verify all snapshots are created
        snapshots = list(mounter.snapshot_dir.glob('snapshot_TestAgent_*.json'))
        self.assertEqual(len(snapshots), 3)
        
        # 驗證最新快照是最後一個
        # Verify latest snapshot is the last one
        snapshot_data = mounter.rehydrate('TestAgent')
        self.assertEqual(snapshot_data['state']['iteration'], 2)
    
    def test_snapshot_with_compression(self):
        """測試快照包含壓縮資料 / Test snapshot includes compressed data"""
        mounter = MemoryQuickMounter(config_path=str(self.config_path))
        mounter.mount()
        
        state = {
            'nested': {
                'data': 'value',
                'list': [1, 2, 3]
            }
        }
        
        mounter.snapshot('TestAgent', state)
        
        # 讀取快照檔案
        # Read snapshot file
        snapshots = list(mounter.snapshot_dir.glob('snapshot_TestAgent_*.json'))
        with open(snapshots[0], 'r', encoding='utf-8') as f:
            snapshot_data = json.load(f)
        
        # 驗證包含壓縮表示
        # Verify includes compressed representation
        self.assertIn('compressed', snapshot_data)
        self.assertIsInstance(snapshot_data['compressed'], str)
        self.assertIn('⊕', snapshot_data['compressed'])


class TestIntegration(unittest.TestCase):
    """整合測試 / Integration tests"""
    
    def setUp(self):
        """設定測試環境 / Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """清理測試環境 / Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_complete_workflow(self):
        """測試完整工作流程 / Test complete workflow"""
        # 設定檔案結構
        # Set up file structure
        config_dir = Path(self.test_dir) / 'config'
        examples_dir = Path(self.test_dir) / 'examples'
        config_dir.mkdir()
        examples_dir.mkdir()
        
        # 創建種子
        # Create seed
        seed_path = examples_dir / 'workflow_seed.json'
        seed_data = {
            'structure': {
                'workflow': 'test_workflow',
                'steps': ['init', 'process', 'finalize']
            },
            'metadata': {'version': '1.0'}
        }
        with open(seed_path, 'w', encoding='utf-8') as f:
            json.dump(seed_data, f)
        
        # 創建配置
        # Create config
        config_path = config_dir / 'workflow_config.json'
        config_data = {
            'context_dir': str(Path(self.test_dir) / 'context'),
            'snapshot_dir': str(Path(self.test_dir) / 'snapshots'),
            'seeds': [str(seed_path)]
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        # 執行完整流程
        # Execute complete workflow
        mounter = MemoryQuickMounter(config_path=str(config_path))
        
        # 1. 掛載
        # 1. Mount
        mount_success = mounter.mount()
        self.assertTrue(mount_success)
        
        # 2. 多步驟快照
        # 2. Multi-step snapshots
        for step in seed_data['structure']['steps']:
            state = {'current_step': step, 'completed': False}
            snapshot_success = mounter.snapshot('WorkflowAgent', state)
            self.assertTrue(snapshot_success)
        
        # 3. 重新載入最新狀態
        # 3. Rehydrate latest state
        final_snapshot = mounter.rehydrate('WorkflowAgent')
        self.assertIsNotNone(final_snapshot)
        self.assertEqual(final_snapshot['state']['current_step'], 'finalize')


def run_tests():
    """執行所有測試 / Run all tests"""
    # 創建測試套件
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加測試類別
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestParticleCompressor))
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedParticleCompressor))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryQuickMounter))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 執行測試
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回結果
    # Return result
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
