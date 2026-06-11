#!/usr/bin/env python3
"""Embodied executive demo: arbitration drives GridWorld suggestions.

    python examples/run_embodied_executive_demo.py --steps 300
    python examples/run_embodied_executive_demo.py --enable-planning

The body senses; homeostasis pressures; the executive arbitrates the body's
suggestion against the desires (with the GridWorld available to prospection
as a deep-copied sandbox); the selected safe simulated action executes only
in simulation. Planning stays off unless the flag is passed.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.embodiment.simulation_runner import (
    SensorimotorSimulationRunner,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Embodied executive demo")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/embodied_executive")
    parser.add_argument("--enable-planning", action="store_true",
                        help="switch to short_plan mode (max 3 steps)")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    runner = SensorimotorSimulationRunner(
        max_steps=args.steps, seed=args.seed, state_dir=args.state_dir,
        enable_homeostasis=True, enable_executive=True,
        executive_mode="short_plan" if args.enable_planning
        else "arbitrated")
    runner.run()
    layer = runner.executive
    summary = layer.summary()

    print("=" * 70)
    print("Solaris-AI-NN -- embodied executive demo (simulation-only)")
    print("=" * 70)
    print(f"steps:               {runner.steps_run} "
          f"(rewards {runner.rewards_consumed}, "
          f"collisions {runner.collisions})")
    print(f"executive mode:      {summary['mode']}")
    print(f"arbitrations:        {summary['decisions']}")
    print(f"selected suggestion: {summary['selected_action_suggestion']}")
    print(f"inhibitions:         {summary['inhibited_candidate_count']}")
    if args.enable_planning and layer.last_plan is not None:
        plan = layer.last_plan
        steps = " -> ".join(s.label for s in plan.live_steps())
        print(f"last plan:           {plan.goal!r}: {steps} "
              f"(rejected: {plan.rejected})")
    print()
    actions = dict(runner.action_counts)
    print(f"executed simulated actions: {actions}")
    blocked = [r for r in runner.action_history if r.blocked_reason]
    print(f"blocked in simulation:      {len(blocked)}")
    print()
    print("note: selections execute only inside the GridWorld simulation, "
          "and only while the executive's mode permits execution.")


if __name__ == "__main__":
    main()
