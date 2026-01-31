"""
Vercel Connector
Vercel 連接器
"""

from typing import Dict, List, Optional, Any

from .base_connector import BaseConnector, ConnectorStatus, ConnectorConfig


class VercelConnector(BaseConnector):
    """Vercel API connector / Vercel API 連接器"""
    
    @property
    def service_name(self) -> str:
        return "Vercel"
    
    @property
    def service_url(self) -> str:
        return "https://api.vercel.com"
    
    @property
    def required_scopes(self) -> List[str]:
        return ["deployments", "projects", "logs"]
    
    def authenticate(self) -> bool:
        """Authenticate with Vercel API / 使用 Vercel API 進行身份驗證"""
        return self._default_authenticate()
    
    def check_connection(self) -> bool:
        """Check Vercel API connection / 檢查 Vercel API 連接"""
        def extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
            user = data.get("user", {})
            return {
                "username": user.get("username"),
                "email": user.get("email")
            }
        
        return self._check_connection_with_request(
            endpoint="v2/user",
            extract_metadata=extract_metadata
        )
    
    def get_auth_url(self) -> Optional[str]:
        """Get OAuth authorization URL / 獲取 OAuth 授權 URL"""
        return "https://vercel.com/account/tokens"
    
    def sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        """Sync Vercel data / 同步 Vercel 數據"""
        return self._default_sync_data(direction)
