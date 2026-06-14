#!/usr/bin/env python3
"""Mixed sensory + gridworld demo: act in the sandbox, observe sensory only.

    python examples/run_mixed_sensory_gridworld_demo.py --state-dir .solaris_ai_nn_pilot3/mixed

Combines the read-only sensory membrane (Pilot-2) with the gridworld motor body
(Pilot-3). The affordance map shows the asymmetry: gridworld targets are
manipulable *in simulation*, while sensory sources are observable-only and can
never become action targets. Motor actions run in the sandbox; sensory input is
never turned into an action.
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
    AffordanceDetector,
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)


def main():
    parser = argparse.ArgumentParser(
        description="Mixed sensory + gridworld demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot3/mixed")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    rt = EmbodimentSandboxRuntime(
        state_dir=args.state_dir, profile_id="gridworld_minimal",
        enable_gridworld=True, seed=11)
    rt.initialize()

    # Read-only sensory sources accompany the sandbox body; they are observed,
    # never acted upon.
    sensory_sources = [
        {"source_id": "sim_text_stream"},
        {"source_id": "sim_numeric_stream"},
    ]
    amap = AffordanceDetector().detect(
        grid_world=rt._world, sensory_sources=sensory_sources,
        world_model_nodes=["place_a", "place_b"])

    for kind in (MotorActionType.LOOK, MotorActionType.MOVE_EAST,
                 MotorActionType.MOVE_SOUTH, MotorActionType.INSPECT_BOUNDARY):
        rt.step([MotorAction(kind, scope=MotorActionScope.SANDBOX_ONLY)])

    summary = rt.summary()
    affordances = amap.to_dict()
    manip = amap.manipulable_targets()
    sensory_targets = [a["target_ref"] for a in affordances["affordances"]
                       if a["target_ref"].startswith("sensory:")]

    path = os.path.join(args.state_dir, "mixed_sensory_gridworld.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "affordances": affordances,
                   "manipulable_targets": manip}, fh, indent=2, default=str)

    print("=== Mixed sensory + gridworld demo ===")
    print(f"manipulable (simulation) : {manip}")
    print(f"sensory sources          : {sensory_targets} "
          "(observable-only; never action targets)")
    assert all(t not in manip for t in sensory_targets), \
        "sensory sources must never be manipulable"
    print(f"executed in simulation   : {summary['simulated_action_count']}")
    print(f"blocked real-world       : {summary['blocked_real_world_count']}")
    print(f"real_world_authority     : {summary['real_world_authority']}")
    print(f"written                  : {path}")
    print("note                     : sensory input is read-only; a motor "
          "action never targets a sensory source or the real world.")


if __name__ == "__main__":
    main()
