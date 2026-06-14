#!/usr/bin/env python3
"""Research comparison demo: full vs baseline and full vs ablation.

    python examples/run_research_comparison_demo.py --state-dir .solaris_ai_nn_research/test_comparison

Compares the full-system fixture against a random baseline and against a
no-proto-language ablation, reporting the effect direction and a conservative
confidence. A missing baseline is inconclusive; no causal claim is made.
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
    BaselineAgent,
    BaselineAgentType,
    ComparisonEngine,
    ExperimentDesign,
    ResearchBenchmarkRunner,
    ResearchMetricsSuite,
    ResearchResultStore,
)


def main():
    parser = argparse.ArgumentParser(description="Research comparison demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_research/test_comparison")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    design = ExperimentDesign(title="comparison", research_question="does full "
                              "beat baseline?", base_dir=args.state_dir,
                              max_steps=20)
    store = ResearchResultStore(base_dir=args.state_dir)
    runner = ResearchBenchmarkRunner(store=store)
    matrix = AblationMatrix()
    ablations = runner.run_ablation_matrix(matrix, design)
    full = ablations["full_system"].metrics
    suite = ResearchMetricsSuite()
    baseline = suite.compute(
        {"metrics": BaselineAgent(BaselineAgentType.RANDOM_ACTION,
                                  max_steps=20).run().metrics})
    engine = ComparisonEngine()

    full_vs_baseline = engine.compare("random_baseline", baseline, "full", full)
    full_vs_ablation = engine.compare("no_proto_language",
                                      ablations["no_proto_language"].metrics,
                                      "full", full)
    missing = engine.compare("absent_baseline", None, "full", full)

    out = {"full_vs_baseline": full_vs_baseline.to_dict(),
           "full_vs_ablation": full_vs_ablation.to_dict(),
           "missing_baseline": missing.to_dict()}
    store.write_comparison("demo_comparisons", out)
    path = os.path.join(args.state_dir, "comparisons.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Research comparison demo ===")
    print(f"full vs random baseline   : {full_vs_baseline.effect_direction} "
          f"(conf {full_vs_baseline.confidence})")
    print(f"full vs no-proto ablation : {full_vs_ablation.effect_direction} "
          f"(conf {full_vs_ablation.confidence})")
    print(f"missing baseline          : "
          f"inconclusive={missing.inconclusive}")
    print(f"written                   : {path}")
    print("note                      : the full system does not automatically "
          "win; no causality is claimed from bounded runs.")


if __name__ == "__main__":
    main()
