#!/usr/bin/env python3
"""
Context Management Example
上下文管理範例

Demonstrates how to use different context management strategies.
示範如何使用不同的上下文管理策略。
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
    RAGStrategy,
    HybridStrategy
)
from datetime import datetime


def example_1_workspace():
    """Example 1: Workspace Strategy for file-based context"""
    print("\n" + "="*60)
    print("Example 1: Workspace Strategy (工作桌面模式)")
    print("="*60)
    
    # Create workspace strategy
    workspace = WorkspaceStrategy(
        workspace_path="./",
        file_patterns=["*.py", "*.md"],
        ignore_patterns=[".git", "__pycache__"]
    )
    
    # Get workspace stats
    stats = workspace.get_workspace_stats()
    print(f"\n📁 Workspace: {stats['workspace_path']}")
    print(f"📄 Total files: {stats['total_files']}")
    print(f"📊 File types: {stats['file_types']}")
    
    # Search for files
    results = workspace.retrieve(query="context", limit=5)
    print(f"\n🔍 Search results for 'context': {len(results)} files found")
    for i, item in enumerate(results[:3], 1):
        print(f"  {i}. {item.metadata.get('path', 'unknown')}")
        print(f"     Size: {item.metadata.get('size', 0)} bytes")


def example_2_sliding_window():
    """Example 2: Sliding Window for conversation history"""
    print("\n" + "="*60)
    print("Example 2: Sliding Window Strategy (滑動視窗策略)")
    print("="*60)
    
    # Create sliding window
    window = SlidingWindowStrategy(
        window_size=10,
        overlap_size=2,
        prioritize_important=True
    )
    
    # Simulate conversation
    print("\n💬 Simulating conversation...")
    conversation = [
        ("user", "Hello! How are you?", 1),
        ("assistant", "I'm doing well, thank you! How can I help you today?", 1),
        ("user", "I need help with Python programming", 5),
        ("assistant", "I'd be happy to help with Python! What specific topic?", 5),
        ("user", "Context management strategies", 10),
        ("assistant", "Great topic! Let me explain the different strategies...", 10),
    ]
    
    for speaker, content, priority in conversation:
        item = ContextItem(
            id=f"{speaker}-{datetime.now().timestamp()}",
            content=content,
            metadata={"speaker": speaker},
            priority=priority
        )
        window.add(item)
        print(f"  {speaker}: {content[:50]}...")
    
    # Add more messages to test window sliding
    for i in range(10):
        window.add(ContextItem(
            id=f"msg-{i}",
            content=f"Additional message {i}",
            priority=1
        ))
    
    # Get window stats
    stats = window.get_window_stats()
    print(f"\n📊 Window stats:")
    print(f"  Current size: {stats['size']}/{stats['capacity']}")
    print(f"  Utilization: {stats['utilization']:.1%}")
    print(f"  Avg priority: {stats['avg_priority']:.1f}")
    
    # Retrieve recent items
    recent = window.retrieve(limit=5)
    print(f"\n📋 Recent items: {len(recent)}")
    for item in recent[:3]:
        print(f"  - {item.content[:50]}...")


def example_3_summary():
    """Example 3: Summary Strategy for long conversations"""
    print("\n" + "="*60)
    print("Example 3: Summary Strategy (摘要壓縮策略)")
    print("="*60)
    
    # Create summary strategy
    summary = SummaryStrategy(
        segment_size=5,
        preserve_recent=3,
        summary_ratio=0.3
    )
    
    # Add many items
    print("\n📝 Adding long conversation (30 items)...")
    for i in range(30):
        content = f"Discussion point {i}: This is important information about topic {i % 5}. "
        content += f"The meeting was on 2026-01-{(i % 28) + 1:02d} at {10 + (i % 8)}:00. "
        content += f"決定 was made regarding project phase {i // 10}."
        
        summary.add(ContextItem(
            id=f"item-{i}",
            content=content,
            priority=i % 10
        ))
    
    # Get compression stats
    stats = summary.get_compression_stats()
    print(f"\n📊 Compression stats:")
    print(f"  Original items: {stats['original_count']}")
    print(f"  Current items: {stats['total_items']}")
    print(f"  Summaries: {stats['summaries']}")
    print(f"  Recent items: {stats['recent_items']}")
    print(f"  Compression ratio: {stats['compression_ratio']:.1%}")
    print(f"  Using particle compression: {stats['use_particle_compression']}")
    
    # Retrieve and show summaries
    results = summary.retrieve(limit=5)
    print(f"\n📄 Retrieved items: {len(results)}")
    for i, item in enumerate(results[:2], 1):
        item_type = item.metadata.get('type', 'unknown')
        print(f"  {i}. Type: {item_type}")
        print(f"     Content: {item.content[:100]}...")


def example_4_rag():
    """Example 4: RAG Strategy for semantic search"""
    print("\n" + "="*60)
    print("Example 4: RAG Strategy (檢索增強生成策略)")
    print("="*60)
    
    # Create RAG strategy (lightweight TF-IDF version)
    rag = RAGStrategy(use_vector_db=False)
    
    # Add documents
    documents = [
        ("Python Programming Guide", "Python is a high-level programming language. It supports multiple paradigms."),
        ("Machine Learning Basics", "Machine learning is a subset of AI that learns from data patterns."),
        ("Web Development with Flask", "Flask is a lightweight Python web framework for building applications."),
        ("Data Science Tutorial", "Data science combines statistics, programming, and domain knowledge."),
        ("Neural Networks Overview", "Neural networks are computing systems inspired by biological brains."),
    ]
    
    print("\n📚 Indexing documents...")
    for title, content in documents:
        rag.add(ContextItem(
            id=f"doc-{title}",
            content=content,
            metadata={"title": title, "type": "document"}
        ))
    
    # Get search stats
    stats = rag.get_search_stats()
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Vocabulary size: {stats['vocabulary_size']}")
    print(f"  Using vector DB: {stats['use_vector_db']}")
    
    # Perform searches
    queries = ["Python programming", "machine learning", "web development"]
    
    for query in queries:
        results = rag.retrieve(query=query, limit=3)
        print(f"\n🔍 Search: '{query}'")
        print(f"  Found {len(results)} relevant documents:")
        for i, item in enumerate(results[:2], 1):
            print(f"    {i}. {item.metadata.get('title', 'Untitled')}")
            print(f"       Priority: {item.priority}")


def example_5_hybrid():
    """Example 5: Hybrid Strategy combining multiple approaches"""
    print("\n" + "="*60)
    print("Example 5: Hybrid Strategy (混合策略)")
    print("="*60)
    
    # Create individual strategies
    window = SlidingWindowStrategy(window_size=20)
    summary = SummaryStrategy(segment_size=5, preserve_recent=5)
    
    # Create hybrid strategy
    hybrid = HybridStrategy(
        strategies=[window, summary],
        weights=[0.6, 0.4],
        routing_rules={
            "recent": "SlidingWindowStrategy",
            "summary": "SummaryStrategy"
        }
    )
    
    print("\n🔗 Hybrid strategy created with:")
    print("  - SlidingWindowStrategy (weight: 0.6)")
    print("  - SummaryStrategy (weight: 0.4)")
    
    # Add items
    print("\n📝 Adding items to hybrid strategy...")
    for i in range(20):
        hybrid.add(ContextItem(
            id=f"item-{i}",
            content=f"Hybrid content item {i} with mixed information",
            priority=i % 5
        ))
    
    # Get performance metrics
    performance = hybrid.get_strategy_performance()
    print(f"\n📊 Strategy performance:")
    for strategy_name, metrics in performance.items():
        print(f"  {strategy_name}:")
        print(f"    Weight: {metrics['weight']:.1%}")
        print(f"    Total items: {metrics['total_items']}")
        print(f"    Utilization: {metrics['utilization']:.1%}")
    
    # Test routing
    print("\n🔍 Testing routing:")
    recent_results = hybrid.retrieve(query="recent items", limit=5)
    print(f"  Query 'recent items': {len(recent_results)} results")
    
    general_results = hybrid.retrieve(query="content", limit=5)
    print(f"  Query 'content': {len(general_results)} results")


def main():
    """Run all examples"""
    print("\n" + "🌟"*30)
    print("Context Management Strategies - Examples")
    print("上下文管理策略 - 範例")
    print("🌟"*30)
    
    try:
        example_1_workspace()
        example_2_sliding_window()
        example_3_summary()
        example_4_rag()
        example_5_hybrid()
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
