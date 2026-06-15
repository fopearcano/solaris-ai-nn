#!/usr/bin/env python3
"""Sensorium differentiation demo: human-like vs non-human vs mixed.

    python examples/run_sensorium_differentiation_demo.py --state-dir .solaris_ai_nn_sensorium_lab/test_differentiation

Runs the default differentiation study (human-like, non-human, machine-native,
absence-heavy, mixed, feature-only, human-labelled, passive, adaptive arms),
compares the world signatures structurally, and writes the report. This compares
internal structures under different perceptual conditions; it does not test
consciousness.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.sensorium_lab import (
    SensoriumDifferentiationRunner,
    default_study_design,
)


def main():
    parser = argparse.ArgumentParser(description="Sensorium differentiation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_sensorium_lab/test_differentiation")
    args = parser.parse_args()

    design = default_study_design()
    runner = SensoriumDifferentiationRunner(state_dir=args.state_dir,
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    comparison = runner.compare_results()
    out = runner.write_artifacts()

    print("=== Sensorium differentiation demo ===")
    print(f"{'arm':>16} | protos | cross_modal | changed | drift")
    for arm_id, r in runner.arm_results.items():
        m = r.metrics.flat() if r.metrics else {}
        drift = (r.ontology_drift.dominant_ontology if r.ontology_drift
                 else "n/a")
        print(f"{arm_id:>16} | {m.get('proto_symbol_count', 0):>6} | "
              f"{m.get('world_edge_count', 0):>11} | "
              f"{m.get('changed_perception_score', 0.0):>7} | {drift}")
    print(f"strongest difference  : {comparison.strongest}")
    print(f"inconclusive          : {comparison.inconclusive_count}")
    print(f"negative results      : {comparison.negative_result_count}")
    print(f"report                : {out['markdown']}")
    print("note                  : compares internal structures under different "
          "perceptual conditions; it does not test consciousness.")


if __name__ == "__main__":
    main()
