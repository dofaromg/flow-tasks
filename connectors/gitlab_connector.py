"""
GitLab Connector
GitLab 連接器
"""

from typing import Dict, List, Optional, Any

from .base_connector import BaseConnector, ConnectorStatus, ConnectorConfig


class GitLabConnector(BaseConnector):
    """GitLab API connector / GitLab API 連接器"""
    
    @property
    def service_name(self) -> str:
        return "GitLab"
    
    @property
    def service_url(self) -> str:
        # Allow custom GitLab instance
        return self.config.custom_settings.get("instance_url", "https://gitlab.com/api/v4")
    
    @property
    def required_scopes(self) -> List[str]:
        return ["api", "read_repository", "write_repository"]
    
    def authenticate(self) -> bool:
        """Authenticate with GitLab API / 使用 GitLab API 進行身份驗證"""
        return self._default_authenticate()
    
    def check_connection(self) -> bool:
        """Check GitLab API connection / 檢查 GitLab API 連接"""
        def extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "username": data.get("username"),
                "email": data.get("email"),
                "instance": self.service_url
            }
        
        return self._check_connection_with_request(
            endpoint="user",
            extract_metadata=extract_metadata
        )
    
    def get_auth_url(self) -> Optional[str]:
        """Get OAuth authorization URL / 獲取 OAuth 授權 URL"""
        base_url = self.config.custom_settings.get("instance_url", "https://gitlab.com")
        return f"{base_url.replace('/api/v4', '')}/-/profile/personal_access_tokens"
    
    def sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        """Sync GitLab data / 同步 GitLab 數據"""
        return self._default_sync_data(direction)
