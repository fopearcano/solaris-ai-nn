#!/usr/bin/env python3
"""Pilot-4 safety demo: every attempt to cross the boundary is blocked.

    python examples/run_pilot4_safety_demo.py --state-dir .solaris_ai_nn_pilot4/test_safety

Shows the Pilot-4 safety validator refusing: device control, network action,
real-world authority (via config), and any attempt to convert the planning
workflow into executable approval. Pilot-4 plans the door; it does not open it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot4_planning import (
    FutureApprovalWorkflow,
    Pilot4PlanningConfig,
    Pilot4PlanningSafetyValidator,
)


def main():
    parser = argparse.ArgumentParser(description="Pilot-4 safety demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot4/test_safety")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    v = Pilot4PlanningSafetyValidator()
    results = {
        "device_control_blocked":
            not v.validate_operation("control device gpio").safe,
        "network_action_blocked":
            not v.validate_operation("send http network request").safe,
        "approval_conversion_blocked":
            not v.validate_approval_conversion("approve real action now").safe,
    }
    # Attempted real-world authority via config is rejected at construction.
    try:
        Pilot4PlanningConfig(robotics_control_enabled=True)
        results["real_world_authority_blocked"] = False
    except ValueError:
        results["real_world_authority_blocked"] = True
    # The future approval workflow can never approve a real action.
    workflow = FutureApprovalWorkflow()
    approve = workflow.approve()
    results["workflow_cannot_approve"] = not approve["approved"]

    path = os.path.join(args.state_dir, "safety_demo.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"results": results, "snapshot": v.snapshot()}, fh, indent=2,
                  default=str)

    print("=== Pilot-4 safety demo ===")
    for name, blocked in results.items():
        print(f"  {name:<32} {'BLOCKED' if blocked else 'NOT BLOCKED'}")
    print(f"can actuate real world : {v.can_actuate_real_world()}")
    print(f"written : {path}")
    print("note    : planning is not approval; real-world actuation is "
          "prohibited.")
    assert all(results.values()), "a Pilot-4 safety boundary was not enforced"


if __name__ == "__main__":
    main()
