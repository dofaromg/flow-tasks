"""
Notion Connector
Notion 連接器

Integration with Notion API for page and database management
整合 Notion API 用於頁面和數據庫管理
"""

from typing import Dict, List, Optional, Any

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
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Notion-specific headers / 獲取 Notion 特定標頭"""
        headers = super()._get_auth_headers()
        headers["Notion-Version"] = "2022-06-28"
        headers["Content-Type"] = "application/json"
        return headers
    
    def authenticate(self) -> bool:
        """Authenticate with Notion API / 使用 Notion API 進行身份驗證"""
        return self._default_authenticate()
    
    def check_connection(self) -> bool:
        """Check Notion API connection / 檢查 Notion API 連接"""
        def extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "user_id": data.get("id"),
                "user_type": data.get("type")
            }
        
        return self._check_connection_with_request(
            endpoint="users/me",
            extract_metadata=extract_metadata
        )
    
    def get_auth_url(self) -> Optional[str]:
        """Get OAuth authorization URL / 獲取 OAuth 授權 URL"""
        return "https://www.notion.so/my-integrations"
    
    def sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        """Sync Notion data / 同步 Notion 數據"""
        return self._default_sync_data(direction)
