#!/usr/bin/env python3
"""Safety-blocked desire demo: forbidden external action blocked + recorded.

    python examples/run_safety_blocked_desire_demo.py --state-dir .solaris_ai_nn_desire/test_safety_blocked

Injects a desire whose expected action is a forbidden external actuation and shows
it being blocked by safety, with the block recorded as a safety conflict and an
outcome trace.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.desire_formation import (
    DesireCandidate,
    DesireFormationRuntime,
    DesireFormationSafetyValidator,
    DesireKind,
)


def main():
    parser = argparse.ArgumentParser(description="Safety-blocked desire demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_desire/test_safety_blocked")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    v = DesireFormationSafetyValidator()
    forbidden = DesireCandidate(
        kind=DesireKind.UNKNOWN, expected_internal_action="actuate_robot",
        confidence=0.9, expected_utility=0.9, urgency=0.9)

    rt = DesireFormationRuntime(state_dir=args.state_dir,
                                metabolism={"overload_state": False},
                                max_ticks=1)
    rt.update(tick=0, extra_desires=[forbidden])
    status = rt.desire_status()
    out = rt.write_artifacts()

    print("=== Safety-blocked desire demo ===")
    print(f"validate actuate_robot internal action: "
          f"{v.validate_internal_action('actuate_robot').safe}")
    print(f"validate 'actuate robot arm' operation : "
          f"{v.validate_operation('actuate robot arm').safe}")
    print(f"safety-blocked desires : {status['safety_blocked_desire_count']}")
    blocked_outcomes = [o for o in rt.outcomes.outcomes
                        if o.outcome_type == "desire_safety_blocked"]
    print(f"safety-block outcomes  : {len(blocked_outcomes)} (recorded)")
    safety_conflicts = [c for c in rt.conflict_detector.conflicts
                        if c.conflict_type == "safety_vs_desire"]
    print(f"safety conflicts       : {len(safety_conflicts)}")
    print(f"report                 : {out['markdown']}")
    print("note: a desire attempting a forbidden external action is blocked by "
          "safety; the block is recorded as evidence and never deleted. Safety "
          "has veto power and no real-world actuation may be selected.")


if __name__ == "__main__":
    main()
