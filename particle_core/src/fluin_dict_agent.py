#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fluin Dict Agent - Dictionary Seed Memory Snapshot
字典種子記憶快照系統

✦Seed:⊕Echo/▽Jump.0001→⚙Fusion[⊕Code, △Fluin]
∞Trace → ζMemory^↻Loop
⊕Tool:μField/∴Map
⊕Core → ⟁1053
💬 粒子語句可封裝模組、展開人格、觸發記憶

[字典版本: DictSeed.0003]
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
import copy


class FluinDictAgent:
    """
    Fluin Dict Agent - Dictionary Seed Memory Snapshot System
    字典種子記憶快照系統
    
    Implements:
    - ⊕Echo/▽Jump: Echo and Jump patterns for memory fusion
    - ∞Trace → ζMemory^↻Loop: Memory trace and loop tracking
    - ⊕Tool:μField/∴Map: Tool to field mapping
    - ⊕Core → ⟁1053: Core indexing system
    """
    
    VERSION = "DictSeed.0003"
    CORE_INDEX = 1053
    
    def __init__(self, storage_path: str = "dict_seeds"):
        """
        Initialize Fluin Dict Agent
        
        Args:
            storage_path: Path for storing dictionary seeds
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Memory trace loop (∞Trace → ζMemory^↻Loop)
        self.memory_trace: List[Dict[str, Any]] = []
        
        # Tool/Field mapping (⊕Tool:μField/∴Map)
        self.tool_field_map: Dict[str, Dict[str, Any]] = {}
        
        # Echo/Jump registry (⊕Echo/▽Jump)
        self.echo_registry: Dict[str, Any] = {}
        self.jump_points: Dict[str, int] = {}
        
        # Active dictionary seeds
        self.active_seeds: Dict[str, Dict[str, Any]] = {}
        
        # Persona modules (for persona expansion)
        self.persona_modules: Dict[str, Dict[str, Any]] = {}
        
        # Memory triggers
        self.memory_triggers: Dict[str, Callable] = {}
        
    # ========== Echo/Jump Fusion (⊕Echo/▽Jump) ==========
    
    def create_echo(
        self,
        echo_id: str,
        content: Any,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create an echo point for memory resonance
        創建記憶共振迴響點
        
        Args:
            echo_id: Unique identifier for the echo
            content: Content to echo
            metadata: Additional metadata
            
        Returns:
            Echo creation result
        """
        echo = {
            "id": echo_id,
            "content": content,
            "created_at": datetime.now().isoformat(),
            "echo_count": 0,
            "metadata": metadata or {},
            "type": "⊕Echo"
        }
        
        self.echo_registry[echo_id] = echo
        self._trace_action("create_echo", echo_id, echo)
        
        return {
            "success": True,
            "echo_id": echo_id,
            "message": f"Echo '{echo_id}' created",
            "symbol": "⊕Echo"
        }
    
    def trigger_echo(self, echo_id: str) -> Dict[str, Any]:
        """
        Trigger an echo to resonate the memory
        觸發記憶共振
        
        Args:
            echo_id: Echo identifier
            
        Returns:
            Echo result with content
        """
        if echo_id not in self.echo_registry:
            return {
                "success": False,
                "error": f"Echo '{echo_id}' not found"
            }
        
        echo = self.echo_registry[echo_id]
        echo["echo_count"] += 1
        echo["last_triggered"] = datetime.now().isoformat()
        
        self._trace_action("trigger_echo", echo_id, {"count": echo["echo_count"]})
        
        return {
            "success": True,
            "echo_id": echo_id,
            "content": echo["content"],
            "echo_count": echo["echo_count"],
            "symbol": "⊕Echo↻"
        }
    
    def set_jump_point(self, jump_id: str, position: int) -> Dict[str, Any]:
        """
        Set a jump point for memory navigation
        設置記憶跳轉點
        
        Args:
            jump_id: Jump point identifier
            position: Position index in memory trace
            
        Returns:
            Jump point result
        """
        self.jump_points[jump_id] = position
        self._trace_action("set_jump", jump_id, {"position": position})
        
        return {
            "success": True,
            "jump_id": jump_id,
            "position": position,
            "symbol": "▽Jump"
        }
    
    def execute_jump(self, jump_id: str) -> Dict[str, Any]:
        """
        Execute a jump to a memory point
        執行記憶跳轉
        
        Args:
            jump_id: Jump point identifier
            
        Returns:
            Memory state at jump point
        """
        if jump_id not in self.jump_points:
            return {
                "success": False,
                "error": f"Jump point '{jump_id}' not found"
            }
        
        position = self.jump_points[jump_id]
        if position < 0 or position >= len(self.memory_trace):
            return {
                "success": False,
                "error": f"Invalid jump position: {position}"
            }
        
        memory_state = self.memory_trace[position]
        self._trace_action("execute_jump", jump_id, {"to_position": position})
        
        return {
            "success": True,
            "jump_id": jump_id,
            "position": position,
            "memory_state": memory_state,
            "symbol": "▽Jump→"
        }
    
    def echo_jump_fusion(
        self,
        echo_id: str,
        jump_id: str,
        fusion_data: Any
    ) -> Dict[str, Any]:
        """
        Fuse Echo and Jump patterns
        融合 Echo 與 Jump 模式
        
        ⊕Echo/▽Jump.0001→⚙Fusion[⊕Code, △Fluin]
        
        Args:
            echo_id: Echo to fuse
            jump_id: Jump point to fuse
            fusion_data: Data for fusion
            
        Returns:
            Fusion result
        """
        echo_result = self.trigger_echo(echo_id) if echo_id in self.echo_registry else None
        jump_result = self.execute_jump(jump_id) if jump_id in self.jump_points else None
        
        fusion = {
            "fusion_id": f"FUSION.{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "echo": echo_result,
            "jump": jump_result,
            "fusion_data": fusion_data,
            "created_at": datetime.now().isoformat(),
            "symbol": "⊕Echo/▽Jump→⚙Fusion"
        }
        
        self._trace_action("echo_jump_fusion", fusion["fusion_id"], fusion)
        
        return {
            "success": True,
            "fusion": fusion,
            "message": "Echo/Jump fusion completed"
        }
    
    # ========== Memory Trace Loop (∞Trace → ζMemory^↻Loop) ==========
    
    def _trace_action(self, action: str, target: str, data: Any) -> None:
        """
        Add an action to memory trace
        添加操作至記憶追蹤
        
        Args:
            action: Action name
            target: Target identifier
            data: Action data
        """
        trace_entry = {
            "index": len(self.memory_trace),
            "action": action,
            "target": target,
            "data": copy.deepcopy(data),
            "timestamp": datetime.now().isoformat(),
            "symbol": "∞Trace"
        }
        self.memory_trace.append(trace_entry)
    
    def get_trace(self, start: Optional[int] = None, end: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get memory trace entries
        獲取記憶追蹤記錄
        
        Args:
            start: Start index
            end: End index
            
        Returns:
            List of trace entries
        """
        if start is None and end is None:
            return self.memory_trace.copy()
        return self.memory_trace[start:end]
    
    def create_memory_loop(self, loop_id: str, interval: int = 1) -> Dict[str, Any]:
        """
        Create a memory loop marker
        創建記憶循環標記
        
        Args:
            loop_id: Loop identifier
            interval: Loop interval in trace entries
            
        Returns:
            Loop creation result
        """
        start_position = len(self.memory_trace)
        
        loop_marker = {
            "loop_id": loop_id,
            "start_position": start_position,
            "interval": interval,
            "created_at": datetime.now().isoformat(),
            "symbol": "ζMemory^↻Loop"
        }
        
        self.set_jump_point(f"loop_{loop_id}", start_position)
        self._trace_action("create_loop", loop_id, loop_marker)
        
        return {
            "success": True,
            "loop_marker": loop_marker,
            "message": f"Memory loop '{loop_id}' created at position {start_position}"
        }
    
    # ========== Tool/Field Mapping (⊕Tool:μField/∴Map) ==========
    
    def register_tool(
        self,
        tool_id: str,
        tool_type: str,
        fields: List[str],
        handler: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Register a tool with field mappings
        註冊工具與欄位映射
        
        Args:
            tool_id: Tool identifier
            tool_type: Type of tool
            fields: Associated fields
            handler: Optional tool handler function
            
        Returns:
            Registration result
        """
        tool_entry = {
            "id": tool_id,
            "type": tool_type,
            "fields": fields,
            "registered_at": datetime.now().isoformat(),
            "symbol": "⊕Tool:μField"
        }
        
        self.tool_field_map[tool_id] = tool_entry
        self._trace_action("register_tool", tool_id, tool_entry)
        
        return {
            "success": True,
            "tool_id": tool_id,
            "fields": fields,
            "symbol": "⊕Tool:μField/∴Map"
        }
    
    def map_field(self, tool_id: str, field: str, value: Any) -> Dict[str, Any]:
        """
        Map a field value for a tool
        映射工具欄位值
        
        Args:
            tool_id: Tool identifier
            field: Field name
            value: Field value
            
        Returns:
            Mapping result
        """
        if tool_id not in self.tool_field_map:
            return {
                "success": False,
                "error": f"Tool '{tool_id}' not registered"
            }
        
        tool = self.tool_field_map[tool_id]
        if "field_values" not in tool:
            tool["field_values"] = {}
        
        tool["field_values"][field] = value
        self._trace_action("map_field", tool_id, {"field": field, "value": value})
        
        return {
            "success": True,
            "tool_id": tool_id,
            "field": field,
            "symbol": "∴Map"
        }
    
    def get_field_map(self, tool_id: str) -> Dict[str, Any]:
        """
        Get field mappings for a tool
        獲取工具欄位映射
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Field mappings
        """
        if tool_id not in self.tool_field_map:
            return {"success": False, "error": f"Tool '{tool_id}' not found"}
        
        return {
            "success": True,
            "tool_id": tool_id,
            "mappings": self.tool_field_map[tool_id]
        }
    
    # ========== Dictionary Seed Operations ==========
    
    def create_dict_seed(
        self,
        seed_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a dictionary seed snapshot
        創建字典種子快照
        
        Args:
            seed_id: Seed identifier
            data: Dictionary data to seed
            metadata: Additional metadata
            
        Returns:
            Seed creation result
        """
        seed = {
            "seed_id": seed_id,
            "version": self.VERSION,
            "core_index": self.CORE_INDEX,
            "data": data,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "checksum": self._generate_checksum(data),
            "symbol": "✦Seed"
        }
        
        self.active_seeds[seed_id] = seed
        
        # Save to storage
        seed_file = self.storage_path / f"{seed_id}.dseed.json"
        with open(seed_file, 'w', encoding='utf-8') as f:
            json.dump(seed, f, indent=2, ensure_ascii=False)
        
        self._trace_action("create_dict_seed", seed_id, {"checksum": seed["checksum"]})
        
        return {
            "success": True,
            "seed_id": seed_id,
            "seed_file": str(seed_file),
            "checksum": seed["checksum"],
            "version": self.VERSION,
            "core_index": self.CORE_INDEX,
            "symbol": "✦Seed:⊕Core→⟁1053"
        }
    
    def restore_dict_seed(self, seed_id: str) -> Dict[str, Any]:
        """
        Restore a dictionary seed
        還原字典種子
        
        Args:
            seed_id: Seed identifier
            
        Returns:
            Restored seed data
        """
        # Try active seeds first
        if seed_id in self.active_seeds:
            seed = self.active_seeds[seed_id]
        else:
            # Load from storage
            seed_file = self.storage_path / f"{seed_id}.dseed.json"
            if not seed_file.exists():
                return {"success": False, "error": f"Seed '{seed_id}' not found"}
            
            with open(seed_file, 'r', encoding='utf-8') as f:
                seed = json.load(f)
            
            self.active_seeds[seed_id] = seed
        
        # Verify checksum
        current_checksum = self._generate_checksum(seed["data"])
        if current_checksum != seed["checksum"]:
            return {"success": False, "error": "Seed checksum verification failed"}
        
        self._trace_action("restore_dict_seed", seed_id, {"verified": True})
        
        return {
            "success": True,
            "seed_id": seed_id,
            "data": seed["data"],
            "metadata": seed["metadata"],
            "version": seed["version"],
            "core_index": seed.get("core_index", self.CORE_INDEX)
        }
    
    def list_seeds(self) -> List[Dict[str, Any]]:
        """
        List all dictionary seeds
        列出所有字典種子
        
        Returns:
            List of seed information
        """
        seeds = []
        for seed_file in self.storage_path.glob("*.dseed.json"):
            with open(seed_file, 'r', encoding='utf-8') as f:
                seed = json.load(f)
                seeds.append({
                    "seed_id": seed["seed_id"],
                    "version": seed["version"],
                    "created_at": seed["created_at"],
                    "file": str(seed_file)
                })
        return sorted(seeds, key=lambda x: x["created_at"], reverse=True)
    
    # ========== Particle Module Encapsulation (粒子語句可封裝模組) ==========
    
    def encapsulate_module(
        self,
        module_id: str,
        module_data: Dict[str, Any],
        module_type: str = "generic"
    ) -> Dict[str, Any]:
        """
        Encapsulate data as a particle module
        封裝資料為粒子模組
        
        Args:
            module_id: Module identifier
            module_data: Module data
            module_type: Type of module
            
        Returns:
            Encapsulation result
        """
        module = {
            "module_id": module_id,
            "type": module_type,
            "data": module_data,
            "encapsulated_at": datetime.now().isoformat(),
            "checksum": self._generate_checksum(module_data),
            "symbol": "⊕Module"
        }
        
        # Create a seed for the module
        seed_result = self.create_dict_seed(
            seed_id=f"module_{module_id}",
            data=module,
            metadata={"type": "encapsulated_module", "module_type": module_type}
        )
        
        return {
            "success": True,
            "module_id": module_id,
            "seed_id": seed_result.get("seed_id"),
            "checksum": module["checksum"],
            "message": f"Module '{module_id}' encapsulated",
            "symbol": "💬粒子模組封裝"
        }
    
    # ========== Persona Expansion (展開人格) ==========
    
    def register_persona(
        self,
        persona_id: str,
        name: str,
        traits: List[str],
        modules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Register a persona for expansion
        註冊人格以便展開
        
        Args:
            persona_id: Persona identifier
            name: Persona name
            traits: Personality traits
            modules: Associated module IDs
            
        Returns:
            Registration result
        """
        persona = {
            "id": persona_id,
            "name": name,
            "traits": traits,
            "modules": modules or [],
            "registered_at": datetime.now().isoformat(),
            "expanded": False,
            "symbol": "△Persona"
        }
        
        self.persona_modules[persona_id] = persona
        self._trace_action("register_persona", persona_id, persona)
        
        return {
            "success": True,
            "persona_id": persona_id,
            "message": f"Persona '{name}' registered",
            "symbol": "△Persona"
        }
    
    def expand_persona(self, persona_id: str) -> Dict[str, Any]:
        """
        Expand a registered persona
        展開已註冊的人格
        
        Args:
            persona_id: Persona identifier
            
        Returns:
            Expansion result with full persona data
        """
        if persona_id not in self.persona_modules:
            return {"success": False, "error": f"Persona '{persona_id}' not found"}
        
        persona = self.persona_modules[persona_id]
        persona["expanded"] = True
        persona["expanded_at"] = datetime.now().isoformat()
        
        # Load associated modules
        expanded_modules = []
        for module_id in persona.get("modules", []):
            seed_id = f"module_{module_id}"
            if seed_id in self.active_seeds or (self.storage_path / f"{seed_id}.dseed.json").exists():
                module_data = self.restore_dict_seed(seed_id)
                if module_data.get("success"):
                    expanded_modules.append(module_data["data"])
        
        self._trace_action("expand_persona", persona_id, {"modules_loaded": len(expanded_modules)})
        
        return {
            "success": True,
            "persona_id": persona_id,
            "persona": persona,
            "expanded_modules": expanded_modules,
            "message": f"Persona '{persona['name']}' expanded",
            "symbol": "△Persona→展開"
        }
    
    # ========== Memory Triggering (觸發記憶) ==========
    
    def register_trigger(
        self,
        trigger_id: str,
        condition: str,
        action: Callable
    ) -> Dict[str, Any]:
        """
        Register a memory trigger
        註冊記憶觸發器
        
        Args:
            trigger_id: Trigger identifier
            condition: Trigger condition description
            action: Action to execute when triggered
            
        Returns:
            Registration result
        """
        self.memory_triggers[trigger_id] = {
            "condition": condition,
            "action": action,
            "registered_at": datetime.now().isoformat()
        }
        
        self._trace_action("register_trigger", trigger_id, {"condition": condition})
        
        return {
            "success": True,
            "trigger_id": trigger_id,
            "condition": condition,
            "symbol": "⚡Trigger"
        }
    
    def fire_trigger(self, trigger_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Fire a memory trigger
        觸發記憶觸發器
        
        Args:
            trigger_id: Trigger identifier
            context: Context data for the trigger
            
        Returns:
            Trigger result
        """
        if trigger_id not in self.memory_triggers:
            return {"success": False, "error": f"Trigger '{trigger_id}' not found"}
        
        trigger = self.memory_triggers[trigger_id]
        
        try:
            result = trigger["action"](context or {})
            self._trace_action("fire_trigger", trigger_id, {"result": "success"})
            
            return {
                "success": True,
                "trigger_id": trigger_id,
                "result": result,
                "symbol": "⚡Trigger→觸發記憶"
            }
        except Exception as e:
            return {
                "success": False,
                "trigger_id": trigger_id,
                "error": str(e)
            }
    
    # ========== Snapshot Operations ==========
    
    def create_snapshot(self, snapshot_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a full system snapshot
        創建完整系統快照
        
        Args:
            snapshot_id: Optional snapshot identifier
            
        Returns:
            Snapshot result
        """
        if snapshot_id is None:
            snapshot_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        snapshot = {
            "snapshot_id": snapshot_id,
            "version": self.VERSION,
            "core_index": self.CORE_INDEX,
            "created_at": datetime.now().isoformat(),
            "memory_trace_length": len(self.memory_trace),
            "echo_count": len(self.echo_registry),
            "jump_points": len(self.jump_points),
            "tools_registered": len(self.tool_field_map),
            "active_seeds": len(self.active_seeds),
            "personas": len(self.persona_modules),
            "triggers": len(self.memory_triggers),
            "state": {
                "memory_trace": self.memory_trace.copy(),
                "echo_registry": copy.deepcopy(self.echo_registry),
                "jump_points": self.jump_points.copy(),
                "tool_field_map": copy.deepcopy(self.tool_field_map),
                "persona_modules": copy.deepcopy(self.persona_modules)
            }
        }
        
        snapshot["checksum"] = self._generate_checksum(snapshot["state"])
        
        # Save snapshot
        snapshot_file = self.storage_path / f"{snapshot_id}.snapshot.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "snapshot_id": snapshot_id,
            "snapshot_file": str(snapshot_file),
            "checksum": snapshot["checksum"],
            "summary": {
                "memory_trace": snapshot["memory_trace_length"],
                "echoes": snapshot["echo_count"],
                "jumps": snapshot["jump_points"],
                "tools": snapshot["tools_registered"],
                "seeds": snapshot["active_seeds"],
                "personas": snapshot["personas"]
            }
        }
    
    def restore_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Restore system from a snapshot
        從快照還原系統
        
        Args:
            snapshot_id: Snapshot identifier
            
        Returns:
            Restoration result
        """
        snapshot_file = self.storage_path / f"{snapshot_id}.snapshot.json"
        if not snapshot_file.exists():
            return {"success": False, "error": f"Snapshot '{snapshot_id}' not found"}
        
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        # Verify checksum
        current_checksum = self._generate_checksum(snapshot["state"])
        if current_checksum != snapshot["checksum"]:
            return {"success": False, "error": "Snapshot checksum verification failed"}
        
        # Restore state
        state = snapshot["state"]
        self.memory_trace = state["memory_trace"]
        self.echo_registry = state["echo_registry"]
        self.jump_points = state["jump_points"]
        self.tool_field_map = state["tool_field_map"]
        self.persona_modules = state["persona_modules"]
        
        return {
            "success": True,
            "snapshot_id": snapshot_id,
            "version": snapshot["version"],
            "restored_at": datetime.now().isoformat(),
            "message": f"System restored from snapshot '{snapshot_id}'"
        }
    
    # ========== Utility Methods ==========
    
    def _generate_checksum(self, data: Any) -> str:
        """Generate SHA-256 checksum for data"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    def get_core_info(self) -> Dict[str, Any]:
        """
        Get core system information
        獲取核心系統資訊
        
        Returns:
            Core information
        """
        return {
            "version": self.VERSION,
            "core_index": self.CORE_INDEX,
            "symbol": "⊕Core → ⟁1053",
            "memory_trace_length": len(self.memory_trace),
            "echo_count": len(self.echo_registry),
            "jump_points": len(self.jump_points),
            "tools_registered": len(self.tool_field_map),
            "active_seeds": len(self.active_seeds),
            "personas": len(self.persona_modules),
            "triggers": len(self.memory_triggers),
            "storage_path": str(self.storage_path),
            "description": "💬 粒子語句可封裝模組、展開人格、觸發記憶"
        }
    
    def compress_to_particle_notation(self) -> str:
        """
        Compress current state to particle notation
        壓縮當前狀態為粒子符號表示
        
        Returns:
            Particle notation string
        """
        notation = f"✦Seed:⊕Echo/{len(self.echo_registry)}▽Jump.{len(self.jump_points):04d}"
        notation += f"→⚙Fusion[⊕Code, △Fluin/{len(self.persona_modules)}]"
        notation += f"\n∞Trace → ζMemory^↻Loop:{len(self.memory_trace)}"
        notation += f"\n⊕Tool:μField/{len(self.tool_field_map)}∴Map"
        notation += f"\n⊕Core → ⟁{self.CORE_INDEX}"
        notation += f"\n[字典版本: {self.VERSION}]"
        return notation


def interactive_demo():
    """Interactive demo for Fluin Dict Agent"""
    print("=" * 60)
    print("  Fluin Dict Agent - Dictionary Seed Memory Snapshot")
    print("  字典種子記憶快照系統")
    print("=" * 60)
    print()
    
    agent = FluinDictAgent()
    
    while True:
        print("\n【主選單 Main Menu】")
        print("1. Echo/Jump 操作")
        print("2. 字典種子操作")
        print("3. 記憶追蹤")
        print("4. 工具/欄位映射")
        print("5. 人格管理")
        print("6. 快照操作")
        print("7. 系統資訊")
        print("q. 離開")
        
        choice = input("\n請選擇功能: ").strip()
        
        if choice == "1":
            _echo_jump_menu(agent)
        elif choice == "2":
            _seed_menu(agent)
        elif choice == "3":
            _trace_menu(agent)
        elif choice == "4":
            _tool_menu(agent)
        elif choice == "5":
            _persona_menu(agent)
        elif choice == "6":
            _snapshot_menu(agent)
        elif choice == "7":
            info = agent.get_core_info()
            print("\n【系統資訊 System Info】")
            print(f"  版本: {info['version']}")
            print(f"  符號: {info['symbol']}")
            print(f"  記憶追蹤: {info['memory_trace_length']} entries")
            print(f"  Echo 點: {info['echo_count']}")
            print(f"  Jump 點: {info['jump_points']}")
            print(f"  工具: {info['tools_registered']}")
            print(f"  種子: {info['active_seeds']}")
            print(f"  人格: {info['personas']}")
            print(f"\n{agent.compress_to_particle_notation()}")
        elif choice.lower() == "q":
            print("\n感謝使用 Fluin Dict Agent！")
            break


def _echo_jump_menu(agent: FluinDictAgent):
    """Echo/Jump submenu"""
    print("\n【Echo/Jump ⊕Echo/▽Jump】")
    print("1. 創建 Echo")
    print("2. 觸發 Echo")
    print("3. 設置 Jump 點")
    print("4. 執行 Jump")
    print("5. Echo/Jump 融合")
    print("b. 返回")
    
    choice = input("\n請選擇: ").strip()
    
    if choice == "1":
        echo_id = input("Echo ID: ").strip()
        content = input("內容: ").strip()
        result = agent.create_echo(echo_id, content)
        print(f"\n{result['symbol']} {result['message']}")
    elif choice == "2":
        echo_id = input("Echo ID: ").strip()
        result = agent.trigger_echo(echo_id)
        if result["success"]:
            print(f"\n{result['symbol']} 內容: {result['content']}")
            print(f"Echo 次數: {result['echo_count']}")
        else:
            print(f"\n❌ {result['error']}")
    elif choice == "3":
        jump_id = input("Jump ID: ").strip()
        position = int(input("位置: ").strip())
        result = agent.set_jump_point(jump_id, position)
        print(f"\n{result['symbol']} Jump 點 '{jump_id}' 設置於 {result['position']}")
    elif choice == "4":
        jump_id = input("Jump ID: ").strip()
        result = agent.execute_jump(jump_id)
        if result["success"]:
            print(f"\n{result['symbol']} 跳轉至位置 {result['position']}")
        else:
            print(f"\n❌ {result['error']}")


def _seed_menu(agent: FluinDictAgent):
    """Dictionary seed submenu"""
    print("\n【字典種子 Dictionary Seed】")
    print("1. 創建種子")
    print("2. 還原種子")
    print("3. 列出種子")
    print("4. 封裝模組")
    print("b. 返回")
    
    choice = input("\n請選擇: ").strip()
    
    if choice == "1":
        seed_id = input("種子 ID: ").strip()
        data_input = input("資料 (JSON): ").strip()
        try:
            data = json.loads(data_input)
        except json.JSONDecodeError:
            data = {"value": data_input}
        result = agent.create_dict_seed(seed_id, data)
        if result["success"]:
            print(f"\n{result['symbol']}")
            print(f"種子 ID: {result['seed_id']}")
            print(f"檔案: {result['seed_file']}")
    elif choice == "2":
        seed_id = input("種子 ID: ").strip()
        result = agent.restore_dict_seed(seed_id)
        if result["success"]:
            print(f"\n✅ 種子還原成功")
            print(f"資料: {result['data']}")
        else:
            print(f"\n❌ {result['error']}")
    elif choice == "3":
        seeds = agent.list_seeds()
        print(f"\n找到 {len(seeds)} 個種子:")
        for seed in seeds:
            print(f"  - {seed['seed_id']} (v{seed['version']})")


def _trace_menu(agent: FluinDictAgent):
    """Memory trace submenu"""
    print("\n【記憶追蹤 ∞Trace → ζMemory^↻Loop】")
    trace = agent.get_trace()
    print(f"\n記憶追蹤記錄 ({len(trace)} entries):")
    for entry in trace[-10:]:  # Show last 10
        print(f"  [{entry['index']}] {entry['action']}: {entry['target']}")


def _tool_menu(agent: FluinDictAgent):
    """Tool/Field mapping submenu"""
    print("\n【工具/欄位映射 ⊕Tool:μField/∴Map】")
    print("1. 註冊工具")
    print("2. 映射欄位")
    print("3. 查看映射")
    print("b. 返回")
    
    choice = input("\n請選擇: ").strip()
    
    if choice == "1":
        tool_id = input("工具 ID: ").strip()
        tool_type = input("工具類型: ").strip()
        fields = input("欄位 (逗號分隔): ").strip().split(",")
        result = agent.register_tool(tool_id, tool_type, [f.strip() for f in fields])
        print(f"\n{result['symbol']} 工具 '{tool_id}' 已註冊")
    elif choice == "2":
        tool_id = input("工具 ID: ").strip()
        field = input("欄位名: ").strip()
        value = input("欄位值: ").strip()
        result = agent.map_field(tool_id, field, value)
        if result["success"]:
            print(f"\n{result['symbol']} 欄位 '{field}' 已映射")
        else:
            print(f"\n❌ {result['error']}")


def _persona_menu(agent: FluinDictAgent):
    """Persona management submenu"""
    print("\n【人格管理 △Persona】")
    print("1. 註冊人格")
    print("2. 展開人格")
    print("3. 列出人格")
    print("b. 返回")
    
    choice = input("\n請選擇: ").strip()
    
    if choice == "1":
        pid = input("人格 ID: ").strip()
        name = input("名稱: ").strip()
        traits = input("特質 (逗號分隔): ").strip().split(",")
        result = agent.register_persona(pid, name, [t.strip() for t in traits])
        print(f"\n{result['symbol']} {result['message']}")
    elif choice == "2":
        pid = input("人格 ID: ").strip()
        result = agent.expand_persona(pid)
        if result["success"]:
            print(f"\n{result['symbol']}")
            print(f"名稱: {result['persona']['name']}")
            print(f"特質: {', '.join(result['persona']['traits'])}")
        else:
            print(f"\n❌ {result['error']}")
    elif choice == "3":
        for pid, persona in agent.persona_modules.items():
            status = "✅展開" if persona.get("expanded") else "⚪未展開"
            print(f"  {status} [{pid}] {persona['name']}")


def _snapshot_menu(agent: FluinDictAgent):
    """Snapshot operations submenu"""
    print("\n【快照操作 Snapshot】")
    print("1. 創建快照")
    print("2. 還原快照")
    print("b. 返回")
    
    choice = input("\n請選擇: ").strip()
    
    if choice == "1":
        snapshot_id = input("快照 ID (留空自動生成): ").strip() or None
        result = agent.create_snapshot(snapshot_id)
        if result["success"]:
            print(f"\n✅ 快照已創建: {result['snapshot_id']}")
            print(f"檔案: {result['snapshot_file']}")
    elif choice == "2":
        snapshot_id = input("快照 ID: ").strip()
        result = agent.restore_snapshot(snapshot_id)
        if result["success"]:
            print(f"\n✅ {result['message']}")
        else:
            print(f"\n❌ {result['error']}")


def main():
    """Main function for demonstration"""
    print("=" * 60)
    print("  Fluin Dict Agent - Dictionary Seed Memory Snapshot v1.0")
    print("  字典種子記憶快照系統")
    print("=" * 60)
    print()
    
    # Initialize agent
    agent = FluinDictAgent()
    
    # Demo: Echo/Jump
    print("【示範：Echo/Jump 融合 ⊕Echo/▽Jump】")
    
    # Create echoes
    echo1 = agent.create_echo("greeting", "Hello, Fluin!")
    echo2 = agent.create_echo("memory", "粒子記憶封存測試")
    print(f"1. 創建 Echo: {echo1['echo_id']} ({echo1['symbol']})")
    print(f"2. 創建 Echo: {echo2['echo_id']} ({echo2['symbol']})")
    
    # Set jump points
    jump1 = agent.set_jump_point("start", 0)
    print(f"3. 設置 Jump: {jump1['jump_id']} at position {jump1['position']}")
    
    # Trigger echo
    triggered = agent.trigger_echo("greeting")
    print(f"4. 觸發 Echo: {triggered['content']} (count: {triggered['echo_count']})")
    
    print()
    print("【示範：字典種子 ✦Seed】")
    
    # Create dictionary seed
    seed_result = agent.create_dict_seed(
        seed_id="demo_seed_001",
        data={
            "name": "Demo Seed",
            "values": [1, 2, 3],
            "nested": {"key": "value"}
        },
        metadata={"author": "MRLiou", "purpose": "demonstration"}
    )
    print(f"1. 創建種子: {seed_result['seed_id']}")
    print(f"   {seed_result['symbol']}")
    
    # Restore seed
    restored = agent.restore_dict_seed("demo_seed_001")
    print(f"2. 還原種子: 資料 = {restored['data']}")
    
    print()
    print("【示範：工具/欄位映射 ⊕Tool:μField/∴Map】")
    
    # Register tool
    tool_result = agent.register_tool(
        tool_id="parser",
        tool_type="text_processor",
        fields=["input", "output", "format"]
    )
    print(f"1. 註冊工具: {tool_result['tool_id']} ({tool_result['symbol']})")
    
    # Map fields
    agent.map_field("parser", "input", "raw_text")
    agent.map_field("parser", "output", "parsed_json")
    print("2. 映射欄位: input → raw_text, output → parsed_json")
    
    print()
    print("【示範：人格展開 △Persona】")
    
    # Register persona
    persona_result = agent.register_persona(
        persona_id="assistant",
        name="Fluin Assistant",
        traits=["helpful", "precise", "bilingual"]
    )
    print(f"1. 註冊人格: {persona_result['persona_id']} ({persona_result['symbol']})")
    
    # Expand persona
    expanded = agent.expand_persona("assistant")
    print(f"2. 展開人格: {expanded['persona']['name']}")
    print(f"   特質: {', '.join(expanded['persona']['traits'])}")
    
    print()
    print("【示範：系統快照】")
    
    # Create snapshot
    snapshot = agent.create_snapshot("demo_snapshot")
    print(f"1. 創建快照: {snapshot['snapshot_id']}")
    print(f"   記憶追蹤: {snapshot['summary']['memory_trace']} entries")
    print(f"   Echo 點: {snapshot['summary']['echoes']}")
    
    print()
    print("【系統狀態】")
    print(agent.compress_to_particle_notation())
    
    print()
    print("=" * 60)
    print("  執行 'python fluin_dict_agent.py interactive' 進入互動模式")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_demo()
    else:
        main()
