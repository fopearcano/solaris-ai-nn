#!/usr/bin/env python3
"""Pilot-4 decision gate demo: the strongest move is planning, never acting.

    python examples/run_pilot4_decision_gate_demo.py --state-dir .solaris_ai_nn_pilot4/test_decision_gate

Drives the Pilot-4 decision gate to show its outcomes: remain simulation-only,
repeat Pilot-3, revise the firewall (on a critical finding), and -- at most --
*draft* a future single-action protocol (planning-only). No option enables real
actuation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot4_planning import Pilot4DecisionGate, Pilot4DecisionOption


def main():
    parser = argparse.ArgumentParser(
        description="Pilot-4 decision gate demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot4/test_decision_gate")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    gate = Pilot4DecisionGate()
    cases = {
        "revise_firewall": gate.decide(pilot3_firewall_critical_findings=1),
        "repeat_pilot3": gate.decide(pilot3_data_present=False),
        "remain_simulation_only": gate.decide(consent_complete=False),
        "draft_future_protocol": gate.decide(
            consent_complete=True, threat_model_complete=True,
            audit_requirements_complete=True),
    }
    out = {name: r.to_dict() for name, r in cases.items()}
    path = os.path.join(args.state_dir, "decision_gate.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Pilot-4 decision gate demo ===")
    for name, r in cases.items():
        print(f"  {name:<24} -> {r.recommendation} "
              f"(planning_only={r.planning_only}, "
              f"real_world={r.real_world_actuation_enabled})")
    no_enable = all("enable" not in o for o in Pilot4DecisionOption.ALL)
    print(f"no option enables real actuation : {no_enable}")
    print(f"written : {path}")
    print("note    : the strongest recommendation is planning a future "
          "protocol, not executing one.")


if __name__ == "__main__":
    main()
