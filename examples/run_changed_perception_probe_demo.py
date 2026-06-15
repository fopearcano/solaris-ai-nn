#!/usr/bin/env python3
"""Changed perception probe demo: early vs late response to similar stimuli.

    python examples/run_changed_perception_probe_demo.py --state-dir .solaris_ai_nn_state/test_changed_perception

Runs the bounded organismic scenario and then compares the organism's early
response to a stimulus against its late response: receptor sensitivity delta,
baseline delta, novelty-response delta, and attention priority delta. A no-change
result is reported honestly.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.organismic_demo import (
    MinimalFieldOrganismRunner,
    OrganismicDemoConfig,
)


def main():
    parser = argparse.ArgumentParser(description="Changed perception probe demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_changed_perception")
    args = parser.parse_args()

    runner = MinimalFieldOrganismRunner(
        state_dir=args.state_dir, config=OrganismicDemoConfig(seed=7))
    runner.run()
    probe = runner.probe_result

    print("=== Changed perception probe demo ===")
    print(f"changed-perception score: {probe.changed_perception_score}")
    print(f"changed                 : {probe.changed}")
    print("aggregate metrics:")
    for m in probe.metrics:
        print(f"  {m.name:>34}: early={m.early:.3f} late={m.late:.3f} "
              f"delta={m.delta:.3f} changed={m.changed}")
    print("per-modality early vs late:")
    for modality, info in probe.per_modality.items():
        print(f"  {modality:>18}: sensitivity_delta="
              f"{info['sensitivity_delta']:.3f} "
              f"novelty_response_delta={info['novelty_response_delta']:.3f}")
    for note in probe.notes:
        print(f"note                  : {note}")
    print("disclaimer            : changed response structure only; not "
          "consciousness or understanding.")


if __name__ == "__main__":
    main()
