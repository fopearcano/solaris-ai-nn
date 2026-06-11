#!/usr/bin/env python3
"""Developmental short demo: months of simulated development, bounded.

    python examples/run_developmental_short_demo.py --steps 500

A bounded simulated-time developmental run: segments of the full
cognitive stack with maintenance ticks between them -- consolidation,
epoch evaluation, milestones, growth/drift snapshots, autobiographical
history, and a ClaimGuard-scanned developmental report. No real month
passes, and no real month run starts here.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental import (
    DevelopmentalQueryInterface,
    DevelopmentalReportBuilder,
    DevelopmentalRuntime,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Developmental short demo")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/developmental_short")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    runtime = DevelopmentalRuntime(
        state_dir=args.state_dir, simulated_time=True,
        time_acceleration=3600.0,  # one step ~ one simulated hour
        max_steps=args.steps, consolidation_interval_steps=100,
        seed=args.seed)
    snapshot = runtime.run()
    summary = snapshot["summary"]

    print("=" * 70)
    print("Solaris-AI-NN -- developmental short demo (simulated time, "
          "bounded)")
    print("=" * 70)
    print(f"steps run:            {args.steps} across "
          f"{summary['segments_run']} segment(s)")
    print(f"developmental age:    "
          f"{summary['developmental_age_hours']:.0f} simulated hours "
          f"(~{summary['developmental_age_hours'] / 24:.1f} days)")
    print(f"current epoch:        {summary['current_epoch']}")
    print(f"milestones:           {summary['milestone_count']} "
          f"(latest: "
          f"{(summary['last_milestone'] or {}).get('type')})")
    print(f"memory layers:        hot="
          f"{summary['memory_layers']['hot_count']} warm="
          f"{summary['memory_layers']['warm_count']} cold="
          f"{summary['memory_layers']['cold_count']} fossil="
          f"{summary['memory_layers']['fossil_count']}")
    print(f"growth status:        {summary['growth_status']}")
    print(f"drift status:         {summary['drift_status']}")
    print(f"structural change:    "
          f"{summary['structural_change_score']}")
    print()
    builder = DevelopmentalReportBuilder(runtime)
    paths = builder.save(Path(args.state_dir) / "developmental_report.json",
                         Path(args.state_dir) / "developmental_report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    queries = DevelopmentalQueryInterface(runtime)
    for question in ("what developmental epoch is active?",
                     "is the system growing or just accumulating data?"):
        print(f"Q: {question}")
        print(f"A: {queries.answer(question).text[:150]}")
        print()
    print("note: this is a persistent developmental process under "
          "measurement -- learning by remaining active across time, "
          "with no teacher, no reward button, and no consciousness "
          "claim.")


if __name__ == "__main__":
    main()
