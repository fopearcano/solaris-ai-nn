#!/usr/bin/env python3
"""Replication registry demo: register runs, index artifacts, registry report.

    python examples/run_replication_registry_demo.py --state-dir .solaris_ai_nn_replication/test_registry

Registers two synthetic developmental runs, indexes their artifacts, and prints
the registry summary. The registry reads metadata only; it never starts runs and
never modifies source artifacts. Replication compares observable structures, not
life or consciousness.
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
    parser = argparse.ArgumentParser(description="Replication registry demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_replication/test_registry")
    args = parser.parse_args()

    rt = DevelopmentalReplicationRuntime(state_dir=args.state_dir, max_runs=8)
    rt.register_run(
        "run_alpha", lineage_id="L1", seed=7, sensorium_profile="non_human",
        fixture_live_replay="fixture",
        developmental_profile={"structural_growth_status":
                               "real_structural_growth", "composite_growth": 0.6},
        source_diet={"rf": 10, "vib": 8})
    rt.register_run(
        "run_beta", lineage_id="L1", seed=9, sensorium_profile="non_human",
        fixture_live_replay="fixture",
        developmental_profile={"structural_growth_status":
                               "real_structural_growth", "composite_growth": 0.58},
        source_diet={"rf": 10, "vib": 8})
    status = rt.registry.status()

    print("=== Replication registry demo ===")
    print(f"registered runs       : {status['registered_run_count']} "
          f"-> {status['runs']}")
    print(f"lineages              : {status['lineages']}")
    print(f"runs with uncertainty : {status['runs_with_uncertainty']}")
    print(f"registry path         : {status['registry_path']}")
    print(f"artifact index path   : {status['artifact_index_path']}")
    print("note                  : the registry reads metadata only; it never "
          "starts runs or modifies artifacts. Replication compares observable "
          "structures, not life or consciousness.")


if __name__ == "__main__":
    main()
