"""
Tests for prompt_template — PromptTemplate and TemplateRegistry.
"""
import json
import pathlib
import tempfile

import pytest

from prompt_template import PromptTemplate, TemplateRegistry, ORIGIN_SIGNATURE


# ─── PromptTemplate ───────────────────────────────────────────────────────────

class TestPromptTemplate:
    def test_variables_extracted(self):
        t = PromptTemplate("greet", "Hello, {name}! You are a {role}.")
        assert sorted(t.variables) == ["name", "role"]

    def test_no_variables(self):
        t = PromptTemplate("static", "No placeholders here.")
        assert t.variables == []

    def test_render_basic(self):
        t = PromptTemplate("greet", "Hello, {name}!")
        assert t.render({"name": "MRL"}) == "Hello, MRL!"

    def test_render_multiple_vars(self):
        t = PromptTemplate("intro", "{greeting}, {name}! You are {role}.")
        result = t.render({"greeting": "Hi", "name": "Agent", "role": "kernel"})
        assert result == "Hi, Agent! You are kernel."

    def test_render_missing_var_raises(self):
        t = PromptTemplate("greet", "Hello, {name}!")
        with pytest.raises(KeyError, match="missing variable"):
            t.render({})

    def test_render_extra_vars_ignored(self):
        t = PromptTemplate("greet", "Hello, {name}!")
        result = t.render({"name": "MRL", "extra": "ignored"})
        assert result == "Hello, MRL!"

    def test_render_int_value(self):
        t = PromptTemplate("count", "Items: {n}")
        assert t.render({"n": 42}) == "Items: 42"

    def test_to_dict_keys(self):
        t = PromptTemplate("greet", "Hello, {name}!", description="greeting")
        d = t.to_dict()
        for key in ("id", "text", "description", "version", "created_at_ms", "variables", "origin_signature"):
            assert key in d

    def test_to_dict_origin_signature(self):
        t = PromptTemplate("x", "text")
        assert t.to_dict()["origin_signature"] == ORIGIN_SIGNATURE

    def test_from_dict_roundtrip(self):
        t = PromptTemplate("greet", "Hello, {name}!", description="A greeting", version=3)
        d = t.to_dict()
        recovered = PromptTemplate.from_dict(d)
        assert recovered.id == t.id
        assert recovered.text == t.text
        assert recovered.description == t.description
        assert recovered.version == t.version
        assert recovered.variables == t.variables

    def test_duplicate_placeholder_deduplicated(self):
        t = PromptTemplate("dupe", "{x} and {x}")
        assert t.variables == ["x"]

    def test_version_default(self):
        t = PromptTemplate("v", "text")
        assert t.version == 1


# ─── TemplateRegistry ─────────────────────────────────────────────────────────

class TestTemplateRegistry:
    @pytest.fixture
    def reg(self, tmp_path):
        store = tmp_path / "templates.json"
        return TemplateRegistry(store_path=store)

    def test_empty_registry(self, reg):
        assert len(reg) == 0
        assert reg.list_ids() == []

    def test_add_and_get(self, reg):
        reg.add("greet", "Hello, {name}!")
        t = reg.get("greet")
        assert t is not None
        assert t.id == "greet"

    def test_add_sets_version_one(self, reg):
        t = reg.add("greet", "Hello, {name}!")
        assert t.version == 1

    def test_add_overwrites_bumps_version(self, reg):
        reg.add("greet", "Hello, {name}!")
        t2 = reg.add("greet", "Hi, {name}!")
        assert t2.version == 2
        assert reg.get("greet").text == "Hi, {name}!"

    def test_list_ids_sorted(self, reg):
        reg.add("z_template", "{x}")
        reg.add("a_template", "{y}")
        assert reg.list_ids() == ["a_template", "z_template"]

    def test_remove_existing(self, reg):
        reg.add("greet", "Hello, {name}!")
        removed = reg.remove("greet")
        assert removed is True
        assert reg.get("greet") is None

    def test_remove_missing(self, reg):
        assert reg.remove("nonexistent") is False

    def test_render_basic(self, reg):
        reg.add("greet", "Hello, {name}!")
        result = reg.render("greet", {"name": "MRL"})
        assert result == "Hello, MRL!"

    def test_render_missing_template_raises(self, reg):
        with pytest.raises(KeyError, match="template not found"):
            reg.render("missing")

    def test_render_record_keys(self, reg):
        reg.add("greet", "Hello, {name}!")
        rec = reg.render_record("greet", {"name": "MRL"})
        for key in ("template_id", "variables", "rendered", "rendered_at_ms", "origin_signature"):
            assert key in rec

    def test_render_record_values(self, reg):
        reg.add("greet", "Hello, {name}!")
        rec = reg.render_record("greet", {"name": "MRL"})
        assert rec["template_id"] == "greet"
        assert rec["rendered"] == "Hello, MRL!"
        assert rec["origin_signature"] == ORIGIN_SIGNATURE

    def test_render_record_no_vars(self, reg):
        reg.add("static", "No placeholders.")
        rec = reg.render_record("static")
        assert rec["rendered"] == "No placeholders."

    def test_persistence(self, tmp_path):
        store = tmp_path / "templates.json"
        reg1 = TemplateRegistry(store_path=store)
        reg1.add("greet", "Hello, {name}!")

        reg2 = TemplateRegistry(store_path=store)
        t = reg2.get("greet")
        assert t is not None
        assert t.text == "Hello, {name}!"

    def test_persistence_version_preserved(self, tmp_path):
        store = tmp_path / "templates.json"
        reg1 = TemplateRegistry(store_path=store)
        reg1.add("greet", "Hello, {name}!")
        reg1.add("greet", "Hi, {name}!")  # bump to v2

        reg2 = TemplateRegistry(store_path=store)
        assert reg2.get("greet").version == 2

    def test_persistence_remove(self, tmp_path):
        store = tmp_path / "templates.json"
        reg1 = TemplateRegistry(store_path=store)
        reg1.add("greet", "Hello, {name}!")
        reg1.remove("greet")

        reg2 = TemplateRegistry(store_path=store)
        assert reg2.get("greet") is None

    def test_len(self, reg):
        assert len(reg) == 0
        reg.add("a", "text")
        reg.add("b", "text")
        assert len(reg) == 2
