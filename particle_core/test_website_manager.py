"""
Test suite for WebsiteManager
網站管家測試套件
"""

import os
import sys
import json
import tempfile
import shutil

# Add particle_core/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from website_manager import WebsiteManager


# Sample conversation data for testing
SAMPLE_CONVERSATION = [
    {"role": "user", "content": "測試問題"},
    {"role": "assistant", "content": "測試回答"}
]


def test_manager_initialization():
    """測試管家初始化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WebsiteManager(workspace_dir=tmpdir)
        
        assert manager is not None
        assert os.path.exists(manager.projects_dir)
        assert os.path.exists(manager.backups_dir)
        assert os.path.exists(manager.config_file)


def test_create_project():
    """測試建立專案"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WebsiteManager(workspace_dir=tmpdir)
        
        project_id = manager.create_project(
            project_name="測試專案",
            conversation=SAMPLE_CONVERSATION,
            metadata={"title": "Test", "date": "2026-01-10"}
        )
        
        assert project_id is not None
        assert project_id in manager.config["projects"]
        
        project = manager.get_project(project_id)
        assert project["project_name"] == "測試專案"
        assert len(project["themes"]) == 6


def test_list_projects():
    """測試列出專案"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WebsiteManager(workspace_dir=tmpdir)
        
        # 建立兩個專案
        project_id1 = manager.create_project(
            "專案1", SAMPLE_CONVERSATION
        )
        project_id2 = manager.create_project(
            "專案2", SAMPLE_CONVERSATION
        )
        
        # Redirect stdout to suppress output
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            projects = manager.list_projects()
        
        assert len(projects) == 2


def test_get_project():
    """測試取得專案"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WebsiteManager(workspace_dir=tmpdir)
        
        project_id = manager.create_project(
            "測試專案", SAMPLE_CONVERSATION
        )
        
        project = manager.get_project(project_id)
        assert project is not None
        assert project["project_id"] == project_id
        
        # 測試取得不存在的專案
        assert manager.get_project("non_existent") is None


def test_backup_project():
    """測試備份專案"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WebsiteManager(workspace_dir=tmpdir)
        
        project_id = manager.create_project(
            "測試專案", SAMPLE_CONVERSATION
        )
        
        backup_path = manager.backup_project(project_id)
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.endswith('.zip')


def test_update_project_theme():
    """測試更新專案主題"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WebsiteManager(workspace_dir=tmpdir)
        
        project_id = manager.create_project(
            "測試專案", SAMPLE_CONVERSATION
        )
        
        original_version = manager.get_project(project_id)["version"]
        
        manager.update_project_theme(project_id, "ocean")
        
        project = manager.get_project(project_id)
        assert project["version"] == original_version + 1


def test_delete_project():
    """測試刪除專案"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WebsiteManager(workspace_dir=tmpdir)
        
        project_id = manager.create_project(
            "測試專案", SAMPLE_CONVERSATION
        )
        
        # 確認專案存在
        assert project_id in manager.config["projects"]
        
        # 刪除專案
        manager.delete_project(project_id, confirm=True)
        
        # 確認專案已刪除
        assert project_id not in manager.config["projects"]
        
        # 確認有備份
        backups = [f for f in os.listdir(manager.backups_dir) if f.endswith('.zip')]
        assert len(backups) > 0


def test_get_statistics():
    """測試取得統計資訊"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WebsiteManager(workspace_dir=tmpdir)
        
        # 建立專案
        manager.create_project("專案1", SAMPLE_CONVERSATION)
        manager.create_project("專案2", SAMPLE_CONVERSATION)
        
        stats = manager.get_statistics()
        
        assert stats["total_projects"] == 2
        assert stats["total_conversations"] == 2
        # Each conversation has 2 messages
        assert stats["total_messages"] >= 4


def test_config_persistence():
    """測試配置持久化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 建立管家並新增專案
        manager1 = WebsiteManager(workspace_dir=tmpdir)
        project_id = manager1.create_project("專案1", SAMPLE_CONVERSATION)
        
        # 重新載入管家
        manager2 = WebsiteManager(workspace_dir=tmpdir)
        
        # 確認專案資訊被保留
        assert project_id in manager2.config["projects"]
        project = manager2.get_project(project_id)
        assert project["project_name"] == "專案1"


def test_cleanup_old_backups():
    """測試清理舊備份"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WebsiteManager(workspace_dir=tmpdir)
        manager.config["settings"]["max_backups"] = 3
        
        project_id = manager.create_project("專案1", SAMPLE_CONVERSATION)
        
        # 建立多個備份
        for i in range(5):
            manager.backup_project(project_id)
        
        # 檢查備份數量
        backups = [f for f in os.listdir(manager.backups_dir) if f.endswith('.zip')]
        assert len(backups) <= 3


# 執行測試
if __name__ == "__main__":
    print("🧪 執行網站管家測試...")
    print("=" * 60)
    
    test_functions = [
        test_manager_initialization,
        test_create_project,
        test_list_projects,
        test_get_project,
        test_backup_project,
        test_update_project_theme,
        test_delete_project,
        test_get_statistics,
        test_config_persistence,
        test_cleanup_old_backups,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"測試結果: {passed} 通過, {failed} 失敗")
    
    if failed == 0:
        print("✅ 所有測試通過！")
    else:
        print(f"⚠️  有 {failed} 個測試失敗")
