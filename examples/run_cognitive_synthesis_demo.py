#!/usr/bin/env python3
"""Cognitive synthesis demo: merge/split + preserved fragments + contradiction.

    python examples/run_cognitive_synthesis_demo.py --state-dir .solaris_ai_nn_cognition/test_cognitive_synthesis

Runs the synthesis engine over signs and inferred relations: a cross-modal-unity
inference seeds a merge, an ambiguous sign seeds a split, and a contradiction is
preserved as a LOGOS tension. Fragments are preserved and contradiction stays
visible.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.semiogenesis import InternalSign, SignKind
from solaris_ai_nn.sensorium_cognition import SynthesisEngine
from solaris_ai_nn.sensorium_cognition.sign_reasoning import (
    SignInferenceType,
    SignRelationInference,
)


def main():
    parser = argparse.ArgumentParser(description="Cognitive synthesis demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_cognition/test_cognitive_synthesis")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    rf = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="rf:01",
                      modality_distribution={"radio_frequency": 4})
    vib = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="vib:01",
                       modality_distribution={"vibration": 4})
    ambiguous = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="echo:01",
                             modality_distribution={"alien_echo": 2})
    ambiguous.ambiguity_score = 0.7

    inferences = [
        SignRelationInference(inference_type=SignInferenceType.CROSS_MODAL_UNITY,
                              sign_refs=[rf.sign_id, vib.sign_id],
                              confidence=0.6),
        SignRelationInference(inference_type=SignInferenceType.CONTRADICTION,
                              sign_refs=[rf.sign_id, vib.sign_id],
                              confidence=0.4),
    ]

    synthesis = SynthesisEngine().synthesize([rf, vib, ambiguous], inferences)

    print("=== Cognitive synthesis demo ===")
    print(f"synthesis events      : {len(synthesis.results)}")
    for r in synthesis.results:
        print(f"  {r.op:42s} fragments={r.fragment_refs} "
              f"preserved_contradiction={r.preserved_contradiction}")
    merges = [r for r in synthesis.results
              if r.op == "merge_into_cross_modal_structure"]
    splits = [r for r in synthesis.results if r.op == "split_ambiguous_sign"]
    contradictions = [r for r in synthesis.results if r.preserved_contradiction]
    print(f"merges                : {len(merges)}")
    print(f"splits                : {len(splits)} (fragments preserved)")
    print(f"preserved contradictions: {len(contradictions)} (kept visible)")
    print("note: synthesis is not proof of understanding; the synthesized "
          "fragments are preserved and irreducible contradiction stays visible "
          "as a LOGOS tension.")


if __name__ == "__main__":
    main()
