"""
Dropbox Connector
Dropbox 連接器
"""

from typing import Dict, List, Optional, Any

from .base_connector import BaseConnector, ConnectorStatus, ConnectorConfig


class DropboxConnector(BaseConnector):
    """Dropbox API connector / Dropbox API 連接器"""
    
    @property
    def service_name(self) -> str:
        return "Dropbox"
    
    @property
    def service_url(self) -> str:
        return "https://api.dropboxapi.com/2"
    
    @property
    def required_scopes(self) -> List[str]:
        return ["files.metadata.read", "files.content.read", "files.content.write"]
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Dropbox-specific headers / 獲取 Dropbox 特定標頭"""
        headers = super()._get_auth_headers()
        headers["Content-Type"] = "application/json"
        return headers
    
    def authenticate(self) -> bool:
        """Authenticate with Dropbox API / 使用 Dropbox API 進行身份驗證"""
        return self._default_authenticate()
    
    def check_connection(self) -> bool:
        """Check Dropbox API connection / 檢查 Dropbox API 連接"""
        def extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "account_id": data.get("account_id"),
                "email": data.get("email")
            }
        
        # Dropbox uses POST for this endpoint
        return self._check_connection_with_request(
            endpoint="users/get_current_account",
            method="POST",
            json_data=None,
            extract_metadata=extract_metadata
        )
    
    def get_auth_url(self) -> Optional[str]:
        """Get OAuth authorization URL / 獲取 OAuth 授權 URL"""
        return "https://www.dropbox.com/developers/apps"
    
    def sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        """Sync Dropbox data / 同步 Dropbox 數據"""
        return self._default_sync_data(direction)
