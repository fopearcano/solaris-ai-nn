#!/usr/bin/env python3
"""World signature demo: build two signatures and compare them structurally.

    python examples/run_world_signature_demo.py --state-dir .solaris_ai_nn_sensorium_lab/test_world_signature

Runs a human-like-only arm and a non-human-only arm, builds a world signature for
each (an observable structural fingerprint, not subjective experience), and
compares them. This does not describe what Solaris feels.
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
    WorldSignatureComparison,
)
from solaris_ai_nn.sensorium_lab.sensorium_profiles import SensoriumProfileType as P


def main():
    parser = argparse.ArgumentParser(description="World signature demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_sensorium_lab/test_world_signature")
    args = parser.parse_args()

    design = SensoriumStudyDesign(ticks=50, max_events=300)
    design.add_arm(SensoriumStudyArm(
        arm_id="human_like", condition=SensoriumStudyCondition.HUMAN_LIKE_ONLY,
        profile_type=P.HUMAN_LIKE_TEXT_LIGHT_TEMPERATURE))
    design.add_arm(SensoriumStudyArm(
        arm_id="non_human", condition=SensoriumStudyCondition.NON_HUMAN_ONLY,
        profile_type=P.RF_ECHO_VIBRATION_MAGNETIC))
    runner = SensoriumDifferentiationRunner(state_dir=args.state_dir,
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()

    sig_h = runner.arm_results["human_like"].signature
    sig_n = runner.arm_results["non_human"].signature
    diff = WorldSignatureComparison().compare(sig_h, sig_n)

    print("=== World signature demo ===")
    print(f"human-like dominant families : {sig_h.dominant_receptor_families}")
    print(f"non-human dominant families  : {sig_n.dominant_receptor_families}")
    print(f"human-like proto families    : "
          f"{list(sig_h.proto_symbol_family_distribution)}")
    print(f"non-human proto families     : "
          f"{list(sig_n.proto_symbol_family_distribution)}")
    print(f"proto-family jaccard         : {diff['proto_family_jaccard']}")
    print(f"changed-perception delta     : {diff['changed_perception_delta']}")
    print(f"grounding delta              : {diff['grounding_delta']}")
    print("note                  : a world signature is an observable structural "
          "fingerprint, not subjective experience or qualia.")


if __name__ == "__main__":
    main()
