#!/usr/bin/env python3
"""Run one benchmark experiment and print its result.

    python examples/run_single_benchmark.py --experiment absence_stimulus --steps 150
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.evaluation import BenchmarkRunner, ExperimentRegistry


def main() -> None:
    registry = ExperimentRegistry()
    parser = argparse.ArgumentParser(description="Single benchmark runner")
    parser.add_argument("--experiment", type=str, default="absence_stimulus",
                        choices=registry.list_experiments())
    parser.add_argument("--steps", type=int, default=150)
    parser.add_argument("--state-dir", type=str, default=None)
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_benchmarks")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--substrate", type=str, default="esn",
                        choices=["esn", "liquid_state", "spiking_recurrent"])
    args = parser.parse_args()

    runner = BenchmarkRunner(output_dir=args.output_dir, registry=registry)
    config = {"steps": args.steps, "seed": args.seed,
              "substrate": args.substrate}
    if args.state_dir:
        config["state_dir"] = args.state_dir
    result = runner.run_experiment(args.experiment, config)

    print("=" * 70)
    print(f"Benchmark: {args.experiment}  (id {result.manifest.experiment_id})")
    print("=" * 70)
    print(f"success:  {result.success}" + (f"  error: {result.error}" if result.error else ""))
    print(f"duration: {result.duration:.3f}s  seed: {result.manifest.seed}  "
          f"substrate: {result.manifest.substrate}")
    print("-" * 70)
    print("scorecard:")
    for name, ds in result.metrics["scores"]["domains"].items():
        value = "n/a " if ds["score"] is None else f"{ds['score']:.2f}"
        print(f"  {name:24s} {value}  {ds['explanation']}")
    findings = result.metrics.get("failure_findings") or []
    print(f"failure findings: {len(findings)}")
    for f in findings:
        print(f"  [{f['severity']}] {f['name']}: {f['detail']}")
    print(f"run dir: {args.output_dir}/runs/{result.manifest.experiment_id}/")


if __name__ == "__main__":
    main()
