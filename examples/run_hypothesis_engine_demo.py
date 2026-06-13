#!/usr/bin/env python3
"""Hypothesis engine demo: a bounded internal scientific loop.

    python examples/run_hypothesis_engine_demo.py --steps 300

A bounded simulated developmental run in a controlled nursery, with the
hypothesis engine enabled. The system turns its own uncertainty (Mysterium,
prediction misses, weak world-model edges, ambiguous proto-symbols, delayed
consequences, anomalies, stagnation) into grounded *hypothesis candidates*,
designs bounded safe tests, collects source-scoped evidence, and updates or
preserves the unknown. No LLM generates hypotheses, no human feedback is
used, and no experiment reaches the real world.
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
from solaris_ai_nn.ecology import NurseryConfig
from solaris_ai_nn.hypothesis import HypothesisReportBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Hypothesis engine demo")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/hypothesis_engine")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    config = NurseryConfig(nursery_id="hypothesis-nursery", seed=args.seed,
                           duration_steps=args.steps,
                           output_state_dir=args.state_dir)
    runtime = DevelopmentalRuntime(
        state_dir=args.state_dir, simulated_time=True,
        time_acceleration=3600.0, max_steps=args.steps,
        consolidation_interval_steps=50, seed=args.seed,
        enable_ecology=True, nursery_config=config,
        enable_proto_language=True, enable_active_perception=True,
        enable_hypothesis_engine=True)
    runtime.run()
    engine = runtime.hypothesis_engine
    summary = engine.summary()

    print("=" * 70)
    print("Solaris-AI-NN -- hypothesis engine (an internal scientific loop)")
    print("=" * 70)
    print(f"steps lived:            {args.steps} (simulated time)")
    print(f"hypothesis candidates:  {summary['hypothesis_count']}")
    print(f"bounded tests run:      {summary['tests_run']}")
    print(f"supported:              {summary['supported_count']}")
    print(f"falsified:              {summary['falsified_count']}")
    print(f"inconclusive:           {summary['inconclusive_count']}")
    print(f"unsafe to test:         {summary['unsafe_to_test_count']}")
    print(f"long-lived unknowns:    {summary['long_lived_unknown_count']}")
    print(f"top hypothesis:         {summary['highest_priority_hypothesis']}")
    print(f"last evidence result:   {summary['last_evidence_result']}")
    families = engine.memory.family_counts()
    print("hypothesis families:")
    for fam, count in sorted(families.items(), key=lambda kv: -kv[1]):
        print(f"  {fam:42s} {count}")
    print()

    builder = HypothesisReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "hypothesis_report.json",
                         Path(args.state_dir) / "hypothesis_report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: hypotheses are internal research artifacts, not beliefs. "
          "Causal language is hedged ('causes candidate'); offline and "
          "counterfactual evidence is never treated as a real observation; "
          "tests are bounded and safe -- no LLM, no human feedback, no "
          "real-world experiment.")


if __name__ == "__main__":
    main()
