#!/usr/bin/env python3
"""Glossary builder demo: glossary entries + forbidden-overclaim clarifications.

    python examples/run_glossary_builder_demo.py --state-dir .solaris_ai_nn_docs/test_glossary

Builds the technical glossary and shows the entries whose definitions carry an
explicit "not consciousness/life/personhood/agency" clarification, demonstrating
that organismic terms are defined as architectural metaphors.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.architecture_book import ArchitectureBookSafetyValidator, GlossaryBuilder


def main():
    parser = argparse.ArgumentParser(description="Glossary builder demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_docs/test_glossary")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    builder = GlossaryBuilder()
    entries = builder.build()
    print("=== Glossary builder demo ===")
    print(f"  glossary entries: {len(entries)}")
    print("\n  sample entries:")
    for e in entries[:6]:
        print(f"    - {e.term}: {e.definition[:80]}")
    print("\n  forbidden-overclaim clarifications (terms defined as metaphors):")
    markers = ("not consciousness", "not emotion", "not a self", "metaphor",
               "not agency", "not life", "not language", "not understanding",
               "not biological", "not self-awareness", "not feeling")
    for e in entries:
        low = e.definition.lower()
        if any(m in low for m in markers):
            print(f"    - {e.term}: {e.definition[:90]}")
    md = builder.render_md()
    print(f"\n  glossary claim-safe: "
          f"{ArchitectureBookSafetyValidator().validate_doc_text(md).safe}")
    print("note: organismic terms are defined as architectural metaphors; the "
          "glossary makes no claim of consciousness, life, personhood, or agency.")


if __name__ == "__main__":
    main()
