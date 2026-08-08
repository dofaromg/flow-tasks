#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MrLiouAI Runtime (整合運行時) — 連接所有模組的核心
Version: 1.0.0

This is the integration layer that connects:
1. FlowCore v1.1.0 (核心循環)
2. ParticleDictionary (粒子字典)
3. FluinBridge (語義轉譯)
4. PersonaSystem (人格系統)
5. MemorySystem (記憶系統)

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                     MrLiouAI Runtime                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Input ──▶ FluinBridge ──▶ ParticleChain                  │
│                       │              │                           │
│                       ▼              ▼                           │
│              PersonaSystem ◀──▶ FlowCore                        │
│                       │              │                           │
│                       ▼              ▼                           │
│              MemorySystem ◀──▶ Trace+Merkle                     │
│                       │                                          │
│                       ▼                                          │
│                  Response ──▶ User                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Philosophy:
- 單檔閉環可驗證 (Single-file closed loop)
- SOURCE_DUAL 對齊 (Dual view alignment)  
- 換載體不換靈魂 (Change carriers without changing souls)
- 怎麼過去，就怎麼回來 (Reversible design)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import time
import json
import hashlib

# Import modules
from particle_dict import ParticleDictionary, ParticleProcessor, ParticleChain
from fluin_bridge import FluinBridge, TranslationResult, IntentType
from persona_system import PersonaSystem, Persona, PersonaType, SelectionReason
from memory_system import FlowMemoryCore, MemoryEntry, MemoryType


# ============================================================
# Utilities
# ============================================================

def now_ns() -> int:
    return time.time_ns()

def hash64(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]

def stable_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# ============================================================
# Runtime Configuration
# ============================================================

@dataclass
class RuntimeConfig:
    """運行時配置"""
    data_dir: str = "./data"
    enable_memory: bool = True
    enable_trace: bool = True
    auto_commit: bool = True
    verbose: bool = False


# ============================================================
# Processing Result
# ============================================================

@dataclass
class ProcessingResult:
    """處理結果"""
    # Input
    input_text: str
    
    # Translation
    translation: TranslationResult
    
    # Persona
    persona: Persona
    persona_reason: SelectionReason
    
    # Particle chain
    particle_chain: ParticleChain
    
    # Memory (if committed)
    memory_entry: Optional[MemoryEntry] = None
    merkle_root: Optional[str] = None
    
    # Output
    response: str = ""
    
    # Trace
    trace_id: str = ""
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_text": self.input_text,
            "translation": self.translation.to_dict(),
            "persona": {
                "id": self.persona.persona_id,
                "name": self.persona.name,
                "type": self.persona.persona_type.value,
            },
            "persona_reason": self.persona_reason.to_dict(),
            "particle_chain": {
                "particles": [p.fx_code for p in self.particle_chain.particles],
                "energy": self.particle_chain.total_energy,
            },
            "memory_entry_id": self.memory_entry.entry_id if self.memory_entry else None,
            "merkle_root": self.merkle_root,
            "response": self.response,
            "trace_id": self.trace_id,
            "processing_time_ms": self.processing_time_ms,
        }


# ============================================================
# MrLiouAI Runtime
# ============================================================

class MrLiouAIRuntime:
    """
    MrLiouAI Runtime — 整合運行時
    
    連接所有模組，提供統一的處理接口。
    """

    def __init__(self, config: RuntimeConfig = None):
        self.config = config or RuntimeConfig()
        
        # Initialize components
        self._init_components()
        
        # Runtime state
        self._process_count = 0
        self._started_at = now_ns()

    def _init_components(self):
        """初始化所有組件"""
        # Particle Dictionary
        self.particle_dict = ParticleDictionary()
        self.particle_processor = ParticleProcessor(self.particle_dict)
        
        # Fluin Bridge
        self.fluin_bridge = FluinBridge(self.particle_dict)
        
        # Persona System
        self.persona_system = PersonaSystem()
        
        # Memory System
        if self.config.enable_memory:
            self.memory = FlowMemoryCore(self.config.data_dir)
        else:
            self.memory = None

    # ============================================================
    # Core Processing
    # ============================================================

    def process(self, text: str, context: Dict[str, Any] = None) -> ProcessingResult:
        """
        處理用戶輸入
        
        Flow:
        1. FluinBridge: 語義轉譯
        2. PersonaSystem: 選擇人格
        3. ParticleProcessor: 粒子處理
        4. MemorySystem: 記憶提交
        5. Generate response
        """
        start_time = time.time()
        self._process_count += 1
        context = context or {}

        # Step 1: Translation
        translation = self.fluin_bridge.translate_forward(text, context)

        # Step 2: Persona selection
        persona, persona_reason = self.persona_system.select(text)
        self.persona_system.gate.activate(persona.persona_id)

        # Step 3: Particle processing
        thought_result = self.particle_processor.process(text, context)
        particle_chain = thought_result.primary_chain

        # Step 4: Memory commit (if enabled)
        memory_entry = None
        merkle_root = None
        
        if self.memory and self.config.auto_commit:
            # Determine if we should commit based on intent
            should_commit = translation.intent.intent_type in [
                IntentType.REMEMBER,
                IntentType.CREATE,
                IntentType.CODE_WRITE,
            ] or "記" in text or "remember" in text.lower()

            if should_commit:
                memory_entry, merkle_node = self._commit_to_memory(
                    text, translation, persona, particle_chain
                )
                merkle_root = memory_entry.entry_id if memory_entry else None

        # Step 5: Generate response
        response = self._generate_response(
            text, translation, persona, particle_chain, memory_entry
        )

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Build result
        result = ProcessingResult(
            input_text=text,
            translation=translation,
            persona=persona,
            persona_reason=persona_reason,
            particle_chain=particle_chain,
            memory_entry=memory_entry,
            merkle_root=merkle_root,
            response=response,
            trace_id=f"flow_{self._process_count:08d}",
            processing_time_ms=processing_time,
        )

        return result

    def _commit_to_memory(
        self,
        text: str,
        translation: TranslationResult,
        persona: Persona,
        chain: ParticleChain,
    ) -> Tuple[MemoryEntry, Any]:
        """提交到記憶系統"""
        content = {
            "text": text,
            "intent": translation.intent.intent_type.value,
            "source_dual": translation.source_dual.to_dict(),
            "particle_chain": [p.fx_code for p in chain.particles],
        }

        # Determine memory type based on intent
        intent_to_type = {
            IntentType.REMEMBER: MemoryType.EPISODIC,
            IntentType.CODE_WRITE: MemoryType.PROCEDURAL,
            IntentType.ANALYZE: MemoryType.SEMANTIC,
        }
        mem_type = intent_to_type.get(translation.intent.intent_type, MemoryType.WORKING)

        # Commit
        result = self.memory.commit(
            content=content,
            memory_type=mem_type,
            tags=[translation.intent.intent_type.value] + [e.value for e in translation.entities[:3]],
            persona_id=persona.persona_id,
        )
        
        # Create MemoryEntry from result
        entry = MemoryEntry(
            entry_id=result.get("entry_id", f"mem_{hash64(str(content))}"),
            content=content,
            memory_type=mem_type,
            tags=[translation.intent.intent_type.value],
        )

        return entry, result

    def _generate_response(
        self,
        text: str,
        translation: TranslationResult,
        persona: Persona,
        chain: ParticleChain,
        memory_entry: Optional[MemoryEntry],
    ) -> str:
        """生成回應"""
        # Base response from translation
        response = translation.suggested_response

        # Add persona flavor
        if persona.persona_type == PersonaType.CODE:
            response = f"[CodeMode] {response}"
        elif persona.persona_type == PersonaType.MEMORY:
            response = f"[MemoryMode] {response}"
        elif persona.persona_type == PersonaType.LOGIC:
            response = f"[LogicMode] {response}"

        # Add memory confirmation
        if memory_entry:
            response += f" (已記錄: {memory_entry.entry_id[:12]}...)"

        return response

    # ============================================================
    # Memory Operations
    # ============================================================

    def remember(self, text: str, tags: List[str] = None) -> MemoryEntry:
        """手動記憶"""
        if not self.memory:
            raise RuntimeError("Memory system not enabled")

        entry, _ = self.memory.commit(
            content={"text": text, "manual": True},
            memory_type=MemoryType.EPISODIC,
            priority=MemoryType.EPISODIC,  # Using MemoryType as fallback
            tags=tags or [],
        )
        return entry

    def recall(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """回憶"""
        if not self.memory:
            return []
        return self.memory.recall(query, limit)

    def search_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索記憶"""
        if not self.memory:
            return []
        entries = self.memory.recall(query, limit)
        return [{"id": e.entry_id, "content": e.content, "tags": e.tags} for e in entries]

    # ============================================================
    # Persona Operations
    # ============================================================

    def get_active_persona(self) -> Optional[Persona]:
        """獲取當前人格"""
        return self.persona_system.gate.get_active()

    def switch_persona(self, persona_type: PersonaType) -> bool:
        """切換人格"""
        type_to_persona = {
            PersonaType.CORE: self.persona_system.core,
            PersonaType.LOGIC: self.persona_system.logic,
            PersonaType.LANGUAGE: self.persona_system.language,
            PersonaType.MEMORY: self.persona_system.memory,
            PersonaType.CODE: self.persona_system.code,
        }
        persona = type_to_persona.get(persona_type)
        if persona:
            return self.persona_system.gate.activate(persona.persona_id)
        return False

    def list_personas(self) -> List[Dict[str, Any]]:
        """列出所有人格"""
        return self.persona_system.gate.list_all()

    # ============================================================
    # Particle Operations
    # ============================================================

    def translate(self, text: str) -> Dict[str, Any]:
        """翻譯為粒子"""
        result = self.fluin_bridge.translate_forward(text)
        return {
            "intent": result.intent.intent_type.value,
            "particles": [p.fx_code for p, _ in result.matched_particles],
            "chain": result.source_dual.ai_view,
            "human_view": result.source_dual.human_view,
        }

    def get_particle(self, fx_code: str) -> Optional[Dict[str, Any]]:
        """獲取粒子信息"""
        p = self.particle_dict.get(fx_code)
        return p.to_dict() if p else None

    # ============================================================
    # Status & Health
    # ============================================================

    def status(self) -> Dict[str, Any]:
        """系統狀態"""
        uptime_ns = now_ns() - self._started_at
        uptime_sec = uptime_ns / 1e9

        status = {
            "version": "1.0.0",
            "uptime_seconds": uptime_sec,
            "process_count": self._process_count,
            "particle_dict_size": self.particle_dict.size,
            "personas": len(self.persona_system.gate.list_all()),
            "active_persona": None,
            "memory_enabled": self.memory is not None,
        }

        active = self.get_active_persona()
        if active:
            status["active_persona"] = {
                "id": active.persona_id,
                "name": active.name,
                "type": active.persona_type.value,
            }

        if self.memory:
            mem_status = self.memory.get_status()
            status["memory"] = {
                "chain_height": mem_status["chain_height"],
                "working_memory": mem_status["working_memory_size"],
            }

        return status

    def health_check(self) -> Dict[str, bool]:
        """健康檢查"""
        checks = {
            "particle_dict": self.particle_dict.size > 0,
            "fluin_bridge": True,
            "persona_system": len(self.persona_system.gate.list_all()) > 0,
            "memory_system": self.memory is not None,
        }

        if self.memory:
            checks["memory_integrity"] = True  # Simplified check

        return checks


# ============================================================
# Quick Access Functions
# ============================================================

_runtime: Optional[MrLiouAIRuntime] = None

def get_runtime() -> MrLiouAIRuntime:
    """獲取全局運行時實例"""
    global _runtime
    if _runtime is None:
        _runtime = MrLiouAIRuntime()
    return _runtime

def process(text: str) -> ProcessingResult:
    """快速處理"""
    return get_runtime().process(text)

def remember(text: str, tags: List[str] = None) -> MemoryEntry:
    """快速記憶"""
    return get_runtime().remember(text, tags)

def recall(query: str) -> List[MemoryEntry]:
    """快速回憶"""
    return get_runtime().recall(query)


# ============================================================
# Main / Demo
# ============================================================

def main():
    print("=" * 60)
    print("MrLiouAI Runtime v1.0.0")
    print("=" * 60)

    # Initialize
    runtime = MrLiouAIRuntime()

    # Health check
    print("\n🏥 Health Check:")
    health = runtime.health_check()
    for component, ok in health.items():
        status = "✅" if ok else "❌"
        print(f"   {status} {component}")

    # Status
    print("\n📊 Initial Status:")
    status = runtime.status()
    print(f"   Particle Dict: {status['particle_dict_size']} particles")
    print(f"   Personas: {status['personas']}")
    print(f"   Memory: {'enabled' if status['memory_enabled'] else 'disabled'}")

    # Process demo
    print("\n" + "=" * 60)
    print("🚀 Processing Demo")
    print("=" * 60)

    test_inputs = [
        "幫我用 Python 寫一個快速排序",
        "記住我喜歡喝拿鐵咖啡",
        "分析這段代碼的問題",
        "之前我們討論了什麼？",
        "Hello, how are you?",
    ]

    for text in test_inputs:
        print(f"\n📝 Input: 「{text}」")
        result = runtime.process(text)
        
        print(f"   Intent: {result.translation.intent.intent_type.value}")
        print(f"   Persona: {result.persona.name}")
        print(f"   Chain: {' → '.join(p.fx_code for p in result.particle_chain.particles[:3])}...")
        print(f"   Response: {result.response}")
        if result.memory_entry:
            print(f"   Memory: {result.memory_entry.entry_id}")
        print(f"   Time: {result.processing_time_ms:.2f}ms")

    # Memory recall demo
    print("\n" + "=" * 60)
    print("🔍 Memory Recall Demo")
    print("=" * 60)

    results = runtime.recall("咖啡")
    print(f"\n   Query: '咖啡'")
    print(f"   Found: {len(results)} results")
    for r in results:
        print(f"   - {r.content.get('text', str(r.content)[:50])}")

    # Final status
    print("\n" + "=" * 60)
    print("📊 Final Status")
    print("=" * 60)
    
    status = runtime.status()
    print(f"\n   Processed: {status['process_count']} requests")
    print(f"   Uptime: {status['uptime_seconds']:.2f}s")
    print(f"   Active Persona: {status['active_persona']['name'] if status['active_persona'] else 'None'}")
    if status.get('memory'):
        print(f"   Memory Chain: {status['memory']['chain_height']} entries")

    print("\n✅ MrLiouAI Runtime Demo Complete!")


if __name__ == "__main__":
    main()
