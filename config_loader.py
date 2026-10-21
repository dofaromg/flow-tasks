"""
Configuration Loader Module
配置加載模組

Provides utilities for loading and validating project configuration,
including integration with context management strategies.

提供專案配置加載和驗證工具，包括與上下文管理策略的整合。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class ConfigLoader:
    """
    Configuration loader with validation and defaults.
    配置加載器，支援驗證和預設值。
    """
    
    DEFAULT_CONFIG_FILES = [
        "config.yaml",
        "config/config.yaml",
        "config.sample.yaml",
    ]
    
    def __init__(self, config_path: Optional[Path | str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Optional path to configuration file.
                        If not provided, will search for default locations.
        """
        self.config_path = self._resolve_config_path(config_path)
        self._config: Optional[Dict[str, Any]] = None
    
    def _resolve_config_path(self, config_path: Optional[Path | str]) -> Path:
        """
        Resolve configuration file path.
        
        Args:
            config_path: User-provided path or None
            
        Returns:
            Resolved Path object
            
        Raises:
            ConfigurationError: If no valid config file is found
        """
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            raise ConfigurationError(f"Config file not found: {config_path}")
        
        # Search for default config files
        for default_path in self.DEFAULT_CONFIG_FILES:
            path = Path(default_path)
            if path.exists():
                return path
        
        raise ConfigurationError(
            f"No configuration file found. Searched: {', '.join(self.DEFAULT_CONFIG_FILES)}\n"
            f"Please create config.yaml from config.sample.yaml"
        )
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigurationError: If config cannot be loaded or is invalid
        """
        if self._config is not None:
            return self._config
        
        try:
            # Use a single open() call which implicitly checks existence and gets file handle
            with self.config_path.open('r', encoding='utf-8') as f:
                # Check file size from the file descriptor to prevent DoS
                f.seek(0, 2)  # Seek to end
                file_size = f.tell()
                f.seek(0)  # Seek back to beginning
                
                max_size = 10 * 1024 * 1024  # 10MB
                if file_size > max_size:
                    raise ConfigurationError(
                        f"Config file too large: {file_size} bytes (max: {max_size} bytes)"
                    )
                
                self._config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load config file: {e}")
        
        if self._config is None:
            raise ConfigurationError("Config file is empty")
        
        self._validate_config(self._config)
        return self._config
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration structure.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Validate data_dir
        if 'data_dir' not in config:
            raise ConfigurationError("Missing required field: data_dir")
        
        # Validate notion config
        if 'notion' in config:
            notion = config['notion']
            if not isinstance(notion, dict):
                raise ConfigurationError("notion must be a dictionary")
            if 'enabled' not in notion:
                raise ConfigurationError("notion.enabled is required")
        
        # Validate github config
        if 'github' in config:
            github = config['github']
            if not isinstance(github, dict):
                raise ConfigurationError("github must be a dictionary")
            if 'enabled' not in github:
                raise ConfigurationError("github.enabled is required")
        
        # Validate context_management config
        if 'context_management' in config:
            ctx_mgmt = config['context_management']
            if not isinstance(ctx_mgmt, dict):
                raise ConfigurationError("context_management must be a dictionary")
            
            if 'default_strategy' in ctx_mgmt:
                valid_strategies = ['workspace', 'sliding_window', 'summary', 'rag', 'hybrid']
                if ctx_mgmt['default_strategy'] not in valid_strategies:
                    raise ConfigurationError(
                        f"Invalid default_strategy: {ctx_mgmt['default_strategy']}. "
                        f"Must be one of: {', '.join(valid_strategies)}"
                    )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'notion.enabled')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        config = self.load()
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_data_dir(self) -> Path:
        """
        Get data directory path.
        
        Returns:
            Path to data directory
        """
        data_dir = self.get('data_dir', 'data')
        path = Path(data_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def is_notion_enabled(self) -> bool:
        """Check if Notion integration is enabled."""
        return self.get('notion.enabled', False)
    
    def is_github_enabled(self) -> bool:
        """Check if GitHub integration is enabled."""
        return self.get('github.enabled', False)
    
    def get_context_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific context management strategy.
        
        Args:
            strategy_name: Name of the strategy (workspace, sliding_window, etc.)
            
        Returns:
            Strategy configuration dictionary
        """
        return self.get(f'context_management.{strategy_name}', {})
    
    def get_default_context_strategy(self) -> str:
        """
        Get the default context management strategy name.
        
        Returns:
            Strategy name (defaults to 'workspace')
        """
        return self.get('context_management.default_strategy', 'workspace')
    
    def create_context_strategy(self, strategy_name: Optional[str] = None):
        """
        Create and configure a context management strategy instance.
        
        Args:
            strategy_name: Strategy to create, or None for default strategy
            
        Returns:
            Configured strategy instance
            
        Raises:
            ConfigurationError: If strategy cannot be created
        """
        from modules.context_management import (
            WorkspaceStrategy,
            SlidingWindowStrategy,
            SummaryStrategy,
            RAGStrategy,
            HybridStrategy,
        )
        
        if strategy_name is None:
            strategy_name = self.get_default_context_strategy()
        
        config = self.get_context_strategy_config(strategy_name)
        
        try:
            if strategy_name == 'workspace':
                workspace_path = config.get('path', './workspace')
                return WorkspaceStrategy(
                    workspace_path=workspace_path,
                    file_patterns=config.get('file_patterns', ['*.py', '*.md', '*.txt', '*.json', '*.yaml']),
                    ignore_patterns=config.get('ignore_patterns', ['.git', 'node_modules']),
                    watch_enabled=config.get('watch_enabled', False)
                )
            
            elif strategy_name == 'sliding_window':
                return SlidingWindowStrategy(
                    window_size=config.get('window_size', 50),
                    overlap_size=config.get('overlap_size', 5),
                    prioritize_important=config.get('prioritize_important', True),
                    max_tokens=config.get('max_tokens', 4096)
                )
            
            elif strategy_name == 'summary':
                return SummaryStrategy(
                    segment_size=config.get('segment_size', 10),
                    preserve_recent=config.get('preserve_recent', 5),
                    summary_ratio=config.get('summary_ratio', 0.3),
                    max_tokens=config.get('max_tokens', 4096)
                )
            
            elif strategy_name == 'rag':
                return RAGStrategy(
                    use_vector_db=config.get('use_vector_db', False),
                    model_name=config.get('model_name', 'all-MiniLM-L6-v2'),
                    max_tokens=config.get('max_tokens', 4096)
                )
            
            elif strategy_name == 'hybrid':
                strategies_config = config.get('strategies', ['workspace', 'sliding_window'])
                weights = config.get('weights', [0.6, 0.4])
                routing_rules = config.get('routing_rules', {})
                
                # Create sub-strategies
                strategies = []
                for sub_strategy_name in strategies_config:
                    strategies.append(self.create_context_strategy(sub_strategy_name))
                
                return HybridStrategy(
                    strategies=strategies,
                    weights=weights,
                    routing_rules=routing_rules
                )
            
            else:
                raise ConfigurationError(f"Unknown strategy: {strategy_name}")
                
        except Exception as e:
            raise ConfigurationError(f"Failed to create {strategy_name} strategy: {e}")


def load_config(config_path: Optional[Path | str] = None) -> Dict[str, Any]:
    """
    Convenience function to load configuration.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Configuration dictionary
    """
    loader = ConfigLoader(config_path)
    return loader.load()


def get_config_loader(config_path: Optional[Path | str] = None) -> ConfigLoader:
    """
    Get a ConfigLoader instance.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        ConfigLoader instance
    """
    return ConfigLoader(config_path)
