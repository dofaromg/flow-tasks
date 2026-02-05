#!/usr/bin/env python3
"""Lightweight runner for the vNext pipeline graphs.

This module intentionally keeps side effects minimal: it loads a graph JSON
specification, validates the requested data root, and prints a friendly summary
of what would be executed. The goal is to provide a predictable entrypoint for
local development and automated environments even when the full pipeline engine
is not present yet.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class GraphNode:
    """Simple representation of a node in the pipeline graph."""

    id: str
    name: str
    type: str
    inputs: List[str]
    outputs: List[str]

    @staticmethod
    def from_dict(node: dict) -> "GraphNode":
        return GraphNode(
            id=str(node.get("id", "")),
            name=str(node.get("name", "")),
            type=str(node.get("type", "")),
            inputs=list(node.get("inputs", [])),
            outputs=list(node.get("outputs", [])),
        )


@dataclass
class PipelineGraph:
    """Container for the pipeline graph description."""

    name: str
    description: str
    nodes: List[GraphNode]

    @staticmethod
    def from_dict(graph: dict) -> "PipelineGraph":
        nodes = [GraphNode.from_dict(node) for node in graph.get("nodes", [])]
        return PipelineGraph(
            name=str(graph.get("name", "")),
            description=str(graph.get("description", "")),
            nodes=nodes,
        )

    def validate(self) -> None:
        """Validate the pipeline graph structure.
        
        Raises:
            ValueError: If the graph structure is invalid.
        """
        # Validate required fields are not empty
        if not self.name:
            raise ValueError("Pipeline name is required and cannot be empty")
        if not self.description:
            raise ValueError("Pipeline description is required and cannot be empty")
        if not self.nodes:
            raise ValueError("Pipeline must contain at least one node")

        # Validate node IDs are unique
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            duplicates = [nid for nid in node_ids if node_ids.count(nid) > 1]
            raise ValueError(f"Duplicate node IDs found: {set(duplicates)}")

        # Validate each node has required fields
        for node in self.nodes:
            if not node.id:
                raise ValueError("Node ID is required and cannot be empty")
            if not node.name:
                raise ValueError(f"Node '{node.id}' name is required and cannot be empty")
            if not node.type:
                raise ValueError(f"Node '{node.id}' type is required and cannot be empty")

        # Build output map for connectivity validation
        output_map = {}
        for node in self.nodes:
            for output in node.outputs:
                if output in output_map:
                    raise ValueError(
                        f"Output '{output}' is produced by multiple nodes: "
                        f"{output_map[output]} and {node.id}"
                    )
                output_map[output] = node.id

        # Validate graph connectivity - all inputs must reference existing outputs
        for node in self.nodes:
            for input_ref in node.inputs:
                if input_ref not in output_map:
                    raise ValueError(
                        f"Node '{node.id}' references input '{input_ref}' "
                        f"which is not produced by any node"
                    )

        # Validate no cycles (DAG validation)
        self._validate_no_cycles()

    def _validate_no_cycles(self) -> None:
        """Validate that the graph is a DAG (no cycles).
        
        Raises:
            ValueError: If a cycle is detected.
        """
        # Build adjacency list for dependency graph
        node_map = {node.id: node for node in self.nodes}
        output_to_node = {}
        for node in self.nodes:
            for output in node.outputs:
                output_to_node[output] = node.id

        # Build graph: node -> list of nodes it depends on
        dependencies = {node.id: [] for node in self.nodes}
        for node in self.nodes:
            for input_ref in node.inputs:
                if input_ref in output_to_node:
                    dependencies[node.id].append(output_to_node[input_ref])

        # DFS to detect cycles
        visited = set()
        rec_stack = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for dependency in dependencies[node_id]:
                if dependency not in visited:
                    if has_cycle(dependency):
                        return True
                elif dependency in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in dependencies:
            if node_id not in visited:
                if has_cycle(node_id):
                    raise ValueError(
                        f"Cycle detected in pipeline graph involving node '{node_id}'"
                    )

    def format_summary(self) -> str:
        lines: List[str] = [f"Pipeline: {self.name}", f"Description: {self.description}"]
        lines.append("Nodes:")
        for node in self.nodes:
            lines.append(
                f"  - {node.id}: {node.name} [{node.type}] inputs={node.inputs} outputs={node.outputs}"
            )
        return "\n".join(lines)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a vNext pipeline graph.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Validate inputs and describe the pipeline run")
    run.add_argument("--data-root", required=True, help="Root directory for pipeline data")
    run.add_argument("--graph", required=True, help="Path to a pipeline graph JSON file")

    list_graphs = subparsers.add_parser("list-graphs", help="List available sample graphs")
    list_graphs.add_argument(
        "--graphs-dir",
        default=Path(__file__).parent / "graphs",
        type=Path,
        help="Directory containing graph JSON files",
    )

    return parser.parse_args(argv)


def load_graph(graph_path: Path) -> PipelineGraph:
    if not graph_path.exists():
        raise FileNotFoundError(f"Graph file not found: {graph_path}")

    with graph_path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in graph file {graph_path}: {exc}") from exc

    return PipelineGraph.from_dict(data)


def ensure_data_root(data_root: Path) -> None:
    if not data_root.exists():
        raise FileNotFoundError(
            f"Data root '{data_root}' does not exist. Create the directory or point to an existing path."
        )
    if not data_root.is_dir():
        raise NotADirectoryError(f"Data root '{data_root}' is not a directory.")


def list_available_graphs(graphs_dir: Path) -> List[Path]:
    if not graphs_dir.exists():
        return []
    return sorted(path for path in graphs_dir.glob("*.json") if path.is_file())


def command_run(args: argparse.Namespace) -> int:
    data_root = Path(args.data_root)
    graph_path = Path(args.graph)

    ensure_data_root(data_root)
    graph = load_graph(graph_path)
    graph.validate()

    print("Inputs validated. Pipeline summary:\n")
    print(graph.format_summary())
    print(
        "\nNote: This lightweight runner validates configuration only. "
        "Integrate your pipeline engine here to execute the graph."
    )
    return 0


def command_list_graphs(args: argparse.Namespace) -> int:
    graphs_dir = Path(args.graphs_dir)
    available = list_available_graphs(graphs_dir)
    if not available:
        print(f"No graph files found in {graphs_dir}.")
        return 1

    print(f"Available graphs in {graphs_dir}:")
    for path in available:
        print(f"- {path.name}")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        if args.command == "run":
            return command_run(args)
        if args.command == "list-graphs":
            return command_list_graphs(args)

        raise ValueError(f"Unknown command: {args.command}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except NotADirectoryError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
