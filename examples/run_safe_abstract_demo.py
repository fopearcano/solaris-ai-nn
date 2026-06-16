#!/usr/bin/env python3
"""Safe abstract demo: technical preprint, README-safe, negative-result.

    python examples/run_safe_abstract_demo.py --state-dir .solaris_ai_nn_claims/test_safe_abstract

Builds claim-constrained abstracts from a weak-evidence claim set: a technical
preprint abstract, a README-safe summary, and a negative-result summary. Abstracts
state when evidence is weak, include no forbidden claim except as a disclaimer,
and fall back to a negative/inconclusive abstract when no publishable claim exists.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.scientific_claims import (
    AbstractVariant,
    ScientificAbstractBuilder,
)


def main():
    parser = argparse.ArgumentParser(description="Safe abstract demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_claims/test_safe_abstract")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    builder = ScientificAbstractBuilder()
    weak = [{"text": "Action-reaction consequence learning is weakly observed."}]
    supported = [{"text": "Sensorium-native signs form under bounded fixtures."}]
    negatives = [{"text": "Cross-modal binding did not emerge in any arm."}]
    limitations = [{"text": "No replication yet."},
                   {"text": "Fixture dependence; no live-field confirmation."}]

    preprint = builder.build(
        AbstractVariant.TECHNICAL_PREPRINT, supported_claims=supported,
        weak_claims=weak, limitations=limitations)
    readme = builder.build(
        AbstractVariant.README_SAFE_SUMMARY, supported_claims=supported,
        weak_claims=weak, limitations=limitations)
    negative = builder.build(
        AbstractVariant.NEGATIVE_RESULT_SUMMARY, negative_results=negatives,
        limitations=limitations)

    print("=== Safe abstract demo ===\n")
    for label, text in (("Technical preprint", preprint),
                        ("README-safe summary", readme),
                        ("Negative-result summary", negative)):
        safety = builder.check_safety(text)
        print(f"## {label}  (claim-safe={safety.safe})")
        print(text)
        print()
    print("note: abstracts are claim-constrained. They state when evidence is "
          "weak, include no forbidden claim except as a disclaimer, and fall "
          "back to a negative/inconclusive abstract when no publishable claim "
          "exists.")


if __name__ == "__main__":
    main()
