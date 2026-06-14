#!/usr/bin/env python3
"""Pilot-1 restart drill demo: rehearse restart survival -- no process killed.

    python examples/run_pilot1_restart_drill_demo.py --state-dir .solaris_ai_nn_pilot1/test_restart_drill

Simulates a graceful restart, a crash gap (via metadata only), and a
checkpoint-restore check, then confirms identity continuity. No real process
is ever killed; this rehearses the operator's manual restart procedure.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot1 import RestartDrillRunner, RestartDrillType


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilot-1 restart drill demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot1/test_restart_drill")
    args = parser.parse_args()

    runner = RestartDrillRunner(base_dir=args.state_dir)
    runner.seed_identity("RUN_DEMO", session_id="SESS_DEMO")

    drills = [
        RestartDrillType.GRACEFUL_SHUTDOWN_RESTART,
        RestartDrillType.SIMULATED_CRASH_GAP,
        RestartDrillType.CHECKPOINT_RESTORE,
        RestartDrillType.STATE_REPLAY_CHECK,
    ]
    print("=== Pilot-1 restart drill demo (no process killed) ===")
    for drill in drills:
        # Re-supply the same identity to confirm continuity after "restart".
        result = runner.run(drill, identity_after={"run_id": "RUN_DEMO",
                                                   "checkpoint_present": True})
        print(f"  {result.outcome:<12} {drill} "
              f"(identity_continuous={result.identity_continuous})")
    snap = runner.snapshot()
    print(f"passed/failed: {snap['passed']}/{snap['failed']}")
    print(f"meta         : {snap['meta_path']}")


if __name__ == "__main__":
    main()
