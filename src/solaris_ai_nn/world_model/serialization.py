"""World-model persistence -- JSON, JSONL, DOT, Mermaid. Stdlib only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from .edges import GraphEdge
from .graph import KnowledgeGraph
from .nodes import GraphNode


def save_graph(graph: KnowledgeGraph, path: Union[str, Path]) -> Path:
    """The whole graph as one JSON document."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(graph.to_dict(), fh, indent=2, default=str)
    return path


def load_graph(path: Union[str, Path]) -> KnowledgeGraph:
    path = Path(path)
    if not path.exists():
        return KnowledgeGraph()
    with open(path, "r", encoding="utf-8") as fh:
        return KnowledgeGraph.from_dict(json.load(fh))


def save_graph_jsonl(graph: KnowledgeGraph,
                     nodes_path: Union[str, Path],
                     edges_path: Union[str, Path]) -> Dict[str, str]:
    """Nodes and edges as line-oriented JSONL (diff- and grep-friendly)."""
    nodes_path, edges_path = Path(nodes_path), Path(edges_path)
    nodes_path.parent.mkdir(parents=True, exist_ok=True)
    with open(nodes_path, "w", encoding="utf-8") as fh:
        for node_id in sorted(graph.nodes):
            fh.write(json.dumps(graph.nodes[node_id].to_dict(),
                                default=str) + "\n")
    with open(edges_path, "w", encoding="utf-8") as fh:
        for edge_id in sorted(graph.edges):
            fh.write(json.dumps(graph.edges[edge_id].to_dict(),
                                default=str) + "\n")
    return {"nodes": str(nodes_path), "edges": str(edges_path)}


def load_graph_jsonl(nodes_path: Union[str, Path],
                     edges_path: Union[str, Path]) -> KnowledgeGraph:
    data: Dict[str, Any] = {"nodes": [], "edges": []}
    nodes_path, edges_path = Path(nodes_path), Path(edges_path)
    if nodes_path.exists():
        with open(nodes_path, "r", encoding="utf-8") as fh:
            data["nodes"] = [json.loads(line) for line in fh
                             if line.strip()]
    if edges_path.exists():
        with open(edges_path, "r", encoding="utf-8") as fh:
            data["edges"] = [json.loads(line) for line in fh
                             if line.strip()]
    return KnowledgeGraph.from_dict(data)


def save_graph_exports(graph: KnowledgeGraph,
                       output_dir: Union[str, Path],
                       basename: str = "world_model") -> Dict[str, str]:
    """The standard artifact set under one directory."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": str(save_graph(graph, out / f"{basename}.json")),
    }
    paths.update(save_graph_jsonl(graph, out / f"{basename}_nodes.jsonl",
                                  out / f"{basename}_edges.jsonl"))
    dot_path = out / f"{basename}.dot"
    dot_path.write_text(graph.to_dot(), encoding="utf-8")
    paths["dot"] = str(dot_path)
    mmd_path = out / f"{basename}.mmd"
    mmd_path.write_text(graph.to_mermaid(), encoding="utf-8")
    paths["mermaid"] = str(mmd_path)
    return paths
