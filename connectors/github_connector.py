"""
GitHub Connector
GitHub 連接器

Integration with GitHub API for repository and workflow management
整合 GitHub API 用於倉庫和工作流程管理
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

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
    
    def authenticate(self) -> bool:
        """Authenticate with GitHub API / 使用 GitHub API 進行身份驗證"""
        token = self.config.credentials.get("token")
        if not token:
            self.health.status = ConnectorStatus.NOT_CONFIGURED
            self.health.error_message = "GitHub token not configured"
            return False
        
        self.health.status = ConnectorStatus.AUTHENTICATING
        return self.check_connection()
    
    def check_connection(self) -> bool:
        """Check GitHub API connection / 檢查 GitHub API 連接"""
        token = self.config.credentials.get("token")
        if not token:
            self.health.status = ConnectorStatus.NOT_CONFIGURED
            return False
        
        try:
            start_time = time.time()
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(
                f"{self.service_url}/user",
                headers=headers,
                timeout=self.config.timeout
            )
            
            latency = (time.time() - start_time) * 1000
            self.health.latency_ms = latency
            self.health.last_check = datetime.now()
            
            if response.status_code == 200:
                self.health.status = ConnectorStatus.CONNECTED
                self.health.last_success = datetime.now()
                
                # Parse rate limit
                self.health.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                self.health.metadata = {
                    "user": response.json().get("login"),
                    "rate_limit": response.headers.get('X-RateLimit-Limit'),
                    "rate_reset": response.headers.get('X-RateLimit-Reset')
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
        # GitHub uses personal access tokens for API access
        return "https://github.com/settings/tokens/new"
    
    def sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        """Sync GitHub data / 同步 GitHub 數據"""
        if not self.check_connection():
            return {"success": False, "error": "Not connected"}
        
        # Implementation for syncing repos, issues, PRs, etc.
        return {
            "success": True,
            "direction": direction,
            "timestamp": datetime.now().isoformat(),
            "items_synced": 0
        }
