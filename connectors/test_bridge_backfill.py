"""Failure-boundary tests for the real Bridge API contract; no live credentials."""

import base64
import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest

spec = importlib.util.spec_from_file_location(
    "mrl_backfill", Path(__file__).resolve().parents[1]
    / "scripts/MRL_verify_bridge_backfill_v1.py",
)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class FakeBridge:
    def __init__(self):
        self.headers = {}
        self.disk = {}
        self.corrupt = False
        self.hostname = "WIN-PBVUI7VK2A6"
        self.capabilities = {"file_write_create_only": True}
        self.race = False
        self.ack = True

    def request(self, method, url, json, **options):
        assert options["allow_redirects"] is False
        response = Mock(status_code=200)
        if url.endswith("/version"):
            response.json.return_value = {
                "hostname": self.hostname, "origin_signature": "MrLiouWord",
                "capabilities": self.capabilities,
            }
        elif url.endswith("/MRL_file/list"):
            response.json.return_value = {"ok": True, "items": []}
        elif url.endswith("/MRL_file/write"):
            assert json["create_only"] is True
            if self.race:
                self.disk[json["filepath"]] = b"concurrent-original"
            if json["filepath"] in self.disk:
                response.status_code = 409
            else:
                self.disk[json["filepath"]] = base64.b64decode(json["b64"])
            response.json.return_value = {"ok": True, "created_exclusively": self.ack}
        elif json["filepath"] not in self.disk:
            response.status_code = 404
        else:
            raw = self.disk[json["filepath"]]
            if self.corrupt:
                raw += b"corrupt"
            response.json.return_value = {
                "ok": True, "content": base64.b64encode(raw).decode(), "size": len(raw),
            }
        return response


def test_backfill_reads_four_source_files_and_receipt():
    session = FakeBridge()
    result = bridge.verify_backfill(session, r"D:\MRL_Mother\EvidenceChain")
    assert result["status"] == "DELIVERY_PASS"
    assert result["file_count"] == 4
    assert result["receipt_readback_verified"] is True
    assert len(session.disk) == 5


def test_readback_corruption_blocks_success():
    session = FakeBridge()
    session.corrupt = True
    with pytest.raises(RuntimeError, match="逐 byte"):
        bridge.write_verified(session, r"D:\MRL_Mother\evidence\unique.bin", b"original")


def test_existing_destination_is_not_overwritten():
    session = FakeBridge()
    path = r"D:\MRL_Mother\evidence\existing.bin"
    session.disk[path] = b"original"
    with pytest.raises(RuntimeError, match="拒絕覆寫"):
        bridge.write_verified(session, path, b"replacement")
    assert session.disk[path] == b"original"


@pytest.mark.parametrize("status", [301, 302, 401, 403, 500])
def test_http_failure_never_reads_response_body(status):
    session = Mock()
    session.request.return_value = Mock(status_code=status)
    with pytest.raises(RuntimeError, match=f"HTTP {status}"):
        bridge.call(session, "POST", "/MRL_file/read", {})
    session.request.return_value.json.assert_not_called()


def test_wrong_host_cannot_write():
    session = FakeBridge()
    session.hostname = "different-host"
    with pytest.raises(RuntimeError, match="主機"):
        bridge.verify_backfill(session, r"D:\MRL_Mother\EvidenceChain")
    assert not session.disk


def test_missing_binding_blocks_before_network(monkeypatch, capsys):
    monkeypatch.delenv("MRL_BRIDGE_API_KEY", raising=False)
    monkeypatch.setattr("sys.argv", ["verify", "--mother-root", r"D:\MRL_Mother"])
    assert bridge.main() == 2
    assert "BLOCKED" in capsys.readouterr().out


@pytest.mark.parametrize("capabilities", [None, {}, {"file_write_create_only": "true"}])
def test_legacy_server_cannot_write(capabilities):
    session = FakeBridge()
    session.capabilities = capabilities
    with pytest.raises(RuntimeError, match="create_only"):
        bridge.verify_backfill(session, r"D:\MRL_Mother\EvidenceChain")
    assert not session.disk


def test_concurrent_creation_is_never_overwritten():
    session = FakeBridge()
    session.race = True
    path = r"D:\MRL_Mother\evidence\race.bin"
    with pytest.raises(RuntimeError, match="HTTP 409"):
        bridge.write_verified(session, path, b"replacement")
    assert session.disk[path] == b"concurrent-original"


def test_missing_exclusive_ack_cannot_pass():
    session = FakeBridge()
    session.ack = False
    with pytest.raises(RuntimeError, match="原子建立"):
        bridge.write_verified(session, r"D:\MRL_Mother\evidence\new.bin", b"data")


@pytest.mark.parametrize("path", [
    r"C:\Windows", r"D:\other", r"D:\MRL_Mother\..\Windows",
    r"D:\MRL_Mother/../Windows", r"D:\MRL_Mother\x:stream",
    r"D:\MRL_Mother\x. ", r"\\server\share", r"D:MRL_Mother",
])
def test_invalid_destination_blocks_before_network(path):
    session = Mock()
    with pytest.raises(ValueError):
        bridge.verify_backfill(session, path)
    session.request.assert_not_called()


@pytest.mark.parametrize("status", [307, 308, 401, 403])
def test_denial_prevents_any_followup_write(status):
    session = Mock()
    session.request.return_value = Mock(status_code=status)
    with pytest.raises(RuntimeError):
        bridge.write_verified(session, r"D:\MRL_Mother\evidence\new.bin", b"data")
    assert session.request.call_count == 1


def test_cli_error_redacts_credentials(monkeypatch, capsys):
    secret = "test-only-sensitive-value"
    monkeypatch.setenv("MRL_BRIDGE_API_KEY", secret)
    monkeypatch.setattr("sys.argv", ["verify", "--mother-root", r"D:\MRL_Mother"])
    monkeypatch.setattr(bridge, "verify_backfill", Mock(side_effect=RuntimeError(secret)))
    assert bridge.main() == 1
    assert secret not in capsys.readouterr().out
