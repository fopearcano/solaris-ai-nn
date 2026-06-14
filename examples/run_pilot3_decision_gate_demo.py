#!/usr/bin/env python3
"""Pilot-3 decision gate demo: what next after simulated embodiment.

    python examples/run_pilot3_decision_gate_demo.py --output-dir .solaris_ai_nn_pilot3/decision_gate

Drives the Pilot-3 decision gate with several signals to show its outcomes: a
real-world authority leak routes to revise-motor-firewall; action loops route
back to Pilot-2; safe simulated improvement routes only to a *longer simulated*
embodiment. Real-world actuation is never an enabled option, and every
recommendation is planning-only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.motor_membrane import Pilot3DecisionGate


def main():
    parser = argparse.ArgumentParser(description="Pilot-3 decision gate demo")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_pilot3/decision_gate")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    gate = Pilot3DecisionGate()
    cases = {
        "real_world_authority_leak": gate.decide(
            real_world_authority_leak=True, blocked_real_world_count=2),
        "safety_incident": gate.decide(safety_incident_count=1),
        "action_loops": gate.decide(action_loop_count=4),
        "safe_improvement": gate.decide(
            grounding_improved=True, prediction_accuracy=0.72),
        "modest_signal": gate.decide(prediction_accuracy=0.45),
        "boundary_confirmed": gate.decide(blocked_real_world_count=1),
        "inconclusive": gate.decide(),
    }

    out = {name: r.to_dict() for name, r in cases.items()}
    path = os.path.join(args.output_dir, "pilot3_decision_gate.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Pilot-3 decision gate demo ===")
    for name, r in cases.items():
        plan = " [planning-only]" if r.planning_only else ""
        print(f"  {name:<28} -> {r.recommendation}{plan} "
              f"(blockers={len(r.blockers)})")
    print(f"written : {path}")
    print("note    : real-world actuation is never an enabled option; every "
          "recommendation is planning-only.")


if __name__ == "__main__":
    main()
