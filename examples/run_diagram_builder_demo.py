#!/usr/bin/env python3
"""Diagram builder demo: architecture, core loop, research cycle Mermaid diagrams.

    python examples/run_diagram_builder_demo.py --state-dir .solaris_ai_nn_docs/test_diagrams

Generates and prints the high-level architecture, organismic core loop, and
research-cycle Mermaid diagrams. Diagrams are Markdown-compatible and imply no
autonomous code modification and no real-world actuation.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.architecture_book import DiagramBuilder, DiagramKind


def main():
    parser = argparse.ArgumentParser(description="Diagram builder demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_docs/test_diagrams")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    builder = DiagramBuilder()
    print("=== Diagram builder demo ===")
    for kind in (DiagramKind.SYSTEM_MAP, DiagramKind.CORE_LOOP,
                 DiagramKind.RESEARCH_CYCLE):
        diagram = builder.build(kind)
        print(f"\n## {diagram.title} ({diagram.kind})")
        print("```mermaid")
        print(diagram.mermaid)
        print("```")
    summary = builder.summary()
    print(f"\ntotal diagram kinds available: {summary['generated_diagram_count']}")
    print("note: Mermaid diagrams are Markdown-compatible and imply no autonomous "
          "code modification and no real-world actuation.")


if __name__ == "__main__":
    main()
