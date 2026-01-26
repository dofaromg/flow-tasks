"""
Dropbox Connector
Dropbox 連接器
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

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
    
    def authenticate(self) -> bool:
        token = self.config.credentials.get("token")
        if not token:
            self.health.status = ConnectorStatus.NOT_CONFIGURED
            self.health.error_message = "Dropbox token not configured"
            return False
        
        self.health.status = ConnectorStatus.AUTHENTICATING
        return self.check_connection()
    
    def check_connection(self) -> bool:
        token = self.config.credentials.get("token")
        if not token:
            self.health.status = ConnectorStatus.NOT_CONFIGURED
            return False
        
        try:
            start_time = time.time()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.service_url}/users/get_current_account",
                headers=headers,
                json=None,
                timeout=self.config.timeout
            )
            
            latency = (time.time() - start_time) * 1000
            self.health.latency_ms = latency
            self.health.last_check = datetime.now()
            
            if response.status_code == 200:
                self.health.status = ConnectorStatus.CONNECTED
                self.health.last_success = datetime.now()
                account = response.json()
                self.health.metadata = {
                    "account_id": account.get("account_id"),
                    "email": account.get("email")
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
                
        except Exception as e:
            self.health.status = ConnectorStatus.ERROR
            self.health.error_message = str(e)
            return False
    
    def get_auth_url(self) -> Optional[str]:
        return "https://www.dropbox.com/developers/apps"
    
    def sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        if not self.check_connection():
            return {"success": False, "error": "Not connected"}
        
        return {
            "success": True,
            "direction": direction,
            "timestamp": datetime.now().isoformat(),
            "items_synced": 0
        }
