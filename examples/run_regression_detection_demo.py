#!/usr/bin/env python3
"""Regression detection demo: prediction decline -> regression + auto-regen.

    python examples/run_regression_detection_demo.py --state-dir .solaris_ai_nn_development/test_regression

Drives a developmental runtime where prediction skill and concept stability decline
across ticks, so a regression is detected (with an auto-regeneration recommendation
when severe). Regression is made visible.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_life import LongHorizonDevelopmentalRuntime


def main():
    parser = argparse.ArgumentParser(description="Regression detection demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_development/test_regression")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    ont = {"proto_concept_count": 10, "stable_concept_count": 8}
    cog = {"prediction_success_rate": 0.8, "failed_prediction_count": 1}
    modules = {"perceptual_ontogenesis": ont, "sensorium_cognition": cog,
               "perceptual_metabolism": {"source_diet_diversity": 0.5}}
    dev = LongHorizonDevelopmentalRuntime(state_dir=args.state_dir,
                                          modules=modules, max_ticks=5)
    for tick in range(5):
        # Prediction and concept stability decline sharply.
        cog["prediction_success_rate"] = max(
            0.0, cog["prediction_success_rate"] - 0.25)
        ont["stable_concept_count"] = max(0, ont["stable_concept_count"] - 3)
        dev.update(tick=tick)

    status = dev.developmental_status()
    print("=== Regression detection demo ===")
    print(f"regressions detected  : {status['regression_count']}")
    for r in dev.regression_detector.regressions:
        print(f"  reason={r.reason} magnitude={r.magnitude} "
              f"auto_regen={r.recommend_auto_regeneration}")
    print("note: regression is made visible; severe regression may recommend an "
          "auto-regeneration check, and regressions are preserved as evidence.")


if __name__ == "__main__":
    main()
