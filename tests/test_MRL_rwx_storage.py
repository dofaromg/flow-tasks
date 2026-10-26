"""Regression checks for unintended default RWX provisioning."""

import importlib.util
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / "scripts/MRL_check_rwx_storage.py"
SPEC = importlib.util.spec_from_file_location("mrl_storage", MODULE)
storage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(storage)


@pytest.mark.parametrize("mode,class_value,expected", [
    ("ReadWriteMany", None, True),
    ("ReadWriteMany", "approved-nfs", False),
    ("ReadWriteMany", "", False),
    ("ReadWriteMany", False, True),
    ("ReadWriteOnce", None, False),
])
def test_storage_decision(mode, class_value, expected):
    claim = {"kind": "PersistentVolumeClaim", "spec": {"accessModes": [mode]}}
    if class_value is not None:
        claim["spec"]["storageClassName"] = class_value
    _, errors = storage.check_documents([claim])
    assert bool(errors) is expected


def test_null_class_and_nested_templates():
    template = {"metadata": {"name": "shared"}, "spec": {
        "accessModes": ["ReadWriteMany"], "storageClassName": None}}
    documents = [{"kind": "List", "items": [{"kind": "StatefulSet", "spec": {
        "volumeClaimTemplates": [template]}}]}]
    claims, errors = storage.check_documents(documents)
    assert len(claims) == len(errors) == 1
    assert "volumeClaimTemplates[0]" in errors[0]


def test_malformed_spec_is_not_a_clean_result():
    _, errors = storage.check_documents([
        {"kind": "PersistentVolumeClaim", "spec": None}])
    assert errors


def test_repository_mongodb_stays_explicit_rwo():
    import yaml
    path = MODULE.parents[1] / "apps/mongodb/pvc.yaml"
    claims, errors = storage.check_documents(list(yaml.safe_load_all(path.read_text())))
    assert not errors
    assert claims[0][2:] == (["ReadWriteOnce"], "standard-rwo")
