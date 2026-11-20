"""GitHub task dispatch and return path. origin_signature: MrLiouWord."""

import base64
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from .base_connector import ConnectorConfig
from .connector_manager import ConnectorManager
from .github_connector import GitHubConnector
from .github_task_runner import main

REPOSITORY = "dofaromg/flow-tasks"
HEAD = "a" * 40


def configured(**settings):
    return GitHubConnector(ConnectorConfig(
        enabled=True, sync_enabled=True,
        custom_settings={"repositories": [REPOSITORY],
                         "allow_public_read": True, **settings}))


def task(**fields):
    return {"task_id": "MRL_GitHub_Test", "operation": "get_pull_request",
            "repository": REPOSITORY, "number": 700, **fields}


def pull_response(**changes):
    return {"number": 700, "state": "open", "merged": False,
            "head": {"sha": HEAD, "ref": "MRL_candidate"},
            "base": {"sha": "b" * 40, "ref": "main",
                     "repo": {"full_name": REPOSITORY}}, **changes}


def response(data, status=200):
    value = requests.Response()
    value.status_code = status
    value._content = json.dumps(data).encode()
    value.headers = {"Content-Type": "application/json"}
    return value


@patch("connectors.base_connector.requests.request")
def test_task_reaches_shared_transport_and_returns_linked_receipt(send):
    send.return_value = response(pull_response())
    connector = configured()
    result = connector.execute_task(task())
    assert result["success"] and result["data"]["head"]["sha"] == HEAD
    assert result["task_id"] == "MRL_GitHub_Test"
    assert result["mrl_bridge"]["parent_ref"]
    records = list(connector.mrl_bridge_center.records)
    assert result["mrl_bridge"]["trace_id"] == records[-2]["trace_id"]
    assert send.call_args.kwargs["allow_redirects"] is False
    assert send.call_args.kwargs["url"] == "https://api.github.com/repos/" + REPOSITORY + "/pulls/700"
    assert send.call_args.kwargs["method"] == "GET"


@pytest.mark.parametrize("change", [
    {"repository": "someone/else"},
    {"repository": "dofaromg/flow-tasks?override=1"},
    {"operation": "merge_pull_request"},
    {"number": True},
    {"number": -1},
    {"task_id": "bad\nidentifier"},
    {"operation": "get_file", "path": "../secret", "ref": HEAD},
    {"operation": "get_file", "path": "README.md", "ref": "main"},
])
@patch("connectors.base_connector.requests.request")
def test_invalid_or_unapproved_tasks_make_no_network_request(send, change):
    result = configured().execute_task(task(**change))
    assert not result["success"]
    send.assert_not_called()


@patch("connectors.base_connector.requests.request")
def test_disabled_or_missing_credentials_stops_before_network(send):
    connector = configured()
    connector.config.enabled = False
    assert connector.execute_task(task())["error"] == "connector_disabled"
    connector = configured(allow_public_read=False)
    assert connector.execute_task(task())["error"] == "github_credentials_missing"
    send.assert_not_called()


@pytest.mark.parametrize("status", [302, 401, 403, 404, 429, 503])
@patch("connectors.base_connector.requests.request")
def test_failed_transport_never_completes_task(send, status):
    send.return_value = response({"message": "private response content"}, status)
    result = configured().execute_task(task())
    assert not result["success"] and result["error"] == "github_http_" + str(status)
    assert "private response content" not in json.dumps(result)


@patch("connectors.base_connector.requests.request")
def test_file_uses_exact_ref_and_preserves_original_bytes(send):
    payload = "MRL 原始內容\n".encode()
    blob = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
    send.return_value = response({
        "type": "file", "path": "MRL_module.py", "encoding": "base64",
        "size": len(payload), "sha": blob, "content": base64.b64encode(payload).decode()})
    result = configured().execute_task(task(
        operation="get_file", path="MRL_module.py", ref=HEAD))
    assert result["success"]
    assert base64.b64decode(result["data"]["content"]) == payload
    assert result["data"]["sha256"] == hashlib.sha256(payload).hexdigest()
    assert send.call_args.kwargs["params"] == {"ref": HEAD}
    send.return_value = response({
        "type": "file", "path": "MRL_module.py", "encoding": "base64",
        "size": len(payload), "sha": "0" * 40, "content": base64.b64encode(payload).decode()})
    assert configured().execute_task(task(
        operation="get_file", path="MRL_module.py", ref=HEAD))["error"] == "file_content_mismatch"


@patch("connectors.base_connector.requests.request")
def test_wrong_repo_and_incomplete_pr_sha_fail(send):
    send.return_value = response(pull_response(base={
        "sha": HEAD, "repo": {"full_name": "another/repo"}}))
    assert not configured().execute_task(task())["success"]
    send.return_value = response(pull_response(head={"sha": "short"}))
    assert not configured().execute_task(task())["success"]


@patch("connectors.base_connector.requests.request")
def test_batch_returns_failure_with_successful_results_preserved(send):
    send.side_effect = [response(pull_response()), response({}, 403)]
    connector = configured(tasks=[task(), task(task_id="MRL_Second")])
    result = connector.sync_data()
    assert result["success"] is False and result["items_synced"] == 1
    assert len(result["results"]) == 2
    assert result["results"][0]["success"]


@patch("connectors.base_connector.requests.request")
def test_empty_batch_and_push_do_not_report_success(send):
    assert not configured().sync_data()["success"]
    assert not configured().sync_data("push")["success"]
    send.assert_not_called()


@patch("connectors.base_connector.requests.request")
def test_manager_runner_writes_new_receipts_without_changing_other_services(send, tmp_path):
    send.return_value = response(pull_response())
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"connectors": {"github": {
        "enabled": True, "sync_enabled": True, "settings": {
            "repositories": [REPOSITORY], "allow_public_read": True, "tasks": [task()]}}}}))
    manager = ConnectorManager(str(config))
    assert all(not connector.config.enabled for name, connector in manager.connectors.items() if name != "github")
    assert manager.execute_task("github", task())["success"]
    argv = ["--config", str(config), "--output-dir", str(tmp_path / "receipts")]
    assert main(argv) == 0
    first = next((tmp_path / "receipts").glob("*.json"))
    original = first.read_bytes()
    assert main(argv) == 0
    assert len(list((tmp_path / "receipts").glob("*.json"))) == 2
    assert first.read_bytes() == original
    assert json.loads(original)["results"][0]["task_id"] == "MRL_GitHub_Test"


def test_runner_and_manager_report_missing_execution_entry(tmp_path):
    assert main(["--config", str(tmp_path / "missing"), "--output-dir", str(tmp_path)]) == 1
    manager = ConnectorManager.__new__(ConnectorManager)
    manager.connectors = {}
    assert not manager.execute_task("missing", task())["success"]


@patch("connectors.base_connector.requests.request")
def test_policy_rejection_preserves_existing_connection_state(send):
    connector = configured()
    connector._handle_connection_success()
    old_status = connector.health.status
    assert not connector.execute_task(task(operation="merge_pull_request"))["success"]
    assert connector.health.status == old_status
    send.assert_not_called()


@patch("connectors.github_task_runner.ConnectorManager", side_effect=KeyboardInterrupt)
def test_runner_records_interrupted_execution(manager, tmp_path):
    config = tmp_path / "config.json"
    config.write_text("{}")
    assert main(["--config", str(config), "--output-dir", str(tmp_path / "receipts")]) == 1
    result = json.loads(next((tmp_path / "receipts").glob("*.json")).read_text())
    assert result["status"] == "INTERRUPTED" and result["success"] is False
