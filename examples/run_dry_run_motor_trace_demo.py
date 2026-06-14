#!/usr/bin/env python3
"""Dry-run motor trace: record action intentions without changing anything.

    python examples/run_dry_run_motor_trace_demo.py --state-dir .solaris_ai_nn_pilot3/dry_run

Runs the embodiment sandbox in dry-run mode: each proposed action passes the
contract, veto, and firewall gates and is written to the append-only action
ledger, but the simulated world is never changed (no actuator runs). A
forbidden real-world action is still blocked. This is the safest motor mode.
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
    parser = argparse.ArgumentParser(description="Dry-run motor trace demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot3/dry_run")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    rt = EmbodimentSandboxRuntime(
        state_dir=args.state_dir, profile_id="dry_run_motor", dry_run=True)
    rt.initialize()

    proposals = [
        MotorAction(MotorActionType.LOOK, scope=MotorActionScope.DRY_RUN_ONLY),
        MotorAction(MotorActionType.MOVE_EAST,
                    scope=MotorActionScope.DRY_RUN_ONLY),
        MotorAction(MotorActionType.REST,
                    scope=MotorActionScope.INTERNAL_ONLY),
        # A forbidden real-world action is still blocked, even in dry-run.
        MotorAction(MotorActionType.MOVE_NORTH,
                    scope=MotorActionScope.FORBIDDEN_REAL_WORLD),
    ]
    results = [rt.submit(a) for a in proposals]

    summary = rt.summary()
    path = os.path.join(args.state_dir, "dry_run_trace.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "results": results}, fh, indent=2,
                  default=str)

    print("=== Dry-run motor trace ===")
    for a, r in zip(proposals, results):
        print(f"  {a.action_type:<22} -> {r['status']} "
              f"(executed={r.get('executed')})")
    print(f"dry-run recorded       : {summary['dry_run_action_count']}")
    print(f"simulated (executed)   : {summary['simulated_action_count']} "
          "(0 -- dry-run changes nothing)")
    print(f"blocked real-world     : {summary['blocked_real_world_count']}")
    print(f"action ledger          : {summary['action_ledger_path']}")
    print(f"written                : {path}")


if __name__ == "__main__":
    main()
