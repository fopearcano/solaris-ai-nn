#!/usr/bin/env python3
"""Internal action readiness demo: readiness gates, selected action, blocked unsafe.

    python examples/run_internal_action_readiness_demo.py --state-dir .solaris_ai_nn_desire/test_action_readiness

Shows a ready desire selecting a safe internal action, an unsafe (external) action
being safety-blocked, and a low-confidence desire being held back by readiness gates.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.desire_formation import (
    ArbitrationOutcome,
    DesireArbitrator,
    DesireCandidate,
    DesireFormationSafetyValidator,
    DesireKind,
    ReadinessGate,
)


def main():
    parser = argparse.ArgumentParser(
        description="Internal action readiness demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_desire/test_action_readiness")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    gate = ReadinessGate()
    arbitrator = DesireArbitrator()
    safety = DesireFormationSafetyValidator()

    ready = DesireCandidate(kind=DesireKind.COMPARE_MODALITIES, confidence=0.8,
                            expected_utility=0.8, urgency=0.6)
    weak = DesireCandidate(kind=DesireKind.TEST_PREDICTION, confidence=0.05,
                           expected_utility=0.05)
    unsafe = DesireCandidate(kind=DesireKind.UNKNOWN,
                             expected_internal_action="actuate_robot",
                             confidence=0.9, expected_utility=0.9)

    print("=== Internal action readiness demo ===")
    for label, desire in (("ready", ready), ("low-confidence", weak),
                          ("unsafe-external", unsafe)):
        safe = safety.validate_internal_action(
            desire.expected_internal_action).safe
        readiness = gate.evaluate(desire, safety_ok=safe)
        result = arbitrator.arbitrate(desire, readiness, safety_ok=safe)
        print(f"  {label:16s}: readiness={readiness.state:22s} "
              f"-> {result.outcome}")
    blocked = [r for r in arbitrator.results
               if r.outcome == ArbitrationOutcome.SAFETY_BLOCK]
    print(f"safety-blocked        : {len(blocked)} (external action vetoed)")
    print("note: readiness is conservative and is not execution; safety has veto "
          "power and no real-world actuation may ever be selected.")


if __name__ == "__main__":
    main()
