#!/usr/bin/env python3
"""Architecture book demo: collect sources, build whitepaper, book, docs index.

    python examples/run_architecture_book_demo.py --state-dir .solaris_ai_nn_docs/test_book --docs-dir docs/whitepaper

Runs the bounded documentation generator: collects local sources read-only, builds
the technical overview, whitepaper, architecture book, module map, roadmap, safety
boundaries, glossary, appendices, and documentation index, and writes the build
report. It writes local Markdown only -- it publishes nothing, uploads nothing,
calls no Git/GitHub, executes no experiment, and makes no consciousness/life/agency
claim.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.architecture_book import ArchitectureBookRuntime


def main():
    parser = argparse.ArgumentParser(description="Architecture book demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_docs/test_book")
    parser.add_argument("--docs-dir", type=str, default="docs/whitepaper",
                        dest="docs_dir")
    args = parser.parse_args()

    rt = ArchitectureBookRuntime(state_dir=args.state_dir, docs_dir=args.docs_dir)
    rt.run()
    rt.write_artifacts()
    st = rt.documentation_status()

    print("=== Architecture book demo ===")
    print(f"  sources collected     : {st['documentation_source_count']} "
          f"(missing {st['missing_documentation_source_count']})")
    print(f"  documents generated   : {st['generated_document_count']}")
    print(f"  chapters              : {st['generated_chapter_count']} "
          f"(skipped {st['skipped_chapter_count']})")
    print(f"  diagrams / glossary   : {st['generated_diagram_count']} / "
          f"{st['glossary_entry_count']}")
    print(f"  ClaimGuard available  : {st['claimguard_available']} "
          f"(doc blocks {st['claimguard_documentation_block_count']})")
    print(f"  whitepaper            : {st['latest_whitepaper_path']}")
    print(f"  architecture book     : {st['latest_architecture_book_path']}")
    print(f"  published / git       : {st['published']} / {st['calls_github']}")
    print("note                    : documentation reconstruction only; writes "
          "local Markdown, publishes nothing, calls no Git/GitHub, executes no "
          "experiment, and makes no consciousness/life/agency claim.")


if __name__ == "__main__":
    main()
