#!/usr/bin/env python3
"""Gloss/contamination demo: approximate gloss + human-label contaminated sign.

    python examples/run_gloss_contamination_demo.py --state-dir .solaris_ai_nn_semiogenesis/test_gloss_contamination

Builds a feature-grounded sign and a human-label contaminated sign, generates
approximate debug glosses, and runs the contamination analyzer. Gloss is approximate
and never ground truth; contaminated signs remain usable but are marked.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.semiogenesis import (
    GlossBuilder,
    InternalSign,
    SignContaminationAnalyzer,
    SignGrounding,
    SignKind,
)


def main():
    parser = argparse.ArgumentParser(description="Gloss/contamination demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_semiogenesis/test_gloss_contamination")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    gloss_builder = GlossBuilder()
    analyzer = SignContaminationAnalyzer()

    feature_grounded = InternalSign(
        kind=SignKind.MODALITY_NATIVE, grounding=SignGrounding.CONCEPT_GROUNDED,
        modality_distribution={"radio_frequency": 6}, grounding_score=0.8)
    contaminated = InternalSign(
        kind=SignKind.HUMAN_LABEL_CONTAMINATED,
        grounding=SignGrounding.LABEL_GROUNDED,
        modality_distribution={"human_textual": 6}, grounding_score=0.1)

    print("=== Gloss/contamination demo ===")
    for label, sign in (("feature-grounded", feature_grounded),
                        ("label-contaminated", contaminated)):
        gloss = gloss_builder.build(sign)
        rep = analyzer.analyze(sign)
        print(f"{label:18s}: code={sign.sign_code}")
        print(f"  gloss        : {gloss.text}")
        print(f"  gloss status : {gloss.status}")
        print(f"  contamination: score={rep.contamination_score} "
              f"feature_grounded={rep.feature_grounded} flags={rep.flags}")
    print("note: any human-readable gloss is an approximate debug annotation, "
          "never ground truth and never the internal sign; contaminated signs "
          "remain usable but are clearly marked.")


if __name__ == "__main__":
    main()
