#!/usr/bin/env python3
"""Plateau detection demo: a no-growth stretch -> plateau + recommendation.

    python examples/run_plateau_detection_demo.py --state-dir .solaris_ai_nn_development/test_plateau

Drives a developmental runtime with flat module statuses (no growth) and a narrow
source diet so a plateau is detected with a report-only recommendation. A plateau is
not failure.
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
    parser = argparse.ArgumentParser(description="Plateau detection demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_development/test_plateau")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    # Flat statuses + narrow source diet -> plateau.
    modules = {
        "perceptual_metabolism": {"source_diet_diversity": 0.1,
                                  "overload_state": False},
        "perceptual_ontogenesis": {"proto_concept_count": 3,
                                   "stable_concept_count": 1},
        "sensorium_cognition": {"prediction_success_rate": 0.3},
        "action_reaction": {"no_effect_action_count": 2}}
    dev = LongHorizonDevelopmentalRuntime(state_dir=args.state_dir,
                                          modules=modules, max_ticks=6)
    dev.run_bounded()

    status = dev.developmental_status()
    print("=== Plateau detection demo ===")
    print(f"plateaus detected     : {status['plateau_count']}")
    for p in dev.plateau_detector.plateaus:
        print(f"  reason={p.reason} recommendation='{p.recommendation}'")
    print(f"composite growth      : {status['composite_growth']} (flat)")
    print("note: a plateau is not failure; it may recommend a source-diet "
          "change, consolidation, or a sensorium study -- recommendations are "
          "internal/report-only.")


if __name__ == "__main__":
    main()
