#!/usr/bin/env python3
"""
Configuration System Example
配置系統範例

Demonstrates how to use the configuration system with context management strategies.
展示如何使用配置系統與上下文管理策略。
"""

from pathlib import Path
from config_loader import ConfigLoader, get_config_loader, load_config
from modules.context_management import ContextItem
from datetime import datetime


def example_basic_config_loading():
    """
    Example 1: Basic Configuration Loading
    範例 1：基本配置加載
    """
    print("\n" + "=" * 60)
    print("Example 1: Basic Configuration Loading")
    print("範例 1：基本配置加載")
    print("=" * 60)
    
    # Method 1: Using convenience function (with fallback to sample)
    try:
        config = load_config()
    except Exception:
        # Fallback to sample config if config.yaml doesn't exist
        config = load_config('config.sample.yaml')
    print(f"✓ Loaded config: {config.get('data_dir', 'N/A')}")
    
    # Method 2: Using ConfigLoader class (uses automatic fallback)
    loader = ConfigLoader()  # Will search config.yaml, then config.sample.yaml
    data_dir = loader.get('data_dir')
    print(f"✓ Data directory: {data_dir}")
    
    # Method 3: Using factory function
    loader2 = get_config_loader()
    notion_enabled = loader2.get('notion.enabled')
    print(f"✓ Notion enabled: {notion_enabled}")


def example_context_strategy_from_config():
    """
    Example 2: Creating Context Strategy from Config
    範例 2：從配置創建上下文策略
    """
    print("\n" + "=" * 60)
    print("Example 2: Creating Context Strategy from Config")
    print("範例 2：從配置創建上下文策略")
    print("=" * 60)
    
    loader = ConfigLoader()
    
    # Get default strategy name
    default_strategy = loader.get_default_context_strategy()
    print(f"✓ Default strategy: {default_strategy}")
    
    # Create workspace strategy from config
    workspace = loader.create_context_strategy('workspace')
    print(f"✓ Created workspace strategy")
    
    # Check workspace path from config
    workspace_config = loader.get_context_strategy_config('workspace')
    print(f"  - Workspace path: {workspace_config.get('path')}")
    print(f"  - Watch enabled: {workspace_config.get('watch_enabled')}")
    print(f"  - File patterns: {workspace_config.get('file_patterns')}")


def example_workspace_strategy_usage():
    """
    Example 3: Using Workspace Strategy
    範例 3：使用工作空間策略
    """
    print("\n" + "=" * 60)
    print("Example 3: Using Workspace Strategy")
    print("範例 3：使用工作空間策略")
    print("=" * 60)
    
    loader = ConfigLoader()
    workspace = loader.create_context_strategy('workspace')
    
    # Retrieve Python files
    results = workspace.retrieve(query="python", limit=5)
    print(f"✓ Found {len(results)} Python-related files")
    
    for i, item in enumerate(results[:3], 1):
        if 'path' in item.metadata:
            print(f"  {i}. {item.metadata['path']}")


def example_sliding_window_strategy():
    """
    Example 4: Using Sliding Window Strategy
    範例 4：使用滑動視窗策略
    """
    print("\n" + "=" * 60)
    print("Example 4: Using Sliding Window Strategy")
    print("範例 4：使用滑動視窗策略")
    print("=" * 60)
    
    loader = ConfigLoader()
    window = loader.create_context_strategy('sliding_window')
    
    # Add conversation items
    for i in range(20):
        item = ContextItem(
            id=f"msg-{i}",
            content=f"This is message number {i} in the conversation",
            metadata={"speaker": "user" if i % 2 == 0 else "assistant"},
            timestamp=datetime.now(),
            priority=1 if i > 15 else 0  # Recent messages have higher priority
        )
        window.add(item)
    
    print(f"✓ Added 20 messages to sliding window")
    
    # Retrieve recent items
    recent = window.retrieve(limit=5)
    print(f"✓ Retrieved {len(recent)} recent items")
    for item in recent[:3]:
        print(f"  - {item.id}: {item.content[:50]}...")


def example_summary_strategy():
    """
    Example 5: Using Summary Strategy with Compression
    範例 5：使用摘要壓縮策略
    """
    print("\n" + "=" * 60)
    print("Example 5: Using Summary Strategy")
    print("範例 5：使用摘要壓縮策略")
    print("=" * 60)
    
    loader = ConfigLoader()
    summary = loader.create_context_strategy('summary')
    
    # Add many conversation items
    for i in range(30):
        item = ContextItem(
            id=f"conv-{i}",
            content=f"Conversation item {i} with detailed information about the topic being discussed",
            priority=i % 5
        )
        summary.add(item)
    
    print(f"✓ Added 30 conversation items")
    
    # Get compression stats
    stats = summary.get_compression_stats()
    print(f"✓ Compression stats:")
    print(f"  - Original count: {stats['original_count']}")
    print(f"  - Total items: {stats['total_items']}")
    print(f"  - Compression ratio: {stats['compression_ratio']:.2%}")


def example_hybrid_strategy():
    """
    Example 6: Using Hybrid Strategy
    範例 6：使用混合策略
    """
    print("\n" + "=" * 60)
    print("Example 6: Using Hybrid Strategy")
    print("範例 6：使用混合策略")
    print("=" * 60)
    
    loader = ConfigLoader()
    
    # Get hybrid config
    hybrid_config = loader.get_context_strategy_config('hybrid')
    print(f"✓ Hybrid strategy config:")
    print(f"  - Strategies: {hybrid_config.get('strategies')}")
    print(f"  - Weights: {hybrid_config.get('weights')}")
    print(f"  - Routing rules: {hybrid_config.get('routing_rules')}")
    
    # Create hybrid strategy
    hybrid = loader.create_context_strategy('hybrid')
    print(f"✓ Created hybrid strategy combining multiple approaches")


def example_data_directory_management():
    """
    Example 7: Data Directory Management
    範例 7：資料目錄管理
    """
    print("\n" + "=" * 60)
    print("Example 7: Data Directory Management")
    print("範例 7：資料目錄管理")
    print("=" * 60)
    
    loader = ConfigLoader()
    
    # Get data directory (creates if doesn't exist)
    data_dir = loader.get_data_dir()
    print(f"✓ Data directory: {data_dir}")
    print(f"  - Exists: {data_dir.exists()}")
    print(f"  - Is directory: {data_dir.is_dir()}")
    
    # Show what's in data directory
    if data_dir.exists():
        contents = list(data_dir.iterdir())
        if contents:
            print(f"  - Contents ({len(contents)} items):")
            for item in contents[:5]:
                print(f"    • {item.name}")
        else:
            print(f"  - Directory is empty")


def example_integration_flags():
    """
    Example 8: Integration Feature Flags
    範例 8：整合功能開關
    """
    print("\n" + "=" * 60)
    print("Example 8: Integration Feature Flags")
    print("範例 8：整合功能開關")
    print("=" * 60)
    
    loader = ConfigLoader()
    
    # Check integration features
    notion_enabled = loader.is_notion_enabled()
    github_enabled = loader.is_github_enabled()
    
    print(f"✓ Integration status:")
    print(f"  - Notion: {'Enabled ✅' if notion_enabled else 'Disabled ❌'}")
    print(f"  - GitHub: {'Enabled ✅' if github_enabled else 'Disabled ❌'}")
    
    if notion_enabled:
        notion_config = loader.get('notion')
        print(f"  - Notion database ID: {notion_config.get('database_id', 'Not set')}")
    
    if github_enabled:
        github_config = loader.get('github')
        print(f"  - GitHub config: {github_config}")


def example_custom_config_path():
    """
    Example 9: Loading from Specific Config Path
    範例 9：從特定配置路徑加載
    """
    print("\n" + "=" * 60)
    print("Example 9: Loading from Specific Config Path")
    print("範例 9：從特定配置路徑加載")
    print("=" * 60)
    
    # Load from a specific path (e.g., sample config)
    loader = ConfigLoader('config.sample.yaml')
    config = loader.load()
    
    print(f"✓ Loaded from specific path: config.sample.yaml")
    print(f"  - Data dir: {config.get('data_dir')}")
    print(f"  - Default strategy: {loader.get_default_context_strategy()}")


def main():
    """Run all examples."""
    print("\n" + "🚀 " * 20)
    print("Configuration System Examples")
    print("配置系統範例集")
    print("🚀 " * 20)
    
    try:
        example_basic_config_loading()
        example_context_strategy_from_config()
        example_workspace_strategy_usage()
        example_sliding_window_strategy()
        example_summary_strategy()
        example_hybrid_strategy()
        example_data_directory_management()
        example_integration_flags()
        example_custom_config_path()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("✅ 所有範例執行成功！")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
