#!/usr/bin/env python3
"""Concept stabilization/decay demo: stable, decaying, and rejected concepts.

    python examples/run_concept_stabilization_decay_demo.py --state-dir .solaris_ai_nn_ontogenesis/test_stabilization_decay

Builds three proto-concepts by hand -- one well-grounded (stabilizes), one that
stops being useful (decays), and one false pattern (rejected) -- and shows the
evidence-backed stabilization/decay decisions. Decay never deletes evidence.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.perceptual_ontogenesis import (
    ConceptDecayEngine,
    ConceptStabilizationEngine,
    ProtoConcept,
    ProtoConceptKind,
)


def main():
    parser = argparse.ArgumentParser(
        description="Concept stabilization/decay demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_ontogenesis/test_stabilization_decay")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    stabilizer = ConceptStabilizationEngine()
    decayer = ConceptDecayEngine()

    strong = ProtoConcept(
        kind=ProtoConceptKind.MODALITY_NATIVE,
        modality_distribution={"radio_frequency": 5, "alien_echo": 3},
        source_distribution={"rf_feed": 5, "echo_feed": 3},
        recurrence_count=5, stability_score=0.6, prediction_utility=0.7,
        compression_utility=0.7, attention_utility=0.6)
    useless = ProtoConcept(
        kind=ProtoConceptKind.MODALITY_NATIVE,
        modality_distribution={"radio_frequency": 4}, recurrence_count=4,
        prediction_utility=0.0, compression_utility=0.0, attention_utility=0.0)
    false_pattern = ProtoConcept(
        kind=ProtoConceptKind.UNKNOWN,
        modality_distribution={"radio_frequency": 1}, recurrence_count=1,
        stability_score=0.0, attention_utility=0.0)

    print("=== Concept stabilization/decay demo ===")
    for label, concept in (("well-grounded", strong),
                           ("no-longer-useful", useless),
                           ("false-pattern", false_pattern)):
        res = stabilizer.stabilize(concept)
        decay = decayer.evaluate(concept, seen_this_tick=True)
        print(f"{label:18s}: stability={res.stability_score} "
              f"status={concept.status} fixture_only={res.fixture_only} "
              f"decay={decay.decayed} reasons={decay.reasons}")
    print("note: stability is provisional (stable does not mean true); decayed/"
          "rejected concepts remain historically visible -- evidence is never "
          "deleted.")


if __name__ == "__main__":
    main()
