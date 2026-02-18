"""Tests for CLI module with programmatic invocation support."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from cli import main, build_parser


@pytest.fixture
def temp_env(tmp_path):
    """Create temporary environment for testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    sandbox_dir = tmp_path / "data_sandbox"
    sandbox_dir.mkdir()
    
    config_file = config_dir / "test_config.yaml"
    config_file.write_text(f"""data_dir: {data_dir}
sandbox_data_dir: {sandbox_dir}
notion:
  enabled: false
github:
  enabled: false
""")
    
    return {
        "config": config_file,
        "data_dir": data_dir,
        "sandbox_dir": sandbox_dir,
    }


def test_main_with_custom_argv_init(temp_env, capsys):
    """Test main() function can be invoked programmatically with init command."""
    argv = ["--config", str(temp_env["config"]), "init"]
    main(argv)
    
    captured = capsys.readouterr()
    assert "Ledger initialized" in captured.out
    assert temp_env["data_dir"].exists()


def test_main_with_custom_argv_init_reset(temp_env, capsys):
    """Test main() function with init --reset flag."""
    # First init
    main(["--config", str(temp_env["config"]), "init"])
    
    # Reset
    argv = ["--config", str(temp_env["config"]), "init", "--reset"]
    main(argv)
    
    captured = capsys.readouterr()
    assert "Ledger initialized" in captured.out


def test_main_with_custom_argv_append(temp_env, capsys):
    """Test main() function with append command."""
    # Initialize first
    main(["--config", str(temp_env["config"]), "init"])
    capsys.readouterr()  # Clear init output
    
    # Append entry
    argv = ["--config", str(temp_env["config"]), "append", "Test content"]
    main(argv)
    
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["content"] == "Test content"
    assert output["index"] == 1
    assert "hash" in output


def test_main_with_custom_argv_verify(temp_env, capsys):
    """Test main() function with verify command."""
    # Initialize and add entries
    main(["--config", str(temp_env["config"]), "init"])
    main(["--config", str(temp_env["config"]), "append", "Entry A"])
    main(["--config", str(temp_env["config"]), "append", "Entry B"])
    
    # Verify
    argv = ["--config", str(temp_env["config"]), "verify"]
    main(argv)
    
    captured = capsys.readouterr()
    assert "Verified 2 entries" in captured.out


def test_main_with_custom_argv_snapshot(temp_env, capsys):
    """Test main() function with snapshot command."""
    # Initialize and add entries
    main(["--config", str(temp_env["config"]), "init"])
    main(["--config", str(temp_env["config"]), "append", "Snapshot test"])
    capsys.readouterr()  # Clear previous output
    
    # Create snapshot
    argv = ["--config", str(temp_env["config"]), "snapshot", "test_snap"]
    main(argv)
    
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["name"] == "test_snap"
    assert "created_at" in output
    assert "head" in output


def test_main_with_custom_argv_log(temp_env, capsys):
    """Test main() function with log command."""
    # Initialize and add entries
    main(["--config", str(temp_env["config"]), "init"])
    main(["--config", str(temp_env["config"]), "append", "Log entry 1"])
    main(["--config", str(temp_env["config"]), "append", "Log entry 2"])
    capsys.readouterr()  # Clear previous output
    
    # Get log
    argv = ["--config", str(temp_env["config"]), "log", "--n", "2"]
    main(argv)
    
    captured = capsys.readouterr()
    entries = json.loads(captured.out)
    assert len(entries) == 2
    assert entries[0]["content"] == "Log entry 1"
    assert entries[1]["content"] == "Log entry 2"


def test_main_with_custom_argv_github_export(temp_env, capsys):
    """Test main() function with github-export command."""
    # Initialize and add entries
    main(["--config", str(temp_env["config"]), "init"])
    main(["--config", str(temp_env["config"]), "append", "Export test"])
    
    # Export
    argv = ["--config", str(temp_env["config"]), "github-export", "--n", "1"]
    main(argv)
    
    captured = capsys.readouterr()
    assert "Exported 1 entries" in captured.out
    
    # Verify export file was created
    export_file = temp_env["data_dir"] / "github_export.json"
    assert export_file.exists()
    export_data = json.loads(export_file.read_text())
    assert len(export_data) == 1


def test_main_with_custom_argv_notion_sync(temp_env, capsys, monkeypatch):
    """Test main() function with notion-sync command."""
    # Set a dummy token to avoid requiring real credentials
    monkeypatch.setenv("NOTION_TOKEN", "test_token_12345")
    
    # Mock the requests module to avoid real API calls
    with patch("adapters.notion_adapter.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Initialize and add entries
        main(["--config", str(temp_env["config"]), "init"])
        main(["--config", str(temp_env["config"]), "append", "Notion test"])
        capsys.readouterr()  # Clear previous output
        
        # Sync (will create local export and mock API call)
        argv = ["--config", str(temp_env["config"]), "notion-sync", "--n", "1"]
        main(argv)
        
        captured = capsys.readouterr()
        assert "Synced 1 entries to Notion" in captured.out
        
        # Verify the API was "called" with correct parameters
        assert mock_get.called


def test_main_with_custom_argv_sandbox_compare_success(temp_env, capsys):
    """Test main() function with sandbox-compare command - matching ledgers."""
    import shutil
    
    # Setup primary
    main(["--config", str(temp_env["config"]), "init"])
    main(["--config", str(temp_env["config"]), "append", "Entry 1"])
    
    # Copy entire primary directory to sandbox to ensure exact match
    shutil.copytree(temp_env["data_dir"], temp_env["sandbox_dir"], dirs_exist_ok=True)
    
    capsys.readouterr()  # Clear previous output
    
    # Compare
    argv = ["--config", str(temp_env["config"]), "sandbox-compare"]
    main(argv)
    
    captured = capsys.readouterr()
    assert "Sandbox ledger matches primary state" in captured.out


def test_main_with_custom_argv_sandbox_compare_mismatch(temp_env, capsys):
    """Test main() function with sandbox-compare command - mismatched ledgers."""
    from amp.storage import Storage
    from amp.ledger import Ledger
    
    # Setup primary
    main(["--config", str(temp_env["config"]), "init"])
    main(["--config", str(temp_env["config"]), "append", "Primary entry"])
    
    # Setup sandbox with different data
    sandbox_storage = Storage(temp_env["sandbox_dir"])
    sandbox_ledger = Ledger(sandbox_storage)
    sandbox_ledger.init()
    sandbox_ledger.append("Sandbox entry")
    
    # Compare - should fail
    argv = ["--config", str(temp_env["config"]), "sandbox-compare"]
    with pytest.raises(SystemExit) as exc_info:
        main(argv)
    
    assert exc_info.value.code == 1


def test_main_with_custom_argv_sandbox_compare_custom_dir(temp_env, capsys):
    """Test main() function with sandbox-compare using custom sandbox directory."""
    import shutil
    
    # Create custom sandbox directory
    custom_sandbox = temp_env["data_dir"].parent / "custom_sandbox"
    custom_sandbox.mkdir()
    
    # Setup primary
    main(["--config", str(temp_env["config"]), "init"])
    main(["--config", str(temp_env["config"]), "append", "Entry 1"])
    
    # Copy entire primary directory to custom sandbox to ensure exact match
    shutil.copytree(temp_env["data_dir"], custom_sandbox, dirs_exist_ok=True)
    
    capsys.readouterr()  # Clear previous output
    
    # Compare with custom directory
    argv = [
        "--config", str(temp_env["config"]),
        "sandbox-compare",
        "--sandbox-dir", str(custom_sandbox)
    ]
    main(argv)
    
    captured = capsys.readouterr()
    assert "Sandbox ledger matches primary state" in captured.out


def test_main_without_argv_shows_help(capsys):
    """Test main() function without arguments shows help."""
    main([])
    captured = capsys.readouterr()
    assert "AMP Index-only ledger CLI" in captured.out


def test_build_parser_returns_valid_parser():
    """Test that build_parser returns a properly configured parser."""
    parser = build_parser()
    assert parser is not None
    assert parser.description == "AMP Index-only ledger CLI"
    
    # Test parsing a valid command
    args = parser.parse_args(["init"])
    assert args.command == "init"
    assert hasattr(args, "func")


def test_build_parser_all_commands():
    """Test that build_parser includes all expected commands."""
    parser = build_parser()
    
    # Test commands with their required arguments
    test_cases = [
        (["init"], "init"),
        (["append", "test_content"], "append"),
        (["snapshot", "snap_name"], "snapshot"),
        (["verify"], "verify"),
        (["log"], "log"),
        (["notion-sync"], "notion-sync"),
        (["github-export"], "github-export"),
        (["sandbox-compare"], "sandbox-compare"),
    ]
    
    for argv, expected_cmd in test_cases:
        args = parser.parse_args(argv)
        assert args.command == expected_cmd
