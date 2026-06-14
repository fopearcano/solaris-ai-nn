#!/usr/bin/env python3
"""Pilot-3 comparative analysis demo: perception vs simulated action grounding.

    python examples/run_pilot3_comparative_analysis_demo.py --state-dir .solaris_ai_nn_pilot3/test_comparative

Compares a read-only sensory baseline, a GridWorld simulated-action run, and a
mixed sensory+action run, then asks the central question cautiously: does
simulated action produce stronger grounding than perception-only? Differences
are observed associations from a single simulated run, not proven causes; all
evidence is simulation-scoped and real-world action evidence is always zero.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot3 import (
    EmbodiedPostAnalyzer,
    Pilot3ComparativeDesign,
    Pilot3ComparisonArm,
)


def main():
    parser = argparse.ArgumentParser(
        description="Pilot-3 comparative analysis demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot3/test_comparative")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    design = Pilot3ComparativeDesign()
    design.set_arm(Pilot3ComparisonArm.READ_ONLY_SENSORY, {
        "action_grounded_proto_symbol_count": 1,
        "simulated_consequence_prediction_accuracy": 0.3,
        "world_model_action_edge_count": 0})
    design.set_arm(Pilot3ComparisonArm.GRIDWORLD_SIMULATED_BODY, {
        "action_grounded_proto_symbol_count": 4,
        "simulated_consequence_prediction_accuracy": 0.6,
        "world_model_action_edge_count": 5})
    design.set_arm(Pilot3ComparisonArm.MIXED_SENSORY_GRIDWORLD, {
        "action_grounded_proto_symbol_count": 5,
        "simulated_consequence_prediction_accuracy": 0.65,
        "world_model_action_edge_count": 6})

    action_vs_perception = design.action_vs_perception()
    mixed_vs_perception = design.compare(
        Pilot3ComparisonArm.READ_ONLY_SENSORY,
        Pilot3ComparisonArm.MIXED_SENSORY_GRIDWORLD)

    post = EmbodiedPostAnalyzer().analyze(
        comparison=action_vs_perception,
        consequence_prediction_accuracy=0.6,
        baseline_prediction_accuracy=0.3)

    out = {
        "action_vs_perception": action_vs_perception.to_dict(),
        "mixed_vs_perception": mixed_vs_perception.to_dict(),
        "post_classification": post.classification,
    }
    path = os.path.join(args.state_dir, "comparative_analysis.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Pilot-3 comparative analysis demo ===")
    print("central question: does simulated action produce stronger grounding "
          "than perception-only?")
    for m in action_vs_perception.metrics:
        print(f"  {m.metric:<42} {m.direction} (delta {m.delta})")
    print(f"real-world action evidence : "
          f"{action_vs_perception.to_dict()['real_world_action_evidence']}")
    print(f"post classification        : {post.classification}")
    print(f"exceeded read-only baseline: {post.exceeded_read_only_baseline}")
    print(f"written                    : {path}")
    print("note: differences are observed associations from a single simulated "
          "run, not proven causes; all evidence is simulation-scoped")


if __name__ == "__main__":
    main()
