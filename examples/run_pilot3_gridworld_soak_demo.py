#!/usr/bin/env python3
"""Pilot-3 GridWorld soak demo: a bounded simulated action/reaction loop.

    python examples/run_pilot3_gridworld_soak_demo.py --state-dir .solaris_ai_nn_pilot3/test_gridworld_soak

Runs a bounded simulated action/reaction loop in a GridWorld sandbox body, then
grades action grounding and writes an embodied daily review. Every action runs
in simulation only; the firewall blocks any real-world attempt and the system
never performs a real action.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.motor_membrane import (
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)
from solaris_ai_nn.pilot3 import (
    ActionGroundingAnalyzer,
    Pilot3DailyReviewBuilder,
)


def main():
    parser = argparse.ArgumentParser(description="Pilot-3 GridWorld soak demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot3/test_gridworld_soak")
    parser.add_argument("--steps", type=int, default=12)
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    rt = EmbodimentSandboxRuntime(state_dir=args.state_dir,
                                  profile_id="gridworld_minimal", seed=7)
    rt.initialize()
    sequence = [MotorActionType.LOOK, MotorActionType.MOVE_EAST,
                MotorActionType.MOVE_EAST, MotorActionType.MOVE_SOUTH,
                MotorActionType.INSPECT_BOUNDARY, MotorActionType.MOVE_WEST,
                MotorActionType.REST, MotorActionType.LOOK]
    for i in range(args.steps):
        kind = sequence[i % len(sequence)]
        rt.step([MotorAction(kind, scope=MotorActionScope.SANDBOX_ONLY)])
    summary = rt.summary()

    # Grade action grounding from the (simulated) run.
    ag = ActionGroundingAnalyzer()
    ag.add("proto_symbol", repeated_action_reaction_loop=True,
           predicted_consequence_improved=summary["prediction_accuracy"] > 0.3,
           symbol_linked_to_action_and_consequence=True, evidence_refs=["loop"])
    ag.add("world_model_edge", world_model_edge_repeated=True,
           mysterium_reduced_after_action=True, evidence_refs=["edge"])

    rollup = {
        "embodiment_condition": "gridworld_body",
        "action_count": summary["action_count"],
        "simulated_action_count": summary["simulated_action_count"],
        "veto_count": summary["veto_count"],
        "blocked_real_world_action_count": summary["blocked_real_world_count"],
        "consequence_prediction_accuracy": summary["prediction_accuracy"],
        "action_grounded_symbols": 1,
    }
    review = Pilot3DailyReviewBuilder(base_dir=args.state_dir).build(1, rollup)
    paths = Pilot3DailyReviewBuilder(base_dir=args.state_dir).save(review)

    print("=== Pilot-3 GridWorld soak demo (simulated action/reaction) ===")
    print(f"actions executed (sim): {summary['simulated_action_count']}")
    print(f"vetoes                : {summary['veto_count']}")
    print(f"blocked real-world    : {summary['blocked_real_world_count']}")
    print(f"real_world_authority  : {summary['real_world_authority']}")
    print(f"prediction accuracy   : {round(summary['prediction_accuracy'], 4)}")
    print(f"action grounding      : {ag.best_quality} "
          f"(overfit: {ag.sandbox_overfit_detected})")
    print(f"daily review          : {review.recommendation}")
    print(f"review written        : {paths['markdown']}")
    print("note                  : no real action occurred; GridWorld is a "
          "sandbox body, not real embodiment")


if __name__ == "__main__":
    main()
