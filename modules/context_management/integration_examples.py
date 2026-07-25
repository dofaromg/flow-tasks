#!/usr/bin/env python3
"""
Integration Example with FlowCore and Process Tasks
與 FlowCore 和 Process Tasks 的整合範例

Demonstrates how to integrate context management strategies
with existing MrLiouAI systems.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.context_management import (
    ContextItem,
    WorkspaceStrategy,
    SlidingWindowStrategy,
    SummaryStrategy,
    HybridStrategy
)
from datetime import datetime


def integration_example_1_task_processing():
    """
    Example: Using context management in task processing
    範例：在任務處理中使用上下文管理
    """
    print("\n" + "="*60)
    print("Integration Example 1: Task Processing Context")
    print("整合範例 1：任務處理上下文")
    print("="*60)
    
    # Scenario: Processing multiple tasks with context
    # Use hybrid strategy for comprehensive context management
    
    workspace = WorkspaceStrategy(
        workspace_path="./tasks",
        file_patterns=["*.yaml", "*.json"]
    )
    
    history = SlidingWindowStrategy(window_size=20)
    
    hybrid = HybridStrategy(
        strategies=[workspace, history],
        weights=[0.7, 0.3]
    )
    
    print("\n📋 Task processing context manager created")
    print("  - Workspace: ./tasks (for task definitions)")
    print("  - History: Last 20 operations")
    
    # Simulate task processing
    tasks = [
        "Load task definitions",
        "Validate task structure",
        "Execute task logic",
        "Store results",
        "Update status"
    ]
    
    for i, task in enumerate(tasks):
        item = ContextItem(
            id=f"task-op-{i}",
            content=f"Operation: {task}",
            metadata={
                "type": "task_operation",
                "step": i + 1,
                "status": "completed"
            },
            priority=5
        )
        hybrid.add(item)
        print(f"  ✓ {task}")
    
    # Query context
    print("\n🔍 Query: Recent task operations")
    results = hybrid.retrieve(query="operation", limit=5)
    print(f"  Found {len(results)} relevant items")
    
    return hybrid


def integration_example_2_particle_compression():
    """
    Example: Using summary strategy with particle compression
    範例：使用摘要策略與粒子壓縮
    """
    print("\n" + "="*60)
    print("Integration Example 2: Particle Compression")
    print("整合範例 2：粒子壓縮")
    print("="*60)
    
    # Create summary strategy (automatically integrates with particle_core)
    summary = SummaryStrategy(
        segment_size=5,
        preserve_recent=3,
        summary_ratio=0.3
    )
    
    print("\n🔬 Summary strategy with particle compression")
    print(f"  Using particle compression: {summary.use_particle}")
    
    # Simulate particle language execution flow
    particle_operations = [
        "STRUCTURE: Define input data structure",
        "MARK: Establish logic jump points",
        "FLOW: Transform to flow structure",
        "RECURSE: Expand into detailed structure",
        "STORE: Archive to logic memory"
    ]
    
    # Add multiple rounds of operations
    for round_num in range(4):
        print(f"\n  Round {round_num + 1}: Executing particle pipeline...")
        for i, op in enumerate(particle_operations):
            item = ContextItem(
                id=f"particle-r{round_num}-{i}",
                content=f"Round {round_num + 1} - {op}",
                metadata={
                    "round": round_num + 1,
                    "step": i + 1,
                    "type": "particle_operation"
                },
                priority=5 - i
            )
            summary.add(item)
    
    # Get compression stats
    stats = summary.get_compression_stats()
    print(f"\n📊 Compression results:")
    print(f"  Original operations: {stats['original_count']}")
    print(f"  Compressed to: {stats['total_items']} items")
    print(f"  Compression ratio: {stats['compression_ratio']:.1%}")
    print(f"  Summaries created: {stats['summaries']}")
    
    # Retrieve summaries
    summaries = [item for item in summary.context_items 
                 if item.metadata.get('type') == 'summary']
    
    if summaries:
        print(f"\n📝 Sample summary:")
        sample = summaries[0]
        print(f"  {sample.content[:100]}...")
    
    return summary


def integration_example_3_conversation_memory():
    """
    Example: Managing conversation memory
    範例：管理對話記憶
    """
    print("\n" + "="*60)
    print("Integration Example 3: Conversation Memory")
    print("整合範例 3：對話記憶")
    print("="*60)
    
    # Use sliding window for recent conversation
    window = SlidingWindowStrategy(
        window_size=30,
        overlap_size=5,
        prioritize_important=True
    )
    
    print("\n💭 Conversation memory manager")
    print("  Window size: 30 messages")
    print("  Overlap: 5 messages")
    
    # Simulate conversation with MrLiouAI
    conversation = [
        ("user", "請幫我實作上下文管理策略", 10),
        ("assistant", "好的，我會實作五種策略：Workspace、SlidingWindow、Summary、RAG、Hybrid", 10),
        ("user", "請先實作基礎策略", 8),
        ("assistant", "已完成 base_strategy.py，包含 ContextItem 和 BaseStrategy", 8),
        ("user", "測試通過了嗎？", 7),
        ("assistant", "是的，所有 69 個測試都通過了", 9),
        ("user", "效能如何？", 6),
        ("assistant", "所有策略都在 1 秒內處理 1000 個項目", 9),
    ]
    
    print("\n💬 Simulating conversation...")
    for speaker, message, priority in conversation:
        item = ContextItem(
            id=f"{speaker}-{datetime.now().timestamp()}",
            content=message,
            metadata={"speaker": speaker, "language": "zh"},
            priority=priority
        )
        window.add(item)
    
    # Get conversation context
    context = window.retrieve(limit=10)
    print(f"\n📋 Current context: {len(context)} messages")
    
    # Important messages (high priority)
    important = [msg for msg in context if msg.priority >= 8]
    print(f"  Important messages: {len(important)}")
    for msg in important[:3]:
        print(f"    • {msg.metadata['speaker']}: {msg.content[:40]}...")
    
    return window


def integration_example_4_knowledge_base():
    """
    Example: Building knowledge base with workspace + RAG
    範例：使用 Workspace + RAG 建立知識庫
    """
    print("\n" + "="*60)
    print("Integration Example 4: Knowledge Base")
    print("整合範例 4：知識庫")
    print("="*60)
    
    from modules.context_management import RAGStrategy
    
    # Combine workspace and RAG for knowledge management
    workspace = WorkspaceStrategy(
        workspace_path="./particle_core/docs",
        file_patterns=["*.md", "*.txt"]
    )
    
    rag = RAGStrategy(use_vector_db=False)
    
    hybrid = HybridStrategy(
        strategies=[workspace, rag],
        weights=[0.5, 0.5],
        routing_rules={
            "file": "WorkspaceStrategy",
            "search": "RAGStrategy"
        }
    )
    
    print("\n📚 Knowledge base manager created")
    print("  - Workspace: ./particle_core/docs")
    print("  - RAG: Semantic search enabled")
    
    # Index some knowledge
    knowledge_items = [
        "粒子語言核心系統實作了邏輯鏈執行",
        "記憶封存種子用於狀態持久化",
        "上下文管理策略優化 AI 對話記憶",
        "Workspace 策略是推薦的檔案管理方法",
        "Summary 策略整合粒子壓縮邏輯"
    ]
    
    for i, content in enumerate(knowledge_items):
        rag.add(ContextItem(
            id=f"kb-{i}",
            content=content,
            metadata={"type": "knowledge", "source": "system"}
        ))
    
    print(f"\n  Indexed {len(knowledge_items)} knowledge items")
    
    # Query knowledge
    queries = ["粒子語言", "記憶管理", "檔案策略"]
    
    for query in queries:
        results = hybrid.retrieve(query=query, limit=3)
        print(f"\n🔍 Query: '{query}'")
        print(f"  Results: {len(results)}")
        if results:
            print(f"    Top: {results[0].content[:50]}...")
    
    return hybrid


def main():
    """Run all integration examples"""
    print("\n" + "🌐"*30)
    print("Context Management - Integration Examples")
    print("上下文管理 - 整合範例")
    print("🌐"*30)
    
    try:
        # Example 1: Task processing
        task_context = integration_example_1_task_processing()
        
        # Example 2: Particle compression
        particle_summary = integration_example_2_particle_compression()
        
        # Example 3: Conversation memory
        conversation_memory = integration_example_3_conversation_memory()
        
        # Example 4: Knowledge base
        knowledge_base = integration_example_4_knowledge_base()
        
        print("\n" + "="*60)
        print("✅ All integration examples completed!")
        print("="*60)
        
        print("\n📊 Summary:")
        print(f"  Task context items: {len(task_context.context_items)}")
        print(f"  Particle compressions: {len(particle_summary.summaries)}")
        print(f"  Conversation messages: {len(conversation_memory.context_items)}")
        print(f"  Knowledge base items: {len(knowledge_base.context_items)}")
        
        print("\n✨ Ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
