#!/usr/bin/env python3
"""Short plan demo: tiny suggestion-only plans in a GridWorld sandbox.

    python examples/run_short_plan_demo.py --max-plan-length 3

The planner builds candidate plans from templates, evaluates each with
bounded prospection over a deep-copied GridWorld, selects the best, and
shows the blocked alternatives. Plans longer than the hard maximum are
refused outright.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.embodiment.grid_world import GridWorld
from solaris_ai_nn.executive import (
    ActionPlan,
    PlanStep,
    ShortHorizonPlanner,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Short plan demo")
    parser.add_argument("--max-plan-length", type=int, default=3)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/short_plan")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    world = GridWorld(seed=args.seed)
    planner = ShortHorizonPlanner(
        max_plan_length=min(args.max_plan_length, 3))
    context = {"grid_world": world,
               "world_model_valence": {"rest": 0.3, "avoid_danger": 0.5,
                                       "approach_reward": 0.4,
                                       "look": 0.1},
               # One goal is governance-blocked to show the alternative path.
               "governance_blocks": {"approach_reward":
                                     "operator paused reward approaches"}}

    print("=" * 70)
    print("Solaris-AI-NN -- short plan demo (suggestion-only)")
    print("=" * 70)
    goals = ["rest", "avoid_danger", "approach_reward", "explore_safely",
             "checkpoint_now"]
    plans = []
    for goal in goals:
        plan = planner.build_plan(goal, context)
        planner.evaluate_plan(plan, context)
        plans.append(plan)
        steps = " -> ".join(s.label for s in plan.live_steps()) or "(none)"
        status = "REJECTED" if plan.rejected else "viable  "
        print(f"  [{status}] {goal:18s} {steps}")
        for step in plan.blocked_steps():
            print(f"             blocked: {step.label!r} -- "
                  f"{step.blocked_reason[:54]}")

    selected = planner.select_plan(plans, context)
    print()
    print(f"selected plan: {selected.goal!r}: "
          + " -> ".join(s.label for s in selected.live_steps()))
    prospection = selected.prospection or {}
    print(f"prospection:   outcome={prospection.get('outcome')} "
          f"valence={prospection.get('expected_valence')} "
          f"confidence={prospection.get('confidence')}")
    print()
    # The bound is hard: a seven-step plan is refused, not truncated quietly.
    long_plan = ActionPlan(goal="wander", steps=[
        PlanStep(index=i, label="look") for i in range(1, 8)])
    refusal = planner.safety.validate_plan(long_plan, {})
    print(f"7-step plan refused: {not refusal.safe} "
          f"({refusal.violations[0][:60]})")
    print()
    print("note: plans are suggestion sequences; nothing executes them by "
          "itself, and long-horizon autonomous planning is refused.")


if __name__ == "__main__":
    main()
