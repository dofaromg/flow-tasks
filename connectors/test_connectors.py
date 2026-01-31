"""
Tests for refactored connectors
連接器重構測試
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from .base_connector import BaseConnector, ConnectorConfig, ConnectorStatus
from .github_connector import GitHubConnector
from .gitlab_connector import GitLabConnector
from .notion_connector import NotionConnector
from .dropbox_connector import DropboxConnector
from .google_drive_connector import GoogleDriveConnector
from .huggingface_connector import HuggingFaceConnector
from .vercel_connector import VercelConnector
from .icloud_connector import ICloudConnector


class TestBaseConnectorSharedMethods:
    """Test shared methods in BaseConnector"""
    
    def test_get_token_returns_token(self):
        """Test _get_token returns token from credentials"""
        config = ConnectorConfig(credentials={"token": "test_token"})
        connector = GitHubConnector(config)
        assert connector._get_token() == "test_token"
    
    def test_get_token_returns_none_when_missing(self):
        """Test _get_token returns None when token is missing"""
        config = ConnectorConfig(credentials={})
        connector = GitHubConnector(config)
        assert connector._get_token() is None
    
    def test_get_auth_headers_with_token(self):
        """Test _get_auth_headers includes Bearer token"""
        config = ConnectorConfig(credentials={"token": "test_token"})
        connector = GitHubConnector(config)
        headers = connector._get_auth_headers()
        assert headers["Authorization"] == "Bearer test_token"
    
    def test_handle_connection_success(self):
        """Test _handle_connection_success updates health status"""
        config = ConnectorConfig(credentials={"token": "test_token"})
        connector = GitHubConnector(config)
        result = connector._handle_connection_success({"user": "testuser"})
        assert result is True
        assert connector.health.status == ConnectorStatus.CONNECTED
        assert connector.health.metadata == {"user": "testuser"}
        assert connector.health.error_message is None
    
    def test_handle_connection_error(self):
        """Test _handle_connection_error updates health status"""
        config = ConnectorConfig(credentials={"token": "test_token"})
        connector = GitHubConnector(config)
        result = connector._handle_connection_error("Test error")
        assert result is False
        assert connector.health.status == ConnectorStatus.ERROR
        assert connector.health.error_message == "Test error"
    
    def test_handle_not_configured(self):
        """Test _handle_not_configured updates health status"""
        config = ConnectorConfig(credentials={})
        connector = GitHubConnector(config)
        result = connector._handle_not_configured()
        assert result is False
        assert connector.health.status == ConnectorStatus.NOT_CONFIGURED
        assert "not configured" in connector.health.error_message.lower()


class TestGitHubConnector:
    """Test GitHubConnector"""
    
    def test_service_properties(self):
        """Test service name and URL"""
        config = ConnectorConfig()
        connector = GitHubConnector(config)
        assert connector.service_name == "GitHub"
        assert connector.service_url == "https://api.github.com"
    
    def test_github_specific_headers(self):
        """Test GitHub includes Accept header"""
        config = ConnectorConfig(credentials={"token": "test_token"})
        connector = GitHubConnector(config)
        headers = connector._get_auth_headers()
        assert "Accept" in headers
        assert "github" in headers["Accept"].lower()
    
    def test_authenticate_without_token(self):
        """Test authenticate fails without token"""
        config = ConnectorConfig(credentials={})
        connector = GitHubConnector(config)
        result = connector.authenticate()
        assert result is False
        assert connector.health.status == ConnectorStatus.NOT_CONFIGURED
    
    @patch('connectors.base_connector.requests.request')
    def test_check_connection_success(self, mock_request):
        """Test check_connection success"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"login": "testuser"}'
        mock_response.json.return_value = {"login": "testuser"}
        mock_response.headers = {"X-RateLimit-Remaining": "5000"}
        mock_request.return_value = mock_response
        
        config = ConnectorConfig(credentials={"token": "test_token"})
        connector = GitHubConnector(config)
        result = connector.check_connection()
        
        assert result is True
        assert connector.health.status == ConnectorStatus.CONNECTED
        assert connector.health.metadata.get("user") == "testuser"
    
    @patch('connectors.base_connector.requests.request')
    def test_check_connection_auth_failure(self, mock_request):
        """Test check_connection handles 401"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        config = ConnectorConfig(credentials={"token": "invalid_token"})
        connector = GitHubConnector(config)
        result = connector.check_connection()
        
        assert result is False
        assert connector.health.status == ConnectorStatus.ERROR
        assert "token" in connector.health.error_message.lower()


class TestGitLabConnector:
    """Test GitLabConnector"""
    
    def test_service_properties(self):
        """Test service name and URL"""
        config = ConnectorConfig()
        connector = GitLabConnector(config)
        assert connector.service_name == "GitLab"
        assert connector.service_url == "https://gitlab.com/api/v4"
    
    def test_custom_instance_url(self):
        """Test custom GitLab instance URL"""
        config = ConnectorConfig(custom_settings={"instance_url": "https://my.gitlab.com/api/v4"})
        connector = GitLabConnector(config)
        assert connector.service_url == "https://my.gitlab.com/api/v4"


class TestNotionConnector:
    """Test NotionConnector"""
    
    def test_service_properties(self):
        """Test service name and URL"""
        config = ConnectorConfig()
        connector = NotionConnector(config)
        assert connector.service_name == "Notion"
        assert connector.service_url == "https://api.notion.com/v1"
    
    def test_notion_specific_headers(self):
        """Test Notion includes version header"""
        config = ConnectorConfig(credentials={"token": "test_token"})
        connector = NotionConnector(config)
        headers = connector._get_auth_headers()
        assert "Notion-Version" in headers


class TestDropboxConnector:
    """Test DropboxConnector"""
    
    def test_service_properties(self):
        """Test service name and URL"""
        config = ConnectorConfig()
        connector = DropboxConnector(config)
        assert connector.service_name == "Dropbox"
        assert connector.service_url == "https://api.dropboxapi.com/2"


class TestGoogleDriveConnector:
    """Test GoogleDriveConnector"""
    
    def test_service_properties(self):
        """Test service name and URL"""
        config = ConnectorConfig()
        connector = GoogleDriveConnector(config)
        assert connector.service_name == "Google Drive"
        assert connector.service_url == "https://www.googleapis.com/drive/v3"


class TestHuggingFaceConnector:
    """Test HuggingFaceConnector"""
    
    def test_service_properties(self):
        """Test service name and URL"""
        config = ConnectorConfig()
        connector = HuggingFaceConnector(config)
        assert connector.service_name == "HuggingFace"
        assert connector.service_url == "https://huggingface.co/api"


class TestVercelConnector:
    """Test VercelConnector"""
    
    def test_service_properties(self):
        """Test service name and URL"""
        config = ConnectorConfig()
        connector = VercelConnector(config)
        assert connector.service_name == "Vercel"
        assert connector.service_url == "https://api.vercel.com"


class TestICloudConnector:
    """Test ICloudConnector"""
    
    def test_service_properties(self):
        """Test service name and URL"""
        config = ConnectorConfig()
        connector = ICloudConnector(config)
        assert connector.service_name == "iCloud"
        assert connector.service_url == "https://www.icloud.com"
    
    def test_credential_key_is_app_password(self):
        """Test iCloud uses app_password as credential key"""
        config = ConnectorConfig()
        connector = ICloudConnector(config)
        assert connector.credential_key == "app_password"
    
    def test_icloud_specific_security_guidelines(self):
        """Test iCloud has specific security guidelines"""
        config = ConnectorConfig()
        connector = ICloudConnector(config)
        guidelines = connector.get_security_guidelines()
        assert "icloud_specific" in guidelines


class TestDefaultSyncData:
    """Test default sync_data implementation across connectors"""
    
    @patch('connectors.base_connector.requests.request')
    def test_sync_data_returns_success_when_connected(self, mock_request):
        """Test sync_data returns success when connected"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"login": "testuser"}'
        mock_response.json.return_value = {"login": "testuser"}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        config = ConnectorConfig(credentials={"token": "test_token"})
        connector = GitHubConnector(config)
        result = connector.sync_data("pull")
        
        assert result["success"] is True
        assert result["direction"] == "pull"
        assert "timestamp" in result
    
    def test_sync_data_returns_error_when_not_connected(self):
        """Test sync_data returns error when not connected"""
        config = ConnectorConfig(credentials={})
        connector = GitHubConnector(config)
        result = connector.sync_data()
        
        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
