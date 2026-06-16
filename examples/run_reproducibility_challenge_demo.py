#!/usr/bin/env python3
"""Reproducibility challenge demo: fixture demo, falsification replay, missing.

    python examples/run_reproducibility_challenge_demo.py --state-dir .solaris_ai_nn_review/test_repro_challenge

Builds reproducibility challenges from an evidence bundle that has a baseline and
falsification artifacts but no soak dossier. The fixture-demo and
falsification-replay challenges are available; the growth-vs-accumulation and
shuffled-order challenges (which need the soak dossier) are unavailable. Every
challenge is an instruction only -- nothing is executed.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.independent_review import ReproducibilityChallengeBuilder


def main():
    parser = argparse.ArgumentParser(description="Reproducibility challenge demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_review/test_repro_challenge")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    bundle = {
        "research_baseline": {"baseline_status": "validated"},
        "scientific_claims": {"claim_registry": {}},
        "falsification": {"falsified_claim_count": 0},
        "replication": {"replication_arm_count": 2},
        "safety": {"critical_regression_count": 0},
        # no "soak" -> shuffled-order / growth-vs-accumulation unavailable
    }
    challenge = ReproducibilityChallengeBuilder().build(bundle).to_dict()

    print("=== Reproducibility challenge demo ===")
    print(f"  challenges  : {challenge['reproducibility_challenge_count']} "
          f"(available {challenge['available_challenge_count']}, unavailable "
          f"{challenge['unavailable_challenge_count']})")
    for s in challenge["steps"]:
        print(f"    - [{s['status']}] {s['challenge_type']}")
        print(f"        command : {s['command']}")
        print(f"        expected: {s['expected']['expected_artifact']} "
              f"(executed={s['executed']})")
    print("note        : challenges are instructions only; nothing is executed. "
          "Missing prerequisite artifacts (e.g. the soak dossier) mark a "
          "challenge unavailable rather than fabricating a result.")


if __name__ == "__main__":
    main()
