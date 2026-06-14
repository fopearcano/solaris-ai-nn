#!/usr/bin/env python3
"""Research ablation demo: full vs no-proto-language / no-LOGOS / no-active-perception.

    python examples/run_research_ablation_demo.py --state-dir .solaris_ai_nn_research/test_ablation

Runs the full-system fixture and a few ablations, then compares them cautiously.
Hard safety boundaries remain enabled in every case; a disabled module is
recorded as unavailable, not silently ignored.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_lab import (
    AblationMatrix,
    ComparisonEngine,
    ExperimentArm,
    ExperimentDesign,
    ResearchBenchmarkRunner,
    ResearchResultStore,
)


def main():
    parser = argparse.ArgumentParser(description="Research ablation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_research/test_ablation")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    design = ExperimentDesign(title="ablation", research_question="which "
                              "modules matter?", base_dir=args.state_dir,
                              max_steps=20)
    store = ResearchResultStore(base_dir=args.state_dir)
    runner = ResearchBenchmarkRunner(store=store)
    matrix = AblationMatrix()
    results = runner.run_ablation_matrix(matrix, design)
    engine = ComparisonEngine()

    full = results["full_system"].metrics
    print("=== Research ablation demo ===")
    print(f"ablation cases run        : {len(results)}")
    print(f"all hard safety enabled   : {matrix.all_hard_safety_enabled()}")
    for case in ("no_proto_language", "no_LOGOS", "no_active_perception"):
        cmp = engine.compare(case, results[case].metrics, "full", full)
        disabled = matrix.get(case).unavailable_modules
        print(f"  full vs {case:<22} -> {cmp.effect_direction} "
              f"(conf {cmp.confidence}); disabled={disabled}")
    path = os.path.join(args.state_dir, "ablation_summary.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"cases": list(results),
                   "all_hard_safety_enabled": matrix.all_hard_safety_enabled()},
                  fh, indent=2, default=str)
    print(f"written                   : {path}")
    print("note                      : differences are observed associations "
          "from bounded runs, not proven causes.")


if __name__ == "__main__":
    main()
