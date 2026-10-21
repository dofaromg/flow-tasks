"""
test_config_manager.py — Smoke tests for config_manager.py
origin_signature: MrLiouWord
"""
from __future__ import annotations

import os
import pathlib
import tempfile

import pytest

from config_manager import ConfigManager, _DEFAULTS


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _tmp_cfg() -> ConfigManager:
    """Return a ConfigManager backed by a fresh temp file (not polluting data/)."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = pathlib.Path(f.name)
    path.unlink()  # Remove so ConfigManager starts from defaults
    return ConfigManager(config_path=path)


# ─── Defaults ────────────────────────────────────────────────────────────────

class TestDefaults:
    def test_default_llm_model(self):
        # deny-by-default (rootlaw rl_00): no implicit "mock" in production config.
        cfg = _tmp_cfg()
        assert cfg.get("llm.default_model") == ""

    def test_default_allow_mock_is_false(self):
        cfg = _tmp_cfg()
        assert cfg.get("llm.allow_mock") is False

    def test_default_api_host(self):
        cfg = _tmp_cfg()
        assert cfg.get("api.host") == "127.0.0.1"

    def test_default_context_max_tokens(self):
        cfg = _tmp_cfg()
        assert cfg.get("context.max_tokens") == 4096

    def test_missing_key_returns_default(self):
        cfg = _tmp_cfg()
        assert cfg.get("nonexistent.key", "fallback") == "fallback"

    def test_missing_key_returns_none_if_no_default(self):
        cfg = _tmp_cfg()
        assert cfg.get("nonexistent.key") is None


# ─── Get / Set ────────────────────────────────────────────────────────────────

class TestGetSet:
    def test_set_and_get(self):
        cfg = _tmp_cfg()
        cfg.set("llm.default_model", "llama3")
        assert cfg.get("llm.default_model") == "llama3"

    def test_set_nested_creates_path(self):
        cfg = _tmp_cfg()
        cfg.set("custom.deep.key", 99)
        assert cfg.get("custom.deep.key") == 99

    def test_set_overwrites(self):
        cfg = _tmp_cfg()
        cfg.set("llm.temperature", 0.1)
        cfg.set("llm.temperature", 0.9)
        assert cfg.get("llm.temperature") == 0.9


# ─── Persistence ─────────────────────────────────────────────────────────────

class TestPersistence:
    def test_save_and_reload(self, tmp_path):
        path = tmp_path / "cfg.json"
        cfg1 = ConfigManager(config_path=path)
        cfg1.set("llm.default_model", "saved-model")
        cfg1.save()

        cfg2 = ConfigManager(config_path=path)
        assert cfg2.get("llm.default_model") == "saved-model"

    def test_reset_restores_defaults(self):
        cfg = _tmp_cfg()
        cfg.set("llm.default_model", "changed")
        cfg.reset()
        assert cfg.get("llm.default_model") == ""

    def test_corrupt_file_falls_back_to_defaults(self, tmp_path):
        path = tmp_path / "corrupt.json"
        path.write_text("not valid json", encoding="utf-8")
        cfg = ConfigManager(config_path=path)
        assert cfg.get("llm.default_model") == ""


# ─── Environment variable overrides ──────────────────────────────────────────

class TestEnvOverrides:
    def test_env_var_overrides_json(self, monkeypatch):
        monkeypatch.setenv("MRL_LLM_DEFAULT_MODEL", "env-model")
        cfg = _tmp_cfg()
        assert cfg.get("llm.default_model") == "env-model"

    def test_env_var_bool_coercion(self, monkeypatch):
        monkeypatch.setenv("MRL_SYSTEM_DEBUG", "true")
        cfg = _tmp_cfg()
        val = cfg.get("system.debug")
        assert val is True

    def test_env_var_int_coercion(self, monkeypatch):
        monkeypatch.setenv("MRL_CONTEXT_MAX_TOKENS", "8192")
        cfg = _tmp_cfg()
        val = cfg.get("context.max_tokens")
        assert val == 8192

    def test_env_var_unset_uses_json(self, monkeypatch):
        monkeypatch.delenv("MRL_LLM_DEFAULT_MODEL", raising=False)
        cfg = _tmp_cfg()
        assert cfg.get("llm.default_model") == ""


# ─── Secret masking ───────────────────────────────────────────────────────────

class TestSecretMasking:
    def test_api_key_masked(self):
        cfg = _tmp_cfg()
        cfg.set("llm.openai_api_key", "sk-secret")
        dumped = cfg.dump(mask_secrets=True)
        llm_section = dumped.get("llm", {})
        assert llm_section.get("openai_api_key") == "***"

    def test_non_sensitive_not_masked(self):
        cfg = _tmp_cfg()
        cfg.set("llm.default_model", "gpt-4o")
        dumped = cfg.dump(mask_secrets=True)
        assert dumped["llm"]["default_model"] == "gpt-4o"

    def test_mask_false_shows_secrets(self):
        cfg = _tmp_cfg()
        cfg.set("llm.openai_api_key", "sk-visible")
        dumped = cfg.dump(mask_secrets=False)
        assert dumped["llm"]["openai_api_key"] == "sk-visible"


# ─── Schema keys ─────────────────────────────────────────────────────────────

class TestSchemaKeys:
    def test_schema_keys_non_empty(self):
        cfg = _tmp_cfg()
        keys = cfg.schema_keys()
        assert len(keys) > 0

    def test_schema_keys_include_known(self):
        cfg = _tmp_cfg()
        keys = cfg.schema_keys()
        assert "llm.default_model" in keys
        assert "api.host" in keys
