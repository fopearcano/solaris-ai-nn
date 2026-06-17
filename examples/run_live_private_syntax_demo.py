#!/usr/bin/env python3
"""Live private syntax demo: relation graph, weak relation, blocked relation.

    python examples/run_live_private_syntax_demo.py --state-dir .solaris_ai_nn_live/syntax_demo

Builds an operational private-syntax graph over generated sign candidates (signs that
share a source/modality or both link absence become related), and also prints the
bundled illustrative relation fixture (including an uncertain relation and a blocked
contaminated relation). Private syntax is operational relation structure -- not
language grammar and not semantics.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_semiogenesis import (
    ConceptInputLoader,
    FirstLiveSemiogenesisRuntime,
)

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "live_semiogenesis")


def main():
    parser = argparse.ArgumentParser(description="Live private syntax demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/syntax_demo")
    args = parser.parse_args()

    # Build a real syntax graph from generated candidates.
    recs = json.load(open(os.path.join(_FIXTURES,
                                       "sample_live_concepts.json")))["records"]
    concepts = ConceptInputLoader().from_records(recs, synthetic=True).eligible
    # Add a contaminated concept so a blocked relation appears.
    cdata = json.load(open(os.path.join(_FIXTURES,
                                        "sample_contaminated_signs.json")))
    contaminated = ConceptInputLoader().from_records(
        cdata["records"], synthetic=True).concepts
    rt = FirstLiveSemiogenesisRuntime(state_dir=args.state_dir,
                                      allow_limited_birth=True)
    rt.analyze_concepts(concepts + contaminated)
    g = rt.syntax_graph

    print("=== Live private syntax demo ===")
    print(f"  relations        : {g.get('live_private_syntax_relation_count')} "
          f"(blocked {g.get('blocked_relation_count')})")
    for rel in g.get("relations", []):
        print(f"    - {rel['source_sign']} --{rel['relation_type']}--> "
              f"{rel['target_sign']} [{rel['strength']}] "
              f"blocked={rel['blocked']}")

    print("  illustrative relation fixture:")
    fixture = json.load(open(os.path.join(_FIXTURES,
                                          "sample_private_syntax.json")))
    for rel in fixture["relations"]:
        print(f"    - {rel['relation_type']} ({rel['strength']}) "
              f"blocked={rel['blocked']}")
    print("note             : private syntax is operational relation structure, "
          "not language grammar or semantics. Relations require evidence; weak "
          "relations are marked weak/uncertain; contaminated relations are "
          "blocked.")


if __name__ == "__main__":
    main()
