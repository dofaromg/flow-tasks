"""
Tests for refactored connectors
連接器重構測試
"""

import json
from pathlib import Path
import subprocess
import sys

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
from .connector_manager import ConnectorManager, main


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


class TestConnectorManager:
    """Test orchestration across all configured cloud spaces."""

    def test_loads_auth_types_and_icloud_credentials_from_environment(
        self, tmp_path, monkeypatch
    ):
        config_path = tmp_path / "connectors.yaml"
        config_path.write_text(
            """
version: '1.0'
connectors:
  github:
    enabled: true
    auth_type: api_key
  icloud:
    enabled: true
    auth_type: basic_auth
global:
  connection_timeout: 12
  retry_attempts: 2
""",
            encoding="utf-8",
        )
        monkeypatch.setenv("ICLOUD_USERNAME", "cloud@example.com")
        monkeypatch.setenv("ICLOUD_APP_PASSWORD", "app-password")

        manager = ConnectorManager(str(config_path))

        assert manager.connectors["github"].config.auth_type.value == "api_key"
        assert manager.connectors["github"].config.timeout == 12
        assert manager.connectors["icloud"].config.credentials == {
            "username": "cloud@example.com",
            "app_password": "app-password",
        }

    @pytest.mark.parametrize("include_disabled", [False, True])
    def test_connect_all_only_attempts_enabled_connectors(
        self, tmp_path, include_disabled
    ):
        manager = ConnectorManager(str(tmp_path / "connectors.yaml"))
        for connector in manager.connectors.values():
            connector.authenticate = Mock(return_value=False)
        github = manager.connectors["github"]
        github.config.enabled = True

        results = manager.connect_all(include_disabled=include_disabled)

        github.authenticate.assert_called_once_with()
        assert "skipped" not in results["github"]
        assert set(results) == set(manager.SUPPORTED_SERVICES)
        for service, connector in manager.connectors.items():
            if service != "github":
                connector.authenticate.assert_not_called()
                assert results[service]["skipped"] is True
                assert results[service]["reason"] == "disabled"

    def test_sync_all_runs_only_sync_enabled_connectors(self, tmp_path):
        manager = ConnectorManager(str(tmp_path / "connectors.yaml"))
        github = manager.connectors["github"]
        github.config.enabled = True
        github.config.sync_enabled = True
        github.sync_data = Mock(return_value={"success": True, "direction": "push"})

        results = manager.sync_all("push")

        github.sync_data.assert_called_once_with("push")
        assert results["github"]["success"] is True
        assert results["notion"]["reason"] == "disabled"

    def test_sync_all_rejects_unknown_direction(self, tmp_path):
        manager = ConnectorManager(str(tmp_path / "connectors.yaml"))

        with pytest.raises(ValueError, match="Unsupported sync direction"):
            manager.sync_all("sideways")


class TestConnectorAudit:
    """Audit inventory must not activate disabled cloud services."""

    @pytest.fixture
    def manager(self, tmp_path):
        # Keep audit tests independent of any real credentials in the environment.
        with patch.object(ConnectorManager, "_load_env_credentials"):
            return ConnectorManager(str(tmp_path / "connectors.yaml"))

    @pytest.mark.parametrize("include_disabled", [False, True])
    @pytest.mark.parametrize("configured", [False, True])
    def test_disabled_inventory_preserves_status_without_authentication(
        self, manager, include_disabled, configured
    ):
        expected = {}
        for service, connector in manager.connectors.items():
            if configured:
                connector.config.credentials = {
                    connector.credential_key: "test-token",
                    "username": "test@example.com",
                }
            connector.health.status = ConnectorStatus.ERROR
            connector.health.error_message = "Previous check failed"
            connector.authenticate = Mock()
            expected[service] = {
                **connector.get_status_report(),
                "skipped": True,
                "reason": "disabled",
            }

        results = manager.connect_all(include_disabled=include_disabled)

        assert results == expected
        for connector in manager.connectors.values():
            connector.authenticate.assert_not_called()

    @pytest.mark.parametrize("enabled, expected_exit", [(False, 0), (True, 1)])
    def test_audit_command_without_credentials(self, tmp_path, enabled, expected_exit):
        config_path = tmp_path / "connectors.yaml"
        config_path.write_text(
            f"connectors:\n  github:\n    enabled: {str(enabled).lower()}\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable, "-m", "connectors.connector_manager",
                "--connect-all", "--include-disabled", "--strict", "--json",
                "--config", str(config_path),
            ],
            cwd=Path(__file__).resolve().parents[1],
            env={},
            capture_output=True,
            text=True,
            timeout=15,
        )

        assert result.returncode == expected_exit
        inventory = json.loads(result.stdout)
        assert set(inventory) == set(ConnectorManager.SUPPORTED_SERVICES)
        for service, report in inventory.items():
            assert report["status"] == "not_configured"
            if service == "github" and enabled:
                assert report["enabled"] is True
                assert not report.get("skipped")
            else:
                assert report["enabled"] is False
                assert report["skipped"] is True
                assert report["reason"] == "disabled"

    @pytest.mark.parametrize("strict", [False, True])
    @pytest.mark.parametrize("outcome", ["connected", "unauthorized", "timeout", "exception"])
    def test_enabled_verification_controls_exit_status(
        self, manager, monkeypatch, capsys, strict, outcome
    ):
        github = manager.connectors["github"]
        github.config.enabled = True
        github.config.credentials = {"token": "test-token"}
        argv = ["connector_manager", "--connect-all", "--include-disabled", "--json"]
        if strict:
            argv.append("--strict")
        monkeypatch.setattr(sys, "argv", argv)

        response = Mock(status_code=200 if outcome == "connected" else 401)
        response.text = '{"login": "testuser"}'
        response.json.return_value = {"login": "testuser"}
        response.headers = {}
        if outcome == "exception":
            github.authenticate = Mock(side_effect=RuntimeError("Test auth error"))
        with (
            patch("connectors.connector_manager.ConnectorManager", return_value=manager),
            patch("connectors.base_connector.requests.request", return_value=response) as request,
        ):
            if outcome == "timeout":
                request.side_effect = requests.exceptions.Timeout()
            if strict and outcome != "connected":
                with pytest.raises(SystemExit) as exc:
                    main()
                assert exc.value.code == 1
            else:
                main()
            if outcome == "exception":
                github.authenticate.assert_called_once_with()
                request.assert_not_called()
            else:
                request.assert_called_once()

        inventory = json.loads(capsys.readouterr().out)
        assert set(inventory) == set(manager.SUPPORTED_SERVICES)
        assert inventory["github"]["status"] == (
            "connected" if outcome == "connected" else "error"
        )
        assert not inventory["github"].get("skipped")
        assert all(
            report.get("skipped")
            for service, report in inventory.items() if service != "github"
        )


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
