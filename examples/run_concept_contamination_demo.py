#!/usr/bin/env python3
"""Concept contamination demo: feature-grounded vs human-label contaminated.

    python examples/run_concept_contamination_demo.py --state-dir .solaris_ai_nn_ontogenesis/test_contamination

Builds a feature-grounded concept and a human-label contaminated concept and runs
the contamination analyzer. Human-labelled concepts are not forbidden -- they are
marked, and contamination lowers grounding/stability. Labels are never ground
truth.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.perceptual_ontogenesis import (
    ConceptContaminationAnalyzer,
    ProtoConcept,
    ProtoConceptGrounding,
    ProtoConceptKind,
)


def main():
    parser = argparse.ArgumentParser(description="Concept contamination demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_ontogenesis/test_contamination")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    analyzer = ConceptContaminationAnalyzer()

    feature_grounded = ProtoConcept(
        kind=ProtoConceptKind.MODALITY_NATIVE,
        grounding=ProtoConceptGrounding.FEATURE_GROUNDED,
        modality_distribution={"radio_frequency": 6}, recurrence_count=6,
        grounding_score=0.8, compression_utility=0.6, stability_score=0.6)
    contaminated = ProtoConcept(
        kind=ProtoConceptKind.HUMAN_LABEL_CONTAMINATED,
        grounding=ProtoConceptGrounding.LABEL_GROUNDED,
        modality_distribution={"human_textual": 6}, recurrence_count=2,
        grounding_score=0.1, stability_score=0.4)
    contaminated.attach_human_annotation("dog")

    print("=== Concept contamination demo ===")
    for label, concept in (("feature-grounded", feature_grounded),
                           ("label-contaminated", contaminated)):
        rep = analyzer.analyze(concept)
        print(f"{label:18s}: score={rep.contamination_score} "
              f"feature_grounded={rep.feature_grounded} flags={rep.flags}")
    print(f"contaminated ratio    : "
          f"{analyzer.contaminated_ratio([analyzer.analyze(feature_grounded), analyzer.analyze(contaminated)])}")
    print("note: human-labelled concepts are allowed but marked; human labels "
          "are external annotations, never ground truth.")


if __name__ == "__main__":
    main()
