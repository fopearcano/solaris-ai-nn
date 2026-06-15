#!/usr/bin/env python3
"""Human label contamination demo: feature-only vs human-labelled stream.

    python examples/run_human_label_contamination_demo.py --state-dir .solaris_ai_nn_sensorium_lab/test_label_contamination

Runs a feature-only arm and a human-labelled arm and shows that the analyzer
detects contamination in the labelled arm (reported, never hidden) while the
feature-only arm rests on features. Human labels are annotations, never ground
truth.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.sensorium_lab import (
    HumanLabelContaminationAnalyzer,
    SensoriumDifferentiationRunner,
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
)
from solaris_ai_nn.sensorium_lab.sensorium_profiles import SensoriumProfileType as P


def main():
    parser = argparse.ArgumentParser(description="Human label contamination demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_sensorium_lab/test_label_contamination")
    args = parser.parse_args()

    design = SensoriumStudyDesign(ticks=50, max_events=300)
    design.add_arm(SensoriumStudyArm(
        arm_id="feature_only", condition=SensoriumStudyCondition.FEATURE_ONLY,
        profile_type=P.FEATURE_ONLY_NO_LABELS))
    design.add_arm(SensoriumStudyArm(
        arm_id="human_labelled",
        condition=SensoriumStudyCondition.HUMAN_LABELLED,
        profile_type=P.HUMAN_LABEL_CONTAMINATED))
    runner = SensoriumDifferentiationRunner(state_dir=args.state_dir,
                                            design=design)
    runner.prepare_study(design)
    runner.run_all()

    print("=== Human label contamination demo ===")
    for arm_id, r in runner.arm_results.items():
        c = r.contamination
        print(f"{arm_id:>16}: score={c.contamination_score} "
              f"contaminated={c.contaminated} sources={c.sources}")
    # Labels can never be ground truth (treating them as truth is blocked).
    analyzer = HumanLabelContaminationAnalyzer()
    print(f"label as ground truth blocked: "
          f"{not analyzer.validate_not_ground_truth(True)}")
    print("note                  : human labels are annotations, never ground "
          "truth; contamination is reported, not hidden.")


if __name__ == "__main__":
    main()
