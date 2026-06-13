#!/usr/bin/env python3
"""Active perception demo: a system that regulates its own exposure.

    python examples/run_active_perception_demo.py --steps 300

A bounded simulated-time developmental run in a controlled nursery, with
active perception enabled in the balanced policy. The system estimates
salience, uncertainty, curiosity (an intrinsic sampling pressure, not a
desire), and stagnation; proposes safe sampling actions; routes them through
safety/governance; and records what helped. No real-world action, no
robotics, no network, no LLM, no autonomy -- sampling is simulation /
internal / read-only only.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.active_perception import ActivePerceptionReportBuilder
from solaris_ai_nn.developmental import DevelopmentalRuntime
from solaris_ai_nn.ecology import NurseryConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Active perception demo")
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/active_perception")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    config = NurseryConfig(nursery_id="active-perception-nursery",
                           seed=args.seed, duration_steps=args.steps,
                           output_state_dir=args.state_dir)
    runtime = DevelopmentalRuntime(
        state_dir=args.state_dir, simulated_time=True,
        time_acceleration=3600.0, max_steps=args.steps,
        consolidation_interval_steps=50, seed=args.seed,
        enable_ecology=True, nursery_config=config,
        enable_proto_language=True, enable_active_perception=True,
        active_perception_mode="balanced")
    runtime.run()
    controller = runtime.active_perception
    snap = controller.snapshot()
    memory = snap["exploration_memory"]
    policy = snap["policy"]

    print("=" * 70)
    print("Solaris-AI-NN -- active perception (regulating its own exposure)")
    print("=" * 70)
    print(f"steps lived:           {args.steps} (simulated time)")
    print(f"sampling policy mode:  {policy['mode']}")
    print(f"sampling decisions:    {policy['decisions_made']}")
    print(f"sampling actions:      {memory['record_count']}")
    print(f"useful sampling rate:  {memory['useful_rate']}")
    print(f"blocked sampling:      {snap['blocked_count']}")
    print(f"curiosity pressure:    {(snap['curiosity'] or {}).get('pressure')}")
    print(f"attention shifts:      "
          f"{(snap['attention'] or {}).get('shifts_total')}")
    print(f"stagnation status:     {(snap['stagnation'] or {}).get('status')}")
    print("outcome counts:")
    for outcome, count in sorted(
            memory.get("outcome_counts", {}).items()):
        print(f"  {outcome:10s} {count}")
    print()

    builder = ActivePerceptionReportBuilder(controller)
    paths = builder.save(Path(args.state_dir) / "active_perception_report.json",
                         Path(args.state_dir) / "active_perception_report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: curiosity is an intrinsic sampling-pressure metric (a drive "
          "to reduce uncertainty), not a desire in the human sense. Every "
          "sampling action is simulation/internal/read-only and a suggestion "
          "until safety, governance, and the executive validate it -- no "
          "real-world autonomy, no LLM.")


if __name__ == "__main__":
    main()
