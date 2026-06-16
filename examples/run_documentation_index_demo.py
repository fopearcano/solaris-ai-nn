#!/usr/bin/env python3
"""Documentation index demo: generated docs, missing docs, docs index.

    python examples/run_documentation_index_demo.py --state-dir .solaris_ai_nn_docs/test_index --docs-dir docs/whitepaper

Builds the documentation and then the documentation index, showing which documents
are present and which are missing (including optional alpha / scientific-claim /
review reports). Missing documents are listed explicitly and never hidden.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.architecture_book import (
    ArchitectureBookRuntime,
    DocumentationIndexBuilder,
)


def main():
    parser = argparse.ArgumentParser(description="Documentation index demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_docs/test_index")
    parser.add_argument("--docs-dir", type=str, default="docs/whitepaper",
                        dest="docs_dir")
    args = parser.parse_args()

    # Build the docs first so the index has something to point at.
    ArchitectureBookRuntime(state_dir=args.state_dir,
                            docs_dir=args.docs_dir).run()
    index = DocumentationIndexBuilder(docs_dir=args.docs_dir).build()
    d = index.to_dict()

    print("=== Documentation index demo ===")
    print(f"  entries: {d['documentation_index_entry_count']} "
          f"(present {d['present_document_count']}, missing "
          f"{d['missing_document_count']})")
    print("\n  present documents:")
    for e in index.present():
        print(f"    - {e['label']}: {e['path']}")
    print("\n  missing documents (shown honestly):")
    for e in index.missing():
        print(f"    - {e['label']}: {e['path']}")
    print("note: the documentation index lists generated docs and missing docs "
          "explicitly; missing documents are never hidden, and nothing is "
          "published or uploaded.")


if __name__ == "__main__":
    main()
