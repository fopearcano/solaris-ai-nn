#!/usr/bin/env python3
"""Soak control arms demo: full stack vs controls (conservative).

    python examples/run_soak_control_arms_demo.py --state-dir .solaris_ai_nn_soak/test_control_arms

Compares the full stack against a passive-parser-only arm, a no-metabolism arm,
and a fixture-only arm. Control arms exist to prevent self-flattering
conclusions; arms with insufficient data stay inconclusive. This does not prove
life or consciousness.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_soak import ControlArmId, DevelopmentalSoakRuntime


def main():
    parser = argparse.ArgumentParser(description="Soak control arms demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_soak/test_control_arms")
    args = parser.parse_args()

    rt = DevelopmentalSoakRuntime(
        state_dir=args.state_dir, stage="developmental_soak_30d",
        max_ticks=6, max_runtime_s=25.0, run_control_arms=True)
    rt.run_stage("developmental_soak_30d")
    rt.run_control_arms_now(arm_ids=[
        ControlArmId.FULL_STACK, ControlArmId.PASSIVE_PARSER_ONLY,
        ControlArmId.NO_PERCEPTUAL_METABOLISM, ControlArmId.FIXTURE_ONLY])
    rt.build_evidence_dossier()

    print("=== Soak control arms demo ===")
    for arm in rt.control_arm_results:
        print(f"  {arm.arm_id:24s} available={arm.available} ran={arm.ran} "
              f"growth={arm.growth_status} score={arm.structural_growth_score}")
    print(f"evidence claims          : "
          f"{rt.dossier.to_dict()['claim_count']}")
    print("note                     : control arms prevent self-flattering "
          "conclusions; insufficient-data arms stay inconclusive; this does "
          "not prove life or consciousness.")


if __name__ == "__main__":
    main()
