#!/usr/bin/env python3
"""Live vs fixture sensorium demo: fixture arm + live arm (inconclusive if absent).

    python examples/run_live_vs_fixture_sensorium_demo.py --state-dir .solaris_ai_nn_sensorium_lab/test_live_vs_fixture

Runs a fixture-replay arm and a live read-only arm. Without governance approval
the live arm is blocked and the live-vs-fixture comparison is inconclusive --
reported honestly rather than failing.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.sensorium_lab import (
    SensoriumDifferentiationRunner,
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
)
from solaris_ai_nn.sensorium_lab.sensorium_profiles import SensoriumProfileType as P


def main():
    parser = argparse.ArgumentParser(description="Live vs fixture sensorium demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_sensorium_lab/test_live_vs_fixture")
    args = parser.parse_args()

    design = SensoriumStudyDesign(ticks=40, max_events=200)
    design.add_arm(SensoriumStudyArm(
        arm_id="fixture_arm", condition=SensoriumStudyCondition.FIXTURE_REPLAY,
        profile_type=P.RF_ECHO_VIBRATION_MAGNETIC))
    design.add_arm(SensoriumStudyArm(
        arm_id="live_arm", condition=SensoriumStudyCondition.LIVE_READ_ONLY,
        profile_type=P.RF_ECHO_VIBRATION_MAGNETIC))
    # No governance attached -> the live arm is blocked, not failed.
    runner = SensoriumDifferentiationRunner(state_dir=args.state_dir,
                                            design=design, governance=None)
    runner.prepare_study(design)
    runner.run_all()

    print("=== Live vs fixture sensorium demo ===")
    for arm_id, r in runner.arm_results.items():
        status = "blocked" if r.blocked else "fixture/ran"
        print(f"{arm_id:>16}: {status} ({'; '.join(r.reasons) or 'ok'})")
    live = runner.arm_results["live_arm"]
    print(f"live arm blocked      : {live.blocked}")
    print("live-vs-fixture       : inconclusive (live arm requires governance)")
    print("note                  : missing live data is inconclusive, not a "
          "failure; live mode requires governance approval.")


if __name__ == "__main__":
    main()
