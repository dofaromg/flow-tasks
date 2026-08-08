import json
from pathlib import Path

from MRL_Mother.mother_registry.registry import REGISTRY_NAMES, MotherRegistry, Source


def test_build_deduplicates_content_and_preserves_evidence(tmp_path: Path):
    first = tmp_path / "dropbox"
    second = tmp_path / "github"
    first.mkdir()
    second.mkdir()
    (first / "Design v1.md").write_text("same evidence", encoding="utf-8")
    (second / "renamed.md").write_text("same evidence", encoding="utf-8")
    output = tmp_path / "registry"

    result = MotherRegistry(
        [Source("github", second, "engineering"), Source("dropbox", first, "records")], output
    ).build()

    assert len(result["assets"]["items"]) == 1
    assert result["assets"]["items"][0]["source"] == "dropbox"
    assert len(result["evidence_registry"]["items"]) == 2
    assert all((output / f"{name}.json").is_file() for name in REGISTRY_NAMES)
    assert len(list((output / "reports").glob("*.md"))) == 15


def test_incremental_build_and_lineage_are_stable(tmp_path: Path):
    source = tmp_path / "local"
    source.mkdir()
    (source / "service-v1.py").write_text("print(1)\n", encoding="utf-8")
    (source / "service-v2.py").write_text("print(2)\n", encoding="utf-8")
    output = tmp_path / "registry"
    registry = MotherRegistry([Source("local-runtime", source)], output)

    first = registry.build()
    second = MotherRegistry([Source("local-runtime", source)], output).build()

    assert len(first["lineage_registry"]["items"]) == 1
    assert [a["asset_id"] for a in first["assets"]["items"]] == [a["asset_id"] for a in second["assets"]["items"]]
    cache = json.loads((output / ".scan-cache.json").read_text(encoding="utf-8"))
    assert len(cache["files"]) == 2
    assert all(item["runtime_capable"] for item in first["assets"]["items"])
