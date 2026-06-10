#!/usr/bin/env python3
"""Run a benchmark suite and print the table + scorecards.

    python examples/run_benchmark_suite.py --quick --steps 150
    python examples/run_benchmark_suite.py --experiments absence_stimulus,reward_danger
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.evaluation import BenchmarkRunner, ExperimentRegistry

QUICK_SUITE = ["absence_stimulus", "feedback_inversion", "restart_recovery",
               "language_trace"]


def main() -> None:
    registry = ExperimentRegistry()
    parser = argparse.ArgumentParser(description="Benchmark suite runner")
    parser.add_argument("--experiments", type=str, default=None,
                        help="comma-separated experiment names")
    parser.add_argument("--steps", type=int, default=150)
    parser.add_argument("--state-dir", type=str, default=None)
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_benchmarks")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--substrate", type=str, default="esn",
                        choices=["esn", "liquid_state", "spiking_recurrent"])
    parser.add_argument("--enable-plasticity", action="store_true")
    parser.add_argument("--embodied", action="store_true")
    parser.add_argument("--language", action="store_true")
    parser.add_argument("--quick", action="store_true",
                        help="run the quick safe suite (default when no "
                             "--experiments given)")
    args = parser.parse_args()

    if args.experiments:
        names = [n.strip() for n in args.experiments.split(",") if n.strip()]
    else:
        names = list(QUICK_SUITE)

    config = {"steps": args.steps, "seed": args.seed,
              "substrate": args.substrate,
              "enable_plasticity": args.enable_plasticity,
              "embodied": args.embodied, "language": args.language}
    runner = BenchmarkRunner(output_dir=args.output_dir, registry=registry)
    results = runner.run_suite(names, config)
    summary = runner.summarize(results)

    print("=" * 76)
    print(f"Solaris-AI-NN benchmark suite ({len(results)} experiments, "
          f"{args.steps} steps, seed {args.seed})")
    print("=" * 76)
    print(f"{'experiment':24s} {'ok':3s} {'dur(s)':>7s} {'findings':>9s}  scores")
    for row in summary["experiments"]:
        scores = " ".join(f"{k.split('_')[0]}={v:.2f}"
                          for k, v in sorted(row["scores"].items()))
        print(f"{row['name']:24s} {'yes' if row['success'] else 'NO ':3s} "
              f"{row['duration_s']:7.2f} {row['findings']:9d}  {scores[:60]}")
    if summary["warnings"]:
        print("-" * 76)
        print("warnings (first few):")
        for w in summary["warnings"][:5]:
            print(f"  - {w.splitlines()[0][:90]}")
    print("-" * 76)
    print(f"suite summary: {args.output_dir}/suite_summary.md")
    print(f"per-run files: {args.output_dir}/runs/<experiment_id>/")
    print("Scores are mechanistic proxies; no consciousness score exists.")


if __name__ == "__main__":
    main()
