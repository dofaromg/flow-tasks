"""Exercise the real terminal HTTP handler without executing host commands.

origin_signature: MrLiouWord
"""
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import Mock

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = "MRL_Mother/04_runtime/flowcore_loop.py"


@pytest.fixture
def terminal(monkeypatch):
    spec = importlib.util.spec_from_file_location("terminal_under_test", ROOT / RUNTIME)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "HUMAN_TOKEN", "synthetic-test-token")
    runner = Mock(return_value="synthetic output\n")
    monkeypatch.setattr(module.subprocess, "check_output", runner)
    steering = Mock()
    steering.load_profile.return_value = dict(module.DEFAULT_STEERING_PROFILE)
    handler_type = module.make_handler(Mock(), Mock(), steering)

    def post(command, token="synthetic-test-token"):
        handler = handler_type.__new__(handler_type)
        body = json.dumps({"cmd": command}).encode("utf-8")
        handler.path = "/terminal/exec"
        handler.headers = {"Content-Length": str(len(body))}
        if token is not None:
            handler.headers["X-Human-Token"] = token
        handler.rfile = io.BytesIO(body)
        handler._send = Mock()
        handler.do_POST()
        return handler._send.call_args.args

    return module, runner, post


@pytest.mark.parametrize("command", ["ls -l", "cat example.txt", "echo hello", "pwd", "echo hello\nworld"])
def test_allowed_commands_keep_route_and_arguments(terminal, command):
    _, runner, post = terminal
    status, response = post(command)
    assert status == 200
    assert response == {"ok": True, "output": "synthetic output\n"}
    runner.assert_called_once_with(command.split(), shell=False, text=True, timeout=10)


@pytest.mark.parametrize("command", [
    "ls-unapproved", "catapult file", "echoevil", "pwd-unapproved",
    "ls/other-program", "cat/other-program", "sh", "/bin/ls",
    "echo hello; pwd", "echo $(pwd)",
    "", " ", None, 123, [], {},
])
def test_unapproved_commands_never_reach_subprocess(terminal, command):
    _, runner, post = terminal
    status, response = post(command)
    assert (status, response) == (403, {"ok": False, "error": "command_not_allowed"})
    runner.assert_not_called()


@pytest.mark.parametrize("token", [None, "wrong-test-token"])
def test_terminal_still_requires_human_token(terminal, token):
    _, runner, post = terminal
    status, response = post("pwd", token)
    assert (status, response) == (403, {"ok": False, "error": "need_human_token"})
    runner.assert_not_called()


def test_terminal_timeout_keeps_existing_response(terminal):
    module, runner, post = terminal
    runner.side_effect = module.subprocess.TimeoutExpired(["pwd"], 10)
    assert post("pwd") == (504, {"ok": False, "error": "command_timeout"})
