#!/usr/bin/env python3
"""Simulation boundary demo: observation, simulation, counterfactual, replay, debug.

    python examples/run_simulation_boundary_demo.py --state-dir .solaris_ai_nn_self_boundary/test_simulation_boundary

Marks records with their boundary markers and shows that simulation, counterfactual,
and debug-truth records are blocked from being used as observation, while a real
observation is allowed.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.self_boundary import BoundaryMarker, SimulationBoundaryValidator


def main():
    parser = argparse.ArgumentParser(description="Simulation boundary demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_self_boundary/test_simulation_boundary")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    v = SimulationBoundaryValidator()
    records = [
        ("obs_1", BoundaryMarker.OBSERVATION),
        ("sim_1", BoundaryMarker.SIMULATION),
        ("cf_1", BoundaryMarker.COUNTERFACTUAL),
        ("replay_1", BoundaryMarker.REPLAY),
        ("debug_1", BoundaryMarker.DEBUG_TRUTH),
    ]
    print("=== Simulation boundary demo ===")
    for ref, marker in records:
        v.mark(ref, marker)
        allowed = v.validate_use_as_observation(ref, marker)
        print(f"  {ref:10s} marker={marker:14s} usable_as_observation={allowed}")
    print(f"boundary violations   : {v.warning_count()} "
          "(non-observation markers blocked from perception)")
    print(f"boundary integrity    : {v.integrity()}")
    print("note: simulation must never become observation; counterfactual must "
          "never overwrite memory of real events; debug truth must never enter "
          "cognition as sensory evidence.")


if __name__ == "__main__":
    main()
