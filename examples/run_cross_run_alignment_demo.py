#!/usr/bin/env python3
"""Cross-run alignment demo: align epoch/concept/sign/prediction profiles.

    python examples/run_cross_run_alignment_demo.py --state-dir .solaris_ai_nn_replication/test_alignment

Aligns two runs across epoch/growth/concept/sign/prediction structures, and
shows a partial/inconclusive alignment when one run is missing data. Alignment
preserves run-specific differences and never forces sensoriums into human labels.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_replication import CrossRunAlignment


def _run(run_id, **profile):
    return {"run_id": run_id, **profile}


def main():
    parser = argparse.ArgumentParser(description="Cross-run alignment demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_replication/test_alignment")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    full = {"developmental_profile": {"developmental_epoch_count": 5,
                                      "composite_growth": 0.6,
                                      "maturation_marker_count": 3,
                                      "durable_prediction_improvement_score": 0.7},
            "world_signature": {"concept_family_distribution": {"rf": 3, "vib": 2},
                                "sign_family_distribution": {"s1": 2}},
            "source_diet": {"rf": 10, "vib": 8}}
    run_a = _run("run_a", **full)
    run_b = _run("run_b", **full)
    # run_c is missing the sign/prediction structure -> partial/inconclusive.
    run_c = _run("run_c", developmental_profile={"developmental_epoch_count": 5,
                                                 "composite_growth": 0.6},
                 world_signature={"concept_family_distribution": {"rf": 3}},
                 source_diet={"rf": 10, "vib": 8})

    aligner = CrossRunAlignment()
    same = aligner.align(run_a, run_b)
    partial = aligner.align(run_a, run_c)

    print("=== Cross-run alignment demo ===")
    print(f"run_a ~ run_b: aligned {same['aligned_count']}, partial "
          f"{same['partial_count']}, divergent {same['divergent_count']}, "
          f"inconclusive {same['inconclusive_count']}")
    print(f"run_a ~ run_c: aligned {partial['aligned_count']}, partial "
          f"{partial['partial_count']}, divergent {partial['divergent_count']}, "
          f"inconclusive {partial['inconclusive_count']} (missing data)")
    print("note         : alignment preserves run-specific differences; missing "
          "data is partial/inconclusive, never forced; this is not consciousness "
          "or life.")


if __name__ == "__main__":
    main()
