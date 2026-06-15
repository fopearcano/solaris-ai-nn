#!/usr/bin/env python3
"""Organismic comparison demo: full adaptive sensorium vs baselines.

    python examples/run_organismic_comparison_demo.py --state-dir .solaris_ai_nn_state/test_organismic_comparison

Replays the same fixture streams through the full adaptive sensorium, a passive
event-list parser, no-adaptation receptors, fixed attention, and human-like-only
/ non-human-only arms, and reports the metrics side by side. A negative result
(full not beating the passive parser) is reported honestly.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.organismic_demo import (
    OrganismicDemoComparison,
    OrganismicDemoConfig,
)


def main():
    parser = argparse.ArgumentParser(description="Organismic comparison demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_organismic_comparison")
    args = parser.parse_args()

    comp = OrganismicDemoComparison(
        state_dir=args.state_dir,
        config=OrganismicDemoConfig(ticks=80, seed=7))
    result = comp.run()

    print("=== Organismic comparison demo ===")
    print(f"{'arm':>18} | changed | cross_modal | proto | grounding")
    for arm in result.arms:
        m = arm.metrics
        print(f"{arm.name:>18} | "
              f"{m.get('changed_perception_score', 0.0):>7} | "
              f"{m.get('cross_modal_relation_count', 0):>11} | "
              f"{m.get('proto_symbol_candidate_count', 0):>5} | "
              f"{m.get('modality_native_grounding_score', 0.0):>9}")
    print(f"full beats passive parser: {result.full_beats_passive}")
    print(f"negative result          : {result.negative_result}")
    print("note                     : compares internal response structure; "
          "makes no claim of consciousness or understanding.")


if __name__ == "__main__":
    main()
