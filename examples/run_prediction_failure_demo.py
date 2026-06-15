#!/usr/bin/env python3
"""Prediction failure demo: prediction, failed prediction, LOGOS tension.

    python examples/run_prediction_failure_demo.py --state-dir .solaris_ai_nn_cognition/test_prediction_failure

Builds signs and a private-syntax pattern, generates a next-sign prediction,
resolves it against observed targets that do NOT contain the predicted sign (so it
fails), and shows the preserved failed prediction and the resulting LOGOS tension.
Failed predictions are useful evidence, never hidden.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.semiogenesis import InternalSign, SignKind
from solaris_ai_nn.semiogenesis.private_syntax import (
    PrivateSyntaxPattern,
    SyntaxRelation,
)
from solaris_ai_nn.sensorium_cognition import PredictionEngine


def main():
    parser = argparse.ArgumentParser(description="Prediction failure demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_cognition/test_prediction_failure")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    a = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="rf:01",
                     modality_distribution={"radio_frequency": 4})
    b = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="vib:01",
                     modality_distribution={"vibration": 4})
    pattern = PrivateSyntaxPattern(relation=SyntaxRelation.PREDICTS,
                                   signs=[a.sign_id, b.sign_id], strength=0.7)

    engine = PredictionEngine()
    result = engine.predict([a, b], [pattern])
    pred = result.predictions[0]
    print("=== Prediction failure demo ===")
    print(f"prediction            : {pred.prediction_type} -> "
          f"{pred.predicted_target} (confidence {pred.confidence})")

    # The predicted sign does NOT appear in the observed targets -> failure.
    pred.resolve(observed_targets=[a.sign_id])
    print(f"resolved outcome      : {pred.outcome}")
    print(f"failed predictions    : {len(result.failed)} (preserved)")
    print(f"success rate          : {result.success_rate}")

    from solaris_ai_nn.logos_complexity.tension import LogosTension, TensionType
    tension = LogosTension(
        tension_type=TensionType.PREDICTION_FAILURE,
        polarity_a="prediction", polarity_b="failure",
        source_modules=["sensorium_cognition"],
        metadata={"prediction_id": pred.prediction_id})
    print(f"LOGOS tension created : {tension.tension_type}")
    print("note: a failed prediction is useful evidence; it is preserved, never "
          "hidden, and it does not diminish into a claim of understanding.")


if __name__ == "__main__":
    main()
