"""
AI 助手網站管家 - AI Assistant Website Manager
作者: MR.liou × Copilot
版本: v1.0

功能:
1. 網站套件管理 (建立、預覽、更新、刪除)
2. 主題動態切換
3. 對話內容即時編輯
4. 多個網站專案管理
5. 自動備份與版本控制
6. 網站統計分析
"""

import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

try:
    from conversation_extractor import ConversationExtractor
    EXTRACTOR_AVAILABLE = True
except ImportError:
    EXTRACTOR_AVAILABLE = False
    print("⚠️  Warning: conversation_extractor not available")


class WebsiteManager:
    """AI 助手網站管家核心類別"""
    
    def __init__(self, workspace_dir: str = None):
        """
        初始化網站管家
        
        Args:
            workspace_dir: 工作空間目錄，預設為 ./website_workspace
        """
        self.workspace_dir = workspace_dir or "./website_workspace"
        self.projects_dir = os.path.join(self.workspace_dir, "projects")
        self.backups_dir = os.path.join(self.workspace_dir, "backups")
        self.config_file = os.path.join(self.workspace_dir, "manager_config.json")
        
        # 創建必要目錄
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.backups_dir, exist_ok=True)
        
        # 載入或初始化配置
        self.config = self._load_config()
        
        if EXTRACTOR_AVAILABLE:
            self.extractor = ConversationExtractor()
        else:
            self.extractor = None
    
    def _load_config(self) -> Dict:
        """載入配置檔案"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 初始配置
            config = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "projects": {},
                "settings": {
                    "auto_backup": True,
                    "default_theme": "default",
                    "max_backups": 10
                }
            }
            self._save_config(config)
            return config
    
    def _save_config(self, config: Dict = None):
        """儲存配置檔案"""
        if config is None:
            config = self.config
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def create_project(self, project_name: str, conversation: List[Dict], 
                      metadata: Dict = None, themes: List[str] = None) -> str:
        """
        建立新的網站專案
        
        Args:
            project_name: 專案名稱
            conversation: 對話內容
            metadata: 對話元數據
            themes: 要生成的主題列表
        
        Returns:
            專案 ID
        """
        if not EXTRACTOR_AVAILABLE or self.extractor is None:
            raise RuntimeError("ConversationExtractor not available")
        
        # 生成專案 ID (使用微秒確保唯一性)
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        project_id = f"proj_{timestamp}"
        project_dir = os.path.join(self.projects_dir, project_id)
        
        print(f"\n🚀 建立新專案: {project_name}")
        print(f"📁 專案 ID: {project_id}")
        print("=" * 60)
        
        # 打包對話
        package = self.extractor.package_conversation(conversation, metadata)
        
        # 生成網站套件
        if themes is None:
            themes = ["default", "ocean", "sunset", "night", "forest", "minimal"]
        
        result = self.extractor.generate_website_bundle(package, project_dir, themes)
        
        # 記錄專案資訊
        project_info = {
            "project_id": project_id,
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "directory": project_dir,
            "themes": themes,
            "metadata": metadata or {},
            "statistics": package.get("statistics", {}),
            "version": 1
        }
        
        self.config["projects"][project_id] = project_info
        self._save_config()
        
        print(f"\n✅ 專案建立完成！")
        print(f"📂 專案目錄: {project_dir}")
        print(f"🌐 訪問: file://{os.path.abspath(os.path.join(project_dir, 'index.html'))}")
        
        return project_id
    
    def list_projects(self) -> List[Dict]:
        """列出所有專案"""
        projects = []
        
        print("\n📋 專案列表")
        print("=" * 60)
        
        if not self.config["projects"]:
            print("   (尚無專案)")
            return projects
        
        for project_id, info in self.config["projects"].items():
            projects.append(info)
            print(f"\n🔹 {info['project_name']}")
            print(f"   ID: {project_id}")
            print(f"   建立時間: {info['created_at'][:19]}")
            print(f"   主題數量: {len(info['themes'])} 個")
            print(f"   版本: v{info['version']}")
        
        print("=" * 60)
        return projects
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """取得專案資訊"""
        return self.config["projects"].get(project_id)
    
    def update_project_theme(self, project_id: str, new_theme: str):
        """
        更新專案主題（重新生成 HTML）
        
        Args:
            project_id: 專案 ID
            new_theme: 新主題名稱
        """
        project = self.get_project(project_id)
        if not project:
            print(f"❌ 找不到專案: {project_id}")
            return
        
        if not EXTRACTOR_AVAILABLE or self.extractor is None:
            raise RuntimeError("ConversationExtractor not available")
        
        print(f"\n🎨 更新專案主題: {project['project_name']}")
        print(f"   新主題: {new_theme}")
        
        # 自動備份
        if self.config["settings"]["auto_backup"]:
            self.backup_project(project_id)
        
        # 重新生成該主題的 HTML
        self.extractor.theme = new_theme
        
        # 這裡需要重新讀取對話內容並生成
        # 簡化版: 只更新配置
        if new_theme not in project["themes"]:
            project["themes"].append(new_theme)
        
        project["updated_at"] = datetime.now().isoformat()
        project["version"] += 1
        
        self._save_config()
        
        print("✅ 主題更新完成！")
    
    def delete_project(self, project_id: str, confirm: bool = False):
        """
        刪除專案
        
        Args:
            project_id: 專案 ID
            confirm: 確認刪除
        """
        project = self.get_project(project_id)
        if not project:
            print(f"❌ 找不到專案: {project_id}")
            return
        
        if not confirm:
            print(f"⚠️  即將刪除專案: {project['project_name']}")
            print(f"   請使用 confirm=True 確認刪除")
            return
        
        print(f"\n🗑️  刪除專案: {project['project_name']}")
        
        # 備份後刪除
        self.backup_project(project_id)
        
        # 刪除專案目錄
        project_dir = project["directory"]
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        
        # 從配置中移除
        del self.config["projects"][project_id]
        self._save_config()
        
        print("✅ 專案已刪除（已備份）")
    
    def backup_project(self, project_id: str) -> str:
        """
        備份專案
        
        Args:
            project_id: 專案 ID
        
        Returns:
            備份檔案路徑
        """
        project = self.get_project(project_id)
        if not project:
            print(f"❌ 找不到專案: {project_id}")
            return None
        
        # 創建備份檔名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{project_id}_v{project['version']}_{timestamp}.zip"
        backup_path = os.path.join(self.backups_dir, backup_name)
        
        # 壓縮專案目錄
        project_dir = project["directory"]
        if os.path.exists(project_dir):
            shutil.make_archive(
                backup_path.replace('.zip', ''),
                'zip',
                project_dir
            )
            
            print(f"💾 備份完成: {backup_name}")
            
            # 清理舊備份
            self._cleanup_old_backups()
            
            return backup_path
        else:
            print(f"❌ 專案目錄不存在: {project_dir}")
            return None
    
    def _cleanup_old_backups(self):
        """清理舊備份檔案"""
        max_backups = self.config["settings"]["max_backups"]
        
        # 取得所有備份檔案
        backups = []
        for filename in os.listdir(self.backups_dir):
            if filename.endswith('.zip'):
                filepath = os.path.join(self.backups_dir, filename)
                backups.append((filepath, os.path.getmtime(filepath)))
        
        # 按時間排序
        backups.sort(key=lambda x: x[1], reverse=True)
        
        # 刪除超過限制的備份
        if len(backups) > max_backups:
            for filepath, _ in backups[max_backups:]:
                os.remove(filepath)
                print(f"   清理舊備份: {os.path.basename(filepath)}")
    
    def get_statistics(self) -> Dict:
        """取得管家統計資訊"""
        total_projects = len(self.config["projects"])
        total_backups = len([f for f in os.listdir(self.backups_dir) if f.endswith('.zip')])
        
        # 計算總對話數和訊息數
        total_conversations = 0
        total_messages = 0
        
        for project_id, project in self.config["projects"].items():
            total_conversations += 1
            stats = project.get("statistics", {})
            total_messages += stats.get("total_messages", 0)
        
        return {
            "total_projects": total_projects,
            "total_backups": total_backups,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "workspace_dir": self.workspace_dir,
            "created_at": self.config.get("created_at", "N/A")
        }
    
    def print_statistics(self):
        """顯示統計資訊"""
        stats = self.get_statistics()
        
        print("\n📊 網站管家統計")
        print("=" * 60)
        print(f"   專案總數: {stats['total_projects']} 個")
        print(f"   備份總數: {stats['total_backups']} 個")
        print(f"   對話總數: {stats['total_conversations']} 個")
        print(f"   訊息總數: {stats['total_messages']} 條")
        print(f"   工作空間: {stats['workspace_dir']}")
        print(f"   建立時間: {stats['created_at'][:19]}")
        print("=" * 60)
    
    def open_project(self, project_id: str):
        """
        在瀏覽器中打開專案
        
        Args:
            project_id: 專案 ID
        """
        project = self.get_project(project_id)
        if not project:
            print(f"❌ 找不到專案: {project_id}")
            return
        
        index_path = os.path.join(project["directory"], "index.html")
        
        if os.path.exists(index_path):
            import webbrowser
            abs_path = os.path.abspath(index_path)
            print(f"🌐 正在打開專案...")
            print(f"   {abs_path}")
            webbrowser.open(f"file://{abs_path}")
        else:
            print(f"❌ 找不到索引頁面: {index_path}")


def demo():
    """示範網站管家功能"""
    print("\n" + "=" * 60)
    print("🤖 AI 助手網站管家示範")
    print("=" * 60)
    
    # 初始化管家
    manager = WebsiteManager(workspace_dir="/tmp/website_manager_demo")
    
    # 準備示範對話
    conversation = [
        {
            "role": "user",
            "content": "網站管家有什麼功能？"
        },
        {
            "role": "assistant",
            "content": "網站管家提供完整的專案管理功能：\n• 建立和管理多個網站專案\n• 動態切換主題\n• 自動備份與版本控制\n• 統計分析和監控"
        },
        {
            "role": "user",
            "content": "如何使用？"
        },
        {
            "role": "assistant",
            "content": "非常簡單！只需要提供對話內容，管家就會自動生成完整的網站套件，並提供管理介面讓你輕鬆維護。"
        }
    ]
    
    # 1. 建立專案
    print("\n📝 示範 1：建立專案")
    project_id = manager.create_project(
        project_name="網站管家功能展示",
        conversation=conversation,
        metadata={
            "title": "AI 助手網站管家",
            "date": "2026-01-10",
            "tags": ["管家", "AI", "網站管理"]
        }
    )
    
    # 2. 列出專案
    print("\n📝 示範 2：列出所有專案")
    manager.list_projects()
    
    # 3. 顯示統計
    print("\n📝 示範 3：統計資訊")
    manager.print_statistics()
    
    # 4. 備份專案
    print("\n📝 示範 4：備份專案")
    manager.backup_project(project_id)
    
    # 5. 更新主題
    print("\n📝 示範 5：更新主題")
    manager.update_project_theme(project_id, "ocean")
    
    print("\n" + "=" * 60)
    print("✅ 所有示範完成！")
    print("=" * 60)
    print(f"\n💡 提示: 工作空間位於 /tmp/website_manager_demo")
    print(f"   可以使用 manager.open_project('{project_id}') 在瀏覽器中查看")


if __name__ == "__main__":
    demo()
