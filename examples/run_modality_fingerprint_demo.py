#!/usr/bin/env python3
"""Modality fingerprint demo: which modality actually shaped the system?

    python examples/run_modality_fingerprint_demo.py --state-dir .solaris_ai_nn_sensorium_lab/test_modality_fingerprint

Runs a mixed-modality arm and prints each modality's fingerprint -- events,
invariants, proto-symbols, structural effect -- so a modality with many events but
no structural effect is reported honestly as structurally weak.
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
    parser = argparse.ArgumentParser(description="Modality fingerprint demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_sensorium_lab/test_modality_fingerprint")
    args = parser.parse_args()

    design = SensoriumStudyDesign(ticks=60, max_events=400)
    design.add_arm(SensoriumStudyArm(
        arm_id="mixed", condition=SensoriumStudyCondition.MIXED_PLURAL_SENSORIUM,
        profile_type=P.MIXED_HUMAN_NONHUMAN))
    runner = SensoriumDifferentiationRunner(state_dir=args.state_dir,
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()
    fingerprints = runner.arm_results["mixed"].fingerprints

    print("=== Modality fingerprint demo ===")
    print(f"{'modality':>18} | events | invariants | protos | effect | weak")
    for fp in fingerprints:
        print(f"{fp.modality:>18} | {fp.event_count:>6} | "
              f"{fp.invariants:>10} | {fp.proto_symbols:>6} | "
              f"{fp.structural_effect:>6} | {fp.structurally_weak}")
    weak = [fp.modality for fp in fingerprints if fp.structurally_weak]
    print(f"structurally weak modalities: {weak or 'none'}")
    print("note                  : a modality with many events but no "
          "structural effect is reported, not assumed important.")


if __name__ == "__main__":
    main()
