#!/usr/bin/env python3
"""Pilot-2 grounding analysis demo: provenance-backed grounding quality.

    python examples/run_pilot2_grounding_analysis_demo.py --state-dir .solaris_ai_nn_pilot2/test_grounding

Grades grounding evidence for several candidate structures: a provenance-backed,
persistent, cross-module sensory proto-symbol (moderate/strong), a
provenance-backed world node (weak/moderate), and an unsupported claim with no
provenance. Grounding is operational association, not understanding.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot2 import GroundingAnalysis


def main():
    parser = argparse.ArgumentParser(description="Pilot-2 grounding demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot2/test_grounding")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    ga = GroundingAnalysis()
    strong = ga.add("proto_symbol", provenance_complete=True,
                    repeated_pattern=True, persistent=True,
                    improves_prediction_or_compression=True,
                    cross_module_support=True, evidence_refs=["prov1", "prov2"])
    weak = ga.add("world_model_node", provenance_complete=True,
                  repeated_pattern=True, evidence_refs=["prov3"])
    unsupported = ga.add("hypothesis", provenance_complete=False,
                         evidence_refs=[])

    path = os.path.join(args.state_dir, "grounding_analysis.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ga.snapshot(), fh, indent=2, default=str)

    print("=== Pilot-2 grounding analysis demo ===")
    print(f"sensory proto-symbol : {strong.quality}")
    print(f"world-model node     : {weak.quality}")
    print(f"unsupported claim    : {unsupported.quality}")
    print(f"best quality         : {ga.best_quality}")
    print(f"distribution         : {ga.quality_distribution()}")
    print(f"written              : {path}")
    print("note                 : grounding is operational association, not "
          "understanding")


if __name__ == "__main__":
    main()
