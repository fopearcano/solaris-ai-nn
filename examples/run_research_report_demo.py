#!/usr/bin/env python3
"""Research report demo: result store, module effects, report (no mind claims).

    python examples/run_research_report_demo.py --state-dir .solaris_ai_nn_research/test_report

Runs the ablation matrix into an append-only result store, analyses each module's
provisional effect, builds a leaderboard, and compiles a ClaimGuard-scanned
research report. Benchmark scores are operational proxies, never consciousness
scores; negative and inconclusive results are preserved.
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
    COGNITIVE_TOGGLES,
    EffectAnalyzer,
    ExperimentDesign,
    ResearchBenchmarkRunner,
    ResearchLeaderboard,
    ResearchReportBuilder,
    ResearchResultStore,
)


def main():
    parser = argparse.ArgumentParser(description="Research report demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_research/test_report")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    design = ExperimentDesign(title="report", research_question="which modules "
                              "matter?", base_dir=args.state_dir, max_steps=20)
    store = ResearchResultStore(base_dir=args.state_dir)
    runner = ResearchBenchmarkRunner(store=store)
    matrix = AblationMatrix()
    results = runner.run_ablation_matrix(matrix, design)
    full = results["full_system"].metrics

    # Per-module effect: full vs the ablation that removes the module.
    ablation_by_module = {}
    for toggle in COGNITIVE_TOGGLES:
        case = f"full_minus_{toggle.replace('enable_', '')}"
        if case in results:
            ablation_by_module[toggle] = results[case].metrics
    analysis = EffectAnalyzer().analyze(full, ablation_by_module)

    lb = ResearchLeaderboard()
    lb.add("full", "variant", full, evidence_count=3)
    lb.add("minimal_spine_only", "ablation",
           results["minimal_spine_only"].metrics, evidence_count=1)

    report = ResearchReportBuilder(base_dir=args.state_dir).build_and_write(
        designs=[design], variants=["full"], baselines=["random_action_baseline"],
        ablations=list(results), effect_analysis=analysis, leaderboard=lb)

    print("=== Research report demo ===")
    print(f"result store records      : {store.snapshot()['result_count']}")
    print(f"positive modules          : {analysis.positive_modules()}")
    print(f"harmful candidates        : {analysis.harmful_candidates()}")
    print(f"inconclusive candidates   : {analysis.inconclusive_candidates()}")
    print(f"leaderboard best overall  : {lb.best()}")
    print(f"claim-guard safe          : {report.claim_guard_safe}")
    print(f"report                    : "
          f"{os.path.join(args.state_dir, 'RESEARCH_REPORT.md')}")
    print("note                      : benchmark scores are operational "
          "proxies; they do not measure or prove consciousness.")


if __name__ == "__main__":
    main()
