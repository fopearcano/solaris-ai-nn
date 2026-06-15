#!/usr/bin/env python3
"""Proto-concept birth demo: repeated invariant vs single weak event.

    python examples/run_proto_concept_birth_demo.py --state-dir .solaris_ai_nn_ontogenesis/test_concept_birth

Shows that a repeated invariant produces a real (non-weak) concept candidate,
while a single isolated low-novelty event does not produce a stable concept.
Concept birth is conservative and preserves evidence refs.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.perceptual_ontogenesis import (
    ConceptBirthEngine,
    PerceptualAtom,
    PerceptualAtomKind,
)


def main():
    parser = argparse.ArgumentParser(description="Proto-concept birth demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_ontogenesis/test_concept_birth")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    engine = ConceptBirthEngine()

    # A repeated invariant atom (recurrence high) -> a real candidate.
    repeated = PerceptualAtom(
        kind=PerceptualAtomKind.INVARIANT, modality="radio_frequency",
        source_id="rf_feed", recurrence_count=5, novelty=0.6,
        stability_score=0.6, compression_score=0.6, prediction_score=0.6,
        provenance_refs=["invariant:INV_demo"])
    # A single isolated low-novelty flux atom -> no candidate.
    isolated = PerceptualAtom(
        kind=PerceptualAtomKind.FLUX, modality="radio_frequency",
        source_id="rf_feed", recurrence_count=1, novelty=0.1)

    repeated_cands = engine.propose([repeated])
    isolated_cands = engine.propose([isolated])

    print("=== Proto-concept birth demo ===")
    print(f"repeated invariant -> candidates : {len(repeated_cands)}")
    if repeated_cands:
        c = repeated_cands[0]
        print(f"  trigger    : {c.trigger}")
        print(f"  weak       : {c.weak}")
        print(f"  name       : {c.concept.operational_name}")
        print(f"  evidence   : {c.evidence_refs}")
    print(f"isolated event -> candidates     : {len(isolated_cands)}")
    print("note: a single isolated low-novelty event does not justify a stable "
          "concept; concept birth is conservative and evidence-backed.")


if __name__ == "__main__":
    main()
