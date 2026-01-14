"""
Tests for Workspace Strategy
工作桌面策略測試
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from modules.context_management.workspace_strategy import WorkspaceStrategy
from modules.context_management.base_strategy import ContextItem


class TestWorkspaceStrategy:
    """Test WorkspaceStrategy"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_create_workspace_strategy(self, temp_workspace):
        """Test creating workspace strategy"""
        strategy = WorkspaceStrategy(workspace_path=temp_workspace)
        
        assert strategy.workspace_path.exists()
        assert len(strategy.file_index) == 0
    
    def test_scan_workspace(self, temp_workspace):
        """Test scanning workspace"""
        # Create test files
        Path(temp_workspace, "test1.txt").write_text("Test content 1")
        Path(temp_workspace, "test2.py").write_text("print('hello')")
        Path(temp_workspace, "test3.md").write_text("# Markdown")
        
        strategy = WorkspaceStrategy(workspace_path=temp_workspace)
        strategy.scan_workspace()
        
        assert strategy.get_file_count() == 3
    
    def test_file_patterns(self, temp_workspace):
        """Test file pattern filtering"""
        Path(temp_workspace, "test.py").write_text("Python")
        Path(temp_workspace, "test.txt").write_text("Text")
        Path(temp_workspace, "test.md").write_text("Markdown")
        
        # Only Python files
        strategy = WorkspaceStrategy(
            workspace_path=temp_workspace,
            file_patterns=['*.py']
        )
        
        assert strategy.get_file_count() == 1
    
    def test_ignore_patterns(self, temp_workspace):
        """Test ignore patterns"""
        Path(temp_workspace, "test.py").write_text("Python")
        Path(temp_workspace, ".hidden").write_text("Hidden")
        Path(temp_workspace, "test.pyc").write_text("Compiled")
        
        strategy = WorkspaceStrategy(workspace_path=temp_workspace)
        
        # .hidden and .pyc should be ignored
        assert strategy.get_file_count() == 1
    
    def test_retrieve_without_query(self, temp_workspace):
        """Test retrieving files without query"""
        Path(temp_workspace, "old.txt").write_text("Old content")
        Path(temp_workspace, "new.txt").write_text("New content")
        
        strategy = WorkspaceStrategy(workspace_path=temp_workspace)
        
        results = strategy.retrieve(limit=10)
        assert len(results) == 2
        assert all(isinstance(item, ContextItem) for item in results)
    
    def test_retrieve_with_query(self, temp_workspace):
        """Test retrieving files with query"""
        Path(temp_workspace, "python.py").write_text("Python code")
        Path(temp_workspace, "java.java").write_text("Java code")
        Path(temp_workspace, "readme.md").write_text("Documentation")
        
        strategy = WorkspaceStrategy(workspace_path=temp_workspace)
        
        # Search for "python"
        results = strategy.retrieve(query="python", limit=10)
        assert len(results) >= 1
        assert any("python" in item.content.lower() for item in results)
    
    def test_compress(self, temp_workspace):
        """Test compression"""
        Path(temp_workspace, "test1.txt").write_text("Content 1")
        Path(temp_workspace, "test2.txt").write_text("Content 2")
        
        strategy = WorkspaceStrategy(workspace_path=temp_workspace)
        
        compressed = strategy.compress()
        assert len(compressed) == 2
        
        # Compressed items should be lightweight references
        assert all("file_reference" in item.metadata.get("type", "") for item in compressed)
    
    def test_workspace_stats(self, temp_workspace):
        """Test workspace statistics"""
        Path(temp_workspace, "test.py").write_text("Python")
        Path(temp_workspace, "test.md").write_text("Markdown")
        
        strategy = WorkspaceStrategy(workspace_path=temp_workspace)
        
        stats = strategy.get_workspace_stats()
        assert stats['total_files'] == 2
        assert stats['total_size_bytes'] > 0
        assert '.py' in stats['file_types']
        assert '.md' in stats['file_types']
    
    def test_add_manual_item(self, temp_workspace):
        """Test manually adding context items"""
        strategy = WorkspaceStrategy(workspace_path=temp_workspace)
        
        item = ContextItem(id="manual-1", content="Manual content")
        strategy.add(item)
        
        assert len(strategy.context_items) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
