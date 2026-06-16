#!/usr/bin/env python3
"""Structural similarity demo: high, low, and fixture-overfit-warning cases.

    python examples/run_structural_similarity_demo.py --state-dir .solaris_ai_nn_replication/test_similarity

Shows a high-similarity case (two comparable runs), a low-similarity case
(different sensorium), and a high-similarity-on-fixtures case that triggers a
fixture-overfit caveat. Similarity is structural, never subjective, and never
implies consciousness.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_replication import StructuralSimilarity


def _run(run_id, fixture, concepts, growth, contamination, boundary):
    return {"run_id": run_id, "fixture_live_replay": fixture,
            "developmental_profile": {"composite_growth": growth,
                                      "durable_prediction_improvement_score":
                                          growth,
                                      "structural_growth_status":
                                          "real_structural_growth"},
            "world_signature": {"concept_family_distribution": concepts,
                                "human_label_contamination_score": contamination,
                                "boundary_clarity_score": boundary},
            "source_diet": {"rf": 10, "vib": 8}}


def main():
    parser = argparse.ArgumentParser(description="Structural similarity demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_replication/test_similarity")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    sim = StructuralSimilarity()
    a = _run("a", "live", {"rf": 3, "vib": 2}, 0.6, 0.1, 0.7)
    b = _run("b", "live", {"rf": 3, "vib": 2}, 0.58, 0.12, 0.68)
    high = sim.compare(a, b)

    c = _run("c", "live", {"txt": 5}, 0.2, 0.8, 0.3)
    low = sim.compare(a, c)

    fa = _run("fa", "fixture", {"rf": 3, "vib": 2}, 0.6, 0.1, 0.7)
    fb = _run("fb", "fixture", {"rf": 3, "vib": 2}, 0.6, 0.1, 0.7)
    overfit = sim.compare(fa, fb)

    print("=== Structural similarity demo ===")
    print(f"high similarity case  : overall {high.overall:.2f} "
          f"({high.measured_dimensions} dims)")
    print(f"low similarity case   : overall {low.overall:.2f} -- caveats: "
          f"{low.caveats or 'none'}")
    print(f"fixture-overfit case  : overall {overfit.overall:.2f} -- caveats: "
          f"{overfit.caveats or 'none'}")
    print("note                  : similarity is structural, not subjective; "
          "high similarity on fixtures may be robust development OR fixture "
          "overfit; low similarity does not by itself mean failure; not "
          "consciousness or life.")


if __name__ == "__main__":
    main()
