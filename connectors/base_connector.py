"""
Base Connector Class
基礎連接器類別

Abstract base class for all cloud service connectors
所有雲端服務連接器的抽象基類
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import hashlib
import json
import time

import requests


class ConnectorStatus(Enum):
    """Connector connection status / 連接器連接狀態"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    AUTHENTICATING = "authenticating"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"
    RATE_LIMITED = "rate_limited"


class AuthType(Enum):
    """Authentication type / 認證類型"""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    TOKEN = "token"
    BASIC = "basic_auth"
    CUSTOM = "custom"


@dataclass
class ConnectorConfig:
    """Connector configuration / 連接器配置"""
    enabled: bool = False
    auth_type: AuthType = AuthType.API_KEY
    credentials: Dict[str, str] = field(default_factory=dict)
    sync_enabled: bool = False
    agent_mode: bool = False
    rate_limit: Optional[int] = None
    timeout: int = 30
    retry_attempts: int = 3
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorHealth:
    """Connector health status / 連接器健康狀態"""
    status: ConnectorStatus
    last_check: datetime
    last_success: Optional[datetime] = None
    error_message: Optional[str] = None
    api_calls_today: int = 0
    rate_limit_remaining: Optional[int] = None
    latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    """
    Abstract base connector for cloud services
    雲端服務的抽象基礎連接器
    """
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.health = ConnectorHealth(
            status=ConnectorStatus.NOT_CONFIGURED,
            last_check=datetime.now()
        )
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """Service name / 服務名稱"""
        pass
    
    @property
    @abstractmethod
    def service_url(self) -> str:
        """Service base URL / 服務基礎 URL"""
        pass
    
    @property
    @abstractmethod
    def required_scopes(self) -> List[str]:
        """Required OAuth scopes / 需要的 OAuth 權限範圍"""
        pass
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the service
        與服務進行身份驗證
        
        Returns:
            bool: True if authentication successful
        """
        pass
    
    @abstractmethod
    def check_connection(self) -> bool:
        """
        Check if connection is active
        檢查連接是否活躍
        
        Returns:
            bool: True if connected
        """
        pass
    
    @abstractmethod
    def get_auth_url(self) -> Optional[str]:
        """
        Get OAuth authorization URL
        獲取 OAuth 授權 URL
        
        Returns:
            Optional[str]: Authorization URL or None if not OAuth
        """
        pass
    
    @abstractmethod
    def sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        """
        Sync data with service
        與服務同步數據
        
        Args:
            direction: "pull", "push", or "bidirectional"
            
        Returns:
            Dict with sync results
        """
        pass
    
    def get_status_report(self) -> Dict[str, Any]:
        """
        Generate status report
        生成狀態報告
        
        Returns:
            Dict with comprehensive status information
        """
        return {
            "service": self.service_name,
            "status": self.health.status.value,
            "enabled": self.config.enabled,
            "sync_enabled": self.config.sync_enabled,
            "agent_mode": self.config.agent_mode,
            "auth_type": self.config.auth_type.value,
            "last_check": self.health.last_check.isoformat(),
            "last_success": self.health.last_success.isoformat() if self.health.last_success else None,
            "error": self.health.error_message,
            "rate_limit_remaining": self.health.rate_limit_remaining,
            "latency_ms": self.health.latency_ms,
            "metadata": self.health.metadata
        }
    
    def get_security_guidelines(self) -> Dict[str, List[str]]:
        """
        Get security guidelines for this connector
        獲取此連接器的安全指引
        
        Returns:
            Dict with security guidelines
        """
        return {
            "data_flow_monitoring": [
                "啟用請求日誌記錄 / Enable request logging",
                "監控異常流量模式 / Monitor abnormal traffic patterns",
                "定期審查存取記錄 / Regular access log review"
            ],
            "disconnection_mechanism": [
                "提供手動斷開功能 / Provide manual disconnect",
                "自動清除憑證 / Auto-clear credentials on disconnect",
                "撤銷 OAuth token / Revoke OAuth tokens"
            ],
            "compliance": [
                "遵守 GDPR 數據保護 / GDPR data protection compliance",
                "符合地區數據駐留要求 / Regional data residency compliance",
                "定期安全審計 / Regular security audits"
            ],
            "best_practices": [
                "使用最小權限原則 / Use least privilege principle",
                "啟用雙因素認證 / Enable 2FA where possible",
                "定期輪換 API 密鑰 / Regular API key rotation",
                "加密存儲憑證 / Encrypt stored credentials"
            ]
        }
    
    def _hash_credentials(self) -> str:
        """
        Generate hash of credentials for verification
        生成憑證哈希值用於驗證
        """
        cred_str = json.dumps(self.config.credentials, sort_keys=True)
        return hashlib.sha256(cred_str.encode()).hexdigest()[:16]

    # =========================================================================
    # Shared methods to reduce code duplication across connectors
    # 共享方法以減少連接器之間的程式碼重複
    # =========================================================================

    @property
    def credential_key(self) -> str:
        """
        Key used to retrieve the authentication token from credentials.
        Override this property if your connector uses a different key.
        用於從憑證中獲取認證令牌的鍵名。
        如果您的連接器使用不同的鍵，請覆蓋此屬性。
        """
        return "token"

    def _get_token(self) -> Optional[str]:
        """
        Get authentication token from credentials.
        從憑證中獲取認證令牌。
        
        Returns:
            Optional[str]: Token if available, None otherwise
        """
        return self.config.credentials.get(self.credential_key)

    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get default authentication headers.
        獲取預設的認證標頭。
        Override this method for custom header requirements.
        
        Returns:
            Dict[str, str]: Headers dictionary
        """
        token = self._get_token()
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
    ) -> requests.Response:
        """
        Make an HTTP request with timing information.
        執行帶有計時資訊的 HTTP 請求。
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Optional headers (merged with auth headers)
            params: Optional query parameters
            json_data: Optional JSON body
            
        Returns:
            requests.Response: The response object
        """
        start_time = time.time()
        
        # Merge auth headers with custom headers
        request_headers = self._get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        response = requests.request(
            method=method,
            url=url,
            headers=request_headers,
            params=params,
            json=json_data,
            timeout=self.config.timeout
        )
        
        latency = (time.time() - start_time) * 1000
        self.health.latency_ms = latency
        self.health.last_check = datetime.now()
        
        return response

    def _handle_connection_success(self, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Handle successful connection.
        處理成功的連接。
        
        Args:
            metadata: Optional metadata to store in health status
            
        Returns:
            bool: Always returns True
        """
        self.health.status = ConnectorStatus.CONNECTED
        self.health.last_success = datetime.now()
        self.health.error_message = None
        if metadata:
            self.health.metadata = metadata
        return True

    def _handle_connection_error(self, error_message: str) -> bool:
        """
        Handle connection error.
        處理連接錯誤。
        
        Args:
            error_message: Error message to store
            
        Returns:
            bool: Always returns False
        """
        self.health.status = ConnectorStatus.ERROR
        self.health.error_message = error_message
        return False

    def _handle_not_configured(self, message: Optional[str] = None) -> bool:
        """
        Handle not configured state.
        處理未配置狀態。
        
        Args:
            message: Optional custom error message
            
        Returns:
            bool: Always returns False
        """
        self.health.status = ConnectorStatus.NOT_CONFIGURED
        self.health.error_message = message or f"{self.service_name} token not configured"
        return False

    def _default_authenticate(self) -> bool:
        """
        Default authentication implementation.
        預設的認證實現。
        Checks for token and calls check_connection().
        
        Returns:
            bool: True if authentication successful
        """
        token = self._get_token()
        if not token:
            return self._handle_not_configured()
        
        self.health.status = ConnectorStatus.AUTHENTICATING
        return self.check_connection()

    def _default_sync_data(self, direction: str = "pull") -> Dict[str, Any]:
        """
        Default sync data implementation.
        預設的數據同步實現。
        
        Args:
            direction: "pull", "push", or "bidirectional"
            
        Returns:
            Dict with sync results
        """
        if not self.check_connection():
            return {"success": False, "error": "Not connected"}
        
        return {
            "success": True,
            "direction": direction,
            "timestamp": datetime.now().isoformat(),
            "items_synced": 0
        }

    def _check_connection_with_request(
        self,
        endpoint: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        extract_metadata: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        extract_rate_limit: Optional[Callable[[requests.Response], Optional[int]]] = None,
    ) -> bool:
        """
        Common implementation for check_connection.
        check_connection 的通用實現。
        
        Args:
            endpoint: API endpoint to check (relative to service_url)
            method: HTTP method to use
            headers: Optional additional headers
            params: Optional query parameters
            json_data: Optional JSON body
            extract_metadata: Optional function to extract metadata from response JSON
            extract_rate_limit: Optional function to extract rate limit from response
            
        Returns:
            bool: True if connected successfully
        """
        token = self._get_token()
        if not token:
            return self._handle_not_configured()
        
        try:
            url = f"{self.service_url}/{endpoint}" if endpoint else self.service_url
            response = self._make_request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json_data=json_data
            )
            
            if response.status_code == 200:
                metadata = {}
                if extract_metadata and response.text:
                    try:
                        metadata = extract_metadata(response.json())
                    except (json.JSONDecodeError, ValueError):
                        pass
                
                if extract_rate_limit:
                    self.health.rate_limit_remaining = extract_rate_limit(response)
                
                return self._handle_connection_success(metadata)
            elif response.status_code == 401:
                return self._handle_connection_error("Invalid or expired token")
            elif response.status_code == 403:
                return self._handle_connection_error("Access forbidden - check permissions")
            else:
                return self._handle_connection_error(f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            return self._handle_connection_error("Connection timeout")
        except requests.exceptions.ConnectionError:
            return self._handle_connection_error("Connection failed")
        except Exception as e:
            return self._handle_connection_error(str(e))
