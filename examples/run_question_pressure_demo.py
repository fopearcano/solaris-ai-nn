#!/usr/bin/env python3
"""Question pressure demo: missing expected sign -> pressure -> attention rec.

    python examples/run_question_pressure_demo.py --state-dir .solaris_ai_nn_cognition/test_question_pressure

Anticipates a sign that is then not observed, generating an operational question
pressure and an attention recommendation. Question pressure is pressure to inspect/
compare/wait/simulate -- NOT human verbal questioning.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.semiogenesis import InternalSign, SignKind
from solaris_ai_nn.sensorium_cognition import QuestionPressureEngine


def main():
    parser = argparse.ArgumentParser(description="Question pressure demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_cognition/test_question_pressure")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    expected = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="rf:09",
                            modality_distribution={"radio_frequency": 3})
    ambiguous = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="vib:09",
                             modality_distribution={"vibration": 2})
    ambiguous.ambiguity_score = 0.7  # makes it ambiguous

    engine = QuestionPressureEngine()
    pressures = engine.generate(
        signs=[expected, ambiguous], failed_predictions=[], logos_tensions=[],
        anticipation_targets=[expected.sign_id],  # expected ...
        observed_targets=[])                       # ... but not observed

    print("=== Question pressure demo ===")
    print(f"question pressures    : {len(pressures)}")
    for q in pressures:
        print(f"  {q.pressure_type:24s} -> {q.recommended_response} "
              f"(intensity {q.intensity})")
    print(f"pressure score        : {engine.pressure_score()}")
    missing = [q for q in pressures
               if q.pressure_type == "missing_expected_sign"]
    print(f"missing-expected-sign : {len(missing)} (attention -> inspect/wait)")
    print("note: question pressure is operational pressure to inspect, compare, "
          "wait, simulate, or preserve an unknown -- not a human verbal "
          "question.")


if __name__ == "__main__":
    main()
