# Cloud Service Connector System
# 雲端服務連接器系統

Unified connector framework for integrating 8 major cloud services with comprehensive security guidelines and operational monitoring.

統一連接器框架，用於整合 8 個主要雲端服務，具備全面的安全指引和營運監控。

## 🌐 Supported Services / 支援的服務

| Service | Status | Auth Type | Sync | Agent Mode | Documentation |
|---------|--------|-----------|------|------------|---------------|
| **GitHub** | ✅ Ready | API Key | ✅ | ✅ | [Docs](https://docs.github.com/en/rest) |
| **Notion** | ✅ Ready | OAuth2 | ✅ | ✅ | [Docs](https://developers.notion.com/) |
| **Dropbox** | ✅ Ready | OAuth2 | ✅ | ⚙️ | [Docs](https://www.dropbox.com/developers) |
| **Google Drive** | ✅ Ready | OAuth2 | ✅ | ⚙️ | [Docs](https://developers.google.com/drive) |
| **Vercel** | ✅ Ready | API Key | ✅ | ✅ | [Docs](https://vercel.com/docs/rest-api) |
| **iCloud** | ⚙️ Limited | App Password | ⚠️ | ❌ | [Docs](https://developer.apple.com/icloud/) |
| **GitLab** | ✅ Ready | API Key | ✅ | ✅ | [Docs](https://docs.gitlab.com/ee/api/) |
| **HuggingFace** | ✅ Ready | API Key | ✅ | ⚙️ | [Docs](https://huggingface.co/docs/hub) |

**Legend:**
- ✅ Ready = Fully implemented
- ⚙️ Limited = Partial implementation
- ⚠️ Warning = Requires additional setup
- ❌ Not Supported

## 🚀 Quick Start / 快速開始

### 1. Installation / 安裝

```bash
# Install dependencies
pip install -r requirements.txt

# No additional packages needed - uses standard library + requests
```

### 2. Configuration / 配置

```bash
# Copy configuration template
cp config/connectors.yaml config/connectors.local.yaml

# Edit configuration (or use environment variables)
vim config/connectors.local.yaml
```

**Environment Variables (Recommended):**
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxx"
export NOTION_TOKEN="secret_xxxxxxxxxxxxx"
export DROPBOX_TOKEN="sl.xxxxxxxxxxxxx"
export GOOGLE_DRIVE_TOKEN="ya29.xxxxxxxxxxxxx"
export VERCEL_TOKEN="xxxxxxxxxxxxx"
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxx"
export HUGGINGFACE_TOKEN="hf_xxxxxxxxxxxxx"
export ICLOUD_TOKEN="xxxx-xxxx-xxxx-xxxx"
```

### 3. Check Connections / 檢查連接

```bash
# Check all services
python -m connectors.connector_manager --check-all

# Check specific service
python -m connectors.connector_manager --service github

# Generate comprehensive report
python -m connectors.connector_manager --generate-report
```

## 📋 Features / 功能特性

### Core Features / 核心功能

- ✅ **Unified Interface** / 統一介面
  - Single API for all cloud services
  - 所有雲端服務的單一 API
  
- ✅ **Health Monitoring** / 健康監控
  - Real-time connection status
  - 即時連接狀態
  - Latency tracking
  - 延遲追蹤
  - Rate limit monitoring
  - 速率限制監控

- ✅ **Security Guidelines** / 安全指引
  - Service-specific security recommendations
  - 服務專用安全建議
  - Data flow monitoring
  - 數據流向監控
  - Compliance checklists
  - 合規檢查清單

- ✅ **Sync Management** / 同步管理
  - Bidirectional data sync
  - 雙向數據同步
  - Conflict resolution
  - 衝突解決
  - Scheduled sync
  - 排程同步

## 📖 Usage Examples / 使用範例

### Python API

```python
from connectors import ConnectorManager

# Initialize manager
manager = ConnectorManager("config/connectors.yaml")

# Check all connections
statuses = manager.check_all_connections()
for service, status in statuses.items():
    print(f"{service}: {status['status']}")

# Get specific connector
github = manager.get_connector("github")
if github.check_connection():
    print("✅ GitHub connected")
    
    # Sync data
    result = github.sync_data(direction="pull")
    print(f"Synced: {result['items_synced']} items")

# Generate report
manager.generate_comprehensive_report("docs/CONNECTOR_SYSTEM_REPORT.md")
```

### CLI Usage

```bash
# List all connectors
python -m connectors.connector_manager --check-all

# Output:
# ✅ github: connected
# ⚙️ notion: not_configured
# 🔴 dropbox: disconnected
# ...

# Check specific service
python -m connectors.connector_manager --service vercel

# Generate full report
python -m connectors.connector_manager --generate-report
```

## 🔐 Security Best Practices / 安全最佳實踐

### Credential Management / 憑證管理

1. **Never commit credentials to Git**
   ```bash
   # Add to .gitignore
   config/connectors.local.yaml
   .env
   ```

2. **Use environment variables**
   ```bash
   # Load from .env file
   source .env
   ```

3. **Rotate credentials regularly**
   - GitHub: Every 90 days
   - OAuth tokens: Implement auto-refresh
   - API keys: Quarterly rotation

### Data Flow Monitoring / 數據流向監控

- Enable request logging for all connectors
- Monitor unusual traffic patterns
- Set up alerts for failed authentications
- Regular access log reviews

### Compliance / 合規性

- **GDPR**: Data protection compliance
- **Regional Requirements**: Data residency
- **Security Audits**: Regular security reviews
- **Access Control**: Least privilege principle

## 📊 Architecture / 架構

```
connectors/
├── __init__.py              # Package initialization
├── base_connector.py        # Abstract base class
├── connector_manager.py     # Central management
├── github_connector.py      # GitHub integration
├── notion_connector.py      # Notion integration
├── dropbox_connector.py     # Dropbox integration
├── google_drive_connector.py # Google Drive integration
├── vercel_connector.py      # Vercel integration
├── icloud_connector.py      # iCloud integration
├── gitlab_connector.py      # GitLab integration
└── huggingface_connector.py # HuggingFace integration

config/
└── connectors.yaml          # Configuration file

docs/
└── CONNECTOR_SYSTEM_REPORT.md # Generated report
```

## 🔧 Configuration Reference / 配置參考

### Connector Configuration Schema

```yaml
connectors:
  service_name:
    enabled: true|false              # Enable/disable connector
    auth_type: "api_key"|"oauth2"   # Authentication method
    sync_enabled: true|false         # Enable data sync
    agent_mode: true|false           # Agent mode support
    credentials:
      token: "xxx"                   # API token
    settings:
      rate_limit: 5000               # Rate limit
      scopes: []                     # Required scopes
```

### Global Settings

- `connection_timeout`: Connection timeout (seconds)
- `retry_attempts`: Number of retry attempts
- `auto_health_check`: Enable automatic health checks
- `health_check_interval`: Check interval (minutes)

## 🔄 Sync Configuration / 同步配置

### Supported Sync Directions

- **pull**: Download from cloud to local
- **push**: Upload from local to cloud
- **bidirectional**: Two-way sync

### Conflict Resolution

- `newest`: Keep newest version
- `oldest`: Keep oldest version
- `manual`: Manual resolution required

## 🐛 Troubleshooting / 故障排除

### Common Issues / 常見問題

**Authentication Failed**
```
Solution:
1. Verify credentials in config/connectors.yaml
2. Check environment variables are set
3. Ensure tokens haven't expired
4. Verify API key has required scopes
```

**Rate Limiting**
```
Solution:
1. Implement exponential backoff
2. Reduce request frequency
3. Consider upgrading service plan
4. Monitor rate_limit_remaining
```

**Connection Timeout**
```
Solution:
1. Check network connectivity
2. Increase connection_timeout in config
3. Verify service availability
4. Check firewall settings
```

## 📚 Service-Specific Guides / 服務專用指南

### GitHub
- **Token Generation**: https://github.com/settings/tokens/new
- **Required Scopes**: `repo`, `workflow`, `read:org`
- **Rate Limit**: 5000 requests/hour

### Notion
- **Integration Setup**: https://www.notion.so/my-integrations
- **OAuth Flow**: Requires web server for callback
- **Scopes**: `read_content`, `update_content`, `insert_content`

### Dropbox
- **App Console**: https://www.dropbox.com/developers/apps
- **OAuth Type**: OAuth 2.0
- **File Size Limit**: 350 GB per file

### Google Drive
- **Credentials**: https://console.cloud.google.com/apis/credentials
- **OAuth Setup**: Requires client ID and secret
- **Quota**: 1 billion requests/day

### Vercel
- **Token**: https://vercel.com/account/tokens
- **Scopes**: Deployment, project, logs access
- **Team Support**: Yes

### iCloud
- **App Password**: https://appleid.apple.com/account/manage
- **Protocol**: WebDAV/CalDAV
- **2FA**: Mandatory

### GitLab
- **Token**: https://gitlab.com/-/profile/personal_access_tokens
- **Self-Hosted**: Supported via custom instance_url
- **API Version**: v4

### HuggingFace
- **Token**: https://huggingface.co/settings/tokens
- **Access**: Models, datasets, spaces
- **Rate Limit**: Depends on plan

## 🚦 Status Codes / 狀態碼

- ✅ `connected`: Successfully connected
- 🔴 `disconnected`: Connection lost
- 🔄 `authenticating`: In authentication process
- ❌ `error`: Connection error
- ⚙️ `not_configured`: Not configured
- ⏱️ `rate_limited`: Rate limit exceeded

## 📈 Monitoring & Metrics / 監控與指標

### Health Metrics

- Connection status
- Last successful connection
- Latency (ms)
- Rate limit remaining
- Error count
- API calls today

### Automated Monitoring

```bash
# Set up cron job for health checks
0 * * * * cd /path/to/flow-tasks && python -m connectors.connector_manager --check-all
```

## 🤝 Contributing / 貢獻

To add a new connector:

1. Inherit from `BaseConnector`
2. Implement required methods
3. Add to `SUPPORTED_SERVICES` in `connector_manager.py`
4. Update configuration schema
5. Add documentation

## 📄 License / 授權

See LICENSE file for details.

## 🔗 Related Documentation / 相關文檔

- [Full System Report](docs/CONNECTOR_SYSTEM_REPORT.md)
- [API Documentation](docs/API.md)
- [Security Guidelines](docs/SECURITY.md)
- [Deployment Guide](DEPLOYMENT.md)

---

**Last Updated**: 2026-01-26  
**Version**: 1.0.0  
**Maintainer**: FlowAgent Team
