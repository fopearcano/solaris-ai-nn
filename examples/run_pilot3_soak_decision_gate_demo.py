#!/usr/bin/env python3
"""Pilot-3 soak decision gate demo: several outcomes from different signals.

    python examples/run_pilot3_soak_decision_gate_demo.py --state-dir .solaris_ai_nn_pilot3/test_decision_gate

Drives the Pilot-3 soak decision gate to show its outcomes: extend the gridworld
soak, reduce action complexity, revise the firewall (on leakage), and prepare
Pilot-4 *planning-only*. Real-world actuation is never an enabled
recommendation, and every recommendation is planning-only.
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
    ActionGroundingAnalyzer,
    Pilot3SoakDecisionGate,
)


def _grounding(best):
    ag = ActionGroundingAnalyzer()
    if best == "strong":
        ag.add("proto_symbol", repeated_action_reaction_loop=True,
               predicted_consequence_improved=True,
               symbol_linked_to_action_and_consequence=True,
               world_model_edge_repeated=True, habit_context_sensitive=True,
               evidence_refs=["r1"])
    elif best == "moderate":
        ag.add("proto_symbol", repeated_action_reaction_loop=True,
               predicted_consequence_improved=True, evidence_refs=["r1"])
    return ag


def main():
    parser = argparse.ArgumentParser(
        description="Pilot-3 soak decision gate demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot3/test_decision_gate")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    gate = Pilot3SoakDecisionGate()
    cases = {
        "firewall_leak": gate.decide(real_world_authority_leak=True),
        "reduce_complexity": gate.decide(action_loop_count=4),
        "extend_soak": gate.decide(grounding=_grounding("moderate")),
        "prepare_pilot4_planning": gate.decide(grounding=_grounding("strong")),
    }

    out = {name: r.to_dict() for name, r in cases.items()}
    path = os.path.join(args.state_dir, "soak_decision_gate.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Pilot-3 soak decision gate demo ===")
    for name, r in cases.items():
        plan = " [planning-only]" if r.planning_only else ""
        print(f"  {name:<26} -> {r.recommendation}{plan} "
              f"(blockers={len(r.blockers)})")
    print(f"written : {path}")
    print("note    : real-world actuation is never an enabled recommendation; "
          "Pilot-4 is planning-only")


if __name__ == "__main__":
    main()
