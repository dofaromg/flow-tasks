#!/usr/bin/env python3
"""Comprehensive tests for the vNext pipeline CLI runner."""

import json
import tempfile
from pathlib import Path

import pytest

from cli_vnext import (
    GraphNode,
    PipelineGraph,
    command_list_graphs,
    command_run,
    ensure_data_root,
    list_available_graphs,
    load_graph,
    main,
    parse_args,
)


class TestGraphNode:
    """Tests for GraphNode dataclass."""

    def test_from_dict_with_all_fields(self):
        node_dict = {
            "id": "test_node",
            "name": "Test Node",
            "type": "transformer",
            "inputs": ["input1"],
            "outputs": ["output1"],
        }
        node = GraphNode.from_dict(node_dict)
        assert node.id == "test_node"
        assert node.name == "Test Node"
        assert node.type == "transformer"
        assert node.inputs == ["input1"]
        assert node.outputs == ["output1"]

    def test_from_dict_with_missing_fields(self):
        node_dict = {}
        node = GraphNode.from_dict(node_dict)
        assert node.id == ""
        assert node.name == ""
        assert node.type == ""
        assert node.inputs == []
        assert node.outputs == []


class TestPipelineGraph:
    """Tests for PipelineGraph dataclass."""

    def test_from_dict_valid_graph(self):
        graph_dict = {
            "name": "Test Pipeline",
            "description": "A test pipeline",
            "nodes": [
                {
                    "id": "node1",
                    "name": "Node 1",
                    "type": "source",
                    "inputs": [],
                    "outputs": ["data1"],
                }
            ],
        }
        graph = PipelineGraph.from_dict(graph_dict)
        assert graph.name == "Test Pipeline"
        assert graph.description == "A test pipeline"
        assert len(graph.nodes) == 1
        assert graph.nodes[0].id == "node1"

    def test_validate_valid_graph(self):
        graph = PipelineGraph(
            name="Valid Pipeline",
            description="A valid pipeline",
            nodes=[
                GraphNode("source", "Source", "source", [], ["data"]),
                GraphNode("sink", "Sink", "sink", ["data"], []),
            ],
        )
        # Should not raise any exception
        graph.validate()

    def test_validate_empty_name(self):
        graph = PipelineGraph(
            name="",
            description="A test",
            nodes=[GraphNode("node1", "Node 1", "type1", [], [])],
        )
        with pytest.raises(ValueError, match="Pipeline name is required"):
            graph.validate()

    def test_validate_empty_description(self):
        graph = PipelineGraph(
            name="Test",
            description="",
            nodes=[GraphNode("node1", "Node 1", "type1", [], [])],
        )
        with pytest.raises(ValueError, match="Pipeline description is required"):
            graph.validate()

    def test_validate_no_nodes(self):
        graph = PipelineGraph(name="Test", description="Test", nodes=[])
        with pytest.raises(ValueError, match="Pipeline must contain at least one node"):
            graph.validate()

    def test_validate_duplicate_node_ids(self):
        graph = PipelineGraph(
            name="Test",
            description="Test",
            nodes=[
                GraphNode("node1", "Node 1", "type1", [], ["out1"]),
                GraphNode("node1", "Node 2", "type2", ["out1"], []),
            ],
        )
        with pytest.raises(ValueError, match="Duplicate node IDs found"):
            graph.validate()

    def test_validate_empty_node_id(self):
        graph = PipelineGraph(
            name="Test",
            description="Test",
            nodes=[GraphNode("", "Node 1", "type1", [], [])],
        )
        with pytest.raises(ValueError, match="Node ID is required"):
            graph.validate()

    def test_validate_empty_node_name(self):
        graph = PipelineGraph(
            name="Test",
            description="Test",
            nodes=[GraphNode("node1", "", "type1", [], [])],
        )
        with pytest.raises(ValueError, match="name is required"):
            graph.validate()

    def test_validate_empty_node_type(self):
        graph = PipelineGraph(
            name="Test",
            description="Test",
            nodes=[GraphNode("node1", "Node 1", "", [], [])],
        )
        with pytest.raises(ValueError, match="type is required"):
            graph.validate()

    def test_validate_duplicate_outputs(self):
        graph = PipelineGraph(
            name="Test",
            description="Test",
            nodes=[
                GraphNode("node1", "Node 1", "type1", [], ["output1"]),
                GraphNode("node2", "Node 2", "type2", [], ["output1"]),
            ],
        )
        with pytest.raises(ValueError, match="Output 'output1' is produced by multiple nodes"):
            graph.validate()

    def test_validate_missing_input_reference(self):
        graph = PipelineGraph(
            name="Test",
            description="Test",
            nodes=[
                GraphNode("node1", "Node 1", "type1", ["nonexistent"], []),
            ],
        )
        with pytest.raises(
            ValueError, match="references input 'nonexistent' which is not produced"
        ):
            graph.validate()

    def test_validate_cycle_detection(self):
        # Create a cycle: A -> B -> C -> A
        graph = PipelineGraph(
            name="Test",
            description="Test",
            nodes=[
                GraphNode("A", "Node A", "type1", ["output_C"], ["output_A"]),
                GraphNode("B", "Node B", "type2", ["output_A"], ["output_B"]),
                GraphNode("C", "Node C", "type3", ["output_B"], ["output_C"]),
            ],
        )
        with pytest.raises(ValueError, match="Cycle detected"):
            graph.validate()

    def test_format_summary(self):
        graph = PipelineGraph(
            name="Test Pipeline",
            description="Test Description",
            nodes=[
                GraphNode("node1", "Node 1", "source", [], ["data"]),
                GraphNode("node2", "Node 2", "sink", ["data"], []),
            ],
        )
        summary = graph.format_summary()
        assert "Test Pipeline" in summary
        assert "Test Description" in summary
        assert "node1" in summary
        assert "node2" in summary


class TestParseArgs:
    """Tests for command-line argument parsing."""

    def test_parse_run_command(self):
        args = parse_args(["run", "--data-root", "/tmp/data", "--graph", "graph.json"])
        assert args.command == "run"
        assert args.data_root == "/tmp/data"
        assert args.graph == "graph.json"

    def test_parse_list_graphs_command(self):
        args = parse_args(["list-graphs"])
        assert args.command == "list-graphs"

    def test_parse_list_graphs_with_dir(self):
        args = parse_args(["list-graphs", "--graphs-dir", "/custom/path"])
        assert args.command == "list-graphs"
        assert args.graphs_dir == Path("/custom/path")

    def test_parse_missing_required_args(self):
        with pytest.raises(SystemExit):
            parse_args(["run", "--data-root", "/tmp/data"])


class TestLoadGraph:
    """Tests for graph loading functionality."""

    def test_load_valid_graph(self, tmp_path):
        graph_file = tmp_path / "test_graph.json"
        graph_data = {
            "name": "Test",
            "description": "Test graph",
            "nodes": [
                {"id": "node1", "name": "Node 1", "type": "source", "inputs": [], "outputs": []}
            ],
        }
        graph_file.write_text(json.dumps(graph_data))

        graph = load_graph(graph_file)
        assert graph.name == "Test"
        assert graph.description == "Test graph"
        assert len(graph.nodes) == 1

    def test_load_missing_file(self, tmp_path):
        missing_file = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError, match="Graph file not found"):
            load_graph(missing_file)

    def test_load_invalid_json(self, tmp_path):
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_graph(invalid_file)


class TestEnsureDataRoot:
    """Tests for data root validation."""

    def test_ensure_valid_directory(self, tmp_path):
        # Should not raise any exception
        ensure_data_root(tmp_path)

    def test_ensure_missing_directory(self, tmp_path):
        missing_dir = tmp_path / "missing"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            ensure_data_root(missing_dir)

    def test_ensure_not_directory(self, tmp_path):
        file_path = tmp_path / "file.txt"
        file_path.write_text("not a directory")
        with pytest.raises(NotADirectoryError, match="is not a directory"):
            ensure_data_root(file_path)


class TestListAvailableGraphs:
    """Tests for listing available graphs."""

    def test_list_graphs_in_directory(self, tmp_path):
        (tmp_path / "graph1.json").write_text("{}")
        (tmp_path / "graph2.json").write_text("{}")
        (tmp_path / "not_json.txt").write_text("text")

        graphs = list_available_graphs(tmp_path)
        assert len(graphs) == 2
        assert all(g.suffix == ".json" for g in graphs)

    def test_list_graphs_missing_directory(self, tmp_path):
        missing_dir = tmp_path / "missing"
        graphs = list_available_graphs(missing_dir)
        assert graphs == []

    def test_list_graphs_empty_directory(self, tmp_path):
        graphs = list_available_graphs(tmp_path)
        assert graphs == []


class TestCommandRun:
    """Tests for the run command."""

    def test_command_run_success(self, tmp_path, capsys):
        # Create data root
        data_root = tmp_path / "data"
        data_root.mkdir()

        # Create valid graph
        graph_file = tmp_path / "graph.json"
        graph_data = {
            "name": "Test Pipeline",
            "description": "Test",
            "nodes": [
                {"id": "source", "name": "Source", "type": "source", "inputs": [], "outputs": ["data"]},
                {"id": "sink", "name": "Sink", "type": "sink", "inputs": ["data"], "outputs": []},
            ],
        }
        graph_file.write_text(json.dumps(graph_data))

        # Mock args
        class Args:
            def __init__(self):
                self.data_root = str(data_root)
                self.graph = str(graph_file)

        result = command_run(Args())
        assert result == 0

        captured = capsys.readouterr()
        assert "Test Pipeline" in captured.out
        assert "Inputs validated" in captured.out

    def test_command_run_missing_data_root(self, tmp_path):
        graph_file = tmp_path / "graph.json"
        graph_file.write_text('{"name":"Test","description":"Test","nodes":[]}')

        class Args:
            def __init__(self):
                self.data_root = str(tmp_path / "missing")
                self.graph = str(graph_file)

        with pytest.raises(FileNotFoundError):
            command_run(Args())

    def test_command_run_invalid_graph(self, tmp_path):
        data_root = tmp_path / "data"
        data_root.mkdir()

        # Create invalid graph (empty name)
        graph_file = tmp_path / "graph.json"
        graph_data = {
            "name": "",
            "description": "Test",
            "nodes": [{"id": "node1", "name": "Node", "type": "type", "inputs": [], "outputs": []}],
        }
        graph_file.write_text(json.dumps(graph_data))

        class Args:
            def __init__(self):
                self.data_root = str(data_root)
                self.graph = str(graph_file)

        with pytest.raises(ValueError, match="Pipeline name is required"):
            command_run(Args())


class TestCommandListGraphs:
    """Tests for the list-graphs command."""

    def test_command_list_graphs_with_graphs(self, tmp_path, capsys):
        (tmp_path / "graph1.json").write_text("{}")
        (tmp_path / "graph2.json").write_text("{}")

        class Args:
            def __init__(self):
                self.graphs_dir = tmp_path

        result = command_list_graphs(Args())
        assert result == 0

        captured = capsys.readouterr()
        assert "graph1.json" in captured.out
        assert "graph2.json" in captured.out

    def test_command_list_graphs_empty(self, tmp_path, capsys):
        class Args:
            def __init__(self):
                self.graphs_dir = tmp_path

        result = command_list_graphs(Args())
        assert result == 1

        captured = capsys.readouterr()
        assert "No graph files found" in captured.out


class TestMain:
    """Tests for the main entry point."""

    def test_main_run_command(self, tmp_path):
        data_root = tmp_path / "data"
        data_root.mkdir()

        graph_file = tmp_path / "graph.json"
        graph_data = {
            "name": "Test",
            "description": "Test",
            "nodes": [
                {"id": "node1", "name": "Node", "type": "source", "inputs": [], "outputs": ["data"]},
                {"id": "node2", "name": "Node2", "type": "sink", "inputs": ["data"], "outputs": []},
            ],
        }
        graph_file.write_text(json.dumps(graph_data))

        result = main(["run", "--data-root", str(data_root), "--graph", str(graph_file)])
        assert result == 0

    def test_main_list_graphs_command(self, tmp_path):
        (tmp_path / "graph.json").write_text("{}")
        result = main(["list-graphs", "--graphs-dir", str(tmp_path)])
        assert result == 0

    def test_main_file_not_found_error(self, tmp_path, capsys):
        result = main(["run", "--data-root", str(tmp_path / "missing"), "--graph", "graph.json"])
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_main_invalid_json_error(self, tmp_path, capsys):
        data_root = tmp_path / "data"
        data_root.mkdir()

        graph_file = tmp_path / "invalid.json"
        graph_file.write_text("{ invalid json }")

        result = main(["run", "--data-root", str(data_root), "--graph", str(graph_file)])
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_main_validation_error(self, tmp_path, capsys):
        data_root = tmp_path / "data"
        data_root.mkdir()

        # Create graph with validation error (empty name)
        graph_file = tmp_path / "graph.json"
        graph_file.write_text('{"name":"","description":"Test","nodes":[{"id":"n","name":"N","type":"t","inputs":[],"outputs":[]}]}')

        result = main(["run", "--data-root", str(data_root), "--graph", str(graph_file)])
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "Pipeline name is required" in captured.err


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
