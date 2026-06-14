#!/usr/bin/env python3
"""Pilot-2 comparative demo: nursery-only vs sensory-only vs mixed (cautious).

    python examples/run_pilot2_comparative_demo.py --state-dir .solaris_ai_nn_pilot2/test_comparative

Builds three comparison arms from mock summaries and prints a cautious
comparison. Differences are observed associations, never proven causes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot2 import ComparativeRunDesign
from solaris_ai_nn.post_pilot import classify_sensory_exposure


def main():
    parser = argparse.ArgumentParser(description="Pilot-2 comparative demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot2/test_comparative")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    design = ComparativeRunDesign()
    design.set_arm("nursery_only_baseline", {
        "symbol_stability": 0.50, "ambiguity_ratio": 0.40,
        "prediction_trend": 0.45, "world_model_node_count": 20})
    design.set_arm("sensory_membrane_only", {
        "symbol_stability": 0.58, "ambiguity_ratio": 0.32,
        "prediction_trend": 0.52, "world_model_node_count": 31})
    design.set_arm("mixed_nursery_membrane", {
        "symbol_stability": 0.60, "ambiguity_ratio": 0.30,
        "prediction_trend": 0.55, "world_model_node_count": 35})

    sensory_cmp = design.compare("nursery_only_baseline",
                                 "sensory_membrane_only")
    mixed_cmp = design.compare("nursery_only_baseline",
                               "mixed_nursery_membrane")
    missing = design.compare("nursery_only_baseline", "fixture_replay")

    exposure = classify_sensory_exposure(
        {"symbol_stability": 0.50, "ambiguity_ratio": 0.40,
         "prediction_score": 0.45},
        {"symbol_stability": 0.58, "ambiguity_ratio": 0.32,
         "prediction_score": 0.52, "grounding_quality": "moderate"})

    out = {"sensory_vs_nursery": sensory_cmp.to_dict(),
           "mixed_vs_nursery": mixed_cmp.to_dict(),
           "missing_baseline": missing.to_dict(),
           "exposure_classification": exposure.to_dict()}
    path = os.path.join(args.state_dir, "comparative.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Pilot-2 comparative demo (cautious) ===")
    print(f"sensory vs nursery  : {len(sensory_cmp.metrics)} metrics, "
          f"inconclusive={sensory_cmp.inconclusive}")
    print(f"mixed vs nursery    : {len(mixed_cmp.metrics)} metrics")
    print(f"missing baseline arm: inconclusive={missing.inconclusive}")
    print(f"exposure verdict    : {exposure.classification}")
    print(f"written             : {path}")
    print("note                : observed associations only, not proven "
          "causes")


if __name__ == "__main__":
    main()
