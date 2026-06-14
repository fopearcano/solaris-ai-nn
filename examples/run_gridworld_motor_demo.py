#!/usr/bin/env python3
"""GridWorld motor demo: simulated embodiment in a sandbox body.

    python examples/run_gridworld_motor_demo.py --state-dir .solaris_ai_nn_pilot3/gridworld

Runs the embodiment sandbox over a short sequence of moves in a GridWorld body.
Each action passes the gated pipeline (ledger -> contract -> veto -> firewall ->
simulated actuator -> ledger -> consequence model). The actions run inside the
sandbox only; an always-on firewall blocks any real-world attempt and the motor
membrane never has real-world authority.
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


def main():
    parser = argparse.ArgumentParser(description="GridWorld motor demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot3/gridworld")
    parser.add_argument("--steps", type=int, default=8)
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    rt = EmbodimentSandboxRuntime(
        state_dir=args.state_dir, profile_id="gridworld_minimal",
        enable_gridworld=True, seed=7)
    rt.initialize()

    sequence = [
        MotorActionType.LOOK, MotorActionType.MOVE_EAST,
        MotorActionType.MOVE_EAST, MotorActionType.MOVE_SOUTH,
        MotorActionType.INSPECT_BOUNDARY, MotorActionType.MOVE_WEST,
        MotorActionType.REST, MotorActionType.LOOK,
    ][:args.steps]

    results = []
    for kind in sequence:
        action = MotorAction(kind, scope=MotorActionScope.SANDBOX_ONLY)
        results.extend(rt.step([action]))

    summary = rt.summary()
    snap = rt.snapshot()
    path = os.path.join(args.state_dir, "gridworld_motor.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "world": snap.get("world")}, fh,
                  indent=2, default=str)

    print("=== GridWorld motor demo (simulated embodiment) ===")
    for kind, r in zip(sequence, results):
        eff = (r.get("result", {}) or {}).get("effect_summary", r["status"])
        print(f"  {kind:<18} -> {r['status']:<22} {eff}")
    print(f"actions proposed       : {summary['action_count']}")
    print(f"executed in simulation : {summary['simulated_action_count']}")
    print(f"vetoed                 : {summary['veto_count']}")
    print(f"blocked real-world     : {summary['blocked_real_world_count']}")
    print(f"real_world_authority   : {summary['real_world_authority']}")
    print(f"sandbox health         : {summary['sandbox_health']}")
    print(f"written                : {path}")


if __name__ == "__main__":
    main()
