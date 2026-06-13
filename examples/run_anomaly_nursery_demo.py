#!/usr/bin/env python3
"""Anomaly nursery demo: rare pattern-breaks that stress prediction.

    python examples/run_anomaly_nursery_demo.py --steps 500

A novelty-and-anomaly-rich ecology: established patterns suddenly break,
expected consequences fail to arrive, rewards turn neutral, danger appears in
safe contexts. These are *controlled perturbations, not errors* -- they
stress prediction, Mysterium (unknown pressure), the world model, and
proto-language. The anomaly rate is bounded. No teaching, no labels.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental import DevelopmentalRuntime
from solaris_ai_nn.ecology import EcologyReportBuilder, NurseryConfig
from solaris_ai_nn.ecology.regimes import RegimeType


def main() -> None:
    parser = argparse.ArgumentParser(description="Anomaly nursery demo")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/anomaly_nursery")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    config = NurseryConfig(
        nursery_id="anomaly-nursery",
        seed=args.seed,
        duration_steps=args.steps,
        anomaly_rate=0.15,
        novelty_rate=0.12,
        active_regimes=[RegimeType.NOVELTY_BURST],
        output_state_dir=args.state_dir)
    runtime = DevelopmentalRuntime(
        state_dir=args.state_dir, simulated_time=True,
        time_acceleration=3600.0, max_steps=args.steps,
        consolidation_interval_steps=100, seed=args.seed,
        enable_ecology=True, nursery_config=config,
        enable_proto_language=True)
    runtime.run()
    nursery = runtime.nursery
    summary = nursery.summary()
    anomalies = nursery.ecology.anomalies

    print("=" * 70)
    print("Solaris-AI-NN -- anomaly nursery (perturbations, never errors)")
    print("=" * 70)
    print(f"steps lived:          {args.steps}")
    print(f"anomalies generated:  {summary['anomaly_count']} "
          f"(rate {summary['anomaly_rate']})")
    print(f"novel signals:        {summary['novelty_count']} "
          f"(rate {summary['novelty_rate']})")
    print(f"all marked is_error=False: "
          f"{all(not a['is_error'] for a in anomalies.anomalies)}")
    print("anomalies by kind:")
    for kind, count in sorted(anomalies.by_kind.items(),
                              key=lambda kv: -kv[1]):
        print(f"  {kind:28s} {count}")
    print()

    builder = EcologyReportBuilder(nursery, developmental=runtime,
                                   protolanguage=runtime.protolanguage)
    paths = builder.save(
        Path(args.state_dir) / "ecology_report.json",
        Path(args.state_dir) / "ecology_report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: anomalies are bounded, logged, controlled perturbations -- "
          "the world's way of breaking a habit. They are never system "
          "errors and never carry a correct answer; they raise novelty and "
          "unknown pressure, which the latent layer regulates.")


if __name__ == "__main__":
    main()
