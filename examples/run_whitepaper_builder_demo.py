#!/usr/bin/env python3
"""Whitepaper builder demo: technical overview, whitepaper, safety disclaimers.

    python examples/run_whitepaper_builder_demo.py --state-dir .solaris_ai_nn_docs/test_whitepaper --docs-dir docs/whitepaper

Builds the technical overview and full whitepaper and prints their explicit
non-claims and safety disclaimers. Both documents state that Solaris-AI-NN is a
research architecture, that "organismic" is a metaphor, and that the system proves
nothing about consciousness/life/agency.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.architecture_book import (
    ArchitectureBookSafetyValidator,
    TechnicalWhitepaperBuilder,
)


def main():
    parser = argparse.ArgumentParser(description="Whitepaper builder demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_docs/test_whitepaper")
    parser.add_argument("--docs-dir", type=str, default="docs/whitepaper",
                        dest="docs_dir")
    args = parser.parse_args()
    os.makedirs(args.docs_dir, exist_ok=True)

    wp = TechnicalWhitepaperBuilder()
    overview = wp.build_overview()
    whitepaper = wp.build_whitepaper()
    v = ArchitectureBookSafetyValidator()

    overview_path = os.path.join(args.docs_dir,
                                 "SOLARIS_AI_NN_TECHNICAL_OVERVIEW.md")
    whitepaper_path = os.path.join(args.docs_dir, "SOLARIS_AI_NN_WHITEPAPER.md")
    with open(overview_path, "w", encoding="utf-8") as fh:
        fh.write(overview)
    with open(whitepaper_path, "w", encoding="utf-8") as fh:
        fh.write(whitepaper)

    print("=== Whitepaper builder demo ===")
    print(f"  technical overview : {overview_path} ({len(overview.split())} words)")
    print(f"  whitepaper         : {whitepaper_path} ({len(whitepaper.split())} "
          "words)")
    print("  explicit non-claims:")
    for c in wp.non_claims():
        print(f"    - {c}")
    print(f"  overview claim-safe   : {v.validate_doc_text(overview).safe}")
    print(f"  whitepaper claim-safe : {v.validate_doc_text(whitepaper).safe}")
    print("note: both documents state that Solaris-AI-NN is a research "
          "architecture, that 'organismic' is a metaphor, and that the system "
          "proves nothing about consciousness, sentience, biological life, "
          "personhood, agency, free will, or subjective experience.")


if __name__ == "__main__":
    main()
