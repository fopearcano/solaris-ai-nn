#!/usr/bin/env python3
"""Sign drift demo: source drift, ambiguity increase, LOGOS recommendation.

    python examples/run_sign_drift_demo.py --state-dir .solaris_ai_nn_semiogenesis/test_sign_drift

Observes one sign twice with changed grounding (new modality + source + rising
ambiguity) and shows the visible drift report and its LOGOS-tension recommendation.
Drift is not automatically bad -- it must be visible.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.semiogenesis import InternalSign, SignDriftDetector, SignKind


def main():
    parser = argparse.ArgumentParser(description="Sign drift demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_semiogenesis/test_sign_drift")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    detector = SignDriftDetector()
    sign = InternalSign(kind=SignKind.MODALITY_NATIVE,
                        modality_distribution={"radio_frequency": 4},
                        source_distribution={"rf_feed": 4})

    first = detector.observe(sign)
    # The sign's grounding broadens (new modality, new source, more ambiguity).
    sign.modality_distribution["vibration"] = 2
    sign.modality_distribution["thermal"] = 1
    sign.source_distribution["other_feed"] = 2
    sign.ambiguity_score = 0.7
    second = detector.observe(sign)

    print("=== Sign drift demo ===")
    print(f"first observation drift : {first.drifted}")
    print(f"second observation drift: {second.drifted} kinds={second.kinds}")
    print(f"severity                : {second.severity}")
    print(f"recommend LOGOS tension : {second.recommend_logos_tension}")
    print(f"recommend concept split : {second.recommend_concept_split}")
    print("note: drift is made visible (not automatically bad); severe drift can "
          "recommend a LOGOS tension or a concept split.")


if __name__ == "__main__":
    main()
