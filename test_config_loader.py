"""
Test Configuration Loader
測試配置加載器

Tests for the configuration loading and validation system.
"""

import pytest
import tempfile
from pathlib import Path
from config_loader import ConfigLoader, ConfigurationError, load_config


def test_load_config_from_default():
    """Test loading config from default location."""
    # This should find config.yaml or config.sample.yaml
    loader = ConfigLoader()
    config = loader.load()
    
    assert config is not None
    assert 'data_dir' in config
    print("✓ Loaded config from default location")


def test_load_config_with_path():
    """Test loading config from specific path."""
    loader = ConfigLoader('config.sample.yaml')
    config = loader.load()
    
    assert config is not None
    assert config['data_dir'] == 'data'
    print("✓ Loaded config from specific path")


def test_config_validation():
    """Test configuration validation."""
    # Create a temporary invalid config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: config\n")
        f.write("# missing data_dir\n")
        temp_path = f.name
    
    try:
        loader = ConfigLoader(temp_path)
        with pytest.raises(ConfigurationError, match="Missing required field: data_dir"):
            loader.load()
        print("✓ Config validation works correctly")
    finally:
        Path(temp_path).unlink()


def test_get_config_value():
    """Test getting config values with dot notation."""
    loader = ConfigLoader('config.sample.yaml')
    
    # Test simple key
    data_dir = loader.get('data_dir')
    assert data_dir == 'data'
    
    # Test nested key
    notion_enabled = loader.get('notion.enabled')
    assert notion_enabled is False
    
    # Test default value
    nonexistent = loader.get('nonexistent.key', 'default')
    assert nonexistent == 'default'
    
    print("✓ Get config value works correctly")


def test_helper_methods():
    """Test helper methods for common config values."""
    loader = ConfigLoader('config.sample.yaml')
    
    # Test data_dir
    data_dir = loader.get_data_dir()
    assert isinstance(data_dir, Path)
    
    # Test notion enabled
    assert loader.is_notion_enabled() is False
    
    # Test github enabled
    assert loader.is_github_enabled() is False
    
    # Test default context strategy
    strategy = loader.get_default_context_strategy()
    assert strategy == 'workspace'
    
    print("✓ Helper methods work correctly")


def test_context_strategy_config():
    """Test getting context strategy configuration."""
    loader = ConfigLoader('config.sample.yaml')
    
    # Test workspace strategy config
    workspace_config = loader.get_context_strategy_config('workspace')
    assert workspace_config['path'] == './workspace'
    assert workspace_config['watch_enabled'] is False
    
    # Test sliding_window strategy config
    window_config = loader.get_context_strategy_config('sliding_window')
    assert window_config['window_size'] == 50
    assert window_config['overlap_size'] == 5
    
    print("✓ Context strategy config retrieval works")


def test_create_context_strategy():
    """Test creating context management strategy instances."""
    loader = ConfigLoader('config.sample.yaml')
    
    # Test creating workspace strategy
    workspace = loader.create_context_strategy('workspace')
    assert workspace is not None
    assert hasattr(workspace, 'retrieve')
    print("✓ Created workspace strategy")
    
    # Test creating sliding window strategy
    sliding_window = loader.create_context_strategy('sliding_window')
    assert sliding_window is not None
    assert hasattr(sliding_window, 'add')
    print("✓ Created sliding_window strategy")
    
    # Test creating default strategy
    default = loader.create_context_strategy()
    assert default is not None
    print("✓ Created default strategy")


def test_convenience_function():
    """Test convenience load_config function."""
    config = load_config('config.sample.yaml')
    assert config is not None
    assert 'data_dir' in config
    print("✓ Convenience function works")


def test_invalid_config_path():
    """Test handling of invalid config path."""
    with pytest.raises(ConfigurationError, match="Config file not found"):
        ConfigLoader('nonexistent.yaml')
    print("✓ Invalid path handling works")


def test_invalid_strategy():
    """Test handling of invalid strategy name."""
    loader = ConfigLoader('config.sample.yaml')
    with pytest.raises(ConfigurationError, match="Unknown strategy"):
        loader.create_context_strategy('invalid_strategy')
    print("✓ Invalid strategy handling works")


if __name__ == '__main__':
    print("Testing Configuration Loader...")
    print("=" * 60)
    
    # Run tests manually for quick validation
    try:
        test_load_config_from_default()
        test_load_config_with_path()
        test_get_config_value()
        test_helper_methods()
        test_context_strategy_config()
        test_create_context_strategy()
        test_convenience_function()
        test_invalid_config_path()
        test_invalid_strategy()
        
        # Validation test needs to be run separately
        print("\nRunning validation test...")
        test_config_validation()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
