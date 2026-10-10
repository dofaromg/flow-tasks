"""Exercise module-a with real Flask, without replacing Flask with a stub."""

import hashlib
import importlib.metadata
import importlib.util
from pathlib import Path
import sys

import flask
import pytest


@pytest.fixture
def module(monkeypatch):
    directory = Path(__file__).resolve().parents[1] / "apps" / "module-a"
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.setenv("MODULE_NAME", "module-a")
    monkeypatch.setenv("ENVIRONMENT", "runtime-test")
    monkeypatch.syspath_prepend(str(directory.parent))
    for name, filename in (("core", "core.py"), ("_module_a_runtime", "app.py")):
        spec = importlib.util.spec_from_file_location(name, directory / filename)
        loaded = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, loaded)
        spec.loader.exec_module(loaded)
    loaded.app.config.update(TESTING=True)
    return loaded


def test_real_flask_and_unique_routes(module):
    assert importlib.metadata.version("Flask")
    assert isinstance(module.app, flask.Flask)
    assert Path(flask.__file__).is_file()
    rules = list(module.app.url_map.iter_rules())
    for path, endpoint in (("/health", "health"), ("/info", "info"),
                           ("/compute", "compute")):
        assert [(r.rule, r.endpoint) for r in rules if r.rule == path] == [(path, endpoint)]
        assert sum(r.endpoint == endpoint for r in rules) == 1
    assert module.app.debug is False


def test_health_and_info(module):
    client = module.app.test_client()
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json == {"status": "healthy"}
    info = client.get("/info")
    assert info.status_code == 200
    assert info.json == {
        "service": "module-a", "version": "2.0.0", "environment": "runtime-test",
        "capabilities": ["compute_particle", "tokenize", "simhash64", "particle_score"],
        "origin_signature": "MrLiouWord",
    }


def test_info_hides_database_credentials(module, monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://private-user:private-password@db:27017/mrl")
    response = module.app.test_client().get("/info")
    assert response.status_code == 200
    assert response.json["mongodb"] == "db:27017/mrl"
    assert "private-user" not in response.text
    assert "private-password" not in response.text


@pytest.mark.parametrize("text,count,unique", [("MRL MRL 世界", 3, 2), ("", 0, 0)])
def test_compute(module, text, count, unique):
    response = module.app.test_client().post("/compute", json={"text": text})
    assert response.status_code == 200
    assert response.json["ok"] is True
    result = response.json["result"]
    assert result["token_count"] == count
    assert result["unique_tokens"] == unique
    assert result["char_count"] == len(text)
    assert result["sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert result["origin_signature"] == "MrLiouWord"


@pytest.mark.parametrize("body", [
    '{}', '{"text":null}', '{"text":123}', '{"text":[]}', '{"text":{}}',
    'null', '[]', '["private-input"]', '"private-input"', '42', 'true',
    '{"text":', '',
])
def test_invalid_input_is_generic_400(module, body):
    response = module.app.test_client().post(
        "/compute", data=body, content_type="application/json")
    assert response.status_code == 400
    assert response.json == {"ok": False, "error": "invalid_input"}


def test_non_json_input_is_generic_400(module):
    response = module.app.test_client().post("/compute", data="private-input")
    assert response.status_code == 400
    assert response.json == {"ok": False, "error": "invalid_input"}


def test_unexpected_error_is_logged_but_not_returned(module, monkeypatch, caplog):
    def fail(_text):
        raise RuntimeError("private-internal-detail")

    monkeypatch.setattr(module.core, "compute_particle", fail)
    module.app.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=False)
    response = module.app.test_client().post("/compute", json={"text": "hello"})
    assert response.status_code == 500
    for forbidden in ("private-internal-detail", "Traceback", "RuntimeError", "app.py"):
        assert forbidden not in response.text
    assert "private-internal-detail" in caplog.text
