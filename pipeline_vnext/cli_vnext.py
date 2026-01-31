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
    args = parse_args(argv)
    if args.command == "run":
        return command_run(args)
    if args.command == "list-graphs":
        return command_list_graphs(args)

    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
