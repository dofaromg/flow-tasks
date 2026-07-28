"""
Connector Manager
連接器管理器
origin_signature: MrLiouWord
layer: L4 WORLD / 多雲端服務集中管理層

Centralized management for all cloud service connectors
所有雲端服務連接器的集中管理
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .base_connector import BaseConnector, ConnectorStatus, ConnectorConfig
from .github_connector import GitHubConnector
from .notion_connector import NotionConnector
from .dropbox_connector import DropboxConnector
from .google_drive_connector import GoogleDriveConnector
from .vercel_connector import VercelConnector
from .icloud_connector import ICloudConnector
from .gitlab_connector import GitLabConnector
from .huggingface_connector import HuggingFaceConnector


class ConnectorManager:
    """
    Centralized connector management system
    集中式連接器管理系統
    """
    
    SUPPORTED_SERVICES = {
        "github": GitHubConnector,
        "notion": NotionConnector,
        "dropbox": DropboxConnector,
        "google_drive": GoogleDriveConnector,
        "vercel": VercelConnector,
        "icloud": ICloudConnector,
        "gitlab": GitLabConnector,
        "huggingface": HuggingFaceConnector
    }
    
    def __init__(self, config_path: str = "config/connectors.yaml"):
        self.config_path = Path(config_path)
        self.connectors: Dict[str, BaseConnector] = {}
        self._load_config()
        self._initialize_connectors()
    
    def _load_config(self):
        """Load connector configuration / 載入連接器配置"""
        if not self.config_path.exists():
            self._create_default_config()
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def _create_default_config(self):
        """Create default configuration file / 創建預設配置文件"""
        default_config = {
            "version": "1.0",
            "connectors": {
                service: {
                    "enabled": False,
                    "auth_type": "api_key",
                    "sync_enabled": False,
                    "agent_mode": False,
                    "credentials": {}
                }
                for service in self.SUPPORTED_SERVICES.keys()
            }
        }
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(default_config, f, allow_unicode=True, sort_keys=False)
        
        self.config = default_config
    
    def _initialize_connectors(self):
        """Initialize all configured connectors / 初始化所有配置的連接器"""
        connectors_config = self.config.get("connectors", {})
        
        for service_name, connector_class in self.SUPPORTED_SERVICES.items():
            service_config = connectors_config.get(service_name, {})
            
            # Load credentials from environment if not in config
            credentials = service_config.get("credentials", {})
            self._load_env_credentials(service_name, credentials)
            
            config = ConnectorConfig(
                enabled=service_config.get("enabled", False),
                auth_type=service_config.get("auth_type", "api_key"),
                credentials=credentials,
                sync_enabled=service_config.get("sync_enabled", False),
                agent_mode=service_config.get("agent_mode", False),
                custom_settings=service_config.get("settings", {})
            )
            
            self.connectors[service_name] = connector_class(config)
    
    def _load_env_credentials(self, service_name: str, credentials: Dict):
        """Load credentials from environment variables / 從環境變數載入憑證"""
        env_var_map = {
            "github": "GITHUB_TOKEN",
            "notion": "NOTION_TOKEN",
            "dropbox": "DROPBOX_TOKEN",
            "google_drive": "GOOGLE_DRIVE_TOKEN",
            "vercel": "VERCEL_TOKEN",
            "icloud": "ICLOUD_TOKEN",
            "gitlab": "GITLAB_TOKEN",
            "huggingface": "HUGGINGFACE_TOKEN"
        }
        
        env_var = env_var_map.get(service_name)
        if env_var and os.getenv(env_var):
            credentials["token"] = os.getenv(env_var)
    
    def check_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        Check all connector connections
        檢查所有連接器連接
        
        Returns:
            Dict with status for all connectors
        """
        results = {}
        
        for service_name, connector in self.connectors.items():
            try:
                is_connected = connector.check_connection()
                results[service_name] = connector.get_status_report()
            except Exception as e:
                results[service_name] = {
                    "service": service_name,
                    "status": ConnectorStatus.ERROR.value,
                    "error": str(e)
                }
        
        return results
    
    def get_connector(self, service_name: str) -> Optional[BaseConnector]:
        """Get connector by service name / 根據服務名稱獲取連接器"""
        return self.connectors.get(service_name)
    
    def generate_comprehensive_report(self, output_path: str = "docs/CONNECTOR_SYSTEM_REPORT.md"):
        """
        Generate comprehensive connector system report
        生成全面的連接器系統報告
        """
        report_lines = [
            "# Cloud Service Connector System Report",
            "# 雲端服務連接器系統報告",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**生成時間:** {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            "",
            "## Executive Summary / 執行摘要",
            ""
        ]
        
        # Get all statuses
        statuses = self.check_all_connections()
        connected = sum(1 for s in statuses.values() if s.get("status") == "connected")
        total = len(statuses)
        
        report_lines.extend([
            f"**Total Services / 總服務數:** {total}",
            f"**Connected / 已連接:** {connected}",
            f"**Connection Rate / 連接率:** {connected/total*100:.1f}%",
            "",
            "## Service Status Overview / 服務狀態概覽",
            "",
            "| Service | Status | Auth Type | Sync | Agent | Last Check |",
            "|---------|--------|-----------|------|-------|------------|"
        ])
        
        for service_name, status in statuses.items():
            report_lines.append(
                f"| {service_name.title()} | "
                f"{self._status_icon(status.get('status', 'unknown'))} {status.get('status', 'N/A')} | "
                f"{status.get('auth_type', 'N/A')} | "
                f"{'✅' if status.get('sync_enabled') else '❌'} | "
                f"{'✅' if status.get('agent_mode') else '❌'} | "
                f"{status.get('last_check', 'N/A')[:19] if status.get('last_check') else 'N/A'} |"
            )
        
        report_lines.extend([
            "",
            "## Detailed Service Analysis / 詳細服務分析",
            ""
        ])
        
        # Detailed analysis for each service
        for service_name in sorted(self.connectors.keys()):
            connector = self.connectors[service_name]
            status = statuses.get(service_name, {})
            
            report_lines.extend(self._generate_service_section(service_name, connector, status))
        
        # Security Guidelines
        report_lines.extend([
            "",
            "## Security & Compliance / 安全與合規",
            "",
            "### General Security Recommendations / 一般安全建議",
            "",
            "- 🔐 **Credential Storage / 憑證儲存**",
            "  - Use environment variables or encrypted secret management",
            "  - 使用環境變數或加密的密鑰管理",
            "  - Never commit credentials to version control",
            "  - 絕不將憑證提交到版本控制",
            "",
            "- 📊 **Monitoring / 監控**",
            "  - Enable API call logging for all connectors",
            "  - 啟用所有連接器的 API 調用日誌",
            "  - Set up alerts for unusual activity",
            "  - 設置異常活動警報",
            "",
            "- 🔄 **Token Rotation / 令牌輪換**",
            "  - Rotate API keys quarterly",
            "  - 每季度輪換 API 密鑰",
            "  - Implement auto-refresh for OAuth tokens",
            "  - 實施 OAuth 令牌自動刷新",
            "",
            "- ⚠️ **Rate Limiting / 速率限制**",
            "  - Monitor rate limit usage",
            "  - 監控速率限制使用情況",
            "  - Implement backoff strategies",
            "  - 實施退避策略",
            ""
        ])
        
        # Operational Recommendations
        report_lines.extend([
            "## Operational Recommendations / 運維建議",
            "",
            "### Connection Management / 連接管理",
            "",
            "1. **Regular Health Checks / 定期健康檢查**",
            "   ```bash",
            "   python -m connectors.connector_manager --check-all",
            "   ```",
            "",
            "2. **Automated Monitoring / 自動化監控**",
            "   - Schedule daily connection checks",
            "   - 安排每日連接檢查",
            "   - Alert on connection failures",
            "   - 連接失敗時發出警報",
            "",
            "3. **Sync Configuration / 同步配置**",
            "   - Enable sync only for required services",
            "   - 僅為必需的服務啟用同步",
            "   - Configure sync intervals based on data volume",
            "   - 根據數據量配置同步間隔",
            "",
            "### Troubleshooting / 故障排除",
            "",
            "Common issues and solutions:",
            "常見問題與解決方案:",
            "",
            "- **Authentication Failures / 認證失敗**",
            "  - Verify credentials in config/connectors.yaml",
            "  - Check environment variables",
            "  - Ensure OAuth tokens are not expired",
            "",
            "- **Rate Limiting / 速率限制**",
            "  - Implement exponential backoff",
            "  - Reduce request frequency",
            "  - Consider upgrading service plan",
            "",
            "- **Sync Failures / 同步失敗**",
            "  - Check network connectivity",
            "  - Verify service availability",
            "  - Review error logs for details",
            ""
        ])
        
        # Write report
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(report_lines), encoding='utf-8')
        
        return output_path
    
    def _status_icon(self, status: str) -> str:
        """Get status icon / 獲取狀態圖標"""
        icons = {
            "connected": "✅",
            "disconnected": "🔴",
            "authenticating": "🔄",
            "error": "❌",
            "not_configured": "⚙️",
            "rate_limited": "⏱️"
        }
        return icons.get(status, "❓")
    
    def _generate_service_section(self, service_name: str, connector: BaseConnector, status: Dict) -> List[str]:
        """Generate detailed section for a service / 生成服務的詳細部分"""
        lines = [
            f"### {service_name.title().replace('_', ' ')}",
            "",
            f"**Status / 狀態:** {self._status_icon(status.get('status', 'unknown'))} {status.get('status', 'N/A')}",
            f"**Service URL / 服務 URL:** {connector.service_url}",
            f"**Authentication / 認證:** {status.get('auth_type', 'N/A')}",
            f"**Sync Enabled / 同步啟用:** {'✅ Yes' if status.get('sync_enabled') else '❌ No'}",
            f"**Agent Mode / 代理模式:** {'✅ Supported' if status.get('agent_mode') else '❌ Not Supported'}",
            ""
        ]
        
        # Connection flow
        lines.extend([
            "**Connection Flow / 連接流程:**",
            ""
        ])
        
        if status.get('status') == 'connected':
            lines.extend([
                "1. ✅ Credentials configured",
                "2. ✅ Authentication successful",
                "3. ✅ Connection verified",
                ""
            ])
        else:
            auth_url = connector.get_auth_url()
            if auth_url:
                lines.extend([
                    f"1. Navigate to: `{auth_url}`",
                    "2. Authorize the application",
                    "3. Copy the token/credentials",
                    "4. Update `config/connectors.yaml` or environment variables",
                    ""
                ])
            else:
                lines.extend([
                    "1. Obtain API key from service dashboard",
                    "2. Set environment variable or update config",
                    "3. Restart connector manager",
                    ""
                ])
        
        # Potential issues
        lines.extend([
            "**Potential Issues / 潛在問題:**",
            ""
        ])
        
        issues = self._get_service_issues(service_name)
        for issue in issues:
            lines.append(f"- {issue}")
        lines.append("")
        
        # Security guidelines
        security = connector.get_security_guidelines()
        lines.extend([
            "**Security Guidelines / 安全指引:**",
            ""
        ])
        
        for category, guidelines in security.items():
            lines.append(f"*{category.replace('_', ' ').title()}:*")
            for guideline in guidelines:
                lines.append(f"- {guideline}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        return lines
    
    def _get_service_issues(self, service_name: str) -> List[str]:
        """Get common issues for a service / 獲取服務的常見問題"""
        issues = {
            "github": [
                "Token expiration - 令牌過期",
                "Rate limiting (5000 requests/hour) - 速率限制",
                "2FA requirements - 雙因素認證要求"
            ],
            "notion": [
                "OAuth token refresh - OAuth 令牌刷新",
                "Page access permissions - 頁面訪問權限",
                "Database schema changes - 數據庫架構變更"
            ],
            "dropbox": [
                "File size limitations - 文件大小限制",
                "API v2 migration - API v2 遷移",
                "Team vs personal accounts - 團隊 vs 個人帳戶"
            ],
            "google_drive": [
                "OAuth consent screen - OAuth 同意畫面",
                "Quota limitations - 配額限制",
                "File sharing permissions - 文件共享權限"
            ],
            "vercel": [
                "Deployment token scope - 部署令牌範圍",
                "Project access rights - 項目訪問權限",
                "Environment variable sync - 環境變數同步"
            ],
            "icloud": [
                "Limited API availability - 有限的 API 可用性",
                "App-specific passwords - 應用專用密碼",
                "2FA mandatory - 雙因素認證強制"
            ],
            "gitlab": [
                "Self-hosted vs GitLab.com - 自架 vs GitLab.com",
                "Access token scopes - 訪問令牌範圍",
                "CI/CD integration - CI/CD 整合"
            ],
            "huggingface": [
                "Model access permissions - 模型訪問權限",
                "Dataset download limits - 數據集下載限制",
                "API rate throttling - API 速率節流"
            ]
        }
        return issues.get(service_name, ["No known issues / 無已知問題"])


def main():
    """Command-line interface for connector manager / 連接器管理器的命令列介面"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cloud Connector Manager / 雲端連接器管理器")
    parser.add_argument("--check-all", action="store_true", help="Check all connections")
    parser.add_argument("--generate-report", action="store_true", help="Generate comprehensive report")
    parser.add_argument("--service", help="Check specific service")
    
    args = parser.parse_args()
    
    manager = ConnectorManager()
    
    if args.generate_report or not any([args.check_all, args.service]):
        print("Generating comprehensive report...")
        report_path = manager.generate_comprehensive_report()
        print(f"✅ Report generated: {report_path}")
    
    if args.check_all:
        print("\nChecking all connections...")
        results = manager.check_all_connections()
        for service, status in results.items():
            icon = manager._status_icon(status.get('status', 'unknown'))
            print(f"{icon} {service}: {status.get('status', 'N/A')}")
    
    if args.service:
        connector = manager.get_connector(args.service)
        if connector:
            print(f"\nChecking {args.service}...")
            connector.check_connection()
            print(json.dumps(connector.get_status_report(), indent=2))
        else:
            print(f"❌ Service not found: {args.service}")


if __name__ == "__main__":
    main()
