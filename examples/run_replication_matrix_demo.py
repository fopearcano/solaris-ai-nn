#!/usr/bin/env python3
"""Replication matrix demo: replicated, diverged, falsified, inconclusive.

    python examples/run_replication_matrix_demo.py --state-dir .solaris_ai_nn_replication/test_matrix

Registers comparable and divergent runs, runs the bounded pipeline, and builds
the conservative replication matrix: replicated, diverged, falsified, and
inconclusive cells -- with no empty green dashboard and falsified claims made
prominent. Replication compares observable structures, not life or consciousness.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_replication import DevelopmentalReplicationRuntime


def main():
    parser = argparse.ArgumentParser(description="Replication matrix demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_replication/test_matrix")
    args = parser.parse_args()

    rt = DevelopmentalReplicationRuntime(state_dir=args.state_dir, max_runs=8)
    common = dict(sensorium_profile="non_human", fixture_live_replay="fixture",
                  developmental_profile={
                      "composite_growth": 0.6,
                      "structural_growth_status": "real_structural_growth",
                      "durable_prediction_improvement_score": 0.7,
                      "maturation_marker_count": 3,
                      "developmental_epoch_count": 5, "plateau_count": 1,
                      "regression_count": 0},
                  world_signature={
                      "concept_family_distribution": {"rf": 3, "vib": 2},
                      "sign_family_distribution": {"s1": 2},
                      "human_label_contamination_score": 0.1,
                      "boundary_clarity_score": 0.7},
                  source_diet={"rf": 10, "vib": 8})
    rt.register_run("run_a", lineage_id="L1", seed=7, **common)
    rt.register_run("run_b", lineage_id="L1", seed=9, **common)
    rt.register_run(
        "run_c", lineage_id="L2", seed=7, sensorium_profile="human_like",
        fixture_live_replay="fixture", human_label_exposure=0.8,
        developmental_profile={"composite_growth": 0.2,
                               "structural_growth_status": "fixture_overfit",
                               "durable_prediction_improvement_score": 0.1,
                               "plateau_count": 3, "regression_count": 2},
        world_signature={"concept_family_distribution": {"txt": 5},
                         "human_label_contamination_score": 0.8,
                         "boundary_clarity_score": 0.3},
        source_diet={"txt": 30})
    rt.relate("run_a", "run_b", "different_seed")
    rt.analyze()
    out = rt.write_artifacts()
    matrix = rt.matrix.to_dict()

    print("=== Replication matrix demo ===")
    print(f"cells                 : {matrix['cell_count']}")
    print(f"  replicated          : {matrix['replicated_claim_count']}")
    print(f"  partially replicated: {matrix['partially_replicated_claim_count']}")
    print(f"  diverged            : {matrix['diverged_claim_count']}")
    print(f"  falsified           : {matrix['falsified_claim_count']}")
    print(f"  inconclusive        : {matrix['inconclusive_claim_count']}")
    print(f"empty green dashboard : {matrix['empty_green_dashboard']}")
    print(f"matrix report         : {out['matrix']}")
    print("note                  : conservative grid; inconclusive is valid and "
          "falsified claims are prominent; replication compares observable "
          "structures only, not consciousness or life.")


if __name__ == "__main__":
    main()
