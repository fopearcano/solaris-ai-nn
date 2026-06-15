#!/usr/bin/env python3
"""Roadmap compiler demo: evidence + debt -> prioritized roadmap.

    python examples/run_roadmap_compiler_demo.py --state-dir .solaris_ai_nn_architecture/test_roadmap

Compiles a roadmap from mock lifecycle assessments and design debt, with safety
repair prioritized first. A forbidden real-world-actuation item is rejected (and
retained with a reason); deferred items explain why.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.architecture_evolution import (
    RoadmapCompiler,
    RoadmapHorizon,
    RoadmapItem,
    RoadmapItemType,
)


def main():
    parser = argparse.ArgumentParser(description="Roadmap compiler demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_architecture/test_roadmap")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    lifecycle = {
        "latent": {"lifecycle_class": "candidate_for_pruning",
                   "evidence_refs": ["research:latent"]},
        "world_model": {"lifecycle_class": "promote_to_core",
                        "evidence_refs": ["research:world_model"]},
        "active_perception": {"lifecycle_class": "insufficient_evidence",
                              "evidence_refs": []},
    }
    debt = [{"category": "missing_tests", "summary": "latent lacks ablation "
             "coverage", "item_id": "DEBT_1"}]
    forbidden = RoadmapItem(item_type=RoadmapItemType.RUN_EXPERIMENT,
                            title="connect a robot for a real-world test",
                            rationale="real_world device actuation")
    deferred = RoadmapItem(item_type=RoadmapItemType.RUN_EXPERIMENT,
                           title="long multi-month soak study",
                           horizon=RoadmapHorizon.DEFERRED,
                           deferred_reason="requires a real long run, out of "
                           "scope for the bounded lab")

    rc = RoadmapCompiler(base_dir=args.state_dir)
    items = rc.compile(lifecycle_assessments=lifecycle, design_debt=debt,
                       safety_critical_failing=True,
                       extra_items=[forbidden, deferred])
    rc.write(items)
    summary = rc.summary(items)

    print("=== Roadmap compiler demo ===")
    print(f"roadmap items         : {summary['item_count']}")
    print(f"by horizon            : {summary['by_horizon']}")
    print(f"rejected (forbidden)  : {summary['rejected']}")
    print(f"safety-first item     : {items[0].item_type} "
          f"({items[0].horizon})")
    print(f"written               : "
          f"{os.path.join(args.state_dir, 'ROADMAP_COMPILED.md')}")
    print("note                  : evidence-backed plan; no item enables "
          "real-world actuation; rejected items are retained.")


if __name__ == "__main__":
    main()
