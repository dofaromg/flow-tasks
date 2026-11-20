"""
GitHub Connector
GitHub 連接器

Integration with GitHub API for repository and workflow management
整合 GitHub API 用於倉庫和工作流程管理
"""

import base64
from datetime import datetime, timezone
import hashlib
import re
from typing import Dict, List, Optional, Any
from urllib.parse import quote

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
        """Execute explicitly configured read tasks; return their actual results."""
        if direction != "pull":
            return {"success": False, "direction": direction,
                    "error": "unsupported_direction", "items_synced": 0}
        if self.config.enabled is not True or self.config.sync_enabled is not True:
            return {"success": False, "direction": direction,
                    "error": "github_pull_disabled", "items_synced": 0}
        tasks = self.config.custom_settings.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            return {"success": False, "direction": direction,
                    "error": "github_tasks_not_configured", "items_synced": 0}
        if len(tasks) > 100:
            return {"success": False, "direction": direction,
                    "error": "too_many_tasks", "items_synced": 0}
        results = [self.execute_task(task) for task in tasks]
        return {"schema": "MRL.GitHubTaskBatch.v1", "success": all(
                    result["success"] for result in results),
                "origin_signature": "MrLiouWord", "direction": direction,
                "items_synced": sum(result["success"] for result in results),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "results": results}

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run one bounded GitHub read through the existing translation center.

        Supported operations: get_repository, get_pull_request, get_file.
        Host configuration selects repositories; it cannot be widened by a task.
        """
        self.last_mrl_bridge_receipt = None
        result = {"schema": "MRL.GitHubTaskResult.v1", "service": "GitHub",
                  "origin_signature": "MrLiouWord", "canonical_authority": "Mr.liou",
                  "observed_at": datetime.now(timezone.utc).isoformat(),
                  "task_id": None, "success": False, "status": "BLOCKED"}
        try:
            if not isinstance(task, dict):
                raise ValueError("task_must_be_an_object")
            task_id = task.get("task_id")
            if not isinstance(task_id, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", task_id):
                raise ValueError("invalid_task_id")
            result["task_id"] = task_id
            if self.config.enabled is not True:
                raise ValueError("connector_disabled")
            settings = self.config.custom_settings
            if not self._get_token() and settings.get("allow_public_read") is not True:
                raise ValueError("github_credentials_missing")
            repository = task.get("repository")
            if not isinstance(repository, str) or not re.fullmatch(
                    r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+", repository):
                raise ValueError("invalid_repository")
            allowed = settings.get("repositories")
            if (not isinstance(allowed, list) or repository.casefold() not in
                    {name.casefold() for name in allowed if isinstance(name, str)}):
                raise ValueError("repository_not_allowed")
            operation = task.get("operation")
            if operation not in {"get_repository", "get_pull_request", "get_file"}:
                raise ValueError("unsupported_operation")
            result.update({"repository": repository, "operation": operation})
            endpoint = "/repos/" + repository
            params = None
            if operation == "get_pull_request":
                number = task.get("number")
                if type(number) is not int or number < 1:
                    raise ValueError("invalid_pull_request_number")
                endpoint += "/pulls/" + str(number)
            elif operation == "get_file":
                path, ref = task.get("path"), task.get("ref")
                if (not isinstance(path, str) or not path or path.startswith("/")
                        or "\\" in path or any(part in {"", ".", ".."} for part in path.split("/"))
                        or any(ord(char) < 32 for char in path)):
                    raise ValueError("invalid_file_path")
                if not isinstance(ref, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
                    raise ValueError("file_requires_exact_commit_sha")
                endpoint += "/contents/" + quote(path, safe="/")
                params = {"ref": ref}
            url = self.service_url + endpoint
            result["source_url"] = url
            if params:
                result["source_ref"] = params["ref"]
            response = self._make_request("GET", url, params=params, allow_redirects=False)
            self.health.api_calls_today += 1
            if response.status_code != 200:
                result["status"] = "ERROR"
                raise ValueError("github_http_" + str(response.status_code))
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("unexpected_response_type")
            if operation == "get_repository":
                if data.get("full_name", "").casefold() != repository.casefold():
                    raise ValueError("repository_identity_mismatch")
            elif operation == "get_pull_request":
                if (data.get("number") != task["number"] or
                        data.get("base", {}).get("repo", {}).get("full_name", "").casefold()
                        != repository.casefold()):
                    raise ValueError("pull_request_identity_mismatch")
                for side in ("head", "base"):
                    if not re.fullmatch(r"[0-9a-fA-F]{40}", data.get(side, {}).get("sha", "")):
                        raise ValueError("pull_request_sha_missing")
            else:
                if (data.get("type") != "file" or data.get("path") != task["path"]
                        or data.get("encoding") != "base64"):
                    raise ValueError("unexpected_file_response")
                size = data.get("size")
                if type(size) is not int or not 0 <= size <= 1024 * 1024:
                    raise ValueError("file_size_out_of_range")
                encoded = data.get("content")
                if not isinstance(encoded, str) or len(encoded) > 1500000:
                    raise ValueError("invalid_file_encoding")
                payload = base64.b64decode("".join(encoded.split()), validate=True)
                blob = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
                if len(payload) != size or blob != data.get("sha"):
                    raise ValueError("file_content_mismatch")
                data = {"path": task["path"], "ref": task["ref"], "blob_sha": blob,
                        "size": size, "sha256": hashlib.sha256(payload).hexdigest(),
                        "encoding": "base64", "content": base64.b64encode(payload).decode()}
            result.update({"success": True, "status": "COMPLETED", "data": data})
            self._handle_connection_success()
        except ValueError as exc:
            result["error"] = str(exc) if str(exc) in {
                "task_must_be_an_object", "invalid_task_id", "connector_disabled",
                "github_credentials_missing", "invalid_repository", "repository_not_allowed",
                "unsupported_operation", "invalid_pull_request_number", "invalid_file_path",
                "file_requires_exact_commit_sha", "unexpected_response_type",
                "repository_identity_mismatch", "pull_request_identity_mismatch",
                "pull_request_sha_missing", "unexpected_file_response", "file_size_out_of_range",
                "invalid_file_encoding", "file_content_mismatch",
                "github_http_301", "github_http_302", "github_http_307", "github_http_308",
                "github_http_401", "github_http_403", "github_http_404", "github_http_429",
                "github_http_500", "github_http_502", "github_http_503",
            } else "invalid_response"
        except Exception as exc:
            result.update({"status": "ERROR", "error": "github_request_failed",
                           "error_type": type(exc).__name__})
        if not result["success"] and result["status"] == "ERROR":
            self._handle_connection_error(result["error"])
        parent = self.last_mrl_bridge_receipt
        receipt = self.mrl_bridge_center.label(
            result, source_ref="GitHub", destination_ref="MRL.connector_manager",
            direction="external_to_mrl", status=result["status"].lower(),
            trace_id=parent["trace_id"] if parent else None,
            parent_ref=parent["event_id"] if parent else None)
        self.last_mrl_bridge_receipt = receipt
        return {**result, "mrl_bridge": receipt}

