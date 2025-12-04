#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test cases for Fluin Dict Agent
字典種子記憶快照系統測試
"""

import unittest
import os
import json
import shutil
import tempfile
from fluin_dict_agent import FluinDictAgent


class TestFluinDictAgent(unittest.TestCase):
    """Test cases for FluinDictAgent class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.agent = FluinDictAgent(storage_path=self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    # ========== Version and Core Tests ==========
    
    def test_version_and_core_index(self):
        """Test version and core index constants"""
        self.assertEqual(FluinDictAgent.VERSION, "DictSeed.0003")
        self.assertEqual(FluinDictAgent.CORE_INDEX, 1053)
    
    def test_get_core_info(self):
        """Test get_core_info returns expected structure"""
        info = self.agent.get_core_info()
        
        self.assertEqual(info["version"], "DictSeed.0003")
        self.assertEqual(info["core_index"], 1053)
        self.assertEqual(info["symbol"], "⊕Core → ⟁1053")
        self.assertIn("memory_trace_length", info)
        self.assertIn("echo_count", info)
    
    # ========== Echo/Jump Tests ==========
    
    def test_create_echo(self):
        """Test creating an echo point"""
        result = self.agent.create_echo("test_echo", "Hello World")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["echo_id"], "test_echo")
        self.assertEqual(result["symbol"], "⊕Echo")
    
    def test_trigger_echo(self):
        """Test triggering an echo"""
        self.agent.create_echo("test_echo", "Content")
        result = self.agent.trigger_echo("test_echo")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["content"], "Content")
        self.assertEqual(result["echo_count"], 1)
        
        # Trigger again
        result2 = self.agent.trigger_echo("test_echo")
        self.assertEqual(result2["echo_count"], 2)
    
    def test_trigger_nonexistent_echo(self):
        """Test triggering a non-existent echo"""
        result = self.agent.trigger_echo("nonexistent")
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_set_jump_point(self):
        """Test setting a jump point"""
        result = self.agent.set_jump_point("start", 0)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["jump_id"], "start")
        self.assertEqual(result["position"], 0)
        self.assertEqual(result["symbol"], "▽Jump")
    
    def test_execute_jump(self):
        """Test executing a jump"""
        # Add some trace entries
        self.agent.create_echo("echo1", "First")
        self.agent.set_jump_point("marker", 0)
        self.agent.create_echo("echo2", "Second")
        
        result = self.agent.execute_jump("marker")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["position"], 0)
    
    def test_execute_invalid_jump(self):
        """Test executing a jump to non-existent point"""
        result = self.agent.execute_jump("nonexistent")
        
        self.assertFalse(result["success"])
    
    def test_echo_jump_fusion(self):
        """Test Echo/Jump fusion"""
        self.agent.create_echo("test_echo", "Fusion content")
        self.agent.set_jump_point("test_jump", 0)
        
        result = self.agent.echo_jump_fusion(
            "test_echo", "test_jump", {"fusion_key": "value"}
        )
        
        self.assertTrue(result["success"])
        self.assertIn("fusion", result)
        self.assertEqual(result["fusion"]["symbol"], "⊕Echo/▽Jump→⚙Fusion")
    
    # ========== Memory Trace Tests ==========
    
    def test_memory_trace_records_actions(self):
        """Test that memory trace records actions"""
        initial_length = len(self.agent.get_trace())
        
        self.agent.create_echo("echo1", "Content")
        
        new_length = len(self.agent.get_trace())
        self.assertGreater(new_length, initial_length)
    
    def test_get_trace_with_range(self):
        """Test getting trace with range"""
        self.agent.create_echo("echo1", "A")
        self.agent.create_echo("echo2", "B")
        self.agent.create_echo("echo3", "C")
        
        # Get subset
        trace_subset = self.agent.get_trace(0, 2)
        self.assertEqual(len(trace_subset), 2)
    
    def test_create_memory_loop(self):
        """Test creating a memory loop"""
        result = self.agent.create_memory_loop("loop1")
        
        self.assertTrue(result["success"])
        self.assertIn("loop_marker", result)
        self.assertEqual(result["loop_marker"]["symbol"], "ζMemory^↻Loop")
    
    # ========== Tool/Field Mapping Tests ==========
    
    def test_register_tool(self):
        """Test registering a tool"""
        result = self.agent.register_tool(
            tool_id="parser",
            tool_type="text_processor",
            fields=["input", "output"]
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["tool_id"], "parser")
        self.assertEqual(result["symbol"], "⊕Tool:μField/∴Map")
    
    def test_map_field(self):
        """Test mapping a field value"""
        self.agent.register_tool("tool1", "test", ["field1"])
        result = self.agent.map_field("tool1", "field1", "value1")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["symbol"], "∴Map")
    
    def test_map_field_unregistered_tool(self):
        """Test mapping field for unregistered tool"""
        result = self.agent.map_field("nonexistent", "field", "value")
        
        self.assertFalse(result["success"])
    
    def test_get_field_map(self):
        """Test getting field mappings"""
        self.agent.register_tool("tool1", "test", ["field1", "field2"])
        self.agent.map_field("tool1", "field1", "value1")
        
        result = self.agent.get_field_map("tool1")
        
        self.assertTrue(result["success"])
        self.assertIn("mappings", result)
    
    # ========== Dictionary Seed Tests ==========
    
    def test_create_dict_seed(self):
        """Test creating a dictionary seed"""
        result = self.agent.create_dict_seed(
            seed_id="test_seed",
            data={"key": "value"},
            metadata={"author": "test"}
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["seed_id"], "test_seed")
        self.assertEqual(result["version"], "DictSeed.0003")
        self.assertEqual(result["core_index"], 1053)
        self.assertIn("checksum", result)
    
    def test_restore_dict_seed(self):
        """Test restoring a dictionary seed"""
        test_data = {"key": "value", "number": 42}
        self.agent.create_dict_seed("test_seed", test_data)
        
        result = self.agent.restore_dict_seed("test_seed")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["data"], test_data)
    
    def test_restore_nonexistent_seed(self):
        """Test restoring non-existent seed"""
        result = self.agent.restore_dict_seed("nonexistent")
        
        self.assertFalse(result["success"])
    
    def test_list_seeds(self):
        """Test listing dictionary seeds"""
        self.agent.create_dict_seed("seed1", {"a": 1})
        self.agent.create_dict_seed("seed2", {"b": 2})
        
        seeds = self.agent.list_seeds()
        
        self.assertEqual(len(seeds), 2)
        seed_ids = [s["seed_id"] for s in seeds]
        self.assertIn("seed1", seed_ids)
        self.assertIn("seed2", seed_ids)
    
    def test_seed_file_persistence(self):
        """Test that seeds are persisted to files"""
        self.agent.create_dict_seed("persist_test", {"data": "test"})
        
        seed_file = os.path.join(self.test_dir, "persist_test.dseed.json")
        self.assertTrue(os.path.exists(seed_file))
        
        with open(seed_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["seed_id"], "persist_test")
        self.assertEqual(saved_data["data"]["data"], "test")
    
    # ========== Module Encapsulation Tests ==========
    
    def test_encapsulate_module(self):
        """Test encapsulating a module"""
        result = self.agent.encapsulate_module(
            module_id="test_module",
            module_data={"config": "value"},
            module_type="config"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["module_id"], "test_module")
        self.assertIn("checksum", result)
    
    # ========== Persona Tests ==========
    
    def test_register_persona(self):
        """Test registering a persona"""
        result = self.agent.register_persona(
            persona_id="test_persona",
            name="Test Persona",
            traits=["helpful", "smart"]
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["persona_id"], "test_persona")
        self.assertEqual(result["symbol"], "△Persona")
    
    def test_expand_persona(self):
        """Test expanding a persona"""
        self.agent.register_persona("test_p", "Test", ["trait1"])
        result = self.agent.expand_persona("test_p")
        
        self.assertTrue(result["success"])
        self.assertTrue(result["persona"]["expanded"])
    
    def test_expand_nonexistent_persona(self):
        """Test expanding non-existent persona"""
        result = self.agent.expand_persona("nonexistent")
        
        self.assertFalse(result["success"])
    
    # ========== Memory Trigger Tests ==========
    
    def test_register_trigger(self):
        """Test registering a memory trigger"""
        def test_action(ctx):
            return "triggered"
        
        result = self.agent.register_trigger(
            trigger_id="test_trigger",
            condition="test condition",
            action=test_action
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["trigger_id"], "test_trigger")
    
    def test_fire_trigger(self):
        """Test firing a trigger"""
        def action(ctx):
            return f"received: {ctx.get('value', 'none')}"
        
        self.agent.register_trigger("test_trigger", "condition", action)
        result = self.agent.fire_trigger("test_trigger", {"value": "data"})
        
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "received: data")
    
    def test_fire_nonexistent_trigger(self):
        """Test firing non-existent trigger"""
        result = self.agent.fire_trigger("nonexistent")
        
        self.assertFalse(result["success"])
    
    # ========== Snapshot Tests ==========
    
    def test_create_snapshot(self):
        """Test creating a snapshot"""
        self.agent.create_echo("echo1", "Content")
        self.agent.register_persona("p1", "Name", [])
        
        result = self.agent.create_snapshot("test_snapshot")
        
        self.assertTrue(result["success"])
        self.assertIn("checksum", result)
        self.assertIn("summary", result)
    
    def test_snapshot_auto_id(self):
        """Test snapshot with auto-generated ID"""
        result = self.agent.create_snapshot()
        
        self.assertTrue(result["success"])
        self.assertTrue(result["snapshot_id"].startswith("snapshot_"))
    
    def test_restore_snapshot(self):
        """Test restoring from snapshot"""
        # Set up state
        self.agent.create_echo("echo1", "Content")
        self.agent.set_jump_point("jump1", 0)
        
        # Create snapshot
        self.agent.create_snapshot("restore_test")
        
        # Modify state
        self.agent.create_echo("echo2", "New content")
        
        # Restore
        result = self.agent.restore_snapshot("restore_test")
        
        self.assertTrue(result["success"])
    
    def test_restore_nonexistent_snapshot(self):
        """Test restoring non-existent snapshot"""
        result = self.agent.restore_snapshot("nonexistent")
        
        self.assertFalse(result["success"])
    
    # ========== Particle Notation Tests ==========
    
    def test_compress_to_particle_notation(self):
        """Test compressing state to particle notation"""
        self.agent.create_echo("echo1", "A")
        
        notation = self.agent.compress_to_particle_notation()
        
        self.assertIn("✦Seed:⊕Echo", notation)
        self.assertIn("∞Trace → ζMemory^↻Loop", notation)
        self.assertIn("⊕Core → ⟁1053", notation)
        self.assertIn("DictSeed.0003", notation)
    
    # ========== Checksum Tests ==========
    
    def test_checksum_consistency(self):
        """Test that checksums are consistent for same data"""
        data = {"key": "value", "number": 42}
        
        checksum1 = self.agent._generate_checksum(data)
        checksum2 = self.agent._generate_checksum(data)
        
        self.assertEqual(checksum1, checksum2)
    
    def test_checksum_difference(self):
        """Test that different data produces different checksums"""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        
        checksum1 = self.agent._generate_checksum(data1)
        checksum2 = self.agent._generate_checksum(data2)
        
        self.assertNotEqual(checksum1, checksum2)


class TestFluinDictAgentIntegration(unittest.TestCase):
    """Integration tests for FluinDictAgent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.agent = FluinDictAgent(storage_path=self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_full_workflow(self):
        """Test complete workflow from echo to snapshot"""
        # Step 1: Create echoes
        self.agent.create_echo("greeting", "Hello")
        self.agent.create_echo("data", {"info": "test"})
        
        # Step 2: Set jump points
        self.agent.set_jump_point("checkpoint1", 0)
        
        # Step 3: Register and use tool
        self.agent.register_tool("processor", "data", ["input", "output"])
        self.agent.map_field("processor", "input", "raw_data")
        
        # Step 4: Register persona
        self.agent.register_persona("assistant", "Helper", ["helpful"])
        
        # Step 5: Create seed with data
        self.agent.create_dict_seed("workflow_seed", {
            "step": "complete",
            "echoes": 2,
            "tools": 1
        })
        
        # Step 6: Create snapshot
        snapshot_result = self.agent.create_snapshot("workflow_snapshot")
        
        # Verify
        self.assertTrue(snapshot_result["success"])
        summary = snapshot_result["summary"]
        self.assertEqual(summary["echoes"], 2)
        self.assertEqual(summary["tools"], 1)
        self.assertEqual(summary["personas"], 1)
    
    def test_memory_trace_completeness(self):
        """Test that all operations are tracked in memory trace"""
        self.agent.create_echo("e1", "A")
        self.agent.trigger_echo("e1")
        self.agent.set_jump_point("j1", 0)
        self.agent.register_tool("t1", "test", [])
        self.agent.create_dict_seed("s1", {})
        self.agent.register_persona("p1", "P", [])
        
        trace = self.agent.get_trace()
        actions = [entry["action"] for entry in trace]
        
        self.assertIn("create_echo", actions)
        self.assertIn("trigger_echo", actions)
        self.assertIn("set_jump", actions)
        self.assertIn("register_tool", actions)
        self.assertIn("create_dict_seed", actions)
        self.assertIn("register_persona", actions)


if __name__ == '__main__':
    unittest.main()
