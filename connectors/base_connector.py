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
from typing import Dict, List, Optional, Any
import hashlib
import json


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
