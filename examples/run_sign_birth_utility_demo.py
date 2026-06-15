#!/usr/bin/env python3
"""Sign birth/utility demo: stable concept -> useful sign; low-utility decays.

    python examples/run_sign_birth_utility_demo.py --state-dir .solaris_ai_nn_semiogenesis/test_sign_birth_utility

Shows a stable, useful proto-concept producing a stable sign, while a low-utility
sign is demoted from stable (it does not get deleted). Useful does not mean true or
understood.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.perceptual_ontogenesis import ProtoConcept, ProtoConceptKind, \
    ProtoConceptStatus
from solaris_ai_nn.semiogenesis import (
    SignBirthEngine,
    SignStatus,
    SignUtilityEvaluator,
)


def main():
    parser = argparse.ArgumentParser(description="Sign birth/utility demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_semiogenesis/test_sign_birth_utility")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    engine = SignBirthEngine()
    evaluator = SignUtilityEvaluator()

    strong = ProtoConcept(
        kind=ProtoConceptKind.MODALITY_NATIVE, status=ProtoConceptStatus.STABLE,
        modality_distribution={"radio_frequency": 5}, recurrence_count=5,
        stability_score=0.8, prediction_utility=0.7, compression_utility=0.7,
        attention_utility=0.6)
    noise = ProtoConcept(
        kind=ProtoConceptKind.UNKNOWN, status=ProtoConceptStatus.UNSTABLE,
        modality_distribution={"radio_frequency": 1}, recurrence_count=1,
        stability_score=0.0)

    strong_cands = engine.propose([strong])
    noise_cands = engine.propose([noise])

    print("=== Sign birth/utility demo ===")
    print(f"stable concept -> sign candidates : {len(strong_cands)}")
    if strong_cands:
        s = strong_cands[0].sign
        res = evaluator.evaluate(s)
        print(f"  sign_code   : {s.sign_code}")
        print(f"  trigger     : {strong_cands[0].trigger}")
        print(f"  status      : {s.status}")
        print(f"  utility     : overall={res.overall} useful={res.useful}")
    print(f"isolated noise -> sign candidates : {len(noise_cands)}")

    # A low-utility but stable sign is demoted (never deleted).
    if strong_cands:
        low = strong_cands[0].sign
        low.status = SignStatus.STABLE
        low.compression_utility = low.prediction_utility = 0.0
        low.attention_utility = low.relation_utility = 0.0
        low.recurrence_count = 1
        res2 = evaluator.evaluate(low)
        print(f"low-utility sign -> status        : {low.status} "
              f"(useful={res2.useful})")
    print("note: useful does not mean true or understood; low-utility signs are "
          "demoted to ambiguous, never deleted.")


if __name__ == "__main__":
    main()
