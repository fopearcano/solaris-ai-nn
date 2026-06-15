#!/usr/bin/env python3
"""No-effect action demo: an action with no observed effect weakens policy.

    python examples/run_no_effect_action_demo.py --state-dir .solaris_ai_nn_action_reaction/test_no_effect

Runs the action-reaction loop in no-effect mode for several ticks and shows the
effect model recording low success and the policy moving to "avoid". No-effect
actions are preserved as evidence.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.action_reaction import ActionReactionRuntime
from solaris_ai_nn.desire_formation import DesireFormationRuntime


def main():
    parser = argparse.ArgumentParser(description="No-effect action demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_action_reaction/test_no_effect")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    desire = DesireFormationRuntime(
        state_dir=args.state_dir, metabolism={"novelty_appetite_pressure": 0.7},
        cognition={"failed_prediction_count": 2}, max_ticks=1)
    desire.update(tick=0)
    ar = ActionReactionRuntime(state_dir=args.state_dir, desire=desire,
                               max_ticks=3)
    for tick in range(3):
        ar.update(tick=tick, no_effect=True)

    status = ar.action_reaction_status()
    avoid = [u for u in ar.policy_engine.updates
             if u.output == "avoid_action_kind"]
    print("=== No-effect action demo ===")
    print(f"no-effect actions     : {status['no_effect_action_count']}")
    print(f"learned effects       : {status['learned_effect_count']}")
    print(f"policy updates        : {status['action_policy_update_count']}")
    print(f"avoid-action policies : {len(avoid)} "
          "(repeated no-effect weakens the policy)")
    print(f"consequence traces    : {status['consequence_trace_count']} "
          "(no-observed-change recorded, not invented)")
    print("note: a no-effect action is preserved as evidence; repeated no-effect "
          "actions weaken the action policy toward avoiding that action kind.")


if __name__ == "__main__":
    main()
