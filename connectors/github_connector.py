"""
GitHub Connector
GitHub 連接器

Integration with GitHub API for repository and workflow management
整合 GitHub API 用於倉庫和工作流程管理
"""

from typing import Dict, List, Optional, Any

from .base_connector import BaseConnector, ConnectorStatus, ConnectorConfig, AuthType


class GitHubConnector(BaseConnector):
    """GitHub API connector / GitHub API 連接器"""
    
    @property
    def service_name(self) -> str:
        return "GitHub"
    
    @property
    def service_url(self) -> str:
        return "https://api.github.com"
    
    @property
    def required_scopes(self) -> List[str]:
        return ["repo", "workflow", "read:org"]
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get GitHub-specific headers / 獲取 GitHub 特定標頭"""
        headers = super()._get_auth_headers()
        headers["Accept"] = "application/vnd.github.v3+json"
        return headers
    
    def authenticate(self) -> bool:
        """Authenticate with GitHub API / 使用 GitHub API 進行身份驗證"""
        return self._default_authenticate()
    
    def check_connection(self) -> bool:
        """Check GitHub API connection / 檢查 GitHub API 連接"""
        def extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
            return {"user": data.get("login")}
        
        def extract_rate_limit(response) -> Optional[int]:
            return int(response.headers.get('X-RateLimit-Remaining', 0))
        
        result = self._check_connection_with_request(
            endpoint="user",
            extract_metadata=extract_metadata,
            extract_rate_limit=extract_rate_limit
        )
        
        # Add extra metadata from headers after successful connection
        if result and hasattr(self, '_last_response_headers'):
            self.health.metadata.update({
                "rate_limit": self._last_response_headers.get('X-RateLimit-Limit'),
                "rate_reset": self._last_response_headers.get('X-RateLimit-Reset')
            })
        
        return result
    
    def get_auth_url(self) -> Optional[str]:
        """Get OAuth authorization URL / 獲取 OAuth 授權 URL"""
        return "https://github.com/settings/tokens/new"
    
    def sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        """Sync GitHub data / 同步 GitHub 數據"""
        return self._default_sync_data(direction)
