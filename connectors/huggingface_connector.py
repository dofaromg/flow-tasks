"""
HuggingFace Connector
HuggingFace 連接器
"""

from typing import Dict, List, Optional, Any

from .base_connector import BaseConnector, ConnectorStatus, ConnectorConfig


class HuggingFaceConnector(BaseConnector):
    """HuggingFace API connector / HuggingFace API 連接器"""
    
    @property
    def service_name(self) -> str:
        return "HuggingFace"
    
    @property
    def service_url(self) -> str:
        return "https://huggingface.co/api"
    
    @property
    def required_scopes(self) -> List[str]:
        return ["read", "write"]
    
    def authenticate(self) -> bool:
        """Authenticate with HuggingFace API / 使用 HuggingFace API 進行身份驗證"""
        return self._default_authenticate()
    
    def check_connection(self) -> bool:
        """Check HuggingFace API connection / 檢查 HuggingFace API 連接"""
        def extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "name": data.get("name"),
                "type": data.get("type"),
                "orgs": len(data.get("orgs", []))
            }
        
        return self._check_connection_with_request(
            endpoint="whoami-v2",
            extract_metadata=extract_metadata
        )
    
    def get_auth_url(self) -> Optional[str]:
        """Get OAuth authorization URL / 獲取 OAuth 授權 URL"""
        return "https://huggingface.co/settings/tokens"
    
    def sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        """Sync HuggingFace data / 同步 HuggingFace 數據"""
        return self._default_sync_data(direction)
