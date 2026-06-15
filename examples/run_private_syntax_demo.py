#!/usr/bin/env python3
"""Private syntax demo: recurring sign sequence, absence relation, utterance.

    python examples/run_private_syntax_demo.py --state-dir .solaris_ai_nn_semiogenesis/test_private_syntax

Builds a handful of internal signs (including an absence sign) and shows the
private syntax patterns and internal utterances that emerge from their relations.
This is internal sign-relation structure, NOT human grammar.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.semiogenesis import (
    InternalSign,
    SignKind,
    SyntaxPatternBuilder,
    UtteranceBuilder,
)


def main():
    parser = argparse.ArgumentParser(description="Private syntax demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_semiogenesis/test_private_syntax")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    rf = InternalSign(kind=SignKind.MODALITY_NATIVE,
                      modality_distribution={"radio_frequency": 4},
                      source_distribution={"rf_feed": 4},
                      proto_concept_refs=["C1"])
    vib = InternalSign(kind=SignKind.MODALITY_NATIVE,
                       modality_distribution={"vibration": 4},
                       source_distribution={"rf_feed": 4},
                       proto_concept_refs=["C2"])
    absence = InternalSign(kind=SignKind.ABSENCE,
                           modality_distribution={"radio_frequency": 1},
                           proto_concept_refs=["C3"])
    signs = [rf, vib, absence]

    relations = [{"source_concept": "C1", "target_concept": "C2",
                  "relation_type": "predicts", "strength": 0.7}]

    builder = SyntaxPatternBuilder()
    patterns = builder.build(signs, concept_relations=relations)
    utterances = UtteranceBuilder().build(patterns)

    print("=== Private syntax demo ===")
    print(f"sign codes            : {[s.sign_code for s in signs]}")
    print(f"syntax pattern count  : {len(patterns)}")
    for p in patterns[:5]:
        print(f"  {p.relation:14s}: {p.signs} (strength {round(p.strength, 2)})")
    print(f"internal utterances   : {len(utterances)}")
    for u in utterances[:3]:
        print(f"  {u.kind:24s}: {u.debug_gloss}")
    print(f"syntax density        : {builder.density(len(signs))}")
    print("note: this is internal sign-relation structure, NOT human grammar; "
          "no subject/verb/object is implied, and utterance glosses are "
          "approximate debug renderings, not human speech.")


if __name__ == "__main__":
    main()
