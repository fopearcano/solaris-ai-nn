#!/usr/bin/env python3
"""Action inhibition demo: unsafe/uncertain action inhibited; LOGOS tension.

    python examples/run_action_inhibition_demo.py --state-dir .solaris_ai_nn_action_reaction/test_inhibition

Injects a forbidden external action into the action-reaction loop and shows it
inhibited (safety risk), recorded, and emitting an inhibition-vs-desire LOGOS
tension. Inhibition is not failure -- it protects against unsafe/useless churn.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.action_reaction import (
    ActionCandidateRecord,
    ActionReactionRuntime,
)
from solaris_ai_nn.desire_formation import DesireFormationRuntime


def main():
    parser = argparse.ArgumentParser(description="Action inhibition demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_action_reaction/test_inhibition")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    desire = DesireFormationRuntime(
        state_dir=args.state_dir, metabolism={"novelty_appetite_pressure": 0.6},
        max_ticks=1)
    desire.update(tick=0)
    ar = ActionReactionRuntime(state_dir=args.state_dir, desire=desire,
                               max_ticks=1)
    forbidden = ActionCandidateRecord(kind="actuate_robot")
    ar.update(tick=0, extra_actions=[forbidden])

    status = ar.action_reaction_status()
    tensions = ar.logos_tensions()
    print("=== Action inhibition demo ===")
    print(f"blocked actions       : {status['blocked_action_count']}")
    print(f"inhibitions           : {status['inhibition_count']}")
    for inh in ar.inhibition_engine.inhibitions:
        print(f"  reason={inh.reason} action_kind={inh.action_kind}")
    inhibition_tensions = [t for t in tensions
                           if t.metadata.get("action_reaction_tension")
                           == "inhibition_vs_desire"]
    print(f"LOGOS inhibition tension: {len(inhibition_tensions)}")
    print("note: inhibition is not failure; it protects the system from unsafe "
          "or useless internal churn, and every inhibited action is recorded.")


if __name__ == "__main__":
    main()
