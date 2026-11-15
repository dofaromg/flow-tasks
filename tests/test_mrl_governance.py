import pytest

from scripts import validate_mrl_governance as governance


def _stub_diff(monkeypatch, diff_output, term_counter=None):
    def fake_obj(path, ref=None):
        if path == governance.MIGRATIONS:
            return {"migrations": []}
        if path == governance.NAMING:
            return {"rename_contract": {"mass_change_file_threshold": 2}}
        raise AssertionError(f"Unexpected JSON file: {path}")

    def fake_git(*args, **kwargs):
        if args[0] == "diff":
            return diff_output
        raise AssertionError(f"Unexpected git command: {args}")

    monkeypatch.setattr(governance, "obj", fake_obj)
    monkeypatch.setattr(governance, "git", fake_git)
    monkeypatch.setattr(
        governance,
        "term_count",
        term_counter or (lambda ref, term: 1),
    )


def test_trusted_default_branch_sync_only_exempts_mass_change_threshold(monkeypatch):
    _stub_diff(monkeypatch, "A\tfirst.txt\nA\tsecond.txt\n")

    with pytest.raises(governance.Failure, match="unapproved mass change: 2 files"):
        governance.validate_diff("base", "head")

    result = governance.validate_diff(
        "base",
        "head",
        trusted_default_branch_sync=True,
    )

    assert result["changed_files"] == 2
    assert result["trusted_default_branch_sync"] is True
    assert result["mass_change_threshold_exempt"] is True


def test_trusted_default_branch_sync_does_not_exempt_protected_path_changes(monkeypatch):
    _stub_diff(monkeypatch, "D\tLICENSE\n")

    with pytest.raises(governance.Failure, match="protected delete/rename"):
        governance.validate_diff(
            "base",
            "head",
            trusted_default_branch_sync=True,
        )


def test_trusted_default_branch_sync_does_not_exempt_identifier_reduction(monkeypatch):
    _stub_diff(
        monkeypatch,
        "A\tnew.txt\n",
        term_counter=lambda ref, term: 1 if ref == "base" else 0,
    )

    with pytest.raises(
        governance.Failure,
        match="protected identifier reduced without root approval",
    ):
        governance.validate_diff(
            "base",
            "head",
            trusted_default_branch_sync=True,
        )


def test_trusted_default_branch_sync_requires_diff_inputs(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["validate_mrl_governance.py", "--trusted-default-branch-sync"],
    )

    with pytest.raises(
        governance.Failure,
        match="--trusted-default-branch-sync requires --base and --head",
    ):
        governance.main()
