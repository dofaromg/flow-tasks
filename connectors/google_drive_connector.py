"""
Google Drive Connector
Google Drive 連接器
"""

from typing import Dict, List, Optional, Any

from .base_connector import BaseConnector, ConnectorStatus, ConnectorConfig


class GoogleDriveConnector(BaseConnector):
    """Google Drive API connector / Google Drive API 連接器"""
    
    @property
    def service_name(self) -> str:
        return "Google Drive"
    
    @property
    def service_url(self) -> str:
        return "https://www.googleapis.com/drive/v3"
    
    @property
    def required_scopes(self) -> List[str]:
        return [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/drive.file"
        ]
    
    def authenticate(self) -> bool:
        """Authenticate with Google Drive API / 使用 Google Drive API 進行身份驗證"""
        return self._default_authenticate()
    
    def check_connection(self) -> bool:
        """Check Google Drive API connection / 檢查 Google Drive API 連接"""
        def extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "user_email": data.get("user", {}).get("emailAddress"),
                "storage_used": data.get("storageQuota", {}).get("usage")
            }
        
        return self._check_connection_with_request(
            endpoint="about",
            params={"fields": "user,storageQuota"},
            extract_metadata=extract_metadata
        )
    
    def get_auth_url(self) -> Optional[str]:
        """Get OAuth authorization URL / 獲取 OAuth 授權 URL"""
        return "https://console.cloud.google.com/apis/credentials"
    
    def sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        """Sync Google Drive data / 同步 Google Drive 數據"""
        return self._default_sync_data(direction)
