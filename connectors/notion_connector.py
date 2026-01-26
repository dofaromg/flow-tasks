"""
Notion Connector
Notion 連接器

Integration with Notion API for page and database management
整合 Notion API 用於頁面和數據庫管理
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

from .base_connector import BaseConnector, ConnectorStatus, ConnectorConfig, AuthType


class NotionConnector(BaseConnector):
    """Notion API connector / Notion API 連接器"""
    
    @property
    def service_name(self) -> str:
        return "Notion"
    
    @property
    def service_url(self) -> str:
        return "https://api.notion.com/v1"
    
    @property
    def required_scopes(self) -> List[str]:
        return ["read_content", "update_content", "insert_content"]
    
    def authenticate(self) -> bool:
        """Authenticate with Notion API / 使用 Notion API 進行身份驗證"""
        token = self.config.credentials.get("token")
        if not token:
            self.health.status = ConnectorStatus.NOT_CONFIGURED
            self.health.error_message = "Notion token not configured"
            return False
        
        self.health.status = ConnectorStatus.AUTHENTICATING
        return self.check_connection()
    
    def check_connection(self) -> bool:
        """Check Notion API connection / 檢查 Notion API 連接"""
        token = self.config.credentials.get("token")
        if not token:
            self.health.status = ConnectorStatus.NOT_CONFIGURED
            return False
        
        try:
            start_time = time.time()
            headers = {
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.service_url}/users/me",
                headers=headers,
                timeout=self.config.timeout
            )
            
            latency = (time.time() - start_time) * 1000
            self.health.latency_ms = latency
            self.health.last_check = datetime.now()
            
            if response.status_code == 200:
                self.health.status = ConnectorStatus.CONNECTED
                self.health.last_success = datetime.now()
                user_data = response.json()
                self.health.metadata = {
                    "user_id": user_data.get("id"),
                    "user_type": user_data.get("type")
                }
                return True
            elif response.status_code == 401:
                self.health.status = ConnectorStatus.ERROR
                self.health.error_message = "Invalid or expired token"
                return False
            else:
                self.health.status = ConnectorStatus.ERROR
                self.health.error_message = f"HTTP {response.status_code}"
                return False
                
        except requests.exceptions.Timeout:
            self.health.status = ConnectorStatus.ERROR
            self.health.error_message = "Connection timeout"
            return False
        except Exception as e:
            self.health.status = ConnectorStatus.ERROR
            self.health.error_message = str(e)
            return False
    
    def get_auth_url(self) -> Optional[str]:
        """Get OAuth authorization URL / 獲取 OAuth 授權 URL"""
        return "https://www.notion.so/my-integrations"
    
    def sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        """Sync Notion data / 同步 Notion 數據"""
        if not self.check_connection():
            return {"success": False, "error": "Not connected"}
        
        return {
            "success": True,
            "direction": direction,
            "timestamp": datetime.now().isoformat(),
            "items_synced": 0
        }
